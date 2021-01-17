"""
Substation Model
"""




import numpy as np
import pandas as pd
import scipy
from numba import jit

import cea.config
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.constants import HOURS_IN_YEAR
from cea.technologies.constants import DT_HEAT, DT_COOL, U_COOL, U_HEAT

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Jimeno A. Fonseca", "Tim Vollrath", "Thuy-An Nguyen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Substation model
def substation_main_heating(locator, total_demand, buildings_name_with_heating, heating_configuration=7, DHN_barcode=""):
    if DHN_barcode.count("1") > 0:  # check if there are buildings connected
        # FIRST GET THE MAXIMUM TEMPERATURE NEEDED BY THE NETWORK AT EVERY TIME STEP
        buildings_dict = {}
        heating_system_temperatures_dict = {}
        T_DHN_supply = np.zeros(HOURS_IN_YEAR)
        for name in buildings_name_with_heating:
            buildings_dict[name] = pd.read_csv(locator.get_demand_results_file(name))
            print(name)
            ## calculates the building side supply and return temperatures for each unit
            Ths_supply_C, Ths_re_C = calc_temp_hex_building_side_heating(buildings_dict[name],
                                                                         heating_configuration)

            # compare and get the minimum tempearture of the DH plant
            T_DH_supply = calc_temp_this_building_heating(Ths_supply_C)
            T_DHN_supply = np.vectorize(calc_DH_supply)(T_DH_supply, T_DHN_supply)

            # Create two vectors for doing the calculation
            heating_system_temperatures_dict[name] = {'Ths_supply_C': Ths_supply_C,
                                                      'Ths_return_C': Ths_re_C}
        # store the temperature of the grid for heating expected
        DHN_supply = {'T_DH_supply_C': T_DHN_supply}

        for name in buildings_name_with_heating:
            substation_demand = total_demand[(total_demand.Name == name)]
            substation_demand.to_csv(locator.get_optimization_substations_total_file(DHN_barcode, 'DH'), sep=',',
                                     index=False, float_format='%.3f')

            # calculate substation parameters per building
            substation_model_heating(name,
                                     buildings_dict[name],
                                     DHN_supply['T_DH_supply_C'],
                                     heating_system_temperatures_dict[name]['Ths_supply_C'],
                                     heating_system_temperatures_dict[name]['Ths_return_C'],
                                     heating_configuration, locator, DHN_barcode)
    else:
        # CALCULATE SUBSTATIONS DURING DECENTRALIZED OPTIMIZATION
        for name in buildings_name_with_heating:
            substation_demand = pd.read_csv(locator.get_demand_results_file(name))
            Ths_supply_C, Ths_return_C = calc_temp_hex_building_side_heating(substation_demand, heating_configuration)
            T_heating_system_supply = calc_temp_this_building_heating(Ths_supply_C)
            substation_model_heating(name,
                                     substation_demand,
                                     T_heating_system_supply,
                                     Ths_supply_C,
                                     Ths_return_C,
                                     heating_configuration, locator,
                                     DHN_barcode)

    return


def calc_temp_this_building_heating(Tww_Ths_supply_C):
    T_DH_supply = np.where(Tww_Ths_supply_C > 0, Tww_Ths_supply_C + DT_HEAT, Tww_Ths_supply_C)
    return T_DH_supply


def calc_temp_hex_building_side_heating(building_demand_df, heating_configuration):
    # space heating

    Ths_return, Ths_supply = calc_compound_Ths(building_demand_df, heating_configuration)
    # domestic hot water
    Tww_supply = building_demand_df.Tww_sys_sup_C.values

    # Supply space heating at the maximum temperature between hot water and space heating
    Ths_supply_C = np.vectorize(calc_DH_supply)(Ths_supply, Tww_supply)

    return Ths_supply_C, Ths_return


def substation_main_cooling(locator, total_demand, buildings_name_with_cooling, cooling_configuration=['aru','ahu','scu'], DCN_barcode=""):
    if DCN_barcode.count("1") > 0:  # CALCULATE SUBSTATIONS DURING CENTRALIZED OPTIMIZATION
        buildings_dict = {}
        cooling_system_temperatures_dict = {}
        T_DCN_supply_to_cs_ref = np.zeros(HOURS_IN_YEAR) + 1E6
        T_DCN_supply_to_cs_ref_data = np.zeros(HOURS_IN_YEAR) + 1E6
        for name in buildings_name_with_cooling:
            buildings_dict[name] = pd.read_csv(locator.get_demand_results_file(name))

            T_supply_to_cs_ref, T_supply_to_cs_ref_data, \
            Tcs_return_C, Tcs_supply_C = calc_temp_hex_building_side_cooling(buildings_dict[name],
                                                                             cooling_configuration)

            # calculates the building side supply and return temperatures for each unit
            T_DC_supply_to_cs_ref, T_DC_supply_to_cs_ref_data = calc_temp_this_building_cooling(T_supply_to_cs_ref,
                                                                                                T_supply_to_cs_ref_data)

            # update the DCN plant supply temperature
            T_DCN_supply_to_cs_ref = np.vectorize(calc_DC_supply)(T_DC_supply_to_cs_ref, T_DCN_supply_to_cs_ref)

            T_DCN_supply_to_cs_ref_data = np.vectorize(calc_DC_supply)(T_DC_supply_to_cs_ref_data,
                                                                       T_DCN_supply_to_cs_ref_data)

            cooling_system_temperatures_dict[name] = {'Tcs_supply_C': Tcs_supply_C, 'Tcs_return_C': Tcs_return_C}

            T_DCN_supply_to_cs_ref = np.where(T_DCN_supply_to_cs_ref != 1E6, T_DCN_supply_to_cs_ref, 0)
            T_DCN_supply_to_cs_ref_data = np.where(T_DCN_supply_to_cs_ref_data != 1E6, T_DCN_supply_to_cs_ref_data, 0)

        DCN_supply = {'T_DC_supply_to_cs_ref_C': T_DCN_supply_to_cs_ref,
                      'T_DC_supply_to_cs_ref_data_C': T_DCN_supply_to_cs_ref_data}

        for name in buildings_name_with_cooling:
            substation_demand = total_demand[(total_demand.Name == name)]
            substation_demand.to_csv(locator.get_optimization_substations_total_file(DCN_barcode, 'DC'), sep=',',
                                     index=False, float_format='%.3f')
            # calculate substation parameters per building
            substation_model_cooling(name, buildings_dict[name],
                                     DCN_supply['T_DC_supply_to_cs_ref_C'],
                                     DCN_supply['T_DC_supply_to_cs_ref_data_C'],
                                     cooling_system_temperatures_dict[name]['Tcs_supply_C'],
                                     cooling_system_temperatures_dict[name]['Tcs_return_C'],
                                     cooling_configuration,
                                     locator, DCN_barcode)
    else:
        # CALCULATE SUBSTATIONS DURING DECENTRALIZED OPTIMIZATION
        for name in buildings_name_with_cooling:
            substation_demand = pd.read_csv(locator.get_demand_results_file(name))
            T_supply_to_cs_ref, T_supply_to_cs_ref_data, \
            Tcs_return_C, Tcs_supply_C = calc_temp_hex_building_side_cooling(substation_demand, cooling_configuration)

            # calculates the building side supply and return temperatures for each unit
            T_DC_supply_to_cs_ref, T_DC_supply_to_cs_ref_data = calc_temp_this_building_cooling(T_supply_to_cs_ref,
                                                                                                T_supply_to_cs_ref_data)

            substation_model_cooling(name, substation_demand,
                                     T_DC_supply_to_cs_ref,
                                     T_DC_supply_to_cs_ref_data,
                                     Tcs_supply_C,
                                     Tcs_return_C,
                                     cooling_configuration,
                                     locator, DCN_barcode)

    return


def calc_temp_hex_building_side_cooling(building_demand_df,
                                        cooling_configuration):
    # data center cooling
    Tcdata_sys_supply = building_demand_df.Tcdata_sys_sup_C.values

    # refrigeration
    Tcref_supply = building_demand_df.Tcre_sys_sup_C.values

    # space cooling
    Tcs_return, Tcs_supply = calc_compound_Tcs(building_demand_df, cooling_configuration)

    # gigantic number 1E6 and small number -1E6
    Tcs_supply_C = np.where(Tcs_supply != 1E6, Tcs_supply, 0)
    Tcs_return_C = np.where(Tcs_return != -1E6, Tcs_return, 0)

    T_supply_to_cs_ref = np.vectorize(calc_DC_supply)(Tcs_supply, Tcref_supply)
    T_supply_to_cs_ref_data = np.vectorize(calc_DC_supply)(T_supply_to_cs_ref, Tcdata_sys_supply)

    return T_supply_to_cs_ref, T_supply_to_cs_ref_data, Tcs_return_C, Tcs_supply_C


def calc_temp_this_building_cooling(T_supply_to_cs_ref, T_supply_to_cs_ref_data):
    T_DC_supply_to_cs_ref = np.where(T_supply_to_cs_ref > 0.0,
                                     T_supply_to_cs_ref - DT_COOL, 0.0)  # when Tcs_supply equals 1E6, there is no flow
    T_DC_supply_to_cs_ref_data = np.where(T_supply_to_cs_ref_data > 0.0,
                                          T_supply_to_cs_ref_data - DT_COOL,
                                          0.0)
    return T_DC_supply_to_cs_ref, T_DC_supply_to_cs_ref_data


def calc_compound_Tcs(building_demand_df,
                      cooling_configuration):
    # HEX sizing for spacing cooling, calculate t_DC_return_cs, mcp_DC_cs
    Qcs_sys_kWh_dict = {'ahu': abs(building_demand_df.Qcs_sys_ahu_kWh.values),
                        'aru': abs(building_demand_df.Qcs_sys_aru_kWh.values),
                        'scu': abs(building_demand_df.Qcs_sys_scu_kWh.values)}
    mcpcs_sys_kWperC_dict = {'ahu': abs(building_demand_df.mcpcs_sys_ahu_kWperC.values),
                             'aru': abs(building_demand_df.mcpcs_sys_aru_kWperC.values),
                             'scu': abs(building_demand_df.mcpcs_sys_scu_kWperC.values)}
    # cooling supply temperature calculations based on heating configurations
    T_cs_supply_dict = {'ahu':building_demand_df.Tcs_sys_sup_ahu_C.values,
                        'aru':building_demand_df.Tcs_sys_sup_aru_C.values,
                        'scu':building_demand_df.Tcs_sys_sup_scu_C.values}
    T_cs_return_dict = {'ahu':building_demand_df.Tcs_sys_re_ahu_C.values,
                        'aru':building_demand_df.Tcs_sys_re_aru_C.values,
                        'scu':building_demand_df.Tcs_sys_re_scu_C.values}

    if len(cooling_configuration) == 1:
        Tcs_supply = T_cs_supply_dict[cooling_configuration[0]]
        Tcs_return = T_cs_return_dict[cooling_configuration[0]]
    elif len(cooling_configuration) == 2:  # AHU + ARU
        unit_1 = cooling_configuration[0]
        unit_2 = cooling_configuration[1]

        Tcs_supply = np.vectorize(calc_DC_supply)(T_cs_supply_dict[unit_1], T_cs_supply_dict[unit_2])
        Tcs_return = np.vectorize(calc_HEX_mix_2_flows)(Qcs_sys_kWh_dict[unit_1], Qcs_sys_kWh_dict[unit_2],
                                                        mcpcs_sys_kWperC_dict[unit_1], mcpcs_sys_kWperC_dict[unit_2],
                                                        T_cs_return_dict[unit_1], T_cs_return_dict[unit_2])
    elif len(cooling_configuration) == 3:  # AHU + ARU + SCU
        unit_1 = cooling_configuration[0]
        unit_2 = cooling_configuration[1]
        unit_3 = cooling_configuration[2]

        T_space_cooling_intermediate_1 = np.vectorize(calc_DC_supply)(T_cs_supply_dict[unit_1], T_cs_supply_dict[unit_2])
        Tcs_supply = np.vectorize(calc_DC_supply)(T_space_cooling_intermediate_1, T_cs_supply_dict[unit_3])
        Tcs_return = np.vectorize(calc_HEX_mix_3_flows)(Qcs_sys_kWh_dict[unit_1], Qcs_sys_kWh_dict[unit_2],
                                                        Qcs_sys_kWh_dict[unit_3], mcpcs_sys_kWperC_dict[unit_1],
                                                        mcpcs_sys_kWperC_dict[unit_2], mcpcs_sys_kWperC_dict[unit_3],
                                                        T_cs_return_dict[unit_1], T_cs_return_dict[unit_2],
                                                        T_cs_return_dict[unit_3])
    elif cooling_configuration == 0:
        Tcs_supply = np.zeros(HOURS_IN_YEAR) + 1E6
        Tcs_return = np.zeros(HOURS_IN_YEAR) - 1E6
    else:
        raise ValueError('wrong cooling configuration specified in substation_main!')
    return Tcs_return, Tcs_supply


# substation cooling
def substation_model_cooling(name, building, T_DC_supply_to_cs_ref_C, T_DC_supply_to_cs_ref_data_C, Tcs_supply_C,
                             Tcs_return_C, cs_configuration,
                             locator, DCN_barcode=""):
    # HEX sizing for spacing cooling, calculate t_DC_return_cs, mcp_DC_cs
    Qcs_sys_kWh_dict = {'ahu': abs(building.Qcs_sys_ahu_kWh.values),
                        'aru': abs(building.Qcs_sys_aru_kWh.values),
                        'scu': abs(building.Qcs_sys_scu_kWh.values)}
    mcpcs_sys_kWperC_dict = {'ahu': abs(building.mcpcs_sys_ahu_kWperC.values),
                             'aru': abs(building.mcpcs_sys_aru_kWperC.values),
                             'scu': abs(building.mcpcs_sys_scu_kWperC.values)}

    ## SIZE FOR THE SPACE COOLING HEAT EXCHANGER
    if len(cs_configuration) == 0:
        tci = 0
        t_DC_return_cs = 0
        mcp_DC_cs = 0
        A_hex_cs = 0
        Qcs_sys_W = np.zeros(HOURS_IN_YEAR)
    else:
        tci = T_DC_supply_to_cs_ref_data_C + 273  # fixme: change according to cs_ref or ce_ref_data
        Qcs_sys_kWh = 0.0
        for unit in cs_configuration:
            Qcs_sys_kWh += Qcs_sys_kWh_dict[unit]
        Qcs_sys_W = abs(Qcs_sys_kWh) * 1000  # in W
        # only include space cooling and refrigeration
        Qnom_W = max(Qcs_sys_W)  # in W
        if Qnom_W > 0:
            tho = Tcs_supply_C + 273  # in K
            thi = Tcs_return_C + 273  # in K
            mcpcs_sys_kWperC = 0.0
            for unit in cs_configuration:
                mcpcs_sys_kWperC += mcpcs_sys_kWperC_dict[unit]
            ch = (mcpcs_sys_kWperC) * 1000  # in W/K #fixme: recalculated with the Tsupply/return
            index = np.where(Qcs_sys_W == Qnom_W)[0][0]
            tci_0 = tci[index]  # in K
            thi_0 = thi[index]
            tho_0 = tho[index]
            ch_0 = ch[index]
            t_DC_return_cs, mcp_DC_cs, A_hex_cs = \
                calc_substation_cooling(Qcs_sys_W, thi, tho, tci, ch, ch_0, Qnom_W, thi_0, tci_0,
                                        tho_0)
        else:
            t_DC_return_cs = tci
            mcp_DC_cs = 0
            A_hex_cs = 0

    # HEX sizing for refrigeration, calculate t_DC_return_ref, mcp_DC_ref
    if len(cs_configuration) == 0:
        t_DC_return_ref = tci
        mcp_DC_ref = 0
        A_hex_ref = 0
        Qcre_sys_W = np.zeros(HOURS_IN_YEAR)

    else:
        Qcre_sys_W = abs(building.Qcre_sys_kWh.values) * 1000  # in W
        Qnom_W = max(Qcre_sys_W)
        if Qnom_W > 0:
            tho = building.Tcre_sys_sup_C + 273  # in K
            thi = building.Tcre_sys_re_C + 273  # in K
            ch = abs(building.mcpcre_sys_kWperC.values) * 1000  # in W/K
            index = np.where(Qcre_sys_W == Qnom_W)[0][0]
            tci_0 = tci[index]  # in K
            thi_0 = thi[index]
            tho_0 = tho[index]
            ch_0 = ch[index]
            t_DC_return_ref, mcp_DC_ref, A_hex_ref = \
                calc_substation_cooling(Qcre_sys_W, thi, tho, tci, ch, ch_0, Qnom_W, thi_0, tci_0, tho_0)
        else:
            t_DC_return_ref = tci
            mcp_DC_ref = 0
            A_hex_ref = 0

    # HEX sizing for datacenter, calculate t_DC_return_data, mcp_DC_data
    if len(cs_configuration) == 0:
        t_DC_return_data = tci
        mcp_DC_data = 0
        A_hex_data = 0
        Qcdata_sys_W = np.zeros(HOURS_IN_YEAR)

    else:
        Qcdata_sys_W = (abs(building.Qcdata_sys_kWh.values) * 1000)
        Qnom_W = max(Qcdata_sys_W)  # in W
        if Qnom_W > 0:
            tho = building.Tcdata_sys_sup_C + 273  # in K
            thi = building.Tcdata_sys_re_C + 273  # in K
            ch = abs(building.mcpcdata_sys_kWperC.values) * 1000  # in W/K
            index = np.where(Qcdata_sys_W == Qnom_W)[0][0]
            tci_0 = tci[index]  # in K
            thi_0 = thi[index]
            tho_0 = tho[index]
            ch_0 = ch[index]
            t_DC_return_data, mcp_DC_data, A_hex_data = \
                calc_substation_cooling(Qcdata_sys_W, thi, tho, tci, ch, ch_0, Qnom_W, thi_0, tci_0, tho_0)
        else:
            t_DC_return_data = tci
            mcp_DC_data = 0
            A_hex_data = 0

    # calculate mix temperature of return DC
    T_DC_return_cs_ref_C = np.vectorize(calc_HEX_mix_2_flows)(Qcs_sys_W, Qcre_sys_W, mcp_DC_cs, mcp_DC_ref,
                                                              t_DC_return_cs, t_DC_return_ref)
    T_DC_return_cs_ref_data_C = np.vectorize(calc_HEX_mix_3_flows)(Qcs_sys_W, Qcre_sys_W, Qcdata_sys_W,
                                                                   mcp_DC_cs, mcp_DC_ref, mcp_DC_data,
                                                                   t_DC_return_cs, t_DC_return_ref, t_DC_return_data,
                                                                   )
    mdot_space_cooling_data_center_and_refrigeration_result_flat = (mcp_DC_cs + mcp_DC_ref + mcp_DC_data) / \
                                                                   HEAT_CAPACITY_OF_WATER_JPERKGK  # convert W/K to kg/s
    mdot_space_cooling_and_refrigeration_result_flat = (mcp_DC_cs + mcp_DC_ref) / \
                                                       HEAT_CAPACITY_OF_WATER_JPERKGK  # convert from W/K to kg/s

    T_r1_space_cooling_and_refrigeration_result_flat = T_DC_return_cs_ref_C + 273.0  # convert to K
    T_r1_space_cooling_data_center_and_refrigeration_result_flat = T_DC_return_cs_ref_data_C + 273.0  # convert to K
    T_supply_DC_flat = T_DC_supply_to_cs_ref_C + 273.0  # convert to K
    T_supply_DC_space_cooling_data_center_and_refrigeration_result_flat = T_DC_supply_to_cs_ref_data_C + 273.0  # convert to K

    # save the results into a .csv file
    results = pd.DataFrame(
        {"mdot_space_cooling_and_refrigeration_result_kgpers": mdot_space_cooling_and_refrigeration_result_flat,
         "mdot_space_cooling_data_center_and_refrigeration_result_kgpers": mdot_space_cooling_data_center_and_refrigeration_result_flat,
         "T_return_DC_space_cooling_and_refrigeration_result_K": T_r1_space_cooling_and_refrigeration_result_flat,
         "T_supply_DC_space_cooling_and_refrigeration_result_K": T_supply_DC_flat,
         "T_return_DC_space_cooling_data_center_and_refrigeration_result_K": T_r1_space_cooling_data_center_and_refrigeration_result_flat,
         "T_supply_DC_space_cooling_data_center_and_refrigeration_result_K": T_supply_DC_space_cooling_data_center_and_refrigeration_result_flat,
         "A_hex_cs": A_hex_cs,
         "A_hex_cs_space_cooling_data_center_and_refrigeration": A_hex_cs + A_hex_data + A_hex_ref,
         "Q_space_cooling_and_refrigeration_W": Qcs_sys_W + Qcre_sys_W,
         "Q_space_cooling_data_center_and_refrigeration_W": Qcs_sys_W + Qcdata_sys_W + Qcre_sys_W,
         })

    results.to_csv(locator.get_optimization_substations_results_file(name, "DC", DCN_barcode), sep=',', index=False,
                   float_format='%.3f')
    return results


def calc_compound_Ths(building_demand_df,
                      heating_configuration):
    # HEX FOR SPACE HEATING, calculate t_DH_return_hs, mcp_DH_hs
    Ths_ahu_supply = building_demand_df.Ths_sys_sup_ahu_C.values  # FIXME: it's the best to have nan when there is no demand
    Ths_aru_supply = building_demand_df.Ths_sys_sup_aru_C.values
    Ths_shu_supply = building_demand_df.Ths_sys_sup_shu_C.values
    Ths_ahu_return = building_demand_df.Ths_sys_re_ahu_C.values
    Ths_aru_return = building_demand_df.Ths_sys_re_aru_C.values
    Ths_shu_return = building_demand_df.Ths_sys_re_shu_C.values

    Qhs_sys_ahu_kWh = building_demand_df.Qhs_sys_ahu_kWh.values
    Qhs_sys_aru_kWh = building_demand_df.Qhs_sys_aru_kWh.values
    Qhs_sys_shu_kWh = building_demand_df.Qhs_sys_shu_kWh.values
    Qhs_sys_kWh_dict = {1: Qhs_sys_ahu_kWh, 2: Qhs_sys_aru_kWh, 3: Qhs_sys_shu_kWh,
                        4: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh, 5: Qhs_sys_ahu_kWh + Qhs_sys_shu_kWh,
                        6: Qhs_sys_aru_kWh + Qhs_sys_shu_kWh, 7: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh + Qhs_sys_shu_kWh}
    mcphs_sys_ahu_kWperC = building_demand_df.mcphs_sys_ahu_kWperC.values
    mcphs_sys_aru_kWperC = building_demand_df.mcphs_sys_aru_kWperC.values
    mcphs_sys_shu_kWperC = building_demand_df.mcphs_sys_shu_kWperC.values
    mcphs_sys_kWperC_dict = {1: mcphs_sys_ahu_kWperC, 2: mcphs_sys_aru_kWperC, 3: mcphs_sys_shu_kWperC,
                             4: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC,
                             5: mcphs_sys_ahu_kWperC + mcphs_sys_shu_kWperC,
                             6: mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC,
                             7: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC}

    if heating_configuration == 1:  # AHU
        Ths_supply = Ths_ahu_supply
        Ths_return = Ths_ahu_return
    elif heating_configuration == 2:  # ARU
        Ths_supply = Ths_aru_supply
        Ths_return = Ths_aru_return
    elif heating_configuration == 3:  # SHU
        Ths_supply = Ths_shu_supply
        Ths_return = Ths_shu_return
    elif heating_configuration == 4:  # AHU + ARU
        Ths_supply = np.vectorize(calc_DH_supply)(Ths_ahu_supply, Ths_aru_supply)
        Ths_return = np.vectorize(calc_HEX_mix_2_flows)(Qhs_sys_kWh_dict[1], Qhs_sys_kWh_dict[2],
                                                        mcphs_sys_kWperC_dict[1], mcphs_sys_kWperC_dict[2],
                                                        Ths_ahu_return,
                                                        Ths_aru_return)
    elif heating_configuration == 5:  # AHU + SHU
        Ths_supply = np.vectorize(calc_DH_supply)(Ths_ahu_supply, Ths_shu_supply)
        Ths_return = np.vectorize(calc_HEX_mix_2_flows)(Qhs_sys_kWh_dict[1], Qhs_sys_kWh_dict[3],
                                                        mcphs_sys_kWperC_dict[1], mcphs_sys_kWperC_dict[3],
                                                        Ths_ahu_return,
                                                        Ths_shu_return)
    elif heating_configuration == 6:  # ARU + SHU
        Ths_supply = np.vectorize(calc_DH_supply)(Ths_aru_supply, Ths_shu_supply)
        Ths_return = np.vectorize(calc_HEX_mix_2_flows)(Qhs_sys_kWh_dict[2], Qhs_sys_kWh_dict[3],
                                                        mcphs_sys_kWperC_dict[2], mcphs_sys_kWperC_dict[3],
                                                        Ths_aru_return,
                                                        Ths_shu_return)
    elif heating_configuration == 7:  # AHU + ARU + SHU
        T_hs_intermediate_1 = np.vectorize(calc_DH_supply)(Ths_ahu_supply, Ths_aru_supply)
        Ths_supply = np.vectorize(calc_DH_supply)(T_hs_intermediate_1, Ths_shu_supply)

        Ths_return = np.vectorize(calc_HEX_mix_3_flows)(Qhs_sys_kWh_dict[1], Qhs_sys_kWh_dict[2], Qhs_sys_kWh_dict[3],
                                                        mcphs_sys_kWperC_dict[1], mcphs_sys_kWperC_dict[2],
                                                        mcphs_sys_kWperC_dict[3],
                                                        Ths_ahu_return, Ths_aru_return, Ths_shu_return
                                                        )


    elif heating_configuration == 0:  # when there is no heating requirement from the centralized plant
        Ths_supply = np.zeros(HOURS_IN_YEAR)
        Ths_return = np.zeros(HOURS_IN_YEAR)
    else:
        raise ValueError('wrong heating configuration specified in substation_main!')
    return Ths_return, Ths_supply


def substation_model_heating(name, building_demand_df, T_DH_supply_C, Ths_supply_C, Ths_return_C, hs_configuration,
                             locator,
                             DHN_barcode=""):
    '''

    :param locator: path to locator function
    :param building_demand_df: dataframe with consumption data per building
    :param T_heating_sup_C: vector with hourly temperature of the district heating network without losses
    :param T_DH_sup_C: vector with hourly temperature of the district heating netowork with losses
    :param T_DC_sup_C: vector with hourly temperature of the district coolig network with losses
    :param t_HS: maximum hourly temperature for all buildings connected due to space heating
    :param t_WW: maximum hourly temperature for all buildings connected due to domestic hot water
    :param DHN_barcode: this iis default to "" which means that it is created for decentralized buildings " 0101011001"
    is acommont type used during optimization
    :return:
        - Dataframe stored for every building with the mass flow rates and temperatures district heating and cooling
        - where fName_result: ID of the building accounting for the individual at which it belongs to.

    '''

    # HEX FOR SPACE HEATING, calculate t_DH_return_hs, mcp_DH_hs
    Qhs_sys_ahu_kWh = building_demand_df.Qhs_sys_ahu_kWh.values
    Qhs_sys_aru_kWh = building_demand_df.Qhs_sys_aru_kWh.values
    Qhs_sys_shu_kWh = building_demand_df.Qhs_sys_shu_kWh.values
    Qhs_sys_kWh_dict = {1: Qhs_sys_ahu_kWh, 2: Qhs_sys_aru_kWh, 3: Qhs_sys_shu_kWh,
                        4: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh, 5: Qhs_sys_ahu_kWh + Qhs_sys_shu_kWh,
                        6: Qhs_sys_aru_kWh + Qhs_sys_shu_kWh, 7: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh + Qhs_sys_shu_kWh}
    mcphs_sys_ahu_kWperC = building_demand_df.mcphs_sys_ahu_kWperC.values
    mcphs_sys_aru_kWperC = building_demand_df.mcphs_sys_aru_kWperC.values
    mcphs_sys_shu_kWperC = building_demand_df.mcphs_sys_shu_kWperC.values
    mcphs_sys_kWperC_dict = {1: mcphs_sys_ahu_kWperC, 2: mcphs_sys_aru_kWperC, 3: mcphs_sys_shu_kWperC,
                             4: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC,
                             5: mcphs_sys_ahu_kWperC + mcphs_sys_shu_kWperC,
                             6: mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC,
                             7: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC}

    # fixme: this is the wrong aggregation! the mcp should be recalculated according to the updated Tsup/re, and this does not aggregate the domestic hot water
    # HEX for space heating
    if hs_configuration == 0:
        t_DH_return_hs = np.zeros(HOURS_IN_YEAR)
        mcp_DH_hs = np.zeros(HOURS_IN_YEAR)
        A_hex_hs = 0
        Qhs_sys_W = np.zeros(HOURS_IN_YEAR)
    else:
        thi = T_DH_supply_C + 273  # In k
        Qhs_sys_W = Qhs_sys_kWh_dict[hs_configuration] * 1000  # in W
        Qnom_W = max(Qhs_sys_W)
        index = np.where(Qhs_sys_W == Qnom_W)[0][0]# in W
        if Qnom_W > 0:
            tco = Ths_supply_C + 273  # in K
            tci = Ths_return_C + 273  # in K
            cc = Qhs_sys_W / (tco - tci)
            thi_0 = thi[index]
            tci_0 = tci[index]
            tco_0 = tco[index]
            cc_0 = cc[index]
            t_DH_return_hs, mcp_DH_hs, A_hex_hs = \
                calc_substation_heating(Qhs_sys_W, thi, tco, tci, cc, cc_0, Qnom_W, thi_0, tci_0, tco_0)
        else:
            t_DH_return_hs = np.zeros(HOURS_IN_YEAR)
            mcp_DH_hs = np.zeros(HOURS_IN_YEAR)
            A_hex_hs = 0
            tci = np.zeros(HOURS_IN_YEAR) + 273  # in K

    # HEX FOR HOT WATER PRODUCTION, calculate t_DH_return_ww, mcp_DH_ww
    Qww_sys_W = building_demand_df.Qww_sys_kWh.values * 1000  # in W
    Qnom_W = max(Qww_sys_W)  # in W
    if Qnom_W > 0:
        thi = T_DH_supply_C + 273  # In k
        tco = building_demand_df.Tww_sys_sup_C + 273  # in K
        tci = building_demand_df.Tww_sys_re_C + 273  # in K
        cc = building_demand_df.mcpww_sys_kWperC.values * 1000  # in W/K
        index = np.where(Qww_sys_W == Qnom_W)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_ww, mcp_DH_ww, A_hex_ww = \
            calc_substation_heating(Qww_sys_W, thi, tco, tci, cc, cc_0, Qnom_W, thi_0, tci_0, tco_0)
    else:
        t_DH_return_ww = np.zeros(HOURS_IN_YEAR)
        A_hex_ww = 0
        mcp_DH_ww = np.zeros(HOURS_IN_YEAR)
        tci = np.zeros(HOURS_IN_YEAR) + 273  # in K

    # CALCULATE MIX IN HEAT EXCHANGERS AND RETURN TEMPERATURE
    T_DH_return_C = np.vectorize(calc_HEX_mix_2_flows)(Qhs_sys_W, Qww_sys_W, mcp_DH_hs, mcp_DH_ww, t_DH_return_hs,
                                                       t_DH_return_ww
                                                       )
    mcp_DH = (mcp_DH_ww + mcp_DH_hs)

    # converting units and quantities:
    T_return_DH_result_flat = T_DH_return_C + 273.0  # convert to K
    T_supply_DH_result_flat = T_DH_supply_C + 273.0  # convert to K
    mdot_DH_result_flat = mcp_DH / HEAT_CAPACITY_OF_WATER_JPERKGK  # convert from W/K to kg/s

    # save the results into a .csv file
    substation_activation = pd.DataFrame({"mdot_DH_result_kgpers": mdot_DH_result_flat,
                                          "T_return_DH_result_K": T_return_DH_result_flat,
                                          "T_supply_DH_result_K": T_supply_DH_result_flat,
                                          "A_hex_heating_design_m2": A_hex_hs,
                                          "A_hex_dhw_design_m2": A_hex_ww,
                                          # fixme: temporary output
                                          "Q_heating_W": Qhs_sys_W,
                                          "Q_dhw_W": Qww_sys_W})

    substation_activation.to_csv(locator.get_optimization_substations_results_file(name, "DH", DHN_barcode), sep=',',
                                 index=False,
                                 float_format='%.3f')

    return


def calc_substation_cooling(Q, thi, tho, tci, ch, ch_0, Qnom, thi_0, tci_0, tho_0):
    '''
    this function calculates the state of the heat exchanger at the substation of every customer with cooling needs

    :param Q: cooling load
    :param thi: in temperature of primary side
    :param tho: out temperature of primary side
    :param tci: in temperature of secondary side
    :param ch: capacity mass flow rate primary side in W
    :param ch_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of primary side
    :param tci_0: nominal in temperature of secondary side
    :param tho_0: nominal out temperature of primary side

    :return:
        - tco = out temperature of secondary side (district cooling network)
        - cc = capacity mass flow rate secondary side
        - Area_HEX_cooling = area of heat exchanger.

    '''

    # nominal conditions network side
    cc_0 = ch_0 * (thi_0 - tho_0) / ((thi_0 - tci_0) * 0.9)
    tco_0 = Qnom / cc_0 + tci_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0)
    # Area heat exchange and UA_heating
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom, dTm_0, U_COOL)
    tco, cc = np.vectorize(calc_HEX_cooling)(Q, UA_cooling, thi, tho, tci, ch)

    return tco, cc, Area_HEX_cooling


# substation heating

def calc_substation_heating(Q, thi, tco, tci, cc, cc_0, Qnom, thi_0, tci_0, tco_0):
    '''
    This function calculates the mass flow rate, temperature of return (secondary side)
    and heat exchanger area of every substation.

    :param Q: heating load
    :param thi: in temperature of secondary side
    :param tco: out temperature of primary side
    :param tci: in temperature of primary side
    :param cc: capacity mass flow rate primary side
    :param cc_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of secondary side
    :param tci_0: nominal in temperature of primary side
    :param tco_0: nominal out temperature of primary side

    :return:
        - tho = out temperature of secondary side (district cooling network)
        - ch = capacity mass flow rate secondary side
        - Area_HEX_heating = area of heat exchanger.

    '''
    if thi_0 <= tco_0:
        raise Exception("The temperature of the hot stream is lower than the cold stream, Please check inputs!")

    # nominal condition of the secondary side
    ch_0 = cc_0 * (tco_0 - tci_0) / ((thi_0 - tci_0) * 0.9) # estimate ch_0 assuming effectiveness = 0.9
    tho_0 = thi_0 - Qnom / ch_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0)
    # Area heat exchange and UA_heating
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom, dTm_0, U_HEAT)
    tho, ch = np.vectorize(calc_HEX_heating)(Q, UA_heating, thi, tco, tci, cc)
    return tho, ch, Area_HEX_heating


@jit(nopython=True)
def calc_plate_HEX(NTU, cr):
    """
    This function calculates the efficiency of exchange for a plate heat exchanger according to the NTU method of
    AShRAE 90.1

    :param NTU: number of transfer units
    :param cr: ratio between min and max capacity mass flow rates

    :return:
        - eff: efficiency of heat exchange

    """
    efficiency = 1 - np.exp((1 / cr) * (NTU ** 0.22) * (np.exp(-cr * (NTU) ** 0.78) - 1))
    return efficiency


@jit('boolean(float64, float64)', nopython=True)
def efficiencies_not_converged(previous_efficiency, current_efficiency):
    tolerance = 0.00000001
    return abs((previous_efficiency - current_efficiency) / previous_efficiency) > tolerance


@jit('boolean(float64, float64)', nopython=True)
def isclose(a, b):
    """adapted from here: https://stackoverflow.com/a/33024979/2260"""
    rel_tol = 1e-09
    abs_tol = 0.0
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


# Heat exchanger model
@jit('UniTuple(f8, 2)(f8, f8, f8, f8, f8, f8)', nopython=True)
def calc_HEX_cooling(Q_cooling_W, UA, thi_K, tho_K, tci_K, ch_kWperK):
    """
    This function calculates the mass flow rate, temperature of return (secondary side)
    and heat exchanger area for a plate heat exchanger.
    Method : Number of Transfer Units (NTU)

    :param Q_cooling_W: cooling load
    :param UA: coefficient representing the area of heat exchanger times the coefficient of transmittance of the
        heat exchanger
    :param thi_K: inlet temperature of primary side
    :param tho_K: outlet temperature of primary side
    :param tci_K: inlet temperature of secondary side
    :param ch_kWperK: capacity mass flow rate primary side
    :return:
        - ``tco``, out temperature of secondary side (district cooling network)
        - ``cc``, capacity mass flow rate secondary side

    """
    if ch_kWperK > 0 and not isclose(thi_K, tho_K):
        previous_efficiency = 0.1
        current_efficiency = -1.0  # dummy value for first iteration - never used in any calculations

        cmin_kWperK = ch_kWperK * (thi_K - tho_K) / ((thi_K - tci_K) * previous_efficiency)
        tco_K = 273.0  # actual value calculated in iteration
        while efficiencies_not_converged(previous_efficiency, current_efficiency):
            assert not (cmin_kWperK < 0.0), "substation.calc_HEX_cooling: cmin is negative!!"

            cc_kWperK = cmin_kWperK
            if cmin_kWperK < ch_kWperK:
                cmax_kWperK = ch_kWperK
            else:
                cmax_kWperK = cc_kWperK
                cmin_kWperK = ch_kWperK

            cr = cmin_kWperK / cmax_kWperK
            NTU = UA / cmin_kWperK

            previous_efficiency = current_efficiency
            current_efficiency = calc_plate_HEX(NTU, cr)

            cmin_kWperK = ch_kWperK * (thi_K - tho_K) / ((thi_K - tci_K) * current_efficiency)
            tco_K = tci_K + current_efficiency * cmin_kWperK * (thi_K - tci_K) / cc_kWperK

            # previous_efficiency = current_efficiency
            # current_efficiency = calculate_next_efficiency

        cc_kWperK = Q_cooling_W / abs(tci_K - tco_K)
        tco_C = tco_K - 273.0
    else:
        tco_C = 0.0
        cc_kWperK = 0.0
    return np.float(tco_C), np.float(cc_kWperK)


@jit(nopython=True)
def calc_shell_HEX(NTU, cr):
    """
    This function calculates the efficiency of exchange for a tube-shell heat exchanger according to the NTU method of
    AShRAE 90.1

    :param NTU: number of transfer units
    :param cr: ratio between min and max capacity mass flow rates

    :return:
        - eff: efficiency of heat exchange

    """
    efficiency = 2 * ((1 + cr + (1 + cr ** 2) ** (1 / 2)) * (
            (1 + np.exp(-(NTU) * (1 + cr ** 2))) / (1 - np.exp(-(NTU) * (1 + cr ** 2))))) ** -1
    return efficiency


def calc_HEX_mix_2_flows(Q1, Q2, m1, m2, t1, t2):
    """
    This function computes the average  temperature between two vectors of heating demand.
    In this case, domestic hotwater and space heating.

    :param Q1: load heating
    :param Q2: load domestic hot water
    :param t1: out temperature of heat exchanger for space heating
    :param m1: mas flow rate secondary side of heat exchanger for space heating
    :param t2: out temperature of heat exchanger for domestic hot water
    :param m2: mas flow rate secondary side of heat exchanger for domestic hot water

    :return:
        - tavg: average out temperature.

    """
    tavg = 0
    if (m1 + m2) > 0:
        if Q1 > 0 or Q2 > 0:
            tavg = (t1 * m1 + t2 * m2) / (m1 + m2)
    return np.float(tavg)


def calc_HEX_mix_3_flows(Q1, Q2, Q3, m1, m2, m3, t1, t2, t3):
    tavg = 0
    if (m1 + m2 + m3) > 0:
        if Q1 > 0 or Q2 > 0 or Q3 > 0:
            tavg = (t1 * m1 + t2 * m2 + t3 * m3) / (m1 + m2 + m3)
    return np.float(tavg)


@jit('UniTuple(f8, 2)(f8, f8, f8, f8, f8, f8)', nopython=True)
def calc_HEX_heating(Q_heating_W, UA, thi_K, tco_K, tci_K, cc_kWperK):
    """
    This function calculates the mass flow rate, temperature of return (secondary side)
    and heat exchanger area for a shell-tube pleat exchanger in the heating case.
    Method of Number of Transfer Units (NTU)

    :param Q_heating_W: load

    :param UA: coefficient representing the area of heat exchanger times the coefficient of transmittance of the
        heat exchanger

    :param thi_K: in temperature of secondary side

    :param tco_K: out temperature of primary side

    :param tci_K: in temperature of primary side

    :param cc_kWperK: capacity mass flow rate primary side

    :return:
        - ``tho``, out temperature of secondary side (district cooling network)
        - ``ch``, capacity mass flow rate secondary side

    """
    ch_kWperK = 0
    if Q_heating_W > 0.0:
        dT_primary = tco_K - tci_K if not isclose(tco_K,
                                                  tci_K) else 0.0001  # to avoid errors with temperature changes < 0.001
        previous_efficiency = 0.1
        current_efficiency = 0.8  # dummy value for first iteration - never used in any calculations
        cmin_kWperK = cc_kWperK * (dT_primary) / ((thi_K - tci_K) * previous_efficiency)

        while efficiencies_not_converged(previous_efficiency, current_efficiency):
            if cmin_kWperK < cc_kWperK:
                ch_kWperK = cmin_kWperK
                cmax_kWperK = cc_kWperK
            else:
                ch_kWperK = cmin_kWperK
                cmax_kWperK = cmin_kWperK
                cmin_kWperK = cc_kWperK
            cr = cmin_kWperK / cmax_kWperK
            NTU = UA / cmin_kWperK
            previous_efficiency = current_efficiency
            current_efficiency = calc_shell_HEX(NTU, cr)
            cmin_kWperK = cc_kWperK * (dT_primary) / ((thi_K - tci_K) * current_efficiency)
            tho_K = thi_K - current_efficiency * cmin_kWperK * (thi_K - tci_K) / ch_kWperK
        tho_C = tho_K - 273
    else:
        tho_C = 0
        ch_kWperK = 0
    return np.float(tho_C), np.float(ch_kWperK)


def calc_dTm_HEX(thi, tho, tci, tco):
    '''
    This function estimates the logarithmic temperature difference between two streams

    :param thi: in temperature hot stream
    :param tho: out temperature hot stream
    :param tci: in temperature cold stream
    :param tco: out temperature cold stream
    :return:
        - dtm = logarithmic temperature difference

    '''
    dT1 = thi - tco
    dT2 = tho - tci if not isclose(tho, tci) else 0.0001  # to avoid errors with temperature changes < 0.001

    try:
        dTm = (dT1 - dT2) / np.log(dT1 / dT2)
    except ZeroDivisionError:
        raise Exception(thi, tco, tho, tci,
                        "Check the emission_system database, there might be a problem with the selection of nominal temperatures")

    return abs(dTm.real)


def calc_area_HEX(Qnom, dTm_0, U):
    """

    Thi function calculates the area of a het exchanger at nominal conditions.

    :param Qnom: nominal load
    :param dTm_0: nominal logarithmic temperature difference
    :param U: coeffiicent of transmissivity
    :return:
        - ``area``, area of heat exchanger
        - ``UA``, coefficient representing the area of heat exchanger times the coefficient of transmittance of the
            heat exchanger

    """
    area = Qnom / (dTm_0 * U)  # Qnom in W
    UA = U * area
    return area, UA


def calc_DC_supply(t_0, t_1):  # fixme: keep the correct one
    """
    This function calculates the temperature of the district cooling network according to the minimum observed
    (different to zero) in all buildings connected to the grid.

    :param t_0: last minimum temperature
    :param t_1:  current minimum temperature to evaluate
    :return: ``tmin``, new minimum temperature
    """
    # TODO: verify if this assumption makes sense
    if isclose(t_0, 0.0):
        if isclose(t_1, 0.0):
            return 0.0
        else:
            return t_1
    elif isclose(t_1, 0.0):
        return t_0
    else:
        return min(t_0, t_1)


def calc_DH_supply(t_0, t_1):
    """
    This function calculates the temperature of the district heating network according to the maximum observed
    in all buildings connected to the grid.

    :param t_0: last maximum temperature
    :param t_1: current maximum temperature
    :return: ``tmax``, new maximum temperature
    """
    tmax = max(t_0, t_1)
    return tmax


def calc_DC_return(t_0, t_1):
    """
    This function calculates the return temperature of the district cooling network according to the maximum observed
    (different to zero) in all buildings connected to the grid.

    :param t_0: last maximum temperature
    :param t_1:  current maximum temperature to evaluate
    :return: ``tmin``, new maximum temperature
    """
    # if t_0 == 0:
    #     t_0 = -1E6
    # if t_1 > 0:
    #     tmax = max(t_0, t_1)
    # else:
    #     tmax = t_0
    if t_0 == 0:
        t_0 = -1E6
    if t_1 == 0:
        t_1 = -1E6
    tmax = max(t_0, t_1)
    return tmax


def calc_DH_return(t_0, t_1):
    """
    This function calculates the return temperature of the district heating network according to the minimum observed
    in all buildings connected to the grid.

    :param t_0: last minimum temperature
    :param t_1: current minimum temperature
    :return: ``tmax``, new minimum temperature
    """
    tmin = min(t_0, t_1)
    return tmin


# ============================
# Test
# ============================

def main(config):
    """
    do some testing... (view this as a scratch-pad...
    """
    calc_dTm_HEX(338.0, 281.728, 282.07, 333.0)

if __name__ == '__main__':
    main(cea.config.Configuration())
