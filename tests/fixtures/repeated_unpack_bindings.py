# Versioned .pyc files are consumed by tests/integration.rs.

# CPython 3.13 starts replacing overwritten stores with POP_TOP.

def repeated_loop(values):
    result = []
    for value, discarded, discarded, discarded in values:
        result.append(value is not None)
    return result


def repeated_list(values):
    return [value is not None for value, discarded, discarded, discarded in values]


def underscore_loop(values):
    result = []
    for value, _, discarded, discarded in values:
        result.append((value, discarded, _))
    return result


def underscore_list(values):
    return [(value, discarded, _) for value, _, discarded, discarded in values]


def nested_loop(values):
    result = []
    for value, (discarded, discarded) in values:
        result.append((value, discarded))
    return result


def nested_list(values):
    return [(value, discarded) for value, (discarded, discarded) in values]
