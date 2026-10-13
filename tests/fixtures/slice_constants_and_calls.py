# Versioned .pyc files are consumed by tests/integration.rs.

# Marshal format 5 adds slice constants in 3.14; runtime calls must
# retain their global lookup on every supported Python version.

def dynamic_axes(data, stop):
    return data[:stop, :]


def constant_axes(data, stop):
    return data[:, :]


def mixed_axes(data, stop):
    return data[1:stop:2, :, 7]


def call(data, stop):
    return data[slice(None, stop, None)]


def call_axes(data, stop):
    return data[slice(None, stop, None), :]
