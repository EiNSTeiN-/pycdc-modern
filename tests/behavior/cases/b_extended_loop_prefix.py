# MIN_VERSION: 3.11


def size_30(rows, work):
    result = []
    for row in rows:
        try:
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
            work(row)
        except ValueError:
            continue
        result.append(row)
    return result


calls = []
def work(row):
    calls.append(row)
    if row == 2:
        raise ValueError(row)
print(size_30([1, 2, 3], work))
print(calls)
