

from __future__ import division


import numpy as np
import pandas as pd

import cea.technologies.solar.photovoltaic as pv
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
from cea.optimization.constants import N_PVT

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Tim Vollrath", "Thuy-An Nguyen", ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def solar_evaluation(locator, config, solar_features, master_to_slave_vars):

    # local variables
    DHN_barcode = master_to_slave_vars.DHN_barcode

    # ADD COSTS AND EMISSIONS DUE TO SOLAR TECHNOLOGIES
    PV_installed_area_m2 = master_to_slave_vars.SOLAR_PART_PV * solar_features.A_PV_m2  # kW
    Capex_a_PV_USD, Opex_fixed_PV_USD, Capex_PV_USD = pv.calc_Cinv_pv(PV_installed_area_m2, locator)

    SC_ET_area_m2 = master_to_slave_vars.SOLAR_PART_SC_ET * solar_features.A_SC_ET_m2
    Capex_a_SC_ET_USD, Opex_fixed_SC_ET_USD, Capex_SC_ET_USD = stc.calc_Cinv_SC(SC_ET_area_m2, locator, config, 'ET')

    SC_FP_area_m2 = master_to_slave_vars.SOLAR_PART_SC_FP * solar_features.A_SC_FP_m2
    Capex_a_SC_FP_USD, Opex_fixed_SC_FP_USD, Capex_SC_FP_USD = stc.calc_Cinv_SC(SC_FP_area_m2, locator, config, 'FP')

    PVT_peak_kW = master_to_slave_vars.SOLAR_PART_PVT * solar_features.A_PVT_m2 * N_PVT  # kW
    Capex_a_PVT_USD, Opex_fixed_PVT_USD, Capex_PVT_USD = pvt.calc_Cinv_PVT(PVT_peak_kW, locator, config)


    # HEATPUMP FOR SOLAR UPGRADE TO DISTRICT HEATING
    df = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                           master_to_slave_vars.generation_number),
                     usecols=["HPScDesignArray_Wh", "HPpvt_designArray_Wh"])
    array = np.array(df)
    Q_HP_max_PVT_wh = np.amax(array[:, 1])
    Q_HP_max_SC_Wh = np.amax(array[:, 0])
    Capex_a_HP_PVT_USD, Opex_fixed_HP_PVT_USD, Capex_HP_PVT_USD = hp.calc_Cinv_HP(Q_HP_max_PVT_wh, locator, config,
                                                                                  'HP2')
    Capex_a_HP_SC_USD, Opex_fixed_HP_SC_USD, Capex_HP_SC_USD = hp.calc_Cinv_HP(Q_HP_max_SC_Wh, locator, config,
                                                                               'HP2')

    # HEAT EXCHANGER FOR SOLAR COLLECTORS
    roof_area_m2 = np.array(pd.read_csv(locator.get_total_demand(), usecols=["Aroof_m2"]))
    areaAvail = 0
    for i in range(len(DHN_barcode)):
        index = DHN_barcode[i]
        if index == "1":
            areaAvail += roof_area_m2[i][0]

    for i in range(len(DHN_barcode)):
        index = DHN_barcode[i]
        if index == "1":
            share = roof_area_m2[i][0] / areaAvail
            # print share, "solar area share", buildList[i]

            Q_max_SC_ET_Wh = solar_features.Q_nom_SC_ET_Wh * master_to_slave_vars.SOLAR_PART_SC_ET * share
            Capex_a_HEX_SC_ET_USD, Opex_fixed_HEX_SC_ET_USD, Capex_HEX_SC_ET_USD = hex.calc_Cinv_HEX(Q_max_SC_ET_Wh,
                                                                                                     locator,
                                                                                                     config, 'HEX1')

            Q_max_SC_FP_Wh = solar_features.Q_nom_SC_FP_Wh * master_to_slave_vars.SOLAR_PART_SC_FP * share
            Capex_a_HEX_SC_FP_USD, Opex_fixed_HEX_SC_FP_USD, Capex_HEX_SC_FP_USD = hex.calc_Cinv_HEX(Q_max_SC_FP_Wh,
                                                                                                     locator,
                                                                                                     config, 'HEX1')

            Q_max_PVT_Wh = solar_features.Q_nom_PVT_Wh * master_to_slave_vars.SOLAR_PART_PVT * share
            Capex_a_HEX_PVT_USD, Opex_fixed_HEX_PVT_USD, Capex_HEX_PVT_USD = hex.calc_Cinv_HEX(Q_max_PVT_Wh,
                                                                                               locator, config,
                                                                                               'HEX1')

    performance = {
        # annualized capex
        "Capex_a_SC_ET_connected_USD": [Capex_a_SC_ET_USD + Capex_a_HP_SC_USD + Capex_a_HEX_SC_ET_USD],
        "Capex_a_SC_FP_connected_USD": [Capex_a_SC_FP_USD + Capex_a_HP_SC_USD + Capex_a_HEX_SC_FP_USD],
        "Capex_a_PVT_connected_USD": [Capex_a_PVT_USD + Capex_a_HP_PVT_USD + Capex_a_HEX_PVT_USD],
        "Capex_a_PV_connected_USD": [Capex_a_PV_USD],

        # total_capex
        "Capex_total_SC_ET_connected_USD": [Capex_SC_ET_USD + Capex_HP_SC_USD + Capex_HEX_SC_ET_USD],
        "Capex_total_SC_FP_connected_USD": [Capex_SC_FP_USD + Capex_HP_SC_USD + Capex_HEX_SC_FP_USD],
        "Capex_total_PVT_connected_USD": [Capex_PVT_USD + Capex_HP_PVT_USD + Capex_HEX_PVT_USD],
        "Capex_total_PV_connected_USD": [Capex_PV_USD],

        # opex fixed costs
        "Opex_fixed_SC_ET_connected_USD": [Opex_fixed_SC_ET_USD],
        "Opex_fixed_SC_FP_connected_USD": [Opex_fixed_SC_FP_USD],
        "Opex_fixed_PVT_connected_USD": [Opex_fixed_PVT_USD],
        "Opex_fixed_PV_connected_USD": [Opex_fixed_PV_USD],

        }

    return performance