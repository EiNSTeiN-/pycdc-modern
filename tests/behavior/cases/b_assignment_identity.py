# MIN_VERSION: 3.9


def separate(read):
    left, right = read(), read()
    return left, right


def shared(read):
    left = right = read()
    return left, right


events = []
def read():
    events.append("read")
    return len(events)

print(separate(read), events)
print(shared(read), events)
