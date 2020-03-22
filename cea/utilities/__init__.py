import os
import sys


def remap(x, in_min, in_max, out_min, out_max):
    """
    Scale x from range [in_min, in_max] to [out_min, out_max]
    Based on this StackOverflow answer: https://stackoverflow.com/a/43567380/2260
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def simple_memoize(obj):
    import functools

    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoized_func(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoized_func


class pushd(object):
    """
    Manage an os.chdir so that at the end of a with block, the path is set back to what it was
    """
    def __init__(self, path):
        self.old_path = os.getcwd()
        self.new_path = path

    def __enter__(self):
        os.chdir(self.new_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_path)


class devnull(object):
    """
    Suppress sys.stdout so that it goes to devnull for duration of the with block
    """
    def __init__(self):
        self.stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.stdout

    def write(self, _):
        pass