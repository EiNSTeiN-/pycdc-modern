def synchronous(read, build):
    try:
        item = read()
    except ValueError:
        return build('missing')
    return build(item)

async def asynchronous(read, build):
    try:
        item = await read()
    except ValueError:
        return build('missing')
    return build(item)

