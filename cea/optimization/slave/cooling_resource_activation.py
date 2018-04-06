from __future__ import division
import numpy as np
import pandas as pd
import math
import cea.config
import cea.globalvar
import cea.inputlocator
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.storage_tank as storage_tank
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3
from cea.optimization.constants import DELTA_P_COEFF, DELTA_P_ORIGIN, PUMP_ETA, EL_TO_OIL_EQ, EL_TO_CO2, \
    ACH_T_IN_FROM_CHP


def cooling_resource_activator(DCN_cooling, limits, cooling_resource_potentials, T_ground_K, prices,
                               master_to_slave_variables):
    """

    :param DCN_cooling:
    :param Qc_available_from_lake_W:
    :type Qc_available_from_lake_W: float
    :param Qc_from_lake_cumulative_W:
    :type Qc_from_lake_cumulative_W: float
    :param prices:
    :return:
    """

    config = cea.config.Configuration()  # TODO: maybe pass config as an argument

    # unpack variables
    Qc_tank_avail_W = cooling_resource_potentials['Qc_tank_avail_W']
    Qc_available_from_lake_W = cooling_resource_potentials['Qc_avail_from_lake_W']
    Qc_from_lake_cumulative_W = cooling_resource_potentials['Qc_from_lake_cumulative_W']

    T_tank_start_C = 4  # FIXME: need to change
    V_tank_m3 = 10000  # FIXME: kW dischared at peak should come form optimization, and translate to V_tank
    T_ambient_C = 30  # FIXME: take from weather file

    T_DCN_sup_K = DCN_cooling[0]
    T_DCN_re_K = DCN_cooling[1]
    mdot_DCN_kgpers = abs(DCN_cooling[2])
    T_tank_C = 273

    Qc_load_W = abs(mdot_DCN_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_DCN_re_K - T_DCN_sup_K))

    opex_var_Lake = 0
    opex_var_VCC = 0
    opex_var_ACH = 0

    co2_output_Lake = 0
    co2_VCC = 0
    co2_ACH = 0

    prim_output_Lake = 0
    prim_energy_VCC = 0
    prim_energy_ACH = 0

    calfactor_output = 0

    Qc_from_Lake_W = 0
    Qc_from_VCC_W = 0
    Qc_from_ACH_W = 0
    Qh_CHP_ACH_W = 0

    Qc_CT_VCC_W = 0
    Qc_CT_ACH_W = 0

    Qc_load_unmet_W = Qc_load_W

    if Qc_load_W <= (Qc_available_from_lake_W - Qc_from_lake_cumulative_W):  # Free cooling possible from the lake

        Qc_from_Lake_W = Qc_load_W
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Lake_W

        # Delta P from linearization after distribution optimization
        deltaP = 2 * (DELTA_P_COEFF * mdot_DCN_kgpers + DELTA_P_ORIGIN)
        calfactor_output = deltaP * (mdot_DCN_kgpers / 1000) / PUMP_ETA
        opex_var_Lake = deltaP * (mdot_DCN_kgpers / 1000) * prices.ELEC_PRICE / PUMP_ETA
        co2_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_CO2 / PUMP_ETA * 0.0036
        prim_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_OIL_EQ / PUMP_ETA * 0.0036


    elif Qc_load_unmet_W > limits['Qc_peak_load_W'] and Qc_tank_avail_W > 0:  # peak hour

        Qc_from_Tank_W = Qc_load_W if Qc_load_W <= limits['Qc_tank_discharged_W'] else limits[
            'Qc_tank_discharged_W']
        Qc_to_tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_start_C, T_ambient_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)
        Qc_tank_avail_W = HEAT_CAPACITY_OF_WATER_JPERKGK * V_tank_m3 * P_WATER_KGPERM3 * (
        (T_DCN_sup_K - 273.0) - T_tank_C)
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Tank_W

    elif Qc_load_unmet_W > 0 and Qc_tank_avail_W < limits['Qc_tank_max_W']:  # off-peak hour
        Qc_to_tank_W = limits['Qc_tank_charged_W']
        Qc_from_Tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_start_C, T_ambient_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)
        Qc_tank_avail_W = HEAT_CAPACITY_OF_WATER_JPERKGK * V_tank_m3 * P_WATER_KGPERM3 * (
        (T_DCN_sup_K - 273.0) - T_tank_C)

        Qc_load_unmet_W = Qc_load_unmet_W + Qc_to_tank_W  # FIXME: calculate tank temperature

    else:  # no charging/discharging
        Qc_from_Tank_W = 0
        Qc_to_tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_start_C, T_ambient_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)
        Qc_tank_avail_W = HEAT_CAPACITY_OF_WATER_JPERKGK * V_tank_m3 * P_WATER_KGPERM3 * (
        (T_DCN_sup_K - 273.0) - T_tank_C)

    # satifying the remaining cooling loads
    if Qc_load_unmet_W > 0 and master_to_slave_variables.Absorption_Chiller_on == 1:
        # activate ACH
        Qc_from_ACH_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
        opex_var_ACH, co2_ACH, prim_energy_ACH, Qc_CT_ACH_W, Qh_CHP_ACH_W = calc_chiller_absorption_operation(
            Qc_from_ACH_W,
            T_DCN_re_K, T_DCN_sup_K,
            T_ground_K, prices,
            config)
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_ACH_W

    if Qc_load_unmet_W > 0 and master_to_slave_variables.VCC_on == 1:
        # activate VCC
        Qc_from_VCC_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
        opex_var_VCC, co2_VCC, prim_energy_VCC, Qc_CT_VCC_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K,
                                                                                 T_DCN_sup_K, prices)
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_VCC_W

    if Qc_load_unmet_W > 0:
        # activate back-up VCC
        Qc_from_backup_VCC_W = Qc_load_unmet_W
        opex_var_VCC, co2_VCC, prim_energy_VCC, Qc_CT_VCC_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K,
                                                                                 T_DCN_sup_K, prices)
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_backup_VCC_W

    if Qc_load_unmet_W != 0:
        raise ValueError(
            'The cooling load is not met! Fix that calculation!')

    # FIXME: combine the 3 outputs into "performance indicators"

    opex_output = {'Opex_var_Lake': opex_var_Lake,
                   'Opex_var_VCC': opex_var_VCC,
                   'Opex_var_ACH': opex_var_ACH}

    co2_output = {'CO2_Lake': co2_output_Lake,
                  'CO2_VCC': co2_VCC,
                  'CO2_ACH': co2_ACH}

    prim_output = {'Primary_Energy_Lake': prim_output_Lake,
                   'Primary_Energy_VCC': prim_energy_VCC,
                   'Primary_Energy_ACH': prim_energy_ACH}

    Qc_supply_output = {'Qc_from_Lake_W': Qc_from_Lake_W,
                        'Qc_from_VCC_W': Qc_from_VCC_W,
                        'Qc_from_ACH_W': Qc_from_ACH_W}

    Qc_CT_W = Qc_CT_ACH_W + Qc_CT_VCC_W

    cooling_resource_potentials_output = {'Qc_tank_avail_W': Qc_tank_avail_W, 'T_tank_C': T_tank_C,
                                          'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                          'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    return opex_output, co2_output, prim_output, Qc_supply_output, calfactor_output, Qc_CT_W, Qh_CHP_ACH_W, cooling_resource_potentials_output


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, prices):
    mdot_VCC_kgpers = Qc_from_VCC_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    VCC_operation = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K)
    # unpack outputs
    opex = VCC_operation['wdot_W'] * prices.ELEC_PRICE
    co2 = VCC_operation['wdot_W'] * EL_TO_CO2 * 3600E-6
    prim_energy = VCC_operation['wdot_W'] * EL_TO_OIL_EQ * 3600E-6
    Qc_CT_W = VCC_operation['q_cw_W']
    return opex, co2, prim_energy, Qc_CT_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, config):
    ACH_type = 'double'
    opex = 0
    co2 = 0
    prim_energy = 0
    Qc_CT_W = 0
    Qc_ACH_nom_W = Qc_from_ACH_W
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)  # FIXME: move out
    chiller_prop = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Absorption_chiller",
                                 usecols=['cap_max', 'type'])
    chiller_prop = chiller_prop[chiller_prop['type'] == ACH_type]
    max_chiller_size = max(chiller_prop['cap_max'].values)
    if Qc_ACH_nom_W < max_chiller_size:  # activate one unit of ACH
        # calculate ACH operation
        mdot_ACH_kgpers = Qc_from_ACH_W / (
            (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K,
                                                             ACH_T_IN_FROM_CHP,
                                                             T_ground_K, ACH_type, Qc_ACH_nom_W, locator, config)
        opex = (ACH_operation['wdot_W']) * prices.ELEC_PRICE
        co2 = (ACH_operation['wdot_W']) * EL_TO_CO2 * 3600E-6
        prim_energy = (ACH_operation['wdot_W']) * EL_TO_OIL_EQ * 3600E-6
        Qc_CT_W = ACH_operation['q_cw_W']
        Qh_CHP_W = ACH_operation['q_hw_W']
    else:  # more than one unit of ACH are activated
        number_of_chillers = int(math.ceil(Qc_ACH_nom_W / max_chiller_size))
        mdot_ACH_kgpers = Qc_from_ACH_W / (
        (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        mdot_ACH_kgpers_per_chiller = mdot_ACH_kgpers / number_of_chillers
        for i in range(number_of_chillers):
            ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers_per_chiller, T_DCN_sup_K, T_DCN_re_K,
                                                                 ACH_T_IN_FROM_CHP,
                                                                 T_ground_K, ACH_type, Qc_ACH_nom_W, locator, config)
            opex = opex + (ACH_operation['wdot_W'].values[0]) * prices.ELEC_PRICE
            co2 = co2 + (ACH_operation['wdot_W'].values[0]) * EL_TO_CO2 * 3600E-6
            prim_energy = prim_energy + (ACH_operation['wdot_W'].values[0]) * EL_TO_OIL_EQ * 3600E-6
            Qc_CT_W = Qc_CT_W + ACH_operation['q_cw_W']
            Qh_CHP_W = Qh_CHP_W + ACH_operation['q_hw_W']

    return opex, co2, prim_energy, Qc_CT_W, Qh_CHP_W
