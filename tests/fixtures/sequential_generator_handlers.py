# Compile with each named CPython version; the committed .pyc files are
# exercised by the existing Rust integration suite.

# The frame-wide StopIteration intrinsic is emitted starting in Python 3.12.

def synchronous(work):
    try:
        yield work("first")
    except ValueError:
        yield 2
    yield 3
    try:
        yield work("last")
    except KeyError:
        yield 5
    yield 6


async def asynchronous(work):
    try:
        yield work("first")
    except ValueError:
        yield 2
    yield 3
    try:
        yield work("last")
    except KeyError:
        yield 5
    yield 6
