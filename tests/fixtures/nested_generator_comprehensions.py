def dictionary(rows):
    return tuple({key: row[key] for key in row} for row in rows)


def list_elements(rows):
    return tuple([value * 2 for value in row] for row in rows)


def set_elements(rows):
    return tuple({value * 2 for value in row} for row in rows)


def call_arguments(rows, collect):
    return tuple(collect([value * 2 for value in row]) for row in rows)


def filtered(rows):
    return tuple({key: row[key] for key in row if key} for row in rows if row)


def unpacked(rows, columns):
    return tuple({key: value for key, value in zip(columns, row) if key} for row in rows)
