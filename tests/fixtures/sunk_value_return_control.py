# Versioned .pyc files are consumed by tests/integration.rs.

def select(value):
    try:
        entry = value.entry
    except AttributeError:
        kind = "missing"
    else:
        kind = "present"
    return kind, value
