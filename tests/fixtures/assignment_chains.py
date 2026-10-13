# COPY-backed chains; CPython 3.13+ can fuse the final two local stores.

def three(read):
    a = b = c = read()
    return a, b, c


def four(read):
    a = b = c = d = read()
    return a, b, c, d


def five(read):
    a = b = c = d = e = read()
    return a, b, c, d, e


def six(read):
    a = b = c = d = e = f = read()
    return a, b, c, d, e, f


def three_none():
    a = b = c = None
    return a, b, c


def four_none():
    a = b = c = d = None
    return a, b, c, d


def five_none():
    a = b = c = d = e = None
    return a, b, c, d, e


def six_none():
    a = b = c = d = e = f = None
    return a, b, c, d, e, f
