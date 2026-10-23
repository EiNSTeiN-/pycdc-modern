def list_positive_separate(values):
    return [value for value in values if isinstance(value, str) if value]


def list_positive_joined(values):
    return [value for value in values if isinstance(value, str) and value]


def list_negative_separate(values):
    return [value for value in values if not isinstance(value, str) if value]


def list_negative_joined(values):
    return [value for value in values if not isinstance(value, str) and value]


def set_positive_separate(values):
    return {value for value in values if isinstance(value, str) if value}


def set_positive_joined(values):
    return {value for value in values if isinstance(value, str) and value}


def set_negative_separate(values):
    return {value for value in values if not isinstance(value, str) if value}


def set_negative_joined(values):
    return {value for value in values if not isinstance(value, str) and value}


def dict_positive_separate(values):
    return {value: value for value in values if isinstance(value, str) if value}


def dict_positive_joined(values):
    return {value: value for value in values if isinstance(value, str) and value}


def dict_negative_separate(values):
    return {value: value for value in values if not isinstance(value, str) if value}


def dict_negative_joined(values):
    return {value: value for value in values if not isinstance(value, str) and value}


def methods_equal(rows, wanted):
    return [row.tag for row in rows if row.value == wanted if row.ready() if row.final()]


def methods_unequal(rows, wanted):
    return [row.tag for row in rows if row.value != wanted if not row.ready() if row.final()]


def broken_lines(values):
    return [value
            for value in values
            if isinstance(value, str)
            if value]
