# Versioned .pyc files are consumed by tests/integration.rs.

# CALL_KW starts in Python 3.13.

def case_0(value, build, other):
    return build("reject" if value else "accept", amount=0)


def case_1(value, build, other):
    return build("prefix", amount=0 if value else 1)


def case_2(value, build, other):
    return build(0 if value else 1, amount=value)


def case_9(value, build, other):
    return build("prefix", amount=1 if value else 2, last=other(value))


def case_11(value, build, other):
    return other(build(amount=1) if value else build(amount=2, other=3))
