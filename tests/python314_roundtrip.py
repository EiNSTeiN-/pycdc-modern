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
    def recover(self, source):
        code = compile(source, 'fixture.py', 'exec')
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
