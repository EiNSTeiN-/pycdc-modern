#!/usr/bin/env python3
"""Dump opcode metadata of the *running* interpreter as JSON.

Used by gen_configs.py (via `uv run --python X.Y`) to obtain data that xdis
does not carry, notably the 3.11+ inline CACHE entry counts.
"""
import json
import sys

import opcode as op
import dis


def cache_entries():
    """{opcode_byte: n_cache_words} for opcodes followed by CACHE entries (3.11+)."""
    from collections.abc import Mapping

    result = {}
    ice = getattr(op, "_inline_cache_entries", None)
    # 3.13+ uses a mapping {name: count}; 3.15 exposes it as a frozendict,
    # which is not a dict subclass, so check Mapping rather than dict.
    if isinstance(ice, Mapping):
        for name, n in ice.items():
            if n and name in op.opmap:
                result[op.opmap[name]] = int(n)
    elif ice:  # 3.11 / 3.12: list indexed by opcode
        for i, n in enumerate(ice):
            if n:
                result[i] = int(n)
    else:
        fmt = getattr(op, "_cache_format", None)
        if isinstance(fmt, Mapping):  # 3.13+: {name: [(field, size), ...]}
            for name, fields in fmt.items():
                n = sum(size for _, size in fields)
                if n and name in op.opmap:
                    result[op.opmap[name]] = int(n)
    return result


def main():
    out = {
        "version": sys.version_info[:3],
        "opmap": dict(op.opmap),
        "hasjrel": list(getattr(op, "hasjrel", [])),
        "hasjabs": list(getattr(op, "hasjabs", [])),
        "hascompare": list(getattr(op, "hascompare", [])),
        "hasconst": list(getattr(op, "hasconst", [])),
        "hasname": list(getattr(op, "hasname", [])),
        "haslocal": list(getattr(op, "haslocal", [])),
        "hasfree": list(getattr(op, "hasfree", [])),
        "hasarg": [i for i in range(256) if i >= op.HAVE_ARGUMENT],
        "cache_entries": cache_entries(),
        "cmp_op": list(op.cmp_op),
    }
    json.dump(out, sys.stdout, indent=0)


if __name__ == "__main__":
    main()
