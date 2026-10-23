# Versioned .pyc files are consumed by tests/integration.rs.

# The long functions require EXTENDED_ARG before FOR_ITER.

def size_1(rows, work):
    result = []
    for row in rows:
        try:
            work(row)
        except ValueError:
            continue
        result.append(row)
    return result


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


def size_60(rows, work):
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
