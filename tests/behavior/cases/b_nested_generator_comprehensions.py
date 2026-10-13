# MIN_VERSION: 3.12


def dictionary(rows):
    return tuple({key: row[key] for key in row} for row in rows)


def call_arguments(rows, collect):
    return tuple(collect([value * 2 for value in row]) for row in rows)


def filtered(rows):
    return tuple({key: row[key] for key in row if key} for row in rows if row)


def unpacked(rows, columns):
    return tuple({key: value for key, value in zip(columns, row) if key} for row in rows)


def collect(values):
    print("collect", values)
    return sum(values)
print(dictionary([{"a": 1, "b": 2}, {}, {"c": 3}]))
print(call_arguments([[1, 2], [], [3]], collect))
print(filtered([{}, {"": 0, "a": 1}]))
print(unpacked([[1, 2], [3, 4]], ["a", "b"]))
