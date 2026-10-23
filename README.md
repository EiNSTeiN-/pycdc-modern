# pycdc-rs

English | [简体中文](README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-2.0--3.15-yellow.svg)](#)
[![Corpus](https://img.shields.io/badge/corpus-520%2F520%20semantic-brightgreen.svg)](#verification)
[![Behavior](https://img.shields.io/badge/behavior-516%2F516-brightgreen.svg)](#verification)
[![Built with ZCode](https://img.shields.io/badge/Built%20with%20ZCode-000000.svg?style=flat&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMTgiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMjU2IDIxOCI+PHBhdGggZmlsbD0iI2ZmZmZmZiIgZD0iTTEzNC40IDAuMTMwMTUyTDExNi40OCAyNS42MDIyQzExMy42NjUgMjkuNTY5OSAxMDkuMDU0IDMyLjAwMTkgMTA0LjA2NCAzMi4wMDE5SDYuMzk5OVYwQzYuMzk5OSAwLjEzMDE0OSAxMzQuNCAwLjEzMDE1MiAxMzQuNCAwLjEzMDE1MloiLz48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjU2IDAuMTMwMTI3TDEwMi40MDEgMjE3LjczMkgwTDE1My41OTkgMC4xMzAxMjdIMjU2WiIvPjxwYXRoIGZpbGw9IiNmZmZmZmYiIGQ9Ik0xMjEuNjAxIDIxNy43MzJMMTM5LjY1IDE5Mi4xMzRDMTQyLjQ2NSAxODguMTY2IDE0Ny4wNzYgMTg1LjczNCAxNTIuMDY3IDE4NS43MzRIMjQ5LjYwNFYyMTcuNzM2SDEyMS42MDFWMjE3LjczMloiLz48L3N2Zz4=)](https://zcode.z.ai/)

Decompile and disassemble Python bytecode (`.pyc`) from **Python 2.0 through 3.15 (dev)** back into readable source — written in Rust, three dependencies, no Python required at runtime.

```sh
pycdc program.pyc          # decompile to stdout
pycdas program.pyc         # disassemble (exception tables, line numbers, nested code)
```

## Highlights

- **100% semantic equivalence** on a 520-module real-stdlib corpus across 13 interpreters (2.6–3.14); 76.5% are byte-exact at the bytecode-signature level
- **Behavior matrix 516/516**: decompiled code runs identically to the original under the same interpreter
- Modern syntax: PEP 695/696 type parameters, PEP 750 t-strings, PEP 649 deferred annotations, match/case, walrus, async, f-strings
- Version differences are pure data: one embedded opcode table per release, overridable via `--opcodes`
- Graceful degradation: unrecognized constructs become comment placeholders — never a crash

## Install

**Homebrew (macOS & Linux):**

```sh
brew install ejfkdev/tap/pycdc
```

**cargo, from [crates.io](https://crates.io/crates/pycdc):**

```sh
cargo install pycdc
```

**Prebuilt binaries:** raw executables (no archive wrapper) on the
[Releases](https://github.com/ejfkdev/pycdc/releases) page —
Linux / Windows x86_64 + arm64, macOS arm64 + x86_64; Linux and Windows
builds are UPX-compressed, macOS ships uncompressed.

**From source:**

```sh
cargo build --release      # -> target/release/pycdc + pycdas
cargo install --path .     # or install both binaries from a checkout
```

Every method provides both `pycdc` and `pycdas`.

## Usage

```sh
# single file -> stdout, a file, or a directory
pycdc program.pyc > program.py
pycdc program.pyc -o program.py
pycdc program.pyc -o ./outdir/

# stdin (pipelines): - reads the pyc from stdin
cat program.pyc | pycdc -

# batch: mirror a directory tree (parallel by default, -j N to control,
# -q suppresses the per-file src -> dst lines)
pycdc ./pyc-corpus -o ./src-out
pycdc ./pyc-corpus               # -> ./pyc-corpus-decompiled/
pycdc a.pyc b.pyc                # -> a.py, b.py next to the inputs
pycdc ./pyc-corpus -o ./src-out -q -j 8

# raw marshal (no pyc header) with an explicit version
pycdc -v 3.8 payload.marshal

# disassembly — same CLI surface (files, dirs, stdin, -o/-j/-q);
# also reachable as the `pycdc dis` subcommand (identical output)
pycdas program.pyc
pycdc dis program.pyc
pycdas ./pyc-corpus -o ./dis-out # -> mirrored .dis files
```

`pycdc --help`, `pycdc dis --help` and `pycdas --help` document every
flag. Exit codes: `0` success, `1` a file failed to process, `2` usage
error.

## Performance

Apple Silicon, 526 real `.pyc` files (~9.5 MB, Python 2.6–3.14 stdlib):

| Scenario | Time | Peak RSS |
|---|---|---|
| Batch, parallel (default) | **≈0.05 s** | ≈25 MB |
| Batch, serial (`-j 1`) | ≈0.34 s | ≈13 MB |
| Largest single file (74 KB, incl. startup) | ≈5.5 ms | ≈4.4 MB |
| Process startup | ≈2 ms | — |

### Real-world corpus (seven large projects, latest release tags)

`tools/fetch_realworld.sh` sparse-checks-out one directory from each of
seven projects **at its latest release tag**, compiles every `.py` to
`.pyc` (`compileall -b`), and lands the tree in `tests/realworld/`
(git-ignored — the script is the way to recreate it):

| Project (tag) | modules | serial `-j 1` | parallel (default) | recompiles | AST-identical¹ |
|---|---|---|---|---|---|
| yt-dlp (2026.08.19) | 1045 | 0.46 s | 0.08 s | **1045/1045** | 501/1045 |
| matplotlib (v3.11.2) | 253 | 0.33 s | 0.06 s | **253/253** | 60/253 |
| pandas (v3.0.5) | 1420 | 0.90 s | 0.14 s | **1420/1420** | 584/1420 |
| django (6.1.1) | 907 | 0.38 s | 0.10 s | **907/907** | 468/907 |
| sympy (1.14.0) | 1532 | 3.03 s | 1.63 s | **1532/1532** | 479/1532 |
| scikit-learn (1.9.1) | 671 | 0.48 s | 0.07 s | **671/671** | 216/671 |
| ansible (v2.21.4) | 583 | 0.27 s | 0.05 s | **583/583** | 185/583 |
| **total** | **6411** | **5.85 s** | **2.13 s** | **6411/6411 (100 %)** | 2493/6411 |

¹ strict: docstring-stripped AST equal to the original source —
equivalent normalizations (an if/else instead of a ternary, a redundant
`*()`/`**{}` around an unpack, reordered keyword arguments) count as
differences, so treat it as a shape-fidelity floor rather than an error
rate. The parse/recompile column is the acceptance bar.

One pycdc process per project: ~0.9 ms per module serial, peak RSS
≈81 MB for the whole 6.4 k-module batch. **All 6411 modules recompile**;
the last family (a dict comprehension nested inside a generator
expression's element, call arguments included) was closed by the
community PR batch. Raw data: [`benchmarks/realworld.json`](benchmarks/realworld.json),
harness: [`tools/bench_realworld.py`](tools/bench_realworld.py).


## Verification

Three independent harnesses, all runnable locally (need pyenv/uv interpreters 2.6–3.14):

| Harness | What it proves | Current |
|---|---|---|
| [`tools/verify_corpus.py`](tools/verify_corpus.py) | 520 stdlib modules: decompile → recompile with the *same* interpreter → compare bytecode signatures, fall back to normalized-AST diff | **520/520 semantic** (398 signature-exact, 0 syntax errors, 0 placeholders) |
| [`tools/run_behavior.py`](tools/run_behavior.py) | 50 behavior cases × 13 interpreters: run original vs decompiled, compare stdout + exit code | **516/516 = 100%** |
| [`tests/roundtrip.py`](tests/roundtrip.py) | fixture matrix: compile → decompile → recompile → strict bytecode compare | 49/54 strict (exceptions fixtures differ structurally, semantically equivalent) |

Per-version results live in `tests/corpus/<version>/report.json`.
A cross-tool comparison (speed, memory, output quality vs
Decompyle++, uncompyle6, decompyle3) lives in
[benchmarks/](benchmarks/README.md). Beyond
these harnesses, releases are gated by ad-hoc quality batteries: a 25-shape
syntax-family fuzz matrix (×10 interpreters), a hostile-input robustness
suite (truncated/corrupted/OOM-bomb pycs — zero crashes), and a
third-party venv smoke (six/packaging/click/attrs/pluggy). See
[docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the detailed known-gap list
and the third-party backlog.

## Project layout

```
src/    loader → marshal → bytecode → decompiler → codegen  (version.rs/opcode.rs hold the per-version data)
configs/ embedded opcode + magic tables (regenerate: tools/gen_configs.py)
tools/   config generation, corpus building, verification harnesses
tests/   Rust tests, fixtures, 520-module corpus, 48 behavior cases
```

## Acknowledgements

Design informed by [Decompyle++ (pycdc)](https://github.com/zrax/pycdc), [uncompyle6/decompyle3](https://github.com/rocky/python-decompyle3) and [xdis](https://github.com/rocky/python-xdis).

## License

[MIT](LICENSE)
