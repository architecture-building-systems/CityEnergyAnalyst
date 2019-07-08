

from __future__ import division


import numpy as np
import pandas as pd

import cea.technologies.solar.photovoltaic as pv
import cea.technologies.solar.photovoltaic_thermal as pvt
import cea.technologies.solar.solar_collector as stc
import cea.technologies.heat_exchangers as hex
import cea.technologies.heatpumps as hp
from cea.optimization.constants import N_PVT
from cea.constants import WH_TO_J

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Tim Vollrath", "Thuy-An Nguyen", ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def solar_evaluation(locator, config, solar_features, master_to_slave_vars, lca):

    # local variables
    DHN_barcode = master_to_slave_vars.DHN_barcode
    storage_activation_data = pd.read_csv(locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                                           master_to_slave_vars.generation_number))
    electricity_activation_curve = pd.read_csv(locator.get_optimization_slave_electricity_activation_pattern_heating(
                master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)


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

    array = np.array(storage_activation_data["HPScDesignArray_Wh", "HPpvt_designArray_Wh"])
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

    perfromance_emissions_pen = performance_solar_technologies(storage_activation_data, electricity_activation_curve, lca)

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

        # opex variable costs
        "Opex_var_SC_ET_connected_USD": [0.0],
        "Opex_var_SC_FP_connected_USD": [0.0],
        "Opex_var_PVT_connected_USD": [0.0],
        "Opex_var_PV_connected_USD": [0.],

        # opex annual costs
        "Opex_a_SC_ET_connected_USD": [Opex_fixed_SC_ET_USD],
        "Opex_a_SC_FP_connected_USD": [Opex_fixed_SC_FP_USD],
        "Opex_a_PVT_connected_USD": [Opex_fixed_PVT_USD],
        "Opex_a_PV_connected_USD": [Opex_fixed_PV_USD],

        # emissions
        "GHG_SC_ET_connected_tonCO2": perfromance_emissions_pen['GHG_SC_ET_connected_tonCO2'],
        "GHG_SC_FP_connected_tonCO2": perfromance_emissions_pen['GHG_SC_FP_connected_tonCO2'],
        "GHG_PVT_connected_tonCO2": perfromance_emissions_pen['GHG_PVT_connected_tonCO2'],
        "GHG_PV_connected_tonCO2": perfromance_emissions_pen['GHG_PV_connected_tonCO2'],

        # primary energy
        "PEN_SC_ET_connected_MJoil": perfromance_emissions_pen['PEN_SC_ET_connected_MJoil'],
        "PEN_SC_FP_connected_MJoil": perfromance_emissions_pen['PEN_SC_FP_connected_MJoil'],
        "PEN_PVT_connected_MJoil": perfromance_emissions_pen['PEN_PVT_connected_MJoil'],
        "PEN_PV_connected_MJoil": perfromance_emissions_pen['PEN_PV_connected_MJoil'],

        }

    return performance

def performance_solar_technologies(storage_activation_data, electricity_activation_curve, lca):

    #Claculate emissions and primary energy
    Q_SC_ET_gen_Wh = storage_activation_data['Q_SC_ET_gen_Wh'].values
    Q_SC_FP_gen_Wh = storage_activation_data['Q_SC_FP_gen_Wh'].values
    Q_PVT_gen_Wh = storage_activation_data['Q_PVT_gen_Wh'].values
    E_PVT_gen_export_W = electricity_activation_curve['E_PVT_gen_export_W'].values
    E_PVT_gen_directload_W = electricity_activation_curve['E_PVT_gen_directload_W'].values
    E_PV_gen_directload_W = electricity_activation_curve['E_PV_gen_directload_W'].values
    E_PV_gen_export_W = electricity_activation_curve['E_PV_gen_export_W'].values

    #calculate emissions hourly (to discount for exports and imports
    GHG_SC_ET_connected_tonCO2hr = (Q_SC_ET_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_CO2 / 1E3
    GHG_SC_FP_connected_tonCO2hr = (Q_SC_FP_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_CO2 / 1E3
    PEN_SC_ET_connected_MJoilhr = (Q_SC_ET_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_OIL
    PEN_SC_FP_connected_MJoilhr = (Q_SC_FP_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_OIL


    GHG_PVT_connected_tonCO2hr = ((Q_PVT_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_CO2 / 1E3) +\
                                 ((E_PVT_gen_directload_W * WH_TO_J / 1.0E6) *lca.EL_TO_CO2 / 1E3) -\
                                 ((E_PVT_gen_export_W * WH_TO_J / 1.0E6) *lca.EL_TO_CO2 / 1E3)

    GHG_PV_connected_tonCO2hr = ((E_PV_gen_directload_W * WH_TO_J / 1.0E6) *lca.EL_TO_CO2 / 1E3) -\
                                ((E_PV_gen_export_W * WH_TO_J / 1.0E6) *lca.EL_TO_CO2 / 1E3)

    PEN_PVT_connected_MJoilhr = ((Q_PVT_gen_Wh * WH_TO_J / 1.0E6) *lca.SOLARCOLLECTORS_TO_OIL) + \
                                ((E_PVT_gen_directload_W * WH_TO_J / 1.0E6) * lca.EL_TO_OIL_EQ) - \
                                ((E_PVT_gen_export_W * WH_TO_J / 1.0E6) * lca.EL_TO_OIL_EQ)

    PEN_PV_connected_MJoilhr = ((E_PV_gen_directload_W * WH_TO_J / 1.0E6) *lca.EL_TO_OIL_EQ) -\
                                ((E_PV_gen_export_W * WH_TO_J / 1.0E6) *lca.EL_TO_OIL_EQ)

        # get yearly totals
    GHG_SC_ET_connected_tonCO2 = sum(GHG_SC_ET_connected_tonCO2hr)
    GHG_SC_FP_connected_tonCO2 = sum(GHG_SC_FP_connected_tonCO2hr)
    GHG_PVT_connected_tonCO2 = sum(GHG_PVT_connected_tonCO2hr)
    GHG_PV_connected_tonCO2 = sum(GHG_PV_connected_tonCO2hr)

    PEN_SC_ET_connected_MJoil = sum(PEN_SC_ET_connected_MJoilhr)
    PEN_SC_FP_connected_MJoil = sum(PEN_SC_FP_connected_MJoilhr)
    PEN_PVT_connected_MJoil = sum(PEN_PVT_connected_MJoilhr)
    PEN_PV_connected_MJoil = sum(PEN_PV_connected_MJoilhr)

    performance_emissions = {
        # emissions
        "GHG_SC_ET_connected_tonCO2": GHG_SC_ET_connected_tonCO2,
        "GHG_SC_FP_connected_tonCO2": GHG_SC_FP_connected_tonCO2,
        "GHG_PVT_connected_tonCO2": GHG_PVT_connected_tonCO2,
        "GHG_PV_connected_tonCO2": GHG_PV_connected_tonCO2,

        # primary energy
        "PEN_SC_ET_connected_MJoil": PEN_SC_ET_connected_MJoil,
        "PEN_SC_FP_connected_MJoil": PEN_SC_FP_connected_MJoil,
        "PEN_PVT_connected_MJoil": PEN_PVT_connected_MJoil,
        "PEN_PV_connected_MJoil": PEN_PV_connected_MJoil
    }

    return performance_emissions