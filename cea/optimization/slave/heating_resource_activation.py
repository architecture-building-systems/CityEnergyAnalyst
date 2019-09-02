from __future__ import division

import numpy as np

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.boiler import cond_boiler_op_cost
from cea.technologies.cogeneration import calc_cop_CCGT
from cea.technologies.constants import FURNACE_MIN_LOAD, BOILER_MIN
from cea.technologies.furnace import furnace_op_cost
from cea.technologies.heatpumps import GHP_op_cost, HPSew_op_cost, HPLake_op_cost

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def heating_source_activator(Q_therm_req_W,
                             hour,
                             master_to_slave_vars,
                             Q_therm_GHP_W,
                             TretGHPArray_K,
                             TretLakeArray_K,
                             Q_therm_Lake_W,
                             Q_therm_Sew_W,
                             TretsewArray_K,
                             tdhsup_K,
                             tdhret_req_K,
                             prices,
                             lca):
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

    ## initializing unmet heating load
    Q_heat_unmet_W = Q_therm_req_W

    # ACTIVATE THE COGEN
    if master_to_slave_vars.CC_on == 1 and Q_heat_unmet_W > 0.0:

        CC_op_cost_data = calc_cop_CCGT(master_to_slave_vars.CCGT_SIZE_W,
                                        tdhsup_K,
                                        "NG",
                                        prices, lca.ELEC_PRICE[hour])  # create cost information
        Q_used_prim_CC_fn_W = CC_op_cost_data['q_input_fn_q_output_W']
        cost_per_Wh_CC_fn = CC_op_cost_data['fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        q_output_CC_min_W = CC_op_cost_data['q_output_min_W']
        Q_output_CC_max_W = CC_op_cost_data['q_output_max_W']
        eta_elec_interpol = CC_op_cost_data['eta_el_fn_q_input']

        if Q_heat_unmet_W >= q_output_CC_min_W:
            source_CHP = 1
            # operation Possible if above minimal load
            if Q_heat_unmet_W <= Q_output_CC_max_W:  # Normal operation Possible within partload regime
                Q_CHP_gen_W = Q_heat_unmet_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                Gas_used_CHP_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_CHP_gen_W = np.float(eta_elec_interpol(Gas_used_CHP_W)) * Gas_used_CHP_W
                opex_var_CHP_USD = cost_per_Wh_CC * Q_CHP_gen_W
            else:  # Only part of the demand can be delivered as 100% load achieved
                Q_CHP_gen_W = Q_output_CC_max_W
                cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CHP_gen_W)
                Gas_used_CHP_W = Q_used_prim_CC_fn_W(Q_CHP_gen_W)
                E_CHP_gen_W = np.float(eta_elec_interpol(Gas_used_CHP_W)) * Gas_used_CHP_W
                opex_var_CHP_USD = cost_per_Wh_CC * Q_CHP_gen_W
        else:
            source_CHP = 0
            Gas_used_CHP_W = 0.0
            E_CHP_gen_W = 0.0
            Q_CHP_gen_W = 0.0
            opex_var_CHP_USD = 0.0
        Q_heat_unmet_W = Q_heat_unmet_W - Q_CHP_gen_W
    else:
        source_CHP = 0
        Gas_used_CHP_W = 0.0
        E_CHP_gen_W = 0.0
        Q_CHP_gen_W = 0.0
        opex_var_CHP_USD = 0.0

    # WET FURNACE
    if master_to_slave_vars.Furnace_wet_on == 1 and Q_heat_unmet_W > 0.0:  # Activate Furnace if its there.
        source_Furnace_wet = 1
        # Operate only if its above minimal load
        if Q_heat_unmet_W > master_to_slave_vars.WBFurnace_Q_max_W:
            if Q_heat_unmet_W > master_to_slave_vars.WBFurnace_Q_max_W:
                Q_Furnace_wet_gen_W = master_to_slave_vars.WBFurnace_Q_max_W
                # scale down if above maximum load, Furnace operates at max. capacity
                Furnace_Cost_Data = furnace_op_cost(Q_Furnace_wet_gen_W,
                                                    master_to_slave_vars.WBFurnace_Q_max_W, tdhret_req_K,
                                                    "wet", lca, hour)

                opex_var_Furnace_wet_USD = Furnace_Cost_Data[0]
                Biomass_used_Furnace_wet_W = Furnace_Cost_Data[2]
                E_Furnace_wet_gen_W = Furnace_Cost_Data[4]

            else:  # Normal Operation Possible
                Q_Furnace_wet_gen_W = Q_heat_unmet_W
                Furnace_Cost_Data = furnace_op_cost(Q_Furnace_wet_gen_W,
                                                    master_to_slave_vars.WBFurnace_Q_max_W,
                                                    tdhret_req_K,
                                                    "wet", lca, hour)

                Biomass_used_Furnace_wet_W = Furnace_Cost_Data[2]
                opex_var_Furnace_wet_USD = Furnace_Cost_Data[0]
                E_Furnace_wet_gen_W = Furnace_Cost_Data[4]
        else:
            source_Furnace_wet = 0
            E_Furnace_wet_gen_W = 0.0
            Biomass_used_Furnace_wet_W = 0.0
            Q_Furnace_wet_gen_W = 0.0
            opex_var_Furnace_wet_USD = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_Furnace_wet_gen_W

    else:
        source_Furnace_wet = 0
        E_Furnace_wet_gen_W = 0.0
        Biomass_used_Furnace_wet_W = 0.0
        Q_Furnace_wet_gen_W = 0.0
        opex_var_Furnace_wet_USD = 0.0

    # DRY FURNACE
    if master_to_slave_vars.Furnace_dry_on == 1 and Q_heat_unmet_W > 0.0:  # Activate Furnace if its there.
        source_Furnace_dry = 1
        # Operate only if its above minimal load
        if Q_heat_unmet_W > master_to_slave_vars.DBFurnace_Q_max_W:
            if Q_heat_unmet_W > master_to_slave_vars.DBFurnace_Q_max_W:
                Q_Furnace_dry_gen_W = master_to_slave_vars.DBFurnace_Q_max_W
                # scale down if above maximum load, Furnace operates at max. capacity
                Furnace_Cost_Data = furnace_op_cost(Q_Furnace_dry_gen_W,
                                                    master_to_slave_vars.DBFurnace_Q_max_W, tdhret_req_K,
                                                    "dry", lca, hour)

                opex_var_Furnace_dry_USD = Furnace_Cost_Data[0]
                Biomass_used_Furnace_dry_W = Furnace_Cost_Data[2]
                E_Furnace_dry_gen_W = Furnace_Cost_Data[4]

            else:  # Normal Operation Possible
                Q_Furnace_dry_gen_W = Q_heat_unmet_W
                Furnace_Cost_Data = furnace_op_cost(Q_Furnace_dry_gen_W,
                                                    master_to_slave_vars.DBFurnace_Q_max_W, tdhret_req_K,
                                                    "dry", lca, hour)

                Biomass_used_Furnace_dry_W = Furnace_Cost_Data[2]
                opex_var_Furnace_dry_USD = Furnace_Cost_Data[0]
                Q_Furnace_dry_gen_W = Q_heat_unmet_W
                E_Furnace_dry_gen_W = Furnace_Cost_Data[4]
        else:
            source_Furnace_dry = 0
            E_Furnace_dry_gen_W = 0.0
            Biomass_used_Furnace_dry_W = 0.0
            Q_Furnace_dry_gen_W = 0.0
            opex_var_Furnace_dry_USD = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_Furnace_dry_gen_W
    else:
        source_Furnace_dry = 0
        E_Furnace_dry_gen_W = 0.0
        Biomass_used_Furnace_dry_W = 0.0
        Q_Furnace_dry_gen_W = 0.0
        opex_var_Furnace_dry_USD = 0.0

    if (master_to_slave_vars.HPSew_on) == 1 and Q_heat_unmet_W > 0.0 and not np.isclose(tdhsup_K,
                                                                                        tdhret_req_K):  # activate if its available

        source_HP_Sewage = 1
        if Q_heat_unmet_W > Q_therm_Sew_W:
            Q_HPSew_gen_W = Q_therm_Sew_W
            mdot_DH_to_Sew_kgpers = Q_HPSew_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
        else:
            Q_HPSew_gen_W = Q_heat_unmet_W
            mdot_DH_to_Sew_kgpers = Q_HPSew_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))

        opex_var_HPSew_USD, \
        E_HPSew_req_W, \
        Q_coldsource_HPSew_W, \
        Q_HPSew_gen_W = HPSew_op_cost(mdot_DH_to_Sew_kgpers,
                                      tdhsup_K,
                                      tdhret_req_K,
                                      TretsewArray_K,
                                      lca,
                                      Q_HPSew_gen_W,
                                      hour)

        Q_heat_unmet_W = Q_heat_unmet_W - Q_HPSew_gen_W

    else:
        source_HP_Sewage = 0
        opex_var_HPSew_USD = 0.0
        E_HPSew_req_W = 0.0
        Q_HPSew_gen_W = 0.0

    if (master_to_slave_vars.HPLake_on) == 1 and Q_heat_unmet_W > 0.0 and not np.isclose(tdhsup_K, tdhret_req_K):
        source_HP_Lake = 1
        if Q_heat_unmet_W > Q_therm_Lake_W:  # Scale down Load, 100% load achieved
            Q_HPLake_gen_W = Q_therm_Lake_W
        else:  # regular operation possible
            Q_HPLake_gen_W = Q_heat_unmet_W

        opex_var_HPLake_USD, E_HPLake_req_W, Q_coldsource_HPLake_W, Q_HPLake_gen_W = HPLake_op_cost(Q_HPLake_gen_W,
                                                                                                    tdhsup_K,
                                                                                                    tdhret_req_K,
                                                                                                    TretLakeArray_K,
                                                                                                    lca,
                                                                                                    hour)
        Q_heat_unmet_W = Q_heat_unmet_W - Q_HPLake_gen_W

    else:
        source_HP_Lake = 0
        opex_var_HPLake_USD = 0.0
        E_HPLake_req_W = 0.0
        Q_HPLake_gen_W = 0.0

    if (master_to_slave_vars.GHP_on) == 1 and Q_heat_unmet_W > 0.0 and not np.isclose(tdhsup_K, tdhret_req_K):
        source_GHP = 1
        if Q_heat_unmet_W > Q_therm_GHP_W:
            Q_GHP_gen_W = Q_therm_GHP_W
            mdot_DH_to_GHP_kgpers = Q_GHP_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))
        else:  # regular operation possible, demand is covered
            Q_GHP_gen_W = Q_heat_unmet_W
            mdot_DH_to_GHP_kgpers = Q_GHP_gen_W / (HEAT_CAPACITY_OF_WATER_JPERKGK * (tdhsup_K - tdhret_req_K))

        opex_var_GHP_USD, E_GHP_req_W, Q_coldsource_GHP_W, Q_GHP_gen_W = GHP_op_cost(mdot_DH_to_GHP_kgpers,
                                                                                     tdhsup_K,
                                                                                     tdhret_req_K,
                                                                                     TretGHPArray_K,
                                                                                     lca,
                                                                                     Q_GHP_gen_W,
                                                                                     hour)
        Q_heat_unmet_W = Q_heat_unmet_W - Q_GHP_gen_W

    else:
        source_GHP = 0
        opex_var_GHP_USD = 0.0
        E_GHP_req_W = 0.0
        Q_GHP_gen_W = 0.0

    if (master_to_slave_vars.Boiler_on) == 1 and Q_heat_unmet_W > 0:
        source_BaseBoiler = 1
        if Q_heat_unmet_W >= BOILER_MIN * master_to_slave_vars.Boiler_Q_max_W:  # Boiler can be activated?
            if Q_heat_unmet_W >= master_to_slave_vars.Boiler_Q_max_W:  # Boiler above maximum Load?
                Q_BaseBoiler_gen_W = master_to_slave_vars.Boiler_Q_max_W
            else:
                Q_BaseBoiler_gen_W = Q_heat_unmet_W

            opex_var_BaseBoiler_USD, C_boil_per_Wh, Gas_used_BaseBoiler_W, E_BaseBoiler_req_W = cond_boiler_op_cost(
                Q_BaseBoiler_gen_W, master_to_slave_vars.Boiler_Q_max_W, tdhret_req_K, "NG",
                prices, lca, hour)
        else:
            source_BaseBoiler = 0
            Q_BaseBoiler_gen_W = 0.0
            opex_var_BaseBoiler_USD = 0.0
            Gas_used_BaseBoiler_W = 0.0
            E_BaseBoiler_req_W = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_BaseBoiler_gen_W

    else:
        source_BaseBoiler = 0
        Q_BaseBoiler_gen_W = 0.0
        opex_var_BaseBoiler_USD = 0.0
        Gas_used_BaseBoiler_W = 0.0
        E_BaseBoiler_req_W = 0.0

    if master_to_slave_vars.BoilerPeak_on == 1 and Q_heat_unmet_W > 0:
        source_PeakBoiler = 1
        if Q_heat_unmet_W >= BOILER_MIN * master_to_slave_vars.BoilerPeak_Q_max_W:  # Boiler can be activated?
            if Q_heat_unmet_W > master_to_slave_vars.BoilerPeak_Q_max_W:  # Boiler above maximum Load?
                Q_PeakBoiler_gen_W = master_to_slave_vars.BoilerPeak_Q_max_W
            else:
                Q_PeakBoiler_gen_W = Q_heat_unmet_W

            opex_var_PeakBoiler_USD, C_boil_per_WhP, Gas_used_PeakBoiler_W, E_PeakBoiler_req_W = cond_boiler_op_cost(
                Q_PeakBoiler_gen_W, master_to_slave_vars.BoilerPeak_Q_max_W, tdhret_req_K,
                "NG", prices, lca, hour)
        else:
            source_PeakBoiler = 0
            opex_var_PeakBoiler_USD = 0.0
            Q_PeakBoiler_gen_W = 0.0
            Gas_used_PeakBoiler_W = 0
            E_PeakBoiler_req_W = 0.0

        Q_heat_unmet_W = Q_heat_unmet_W - Q_PeakBoiler_gen_W

    else:
        source_PeakBoiler = 0
        opex_var_PeakBoiler_USD = 0.0
        Q_PeakBoiler_gen_W = 0.0
        Gas_used_PeakBoiler_W = 0
        E_PeakBoiler_req_W = 0.0

    if Q_heat_unmet_W > 1.0E-3:
        Q_uncovered_W = Q_heat_unmet_W  # this will become the back-up boiler
    else:
        Q_uncovered_W = 0.0

    source_output = {'Source_HP_Sewage': source_HP_Sewage,
                     'Source_HP_Lake': source_HP_Lake,
                     'Source_GHP': source_GHP,
                     'Source_CHP': source_CHP,
                     'Source_Furnace_dry': source_Furnace_dry,
                     'Source_Furnace_wet': source_Furnace_wet,
                     'Source_BaseBoiler': source_BaseBoiler,
                     'Source_PeakBoiler': source_PeakBoiler}

    Q_output = {'Q_HPSew_gen_W': Q_HPSew_gen_W,
                'Q_HPLake_gen_W': Q_HPLake_gen_W,
                'Q_GHP_gen_W': Q_GHP_gen_W,
                'Q_CHP_gen_W': Q_CHP_gen_W,
                'Q_Furnace_dry_gen_W': Q_Furnace_dry_gen_W,
                'Q_Furnace_wet_gen_W': Q_Furnace_wet_gen_W,
                'Q_BaseBoiler_gen_W': Q_BaseBoiler_gen_W,
                'Q_PeakBoiler_gen_W': Q_PeakBoiler_gen_W,
                'Q_AddBoiler_gen_W': Q_uncovered_W}

    E_output = {'E_HPSew_req_W': E_HPSew_req_W,
                'E_HPLake_req_W': E_HPLake_req_W,
                'E_BaseBoiler_req_W': E_BaseBoiler_req_W,
                'E_PeakBoiler_req_W': E_PeakBoiler_req_W,
                'E_GHP_req_W': E_GHP_req_W,
                'E_CHP_gen_W': E_CHP_gen_W,
                'E_Furnace_dry_gen_W': E_Furnace_dry_gen_W,
                'E_Furnace_wet_gen_W': E_Furnace_wet_gen_W,
                }
    Gas_output = {'Gas_CHP_req_W': Gas_used_CHP_W,
                  'Gas_BaseBoiler_req_W': Gas_used_BaseBoiler_W,
                  'Gas_PeakBoiler_req_W': Gas_used_PeakBoiler_W}

    Biomass_output = {'Biomass_Furnace_dry_req_W': Biomass_used_Furnace_dry_W,
                      'Biomass_Furnace_wet_req_W': Biomass_used_Furnace_wet_W}

    return source_output, Q_output, E_output, Gas_output, Biomass_output
