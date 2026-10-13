def rating_lookup(values):
    for value in values:
        if not value.rating < 10:
            continue
        coordinator = value.coordinator
        if coordinator is None:
            continue
        return coordinator


def dictionary_lookup(rows):
    for row in rows:
        if not isinstance(row, dict):
            continue
        coordinator = row.get("coordinator")
        if coordinator is None:
            continue
        return coordinator


def none_lookup(rows):
    for row in rows:
        if row is None:
            continue
        coordinator = row.coordinator
        if coordinator is None:
            continue
        return coordinator


def comprehension(rows):
    return [row.get("coordinator") for row in rows if isinstance(row, dict)]

