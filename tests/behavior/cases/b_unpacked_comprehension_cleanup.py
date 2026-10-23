# MIN_VERSION: 3.12


def unpack4(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [a + b + c + d for rows in groups for a, b, c, d in rows]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack_list(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c) for a, b in groups for c, d in b]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


def unpack6(groups):
    a, b, c, d, e, f = 10, 20, 30, 40, 50, 60
    result = [(a, c, e) for a, b in groups for c, d in b for e, f in d]
    after = 0
    for number in (1, 2, 3):
        after += number
    return result, (a, b, c, d, e, f), after


print(unpack4([[], [(1, 2, 3, 4)], [(5, 6, 7, 8)]]))
print(unpack_list([(1, [(3, 4), (5, 6)]), (7, [])]))
print(unpack6([(1, [(3, [(5, 6), (7, 8)])]), (9, [])]))
