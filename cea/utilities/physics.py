# -*- coding: utf-8 -*-
"""
Physical functions
"""
from __future__ import division

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# stefan-boltzmann constant
BOLTZMANN = 0.000000056697  # W/m2K4


def calc_rho_air(temp_air):
    """
    Calculation of density of air according to 6.4.2.1 in [1]

    temp_air : air temperature in (°C)

    rho_air : air density in (kg/m3)

    """
    # constants from Table 12 in [1]
    # TODO import from global variables
    # TODO implement dynamic air density in other functions
    rho_air_ref = 1.23  # (kg/m3)
    temp_air_ref_K = 283  # (K)
    temp_air_K = temp_air + 273  # conversion to (K)

    # Equation (1) in [1]
    rho_air = temp_air_ref_K / temp_air_K * rho_air_ref

    return rho_air

