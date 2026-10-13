def select(call, before, first, second, last, after):
    return call(before(), (first() and second()) or last(), after())


def repeated_prefix(call, value, second, last, after):
    return call(value, (value and second()) or last(), after())


def alternatives(a, b, c, d, e):
    return bool((a and b) or c or d or e)


def or_prefix(a, b, c, d, e):
    return bool(c or d or (a and b) or e)


def method(a, b, c, d, e):
    return bool((a and a.get("available")) or b or c or d or e)


def assignment(a, b, c, d, e):
    value = (a and a.get("available")) or b or c or d or e
    return bool(value)


def pure_or(a, b, c, d, e):
    return bool(a or b or c or d or e)


def pure_and(a, b, c, d, e):
    return bool(a and b and c and d and e)


def following_branch(call, a, b, c, d, e):
    return call((a and b) or c, d if e else 0)
