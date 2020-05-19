"""
This is the official list of CEA colors to use in plots
"""

from __future__ import print_function
from __future__ import division

import os
import pandas as pd
import yaml
import warnings
import functools
from typing import List, Callable

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


COLORS_TO_RGB = {"red": "rgb(240,75,91)",
                 "red_light": "rgb(246,148,143)",
                 "red_lighter": "rgb(252,217,210)",
                 "blue": "rgb(63,192,194)",
                 "blue_light": "rgb(171,221,222)",
                 "blue_lighter": "rgb(225,242,242)",
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
                 "grey": "rgb(68,76,83)",
                 "grey_light": "rgb(126,127,132)",
                 "black": "rgb(35,31,32)",
                 "white": "rgb(255,255,255)",
                 "orange": "rgb(245,131,69)",
                 "orange_light": "rgb(248,159,109)",
                 "orange_lighter": "rgb(254,220,198)"}