from __future__ import division
import copy
import numpy as np
from cea.optimization.constants import *
from cea.optimization import prices
import pandas as pd

from cea.technologies.heatpumps import GHP_op_cost, HPSew_op_cost, HPLake_op_cost, GHP_Op_max
from cea.technologies.furnace import furnace_op_cost
from cea.technologies.cogeneration import calc_Cop_CCT
from cea.technologies.boilers import cond_boiler_op_cost


def heating_source_activator(Q_therm_req_W, hour, context, mdot_DH_req_kgpers, tdhsup_K, tdhret_req_K, TretsewArray_K,
                             gv, prices):
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
    # print (hour)
    MS_Var = context
    current_source = act_first  # Start with first source, no cost yet

    # Initializing resulting values (necessairy as not all of them are over-written):
    Q_uncovered_W = 0
    cost_HPSew, cost_HPLake, cost_GHP, cost_CHP, cost_Furnace, cost_BaseBoiler, cost_PeakBoiler = 0, 0, 0, 0, 0, 0, 0

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
    E_gas_HPSew_W, E_gas_HPLake_W, E_gas_GHP_W, E_gas_CHP_W, E_gas_Furnace_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0
    E_wood_HPSew_W, E_wood_HPLake_W, E_wood_GHP_W, E_wood_CHP_W, E_wood_Furnace_W, E_wood_BaseBoiler_W, E_wood_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0
    E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W, E_coldsource_CHP_W, \
    E_coldsource_Furnace_W, E_coldsource_BaseBoiler_W, E_coldsource_PeakBoiler_W = 0, 0, 0, 0, 0, 0, 0

    while Q_therm_req_W > 1E-1:  # cover demand as long as the supply is lower than demand!
        if current_source == 'HP':  # use heat pumps available!

            if (MS_Var.HP_Sew_on) == 1 and Q_therm_req_W > 0 and HPSew_allowed == 1:  # activate if its available

                source_HP_Sewage = 0
                cost_HPSew = 0.0
                Q_HPSew_gen_W = 0.0
                E_HPSew_req_W = 0.0
                E_coldsource_HPSew_W = 0.0

                if Q_therm_req_W > MS_Var.HPSew_maxSize:
                    Q_therm_Sew_W = MS_Var.HPSew_maxSize
                    mdot_DH_to_Sew_kgpers = mdot_DH_req_kgpers * Q_therm_Sew_W / Q_therm_req_W.copy()  # scale down the mass flow if the thermal demand is lowered

                else:
                    Q_therm_Sew_W = float(Q_therm_req_W.copy())
                    mdot_DH_to_Sew_kgpers = float(mdot_DH_req_kgpers.copy())

                HP_Sew_Cost_Data = HPSew_op_cost(mdot_DH_to_Sew_kgpers, tdhsup_K, tdhret_req_K, TretsewArray_K,
                                                 gv, prices)
                C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary_W, Q_HPSew_therm_W, E_HPSew_req_W = HP_Sew_Cost_Data
                Q_therm_req_W -= Q_HPSew_therm_W

                # Storing data for further processing
                if Q_HPSew_therm_W > 0:
                    source_HP_Sewage = 1
                cost_HPSew = float(C_HPSew_el_pure)
                Q_HPSew_gen_W = float(Q_HPSew_therm_W)
                E_HPSew_req_W = float(E_HPSew_req_W)
                E_coldsource_HPSew_W = float(Q_HPSew_cold_primary_W)

            if (
            MS_Var.GHP_on) == 1 and hour >= MS_Var.GHP_SEASON_ON and hour <= MS_Var.GHP_SEASON_OFF and Q_therm_req_W > 0 and not np.isclose(
                    tdhsup_K, tdhret_req_K):
                # activating GHP plant if possible

                source_GHP = 0
                cost_GHP = 0.0
                Q_GHP_gen_W = 0.0
                E_GHP_req_W = 0.0
                E_coldsource_GHP_W = 0.0

                Q_max_W, GHP_COP = GHP_Op_max(tdhsup_K, TGround, MS_Var.GHP_number, gv)

                if Q_therm_req_W > Q_max_W:
                    mdot_DH_to_GHP_kgpers = Q_max_W / (gv.cp * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W -= Q_max_W

                else:  # regular operation possible, demand is covered
                    mdot_DH_to_GHP_kgpers = Q_therm_req_W.copy() / (gv.cp * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W = 0

                GHP_Cost_Data = GHP_op_cost(mdot_DH_to_GHP_kgpers, tdhsup_K, tdhret_req_K, gv, GHP_COP, prices)
                C_GHP_el, E_GHP_req_W, Q_GHP_cold_primary_W, Q_GHP_therm_W = GHP_Cost_Data

                # Storing data for further processing
                source_GHP = 1
                cost_GHP = C_GHP_el
                Q_GHP_gen_W = Q_GHP_therm_W
                E_GHP_req_W = E_GHP_req_W
                E_coldsource_GHP_W = Q_GHP_cold_primary_W

            if (MS_Var.HP_Lake_on) == 1 and Q_therm_req_W > 0 and HPLake_allowed == 1 and not np.isclose(tdhsup_K,
                                                                                                         tdhret_req_K):  # run Heat Pump Lake
                source_HP_Lake = 0
                cost_HPLake = 0
                Q_HPLake_gen_W = 0
                E_HPLake_req_W = 0
                E_coldsource_HPLake_W = 0

                if Q_therm_req_W > MS_Var.HPLake_maxSize:  # Scale down Load, 100% load achieved
                    Q_therm_HPL_W = MS_Var.HPLake_maxSize
                    mdot_DH_to_Lake_kgpers = Q_therm_HPL_W / (
                            gv.cp * (
                            tdhsup_K - tdhret_req_K))  # scale down the mass flow if the thermal demand is lowered
                    Q_therm_req_W -= MS_Var.HPLake_maxSize

                else:  # regular operation possible
                    Q_therm_HPL_W = Q_therm_req_W.copy()
                    mdot_DH_to_Lake_kgpers = Q_therm_HPL_W / (gv.cp * (tdhsup_K - tdhret_req_K))
                    Q_therm_req_W = 0
                HP_Lake_Cost_Data = HPLake_op_cost(mdot_DH_to_Lake_kgpers, tdhsup_K, tdhret_req_K, TLake, gv, prices)
                C_HPL_el, E_HPLake_req_W, Q_HPL_cold_primary_W, Q_HPL_therm_W = HP_Lake_Cost_Data

                # Storing Data
                source_HP_Lake = 1
                cost_HPLake = C_HPL_el
                Q_HPLake_gen_W = Q_therm_HPL_W
                E_HPLake_req_W = E_HPLake_req_W
                E_coldsource_HPLake_W = Q_HPL_cold_primary_W

        if current_source == 'CHP' and Q_therm_req_W > 0:  # start activating the combined cycles

            # By definition, one can either activate the CHP (NG-CC) or ORC (Furnace) BUT NOT BOTH at the same time (not activated by Master)
            Cost_CC = 0.0
            source_CHP = 0
            cost_CHP = 0.0
            Q_CHP_gen_W = 0.0
            E_gas_CHP_W = 0.0
            E_CHP_gen_W = 0

            if (
                    MS_Var.CC_on) == 1 and Q_therm_req_W > 0 and CC_allowed == 1:  # only operate if the plant is available
                CC_op_cost_data = calc_Cop_CCT(MS_Var.CC_GT_SIZE, tdhsup_K, MS_Var.gt_fuel,
                                               gv, prices)  # create cost information
                Q_used_prim_CC_fn_W = CC_op_cost_data[1]
                cost_per_Wh_CC_fn = CC_op_cost_data[2]  # gets interpolated cost function
                Q_CC_min_W = CC_op_cost_data[3]
                Q_CC_max_W = CC_op_cost_data[4]
                eta_elec_interpol = CC_op_cost_data[5]

                if Q_therm_req_W > Q_CC_min_W:  # operation Possible if above minimal load
                    if Q_therm_req_W < Q_CC_max_W:  # Normal operation Possible within partload regime
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req_W)
                        Q_used_prim_CC_W = Q_used_prim_CC_fn_W(Q_therm_req_W)
                        Q_CC_delivered_W = Q_therm_req_W.copy()
                        Q_therm_req_W = 0
                        E_CHP_gen_W = np.float(eta_elec_interpol(Q_used_prim_CC_W)) * Q_used_prim_CC_W


                    else:  # Only part of the demand can be delivered as 100% load achieved
                        cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CC_max_W)
                        Q_used_prim_CC_W = Q_used_prim_CC_fn_W(Q_CC_max_W)
                        Q_CC_delivered_W = Q_CC_max_W
                        Q_therm_req_W -= Q_CC_max_W
                        E_CHP_gen_W = np.float(eta_elec_interpol(Q_CC_max_W)) * Q_used_prim_CC_W

                    Cost_CC = cost_per_Wh_CC * Q_CC_delivered_W
                    source_CHP = 1
                    cost_CHP = Cost_CC
                    Q_CHP_gen_W = Q_CC_delivered_W
                    E_gas_CHP_W = Q_used_prim_CC_W

            if (MS_Var.Furnace_on) == 1 and Q_therm_req_W > 0:  # Activate Furnace if its there. By definition, either ORC or NG-CC!
                Q_Furn_therm_W = 0
                source_Furnace = 0
                cost_Furnace = 0.0
                Q_Furnace_gen_W = 0.0
                E_wood_Furnace_W = 0.0
                Q_Furn_prim_W = 0.0

                if Q_therm_req_W > (
                        gv.Furn_min_Load * MS_Var.Furnace_Q_max):  # Operate only if its above minimal load

                    if Q_therm_req_W > MS_Var.Furnace_Q_max:  # scale down if above maximum load, Furnace operates at max. capacity
                        Furnace_Cost_Data = furnace_op_cost(MS_Var.Furnace_Q_max, MS_Var.Furnace_Q_max, tdhret_req_K,
                                                            MS_Var.Furn_Moist_type, gv)

                        C_Furn_therm = Furnace_Cost_Data[0]
                        Q_Furn_prim_W = Furnace_Cost_Data[2]
                        Q_Furn_therm_W = MS_Var.Furnace_Q_max
                        Q_therm_req_W -= Q_Furn_therm_W
                        E_Furnace_gen_W = Furnace_Cost_Data[4]

                    else:  # Normal Operation Possible
                        Furnace_Cost_Data = furnace_op_cost(Q_therm_req_W, MS_Var.Furnace_Q_max, tdhret_req_K,
                                                            MS_Var.Furn_Moist_type, gv)

                        Q_Furn_prim_W = Furnace_Cost_Data[2]
                        C_Furn_therm = Furnace_Cost_Data[0]
                        Q_Furn_therm_W = Q_therm_req_W.copy()
                        E_Furnace_gen_W = Furnace_Cost_Data[4]

                        Q_therm_req_W = 0

                    source_Furnace = 1
                    cost_Furnace = C_Furn_therm.copy()
                    Q_Furnace_gen_W = Q_Furn_therm_W
                    E_wood_Furnace_W = Q_Furn_prim_W


        if current_source == 'BoilerBase' and Q_therm_req_W > 0:

            Q_therm_boiler_W = 0
            if (MS_Var.Boiler_on) == 1:
                source_BaseBoiler = 0
                cost_BaseBoiler = 0.0
                Q_BaseBoiler_gen_W = 0.0
                E_gas_BaseBoiler_W = 0.0
                E_BaseBoiler_req_W = 0.0

                if Q_therm_req_W >= Boiler_min * MS_Var.Boiler_Q_max:  # Boiler can be activated?
                    # Q_therm_boiler = Q_therm_req

                    if Q_therm_req_W >= MS_Var.Boiler_Q_max:  # Boiler above maximum Load?
                        Q_therm_boiler_W = MS_Var.Boiler_Q_max
                    else:
                        Q_therm_boiler_W = Q_therm_req_W.copy()

                    Boiler_Cost_Data = cond_boiler_op_cost(Q_therm_boiler_W, MS_Var.Boiler_Q_max, tdhret_req_K, \
                                                           context.BoilerType, context.EL_TYPE, gv, prices)
                    C_boil_therm, C_boil_per_Wh, Q_primary_W, E_aux_Boiler_req_W = Boiler_Cost_Data

                    source_BaseBoiler = 1
                    cost_BaseBoiler = C_boil_therm
                    Q_BaseBoiler_gen_W = Q_therm_boiler_W
                    E_gas_BaseBoiler_W = Q_primary_W
                    E_BaseBoiler_req_W = E_aux_Boiler_req_W
                    Q_therm_req_W -= Q_therm_boiler_W


        if current_source == 'BoilerPeak' and Q_therm_req_W > 0:

            if (MS_Var.BoilerPeak_on) == 1:
                source_PeakBoiler = 0
                cost_PeakBoiler = 0.0
                Q_PeakBoiler_gen_W = 0.0
                E_gas_PeakBoiler_W = 0
                E_PeakBoiler_req_W = 0

                if Q_therm_req_W > 0:  # gv.Boiler_min*MS_Var.BoilerPeak_Q_max: # Boiler can be activated?

                    if Q_therm_req_W > MS_Var.BoilerPeak_Q_max:  # Boiler above maximum Load?
                        Q_therm_boilerP_W = MS_Var.BoilerPeak_Q_max
                        Q_therm_req_W -= Q_therm_boilerP_W
                    else:
                        Q_therm_boilerP_W = Q_therm_req_W.copy()
                        Q_therm_req_W = 0

                    Boiler_Cost_DataP = cond_boiler_op_cost(Q_therm_boilerP_W, MS_Var.BoilerPeak_Q_max, tdhret_req_K, \
                                                            context.BoilerPeakType, context.EL_TYPE, gv, prices)
                    C_boil_thermP, C_boil_per_WhP, Q_primaryP_W, E_aux_BoilerP_W = Boiler_Cost_DataP

                    source_PeakBoiler = 1
                    cost_PeakBoiler = C_boil_thermP
                    Q_PeakBoiler_gen_W = Q_therm_boilerP_W
                    E_gas_PeakBoiler_W = Q_primaryP_W
                    E_PeakBoiler_req_W = E_aux_BoilerP_W

        Q_excess_W = 0
        if np.floor(Q_therm_req_W) > 0:
            if current_source == act_first:
                current_source = act_second
            elif current_source == act_second:
                current_source = act_third
            elif current_source == act_third:
                current_source = act_fourth
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
    #
    # PP_activation_data["Cost_HPSew"][hour] = costHPSew
    # PP_activation_data["Cost_HPLake"][hour] = costHPSew
    # PP_activation_data["Cost_HPSew"], \
    # PP_activation_data["Cost_HPSew"], \
    # PP_activation_data["Cost_HPSew"], \

    cost_data_centralPlant_op = cost_HPSew, cost_HPLake, cost_GHP, cost_CHP, cost_Furnace, cost_BaseBoiler, cost_PeakBoiler
    # cost_data_centralPlant_op = pd.DataFrame({'Cost_HP_Sewage': costHPSew,
    #                                           'Cost_HP_Lake': costHPLake,
    #                                           'Cost_GHP': costGHP,
    #                                           'cost_CC': costCC,
    #                                           'cost_Furnace': costFurnace,
    #                                           'cost_Boiler': costBoiler,
    #                                           'cost_Backup_Boiler': costBackup}, index=[0])
    # cost_data_centralPlant_op.set_index('hour')

    source_info = source_HP_Sewage, source_HP_Lake, source_GHP, source_CHP, source_Furnace, source_BaseBoiler, source_PeakBoiler
    Q_source_data_W = Q_HPSew_gen_W, Q_HPLake_gen_W, Q_GHP_gen_W, Q_CHP_gen_W, Q_Furnace_gen_W, Q_BaseBoiler_gen_W, Q_PeakBoiler_gen_W, Q_uncovered_W
    E_PP_el_data_W = E_HPSew_req_W, E_HPLake_req_W, E_GHP_req_W, E_CHP_gen_W, E_Furnace_gen_W, E_BaseBoiler_req_W, E_PeakBoiler_req_W
    E_gas_data_W = E_gas_HPSew_W, E_gas_HPLake_W, E_gas_GHP_W, E_gas_CHP_W, E_gas_Furnace_W, E_gas_BaseBoiler_W, E_gas_PeakBoiler_W
    E_wood_data_W = E_wood_HPSew_W, E_wood_HPLake_W, E_wood_GHP_W, E_wood_CHP_W, E_wood_Furnace_W, E_wood_BaseBoiler_W, E_wood_PeakBoiler_W
    E_coldsource_data_W = E_coldsource_HPSew_W, E_coldsource_HPLake_W, E_coldsource_GHP_W, E_coldsource_CHP_W, \
                          E_coldsource_Furnace_W, E_coldsource_BaseBoiler_W, E_coldsource_PeakBoiler_W

    opex_output = {'Opex_var_HP_Sewage':cost_HPSew,
              'Opex_var_HP_Lake': cost_HPLake,
              'Opex_var_GHP': cost_GHP,
              'Opex_var_CHP': cost_CHP,
              'Opex_var_Furnace': cost_Furnace,
              'Opex_var_BaseBoiler': cost_BaseBoiler,
              'Opex_var_PeakBoiler': cost_PeakBoiler}

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

    Gas_output = {'E_gas_HPSew_W': E_gas_HPSew_W,
                  'E_gas_HPLake_W': E_gas_HPLake_W,
                  'E_gas_GHP_W': E_gas_GHP_W,
                  'E_gas_CHP_W': E_gas_CHP_W,
                  'E_gas_Furnace_W': E_gas_Furnace_W,
                  'E_gas_BaseBoiler_W': E_gas_BaseBoiler_W,
                  'E_gas_PeakBoiler_W': E_gas_PeakBoiler_W}

    Wood_output = {'E_wood_HPSew_W': E_wood_HPSew_W,
                   'E_wood_HPLake_W': E_wood_HPLake_W,
                   'E_wood_GHP_W': E_wood_GHP_W,
                   'E_wood_CHP_W': E_wood_CHP_W,
                   'E_wood_Furnace_W': E_wood_Furnace_W,
                   'E_wood_BaseBoiler_W': E_wood_BaseBoiler_W,
                   'E_wood_PeakBoiler_W': E_wood_PeakBoiler_W}

    coldsource_output = {'E_coldsource_HPSew_W': E_coldsource_HPSew_W,
                         'E_coldsource_HPLake_W': E_coldsource_HPLake_W,
                         'E_coldsource_GHP_W': E_coldsource_GHP_W,
                         'E_coldsource_CHP_W': E_coldsource_CHP_W,
                         'E_coldsource_Furnace_W': E_coldsource_Furnace_W,
                         'E_coldsource_BaseBoiler_W': E_coldsource_BaseBoiler_W,
                         'E_coldsource_PeakBoiler_W': E_coldsource_PeakBoiler_W}

    return opex_output, source_output, Q_output, E_output, Gas_output, Wood_output, coldsource_output, Q_excess_W

    # return cost_data_centralPlant_op, source_info, Q_source_data_W, E_coldsource_data_W, E_PP_el_data_W, E_gas_data_W, E_wood_data_W, Q_excess_W

