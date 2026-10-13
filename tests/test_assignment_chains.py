"""Compile, decompile and execute original fixtures with CPython 3.11–3.14."""

import importlib.util
import marshal
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get("PYCDC_BINARY", ROOT / "target/debug/pycdc"))


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

    def test_long_copy_chains_keep_one_evaluation_and_fused_stores(self):
        for size in (3, 4, 5, 6):
            names = [f"value{index}" for index in range(size)]
            for expression in ("read()", "None"):
                source = (
                    "def select(read):\n    "
                    + " = ".join(names)
                    + " = "
                    + expression
                    + "\n    return "
                    + ", ".join(names)
                    + "\n"
                )
                original, recovered = self.recover(source)
                self.assertEqual(original.__code__.co_code, recovered.__code__.co_code)
                self.assertEqual(
                    original.__code__.co_exceptiontable,
                    recovered.__code__.co_exceptiontable,
                )
                for failure in (False, True):
                    outcomes = []
                    for function in (original, recovered):
                        events = []
                        value = object()

                        def read():
                            events.append("read")
                            if failure:
                                raise ValueError("owned chain")
                            return value

                        try:
                            result = function(read)
                            outcome = (
                                "value",
                                all(item is result[0] for item in result),
                                result[0] is value
                                if expression == "read()"
                                else result[0] is None,
                            )
                        except ValueError as error:
                            outcome = (type(error).__name__, str(error))
                        outcomes.append((outcome, events))
                    with self.subTest(
                        size=size, expression=expression, failure=failure
                    ):
                        self.assertEqual(outcomes[1], outcomes[0])
                        self.assertEqual(
                            len(outcomes[1][1]), int(expression == "read()")
                        )


if __name__ == "__main__":
    unittest.main()
