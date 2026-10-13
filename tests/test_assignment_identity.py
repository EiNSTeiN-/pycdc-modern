"""Compile, decompile and execute original fixtures with CPython 3.11–3.14."""

import importlib.util
import marshal
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("PYCDC_BINARY", ROOT / "target/debug/pycdc"))


@unittest.skipUnless(
    sys.implementation.name == "cpython" and (3, 11) <= sys.version_info[:2] < (3, 15),
    "requires CPython 3.11–3.14; 3.15 LOAD_COMMON_CONSTANT 7 (None) is not handled",
)
class RoundTrip(unittest.TestCase):
    def recover(self, source):
        code = compile(source, "fixture.py", "exec", dont_inherit=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.pyc"
            path.write_bytes(
                importlib.util.MAGIC_NUMBER + bytes(12) + marshal.dumps(code)
            )
            result = subprocess.run(
                [str(BINARY), str(path)], capture_output=True, text=True, timeout=10
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("incomplete", result.stderr.lower())
        self.assertNotIn("INCOMPLETE", result.stdout)
        original, recovered = {}, {}
        exec(code, original)
        exec(
            compile(result.stdout, "recovered.py", "exec", dont_inherit=True), recovered
        )
        return original["select"], recovered["select"]

    def test_independent_equal_assignments_keep_both_evaluations_and_true_chains(self):
        sources = (
            "def select(read):\n    left, right = read(), read()\n    return left, right\n",
            "def select(read):\n    left = right = read()\n    return left, right\n",
            "def select(read):\n    left, right = None, None\n    return left, right\n",
            "def select(read):\n    right = left = None\n    return left, right\n",
        )
        for index, source in enumerate(sources):
            original, recovered = self.recover(source)
            self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
            self.assertEqual(
                original.__code__.co_exceptiontable,
                recovered.__code__.co_exceptiontable,
            )
            for failure_at in (None, 1, 2):
                outcomes = []
                for function in (original, recovered):
                    events = []

                    def read():
                        events.append(len(events) + 1)
                        if events[-1] == failure_at:
                            raise ValueError("owned evaluation")
                        return events[-1]

                    try:
                        result = ("value", function(read))
                    except ValueError as error:
                        result = (type(error).__name__, str(error))
                    outcomes.append((result, events))
                with self.subTest(source=index, failure_at=failure_at):
                    self.assertEqual(outcomes[1], outcomes[0])
            if index == 0:
                counter = iter((7, 8))
                self.assertEqual(recovered(lambda: next(counter)), (7, 8))


if __name__ == "__main__":
    unittest.main()
