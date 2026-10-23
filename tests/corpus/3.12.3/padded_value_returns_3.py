# Generate .pyc files with the matching CPython 3.11–3.14 interpreter:
# python tools/compile_padded_value_returns.py
# Each RETURN_VALUE receives 1, 3 or 9 NOPs, with jumps and exception
# boundaries relocated. Padding never constructs a new return value.

def synchronous(read, build):
    try:
        item = read()
    except ValueError:
        return build("missing")
    return build(item)


async def asynchronous(read, build):
    try:
        item = await read()
    except ValueError:
        return build("missing")
    return build(item)
