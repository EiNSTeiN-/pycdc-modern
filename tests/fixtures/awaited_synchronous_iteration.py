# Versioned .pyc files are consumed by tests/integration.rs.

# async/await syntax starts in Python 3.5.

async def awaited(read):
    result = []
    for item in await read():
        result.append(item)
    return result


async def asynchronous(read):
    result = []
    async for item in read():
        result.append(item)
    return result


async def sync(read):
    result = []
    for item in read():
        result.append(item)
    return result
