# MIN_VERSION: 3.13


def case_0(value, build, other):
    return build("reject" if value else "accept", amount=0)


def case_1(value, build, other):
    return build("prefix", amount=0 if value else 1)


def case_9(value, build, other):
    return build("prefix", amount=1 if value else 2, last=other(value))


def build(*args, **kwargs):
    print("build", args, sorted(kwargs.items()))
    return args
def other(value):
    print("other", value)
    return 8
print(case_0(False, build, other))
print(case_0(True, build, other))
print(case_1(False, build, other))
print(case_9(True, build, other))
