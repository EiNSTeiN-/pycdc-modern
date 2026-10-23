# MIN_VERSION: 3.9
import asyncio

async def awaited(read):
    result = []
    for item in await read():
        result.append(item)
    return result


async def read():
    print("read")
    return [1, 2, 3]
print(asyncio.run(awaited(read)))
