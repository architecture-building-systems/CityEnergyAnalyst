def remap(x, in_min, in_max, out_min, out_max):
    """
    Scale x from range [in_min, in_max] to [out_min, out_max]
    Based on this StackOverflow answer: https://stackoverflow.com/a/43567380/2260
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min