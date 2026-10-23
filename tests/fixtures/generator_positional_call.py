def select(rows, factory):
    return tuple(factory(*row) for row in rows)
