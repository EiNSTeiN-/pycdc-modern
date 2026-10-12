"""Behavior checks using original fixtures only; requires CPython 3.14."""
import asyncio
from contextlib import nullcontext
import importlib.util
import marshal
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get('PYCDC_BINARY', str(ROOT / 'target/debug/pycdc')))


@unittest.skipUnless(sys.version_info[:2] == (3, 14), 'Requires CPython 3.14')
class Python314RoundTrip(unittest.TestCase):
    def check_generator_bytes(self, source):
        import types
        code = compile(source, 'owned-original', 'exec')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'owned.pyc'
            path.write_bytes(importlib.util.MAGIC_NUMBER + bytes(12) + marshal.dumps(code))
            result = subprocess.run([str(BINARY), str(path)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('incomplete', result.stderr)
        recovered = compile(result.stdout, 'owned-recovered', 'exec')
        def generator(module):
            function = next(value for value in module.co_consts
                            if isinstance(value, types.CodeType) and value.co_name == 'select')
            return next(value for value in function.co_consts
                        if isinstance(value, types.CodeType) and value.co_name == '<genexpr>')
        left, right = generator(code), generator(recovered)
        self.assertEqual(left.co_code, right.co_code)
        self.assertEqual(left.co_exceptiontable, right.co_exceptiontable)
        self.assertEqual(left.co_varnames, right.co_varnames)
        namespaces = [{}, {}]; exec(code, namespaces[0]); exec(recovered, namespaces[1])
        return namespaces[0]['select'], namespaces[1]['select']

    def test_repeated_unpack_target_keeps_elided_stores_and_errors(self):
        original, recovered = self.check_generator_bytes(
            'def select(values):\n'
            '    return tuple(value is not None for value, discarded, discarded, discarded in values)\n')
        for values in ([], [(None, 1, 2, 3)], [(1, 2, 3, 4), (None, 5, 6, 7)],
                       [(1, 2)], [None]):
            outcomes = []
            for function in (original, recovered):
                try: outcomes.append(function(values))
                except (TypeError, ValueError) as error: outcomes.append((type(error).__name__, str(error)))
            self.assertEqual(outcomes[1], outcomes[0])

    def test_real_underscore_and_surviving_repeat_values_are_kept(self):
        original, recovered = self.check_generator_bytes(
            'def select(values):\n'
            '    return tuple((value, discarded, _) for value, _, discarded, discarded in values)\n')
        for values in ([], [(1, 2, 3, 4)], [(5, 6, 7, 8), (9, 10, 11, 12)]):
            self.assertEqual(recovered(values), original(values))

    def test_filtered_generator_keeps_value_preserving_boolops(self):
        for expression in ('row[1] or 0', 'row[1] and row[2]',
                           'row[1] or row[2] or 0', '(row[1] and row[2]) or 0'):
            original, recovered = self.check_generator_bytes(
                'def select(rows):\n'
                f'    return tuple({expression} for row in rows if row[0])\n')
            for rows in ([], [(False, 3, 4)], [(True, 0, 2)],
                         [(True, 2, 3), (True, None, 4), (False, 5, 6)],
                         [(True, '', 7), (True, 'kept', 8)]):
                self.assertEqual(recovered(rows), original(rows))

    def test_generator_none_filter_and_boolop_keep_truth_and_call_order(self):
        original, recovered = self.check_generator_bytes(
            'def select(rows):\n'
            '    return tuple(row.get("amount") or 0.0 for row in rows if row.get("amount") is not None)\n')
        def exercise(function):
            calls = []
            class Value:
                def __init__(self, tag, truth):
                    self.tag, self.truth = tag, truth
                def __bool__(self):
                    calls.append(('bool', self.tag))
                    return self.truth
            class Row:
                def __init__(self, tag, value):
                    self.tag, self.value = tag, value
                def get(self, key):
                    calls.append(('get', self.tag, key))
                    return self.value
            values = [Row('missing', None), Row('zero', 0),
                      Row('false', Value('false', False)),
                      Row('true', Value('true', True))]
            result = function(values)
            return tuple(value.tag if isinstance(value, Value) else value
                         for value in result), calls
        self.assertEqual(exercise(recovered), exercise(original))

    def recover(self, source):
        code = compile(source, 'fixture.py', 'exec')
        return self.recover_code(code)

    def recover_code(self, code):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'fixture.pyc'
            file.write_bytes(importlib.util.MAGIC_NUMBER + bytes(12) + marshal.dumps(code))
            result = subprocess.run([str(BINARY), str(file)], capture_output=True,
                                    text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('incomplete', result.stderr)
        original, recovered = {}, {}
        exec(code, original)
        exec(compile(result.stdout, 'recovered_fixture.py', 'exec'), recovered)
        return original['select'], recovered['select']

    def test_padded_exception_returns_keep_the_mainline_value_build(self):
        import dis
        import types
        source = (
            'async def select(read, work, response):\n'
            '    try:\n        payload = await read()\n'
            '    except Exception:\n        return response({"error": "invalid_json"}, status=400)\n'
            '    if not isinstance(payload, dict):\n'
            '        return response({"error": "invalid_payload"}, status=400)\n'
            '    try:\n        request_id = int(payload["request_id"])\n'
            '    except (KeyError, TypeError, ValueError):\n'
            '        return response({"error": "invalid_payload"}, status=400)\n'
            '    try:\n        result = await work(request_id)\n'
            '    except Exception as error:\n'
            '        reason = str(getattr(error, "key", None) or "request_failed")\n'
            '        status = 403 if reason in {"forbidden", "license_required"} else 400\n'
            '        return response({"error": reason}, status=status)\n'
            '    return response({"success": True, **(result if isinstance(result, dict) else {})},\n'
            '                    headers={"Cache-Control": "no-store"})\n')
        module = compile(source, 'fixture.py', 'exec')
        code = next(value for value in module.co_consts if isinstance(value, types.CodeType))
        instructions = list(dis.get_instructions(code))
        # This owned compact fixture needs no extended operands. Three NOPs
        # reproduce the masked-exit layout, preserving the return's value.
        self.assertFalse(any(item.opname == 'EXTENDED_ARG' for item in instructions))
        starts, sizes, cursor = {}, {}, 0
        for index, item in enumerate(instructions):
            starts[item.offset] = cursor
            end = instructions[index + 1].offset if index + 1 < len(instructions) else len(code.co_code)
            sizes[item.offset] = end - item.offset
            cursor += sizes[item.offset] + (6 if item.opname == 'RETURN_VALUE' else 0)
        starts[len(code.co_code)] = cursor
        output = bytearray()
        for item in instructions:
            if item.opname == 'RETURN_VALUE':
                output.extend(bytes((dis.opmap['NOP'], 0)) * 3)
            actual = len(output)
            raw = bytearray(code.co_code[item.offset:item.offset + sizes[item.offset]])
            if item.opcode in dis.hasjump:
                delta = (starts[item.argval] - (actual + sizes[item.offset])) // 2
                operand = -delta if 'BACKWARD' in item.opname else delta
                self.assertTrue(0 <= operand <= 255)
                raw[1] = operand
            output.extend(raw)
        def varint(value, marker=False):
            digits = [value & 63]
            while value >> 6:
                value >>= 6
                digits.append(value & 63)
            digits.reverse()
            for index in range(len(digits) - 1):
                digits[index] |= 64
            if marker:
                digits[0] |= 128
            return bytes(digits)
        table = b''.join(varint(starts[row.start] // 2, True)
                         + varint((starts[row.end] - starts[row.start]) // 2)
                         + varint(starts[row.target] // 2)
                         + varint((row.depth << 1) | row.lasti)
                         for row in dis.Bytecode(code).exception_entries)
        padded = code.replace(co_code=bytes(output), co_exceptiontable=table, co_linetable=b'')
        module = module.replace(co_consts=tuple(padded if value is code else value for value in module.co_consts))
        original, recovered = self.recover_code(module)
        plain_namespace = {}
        exec(compile(source, 'plain_fixture.py', 'exec'), plain_namespace)
        async def exercise(function, payload, result):
            calls = []
            async def read():
                calls.append('read')
                if isinstance(payload, Exception):
                    raise payload
                return payload
            async def work(request_id):
                calls.append(('work', request_id))
                if isinstance(result, Exception):
                    raise result
                return result
            def response(value, **options):
                return value, options
            return await function(read, work, response), calls
        cases = [(ValueError('owned failure'), None), ([], None), ({}, None),
                 ({'request_id': 'bad'}, None), ({'request_id': '7'}, {'value': 3}),
                 ({'request_id': 7}, None), ({'request_id': 7}, RuntimeError('owned failure'))]
        for payload, result in cases:
            expected = asyncio.run(exercise(plain_namespace['select'], payload, result))
            self.assertEqual(asyncio.run(exercise(original, payload, result)), expected)
            self.assertEqual(asyncio.run(exercise(recovered, payload, result)), expected)

    def test_real_sunk_value_tail_keeps_its_else_path(self):
        from types import SimpleNamespace
        original, recovered = self.recover(
            'def select(value):\n'
            '    try:\n        entry = value.entry\n'
            '    except AttributeError:\n        kind = "missing"\n'
            '    else:\n        kind = "present"\n'
            '    return kind, value\n')
        for value in (object(), SimpleNamespace(entry=3)):
            expected = original(value)
            result = recovered(value)
            self.assertEqual(result, expected)
            self.assertIs(result[1], value)

    def test_shared_rejection_guard_keeps_factory_returns_and_truth_tests(self):
        for source, values in (
            ('def select(value, build):\n'
             '    if value is None or not 0.0 <= value <= 20.0:\n'
             '        return build("reject", amount=0)\n'
             '    return build("accept", amount=value)\n',
             (None, -1.0, 0.0, 20.0, 21.0, float('nan'))),
            ('def select(value, build):\n'
             '    if not value or len(value) < 2:\n'
             '        return build("reject", amount=0)\n'
             '    return build("accept", amount=len(value))\n',
             ([], [1], [1, 2], [1, 2, 3]))):
            original, recovered = self.recover(source)
            for value in values:
                outputs = []
                for function in (original, recovered):
                    calls = []
                    def build(kind, **options):
                        calls.append((kind, options))
                        return kind, options
                    outputs.append((function(value, build), calls))
                self.assertEqual(outputs[1], outputs[0])

    def test_constant_and_conditional_class_annotation_gates(self):
        import types
        original, recovered = self.recover(
            'def select(enabled):\n    import annotationlib\n'
            '    class Result:\n        "Documented result."\n'
            '        if True:\n            amount: int = 3\n'
            '        if enabled:\n            label: str = "ready"\n'
            '        def read(self) -> int:\n            return self.amount\n'
            '    return (Result.__doc__, Result().read(),\n'
            '            annotationlib.get_annotations(Result, format=annotationlib.Format.STRING))\n')
        for enabled in (False, True):
            self.assertEqual(recovered(enabled), original(enabled))
        def class_code(function):
            return next(value for value in function.__code__.co_consts
                        if isinstance(value, types.CodeType) and value.co_name == 'Result')
        left, right = class_code(original), class_code(recovered)
        self.assertEqual(right.co_cellvars, left.co_cellvars)
        annotation = lambda code: next(value for value in code.co_consts
                                       if isinstance(value, types.CodeType) and value.co_name == '__annotate__'
                                       and '__conditional_annotations__' in value.co_freevars)
        self.assertEqual(annotation(right).co_freevars, annotation(left).co_freevars)

    def test_loop_class_annotations_preserve_registration_and_default_calls(self):
        original, recovered = self.recover(
            'def select(values):\n    import annotationlib\n    calls = []\n'
            '    def default(value):\n        calls.append(value)\n        return value\n'
            '    class Result:\n'
            '        for value in values:\n            amount: int = default(value)\n'
            '    return (calls, getattr(Result, "amount", None),\n'
            '            annotationlib.get_annotations(Result, format=annotationlib.Format.STRING))\n')
        for values in ([], [3], [2, 5]):
            self.assertEqual(recovered(values), original(values))

    def test_nested_dictionary_comprehension_in_generator(self):
        original, recovered = self.recover(
            'def select(rows):\n    return tuple({key: row[key] for key in row} for row in rows)\n')
        rows = [{'a': 2, 'b': 3}, {'x': 5}]
        self.assertEqual(recovered(rows), original(rows))

    def test_expanded_kwargs_in_generator(self):
        original, recovered = self.recover(
            'def select(rows, factory):\n    return tuple(factory(**dict(row)) for row in rows)\n')
        rows, factory = [{'a': 2}, {'x': 5}], lambda **values: values
        self.assertEqual(recovered(rows, factory), original(rows, factory))

    def test_nested_generator_global_call_preserves_callable(self):
        original, recovered = self.recover(
            'def select(rows):\n'
            '    return sorted(sum(value for value in row) / len(row) for row in rows)\n')
        rows = [[1, 2, 3], [5, 9], [3]]
        self.assertEqual(recovered(rows), original(rows))

    def test_nested_generator_captures_multiple_closure_cells(self):
        original, recovered = self.recover(
            'def select(rows):\n'
            '    deltas = rows\n'
            '    factory = sum\n'
            '    return sorted(sum(factory(deltas) for _ in deltas) / len(deltas) for _ in range(3))\n')
        rows = [1, 2, 4]
        self.assertEqual(recovered(rows), original(rows))

    def test_async_context_with_guard_and_finally(self):
        original, recovered = self.recover(
            'async def select(manager, calculate):\n    async with manager:\n        if calculate is None:\n            return 3\n        try:\n            return await calculate()\n        finally:\n            last = False\n')
        async def calculate():
            return 7
        for function in (None, calculate):
            self.assertEqual(asyncio.run(recovered(nullcontext(), function)),
                             asyncio.run(original(nullcontext(), function)))

    def test_async_generator_try_except_else_finally(self):
        original, recovered = self.recover(
            'async def select(work, nested):\n'
            '    if nested:\n'
            '        try:\n            yield 3\n'
            '        except BaseException:\n'
            '            await work("rollback")\n            await work("release")\n            raise\n'
            '        else:\n            await work("release")\n'
            '        finally:\n            await work("finish")\n'
            '        return\n'
            '    yield 5\n')

        async def exercise(function, nested, fail):
            calls = []
            async def work(operation):
                calls.append(operation)
            iterator = function(work, nested)
            value = await anext(iterator)
            if fail:
                with self.assertRaises(RuntimeError):
                    await iterator.athrow(RuntimeError('fixture'))
            else:
                with self.assertRaises(StopAsyncIteration):
                    await anext(iterator)
            return value, calls

        for nested in (False, True):
            for fail in (False, True):
                self.assertEqual(asyncio.run(exercise(recovered, nested, fail)),
                                 asyncio.run(exercise(original, nested, fail)))

    def test_sequential_async_handlers_resume_shared_tail(self):
        original, recovered = self.recover(
            'async def select(manager, work):\n    results = []\n'
            '    try:\n        async with manager:\n            results.append(await work("first"))\n'
            '    except ValueError:\n        results.append(2)\n'
            '    results.extend(value for value in [3, 4])\n'
            '    try:\n        async with manager:\n            results.append(await work("last"))\n'
            '    except KeyError:\n        results.append(5)\n'
            '    return results\n')
        async def exercise(function, first_error, last_error):
            calls = []
            async def work(stage):
                calls.append(stage)
                error = first_error if stage == 'first' else last_error
                if error:
                    raise error('owned failure')
                return 11 if stage == 'first' else 22
            return await function(nullcontext(), work), calls
        for first_error, last_error in ((None, None), (ValueError, None),
                                         (None, KeyError), (ValueError, KeyError)):
            self.assertEqual(asyncio.run(exercise(recovered, first_error, last_error)),
                             asyncio.run(exercise(original, first_error, last_error)))

    def test_short_circuit_inside_comprehension_element(self):
        original, recovered = self.recover(
            'def select(rows):\n    return [max(0.0, float(row.get("x") or 0.0)) for row in rows]\n')
        rows = [{'x': 7}, {'x': None}, {'x': -2}, {}]
        self.assertEqual(recovered(rows), original(rows))

    def test_none_or_negated_chained_comparison_guard(self):
        original, recovered = self.recover(
            'def select(value):\n'
            '    if value is None or not 0.0 <= value <= 15.0:\n        return False\n'
            '    return True\n')
        for value in (None, -1.0, 0.0, 10.0, 15.0, 16.0, float('nan')):
            with self.subTest(value=value):
                self.assertEqual(recovered(value), original(value))

    def test_loop_guard_skips_every_missing_value(self):
        original, recovered = self.recover(
            'def select(rows):\n    result = []\n'
            '    for row in rows:\n'
            '        a = row.get("a")\n        b = row.get("b")\n'
            '        c = row.get("c")\n        d = row.get("d")\n'
            '        if a is None or b is None or c is None or d is None or d < 0.01:\n'
            '            continue\n'
            '        result.append(a + b + c + d)\n'
            '    return result\n')
        rows = [{}, {'a': 1}, {'a': 1, 'b': 2, 'c': 3, 'd': 0},
                {'a': 1, 'b': 2, 'c': 3, 'd': 4}]
        self.assertEqual(recovered(rows), original(rows))

    def test_independent_loop_rejections_keep_assignment_and_return_scope(self):
        original, recovered = self.recover(
            'def select(rows):\n'
            '    for row in rows:\n'
            '        if not isinstance(row, dict):\n            continue\n'
            '        coordinator = row.get("coordinator")\n'
            '        if coordinator is None:\n            continue\n'
            '        return coordinator\n')
        for rows in ([], [1], [1, {}], [1, {'coordinator': 7}],
                     [{}, {'coordinator': None}, {'coordinator': 0}],
                     [{'coordinator': False}, {'coordinator': 9}]):
            self.assertEqual(recovered(rows), original(rows))
        def exercise(function):
            calls = []
            class Coordinator:
                def __bool__(self): raise AssertionError('Must test None identity only')
            result = Coordinator()
            class Row(dict):
                def get(self, key): calls.append(key); return result
            self.assertIs(function([object(), {}, Row()]), result)
            return calls
        self.assertEqual(exercise(recovered), exercise(original))
        # Line metadata may alter fused stores, but this fixture has identical
        # instruction/exception bytes and all original local spellings.
        self.assertEqual(recovered.__code__.co_code, original.__code__.co_code)
        self.assertEqual(recovered.__code__.co_exceptiontable, original.__code__.co_exceptiontable)
        self.assertEqual(recovered.__code__.co_varnames, original.__code__.co_varnames)

    def test_negated_chain_evaluates_middle_call_once(self):
        original, recovered = self.recover(
            'def select(value):\n'
            '    if value is None or not 0.0 <= value() <= 15.0:\n        return False\n'
            '    return True\n')
        for number in (-1.0, 0.0, 15.0, 16.0, float('nan')):
            results = []
            for function in (original, recovered):
                calls = []
                def value():
                    calls.append('evaluated')
                    return number
                results.append((function(value), calls))
            self.assertEqual(results[1], results[0])
            self.assertEqual(results[0][1], ['evaluated'])

    def test_guard_does_not_absorb_later_constant_return(self):
        original, recovered = self.recover(
            'def select(value):\n'
            '    if value is None or not 0.0 <= value <= 15.0:\n        return False\n'
            '    return False\n')
        for value in (None, -1.0, 1.0, 16.0):
            self.assertEqual(recovered(value), original(value))

    def test_multi_link_rejection_guard_keeps_every_operand_and_call(self):
        original, recovered = self.recover(
            'def select(first, second):\n'
            '    if first is None or not 0.0 <= first() <= second() <= 15.0:\n'
            '        return False\n    return True\n')
        for first_value, second_value in ((1.0, 2.0), (-1.0, 2.0), (3.0, 2.0),
                                          (2.0, 16.0), (float('nan'), 2.0), (2.0, float('nan'))):
            results = []
            for function in (original, recovered):
                calls = []
                def first():
                    calls.append('first')
                    return first_value
                def second():
                    calls.append('second')
                    return second_value
                results.append((function(first, second), calls))
            self.assertEqual(results[1], results[0])
        self.assertEqual(recovered(None, lambda: 5), original(None, lambda: 5))

    def test_separate_comparisons_keep_distinct_calls(self):
        original, recovered = self.recover(
            'def select(value):\n'
            '    if value is None or not (0.0 <= value() and value() <= 15.0):\n'
            '        return False\n    return True\n')
        results = []
        for function in (original, recovered):
            calls = []
            values = iter((1.0, 16.0))
            def value():
                calls.append('value')
                return next(values)
            results.append((function(value), calls))
        self.assertEqual(results[1], results[0])
        self.assertEqual(results[0], (False, ['value', 'value']))

    def test_large_dictionary_literal_inside_comprehension(self):
        literal = ', '.join(f'"k{i}": row + {i}' for i in range(20))
        original, recovered = self.recover(f'def select(rows):\n    return [{{{literal}}} for row in rows]\n')
        self.assertEqual(recovered([1, 3]), original([1, 3]))


if __name__ == '__main__':
    unittest.main()
