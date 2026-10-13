# Compile with each named CPython version; the committed .pyc files are
# exercised by the existing Rust integration suite.

# Python 3.12+ inlines these comprehensions; 3.11 is the legacy control.

def list_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = [field for row in rows for field in row.get("values", [])]
    return result, row, field


def set_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = {field for row in rows for field in row.get("values", {})}
    return result, row, field


def dict_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = {field: len(field) for row in rows for field in row.get("values", {})}
    return result, row, field


def nested_list(rows):
    row = "saved-row"
    field = "saved-field"
    result = [[field for field in row.get("values", [])] for row in rows]
    return result, row, field


def nested_set(rows):
    row = "saved-row"
    field = "saved-field"
    result = [{field for field in row.get("values", {})} for row in rows]
    return result, row, field


def nested_dict(rows):
    row = "saved-row"
    field = "saved-field"
    result = [{field: len(field) for field in row.get("values", {})} for row in rows]
    return result, row, field


def subscript(rows):
    row = "saved-row"
    field = "saved-field"
    result = [field for row in rows for field in row["values"]]
    return result, row, field


def no_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = [field for row in rows for field in row.get("values")]
    return result, row, field


def tuple_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = [field for row in rows for field in row.get("values", ())]
    return result, row, field
