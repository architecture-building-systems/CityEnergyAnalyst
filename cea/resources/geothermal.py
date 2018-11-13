


import pandas as pd
import numpy as np
import math

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_ground_temperature(locator, config, T_ambient_C, depth_m):
    """
    Calculates hourly ground temperature fluctuation over a year following [Kusuda, T. et al., 1965]_.

    :param T_ambient_C: vector with outdoor temperature
    :type T_ambient_C: np array
    :param depth_m: globalvar.py


    :return Tg: vector with ground temperatures in [K]
    :rtype Tg: np array

    ..[Kusuda, T. et al., 1965] Kusuda, T. and P.R. Achenbach (1965). Earth Temperatures and Thermal Diffusivity at
    Selected Stations in the United States. ASHRAE Transactions. 71(1):61-74
    """
    material_properties = pd.read_excel(locator.get_thermal_networks(config.region),
                                        sheetname=['MATERIAL PROPERTIES'])['MATERIAL PROPERTIES'].set_index('material')
    heat_capacity_soil = material_properties.loc['Soil','Cp_JkgK']   # _[A. Kecebas et al., 2011]
    conductivity_soil = material_properties.loc['Soil','lambda_WmK']  # _[A. Kecebas et al., 2011]
    density_soil = material_properties.loc['Soil','rho_kgm3']   # _[A. Kecebas et al., 2011]


    T_max = max(T_ambient_C) + 273.15 # to K
    T_avg = np.mean(T_ambient_C) + 273.15 # to K
    e = depth_m * math.sqrt ((math.pi * heat_capacity_soil * density_soil) / (8760 * conductivity_soil)) # soil constants
    Tg = [ T_avg + ( T_max - T_avg ) * math.exp( -e ) * math.cos ( ( 2 * math.pi * ( i + 1 ) / 8760 ) - e )
           for i in range(8760)]

    return Tg
