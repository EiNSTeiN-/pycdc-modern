# MIN_VERSION: 3.12


def methods_equal(rows, wanted):
    return [row.tag for row in rows if row.value == wanted if row.ready() if row.final()]


def methods_unequal(rows, wanted):
    return [row.tag for row in rows if row.value != wanted if not row.ready() if row.final()]


class Row:
    def __init__(self, tag, value, ready):
        self.tag = tag
        self.value = value
        self.available = ready
    def ready(self):
        print("ready", self.tag)
        return self.available
    def final(self):
        print("final", self.tag)
        return True
rows = [Row("a", 1, True), Row("b", 2, True), Row("c", 1, False)]
print(methods_equal(rows, 1))
print(methods_unequal(rows, 2))
