def select(rows):
    return [max(0.0, float(row.get("x") or 0.0)) for row in rows]


def element_or(rows):
    return [row[1] or 0 for row in rows]


def element_and(rows):
    return [row[1] and 7 for row in rows]


def set_values(rows):
    return {row[1] or 0 for row in rows}


def dict_values(rows):
    return {row[0]: row[1] and 7 for row in rows}


def calls(rows):
    return [row.first() or row.second() for row in rows]


def and_calls(rows):
    return [row.first() and row.second() for row in rows]


def single_filter(rows):
    return [row[1] for row in rows if row[0]]


def filtered_value(rows):
    return [row[1] or 0 for row in rows if row[0]]


def ternary_control(rows):
    return [row[1] if row[0] else 0 for row in rows]
