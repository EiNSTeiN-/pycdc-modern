# Compile with each named CPython version; the committed .pyc files are
# exercised by the existing Rust integration suite.

# Python 3.12+ inlines these comprehensions; 3.11 is the legacy control.

def unpack4(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [a + b + c + d for rows in groups for a, b, c, d in rows]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack_list(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c) for a, b in groups for c, d in b]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack_set(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = {(a, c) for a, b in groups for c, d in b}
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack_dict(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = {a: c for a, b in groups for c, d in b}
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack6(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c, e) for a, b in groups for c, d in b for e, f in d]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def simple(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c) for a in groups for c in a]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def mixed(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c) for key, a in groups for c in a]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def mixed_inner(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c) for a in groups for key, c in a]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after
