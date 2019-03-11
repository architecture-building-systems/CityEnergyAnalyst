"""
Substation Model
"""
from __future__ import division

import time
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
import numpy as np
import pandas as pd
import scipy
from numba import jit
import cea.config
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

def substation_main(locator, total_demand, building_names, heating_configuration, cooling_configuration, Flag):
    """
    This function calculates the temperatures and mass flow rates of the district heating network
    at every costumer. Based on this, the script calculates the hourly temperature of the network at the plant.
    This temperature needs to be equal to that of the customer with the highest temperature requirement plus thermal
    losses in the network.

    :param locator: path to locator function
    :param total_demand: dataframe with total demand and names of all building in the area
    :param building_names:  dataframe with names of all buildings in the area
    :param Flag: boolean, True if the function is called by the master optimizaiton. False if the fucntion is
        called during preprocessing
    :param heating_configuration: integer between 1-7, where 1: AHU, 2: ARU, 3: SHU, 4: AHU+ARU, 5: AHU+SHU, 6: ARU+SHU, 7: AHU + ARU + SHU
    :param cooling_configuration: integer between 1-7, where 1: AHU, 2: ARU, 3: SCU, 4: AHU+ARU, 5: AHU+SCU, 6: ARU+SCU, 7: AHU + ARU + SCU

    """

    t0 = time.clock()
    # generate empty vectors
    # Ths_ahu_supply = np.zeros(8760)
    # Ths_aru_supply = np.zeros(8760)
    # Ths_shu_supply = np.zeros(8760)
    # Ths_ahu_return = np.zeros(8760)
    # Ths_aru_return = np.zeros(8760)
    # Ths_shu_return = np.zeros(8760)
    # Tww_supply = np.zeros(8760)
    # Tww_return = np.zeros(8760)
    T_cooling_supply_initial = np.zeros(8760) + 1E6
    T_cooling_return_initial = np.zeros(8760) - 1E6
    # Tcdata_sys_supply = np.zeros(8760) + 1E6
    # Tcref_supply = np.zeros(8760) + 1E6
    # Tcs_ahu_supply = np.zeros(8760) + 1E6
    # Tcs_aru_supply = np.zeros(8760) + 1E6
    # Tcs_scu_supply = np.zeros(8760) + 1E6
    # Tcdata_sys_return = np.zeros(8760) - 1E6
    # Tcref_return = np.zeros(8760) - 1E6
    # Tcs_ahu_return = np.zeros(8760) - 1E6
    # Tcs_aru_return = np.zeros(8760) - 1E6
    # Tcs_scu_return = np.zeros(8760) - 1E6

    # Calculate the plant supply temperautres according to all building demands
    # hence, the lowest temperature for DC, and the highest temperature for DH
    buildings_dict = {}
    cooling_system_temperatures_dict = {}
    heating_system_temperatures_dict = {}
    T_DHN_supply = np.zeros(8760)
    T_DCN_supply_to_cs_ref = np.zeros(8760) + 1E6
    T_DCN_supply_to_cs_ref_data = np.zeros(8760) + 1E6
    for name in building_names:
        buildings_dict[name] = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                           usecols=['Name', 'Ths_sys_sup_ahu_C', 'Ths_sys_sup_aru_C', 'Ths_sys_sup_shu_C',
                                                    'Ths_sys_re_ahu_C', 'Ths_sys_re_aru_C', 'Ths_sys_re_shu_C',
                                                    'Tcs_sys_sup_ahu_C', 'Tcs_sys_sup_aru_C', 'Tcs_sys_sup_scu_C',
                                                    'Tcs_sys_re_ahu_C', 'Tcs_sys_re_aru_C', 'Tcs_sys_re_scu_C',
                                                    'Tww_sys_sup_C', 'Tww_sys_re_C',
                                                    'Tcdata_sys_sup_C', 'Tcdata_sys_re_C', 'Tcre_sys_sup_C', 'Tcre_sys_re_C',
                                                    'Qhs_sys_ahu_kWh', 'Qhs_sys_aru_kWh', 'Qhs_sys_shu_kWh',
                                                    'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh', 'Qcs_sys_scu_kWh',
                                                    'Qww_sys_kWh', 'Qcre_sys_kWh', 'Qcdata_sys_kWh', 'mcpcdata_sys_kWperC',
                                                    'mcphs_sys_ahu_kWperC', 'mcphs_sys_aru_kWperC', 'mcphs_sys_shu_kWperC',
                                                    'mcpww_sys_kWperC', 'mcpcs_sys_ahu_kWperC', 'mcpcs_sys_aru_kWperC',
                                                    'mcpcs_sys_scu_kWperC', 'E_sys_kWh'])

        ## calculates the building side supply and return temperatures for each units
        # space heating
        Ths_ahu_supply = buildings_dict[
            name].Ths_sys_sup_ahu_C.values  # FIXME: it's the best to have nan when there is no demand
        Ths_aru_supply = buildings_dict[name].Ths_sys_sup_aru_C.values
        Ths_shu_supply = buildings_dict[name].Ths_sys_sup_shu_C.values
        Ths_ahu_return = buildings_dict[name].Ths_sys_re_ahu_C.values
        Ths_aru_return = buildings_dict[name].Ths_sys_re_aru_C.values
        Ths_shu_return = buildings_dict[name].Ths_sys_re_shu_C.values

        # domestic hot water
        Tww_supply = buildings_dict[name].Tww_sys_sup_C.values
        Tww_return = buildings_dict[name].Tww_sys_re_C.values

        # data center cooling
        Tcdata_sys_supply = buildings_dict[name].Tcdata_sys_sup_C.values
        Tcdata_sys_return = buildings_dict[name].Tcdata_sys_re_C.values

        # refrigeration
        Tcref_supply = buildings_dict[name].Tcre_sys_sup_C.values
        Tcref_return = buildings_dict[name].Tcre_sys_re_C.values

        # space cooling
        Tcs_ahu_supply = buildings_dict[name].Tcs_sys_sup_ahu_C.values
        Tcs_aru_supply = buildings_dict[name].Tcs_sys_sup_aru_C.values
        Tcs_scu_supply = buildings_dict[name].Tcs_sys_sup_scu_C.values
        Tcs_ahu_return = buildings_dict[name].Tcs_sys_re_ahu_C.values
        Tcs_aru_return = buildings_dict[name].Tcs_sys_re_aru_C.values
        Tcs_scu_return = buildings_dict[name].Tcs_sys_re_scu_C.values

        # heating supply temperature calculations based on heating configurations
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
            Ths_return = np.vectorize(calc_DH_return)(Ths_ahu_return, Ths_aru_return)
        elif heating_configuration == 5:  # AHU + SHU
            Ths_supply = np.vectorize(calc_DH_supply)(Ths_ahu_supply, Ths_shu_supply)
            Ths_return = np.vectorize(calc_DH_return)(Ths_ahu_return, Ths_shu_return)
        elif heating_configuration == 6:  # ARU + SHU
            Ths_supply = np.vectorize(calc_DH_supply)(Ths_aru_supply, Ths_shu_supply)
            Ths_return = np.vectorize(calc_DH_return)(Ths_aru_return, Ths_shu_return)
        elif heating_configuration == 7:  # AHU + ARU + SHU
            T_hs_intermediate_1 = np.vectorize(calc_DH_supply)(Ths_ahu_supply, Ths_aru_supply)
            Ths_supply = np.vectorize(calc_DH_supply)(T_hs_intermediate_1, Ths_shu_supply)
            T_hs_intermediate_2 = np.vectorize(calc_DH_return)(Ths_ahu_return, Ths_aru_return)
            Ths_return = np.vectorize(calc_DH_return)(T_hs_intermediate_2, Ths_shu_return)
        elif heating_configuration == 0: # when there is no heating requirement from the centralized plant
            Ths_supply = np.zeros(8760)
            Ths_return = np.zeros(8760)
        else:
            raise ValueError('wrong heating configuration specified in substation_main!')

        T_building_heatiing_supply_C = np.vectorize(calc_DH_supply)(Ths_supply,
                                                                    Tww_supply)  # FIXME: consider seperated DHW HEX

        # compare and update the DH plant supply temperature
        T_DH_supply = np.where(T_building_heatiing_supply_C > 0, T_building_heatiing_supply_C + DT_HEAT,
                               T_building_heatiing_supply_C)
        T_DHN_supply = np.vectorize(calc_DH_supply)(T_DH_supply, T_DHN_supply)


        heating_system_temperatures_dict[name] = {'Ths_supply_C': Ths_supply, 'Ths_return_C': Ths_return}


        # cooling supply temperature calculations based on heating configurations
        if cooling_configuration == 1:  # AHU
            Tcs_supply = Tcs_ahu_supply
            Tcs_return = Tcs_ahu_return
        elif cooling_configuration == 2:  # ARU
            Tcs_supply = Tcs_aru_supply
            Tcs_return = Tcs_aru_return
        elif cooling_configuration == 3:  # SCU
            Tcs_supply = Tcs_scu_supply
            Tcs_return = Tcs_scu_return
        elif cooling_configuration == 4:  # AHU + ARU
            Tcs_supply = np.vectorize(calc_DC_supply)(Tcs_ahu_supply, Tcs_aru_supply)
            Tcs_return = np.vectorize(calc_DC_return)(Tcs_ahu_return, Tcs_aru_return)
        elif cooling_configuration == 5:  # AHU + SHU
            Tcs_supply = np.vectorize(calc_DC_supply)(Tcs_ahu_supply, Tcs_scu_supply)
            Tcs_return = np.vectorize(calc_DC_return)(Tcs_ahu_return, Tcs_scu_return)
        elif cooling_configuration == 6:  # ARU + SHU
            Tcs_supply = np.vectorize(calc_DC_supply)(Tcs_aru_supply, Tcs_scu_supply)
            Tcs_return = np.vectorize(calc_DC_return)(Tcs_aru_return, Tcs_scu_return)
        elif cooling_configuration == 7:  # AHU + ARU + SHU
            T_space_cooling_intermediate_1 = np.vectorize(calc_DC_supply)(Tcs_ahu_supply, Tcs_aru_supply)
            Tcs_supply = np.vectorize(calc_DC_supply)(T_space_cooling_intermediate_1, Tcs_scu_supply)
            T_space_cooling_intermediate_2 = np.vectorize(calc_DC_return)(Tcs_ahu_return, Tcs_aru_return)
            Tcs_return = np.vectorize(calc_DC_return)(T_space_cooling_intermediate_2, Tcs_scu_return)
        elif cooling_configuration == 0:
            Tcs_supply = np.zeros(8760) + 1E6
            Tcs_return = np.zeros(8760) - 1E6
        else:
            raise ValueError('wrong heating configuration specified in substation_main!')

        # find the lowest temperature among space cooling, refrigeration, data center
        Tcs_supply_C = np.where(Tcs_supply != 1E6, Tcs_supply, 0)
        Tcs_return_C = np.where(Tcs_return != -1E6, Tcs_return, 0)
        T_supply_to_cs_ref = np.vectorize(calc_DC_supply)(Tcs_supply, Tcref_supply)
        T_supply_to_cs_ref_data = np.vectorize(calc_DC_supply)(T_supply_to_cs_ref, Tcdata_sys_supply)

        # update the DCN plant supply temperature
        T_DC_supply_to_cs_ref = np.where(T_supply_to_cs_ref != 1E6, T_supply_to_cs_ref - DT_COOL,
                                         1E6)  # when Tcs_supply equals 1E6, there is no flow
        T_DCN_supply_to_cs_ref = np.vectorize(calc_DC_supply)(T_DC_supply_to_cs_ref, T_DCN_supply_to_cs_ref)
        T_DC_supply_to_cs_ref_data = np.where(T_supply_to_cs_ref_data != 1E6, T_supply_to_cs_ref_data - DT_COOL, 1E6)
        T_DCN_supply_to_cs_ref_data = np.vectorize(calc_DC_supply)(T_DC_supply_to_cs_ref_data,
                                                                        T_DCN_supply_to_cs_ref_data)

        cooling_system_temperatures_dict[name] = {'Tcs_supply_C': Tcs_supply_C, 'Tcs_return_C': Tcs_return_C}


    DHN_supply = {'T_DH_supply_C': T_DHN_supply}
    T_DCN_supply_to_cs_ref = np.where(T_DCN_supply_to_cs_ref != 1E6, T_DCN_supply_to_cs_ref, 0)
    T_DCN_supply_to_cs_ref_data = np.where(T_DCN_supply_to_cs_ref_data != 1E6,
                                                T_DCN_supply_to_cs_ref_data, 0)
    DCN_supply = {'T_DC_supply_to_cs_ref_C': T_DCN_supply_to_cs_ref,
                  'T_DC_supply_to_cs_ref_data_C': T_DCN_supply_to_cs_ref_data}
    # Calculate disconnected buildings files and substation operation.
    if Flag:
        index = 0
        combi = [0] * len(building_names)
        for name in building_names:
            print name
            dfRes = total_demand[(total_demand.Name == name)]
            combi[index] = 1
            key = "".join(str(e) for e in combi)
            dfRes.to_csv(locator.get_optimization_substations_total_file(key), sep=',', float_format='%.3f')
            combi[index] = 0

            # calculate substation parameters per building
            print(name)
            substation_model(buildings_dict[name], DHN_supply, DCN_supply,
                             cooling_system_temperatures_dict[name], heating_system_temperatures_dict[name],
                             heating_configuration, cooling_configuration, locator)

            index += 1
    else:
        index = 0
        # calculate substation parameters per building
        for name in building_names:
            print(name)
            substation_model(buildings_dict[name], DHN_supply, DCN_supply,
                             cooling_system_temperatures_dict[name], heating_system_temperatures_dict[name],
                             heating_configuration, cooling_configuration, locator)

            # index += 1
    print time.clock() - t0, "seconds process time for the Substation Routine."


def substation_model(building, DHN_supply, DCN_supply, cs_temperatures, hs_temperatures, hs_configuration,
                     cs_configuration, locator):
    '''
    :param locator: path to locator function
    :param building: dataframe with consumption data per building
    :param T_heating_sup_C: vector with hourly temperature of the district heating network without losses
    :param T_DH_sup_C: vector with hourly temperature of the district heating netowork with losses
    :param T_DC_sup_C: vector with hourly temperature of the district coolig network with losses
    :param t_HS: maximum hourly temperature for all buildings connected due to space heating
    :param t_WW: maximum hourly temperature for all buildings connected due to domestic hot water
    :return:
        - Dataframe stored for every building with the mass flow rates and temperatures district heating and cooling
            side in:
        - where fName_result: ID of the building accounting for the individual at which it belongs to.

    '''

    # HEX sizing for space heating, calculate t_DH_return_hs, mcp_DH_hs
    Qhs_sys_ahu_kWh = building.Qhs_sys_ahu_kWh.values
    Qhs_sys_aru_kWh = building.Qhs_sys_aru_kWh.values
    Qhs_sys_shu_kWh = building.Qhs_sys_shu_kWh.values
    Qhs_sys_kWh_dict = {1: Qhs_sys_ahu_kWh, 2: Qhs_sys_aru_kWh, 3: Qhs_sys_shu_kWh,
                     4: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh, 5: Qhs_sys_ahu_kWh + Qhs_sys_shu_kWh,
                     6: Qhs_sys_aru_kWh + Qhs_sys_shu_kWh, 7: Qhs_sys_ahu_kWh + Qhs_sys_aru_kWh + Qhs_sys_shu_kWh}
    mcphs_sys_ahu_kWperC = building.mcphs_sys_ahu_kWperC.values
    mcphs_sys_aru_kWperC = building.mcphs_sys_aru_kWperC.values
    mcphs_sys_shu_kWperC = building.mcphs_sys_shu_kWperC.values
    mcphs_sys_kWperC_dict = {1: mcphs_sys_ahu_kWperC, 2: mcphs_sys_aru_kWperC, 3: mcphs_sys_shu_kWperC,
                          4: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC, 5: mcphs_sys_ahu_kWperC + mcphs_sys_shu_kWperC,
                          6: mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC,
                          7: mcphs_sys_ahu_kWperC + mcphs_sys_aru_kWperC + mcphs_sys_shu_kWperC}
    # fixme: this is the wrong aggregation! the mcp should be recalculated according to the updated Tsup/re, and this does not aggregate the domestic hot water

    if hs_configuration == 0:
        t_DH_return_hs = np.zeros(8760)
        mcp_DH_hs = np.zeros(8760)
        A_hex_hs = 0
        Qhs_sys_W = np.zeros(8760)
    else:
        thi = DHN_supply['T_DH_supply_C'] + 273  # In k
        Qhs_sys_W = Qhs_sys_kWh_dict[hs_configuration] * 1000  # in W
        Qnom_W = max(Qhs_sys_W)  # in W
        if Qnom_W > 0:
            tco = hs_temperatures['Ths_supply_C'] + 273  # in K
            tci = hs_temperatures['Ths_return_C'] + 273  # in K
            cc = mcphs_sys_kWperC_dict[hs_configuration] * 1000  # in W/K #fixme: recalculated with the Tsupply/return
            index = np.where(Qhs_sys_W == Qnom_W)[0][0]
            thi_0 = thi[index]
            tci_0 = tci[index]
            tco_0 = tco[index]
            cc_0 = cc[index]
            t_DH_return_hs, mcp_DH_hs, A_hex_hs = \
                calc_substation_heating(Qhs_sys_W, thi, tco, tci, cc, cc_0, Qnom_W, thi_0, tci_0, tco_0)
        else:
            t_DH_return_hs = np.zeros(8760)
            mcp_DH_hs = np.zeros(8760)
            A_hex_hs = 0
            tci = np.zeros(8760) + 273  # in K

    # HEX sizing for domestic hot water, calculate t_DH_return_ww, mcp_DH_ww
    Qww_sys_W = building.Qww_sys_kWh.values * 1000  # in W
    Qnom_W = max(Qww_sys_W)  # in W
    if Qnom_W > 0:
        thi = DHN_supply['T_DH_supply_C'] + 273  # In k
        tco = building.Tww_sys_sup_C + 273  # in K
        tci = building.Tww_sys_re_C + 273  # in K
        cc = building.mcpww_sys_kWperC.values * 1000  # in W/K
        index = np.where(Qww_sys_W == Qnom_W)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_ww, mcp_DH_ww, A_hex_ww = \
            calc_substation_heating(Qww_sys_W, thi, tco, tci, cc, cc_0, Qnom_W, thi_0, tci_0, tco_0)
    else:
        t_DH_return_ww = np.zeros(8760)
        A_hex_ww = 0
        mcp_DH_ww = np.zeros(8760)
        tci = np.zeros(8760) + 273  # in K


    # calculate mix temperature of return DH
    T_DH_return_C = np.vectorize(calc_DH_HEX_mix)(Qhs_sys_W, Qww_sys_W, t_DH_return_ww, mcp_DH_ww, t_DH_return_hs, mcp_DH_hs)
    mcp_DH = (mcp_DH_ww + mcp_DH_hs)

    # HEX sizing for spacing cooling, calculate t_DC_return_cs, mcp_DC_cs
    Qcs_sys_ahu_kWh = abs(building.Qcs_sys_ahu_kWh.values)
    Qcs_sys_aru_kWh = abs(building.Qcs_sys_aru_kWh.values)
    Qcs_sys_scu_kWh = abs(building.Qcs_sys_scu_kWh.values)
    Qcs_sys_kWh_dict = {1: Qcs_sys_ahu_kWh, 2: Qcs_sys_aru_kWh, 3: Qcs_sys_scu_kWh,
                     4: Qcs_sys_ahu_kWh + Qcs_sys_aru_kWh, 5: Qcs_sys_ahu_kWh + Qcs_sys_scu_kWh,
                     6: Qcs_sys_aru_kWh + Qcs_sys_scu_kWh, 7: Qcs_sys_ahu_kWh + Qcs_sys_aru_kWh + Qcs_sys_scu_kWh}
    mcpcs_sys_ahu_kWperC = abs(building.mcpcs_sys_ahu_kWperC.values)
    mcpcs_sys_aru_kWperC = abs(building.mcpcs_sys_aru_kWperC.values)
    mcpcs_sys_scu_kWperC = abs(building.mcpcs_sys_scu_kWperC.values)
    mcpcs_sys_kWperC_dict = {1: mcpcs_sys_ahu_kWperC, 2: mcpcs_sys_aru_kWperC, 3: mcpcs_sys_scu_kWperC,
                          4: mcpcs_sys_ahu_kWperC + mcpcs_sys_aru_kWperC, 5: mcpcs_sys_ahu_kWperC + mcpcs_sys_scu_kWperC,
                          6: mcpcs_sys_aru_kWperC + mcpcs_sys_scu_kWperC,
                          7: mcpcs_sys_ahu_kWperC + mcpcs_sys_aru_kWperC + mcpcs_sys_scu_kWperC}


    ## Cooling substation calculations
    if cs_configuration == 0:
        t_DC_return_cs = tci
        mcp_DC_cs = 0
        A_hex_cs = 0
        Qcs_sys_W = np.zeros(8760)
    else:
        tci = DCN_supply['T_DC_supply_to_cs_ref_data_C'] + 273 # fixme: change according to cs_ref or ce_ref_data
        Qcs_sys_W = abs(Qcs_sys_kWh_dict[cs_configuration]) * 1000  # in W
        # only include space cooling and refrigeration
        Qnom_W = max(Qcs_sys_W)  # in W
        if Qnom_W > 0:
            tho = cs_temperatures['Tcs_supply_C'] + 273  # in K
            thi = cs_temperatures['Tcs_return_C'] + 273  # in K
            ch = (mcpcs_sys_kWperC_dict[cs_configuration]) * 1000  # in W/K #fixme: recalculated with the Tsupply/return
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
    if cs_configuration == 0:
        t_DC_return_ref = tci
        mcp_DC_ref = 0
        A_hex_ref = 0
        Qcre_sys_W = np.zeros(8760)

    else:
        Qcre_sys_W = abs(building.Qcre_sys_kWh.values) * 1000  # in W
        Qnom_W = max(Qcre_sys_W)
        if Qnom_W > 0:
            tho = building.Tcref_sup_C + 273  # in K
            thi = building.Tcref_re_C + 273  # in K
            ch = (mcpcs_sys_kWperC_dict[cs_configuration]) * 1000  # in W/K
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
    if cs_configuration == 0:
        t_DC_return_data = tci
        mcp_DC_data = 0
        A_hex_data = 0
        Qcdata_sys_W = np.zeros(8760)

    else:
        Qcdata_sys_W = (abs(building.Qcdata_sys_kWh.values) * 1000)
        Qnom_W = max(Qcdata_sys_W)  # in W
        if Qnom_W > 0:
            tho = building.Tcdata_sys_sup_C + 273  # in K
            thi = building.Tcdata_sys_re_C + 273  # in K
            ch = (mcpcs_sys_kWperC_dict[cs_configuration]) * 1000  # in W/K
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
    T_DC_return_cs_ref_C = np.vectorize(calc_DH_HEX_mix)(Qcs_sys_W, Qcre_sys_W, t_DC_return_cs, mcp_DC_cs, t_DC_return_ref, mcp_DC_ref)
    T_DC_return_cs_ref_data_C = np.vectorize(calc_DC_HEX_mix)(Qcs_sys_W, Qcre_sys_W, Qcdata_sys_W, t_DC_return_cs, mcp_DC_cs,
                                                  t_DC_return_ref, mcp_DC_ref, t_DC_return_data, mcp_DC_data)
    mdot_space_cooling_data_center_and_refrigeration_result_flat = (mcp_DC_cs + mcp_DC_ref + mcp_DC_data)/ HEAT_CAPACITY_OF_WATER_JPERKGK  # convert from W/K to kg/s
    mdot_space_cooling_and_refrigeration_result_flat = (mcp_DC_cs + mcp_DC_ref)/ HEAT_CAPACITY_OF_WATER_JPERKGK  # convert from W/K to kg/s

    # converting units and quantities:
    T_return_DH_result_flat = T_DH_return_C + 273.0  # convert to K
    T_supply_DH_result_flat = DHN_supply['T_DH_supply_C'] + 273.0  # convert to K
    mdot_DH_result_flat = mcp_DH / HEAT_CAPACITY_OF_WATER_JPERKGK  # convert from W/K to kg/s


    # fixme: the following lines might be redundant
    T_supply_max_all_buildings_flat = hs_temperatures[
                                          'Ths_supply_C'] + 273.0  # convert to K #FIXME: check with old script
    T_hotwater_max_all_buildings_flat = building.Tww_sys_sup_C.values + 273.0  # convert to K #FIXME: check with old script
    T_heating_sup_max_all_buildings_flat = hs_temperatures[
                                               'Ths_supply_C'] + 273.0  # convert to K #FIXME: check with old script

    T_r1_dhw_result_flat = t_DH_return_ww + 273.0  # convert to K
    T_r1_space_heating_result_flat = t_DH_return_hs + 273.0  # convert to K

    T_r1_space_cooling_and_refrigeration_result_flat = T_DC_return_cs_ref_C + 273.0  # convert to K
    T_r1_space_cooling_data_center_and_refrigeration_result_flat = T_DC_return_cs_ref_data_C + 273.0  # convert to K

    T_supply_DC_flat = DCN_supply['T_DC_supply_to_cs_ref_C'] + 273.0  # convert to K
    T_supply_DC_space_cooling_data_center_and_refrigeration_result_flat = DCN_supply[
                                                                              'T_DC_supply_to_cs_ref_data_C'] + 273.0  # convert to K

    Electr_array_all_flat = building.E_sys_kWh.values * 1000  # convert to #to W #FIXME: check with old script

    # save the results into a .csv file
    # fixme: find usage of all results
    results = pd.DataFrame({"mdot_DH_result_kgpers": mdot_DH_result_flat,
                            "T_return_DH_result_K": T_return_DH_result_flat,
                            "T_supply_DH_result_K": T_supply_DH_result_flat,
                            "mdot_space_cooling_and_refrigeration_result_kgpers": mdot_space_cooling_and_refrigeration_result_flat,
                            "mdot_space_cooling_data_center_and_refrigeration_result_kgpers": mdot_space_cooling_data_center_and_refrigeration_result_flat,
                            "T_return_DC_space_cooling_and_refrigeration_result_K": T_r1_space_cooling_and_refrigeration_result_flat,
                            "T_return_DC_space_cooling_data_center_and_refrigeration_result_K": T_r1_space_cooling_data_center_and_refrigeration_result_flat,
                            "T_supply_DC_space_cooling_and_refrigeration_result_K": T_supply_DC_flat,
                            "T_supply_DC_space_cooling_data_center_and_refrigeration_result_K": T_supply_DC_space_cooling_data_center_and_refrigeration_result_flat,
                            "A_hex_heating_design_m2": A_hex_hs,
                            "A_hex_dhw_design_m2": A_hex_ww,
                            "A_hex_cs": A_hex_cs,
                            "A_hex_cs_space_cooling_data_center_and_refrigeration": A_hex_cs + A_hex_data + A_hex_ref,
                            # fixme: temporary output
                            "Q_heating_W": Qhs_sys_W,
                            "Q_dhw_W": Qww_sys_W,
                            "Q_space_cooling_and_refrigeration_W": Qcs_sys_W + Qcre_sys_W,  # fixme: temporary output
                            "Q_space_cooling_data_center_and_refrigeration_W": Qcs_sys_W + Qcdata_sys_W + Qcre_sys_W,
                            # fixme: temporary output
                            "T_total_supply_max_all_buildings_intern_K": T_supply_max_all_buildings_flat,
                            "T_hotwater_max_all_buildings_intern_K": T_hotwater_max_all_buildings_flat,
                            "T_heating_max_all_buildings_intern_K": T_heating_sup_max_all_buildings_flat,
                            "Electr_array_all_flat_W": Electr_array_all_flat})

    results.to_csv(locator.get_optimization_substations_results_file(building.Name.values[0]), sep=',', index=False,
                   float_format='%.3f')
    return results


# substation cooling
def calc_substation_cooling(Q, thi, tho, tci, ch, ch_0, Qnom, thi_0, tci_0, tho_0):
    '''
    this function calculates the state of the heat exchanger at the substation of every customer with cooling needs

    :param Q: cooling laad
    :param thi: in temperature of primary side
    :param tho: out temperature of primary side
    :param tci: in temperature of secondary side
    :param ch: capacity mass flow rate primary side
    :param ch_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of primary side
    :param tci_0: nominal in temperature of secondary side
    :param tho_0: nominal out temperature of primary side

    :return:
        - tco = out temperature of secondary side (district cooling network)
        - cc = capacity mass flow rate secondary side
        - Area_HEX_cooling = are of heat excahnger.

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
        - Area_HEX_heating = are of heat excahnger.

    '''
    # nominal conditions network side
    ch_0 = cc_0 * (tco_0 - tci_0) / ((thi_0 - tci_0) * 0.9)
    tho_0 = thi_0 - Qnom / ch_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0)
    # Area heat excahnge and UA_heating
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
    efficiency = 1 - scipy.exp((1 / cr) * (NTU ** 0.22) * (scipy.exp(-cr * (NTU) ** 0.78) - 1))
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
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

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
        (1 + scipy.exp(-(NTU) * (1 + cr ** 2))) / (1 - scipy.exp(-(NTU) * (1 + cr ** 2))))) ** -1
    return efficiency


def calc_DH_HEX_mix(Q1, Q2, t1, m1, t2, m2):
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
    if (m1 + m2) > 0:
        if Q1 > 0 or Q2 > 0:
            tavg = (t1 * m1 + t2 * m2) / (m1 + m2)
    else:
        tavg = 0
    return np.float(tavg)


def calc_DC_HEX_mix(Q1, Q2, Q3, t1, m1, t2, m2, t3, m3):

    if (m1 + m2 + m3) > 0:
        if Q1 > 0 or Q2 > 0 or Q3 > 0:
            tavg = (t1 * m1 + t2 * m2 + t3 * m3) / (m1 + m2 + m3)
    else:
        tavg = 0
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

    if Q_heating_W > 0.0:
        dT_primary = tco_K - tci_K if not isclose(tco_K, tci_K) else 0.0001  # to avoid errors with temperature changes < 0.001
        previous_efficiency = 0.1
        current_efficiency = -1.0  # dummy value for first iteration - never used in any calculations
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
        - dtm = logaritimic temperature difference

    '''
    dT1 = thi - tco
    dT2 = tho - tci if not isclose(tho, tci) else 0.0001  # to avoid errors with temperature changes < 0.001

    try:
        dTm = (dT1 - dT2) / scipy.log(dT1 / dT2)
    except ZeroDivisionError:
        raise Exception(thi, tco, tho, tci, "Check the emission_system database, there might be a problem with the selection of nominal temperatures")

    return abs(dTm.real)


def calc_area_HEX(Qnom, dTm_0, U):
    """

    Thi function calculates the area of a het exchanger at nominal conditions.

    :param Qnom: nominal load
    :param dTm_0: nominal logarithmic temperature difference
    :param U: coeffiicent of transmissivity
    :return:
        - ``area``, area of heat exchange
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
    # if t_0 == 0:
    #     t_0 = 1E6
    # if t_1 > 0:
    #     tmin = min(t_0, t_1)
    # else:
    #     tmin = t_0
    if t_0 == 0:
        t_0 = 1E6
    if t_1 == 0:
        t_1 = 1E6
    tmin = min(t_0, t_1)
    return tmin


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
    run the whole network summary routine
    """
    import cea.inputlocator as inputlocator

    locator = inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())

    substation_main(locator, total_demand, total_demand['Name'], heating_configuration=7, cooling_configuration=7,
                    Flag=False)

    print 'substation_main() succeeded'


if __name__ == '__main__':
    main(cea.config.Configuration())
