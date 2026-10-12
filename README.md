# pycdc-rs

This fork extends [ejfkdev/pycdc](https://github.com/ejfkdev/pycdc) for several
CPython 3.14 constructs encountered during static source recovery:

- Python 3.14 generator elements reuse the main parser for nested inline
  comprehensions, locals-plus slots and closure captures, including nested
  generator calls with multiple captured cells.
- Expanded generator calls consume Python 3.14's unconditional kwargs slot.
- Await cleanup trampolines and fragmented exception regions stay out of source
  `try` blocks; returns remain inside their enclosing async context and `finally`.
- Split exception/success/finally suites are reunited when the outer success
  suite belongs to the single inner handler-bearing try. No statements are
  replaced with synthetic exception behavior; candidates still require
  separate bytecode verification.
- Short-circuit values inside comprehension elements remain values rather than
  being mistaken for filters.
- Chained inline-comprehension filters keep each guard's original polarity.
  An accepting jump can land at the next guard rather than directly at the
  append. The exact fall-through padding/back-edge span identifies that path;
  general forward regions and classic skip jumps keep their existing handling.
  Owned list/set/dictionary fixtures compare exact instruction and exception
  bytes, including positive/negative guards and conjunctions versus successive
  filters. Additional fixtures check equality hooks, calls, short-circuit
  evaluation and errors across three guards.
- Filtered Python 3.14 generators retain `and`/`or` element values and rejection
  guards. The arm's first discard looks past NOT_TAKEN padding; an inverted
  continue guard becomes the generator filter without reverting to the legacy
  expression simulator. Owned fixtures compare exact generator instruction and
  exception bytes, false/None/true values, and truth-test/getter call order.
- Independent for-loop lookup guards retain their continue branches and
  assignment/return scope. A forward success jump around one back edge is
  retained as rejection only when its suite assigns the local checked by a
  later independent None guard and returned afterward. Its success suite is
  not incorrectly bounded by that later guard's back edge. Protected suites,
  inline comprehensions and nested while loops keep their separate handling.
  Owned fixtures include non-dictionary rows, missing/None/false results,
  side-effecting getters and an object whose truth conversion raises.
  Comparison operators remain unchanged when the rejection polarity is
  inverted; NaN and rich-comparison hooks receive dedicated behavior tests.
- Large dictionary displays inside comprehensions keep their own `MAP_ADD 1`
  operations.
- Shared rejection guards preserve missing-value and ordinary truth tests,
  negated chained comparisons, and shared continue/return blocks. Rejections
  can construct results with positional/keyword arguments. Guard generators
  reuse the main parser and retain lexical captures and lazy consumption.
  Shared raises retain their exception expression and optional explicit
  cause, with the exact required stack operands. A recognized comparison
  cleanup trampoline stays off the success path into a later predicate.
  Formatted messages retain conversions and dynamic specifications through
  the existing f-string model; bare reraises, cleanup and general branches
  remain outside this reconstruction. Owned fixtures compare instruction
  and exception bytes, rich-comparison/format hooks, NaN, constructor errors,
  cause evaluation and exception metadata.
  Chained middle expressions
  are evaluated once, and NaN comparisons retain their original polarity.
  Extending an accumulated comparison chain retains every earlier operand;
  distinct calls in explicitly separate comparisons remain distinct.
- Exception-return tail matching requires a genuine independent value head.
  Masked padding is never treated as a value-building tail or used to swallow
  a later success response. Owned fixtures cover padded sequential handlers
  and a genuine sunk value tail with an `else` path.
- A Python 3.14 padded `RETURN_VALUE` after a protected calculation consumes
  the live value already on the parser stack. The existing tail recognizer
  accepts only padding and one unwalked return; the value repair additionally
  requires exactly one expression on the stack and no with protocol. It does
  not re-evaluate the calculation or supply a result for an empty stack.
  Owned fixtures cover call, attribute, tuple and dictionary results with
  several padding widths, false values, handled errors, fallback errors and
  base exceptions. An explicit bare-return fixture keeps its side effect.
- Compiler StopIteration routes remain frame machinery when bounding lexical
  handler chains. Shared continuations after handled exceptions stay outside
  those chains, preserving later generator expressions and sequential work.
- Deferred class annotations retain their registration gates on recompilation.
  A constant-folded source block preserves the compiler's cell and guarded
  annotation entries without introducing a runtime condition. Consecutive
  fields share one block. Actual conditions, loops, default-value calls and
  deferred annotation lookups are covered by owned behavior regressions.
- Repeated local unpack targets retain the surviving binding's spelling when
  earlier stores were elided as POP_TOP. The bounded lookup stops at nested
  unpacking, side effects and control flow; real underscore stores are retained.
  Owned generator fixtures compare exact instruction/exception bytes, normal
  values, surviving targets and unpack failures without extra discard locals.

Build with `cargo build --release --locked`. In addition to `cargo test`, run
`PYCDC_BINARY=target/release/pycdc python3.14 tests/python314_roundtrip.py -v`.
These checks compile and execute only the original small fixtures in that file.
The verification figures below describe the upstream project's corpus; this
fork's changes have separate regression coverage and do not imply that arbitrary
decompilations are equivalent to their inputs.

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
| yt-dlp (2026.08.19) | 1045 | 0.93 s | 0.12 s | **1045/1045** | 500/1045 |
| matplotlib (v3.11.2) | 253 | 0.47 s | 0.09 s | **253/253** | 59/253 |
| pandas (v3.0.5) | 1420 | 1.35 s | 0.21 s | 1419/1420 | 582/1420 |
| django (6.1.1) | 907 | 0.67 s | 0.16 s | **907/907** | 467/907 |
| sympy (1.14.0) | 1532 | 3.68 s | 1.85 s | **1532/1532** | 479/1532 |
| scikit-learn (1.9.1) | 671 | 0.71 s | 0.10 s | 669/671 | 216/671 |
| ansible (v2.21.4) | 583 | 0.35 s | 0.06 s | **583/583** | 185/583 |
| **total** | **6411** | **8.16 s** | **2.59 s** | **6408/6411 (99.95 %)** | 2488/6411 |

¹ strict: docstring-stripped AST equal to the original source —
equivalent normalizations (an if/else instead of a ternary, a redundant
`*()`/`**{}` around an unpack, reordered keyword arguments) count as
differences, so treat it as a shape-fidelity floor rather than an error
rate. The parse/recompile column is the acceptance bar.

One pycdc process per project: ~1.0 ms per module serial, peak RSS
≈99 MB for the whole 6.4 k-module batch. The three remaining modules are one shape: a dict comprehension
nested inside a generator expression's element (call arguments
included) — marked incomplete, never a crash. Raw data: [`benchmarks/realworld.json`](benchmarks/realworld.json),
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

### Python 3.14 handler and comprehension cleanup

The recovery fork retains unnamed exception-handler return values across NOP,
NOT_TAKEN, and CACHE padding. Its post-POP_EXCEPT scan continues through padding
before deciding whether the handler ends in a return; real jumps and handler
boundaries remain significant. Owned async fixtures cover successful saves,
custom failures, ordinary failures, and cancellation with 1, 3, and 9 NOPs.

Within a PEP 709 inline comprehension, reconstructing an unpacked target
consumes its modeled iterator. The decoder restores that slot after completing
the target, matching the simple-target path. VM iterator cleanup can then run
normally without discarding the accumulator. Four- and six-target list/set/dict
fixtures retain exact bytecode and exception tables, saved target variables,
ordinary loops afterward, and iteration/unpacking errors. Mixed simple/unpacked
target fixtures cover the counterexample to blanket inner cleanup suppression.

The first 0.6.14 corpus trial gained 97 units but lost five previous matches.
Its blanket inner-cleanup suppression was rejected at the retention gate, even
though its initial owned tests and CI passed. The 0.6.15 correction models the
missing iterator instead. Never publish a recovered-source checkpoint based
only on net gains or successful tests; require set-wise retention as well.

### Python 3.14 expression identity and exact loop targets

The 0.6.16 investigation checkpoint fixes five independently reproduced defects:

- Consecutive assignment stores use evaluated-value identity, rather than AST
  equality, to recognize a true chained assignment. Two equal calls remain two
  evaluations; COPY-derived chains still evaluate once.
- Actual slice constants in multi-axis indexes become colon syntax, including
  constant tuples. Runtime `slice(...)` calls retain their global lookup, which
  may be shadowed or have effects.
- A generator's real nonlocal cell declarations no longer force a legacy
  expression fallback that corrupts value-preserving AND/walrus expressions.
  Unrelated nonlocals and global declarations do not qualify.
- The expression-region simulator retains a walrus assignment only when its
  stored value is a COPY of the surviving stack value. Ordinary assignments
  remain statements.
- Modern loop backedges may target a FOR_ITER's EXTENDED_ARG prefix. The
  original bytes must prove a contiguous, aligned prefix; a missing decoded
  instruction alone cannot distinguish a prefix from an inline CACHE gap.

Owned validation passes 35 Rust cases and 43 CPython 3.14 behavior methods,
including independent evaluation errors, true chains, shadowed slice globals,
cell short circuit, and large-loop handler continuations. Full-corpus source
publication still requires an independent set-wise retention gate; these test
results do not establish recovery of the remaining application units.


The 0.6.17 recovery work fixes ordinary FOR_ITER loops over awaited collections,
fused stores at the end of longer COPY assignment chains, nested conditional
values in comprehension then-arms, and padded None handler tails. The narrowed
carried-return reconstruction keeps the original call protected without consuming
following branches; owned controls retain unprotected/else calls and timezone
conversion errors. The owned Python 3.14 suite has 47 methods, including exact
code/exception comparisons on ordinary fixtures, paired errors/cancellation,
mutable identity, and padded timestamp scope controls. Full protected-corpus
retention remains a separate required publication gate.

The 0.6.18 development work retains separate ordered keyword expansions in
`CALL_FUNCTION_EX`. `fn(fixed=2, **first, **second)` must reject duplicate keys
before evaluating later expansions; a dictionary intentionally constructed with
updates must keep its overwrite semantics. Merge boundaries are retained when
an expanded argument is itself a constructed dictionary, and unnamed keyword
entries render with `**`. The Python 3.14 suite passes 48 methods, including
direct expansions, named arguments between expansions, intentional dictionary
updates, invalid mappings/keys, and factory evaluation order. The 35 Rust tests
also pass. Protected-corpus coverage and the stable branch remain at the
preceding checkpoint until a complete unchanged-input retention audit passes.

The 0.6.19 development work reconstructs positive comparison chains guarding
inline-comprehension ternary values. Both arms must be pure value regions with
the original forward merge and false-arm cleanup; only the COPY-retained middle
operand is removed, preserving prefix arithmetic and single evaluation of
side-effecting comparisons. Genuine comprehension filters retain their path.
Sunk constant-return async context exits preserve the later normal exit slot
even when the first protocol call is beyond the final protected fragment.
The arm must contain the bounded return protocol. Expected underflow for the
unmodeled exit callable keeps the clean state from before that call, including
any earlier incomplete diagnostic. The Python 3.14 suite has 50 methods with
120 paired async return/error/suppression/cancellation cases and chained
dict-key/value/list arithmetic and side-effect controls. Full corpus retention
remains required before advancing the stable branch or claiming new coverage.

The complete `substantive-values-01` audit with unpacker 0.4.27 passed that
gate: 13,821/14,291 application units match, 120 candidate modules are complete,
and raw/composite views each gain 14 units with no lost matches. Backend 0.6.19
has therefore advanced to the stable branch; these figures include the source
repair trials and are not a claim of complete application recovery.

Version 0.6.20 development folds a computed context return while its With
block is still open. Out-of-line loop handlers can extend that region beyond
the normal return tail; simulating its exit slots then emitted a bogus call
to None and discarded the returned result. The existing pure exit-protocol
matcher must prove the complete tail before the open With can close and carry
its value. Owned synchronous and asynchronous loop fixtures verify exact
instructions and exception tables for list, scalar and mapping returns, with
126 paired normal, rejected-row, body-error, entry/exit-error, suppression and
cancellation cases. A complete application retention gate remains required
before promoting this development version.

The `open-context-return-01` audit passed that gate: 13,824/14,291 application
units match, with three gains and no losses in either raw or composite views.
Version 0.6.20 is now stable. All 274 modules were independently audited;
identical native output and diagnostics allowed 269 unchanged source-generation
inputs to be reused with the frozen source API, while five were regenerated.

Version 0.6.21 development distinguishes real inline-comprehension accumulators
from empty containers consumed as call defaults. Modern accumulator setup must
be followed by the compiler's `SWAP 2`; a preceding `row.get("values", {})`
does not create a nested comprehension level. Legacy setup keeps its separate
handling. Nine owned list/set/mapping and nested-comprehension fixtures compare
exact instruction and exception bytes and 45 paired normal/error cases, including
preserved outer locals and genuine empty/default-free iterable controls. The
Python 3.14 suite now contains 52 methods. Full application retention remains
required before advancing this version to the stable branch.

The complete `comprehension-defaults-01` audit passed that gate: raw and
composite source each gained one unit with no losses across 274 modules,
reaching 13,825/14,291 composite matches. Version 0.6.21 is stable. The
subsequent source-API 0.4.28 `shared-guards-01` audit adds 14 further units
without losses, reaching 13,839/14,291 and 123 complete candidate modules.

Version 0.6.22 development distinguishes an enclosing for-loop back edge
from a rotated while condition when reconstructing disjunctions. A known
nearest For header can terminate the existing arm; backward edges into a
condition or nearest While retain the previous veto. Eleven owned layouts
check exact instruction and exception bytes and 41 paired short-circuit,
missing/nonnumeric, break/else, continue and genuine while cases.

Computed returns spanning nested context exits retain one carried value
across the complete modern SWAP/None/call/await/pop groups, bounded by known
exit slots. The return belongs in the innermost closed context body when
the enclosing contexts remain open. Those outer blocks and slots remain
available to their exception-suppression paths; closing them prematurely
emits stray protocol calls. Owned one/two/three-level synchronous and async
fixtures cover scalar, tuple, mapping and awaited results, with 168 paired
normal, entry/body/exit error, suppression and cancellation cases. Separate
return-after-inner-context controls keep their original placement.

All 54 Python 3.14 methods, 35 Rust tests and 192 unpacker cases pass locally
(one unpacker case remains an existing expected failure). Complete application
retention remains required before stable promotion or new coverage claims.

The complete 0.6.22 corpus gate passed: all 274 modules retain every prior
raw and composite match, gaining 11 raw/10 composite units to reach
13,849/14,291 composite matches. Version 0.6.22 is stable. The independently
audited source API 0.4.29 then gains 39 more with zero losses, reaching
13,888/14,291 and 132 complete candidate modules; comparison rules are
unchanged throughout.

Version 0.6.23 development retains guarded work inside a modern Else whose
finite end is authoritatively established by the immediately preceding
unconditional then-arm skip. An inner condition sharing that merge does not
close the Else early. The old behavior could eject a queried row's guard and
read that local on the other branch before assignment. Inferred boundaries,
legacy versions and TryElse keep their prior handling.

Eighteen owned literal/call/subscript and optional-fallback layouts compare
exact instructions and exception tables. Five guard/query controls and one
genuinely independent row guard keep their separate ownership. Three methods
cover 900 paired active/inactive, missing/empty/invalid row, query failure and
cancellation cases. All 57 Python behavior methods and 35 Rust tests pass.
The full 274-module retention audit remains required before stable promotion
or any new application coverage claim.

Version 0.6.24 development consumes the exact saved COPY operand when a
complete modern AND-in-OR value chain folds, preserving the callee/NULL and
other argument prefix. Remaining OR links qualify only with their bounded
COPY/TO_BOOL/true-jump-to-the-same-merge protocol and matching POP cleanup.
Different branch targets and arbitrary statement control flow do not qualify.
The old behavior left an extra argument or used None as a callee. Nine owned
compound/simple/assigned value layouts now retain exact instruction and
exception bytes, including method/subscript/call operands and multiple OR
tails. Prefix controls preserve a genuinely separate first argument, ordered
callbacks, and failure paths. Two methods cover 113 paired cases; the full
Python behavior suite has 59 methods. Full corpus retention is still required
before stable promotion or application coverage claims. No comparison rule
is relaxed.
