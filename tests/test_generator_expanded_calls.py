"""Round-trip expanded generator calls across Python 3.11–3.14 stack layouts."""

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

    def test_expanded_calls_keep_arguments_and_error_order(self):
        cases = (
            ("factory(*row)", [(1, 2), (3,)]),
            ("factory(**dict(row))", [{"a": 1}, {"b": 2}]),
            ("factory(*row[0], **row[1])", [((1, 2), {"flag": 7}), ((3,), {})]),
        )
        for expression, rows in cases:
            source = (
                "def select(rows, factory):\n"
                f"    return tuple({expression} for row in rows)\n"
            )
            for failure_at in (None, 1, 2):
                with self.subTest(expression=expression, failure_at=failure_at):
                    original, recovered = self.recover(source)
                    outcomes = []
                    for function in (original, recovered):
                        events = []

                        def factory(*args, **kwargs):
                            events.append((args, tuple(kwargs.items())))
                            if len(events) == failure_at:
                                raise ValueError("factory failed")
                            return args, kwargs

                        try:
                            value = ("value", function(rows, factory))
                        except ValueError as error:
                            value = (type(error).__name__, str(error))
                        outcomes.append((value, events))
                    self.assertEqual(outcomes[1], outcomes[0])
                    self.assertEqual(len(outcomes[1][1]), failure_at or 2)
                    self.assertEqual(recovered([], factory), ())


if __name__ == "__main__":
    unittest.main()
