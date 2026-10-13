# MIN_VERSION: 3.12


def list_default(rows):
    row = "saved-row"
    field = "saved-field"
    result = [field for row in rows for field in row.get("values", [])]
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


print(list_default([{}, {"values": ["a", "bb"]}, {}]))
print(dict_default([{}, {"values": {"a": 1, "bb": 2}}, {}]))
print(nested_list([{}, {"values": ["a"]}, {}]))
