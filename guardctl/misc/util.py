import dpath.util

def dget(d, path, default):
    try:
        return dpath.util.get(d, path)
    except KeyError:
        return default
