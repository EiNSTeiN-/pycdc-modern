# MIN_VERSION: 3.12
import asyncio

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


def work(stage):
    print(stage)
    if stage == "first":
        raise ValueError(stage)
    return 9
print(tuple(synchronous(work)))
async def consume():
    result = []
    async for value in asynchronous(work):
        result.append(value)
    return result
print(asyncio.run(consume()))
