# MIN_VERSION: 3.11
import asyncio

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


class Owner:
    def __init__(self, active, row):
        self.active = active
        self.row = row
    async def fetch(self):
        print("fetch", self.row)
        return self.row
    def record(self, value):
        print("record", value)
print(asyncio.run(awaited(Owner(True, (9,)))))
print(asyncio.run(awaited(Owner(False, (9,)))))
print(asyncio.run(awaited(Owner(False, (None,)))))
print(asyncio.run(awaited(Owner(False, None))))
