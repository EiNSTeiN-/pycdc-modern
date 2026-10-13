# Compile with each named CPython version; the committed .pyc files are
# exercised by the existing Rust integration suite.

# Python 3.10+ uses MAP_ADD 1 for large dictionary displays.

def list17(rows):
    return [{
        "k0": row + 0, "k1": row + 1, "k2": row + 2, "k3": row + 3,
        "k4": row + 4, "k5": row + 5, "k6": row + 6, "k7": row + 7,
        "k8": row + 8, "k9": row + 9, "k10": row + 10, "k11": row + 11,
        "k12": row + 12, "k13": row + 13, "k14": row + 14, "k15": row + 15,
        "k16": row + 16,
    } for row in rows]


def generator17(rows):
    return ({
        "k0": row + 0, "k1": row + 1, "k2": row + 2, "k3": row + 3,
        "k4": row + 4, "k5": row + 5, "k6": row + 6, "k7": row + 7,
        "k8": row + 8, "k9": row + 9, "k10": row + 10, "k11": row + 11,
        "k12": row + 12, "k13": row + 13, "k14": row + 14, "k15": row + 15,
        "k16": row + 16,
    } for row in rows)


def list20(rows):
    return [{
        "k0": row + 0, "k1": row + 1, "k2": row + 2, "k3": row + 3,
        "k4": row + 4, "k5": row + 5, "k6": row + 6, "k7": row + 7,
        "k8": row + 8, "k9": row + 9, "k10": row + 10, "k11": row + 11,
        "k12": row + 12, "k13": row + 13, "k14": row + 14, "k15": row + 15,
        "k16": row + 16, "k17": row + 17, "k18": row + 18, "k19": row + 19,
    } for row in rows]


def generator20(rows):
    return ({
        "k0": row + 0, "k1": row + 1, "k2": row + 2, "k3": row + 3,
        "k4": row + 4, "k5": row + 5, "k6": row + 6, "k7": row + 7,
        "k8": row + 8, "k9": row + 9, "k10": row + 10, "k11": row + 11,
        "k12": row + 12, "k13": row + 13, "k14": row + 14, "k15": row + 15,
        "k16": row + 16, "k17": row + 17, "k18": row + 18, "k19": row + 19,
    } for row in rows)


def dictionary_comprehension(rows):
    return {row: row + 1 for row in rows}


def small_display(rows):
    return [{"value": row} for row in rows]
