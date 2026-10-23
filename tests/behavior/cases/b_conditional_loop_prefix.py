# MIN_VERSION: 3.11

# Attribute loads make FOR_ITER require EXTENDED_ARG on Python 3.12+.
# Conditional branches lead to adjacent back edges targeting that prefix.
def process(rows, work):
    success = True
    for row in rows:
        if row.is_file:
            if not work(
                "file", row.ok,
                row.a, row.b, row.c, row.d, row.e, row.f,
                row.g, row.h, row.i, row.j, row.k, row.l,
            ):
                success = False
        else:
            if not work(
                "directory", row.ok,
                row.a, row.b, row.c, row.d, row.e, row.f,
                row.g, row.h, row.i, row.j, row.k, row.l,
            ):
                success = False
    return success


class Row:
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    l = 12

    def __init__(self, is_file, ok):
        self.is_file = is_file
        self.ok = ok


def work(kind, ok, *values):
    calls.append((kind, ok, values))
    return ok


for outcomes in [
    [],
    [(True, True)],
    [(True, False)],
    [(False, True)],
    [(False, False)],
    [(True, True), (False, True)],
    [(False, True), (True, True)],
    [(True, False), (False, True), (True, True)],
    [(False, False), (True, True), (False, True)],
]:
    calls = []
    rows = [Row(is_file, ok) for is_file, ok in outcomes]
    print(process(rows, work))
    print(calls)
