"""Regenerate the padded handler-return fixtures with CPython 3.11–3.14.

Run once per interpreter from any directory. This prepares bytecode inputs
for tests/integration.rs; it is not a separate test runner. Only RETURN_VALUE
is padded, leaving versions that emit RETURN_CONST as compatibility controls.
"""
import importlib.util
import marshal
from pathlib import Path
import sys
import types

def pad_return_values(code, count=3):
    """Add NOP padding while retaining jumps and exact handler boundaries."""
    import dis
    instructions = list(dis.get_instructions(code))
    # This compact fixture needs no extended operands. NOPs
    # reproduce the padded return layout, preserving the return's value.
    assert not any(item.opname == 'EXTENDED_ARG' for item in instructions)
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
        if item.opcode in getattr(dis, "hasjump", dis.hasjrel + dis.hasjabs):
            delta = (starts[item.argval] - (actual + sizes[item.offset])) // 2
            operand = -delta if 'BACKWARD' in item.opname else delta
            assert 0 <= operand <= 255
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


if __name__ == "__main__":
    if not (3, 11) <= sys.version_info[:2] <= (3, 14):
        raise SystemExit("Use CPython 3.11, 3.12, 3.13 or 3.14")
    root = Path(__file__).resolve().parents[1]
    source_path = Path("tests/fixtures/handler_return_padding.py")
    source = (root / source_path).read_bytes()
    module = compile(source, source_path.as_posix(), "exec", dont_inherit=True)
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    header = (importlib.util.MAGIC_NUMBER + (3).to_bytes(4, "little")
              + importlib.util.source_hash(source))
    for count in (1, 3, 9):
        padded = module.replace(co_consts=tuple(
            pad_return_values(value, count) if isinstance(value, types.CodeType) else value
            for value in module.co_consts))
        path = root / f"tests/pyc/handler_return_padding_{count}.{version}.pyc"
        path.write_bytes(header + marshal.dumps(padded))
