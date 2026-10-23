if True:
    module_count: int = 5


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


def loop_only(values, default):
    class Result:
        for value in values:
            amount: int = default(value)
    return Result
