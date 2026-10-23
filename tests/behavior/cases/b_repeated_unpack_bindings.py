# MIN_VERSION: 3.13


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


rows = [(1, 2, 3, 4), (5, 6, 7, 8)]
print(underscore_loop(rows))
print(underscore_list(rows))
nested = [(1, (2, 3)), (4, (5, 6))]
print(nested_loop(nested))
print(nested_list(nested))
