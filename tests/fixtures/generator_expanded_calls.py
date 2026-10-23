# CALL_FUNCTION_EX changes stack layout in CPython 3.13 and 3.14.

def positional(rows, factory):
    return tuple(factory(*row) for row in rows)


def keywords(rows, factory):
    return tuple(factory(**dict(row)) for row in rows)


def both(rows, factory):
    return tuple(factory(*row[0], **row[1]) for row in rows)
