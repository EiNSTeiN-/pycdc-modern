# MIN_VERSION: 3.14


class Always:
    "Documented class."
    if True:
        amount: int = 3
        label: str = "ready"

    def read(self) -> int:
        return self.amount


def select(enabled, values, default):
    class Result:
        if True:
            amount: int = 3
        if enabled:
            label: str = "ready"
        for value in values:
            limit: int = default(value)
    return Result


print(Always.__annotate__.__code__.co_freevars)
print(sorted(Always.__annotations__))
def default(value):
    print("default", value)
    return value
print(sorted(select(False, [], default).__annotations__))
print(sorted(select(True, [3, 4], default).__annotations__))
