# MIN_VERSION: 3.12


def select(rows):
    return [max(0.0, float(row.get("x") or 0.0)) for row in rows]


def calls(rows):
    return [row.first() or row.second() for row in rows]


def and_calls(rows):
    return [row.first() and row.second() for row in rows]


print(select([{}, {"x": None}, {"x": 0}, {"x": -2}, {"x": 7}]))
class Row:
    def __init__(self, value):
        self.value = value
    def first(self):
        print("first", self.value)
        return self.value
    def second(self):
        print("second", self.value)
        return 9
print(calls([Row(0), Row(3)]))
print(and_calls([Row(0), Row(3)]))
