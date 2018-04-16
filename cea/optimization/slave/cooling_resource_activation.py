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
from cea.technologies.constants import DT_COOL


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
    Qh_CHP_W = 0
    Qc_ACH_nom_W = Qc_from_ACH_W
    locator = cea.inputlocator.InputLocator(scenario=config.scenario) # TODO: move out
    chiller_prop = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Absorption_chiller",
                                 usecols=['cap_max', 'type'])
    chiller_prop = chiller_prop[chiller_prop['type'] == ACH_type]
    max_chiller_size = max(chiller_prop['cap_max'].values)
    if Qc_ACH_nom_W < max_chiller_size:  # activate one unit of ACH
        # calculate ACH operation
        if T_DCN_re_K == T_DCN_sup_K:
            mdot_ACH_kgpers = 0
        else:
            mdot_ACH_kgpers = Qc_from_ACH_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K,
                                                             ACH_T_IN_FROM_CHP, T_ground_K, ACH_type, Qc_ACH_nom_W,
                                                             locator, config)
        opex = (ACH_operation['wdot_W']) * prices.ELEC_PRICE
        co2 = (ACH_operation['wdot_W']) * EL_TO_CO2 * 3600E-6
        prim_energy = (ACH_operation['wdot_W']) * EL_TO_OIL_EQ * 3600E-6
        Qc_CT_W = ACH_operation['q_cw_W']
        Qh_CHP_W = ACH_operation['q_hw_W']
    else:  # more than one unit of ACH are activated
        number_of_chillers = int(math.ceil(Qc_ACH_nom_W / max_chiller_size))
        if T_DCN_re_K == T_DCN_sup_K:
            mdot_ACH_kgpers = 0
        else:
            mdot_ACH_kgpers = Qc_from_ACH_W / (
                (T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)  # required chw flow rate from ACH
        mdot_ACH_kgpers_per_chiller = mdot_ACH_kgpers / number_of_chillers
        for i in range(number_of_chillers):
            ACH_operation = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers_per_chiller, T_DCN_sup_K, T_DCN_re_K,
                                                                 ACH_T_IN_FROM_CHP,
                                                                 T_ground_K, ACH_type, Qc_ACH_nom_W, locator, config)
            if type(ACH_operation['wdot_W']) is int:
                opex = opex + (ACH_operation['wdot_W']) * prices.ELEC_PRICE
                co2 = co2 + (ACH_operation['wdot_W']) * EL_TO_CO2 * 3600E-6
                prim_energy = prim_energy + (ACH_operation['wdot_W']) * EL_TO_OIL_EQ * 3600E-6
                Qc_CT_W = Qc_CT_W + ACH_operation['q_cw_W']
                Qh_CHP_W = Qh_CHP_W + ACH_operation['q_hw_W']
            else:
                opex = opex + (ACH_operation['wdot_W'].values[0]) * prices.ELEC_PRICE
                co2 = co2 + (ACH_operation['wdot_W'].values[0]) * EL_TO_CO2 * 3600E-6
                prim_energy = prim_energy + (ACH_operation['wdot_W'].values[0]) * EL_TO_OIL_EQ * 3600E-6
                Qc_CT_W = Qc_CT_W + ACH_operation['q_cw_W']
                Qh_CHP_W = Qh_CHP_W + ACH_operation['q_hw_W']

    return opex, co2, prim_energy, Qc_CT_W, Qh_CHP_W


def cooling_resource_activator(DCN_cooling, limits, cooling_resource_potentials, T_ground_K, prices,
                               master_to_slave_variables, config, Q_cooling_req):
    """

    :param DCN_cooling:
    :param Qc_available_from_lake_W:
    :type Qc_available_from_lake_W: float
    :param Qc_from_lake_cumulative_W:
    :type Qc_from_lake_cumulative_W: float
    :param prices:
    :return:
    """

    # unpack variables
    T_tank_C = cooling_resource_potentials['T_tank_K'] - 273.0
    Qc_available_from_lake_W = cooling_resource_potentials['Qc_avail_from_lake_W']
    Qc_from_lake_cumulative_W = cooling_resource_potentials['Qc_from_lake_cumulative_W']

    # unpack variables
    V_tank_m3 = limits['V_tank_m3']
    Qc_tank_discharge_peak_W = limits['Qc_tank_discharge_peak_W']
    Qc_tank_charge_max_W = limits['Qc_tank_charge_max_W']
    T_tank_fully_charged_C = limits['T_tank_fully_charged_K'] - 273.0
    T_ground_C = T_ground_K - 273.0

    T_DCN_sup_K = DCN_cooling[0]
    T_DCN_re_K = DCN_cooling[1]
    mdot_DCN_kgpers = abs(DCN_cooling[2])

    opex_var_Lake = 0
    co2_output_Lake = 0
    prim_output_Lake = 0

    opex_var_VCC = []
    co2_VCC = []
    prim_energy_VCC = []

    opex_var_VCC_backup = []
    co2_VCC_backup = []
    prim_energy_VCC_backup = []

    opex_var_ACH = []
    co2_ACH = []
    prim_energy_ACH = []

    calfactor_output = 0

    Qc_from_Lake_W = 0
    Qc_from_VCC_W = 0
    Qc_from_ACH_W = 0
    Qc_from_Tank_W = 0
    Qc_from_backup_VCC_W = 0
    Qc_from_VCC_to_tank_W = 0
    Qc_to_tank_W = 0

    Qh_CHP_W = []
    Qc_CT_W = []

    ## initializing unmet cooling load
    Qc_load_unmet_W = Q_cooling_req

    ## activate lake cooling
    if Qc_load_unmet_W <= (Qc_available_from_lake_W - Qc_from_lake_cumulative_W) and Qc_load_unmet_W > 0:  # Free cooling possible from the lake

        Qc_from_Lake_W = Qc_load_unmet_W
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Lake_W
        Qc_from_lake_cumulative_W = Qc_from_lake_cumulative_W + Qc_from_Lake_W

        # Delta P from linearization after distribution optimization
        deltaP = 2 * (DELTA_P_COEFF * mdot_DCN_kgpers + DELTA_P_ORIGIN)
        calfactor_output = deltaP * (mdot_DCN_kgpers / 1000) / PUMP_ETA
        opex_var_Lake = deltaP * (mdot_DCN_kgpers / 1000) * prices.ELEC_PRICE / PUMP_ETA
        co2_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_CO2 / PUMP_ETA * 0.0036
        prim_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_OIL_EQ / PUMP_ETA * 0.0036

    ## activate cold thermal storage (fully mixed water tank)
    if Qc_load_unmet_W > limits['Qc_peak_load_W'] and T_tank_C < (
                T_DCN_sup_K - DT_COOL - 273.0):  # peak hour, discharge the storage

        Qc_from_Tank_W = Qc_load_unmet_W if Q_cooling_req <= Qc_tank_discharge_peak_W else Qc_tank_discharge_peak_W
        Qc_to_tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Tank_W

    elif Qc_load_unmet_W <= 0 and T_tank_C > T_tank_fully_charged_C:  # no-load, charge the storage
        Qc_to_tank_max_W = V_tank_m3 * P_WATER_KGPERM3 * HEAT_CAPACITY_OF_WATER_JPERKGK * (
            T_tank_C - T_tank_fully_charged_C)  # available to charge

        Qc_to_tank_W = Qc_tank_charge_max_W if Qc_to_tank_max_W > Qc_tank_charge_max_W else Qc_to_tank_max_W
        Qc_from_Tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)

    else:  # no charging/discharging
        Qc_from_Tank_W = 0
        Qc_to_tank_W = 0
        T_tank_C = storage_tank.calc_fully_mixed_tank(T_tank_C, T_ground_C, Qc_from_Tank_W, Qc_to_tank_W,
                                                      V_tank_m3)

    ## activate ACH and VCC to satify the remaining cooling loads
    if Qc_load_unmet_W > 0 and master_to_slave_variables.Absorption_Chiller_on == 1:
        # activate ACH
        Qc_from_ACH_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
        opex_var, co2, prim_energy, Qc_CT_ACH_W, Qh_CHP_ACH_W = calc_chiller_absorption_operation(
            Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, config)
        opex_var_ACH.append(opex_var)
        co2_ACH.append(co2)
        prim_energy_ACH.append(prim_energy)
        Qc_CT_W.append(Qc_CT_ACH_W)
        Qh_CHP_W.append(Qh_CHP_ACH_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_ACH_W

    if Qc_load_unmet_W > 0 and master_to_slave_variables.VCC_on == 1:
        # activate VCC
        Qc_from_VCC_W = Qc_load_unmet_W if Qc_load_unmet_W <= limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
        opex_var, co2, prim_energy, Qc_CT_VCC_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K,
                                                                     T_DCN_sup_K, prices)
        opex_var_VCC.append(opex_var)
        co2_VCC.append(co2)
        prim_energy_VCC.append(prim_energy)
        Qc_CT_W.append(Qc_CT_VCC_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_VCC_W

    if Qc_load_unmet_W > 0:
        # activate back-up VCC
        Qc_from_backup_VCC_W = Qc_load_unmet_W
        opex_var, co2, prim_energy, Qc_CT_VCC_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K,
                                                                                 T_DCN_sup_K, prices)
        opex_var_VCC_backup.append(opex_var)
        co2_VCC_backup.append(co2)
        prim_energy_VCC_backup.append(prim_energy)
        Qc_CT_W.append(Qc_CT_VCC_W)
        # update unmet cooling load
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_backup_VCC_W

    if Qc_load_unmet_W != 0:
        raise ValueError(
            'The cooling load is not met! Fix that calculation!')

    ## activate chillers to charge the thermal storage in order: VCC -> ACH -> VCC_backup
    if Qc_to_tank_W > 0:
        T_chiller_in_K = T_tank_C + 273.0  # temperature of a fully mixed tank
        T_chiller_out_K = (T_tank_fully_charged_C + 273.0) - DT_COOL

        if master_to_slave_variables.VCC_on == 1 and Qc_to_tank_W > 0: # activate VCC to charge the tank
            Qc_from_VCC_to_tank_W = Qc_to_tank_W if Qc_to_tank_W <= limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
            opex_var, co2, prim_energy, Qc_CT_VCC_W = calc_vcc_operation(Qc_from_VCC_to_tank_W, T_chiller_in_K,
                                                                         T_chiller_out_K, prices)
            opex_var_VCC.append(opex_var)
            co2_VCC.append(co2)
            prim_energy_VCC.append(prim_energy)
            Qc_CT_W.append(Qc_CT_VCC_W)
            Qc_to_tank_W -= Qc_from_VCC_to_tank_W

        if master_to_slave_variables.Absorption_Chiller_on == 1 and Qc_to_tank_W > 0: # activate ACH to charge the tank
            Qc_from_ACH_to_tank_W = Qc_to_tank_W if Qc_to_tank_W <= limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
            opex_var, co2, prim_energy, Qc_CT_ACH_W, Qh_CHP_ACH_W = calc_chiller_absorption_operation(
                Qc_from_ACH_to_tank_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, config)
            opex_var_ACH.append(opex_var)
            co2_ACH.append(co2)
            prim_energy_ACH.append(prim_energy)
            Qc_CT_W.append(Qc_CT_ACH_W)
            Qh_CHP_W.append(Qh_CHP_ACH_W)
            Qc_to_tank_W -= Qc_from_ACH_to_tank_W

        if Qc_to_tank_W > 0:
            raise ValueError(
                'There are no vapor compression chiller nor absorption chiller installed to charge the storage!')

    ## writing outputs
    performance_indicators_output = {'Opex_var_Lake': opex_var_Lake,
                                     'Opex_var_VCC': sum(opex_var_VCC),
                                     'Opex_var_ACH': sum(opex_var_ACH),
                                     'Opex_var_VCC_backup': sum(opex_var_VCC_backup),
                                     'CO2_Lake': co2_output_Lake,
                                     'CO2_VCC': sum(co2_VCC),
                                     'CO2_ACH': sum(co2_ACH),
                                     'CO2_VCC_backup': sum(co2_VCC_backup),
                                     'Primary_Energy_Lake': prim_output_Lake,
                                     'Primary_Energy_VCC': sum(prim_energy_VCC),
                                     'Primary_Energy_ACH': sum(prim_energy_ACH),
                                     'Primary_Energy_VCC_backup': sum(prim_energy_VCC_backup)}

    Qc_supply_to_DCN = {'Qc_from_Lake_W': Qc_from_Lake_W,
                        'Qc_from_VCC_W': Qc_from_VCC_W,
                        'Qc_from_ACH_W': Qc_from_ACH_W,
                        'Qc_from_Tank_W': Qc_from_Tank_W,
                        'Qc_from_backup_VCC_W': Qc_from_backup_VCC_W}

    cooling_resource_potentials_output = {'T_tank_K': T_tank_C + 273.0,
                                          'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                          'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}
    Qc_CT_tot_W = sum(Qc_CT_W)
    Qh_CHP_tot_W = sum(Qh_CHP_W)

    return performance_indicators_output, Qc_supply_to_DCN, calfactor_output, Qc_CT_tot_W, Qh_CHP_tot_W, cooling_resource_potentials_output
