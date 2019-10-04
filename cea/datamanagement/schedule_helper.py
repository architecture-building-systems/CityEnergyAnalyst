"""
This script creates schedules per building in CEA
"""
from __future__ import division
from __future__ import print_function

import math
import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.utilities.schedule_reader import read_cea_schedule, save_cea_schedule

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def schedule_helper(locator, config):

    #local variables

    x=1
    return x

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    schedule_helper(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())