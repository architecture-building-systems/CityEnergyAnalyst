
"""
Configuration for building_main
"""

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# Parameters you can/need to change - General
DELTA_P_DIM = 5  # (Pa) dimensioning differential pressure for multi-storey building shielded from wind,
# found in CEA > demand > constants.py
DENSITY_AIR = 1.205  # [kg/m3]
HEAT_CAPACITY_AIR = 1211.025  # [J/(m3.K)]
HE_E = 25  # [W/(m2.K)]
H_I = 7.7  # [W/(m2.K)]
# Parameters you can/need to change - HVAC efficiencies
PHI_5_MAX = 6.73 * (10 ** 6)  # TODO:  Remind the user that this needs to be updated when the reference case changes
FB = 0.7
HP_ETA_EX_COOL = 0.3
HP_AUXRATIO = 0.83