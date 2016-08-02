# -*- coding: utf-8 -*-


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def night_flushing_status(hoy, tsd, bpr, weather_data):

    # TODO: get night flushing building property (bpr)
    night_flushing = True

    # TODO: get control temperatures from ? (gv?)
    if night_flushing:

        if h.is_nighttime_hoy(hoy) and h.is_coolingseason_hoy(hoy):  # clocktime condition

            temp_zone_control = 28  # TODO: make dynamic
            temp_ext_control = 26 # TODO: make dynamic (as function of zone air temperature, e.g. Ta - 2°C)

            if tsd['Ta'].values[hoy] > temp_zone_control and weather_data.drybulb_C.values[hoy] < temp_ext_control:  # temperature condition

                return True
            else:
                return False
        else:
            return False
    else:
        return False


