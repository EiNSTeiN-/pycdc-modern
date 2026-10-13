# Resolving owner.build belongs after the condition. Reconstructing this as
# outer(owner.build(amount=1 if value else 2)) changes descriptor evaluation
# order. The bounded merger must decline rather than report a clean result.
def select(value, owner, outer):
    return outer(owner.build(amount=1) if value else owner.build(amount=2))
