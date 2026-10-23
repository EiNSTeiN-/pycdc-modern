# MIN_VERSION: 3.13


def select(call, before, first, second, last, after):
    return call(before(), (first() and second()) or last(), after())


def alternatives(a, b, c, d, e):
    return bool((a and b) or c or d or e)


def before():
    print("before")
    return 1
def first():
    print("first")
    return 0
def second():
    print("second")
    return 2
def last():
    print("last")
    return 3
def after():
    print("after")
    return 4
def call(*args):
    return args
print(select(call, before, first, second, last, after))
print(alternatives(1, 0, 0, 0, 5))
print(alternatives(1, 2, 0, 0, 0))
