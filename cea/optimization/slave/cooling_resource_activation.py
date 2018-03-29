from __future__ import division
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.constants import DELTA_P_COEFF, DELTA_P_ORIGIN, PUMP_ETA, EL_TO_OIL_EQ, EL_TO_CO2
import cea.technologies.chiller_vapor_compression as chiller_vapor_compression
import cea.technologies.chiller_absorption as chiller_absorption
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK


def cooling_resource_activator(DCN_cooling, Qc_available_from_lake_W, Q_from_lake_cumulative_W, limits, T_ground_K,
                               prices):
    """

    :param DCN_cooling:
    :param Qc_available_from_lake_W:
    :type Qc_available_from_lake_W: float
    :param Q_from_lake_cumulative_W:
    :type Q_from_lake_cumulative_W: float
    :param prices:
    :return:
    """

    config = cea.config.Configuration()  # TODO: maybe pass config as an argument

    T_DCN_sup_K = DCN_cooling[0]
    T_DCN_re_K = DCN_cooling[1]
    mdot_DCN_kgpers = abs(DCN_cooling[2])

    Qc_load_W = abs(mdot_DCN_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_DCN_re_K - T_DCN_sup_K))

    opex_var_Lake = 0
    opex_var_VCC = 0
    co2_output_Lake = 0
    co2_VCC = 0
    prim_output_Lake = 0
    prim_energy_VCC = 0
    calfactor_output = 0

    Qc_from_Lake_W = 0
    Qc_from_VCC_W = 0

    Qc_CT_W = 0
    Qc_load_unmet_W = Qc_load_W

    if Qc_load_W <= (Qc_available_from_lake_W - Q_from_lake_cumulative_W):  # Free cooling possible from the lake

        Qc_from_Lake_W = Qc_load_W
        Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Lake_W

        # Delta P from linearization after distribution optimization
        deltaP = 2 * (DELTA_P_COEFF * mdot_DCN_kgpers + DELTA_P_ORIGIN)
        calfactor_output = deltaP * (mdot_DCN_kgpers / 1000) / PUMP_ETA
        opex_var_Lake = deltaP * (mdot_DCN_kgpers / 1000) * prices.ELEC_PRICE / PUMP_ETA
        co2_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_CO2 / PUMP_ETA * 0.0036
        prim_output_Lake = deltaP * (mdot_DCN_kgpers / 1000) * EL_TO_OIL_EQ / PUMP_ETA * 0.0036


    elif Qc_load_W > limits['Qc_peak_W'] and limits['Qc_tank_avail_W'] > 0:  # peak hour

        if limits['Qc_tank_avail_W'] > 0:  # discharge from tank
            Qc_from_Tank_W = Qc_load_W if Qc_load_W <= limits['Qc_tank_discharged_W'] else limits[
                'Qc_tank_discharged_W']
            Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_Tank_W
            limits['Qc_tank_avail_W'] -= Qc_from_Tank_W  # FIXME: calculate tank temperatures...

        if Qc_load_unmet_W > 0:
            # activate ACH
            Qc_from_ACH_W = Qc_load_unmet_W if Qc_load_unmet_W > limits['Qc_ACH_max_W'] else limits['Qc_ACH_max_W']
            mdot_VCC_kgpers = Qc_from_VCC_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)

            Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_ACH_W

            if Qc_load_unmet_W > 0:
                # activate VCC
                Qc_from_VCC_W = Qc_load_unmet_W if Qc_load_unmet_W > limits['Qc_VCC_max_W'] else limits['Qc_VCC_max_W']
                opex_var_VCC, co2_VCC, prim_energy_VCC, Qc_CT_W = calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K,
                                                                                     T_DCN_sup_K, prices)
                # unmet loads
                Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_VCC_W

                if Qc_load_unmet_W > 0:
                    # activate back-up VCC
                    Qc_from_backup_VCC_W = Qc_load_unmet_W
                    Qc_load_unmet_W = Qc_load_unmet_W - Qc_from_backup_VCC_W

    opex_output = {'Opex_var_Lake': opex_var_Lake,
                   'Opex_var_VCC': opex_var_VCC}

    co2_output = {'CO2_Lake': co2_output_Lake,
                  'CO2_VCC': co2_VCC}

    prim_output = {'Primary_Energy_Lake': prim_output_Lake,
                   'Primary_Energy_VCC': prim_energy_VCC}

    Qc_supply_output = {'Qc_from_Lake_W': Qc_from_Lake_W,
                        'Qc_from_VCC_W': Qc_from_VCC_W}

    return opex_output, co2_output, prim_output, Qc_supply_output, calfactor_output, Qc_CT_W


def calc_vcc_operation(Qc_from_VCC_W, T_DCN_re_K, T_DCN_sup_K, prices):
    mdot_VCC_kgpers = Qc_from_VCC_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    wdot_W, qhotdot_W = chiller_vapor_compression.calc_VCC(mdot_VCC_kgpers, T_DCN_sup_K, T_DCN_re_K)
    opex = wdot_W * prices.ELEC_PRICE
    co2 = wdot_W * EL_TO_CO2 * 3600E-6
    prim_energy = wdot_W * EL_TO_OIL_EQ * 3600E-6
    Qc_CT_W = qhotdot_W
    return opex, co2, prim_energy, Qc_CT_W


def calc_chiller_absorption_operation(Qc_from_ACH_W, T_DCN_re_K, T_DCN_sup_K, T_ground_K, prices, config):
    T_hw_in_CHP_C = 150  # FIXME: take from cogen
    ACH_type_double = 'double'
    Qc_ACH_nom_W = Qc_from_ACH_W  # FIXME: this should be the capacity from master
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)  # FIXME: move out
    mdot_ACH_kgpers = Qc_from_ACH_W / ((T_DCN_re_K - T_DCN_sup_K) * HEAT_CAPACITY_OF_WATER_JPERKGK)
    wdot_W, qhotdot_W = chiller_absorption.calc_chiller_main(mdot_ACH_kgpers, T_DCN_sup_K, T_DCN_re_K, T_hw_in_CHP_C,
                                                             T_ground_K, ACH_type_double, Qc_ACH_nom_W, locator)
    opex = wdot_W * prices.ELEC_PRICE
    co2 = wdot_W * EL_TO_CO2 * 3600E-6
    prim_energy = wdot_W * EL_TO_OIL_EQ * 3600E-6
    Qc_CT_W = qhotdot_W
    return opex, co2, prim_energy, Qc_CT_W
