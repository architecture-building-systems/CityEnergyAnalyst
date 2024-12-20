"""
This is the official list of CEA colors to use in plots
"""






__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


COLORS_TO_RGB = {"red": "rgb(240,77,91)",
                 "red_light": "rgb(246,149,143)",
                 "red_lighter": "rgb(252,217,210)",
                 "red_dark": "rgb(191,98,96)",
                 "blue": "rgb(63,192,194)",
                 "blue_light": "rgb(151,214,215)",
                 "blue_lighter": "rgb(219,240,239)",
                 "yellow": "rgb(255,209,29)",
                 "yellow_light": "rgb(255,225,133)",
                 "yellow_lighter": "rgb(255,243,211)",
                 "brown": "rgb(174,148,72)",
                 "brown_light": "rgb(201,183,135)",
                 "brown_lighter": "rgb(233,225,207)",
                 "purple": "rgb(171,95,127)",
                 "purple_light": "rgb(198,149,167)",
                 "purple_lighter": "rgb(231,214,219)",
                 "green": "rgb(126,199,143)",
                 "green_light": "rgb(178,219,183)",
                 "green_lighter": "rgb(227,241,228)",
                 "grey": "rgb(127,128,134)",
                 "grey_light": "rgb(162,161,166)",
                 "grey_lighter": "rgb(201,200,203)",
                 "black": "rgb(69,77,84)",
                 "white": "rgb(255,255,255)",
                 "orange": "rgb(245,131,69)",
                 "orange_light": "rgb(250,177,133)",
                 "orange_lighter": "rgb(254,226,207)"}


def color_to_rgb(color):
    rgb = COLORS_TO_RGB.get(color)

    if rgb is None:
        raise ValueError(f"Color {color} not found.")

    return rgb

def rgb_to_hex(rgb_string):
    rgb_values = rgb_string.strip("rgb()").split(",")
    if len(rgb_values) != 3:
        raise ValueError("RGB string must contain exactly 3 values")
    rgb = [max(0, min(255, int(val.strip()))) for val in rgb_values]
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def color_to_hex(color):
    rgb = color_to_rgb(color)

    return rgb_to_hex(rgb)
