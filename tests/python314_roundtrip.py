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


def pad_return_values(test, code, count=3):
    """Add owned padding while retaining jumps and exact handler boundaries."""
    import dis
    instructions = list(dis.get_instructions(code))
    # This owned compact fixture needs no extended operands. NOPs
    # reproduce the masked-exit layout, preserving the return's value.
    test.assertFalse(any(item.opname == 'EXTENDED_ARG' for item in instructions))
    starts, sizes, cursor = {}, {}, 0
    for index, item in enumerate(instructions):
        starts[item.offset] = cursor
        end = instructions[index + 1].offset if index + 1 < len(instructions) else len(code.co_code)
        sizes[item.offset] = end - item.offset
        cursor += sizes[item.offset] + (2 * count if item.opname == 'RETURN_VALUE' else 0)
    starts[len(code.co_code)] = cursor
    output = bytearray()
    for item in instructions:
        if item.opname == 'RETURN_VALUE':
            output.extend(bytes((dis.opmap['NOP'], 0)) * count)
        actual = len(output)
        raw = bytearray(code.co_code[item.offset:item.offset + sizes[item.offset]])
        if item.opcode in dis.hasjump:
            delta = (starts[item.argval] - (actual + sizes[item.offset])) // 2
            operand = -delta if 'BACKWARD' in item.opname else delta
            test.assertTrue(0 <= operand <= 255)
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
    return padded


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

    def test_inline_comprehension_chained_filters_keep_each_polarity(self):
        for kind in ('list', 'set', 'dict'):
            for guard in ('isinstance(value, str)', 'not isinstance(value, str)'):
                for join in (' and ', ' if '):
                    element = 'value: value' if kind == 'dict' else 'value'
                    opening, closing = ('[', ']') if kind == 'list' else ('{', '}')
                    source = ('def select(values):\n'
                              f'    return {opening}{element} for value in values '
                              f'if {guard}{join}value{closing}\n')
                    with self.subTest(kind=kind, guard=guard, join=join):
                        original, recovered = self.recover(source)
                        self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
                        self.assertEqual(original.__code__.co_exceptiontable,
                                         recovered.__code__.co_exceptiontable)
                        for values in ([], ['', 'kept', None, 0, 2, 'again'],
                                       ['repeat', 'repeat', False, True]):
                            self.assertEqual(recovered(values), original(values))

    def test_inline_filter_accept_edge_preserves_calls_short_circuit_and_errors(self):
        sources = (
            'def select(rows, wanted):\n'
            '    return [row.tag for row in rows if row.value == wanted '
            'if row.ready() if row.final()]\n',
            'def select(rows, wanted):\n'
            '    return [row.tag for row in rows if row.value != wanted '
            'if not row.ready() if row.final()]\n',
        )
        def exercise(function, inputs):
            calls = []
            class Value:
                def __init__(self, row):
                    self.row = row
                def compare(self, name, wanted):
                    calls.append((name, self.row.tag, wanted))
                    if self.row.failure == name:
                        raise ValueError(name + ' failed')
                    return self.row.matches if name == 'eq' else not self.row.matches
                def __eq__(self, wanted):
                    return self.compare('eq', wanted)
                def __ne__(self, wanted):
                    return self.compare('ne', wanted)
            class Row:
                def __init__(self, tag, matches, ready, final, failure=''):
                    self.tag, self.matches = tag, matches
                    self.is_ready, self.is_final, self.failure = ready, final, failure
                    self.value = Value(self)
                def ready(self):
                    calls.append(('ready', self.tag))
                    if self.failure == 'ready':
                        raise RuntimeError('ready failed')
                    return self.is_ready
                def final(self):
                    calls.append(('final', self.tag))
                    if self.failure == 'final':
                        raise RuntimeError('final failed')
                    return self.is_final
            try:
                result = function([Row(*row) for row in inputs], 'wanted')
                outcome = ('value', result)
            except (RuntimeError, ValueError) as error:
                outcome = (type(error).__name__, str(error))
            return outcome, calls
        from itertools import product
        inputs = [('case-' + str(index), *values) for index, values in
                  enumerate(product((False, True), repeat=3))]
        cases = ([], inputs,
                 [('failure', True, True, True, 'eq')],
                 [('failure', False, False, True, 'ne')],
                 [('failure', True, True, True, 'ready')],
                 [('failure', False, False, True, 'ready')],
                 [('failure', True, True, True, 'final')],
                 [('failure', False, False, True, 'final')])
        for source in sources:
            original, recovered = self.recover(source)
            self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
            self.assertEqual(original.__code__.co_exceptiontable,
                             recovered.__code__.co_exceptiontable)
            for rows in cases:
                with self.subTest(source=source, rows=rows):
                    self.assertEqual(exercise(recovered, rows), exercise(original, rows))

    def test_shared_raise_guard_keeps_predicates_constructor_and_errors(self):
        source = ('def select(value, bad, ready, make_error):\n'
                  '    if value is None or bad(value) or not ready(value):\n'
                  '        raise make_error("invalid", value=value)\n'
                  '    return value\n')
        original, recovered = self.recover(source)
        self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
        self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
        def exercise(function, value, bad_value, ready_value, fail):
            calls = []
            def bad(item):
                calls.append(('bad', item))
                if fail == 'bad': raise KeyError('bad failed')
                return bad_value
            def ready(item):
                calls.append(('ready', item))
                if fail == 'ready': raise KeyError('ready failed')
                return ready_value
            def make_error(message, **keywords):
                calls.append(('error', message, keywords))
                if fail == 'constructor': raise TypeError('constructor failed')
                return ValueError(message)
            try: result = ('value', function(value, bad, ready, make_error))
            except (KeyError, TypeError, ValueError) as error:
                result = (type(error).__name__, str(error))
            return result, calls
        from itertools import product
        for value, bad, ready, fail in product((None, 0, 7), (False, True), (False, True),
                                               ('', 'bad', 'ready', 'constructor')):
            self.assertEqual(exercise(recovered, value, bad, ready, fail),
                             exercise(original, value, bad, ready, fail))

    def test_shared_raise_comparison_chain_keeps_middle_call_nan_and_rich_hooks(self):
        source = ('def select(value, read, invalid, make_error):\n'
                  '    if value is None or not 0 <= read(value) <= 10 or invalid(value):\n'
                  '        raise make_error("range failed")\n'
                  '    return value\n')
        original, recovered = self.recover(source)
        self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
        self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
        def exercise(function, value, number, invalid_value, failure):
            calls = []
            class Number:
                def __ge__(self, other):
                    calls.append(('ge', other))
                    if failure == 'ge': raise TypeError('ge failed')
                    return number >= other
                def __le__(self, other):
                    calls.append(('le', other))
                    if failure == 'le': raise TypeError('le failed')
                    return number <= other
                def __lt__(self, other):
                    raise AssertionError('Do not replace a negated chain with inverse comparisons')
                def __gt__(self, other):
                    raise AssertionError('Do not replace a negated chain with inverse comparisons')
            def read(item):
                calls.append(('read', item))
                if failure == 'read': raise TypeError('read failed')
                return Number()
            def invalid(item):
                calls.append(('invalid', item))
                return invalid_value
            def make_error(message):
                calls.append(('error', message))
                return ValueError(message)
            try: result = ('value', function(value, read, invalid, make_error))
            except (TypeError, ValueError) as error:
                result = (type(error).__name__, str(error))
            return result, calls
        from itertools import product
        for value, number, invalid, failure in product((None, 'value'), (-1, 0, 5, 10, 11, float('nan')),
                                                       (False, True), ('', 'read', 'ge', 'le')):
            self.assertEqual(exercise(recovered, value, number, invalid, failure),
                             exercise(original, value, number, invalid, failure))

    def test_shared_raise_explicit_cause_preserves_evaluation_and_exception_metadata(self):
        source = ('def select(value, reject, make_error, make_cause):\n'
                  '    if value is None or reject(value):\n'
                  '        raise make_error("invalid", value=value) from make_cause(value)\n'
                  '    return value\n')
        original, recovered = self.recover(source)
        self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
        self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
        def exercise(function, value, rejects, cause_mode):
            calls = []
            def reject(item):
                calls.append(('reject', item)); return rejects
            def make_error(message, **keywords):
                calls.append(('error', message, keywords)); return ValueError(message)
            def make_cause(item):
                calls.append(('cause', item))
                if cause_mode == 'failure': raise KeyError('cause factory failed')
                if cause_mode == 'invalid': return 'invalid cause'
                return RuntimeError('original cause') if cause_mode == 'exception' else None
            try: result = ('value', function(value, reject, make_error, make_cause))
            except (KeyError, TypeError, ValueError) as error:
                cause = error.__cause__
                result = (type(error).__name__, str(error),
                          None if cause is None else (type(cause).__name__, str(cause)),
                          error.__suppress_context__)
            return result, calls
        from itertools import product
        for value, rejects, cause_mode in product((None, 0, 7), (False, True),
                                                   ('none', 'exception', 'invalid', 'failure')):
            self.assertEqual(exercise(recovered, value, rejects, cause_mode),
                             exercise(original, value, rejects, cause_mode))

    def test_shared_raise_formatted_messages_keep_conversion_spec_and_cause_order(self):
        messages = ('f"{label!r}: {value!s:>{width}}"',
                    'f"{label!a}: {value:{width}}"')
        def exercise(function, number, rejects, failure):
            calls = []
            class Label:
                def __repr__(self):
                    calls.append('repr')
                    if failure == 'repr': raise TypeError('repr failed')
                    return 'label-α'
            class Value:
                def __str__(self):
                    calls.append('str')
                    if failure == 'str': raise TypeError('str failed')
                    return 'value'
                def __format__(self, spec):
                    calls.append(('format', spec))
                    if failure == 'format': raise TypeError('format failed')
                    return 'formatted-' + spec
            class Width:
                def __format__(self, spec):
                    calls.append(('width', spec))
                    if failure == 'width': raise TypeError('width failed')
                    return '6'
            def read(value):
                calls.append('read'); return number
            def reject(value):
                calls.append('reject'); return rejects
            def make_error(message):
                calls.append(('error', message)); return ValueError(message)
            def make_cause():
                calls.append('cause')
                if failure == 'cause': raise KeyError('cause failed')
                return RuntimeError('cause')
            value = None if number is None else Value()
            try:
                result = function(value, Label(), Width(), read, reject, make_error, make_cause)
                result = ('value', 'value object' if result is value and value is not None else result)
            except (KeyError, TypeError, ValueError) as error:
                cause = error.__cause__
                result = (type(error).__name__, str(error),
                          None if cause is None else (type(cause).__name__, str(cause)),
                          error.__suppress_context__)
            return result, calls
        from itertools import product
        for message, cause in product(messages, ('', ' from make_cause()')):
            source = ('def select(value, label, width, read, reject, make_error, make_cause):\n'
                      '    if value is None or not 0 <= read(value) <= 10 or reject(value):\n'
                      f'        raise make_error({message}){cause}\n'
                      '    return value\n')
            original, recovered = self.recover(source)
            self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
            self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
            for number, rejects, failure in product((None, 5, 11), (False, True),
                                                     ('', 'repr', 'str', 'format', 'width', 'cause')):
                with self.subTest(message=message, cause=cause, number=number, rejects=rejects, failure=failure):
                    self.assertEqual(exercise(recovered, number, rejects, failure),
                                     exercise(original, number, rejects, failure))

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
        padded = pad_return_values(self, code)
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

    def test_padded_unnamed_handler_retains_false_return_before_success_tail(self):
        import types
        source = ('async def select(value):\n'
                  '    try:\n        await sink(value)\n        log("saved")\n'
                  '    except CustomError:\n        notify("locked")\n        return False\n'
                  '    except Exception as error:\n        log("failed", error)\n        return False\n'
                  '    return True\n')
        module = compile(source, 'owned-original', 'exec', dont_inherit=True)
        code = next(v for v in module.co_consts if isinstance(v, types.CodeType))
        for padding in (1, 3, 9):
            padded = pad_return_values(self, code, padding)
            exported = module.replace(co_consts=tuple(padded if v is code else v for v in module.co_consts))
            original, recovered = self.recover_code(exported)
            async def exercise(function, failure):
                calls = []
                class CustomError(Exception): pass
                async def sink(value):
                    calls.append(('sink', value))
                    await asyncio.sleep(0)
                    if failure == 'custom': raise CustomError('owned locked')
                    if failure == 'ordinary': raise ValueError('owned ordinary')
                    if failure == 'cancel': raise asyncio.CancelledError('owned cancelled')
                def log(*values):
                    calls.append(tuple(str(value) for value in values))
                function.__globals__.update(sink=sink, log=log, CustomError=CustomError,
                                            notify=lambda value: calls.append(('notify', value)))
                try: outcome = ('value', await function(7))
                except asyncio.CancelledError as error: outcome = ('cancelled', str(error))
                return outcome, calls
            for failure in ('', 'custom', 'ordinary', 'cancel'):
                with self.subTest(padding=padding, failure=failure):
                    expected = asyncio.run(exercise(original, failure))
                    self.assertEqual(asyncio.run(exercise(recovered, failure)), expected)
                    if failure in ('custom', 'ordinary'):
                        self.assertEqual(expected[0], ('value', False))

    def test_nested_inline_comprehension_cleanup_keeps_four_and_six_targets(self):
        expressions = ('[(a, c) for a, b in data for c, d in b]',
                       '{(a, c) for a, b in data for c, d in b}',
                       '{(a, c): d for a, b in data for c, d in b}',
                       '[(a, c, e) for a, b in data for c, d in b for e, f in d]')
        for expression in expressions:
            # Saved target names must survive; actual post-loop assignments
            # and ordinary loop cleanup must still execute normally.
            source = ('def select(data):\n'
                      '    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60\n'
                      f'    result = {expression}\n'
                      '    after = 0\n    for number in (1, 2, 3):\n        after += number\n'
                      '    return result, (a, b, c, d, e, f), after\n')
            original, recovered = self.recover(source)
            self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
            self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
            data = [(1, [(2, [(3, 4), (5, 6)])])] if 'for e, f' in expression else [(1, [(2, 3), (4, 5)]), (6, [])]
            for values in ([], data, [(1, [(2,)])], [None], None):
                outputs = []
                for function in (original, recovered):
                    try: outcome = ('value', function(values))
                    except (TypeError, ValueError) as error: outcome = (type(error).__name__, str(error))
                    outputs.append(outcome)
                with self.subTest(expression=expression, values=values):
                    self.assertEqual(outputs[1], outputs[0])
            self.assertEqual(recovered(data)[1:], ((10, 20, 30, 40, 50, 60), 6))

    def test_simple_and_mixed_comprehension_targets_keep_real_iterator_cleanup(self):
        cases = (
            ('[(a, c) for a in data for c in a]', [[1, 2], [3]]),
            ('[(a, c) for key, a in data for c in a]', [(0, [1, 2]), (1, [3])]),
            ('[(a, c) for a in data for key, c in a]', [[(0, 1), (1, 2)]]),
            ('[(a, c, e) for a, b in data for c, d in b for e in d]', [(1, [(2, [3, 4])])]),
            ('{(a, c) for a in data for c in a}', [(1, 2), (3,)]),
        )
        for expression, data in cases:
            source = f'def select(data):\n    return {expression}\n'
            original, recovered = self.recover(source)
            with self.subTest(expression=expression):
                self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
                self.assertEqual(original.__code__.co_exceptiontable, recovered.__code__.co_exceptiontable)
                self.assertEqual(recovered(data), original(data))
                self.assertEqual(recovered([]), original([]))

    def test_padded_try_return_consumes_its_existing_calculated_value(self):
        import types
        expressions = ('make(value)', 'make(value).result',
                       '(make(value), 7)', '{"value": make(value)}')
        for expression in expressions:
            source = ('def select(value):\n'
                      '    if value:\n        try:\n'
                      f'            return {expression}\n'
                      '        except Exception:\n            pass\n'
                      '    return (fallback.read if True else None)().result or default.result\n')
            module = compile(source, 'owned-original', 'exec', dont_inherit=True)
            code = next(v for v in module.co_consts if isinstance(v, types.CodeType))
            plain = {}; exec(module, plain)
            for padding in (1, 3, 9):
                padded = pad_return_values(self, code, padding)
                exported = module.replace(co_consts=tuple(
                    padded if v is code else v for v in module.co_consts))
                original, recovered = self.recover_code(exported)
                def exercise(function, truth, result, failure):
                    calls = []
                    class Value:
                        def __bool__(self):
                            calls.append('truth')
                            if failure == 'truth': raise ValueError('truth failed')
                            return truth
                    class Result:
                        @property
                        def result(self):
                            calls.append('result')
                            if failure == 'attribute': raise AttributeError('result failed')
                            return result
                    class Fallback:
                        def read(self):
                            calls.append('fallback')
                            if failure == 'fallback': raise RuntimeError('fallback failed')
                            return types.SimpleNamespace(result='fallback-result')
                    def make(value):
                        calls.append('make')
                        if failure == 'make': raise KeyError('make failed')
                        if failure == 'base': raise KeyboardInterrupt('owned interrupt')
                        return Result() if expression == 'make(value).result' else result
                    function.__globals__.update(make=make, fallback=Fallback(),
                                                default=types.SimpleNamespace(result='default'))
                    try:
                        outcome = ('value', function(Value()))
                    except (Exception, KeyboardInterrupt) as error:
                        outcome = (type(error).__name__, str(error))
                    return outcome, calls
                for truth in (False, True):
                    for result in (None, 0, 'success'):
                        for failure in ('', 'truth', 'attribute', 'make', 'base', 'fallback'):
                            expected = exercise(plain['select'], truth, result, failure)
                            with self.subTest(expression=expression, padding=padding,
                                              truth=truth, result=result, failure=failure):
                                self.assertEqual(exercise(original, truth, result, failure), expected)
                                self.assertEqual(exercise(recovered, truth, result, failure), expected)
                self.assertEqual(exercise(recovered, False, None, '')[0],
                                 ('value', 'fallback-result'))
                if expression == 'make(value)':
                    self.assertEqual(exercise(recovered, True, None, ''),
                                     (('value', None), ['truth', 'make']))

    def test_padded_explicit_bare_return_keeps_only_the_side_effect(self):
        import types
        source = ('def select(value):\n'
                  '    if value:\n        try:\n            make(value)\n            return None\n'
                  '        except Exception:\n            return "handled"\n'
                  '    return (fallback.read if True else None)().result or default.result\n')
        module = compile(source, 'owned-original', 'exec', dont_inherit=True)
        code = next(v for v in module.co_consts if isinstance(v, types.CodeType))
        padded = pad_return_values(self, code)
        module = module.replace(co_consts=tuple(padded if v is code else v for v in module.co_consts))
        original, recovered = self.recover_code(module)
        for truth, fails in ((False, False), (True, False), (True, True)):
            outcomes = []
            for function in (original, recovered):
                calls = []
                def make(value):
                    calls.append('make')
                    if fails: raise ValueError('owned failure')
                    return 'discarded'
                def read():
                    calls.append('fallback'); return types.SimpleNamespace(result='fallback')
                function.__globals__.update(make=make, fallback=types.SimpleNamespace(read=read),
                                            default=types.SimpleNamespace(result='default'))
                outcomes.append((function(truth), calls))
            self.assertEqual(outcomes[1], outcomes[0])
            self.assertEqual(outcomes[0], (None, ['make']) if truth and not fails
                             else ('handled', ['make']) if truth
                             else ('fallback', ['fallback']))

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

    def test_negated_loop_comparison_keeps_nan_and_original_rich_operator(self):
        original, recovered = self.recover(
            'def select(values):\n'
            '    for value in values:\n'
            '        if not value < 10:\n            continue\n'
            '        return value\n')
        for values in ([], [float('nan'), 3], [float('nan')], [20, 5], [-1, 20]):
            self.assertEqual(recovered(values), original(values))
        def exercise(function):
            calls = []
            class Value:
                def __init__(self, label, number): self.label, self.number = label, number
                def __lt__(self, limit): calls.append((self.label, 'lt', limit)); return self.number < limit
                def __ge__(self, limit): raise AssertionError('Must not invert rich comparison')
            result = function([Value('skip', 20), Value('take', 5)])
            return result.label, calls
        self.assertEqual(exercise(recovered), exercise(original))
        self.assertEqual(recovered.__code__.co_code, original.__code__.co_code)

    def test_lookup_guard_keeps_comparison_and_getter_order(self):
        original, recovered = self.recover(
            'def select(values):\n'
            '    for value in values:\n'
            '        if not value.rating < 10:\n            continue\n'
            '        coordinator = value.coordinator\n'
            '        if coordinator is None:\n            continue\n'
            '        return coordinator\n')
        from types import SimpleNamespace
        for values in ([], [SimpleNamespace(rating=float('nan'), coordinator=7)],
                       [SimpleNamespace(rating=float('nan'), coordinator=7),
                        SimpleNamespace(rating=3, coordinator=0)]):
            self.assertEqual(recovered(values), original(values))
        def exercise(function):
            calls = []
            class Rating:
                def __init__(self, label, number): self.label, self.number = label, number
                def __lt__(self, limit): calls.append((self.label, 'lt', limit)); return self.number < limit
                def __ge__(self, limit): raise AssertionError('Must preserve comparison operator')
            class Row:
                def __init__(self, label, number, coordinator):
                    self.label, self.rating, self.value = label, Rating(label, number), coordinator
                @property
                def coordinator(self): calls.append(('getter', self.label)); return self.value
            result = function([Row('skip', 20, 7), Row('missing', 5, None), Row('take', 6, 0)])
            return result, calls
        self.assertEqual(exercise(recovered), exercise(original))
        self.assertEqual(recovered.__code__.co_code, original.__code__.co_code)

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
