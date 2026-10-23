def select(rows):
    return [{
        "excluded": ({"count": row["count"],
                      "reasons": loads(row["reasons"]) if row["reasons"] else {}}
                     if row["count"] is not None else {}),
        "archived": str(row["archived"]) if row["archived"] else None,
    } for row in rows]


def then_arm(rows, build):
    return [build(1 if row.inner else 2) if row.outer else 3 for row in rows]


def else_arm(rows, build):
    return [1 if row.outer else build(2 if row.inner else 3) for row in rows]


def both_arms(rows, build):
    return [build(1 if row.inner is None else 2) if row.outer
            else build(3 if row.inner is not None else 4) for row in rows]
