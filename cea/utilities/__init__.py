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
