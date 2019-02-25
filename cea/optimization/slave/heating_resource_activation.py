from __future__ import division
import numpy as np
from cea.optimization.constants import ACT_FIRST, HP_SEW_ALLOWED,T_LAKE, HP_LAKE_ALLOWED, CC_ALLOWED, BOILER_MIN, ACT_SECOND, ACT_THIRD, ACT_FOURTH
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.heatpumps import GHP_op_cost, HPSew_op_cost, HPLake_op_cost, GHP_Op_max
from cea.technologies.furnace import furnace_op_cost
from cea.technologies.cogeneration import calc_cop_CCGT
from cea.technologies.boiler import cond_boiler_op_cost

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def heating_source_activator(Q_therm_req_W, hour, master_to_slave_vars, mdot_DH_req_kgpers, tdhsup_K, tdhret_req_K, TretsewArray_K,
                             gv, prices, lca, T_ground, config):
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

    current_source = ACT_FIRST  # Start with first source, no cost yet
    Q_therm_req_W_copy = Q_therm_req_W
    # Initializing resulting values (necessairy as not all of them are over-written):
    Q_uncovered_W = 0
    cost_HPSew_USD, cost_HPLake_USD, cost_GHP_USD, cost_CHP_USD, cost_Furnace_USD, cost_BaseBoiler_USD, cost_PeakBoiler_USD = 0, 0, 0, 0, 0, 0, 0

    # initialize all sources to be off = 0 (turn to "on" with setting to 1)
    source_HP_Sewage = 0
    source_HP_Lake = 0
    source_GHP = 0
    source_CHP = 0
    source_Furnace = 0
    source_BaseBoiler = 0
    source_PeakBoiler = 0
    Q_excess_W = 0
    Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W = 0, 0, 0, 0, 0, 0, 0
    E_HPSew_req_W, E_HPLake_req_W, E_GHP_req_W, E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W = 0, 0, 0, 0, 0, 0, 0
    Gas_used_HPSew_W, Gas_used_HPLake_W, Gas_used_GHP_W, Gas_used_CHP_W, Gas_used_Furnace_W, Gas_used_BaseBoiler_W, Gas_used_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0
    Wood_used_HPSew_W, Wood_used_HPLake_W, Wood_used_GHP_W, Wood_used_CHP_W, Wood_used_Furnace_W, Wood_used_BaseBoiler_W, Wood_used_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0
    Q_coldsource_HPSew_W, Q_coldsource_HPLake_W, Q_coldsource_GHP_W, Q_coldsource_CHP_W, \
    Q_coldsource_Furnace_W, Q_coldsource_BaseBoiler_W, Q_coldsource_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0

    while Q_therm_req_W > 1E-1:  # cover demand as long as the supply is lower than demand!
        if current_source == 'HP':  # use heat pumps available!

            if (master_to_slave_vars.HP_Sew_on) == 1 and Q_therm_req_W > 0 and HP_SEW_ALLOWED == 1:  # activate if its available

                source_HP_Sewage = 0
                cost_HPSew_USD = 0.0
                Q_HPSew_gen_W = 0.0
                E_HPSew_req_W = 0.0
                Q_coldsource_HPSew_W = 0.0

                if Q_therm_req_W > master_to_slave_vars.HPSew_maxSize_W:
                    Q_therm_Sew_W = master_to_slave_vars.HPSew_maxSize_W
                    mdot_DH_to_Sew_kgpers = mdot_DH_req_kgpers * Q_therm_Sew_W / Q_therm_req_W.copy()  # scale down the mass flow if the thermal demand is lowered

                else:
                    Q_therm_Sew_W = float(Q_therm_req_W.copy())
                    mdot_DH_to_Sew_kgpers = float(mdot_DH_req_kgpers.copy())

                C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary_W, Q_HPSew_therm_W, E_HPSew_req_W = HPSew_op_cost(mdot_DH_to_Sew_kgpers, tdhsup_K, tdhret_req_K, TretsewArray_K,
                                                  lca, Q_therm_Sew_W, hour)
                Q_therm_req_W -= Q_HPSew_therm_W

                # Storing data for further processing
                if Q_HPSew_therm_W > 0:
                    source_HP_Sewage = 1
                cost_HPSew_USD = float(C_HPSew_el_pure)
                Q_HPSew_gen_W = float(Q_HPSew_therm_W)
                E_HPSew_req_W = float(E_HPSew_req_W)
                Q_coldsource_HPSew_W = float(Q_HPSew_cold_primary_W)

            if (master_to_slave_vars.GHP_on) == 1 and hour >= master_to_slave_vars.GHP_SEASON_ON and hour <= master_to_slave_vars.GHP_SEASON_OFF and Q_therm_req_W > 0 and not np.isclose(
                    tdhsup_K, tdhret_req_K):
                # activating GHP plant if possible

                source_GHP = 0
                cost_GHP_USD = 0.0
                Q_GHP_gen_W = 0.0
                E_GHP_req_W = 0.0
                Q_coldsource_GHP_W = 0.0

                Q_max_W, GHP_COP = GHP_Op_max(tdhsup_K, T_ground, master_to_slave_vars.GHP_number)

                if Q_therm_req_W > Q_max_W:
                    mdot_DH_to_GHP_kgpers = Q_max_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W -= Q_max_W

                else:  # regular operation possible, demand is covered
                    mdot_DH_to_GHP_kgpers = Q_therm_req_W.copy() / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W = 0

                C_GHP_el, E_GHP_req_W, Q_GHP_cold_primary_W, Q_GHP_therm_W = GHP_op_cost(mdot_DH_to_GHP_kgpers, tdhsup_K, tdhret_req_K, GHP_COP, lca, hour)

                # Storing data for further processing
                source_GHP = 1
                cost_GHP_USD = C_GHP_el
                Q_GHP_gen_W = Q_GHP_therm_W
                E_GHP_req_W = E_GHP_req_W
                Q_coldsource_GHP_W = Q_GHP_cold_primary_W

            if (master_to_slave_vars.HP_Lake_on) == 1 and Q_therm_req_W > 0 and HP_LAKE_ALLOWED == 1 and not np.isclose(tdhsup_K,
                                                                                                          tdhret_req_K):  # run Heat Pump Lake
                source_HP_Lake = 0
                cost_HPLake_USD = 0
                Q_HPLake_gen_W = 0
                E_HPLake_req_W = 0
                Q_coldsource_HPLake_W = 0

                if Q_therm_req_W > master_to_slave_vars.HPLake_maxSize_W:  # Scale down Load, 100% load achieved
                    Q_therm_HPL_W = master_to_slave_vars.HPLake_maxSize_W
                    mdot_DH_to_Lake_kgpers = Q_therm_HPL_W / (
                            HEAT_CAPACITY_OF_WATER_JPERKGK * (
                            tdhsup_K - tdhret_req_K))  # scale down the mass flow if the thermal demand is lowered
                    Q_therm_req_W -= master_to_slave_vars.HPLake_maxSize_W

                else:  # regular operation possible
                    Q_therm_HPL_W = Q_therm_req_W.copy()
                    mdot_DH_to_Lake_kgpers = Q_therm_HPL_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W = 0
                C_HPL_el, E_HPLake_req_W, Q_HPL_cold_primary_W, Q_HPL_therm_W = HPLake_op_cost(mdot_DH_to_Lake_kgpers, tdhsup_K, tdhret_req_K, T_LAKE, lca, hour)

                # Storing Data
                source_HP_Lake = 1
                cost_HPLake_USD = C_HPL_el
                Q_HPLake_gen_W = Q_therm_HPL_W
                E_HPLake_req_W = E_HPLake_req_W
                Q_coldsource_HPLake_W = Q_HPL_cold_primary_W

        if current_source == 'CHP' and Q_therm_req_W > 0:  # start activating the combined cycles

            # By definition, one can either activate the CHP (NG-CC) or ORC (Furnace) BUT NOT BOTH at the same time (not activated by Master)
            Cost_CC = 0.0
            source_CHP = 0
            cost_CHP_USD = 0.0
            Q_CHP_gen_W = 0.0
            Gas_used_CHP_W = 0.0
            E_CHP_gen_W = 0

            if (master_to_slave_vars.CC_on) == 1 and Q_therm_req_W > 0 and CC_ALLOWED == 1:  # only operate if the plant is available
                CC_op_cost_data = calc_cop_CCGT(master_to_slave_vars.CC_GT_SIZE_W, tdhsup_K, master_to_slave_vars.gt_fuel,
                                                prices, lca.ELEC_PRICE[hour])  # create cost information
                Q_used_prim_CC_fn_W = CC_op_cost_data['q_input_fn_q_output_W']
                cost_per_Wh_CC_fn = CC_op_cost_data['fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
                q_output_CC_min_W = CC_op_cost_data['q_output_min_W']
                Q_output_CC_max_W = CC_op_cost_data['q_output_max_W']
                eta_elec_interpol = CC_op_cost_data['eta_el_fn_q_input']

                if Q_therm_req_W > q_output_CC_min_W:  # operation Possible if above minimal load
                    if Q_therm_req_W < Q_output_CC_max_W:  # Normal operation Possible within partload regime
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req_W)
                        Q_used_prim_CC_W = Q_used_prim_CC_fn_W(Q_therm_req_W)
                        Q_CC_delivered_W = Q_therm_req_W.copy()
                        Q_therm_req_W = 0
                        E_CHP_gen_W = np.float(eta_elec_interpol(Q_used_prim_CC_W)) * Q_used_prim_CC_W


                    else:  # Only part of the demand can be delivered as 100% load achieved
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_output_CC_max_W)
                        Q_used_prim_CC_W = Q_used_prim_CC_fn_W(Q_output_CC_max_W)
                        Q_CC_delivered_W = Q_output_CC_max_W
                        Q_therm_req_W -= Q_output_CC_max_W
                        E_CHP_gen_W = np.float(eta_elec_interpol(Q_output_CC_max_W)) * Q_used_prim_CC_W

                    Cost_CC = cost_per_Wh_CC * Q_CC_delivered_W
                    source_CHP = 1
                    cost_CHP_USD = Cost_CC
                    Q_CHP_gen_W = Q_CC_delivered_W
                    Gas_used_CHP_W = Q_used_prim_CC_W

            if (master_to_slave_vars.Furnace_on) == 1 and Q_therm_req_W > 0:  # Activate Furnace if its there. By definition, either ORC or NG-CC!
                Q_Furn_therm_W = 0
                source_Furnace = 0
                cost_Furnace_USD = 0.0
                Q_Furnace_gen_W = 0.0
                Wood_used_Furnace_W = 0.0
                Q_Furn_prim_W = 0.0

                if Q_therm_req_W > (
                        gv.Furn_min_Load * master_to_slave_vars.Furnace_Q_max_W):  # Operate only if its above minimal load

                    if Q_therm_req_W > master_to_slave_vars.Furnace_Q_max_W:  # scale down if above maximum load, Furnace operates at max. capacity
                        Furnace_Cost_Data = furnace_op_cost(master_to_slave_vars.Furnace_Q_max_W, master_to_slave_vars.Furnace_Q_max_W, tdhret_req_K,
                                                            master_to_slave_vars.Furn_Moist_type, lca, hour)

                        C_Furn_therm = Furnace_Cost_Data[0]
                        Q_Furn_prim_W = Furnace_Cost_Data[2]
                        Q_Furn_therm_W = master_to_slave_vars.Furnace_Q_max_W
                        Q_therm_req_W -= Q_Furn_therm_W
                        E_Furnace_gen_W = Furnace_Cost_Data[4]

                    else:  # Normal Operation Possible
                        Furnace_Cost_Data = furnace_op_cost(Q_therm_req_W, master_to_slave_vars.Furnace_Q_max_W, tdhret_req_K,
                                                            master_to_slave_vars.Furn_Moist_type, lca, hour)

                        Q_Furn_prim_W = Furnace_Cost_Data[2]
                        C_Furn_therm = Furnace_Cost_Data[0]
                        Q_Furn_therm_W = Q_therm_req_W.copy()
                        E_Furnace_gen_W = Furnace_Cost_Data[4]

                        Q_therm_req_W = 0

                    source_Furnace = 1
                    cost_Furnace_USD = C_Furn_therm.copy()
                    Q_Furnace_gen_W = Q_Furn_therm_W
                    Wood_used_Furnace_W = Q_Furn_prim_W


        if current_source == 'BoilerBase' and Q_therm_req_W > 0:

            Q_therm_boiler_W = 0
            if (master_to_slave_vars.Boiler_on) == 1:
                source_BaseBoiler = 0
                cost_BaseBoiler_USD = 0.0
                Q_BaseBoiler_gen_W = 0.0
                Gas_used_BaseBoiler_W = 0.0
                E_BaseBoiler_req_W = 0.0

                if Q_therm_req_W >= BOILER_MIN * master_to_slave_vars.Boiler_Q_max_W:  # Boiler can be activated?
                    # Q_therm_boiler = Q_therm_req

                    if Q_therm_req_W >= master_to_slave_vars.Boiler_Q_max_W:  # Boiler above maximum Load?
                        Q_therm_boiler_W = master_to_slave_vars.Boiler_Q_max_W
                    else:
                        Q_therm_boiler_W = Q_therm_req_W.copy()

                    C_boil_therm, C_boil_per_Wh, Q_primary_W, E_aux_Boiler_req_W = cond_boiler_op_cost(Q_therm_boiler_W, master_to_slave_vars.Boiler_Q_max_W, tdhret_req_K, \
                                                           master_to_slave_vars.BoilerType, master_to_slave_vars.EL_TYPE, prices, lca, hour)

                    source_BaseBoiler = 1
                    cost_BaseBoiler_USD = C_boil_therm
                    Q_BaseBoiler_gen_W = Q_therm_boiler_W
                    Gas_used_BaseBoiler_W = Q_primary_W
                    E_BaseBoiler_req_W = E_aux_Boiler_req_W
                    Q_therm_req_W -= Q_therm_boiler_W


        if current_source == 'BoilerPeak' and Q_therm_req_W > 0:

            if (master_to_slave_vars.BoilerPeak_on) == 1:
                source_PeakBoiler = 0
                cost_PeakBoiler_USD = 0.0
                Q_PeakBoiler_gen_W = 0.0
                Gas_used_PeakBoiler_W = 0
                E_PeakBoiler_req_W = 0

                if Q_therm_req_W > 0:  # gv.Boiler_min*master_to_slave_vars.BoilerPeak_Q_max: # Boiler can be activated?

                    if Q_therm_req_W > master_to_slave_vars.BoilerPeak_Q_max_W:  # Boiler above maximum Load?
                        Q_therm_boilerP_W = master_to_slave_vars.BoilerPeak_Q_max_W
                        Q_therm_req_W -= Q_therm_boilerP_W
                    else:
                        Q_therm_boilerP_W = Q_therm_req_W.copy()
                        Q_therm_req_W = 0

                    C_boil_thermP, C_boil_per_WhP, Q_primaryP_W, E_aux_BoilerP_W = cond_boiler_op_cost(Q_therm_boilerP_W, master_to_slave_vars.BoilerPeak_Q_max_W, tdhret_req_K, \
                                                            master_to_slave_vars.BoilerPeakType, master_to_slave_vars.EL_TYPE, prices, lca, hour)

                    source_PeakBoiler = 1
                    cost_PeakBoiler_USD = C_boil_thermP
                    Q_PeakBoiler_gen_W = Q_therm_boilerP_W
                    Gas_used_PeakBoiler_W = Q_primaryP_W
                    E_PeakBoiler_req_W = E_aux_BoilerP_W

        Q_excess_W = 0
        if np.floor(Q_therm_req_W) > 0:
            if current_source == ACT_FIRST:
                current_source = ACT_SECOND
            elif current_source == ACT_SECOND:
                current_source = ACT_THIRD
            elif current_source == ACT_THIRD:
                current_source = ACT_FOURTH
            else:
                Q_uncovered_W = Q_therm_req_W
                break

        elif round(Q_therm_req_W, 0) != 0:
            Q_uncovered_W = 0  # Q_therm_req
            Q_excess_W = -Q_therm_req_W
            Q_therm_req_W = 0
            # break
        else:
            Q_therm_req_W = 0

    source_info = source_HP_Sewage, source_HP_Lake, source_GHP, source_CHP, source_Furnace, source_BaseBoiler, source_PeakBoiler
    Q_source_data_W = Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W
    E_PP_el_data_W = E_HPSew_req_W, E_HPLake_req_W, E_GHP_req_W, E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W
    E_gas_data_W = Gas_used_HPSew_W, Gas_used_HPLake_W, Gas_used_GHP_W, Gas_used_CHP_W, Gas_used_Furnace_W, Gas_used_BaseBoiler_W, Gas_used_PeakBoiler_W
    E_wood_data_W = Wood_used_HPSew_W, Wood_used_HPLake_W, Wood_used_GHP_W, Wood_used_CHP_W, Wood_used_Furnace_W, Wood_used_BaseBoiler_W, Wood_used_PeakBoiler_W
    E_coldsource_data_W = Q_coldsource_HPSew_W, Q_coldsource_HPLake_W, Q_coldsource_GHP_W, Q_coldsource_CHP_W, \
                          Q_coldsource_Furnace_W, Q_coldsource_BaseBoiler_W, Q_coldsource_PeakBoiler_W

    opex_output = {'Opex_var_HP_Sewage_USD':cost_HPSew_USD,
              'Opex_var_HP_Lake_USD': cost_HPLake_USD,
              'Opex_var_GHP_USD': cost_GHP_USD,
              'Opex_var_CHP_USD': cost_CHP_USD,
              'Opex_var_Furnace_USD': cost_Furnace_USD,
              'Opex_var_BaseBoiler_USD': cost_BaseBoiler_USD,
              'Opex_var_PeakBoiler_USD': cost_PeakBoiler_USD}

    source_output = {'HP_Sewage': source_HP_Sewage,
                     'HP_Lake': source_HP_Lake,
                     'GHP': source_GHP,
                     'CHP': source_CHP,
                     'Furnace': source_Furnace,
                     'BaseBoiler': source_BaseBoiler,
                     'PeakBoiler': source_PeakBoiler}

    Q_output = {'Q_HPSew_gen_W': Q_HPSew_gen_W,
                'Q_HPLake_gen_W': Q_HPLake_gen_W,
                'Q_GHP_gen_W': Q_GHP_gen_W,
                'Q_CHP_gen_W': Q_CHP_gen_W,
                'Q_Furnace_gen_W': Q_Furnace_gen_W,
                'Q_BaseBoiler_gen_W': Q_BaseBoiler_gen_W,
                'Q_PeakBoiler_gen_W': Q_PeakBoiler_gen_W,
                'Q_uncovered_W': Q_uncovered_W}

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

    return opex_output, source_output, Q_output, E_output, Gas_output, Wood_output, coldsource_output, Q_excess_W


