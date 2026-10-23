# MIN_VERSION: 3.9


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


class Data:
    def __getitem__(self, key):
        return repr(key)
def slice(*args):
    print("custom slice", args)
    return args
data = Data()
print(dynamic_axes(data, 4))
print(constant_axes(data, 4))
print(mixed_axes(data, 4))
print(call(data, 4))
print(call_axes(data, 4))
