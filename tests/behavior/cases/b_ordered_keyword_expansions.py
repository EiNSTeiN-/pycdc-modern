# MIN_VERSION: 3.9


def direct(fn, first, second):
    return fn(1, fixed=2, **first, **second)


def dictionary(fn, first, second):
    return fn(1, **{"fixed": 2, **first, **second})


def effectful(fn, get_first, get_second):
    return fn(1, fixed=2, **get_first(), **get_second())


def fn(*args, **kwargs):
    print("call", args, sorted(kwargs.items()))
def first():
    print("first")
    return {"fixed": 7}
def second():
    print("second")
    return {"extra": 8}
try:
    direct(fn, {"fixed": 7}, {"extra": 8})
except TypeError:
    print("duplicate")
dictionary(fn, {"fixed": 7}, {"extra": 8})
try:
    effectful(fn, first, second)
except TypeError:
    print("duplicate before second")
