# Python 3.15 bytecode changes: inline-comprehension layout, extended
# common constants, IMPORT_NAME packing, yield-from, loop returns, with
# targets, nested genexpr closures, and class-dict protocol locals.
import os.path
from os.path import join


def inline_comps(xs):
    return [x * 2 for x in xs], {x for x in xs}, {x: x + 1 for x in xs}


def genexp_calls(xs, fn):
    return tuple(
        fn(x, alphas=1, X_test=x, mode=2, max_iter=int(0.1 * 3))
        for x in xs
    )


def genexp_ternary(xs, fn):
    return tuple(fn(x, x if x > 1 else 0) for x in xs)


def inline_any_filter(paths):
    return set([p for p in paths if not any(s in p for s in [".a", ".b"])])


def nested_tuple_genexpr(rows):
    return tuple(tuple(s for s in row) for row in rows)


def handler_loop(a):
    try:
        return [1][5]
    except IndexError:
        for i in range(3):
            if i == a:
                return "hit%d" % i


def delegated(xs):
    yield 0
    yield from xs
    yield 1


def constants(v):
    if v is True:
        return 1
    if v is False:
        return 2
    if v is None:
        return 3
    return -1


class Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def with_targets(ctx, holder):
    with ctx as holder.value:
        holder.value = 1
    with ctx as holder["k"]:
        holder["k"] = 2
    return holder
