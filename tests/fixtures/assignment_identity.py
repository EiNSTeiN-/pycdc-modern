# Separate evaluations must not become one COPY-backed chained assignment.

def separate(read):
    left, right = read(), read()
    return left, right


def shared(read):
    left = right = read()
    return left, right


def separate_none():
    left, right = None, None
    return left, right


def shared_none():
    right = left = None
    return left, right
