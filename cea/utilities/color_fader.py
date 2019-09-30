"""
Interpolate colors to create a gradient. This is based on code from here: https://stackoverflow.com/a/50784012/2260
"""

import matplotlib as mpl
import numpy as np


def color_fader_rgb(c1, c2, mix=0):
    """fade (linear interpolate) from color c1 (at mix=0) to c2 (mix=1)

    Expects c1 and c2 to be arrays or matplotlib colors, ranges for the colors of input and output are [0.0, 1.0]
    """
    c1 = np.array(mpl.colors.to_rgb(c1))
    c2 = np.array(mpl.colors.to_rgb(c2))
    color_np_array = (1 - mix) * c1 + mix * c2
    print("color_fader_rgb({c1}, {c2}, {mix}, {result}".format(
        c1=c1, c2=c2, mix=mix, result=color_np_array.tolist()
    ))
    return color_np_array.tolist()
