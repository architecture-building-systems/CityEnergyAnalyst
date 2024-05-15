# -*- coding: utf-8 -*-
"""
Water body potential
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

import cea.config
import cea.inputlocator
from cea.constants import P_WATER_KGPERM3, HEAT_CAPACITY_OF_WATER_JPERKGK, Mixed_Layer_Depth, T_sup, T_bot, HEX_WIDTH_M
from cea.resources.geothermal import calc_temperature_underground
from cea.datamanagement.surroundings_helper import get_water_basin

__author__ = "Giuseppe Nappi"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_lake_potential(locator, config):

    """
    Calculation of lake potential. This does not refer to CEA original publication.
    In that case, the implementation of the lake potential algorithm was carried out with another tool and then
    the result was implemented in CEA for a specific case study.
    """
    
    # local variables
    heat_capacity_water = HEAT_CAPACITY_OF_WATER_JPERKGK  # JkgK
    AT_max_K = config.water_body.max_delta_temperature_withdrawal  # K
    V_max_m3 = config.water_body.water_volume * 1e9 # m3
    avg_depth = config.water_body.average_depth # m

    # Calculation of heat released in the water
    Q_max_kwh = (V_max_m3 * P_WATER_KGPERM3 / 3600) * heat_capacity_water / 1000 * AT_max_K / 8760 # in kW

    # Max heat dischargeable in the lake to obtain an increase of 0.5 K in one year, which does not cause substantial
    # changes in the lake ecosystem

    Z = [] # depth in meters
    T = [] # temperature in kelvin

    # Check whether there is a water basin in the area under analysis or in the immediate proximity
    check, area = check_presence_water_basin(locator)

    if check:
        for z in np.arange(0, avg_depth, 0.1):
            Water_temperature = model_temperature_variation(z, avg_depth) - 273 #°C
            Z.append(z)
            T.append(Water_temperature)
        plt.plot(T, Z)
        plt.gca().invert_yaxis()
        # plt.show()
        q_yearly = [Q_max_kwh] * 8760
    else:
        q_yearly = [0] * 8760
        T = [0]

    # export
    lake_gen = locator.get_water_body_potential()
    pd.DataFrame({"Ts_C": T[-1], "QLake_kW": q_yearly}).to_csv(lake_gen, index=False, float_format='%.3f')
    if T[-1] == 0:
        return
    update_ec(locator, T[-1])

def model_temperature_variation(z, avg_depth):

    """
    Calculation of temperature of the lake at a chosen depth z, knowing the top and bottom temperature
    """
    
    measurement_depth = avg_depth
    heat_capacity_water = HEAT_CAPACITY_OF_WATER_JPERKGK  # JkgK
    drag = 0.002 # surface drag coefficient
    alpha_T = 1.6509e-5 # 1/K
    g = 9.81 # m/s2
    wind_vel = 2.026 # m/s
    # Karthikeya, B. R. “Wind Resource Assessment for Urban Renewable Energy Application in Singapore.”

    T_superficial_K = T_sup + 273  # to kelvin
    T_bottom_K = T_bot + 273  # to kelvin

    density_water_sup = 1000 * (1 - 0.5 * alpha_T * (T_superficial_K - 277.13) ** 2 )  # kg/m3
    density_water_bot = 1000 * (1 - 0.5 * alpha_T * (T_bottom_K - 277.13) ** 2 )  # kg/m3

    C_3 = np.sqrt(-(g * alpha_T * (T_bottom_K - T_superficial_K)) / (measurement_depth - Mixed_Layer_Depth))
    C_4 = np.sqrt((density_water_sup * drag * wind_vel ** 2) / (density_water_bot * heat_capacity_water))
    C_1 = 0.5 #(0.3 * 0.03 * C_4 ** 2) / ((measurement_depth - Mixed_Layer_Depth) ** 2 * C_3)
    # Approximated value for C_1 taken from literature for a linear underwater profile
    C_2 = (z - Mixed_Layer_Depth) / (measurement_depth - Mixed_Layer_Depth)

    shape_function = (40 / 3 * C_1 - 20 / 3) * C_2 + (18 - 30 * C_1) * C_2 ** 2 + (20 * C_1 - 12) * C_2 ** 3 + (
                5 / 3 - 10 / 3 * C_1) * C_2 ** 4

    # Water temperature selection based on depth
    if 0 <= z <= Mixed_Layer_Depth:
        T_water = T_superficial_K

    elif Mixed_Layer_Depth <= z <= measurement_depth:
        T_water = T_superficial_K - (T_superficial_K - T_bottom_K) * shape_function

    else:
        print('Depth outside maximum range of measurement. Please check the depth value.')
        T_water = None

    return T_water

def update_ec(locator, Water_temperature):

    ''' 
    This function calls the energy carrier database and adds the new energy carrier based on the temperature calculated.
    In this way, a different lake analysis can easily be updated.
    '''

    T_water = math.trunc(Water_temperature)
    e_carriers = pd.read_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS')
    row_copy = e_carriers.loc[e_carriers['description'] == 'Fresh water'].copy()
    row_copy['mean_qual'] = T_water
    row_copy['code'] = f'T{T_water}LW'
    row_copy['description'] = 'Bottom Lake Water'
    row_copy['subtype'] = 'water sink'

    if not e_carriers.loc[e_carriers['description'] == 'Bottom Lake Water'].empty:
        row_copy.index = e_carriers.loc[e_carriers['description'] == 'Bottom Lake Water'].index
        e_carriers.loc[e_carriers['description'] == 'Bottom Lake Water'] = row_copy.copy()
    else:
        e_carriers = pd.concat([e_carriers, row_copy], axis=0)

    e_carriers.to_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS', index=False)

def check_presence_water_basin(locator):

    """
    Check if the water basin is present in the area under the analysis.
    """

    water_basin_check, area_tot = get_water_basin(locator)

    return water_basin_check, area_tot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_lake_potential(locator=locator, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())
