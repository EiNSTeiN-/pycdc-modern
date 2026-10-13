# MIN_VERSION: 3.12


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


class Rating:
    def __init__(self, value):
        self.value = value
    def __lt__(self, limit):
        print("lt", self.value, limit)
        return self.value < limit
    def __ge__(self, limit):
        raise AssertionError("comparison must not be inverted")
class Row:
    def __init__(self, rating, coordinator):
        self.rating = Rating(rating)
        self.coordinator = coordinator
print(rating_lookup([Row(float("nan"), 8), Row(3, None), Row(4, 0)]))
print(dictionary_lookup([1, {}, {"coordinator": False}]))
