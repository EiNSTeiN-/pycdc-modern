# MIN_VERSION: 3.13


def positional(rows, factory):
    return tuple(factory(*row) for row in rows)


def keywords(rows, factory):
    return tuple(factory(**dict(row)) for row in rows)


def both(rows, factory):
    return tuple(factory(*row[0], **row[1]) for row in rows)


def factory(*args, **kwargs):
    return args, sorted(kwargs.items())
print(positional([[1, 2], [3]], factory))
print(keywords([{"a": 1}, {"b": 2}], factory))
print(both([([1], {"a": 2})], factory))
