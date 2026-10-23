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
