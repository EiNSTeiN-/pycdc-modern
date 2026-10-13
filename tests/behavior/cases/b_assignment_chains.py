# MIN_VERSION: 3.13


def three(read):
    a = b = c = read()
    return a, b, c


def six(read):
    a = b = c = d = e = f = read()
    return a, b, c, d, e, f


def three_none():
    a = b = c = None
    return a, b, c


events = []
def read():
    events.append("read")
    return len(events)

print(three(read), events)
print(six(read), events)
print(three_none())
