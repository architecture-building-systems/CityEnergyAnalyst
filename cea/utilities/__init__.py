


import os
import sys
import string


def remap(x, in_min, in_max, out_min, out_max):
    """
    Scale x from range [in_min, in_max] to [out_min, out_max]
    Based on this StackOverflow answer: https://stackoverflow.com/a/43567380/2260
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def identifier(s, sep="-"):
    """
    First, all characters are lowercased, then, any character that is not in ascii_lowercase is replaced with ``sep``.

    :param str s: the string to create an identifier of
    :param str use_underscores: if set to true, underscores ("_") will be used instead of dashes ("-")
    :rtype: str
    """
    return "".join(c if c in string.ascii_lowercase else sep for c in s.lower())


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


def unique(sequence):
    """
    Return only the unique elements in sequence, preserving order.

    :param Sequence[T] sequence: the sequence to unique-ify
    :rtype: List[T]
    """
    seen = set()
    result = []
    for item in sequence:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def parse_string_to_list(line):
    """Parse a line in the csv format into a list of strings"""
    if line is None:
        return []
    line = line.replace('\n', ' ')
    line = line.replace('\r', ' ')
    return [str(field.strip()) for field in line.split(',') if field.strip()]
