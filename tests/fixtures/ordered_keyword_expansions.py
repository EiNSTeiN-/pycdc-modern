def direct(fn, first, second):
    return fn(1, fixed=2, **first, **second)


def interleaved(fn, first, second):
    return fn(1, **first, fixed=2, **second)


def mappings(fn, first, second):
    return fn(1, **first, **second)


def dictionary(fn, first, second):
    return fn(1, **{"fixed": 2, **first, **second})


def non_identifier(fn, first, second):
    return fn(1, **{"my col": 2, **first, **second})


def reserved_word(fn, first, second):
    return fn(1, **{"class": 2, **first, **second})


def repeated_literal(fn, first, second):
    return fn(1, **{"fixed": 2, "fixed": 3, **first, **second})


def effectful(fn, get_first, get_second):
    return fn(1, fixed=2, **get_first(), **get_second())
