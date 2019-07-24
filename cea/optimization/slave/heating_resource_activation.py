from __future__ import division

import numpy as np

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.optimization.constants import T_LAKE, CC_ALLOWED
from cea.technologies.boiler import cond_boiler_op_cost
from cea.technologies.cogeneration import calc_cop_CCGT
from cea.technologies.constants import FURNACE_MIN_LOAD, BOILER_MIN
from cea.technologies.furnace import furnace_op_cost
from cea.technologies.heatpumps import GHP_op_cost, HPSew_op_cost, HPLake_op_cost, GHP_Op_max

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def heating_source_activator(Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_req_kgpers, Q_therm_Sew_W, TretsewArray_K, tdhsup_K, tdhret_req_K,
                             prices, lca, T_ground_K):
    """
    :param Q_therm_req_W:
    :param hour:
    :param context:
    :type Q_therm_req_W: float
    :type hour: int
    :type context: list
    :return: cost_data_centralPlant_op, source_info, Q_source_data, E_coldsource_data, E_PP_el_data, E_gas_data, E_wood_data, Q_excess
    :rtype:
    """

    # Initializing resulting values (necessairy as not all of them are over-written):


    # initialize all sources to be off = 0 (turn to "on" with setting to 1)
    #integer variables
    source_HP_Sewage = 0
    source_HP_Lake = 0
    source_GHP = 0
    source_CHP = 0
    source_Furnace = 0
    source_BaseBoiler = 0
    source_PeakBoiler = 0
    source_HP_DataCenter = 0

    #double variables
    Q_uncovered_W = 0.0
    cost_HPSew_USD, cost_HPLake_USD, cost_GHP_USD, cost_CHP_USD, cost_Furnace_USD, cost_BaseBoiler_USD, cost_PeakBoiler_USD = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    E_HPSew_req_W, E_HPLake_req_W, E_GHP_req_W, E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    Gas_used_HPSew_W, Gas_used_HPLake_W, Gas_used_GHP_W, Gas_used_CHP_W, Gas_used_Furnace_W, Gas_used_BaseBoiler_W, Gas_used_PeakBoiler_W = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    Wood_used_HPSew_W, Wood_used_HPLake_W, Wood_used_GHP_W, Wood_used_CHP_W, Wood_used_Furnace_W, Wood_used_BaseBoiler_W, Wood_used_PeakBoiler_W = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    Q_coldsource_HPSew_W, Q_coldsource_HPLake_W, Q_coldsource_GHP_W, Q_coldsource_CHP_W, \
    Q_coldsource_Furnace_W, Q_coldsource_BaseBoiler_W, Q_coldsource_PeakBoiler_W = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    ## initializing unmet heating load
    Q_heat_unmet_W = Q_therm_req_W
    if master_to_slave_vars.CC_on == 1 and Q_heat_unmet_W > 0:

        CC_op_cost_data = calc_cop_CCGT(master_to_slave_vars.CC_GT_SIZE_W, tdhsup_K, master_to_slave_vars.gt_fuel,
                                        prices, lca.ELEC_PRICE[hour])  # create cost information
        Q_used_prim_CC_fn_W = CC_op_cost_data['q_input_fn_q_output_W']
        cost_per_Wh_CC_fn = CC_op_cost_data['fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        q_output_CC_min_W = CC_op_cost_data['q_output_min_W']
        Q_output_CC_max_W = CC_op_cost_data['q_output_max_W']
        eta_elec_interpol = CC_op_cost_data['eta_el_fn_q_input']

        if Q_heat_unmet_W >= q_output_CC_min_W:
            source_CHP = 1
            # operation Possible if above minimal load
            if Q_heat_unmet_W < Q_output_CC_max_W:  # Normal operation Possible within partload regime
                Q_CHP_gen_W = Q_heat_unmet_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                Gas_used_CHP_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_CHP_gen_W = np.float(eta_elec_interpol(Gas_used_CHP_W)) * Gas_used_CHP_W
                cost_CHP_USD = cost_per_Wh_CC * Q_CHP_gen_W
            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                Gas_used_CHP_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_CHP_gen_W = np.float(eta_elec_interpol(Q_output_CC_max_W)) * Gas_used_CHP_W
                cost_CHP_USD = cost_per_Wh_CC * Q_CHP_gen_W
        else:
            source_CHP = 0
            Gas_used_CHP_W = 0.0
            E_CHP_gen_W = 0.0
            Q_CHP_gen_W = 0.0
            cost_CHP_USD = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_CHP_gen_W

    if master_to_slave_vars.Furnace_on == 1 and Q_heat_unmet_W > 0.0:  # Activate Furnace if its there.
        source_Furnace = 1
        # Operate only if its above minimal load
        if Q_heat_unmet_W > (FURNACE_MIN_LOAD * master_to_slave_vars.Furnace_Q_max_W):
            if Q_heat_unmet_W > master_to_slave_vars.Furnace_Q_max_W:  # scale down if above maximum load, Furnace operates at max. capacity
                Furnace_Cost_Data = furnace_op_cost(master_to_slave_vars.Furnace_Q_max_W,
                                                    master_to_slave_vars.Furnace_Q_max_W, tdhret_req_K,
                                                    master_to_slave_vars.Furn_Moist_type, lca, hour)

                cost_Furnace_USD = Furnace_Cost_Data[0]
                Wood_used_Furnace_W = Furnace_Cost_Data[2]
                Q_Furnace_gen_W = master_to_slave_vars.Furnace_Q_max_W
                E_Furnace_gen_W = Furnace_Cost_Data[4]

            else:  # Normal Operation Possible
                Furnace_Cost_Data = furnace_op_cost(Q_therm_req_W, master_to_slave_vars.Furnace_Q_max_W, tdhret_req_K,
                                                    master_to_slave_vars.Furn_Moist_type, lca, hour)

                Wood_used_Furnace_W = Furnace_Cost_Data[2]
                cost_Furnace_USD = Furnace_Cost_Data[0]
                Q_Furnace_gen_W = Q_heat_unmet_W
                E_Furnace_gen_W = Furnace_Cost_Data[4]
        else:
            source_Furnace = 0
            E_Furnace_gen_W = 0.0
            Wood_used_Furnace_W = 0.0
            Q_Furnace_gen_W = 0.0
            cost_Furnace_USD = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_Furnace_gen_W

    if (master_to_slave_vars.HP_Sew_on) == 1 and Q_heat_unmet_W > 0:  # activate if its available

        source_HP_Sewage = 1
        if Q_heat_unmet_W >= Q_therm_Sew_W:
            mdot_DH_to_Sew_kgpers = mdot_DH_req_kgpers * Q_therm_Sew_W / Q_heat_unmet_W
            Q_therm_Sew_gen_W = Q_therm_Sew_W
        else:
            Q_therm_Sew_gen_W = float(Q_heat_unmet_W)
            mdot_DH_to_Sew_kgpers = float(mdot_DH_req_kgpers)

        cost_HPSew_USD, C_HPSew_per_kWh_th_pure, \
        Q_coldsource_HPSew_W, Q_HPSew_gen_W, \
        E_HPSew_req_W = HPSew_op_cost(mdot_DH_to_Sew_kgpers,
                                      tdhsup_K, tdhret_req_K,
                                      TretsewArray_K, lca, Q_therm_Sew_gen_W, hour)

        Q_heat_unmet_W = Q_heat_unmet_W - Q_HPSew_gen_W

    if (master_to_slave_vars.HP_Lake_on) == 1 and Q_heat_unmet_W > 0 and not np.isclose(tdhsup_K, tdhret_req_K):
        source_HP_Lake = 1
        if Q_heat_unmet_W > master_to_slave_vars.HPLake_maxSize_W:  # Scale down Load, 100% load achieved
            Q_HPLake_gen_W = master_to_slave_vars.HPLake_maxSize_W
            mdot_DH_to_Lake_kgpers = Q_HPLake_gen_W / (
                    HEAT_CAPACITY_OF_WATER_JPERKGK * (
                    tdhsup_K - tdhret_req_K))  # scale down the mass flow if the thermal demand is lowered
        else:  # regular operation possible
            Q_HPLake_gen_W = Q_heat_unmet_W
            mdot_DH_to_Lake_kgpers = Q_HPLake_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))

        cost_HPLake_USD, E_HPLake_req_W, Q_coldsource_HPLake_W, Q_HPLake_gen_W = HPLake_op_cost(mdot_DH_to_Lake_kgpers,
                                                                                               tdhsup_K, tdhret_req_K,
                                                                                               T_LAKE, lca, hour)

        Q_heat_unmet_W = Q_heat_unmet_W - Q_HPLake_gen_W

    if (master_to_slave_vars.GHP_on) == 1 and \
            hour >= master_to_slave_vars.GHP_SEASON_ON and\
            hour <= master_to_slave_vars.GHP_SEASON_OFF and \
            Q_heat_unmet_W > 0 and not np.isclose(
            tdhsup_K, tdhret_req_K):

        source_GHP = 1
        # activating GHP plant if possible
        Q_max_GHP_W, GHP_COP = GHP_Op_max(tdhsup_K, T_ground_K, master_to_slave_vars.GHP_number)

        if Q_heat_unmet_W >= Q_max_GHP_W:
            Q_therm_GHP_W = Q_max_GHP_W
            mdot_DH_to_GHP_kgpers = Q_therm_GHP_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
        else:  # regular operation possible, demand is covered
            Q_therm_GHP_W = float(Q_heat_unmet_W)
            mdot_DH_to_GHP_kgpers = Q_therm_GHP_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))

        cost_GHP_USD, E_GHP_req_W, Q_coldsource_GHP_W, Q_GHP_gen_W = GHP_op_cost(mdot_DH_to_GHP_kgpers, tdhsup_K,
                                                                                 tdhret_req_K, GHP_COP, lca, hour)

        Q_heat_unmet_W = Q_heat_unmet_W - Q_GHP_gen_W


    if (master_to_slave_vars.Boiler_on) == 1 and Q_heat_unmet_W > 0:
        source_BaseBoiler = 1
        if Q_heat_unmet_W >= BOILER_MIN * master_to_slave_vars.Boiler_Q_max_W:  # Boiler can be activated?
            if Q_heat_unmet_W >= master_to_slave_vars.Boiler_Q_max_W:  # Boiler above maximum Load?
                Q_BaseBoiler_gen_W = master_to_slave_vars.Boiler_Q_max_W
            else:
                Q_BaseBoiler_gen_W = Q_heat_unmet_W

            cost_BaseBoiler_USD, C_boil_per_Wh, Gas_used_BaseBoiler_W, E_BaseBoiler_req_W = cond_boiler_op_cost(
                Q_BaseBoiler_gen_W, master_to_slave_vars.Boiler_Q_max_W, tdhret_req_K, master_to_slave_vars.BoilerType,
                prices, lca, hour)
        else:
            source_BaseBoiler = 0
            Q_BaseBoiler_gen_W = 0.0
            cost_BaseBoiler_USD = 0.0
            Gas_used_BaseBoiler_W = 0.0
            E_BaseBoiler_req_W = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_BaseBoiler_gen_W

    if (master_to_slave_vars.BoilerPeak_on) == 1 and Q_heat_unmet_W > 0:
        source_PeakBoiler = 1
        if Q_heat_unmet_W >= BOILER_MIN * master_to_slave_vars.BoilerPeak_Q_max_W:  # Boiler can be activated?
            if Q_heat_unmet_W > master_to_slave_vars.BoilerPeak_Q_max_W:  # Boiler above maximum Load?
                Q_PeakBoiler_gen_W = master_to_slave_vars.BoilerPeak_Q_max_W
            else:
                Q_PeakBoiler_gen_W = Q_heat_unmet_W

            cost_PeakBoiler_USD, C_boil_per_WhP, Gas_used_PeakBoiler_W, E_PeakBoiler_req_W = cond_boiler_op_cost(
                Q_PeakBoiler_gen_W, master_to_slave_vars.BoilerPeak_Q_max_W, tdhret_req_K,
                master_to_slave_vars.BoilerPeakType, prices, lca, hour)
        else:
            source_PeakBoiler = 0
            cost_PeakBoiler_USD = 0.0
            Q_PeakBoiler_gen_W = 0.0
            Gas_used_PeakBoiler_W = 0
            E_PeakBoiler_req_W = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_PeakBoiler_gen_W

    if Q_heat_unmet_W > 0:
        Q_uncovered_W = Q_heat_unmet_W # this will become the back-up boiler

    opex_output = {'Opex_var_HP_Sewage_USDhr': cost_HPSew_USD,
                   'Opex_var_HP_Lake_USDhr': cost_HPLake_USD,
                   'Opex_var_GHP_USDhr': cost_GHP_USD,
                   'Opex_var_CHP_USDhr': cost_CHP_USD,
                   'Opex_var_Furnace_USDhr': cost_Furnace_USD,
                   'Opex_var_BaseBoiler_USDhr': cost_BaseBoiler_USD,
                   'Opex_var_PeakBoiler_USDhr': cost_PeakBoiler_USD}

    source_output = {'Source_HP_Sewage': source_HP_Sewage,
                     'Source_HP_Lake': source_HP_Lake,
                     'Source_GHP': source_GHP,
                     'Source_CHP': source_CHP,
                     'Source_Furnace': source_Furnace,
                     'Source_BaseBoiler': source_BaseBoiler,
                     'Source_PeakBoiler': source_PeakBoiler}

    Q_output = {'Q_HPSew_gen_W': Q_HPSew_gen_W,
                'Q_HPLake_gen_W': Q_HPLake_gen_W,
                'Q_GHP_gen_W': Q_GHP_gen_W,
                'Q_CHP_gen_W': Q_CHP_gen_W,
                'Q_Furnace_gen_W': Q_Furnace_gen_W,
                'Q_BaseBoiler_gen_W': Q_BaseBoiler_gen_W,
                'Q_PeakBoiler_gen_W': Q_PeakBoiler_gen_W,
                'Q_AddBoiler_gen_W': Q_uncovered_W}

    E_output = {'E_HPSew_req_W': E_HPSew_req_W,
                'E_HPLake_req_W': E_HPLake_req_W,
                'E_GHP_req_W': E_GHP_req_W,
                'E_CHP_gen_W': E_CHP_gen_W,
                'E_Furnace_gen_W': E_Furnace_gen_W,
                'E_BaseBoiler_req_W': E_BaseBoiler_req_W,
                'E_PeakBoiler_req_W': E_PeakBoiler_req_W}

    Gas_output = {'Gas_used_HPSew_W': Gas_used_HPSew_W,
                  'Gas_used_HPLake_W': Gas_used_HPLake_W,
                  'Gas_used_GHP_W': Gas_used_GHP_W,
                  'Gas_used_CHP_W': Gas_used_CHP_W,
                  'Gas_used_Furnace_W': Gas_used_Furnace_W,
                  'Gas_used_BaseBoiler_W': Gas_used_BaseBoiler_W,
                  'Gas_used_PeakBoiler_W': Gas_used_PeakBoiler_W}

    Wood_output = {'Wood_used_HPSew_W': Wood_used_HPSew_W,
                   'Wood_used_HPLake_W': Wood_used_HPLake_W,
                   'Wood_used_GHP_W': Wood_used_GHP_W,
                   'Wood_used_CHP_W': Wood_used_CHP_W,
                   'Wood_used_Furnace_W': Wood_used_Furnace_W,
                   'Wood_used_BaseBoiler_W': Wood_used_BaseBoiler_W,
                   'Wood_used_PeakBoiler_W': Wood_used_PeakBoiler_W}

    coldsource_output = {'Q_coldsource_HPSew_W': Q_coldsource_HPSew_W,
                         'Q_coldsource_HPLake_W': Q_coldsource_HPLake_W,
                         'Q_coldsource_GHP_W': Q_coldsource_GHP_W,
                         'Q_coldsource_CHP_W': Q_coldsource_CHP_W,
                         'Q_coldsource_Furnace_W': Q_coldsource_Furnace_W,
                         'Q_coldsource_BaseBoiler_W': Q_coldsource_BaseBoiler_W,
                         'Q_coldsource_PeakBoiler_W': Q_coldsource_PeakBoiler_W}

    return opex_output, source_output, Q_output, E_output, Gas_output, Wood_output, coldsource_output
