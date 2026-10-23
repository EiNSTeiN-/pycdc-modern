# Versioned .pyc files are consumed by tests/integration.rs.

# The finite else-span guard applies to Python 3.11+.

async def awaited(owner):
    value = None
    active = owner.active
    if active:
        value = 1
    else:
        row = await owner.fetch()
        if row and row[0] is not None:
            value = float(row[0])
    owner.record(value)
    return value


async def synchronous(owner):
    value = None
    active = owner.active
    if active:
        value = float(1)
    else:
        row = owner.fetch()
        if row and row[0] is not None:
            value = 2
    owner.record(value)
    return value


async def attribute(owner):
    value = None
    active = owner.active
    if active:
        value = float(active['total'])
    else:
        row = owner.row
        if row and row[0] is not None:
            value = float(row[0])
    owner.record(value)
    return value


async def following_else_work(owner):
    value = None
    active = owner.active
    if active:
        value = 1
    else:
        row = await owner.fetch()
        if row and row[0] is not None:
            value = 2
        owner.record('queried')
    owner.record(value)
    return value


async def independent(owner):
    value = None
    row = None
    if owner.active:
        value = 1
    else:
        row = await owner.fetch()
    if row and row[0] is not None:
        value = 2
    return value
