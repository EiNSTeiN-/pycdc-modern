# MIN_VERSION: 3.12


def select(rows):
    return [{
        "excluded": ({"count": row["count"],
                      "reasons": loads(row["reasons"]) if row["reasons"] else {}}
                     if row["count"] is not None else {}),
        "archived": str(row["archived"]) if row["archived"] else None,
    } for row in rows]


def loads(value):
    print("loads", value)
    return {"decoded": value}
print(select([{"count": 1, "reasons": "why", "archived": 3},
              {"count": None, "reasons": "skip", "archived": 0},
              {"count": 2, "reasons": "", "archived": None}]))
