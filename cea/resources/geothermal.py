


import pandas as pd
import numpy as np
import math
from cea.constants import HOURS_IN_YEAR

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_ground_temperature(locator, T_ambient_C, depth_m):
    """
    Calculates hourly ground temperature fluctuation over a year following [Kusuda, T. et al., 1965]_.

    :param T_ambient_C: vector with outdoor temperature
    :type T_ambient_C: np array
    :param depth_m: globalvar.py


    :return T_ground_K: vector with ground temperatures in [K]
    :rtype T_ground_K: np array

    ..[Kusuda, T. et al., 1965] Kusuda, T. and P.R. Achenbach (1965). Earth Temperatures and Thermal Diffusivity at
    Selected Stations in the United States. ASHRAE Transactions. 71(1):61-74
    """

    material_properties = pd.read_excel(locator.get_thermal_networks(), sheet_name='MATERIAL PROPERTIES').set_index(
        'material')
    heat_capacity_soil = material_properties.loc['Soil','Cp_JkgK']   # _[A. Kecebas et al., 2011]
    conductivity_soil = material_properties.loc['Soil','lambda_WmK']  # _[A. Kecebas et al., 2011]
    density_soil = material_properties.loc['Soil','rho_kgm3']   # _[A. Kecebas et al., 2011]

    T_amplitude = abs((max(T_ambient_C) - min(T_ambient_C))+ 273.15)  # to K
    T_avg = np.mean(T_ambient_C) + 273.15  # to K
    T_ground_K = calc_temperature_underground(T_amplitude, T_avg, conductivity_soil, density_soil, depth_m, heat_capacity_soil)

    return T_ground_K


def calc_temperature_underground(T_amplitude_K, T_avg, conductivity_soil, density_soil, depth_m, heat_capacity_soil):

    diffusivity = conductivity_soil /(density_soil *heat_capacity_soil) *3600 #in m2/hour
    hour_with_minimum = 0
    e = depth_m * math.sqrt(math.pi / HOURS_IN_YEAR / diffusivity)  # soil constants
    T_ground_K = [T_avg - T_amplitude_K * (math.exp(-e) * math.cos(2*math.pi/HOURS_IN_YEAR*(i-hour_with_minimum-e/2)))for i in range(1, HOURS_IN_YEAR+1)]
    return T_ground_K
