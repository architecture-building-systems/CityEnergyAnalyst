"""
Hydraulic - thermal network

"""
from __future__ import division

import math
import time

import numpy as np
import pandas as pd

from cea.optimization.constants import K_DH, ZERO_DEGREES_CELSIUS_IN_KELVIN
from cea.resources.geothermal import calc_ground_temperature
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.utilities import epwreader


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath", ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def network_main(locator, total_demand, building_names, config, gv, key):
    """
    This function summarizes the distribution demands and will give them as:
    - absolute values (design values = extreme values)
    - hourly operation scheme of input/output of distribution
    :param locator: locator class
    :param total_demand: dataframe with total demand of buildings
    :param building_names: vector with names of buildings
    :param gv: global variables class
    :param key: when called by the optimization, a key will provide an id for the individual
     and the generation.
    :type locator: class
    :type total_demand: list
    :type building_names: vector
    :type gv: class
    :type key: int
    :return: csv file stored in locator.get_optimization_network_results_folder() as fName_result
        where fName_result: FIXME: what?
    :rtype: Nonetype
    """

    t0 = time.clock()
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C','relhum_percent',
                                                              'windspd_ms', 'skytemp_C']]
    ground_temp = calc_ground_temperature(locator, weather_data['drybulb_C'], depth_m=10)
    # import properties of distribution
    network_type = config.thermal_network.network_type
    list_network_name = ['', '']  # config.thermal_network.network_names
    num_buildings_network = total_demand.Name.count()
    if len(list_network_name) == 0:
        network_name = ''
        pipes_tot_length = pd.read_csv(locator.get_optimization_network_edge_list_file(network_type, network_name),
                                       usecols=['pipe length']).sum().values
    else:
        for i, network_name in enumerate(list_network_name):
            if i == 0:
                pipes_tot_length = pd.read_csv(
                    locator.get_optimization_network_edge_list_file(network_type, network_name),
                    usecols=['pipe length']).sum().values
            else:
                pipes_tot_length = pipes_tot_length + pd.read_csv(
                    locator.get_optimization_network_edge_list_file(network_type, network_name),
                    usecols=['pipe length']).sum().values

    ntwk_length = pipes_tot_length.sum() * num_buildings_network / gv.num_tot_buildings

    # empty vectors
    buildings = []
    substations = []
    Qcdata_netw_total_kWh = np.zeros(8760)
    mcpdata_netw_total_kWperC = np.zeros(8760)
    Electr_netw_total_W = np.zeros(8760)
    mdot_heat_netw_all_kgpers = np.zeros(8760)
    mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers = np.zeros(8760)
    mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers = np.zeros(8760)
    Q_DH_building_netw_total_W = np.zeros(8760)
    Q_DC_building_netw_space_cooling_and_refrigeration_total_W = np.zeros(8760)
    Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W = np.zeros(8760)
    sum_tret_mdot_heat = np.zeros(8760)
    sum_tret_mdot_cool_space_cooling_and_refrigeration = np.zeros(8760)
    sum_tret_mdot_cool_space_cooling_data_center_and_refrigeration = np.zeros(8760)
    mdot_heat_netw_min_kgpers = np.zeros(8760) + 1E6
    mdot_cool_space_cooling_and_refrigeration_netw_min_kgpers = np.zeros(8760) + 1E6
    mdot_cool_space_cooling_data_center_and_refrigeration_netw_min_kgpers = np.zeros(8760) + 1E6
    iteration = 0

    for building_name in building_names:
        buildings.append(pd.read_csv(locator.get_demand_results_file(building_name),
                                     usecols=['DATE', 'mcpcdata_sys_kWperC', 'Qcdata_sys_kWh']))
        substations.append(pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                                       usecols=['Electr_array_all_flat_W', 'mdot_DH_result_kgpers',
                                                'mdot_space_cooling_and_refrigeration_result_kgpers',
                                                'mdot_space_cooling_data_center_and_refrigeration_result_kgpers',
                                                'Q_heating_W', 'Q_dhw_W',
                                                'Q_space_cooling_and_refrigeration_W',
                                                'Q_space_cooling_data_center_and_refrigeration_W',
                                                'T_return_DH_result_K',
                                                'T_return_DC_space_cooling_and_refrigeration_result_K',
                                                'T_return_DC_space_cooling_data_center_and_refrigeration_result_K',
                                                'T_supply_DH_result_K',
                                                'T_supply_DC_space_cooling_and_refrigeration_result_K',
                                                'T_supply_DC_space_cooling_data_center_and_refrigeration_result_K']))

        Qcdata_netw_total_kWh += buildings[iteration].Qcdata_sys_kWh.values
        mcpdata_netw_total_kWperC += buildings[iteration].mcpcdata_sys_kWperC.values
        Electr_netw_total_W += substations[iteration].Electr_array_all_flat_W.values
        mdot_heat_netw_all_kgpers += substations[iteration].mdot_DH_result_kgpers.values
        mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers += substations[iteration].mdot_space_cooling_and_refrigeration_result_kgpers.values
        mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers += substations[iteration].mdot_space_cooling_data_center_and_refrigeration_result_kgpers.values
        Q_DH_building_netw_total_W += (
                substations[iteration].Q_heating_W.values + substations[iteration].Q_dhw_W.values)
        Q_DC_building_netw_space_cooling_and_refrigeration_total_W += (substations[iteration].Q_space_cooling_and_refrigeration_W.values)
        Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W += (substations[iteration].Q_space_cooling_data_center_and_refrigeration_W.values)
        sum_tret_mdot_heat += substations[iteration].T_return_DH_result_K.values * substations[
            iteration].mdot_DH_result_kgpers.values
        sum_tret_mdot_cool_space_cooling_and_refrigeration += substations[
                                                                  iteration].T_return_DC_space_cooling_and_refrigeration_result_K.values * \
                                                              substations[iteration].mdot_space_cooling_and_refrigeration_result_kgpers.values
        sum_tret_mdot_cool_space_cooling_data_center_and_refrigeration += substations[
                                                                  iteration].T_return_DC_space_cooling_data_center_and_refrigeration_result_K.values * \
                                                              substations[iteration].mdot_space_cooling_data_center_and_refrigeration_result_kgpers.values

        # evaluate minimum flows
        mdot_heat_netw_min_kgpers = np.vectorize(calc_min_flow)(mdot_heat_netw_min_kgpers,
                                                                substations[iteration].mdot_DH_result_kgpers.values)
        mdot_cool_space_cooling_and_refrigeration_netw_min_kgpers = np.vectorize(calc_min_flow)(mdot_cool_space_cooling_and_refrigeration_netw_min_kgpers,
                                                                substations[iteration].mdot_space_cooling_and_refrigeration_result_kgpers.values)
        mdot_cool_space_cooling_data_center_and_refrigeration_netw_min_kgpers = np.vectorize(calc_min_flow)(mdot_cool_space_cooling_data_center_and_refrigeration_netw_min_kgpers,
                                                                substations[iteration].mdot_space_cooling_data_center_and_refrigeration_result_kgpers.values)
        iteration += 1

    # calculate thermal losses of distribution
    T_DHN_withoutlosses_re_K = np.vectorize(calc_return_temp)(sum_tret_mdot_heat, mdot_heat_netw_all_kgpers)

    T_DHN_withoutlosses_sup_K = np.vectorize(calc_supply_temp)(T_DHN_withoutlosses_re_K,
                                                               Q_DH_building_netw_total_W,
                                                               mdot_heat_netw_all_kgpers,
                                                               HEAT_CAPACITY_OF_WATER_JPERKGK, "DH")

    T_DCN_space_cooling_and_refrigeration_withoutlosses_re_K = np.vectorize(calc_return_temp)(sum_tret_mdot_cool_space_cooling_and_refrigeration,
                                                                                              mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers)
    T_DCN_space_cooling_and_refrigeration_withoutlosses_sup_K = np.vectorize(calc_supply_temp)(T_DCN_space_cooling_and_refrigeration_withoutlosses_re_K,
                                                                                               Q_DC_building_netw_space_cooling_and_refrigeration_total_W,
                                                                                               mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers,
                                                                                               HEAT_CAPACITY_OF_WATER_JPERKGK, "DC")

    T_DCN_space_cooling_data_center_and_refrigeration_withoutlosses_re_K = np.vectorize(calc_return_temp)(sum_tret_mdot_cool_space_cooling_data_center_and_refrigeration,
                                                                                                          mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers)
    T_DCN_space_cooling_data_center_and_refrigeration_withoutlosses_sup_K = np.vectorize(calc_supply_temp)(T_DCN_space_cooling_data_center_and_refrigeration_withoutlosses_re_K,
                                                                                                           Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W,
                                                                                                           mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers,
                                                                                                           HEAT_CAPACITY_OF_WATER_JPERKGK, "DC")



    Q_DH_losses_sup_W = np.vectorize(calc_piping_thermal_losses_heating)(T_DHN_withoutlosses_sup_K,
                                                                 mdot_heat_netw_all_kgpers, mdot_heat_netw_min_kgpers,
                                                                 ntwk_length, ground_temp, K_DH, HEAT_CAPACITY_OF_WATER_JPERKGK)

    Q_DH_losses_re_W = np.vectorize(calc_piping_thermal_losses_heating)(T_DHN_withoutlosses_re_K,
                                                                mdot_heat_netw_all_kgpers, mdot_heat_netw_min_kgpers,
                                                                ntwk_length, ground_temp, K_DH, HEAT_CAPACITY_OF_WATER_JPERKGK)
    Q_DH_losses_W = Q_DH_losses_sup_W + Q_DH_losses_re_W
    Q_DHNf_W = Q_DH_building_netw_total_W + Q_DH_losses_W

    Q_DC_space_cooling_and_refrigeration_losses_sup_W = np.vectorize(calc_piping_thermal_losses_cooling)(Q_DC_building_netw_space_cooling_and_refrigeration_total_W)
    Q_DC_space_cooling_data_center_and_refrigeration_losses_sup_W = np.vectorize(calc_piping_thermal_losses_cooling)(Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W)


    Q_DC_space_cooling_and_refrigeration_losses_re_W = np.vectorize(calc_piping_thermal_losses_cooling)(Q_DC_building_netw_space_cooling_and_refrigeration_total_W)
    Q_DC_space_cooling_data_center_and_refrigeration_losses_re_W = np.vectorize(calc_piping_thermal_losses_cooling)(Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W)

    Q_DC_space_cooling_and_refrigeration_losses_W = Q_DC_space_cooling_and_refrigeration_losses_sup_W + Q_DC_space_cooling_and_refrigeration_losses_re_W
    Q_DC_space_cooling_data_center_and_refrigeration_losses_W = Q_DC_space_cooling_data_center_and_refrigeration_losses_sup_W + Q_DC_space_cooling_data_center_and_refrigeration_losses_re_W

    Q_DCNf_space_cooling_and_refrigeration_W = Q_DC_building_netw_space_cooling_and_refrigeration_total_W + Q_DC_space_cooling_and_refrigeration_losses_W
    Q_DCNf_space_cooling_data_center_and_refrigeration_W = Q_DC_building_netw_space_cooling_data_center_and_refrigeration_total_W + Q_DC_space_cooling_data_center_and_refrigeration_losses_W


    T_DHN_re_K = np.vectorize(calc_temp_withlosses)(T_DHN_withoutlosses_re_K,
                                                    Q_DH_losses_re_W, mdot_heat_netw_all_kgpers,
                                                    HEAT_CAPACITY_OF_WATER_JPERKGK, "negative")

    T_DHN_sup_K = np.vectorize(calc_temp_withlosses)(T_DHN_withoutlosses_sup_K,
                                                     Q_DH_losses_sup_W, mdot_heat_netw_all_kgpers,
                                                     HEAT_CAPACITY_OF_WATER_JPERKGK, "positive")

    T_DCN_space_cooling_and_refrigeration_re_K = np.vectorize(calc_temp_withlosses)(T_DCN_space_cooling_and_refrigeration_withoutlosses_re_K,
                                                                                    Q_DC_space_cooling_and_refrigeration_losses_re_W,
                                                                                    mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers,
                                                                                    HEAT_CAPACITY_OF_WATER_JPERKGK, "positive")

    T_DCN_space_cooling_data_center_and_refrigeration_re_K = np.vectorize(calc_temp_withlosses)(T_DCN_space_cooling_data_center_and_refrigeration_withoutlosses_re_K,
                                                                                    Q_DC_space_cooling_data_center_and_refrigeration_losses_re_W,
                                                                                    mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers,
                                                                                    HEAT_CAPACITY_OF_WATER_JPERKGK, "positive")

    T_DCN_space_cooling_and_refrigeration_sup_K = np.vectorize(calc_temp_withlosses)(T_DCN_space_cooling_and_refrigeration_withoutlosses_sup_K,
                                                                                     Q_DC_space_cooling_and_refrigeration_losses_sup_W,
                                                                                     mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers,
                                                                                     HEAT_CAPACITY_OF_WATER_JPERKGK, "negative")

    T_DCN_space_cooling_data_center_and_refrigeration_sup_K = np.vectorize(calc_temp_withlosses)(T_DCN_space_cooling_data_center_and_refrigeration_withoutlosses_sup_K,
                                                                                     Q_DC_space_cooling_data_center_and_refrigeration_losses_sup_W,
                                                                                     mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers,
                                                                                     HEAT_CAPACITY_OF_WATER_JPERKGK, "negative")

    day_of_max_heatmassflow_fin = np.zeros(8760)
    day_of_max_heatmassflow = find_index_of_max(mdot_heat_netw_all_kgpers)
    day_of_max_heatmassflow_fin[:] = day_of_max_heatmassflow

    for i in range(8760):
        if T_DCN_space_cooling_data_center_and_refrigeration_sup_K[i] > T_DCN_space_cooling_data_center_and_refrigeration_re_K[i]:
            print (i)

        if T_DCN_space_cooling_and_refrigeration_sup_K[i] > T_DCN_space_cooling_and_refrigeration_re_K[i]:
            print (i)


    date = pd.read_csv(locator.get_demand_results_file(building_names[0])).DATE.values
    results = pd.DataFrame({"DATE": date,
                            "mdot_DH_netw_total_kgpers": mdot_heat_netw_all_kgpers,
                            "mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers": mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers,
                            "mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers": mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers,
                            "Q_DHNf_W": Q_DHNf_W,
                            "Q_DCNf_space_cooling_and_refrigeration_W": Q_DCNf_space_cooling_and_refrigeration_W,
                            "Q_DCNf_space_cooling_data_center_and_refrigeration_W": Q_DCNf_space_cooling_data_center_and_refrigeration_W,
                            "T_DHNf_re_K": T_DHN_re_K,
                            "T_DCNf_space_cooling_and_refrigeration_re_K": T_DCN_space_cooling_and_refrigeration_re_K,
                            "T_DCNf_space_cooling_data_center_and_refrigeration_re_K": T_DCN_space_cooling_data_center_and_refrigeration_re_K,
                            "T_DHNf_sup_K": T_DHN_sup_K,
                            "T_DCNf_space_cooling_and_refrigeration_sup_K": T_DCN_space_cooling_and_refrigeration_sup_K,
                            "T_DCNf_space_cooling_data_center_and_refrigeration_sup_K": T_DCN_space_cooling_data_center_and_refrigeration_sup_K,
                            "Qcdata_netw_total_kWh": Qcdata_netw_total_kWh,
                            "day_of_max_heatmassflow": day_of_max_heatmassflow,
                            "mcpdata_netw_total_kWperC": mcpdata_netw_total_kWperC,
                            "Electr_netw_total_W": Electr_netw_total_W,
                            "Q_DH_losses_W": Q_DH_losses_W,
                            "Q_DC_space_cooling_and_refrigeration_losses_W": Q_DC_space_cooling_and_refrigeration_losses_W,
                            "Q_DC_space_cooling_data_center_and_refrigeration_losses_W": Q_DC_space_cooling_data_center_and_refrigeration_losses_W})

    # the key depicts weather this is the distribution of all customers or a distribution of a gorup of them.
    if key == 'all':
        results.to_csv(locator.get_optimization_network_all_results_summary(key), index=False)
    else:
        results.to_csv(locator.get_optimization_network_results_summary(key), index=False)

    print time.clock() - t0, "seconds process time for Network summary for configuration", key, "\n"


# ============================
# Supply and return temperatures
# ============================

def calc_temp_withlosses(t0_K, Q_W, m_kgpers, cp, case):
    """
    This function calculates the new temperature of the distribution including losses
    :param t0_K: current distribution temperature
    :param Q_W: thermal losses in the corresponding network (either supply or return)
    :param m_kgpers: mass flow rate
    :param cp: specific heat capacity
    :param case: "positive": if there is an addition to the losses, :negative" otherwise
    :type t0_K: float
    :type Q_W: float
    :type m_kgpers: float
    :type cp: float
    :type case: string
    :return: t1: new temperature of the distribution accounting for thermal losses in the grid
    :rtype: float
    """
    if m_kgpers > 0:
        if case == "positive":
            t1_K = t0_K + Q_W / (m_kgpers * cp)
        else:
            t1_K = t0_K - Q_W / (m_kgpers * cp)
    else:
        t1_K = ZERO_DEGREES_CELSIUS_IN_KELVIN
    return t1_K


def calc_return_temp(sum_t_m, sum_m):
    """
    This function calculates the return temperature of the distribution for a time step
    It is a weighted average of all the return temperatures (from the substations) in the network
    This is an approximation of the return temperature of the network to the centralized plant
    :param sum_t_m: sum of temperature times mass flow rate
    :param sum_m: sum of mass flow rate
    :type sum_t_m: float
    :type sum_m: float
    :return: tr: vector return temperature
    :rtype: float
    """
    if sum_m > 0:
        tr_K = sum_t_m / sum_m
    else:
        tr_K = ZERO_DEGREES_CELSIUS_IN_KELVIN
    return tr_K


def calc_supply_temp(tr, Q, m, cp, case):
    """
    This function calculates the supply temperature of the distribution for a time step.
    :param tr: current return temperature
    :param Q: load including thermal losses
    :param m: mass flow rate
    :param cp: specific heat capacity
    :param case: 'DH' or something else??
    :type tr: float
    :type Q: float
    :type m: float
    :type cp: float
    :type case: string
    :return: ts: new temperature of the distribution accounting for thermal losses in the grid
    :rtype: float
    """
    if m > 0:
        if case == "DH":
            ts_K = tr + Q / (m * cp)
        else:
            ts_K = tr - Q / (m * cp)
    else:
        ts_K = ZERO_DEGREES_CELSIUS_IN_KELVIN
    return ts_K


# ============================
# Thermal losses
# ============================

def calc_piping_thermal_losses_heating(Tnet_K, m_max_kgpers, m_min_kgpers, L, Tg, K, cp):
    """
    This function estimates the average thermal losses of a distribution for an hour of the year
    :param Tnet_K: current temperature of the pipe
    :param m_max_kgpers: maximum mass flow rate in the pipe
    :param m_min_kgpers: minimum mass flow rate in the pipe
    :param L: length of the pipe
    :param Tg: ground temperature
    :param K: linear transmittance coefficient (it accounts for insulation and pipe diameter)
    :param cp: specific heat capacity
    :type Tnet_K: float
    :type m_max_kgpers: float
    :type m_min_kgpers: float
    :type L: float
    :type Tg: float
    :type K: float
    :type cp: float
    :return: Qloss: thermal lossess in the pipe.
    :rtype: float
    """
    if m_min_kgpers != 1E6:  # control variable see function fn.calc_min_flow
        mavg = (m_max_kgpers + m_min_kgpers) / 2
        Tx = Tg + (Tnet_K - Tg) * math.exp(-K * L / (mavg * cp))
        Qloss = (Tnet_K - Tx) * mavg * cp
    else:
        Qloss = 0
    return Qloss

def calc_piping_thermal_losses_cooling(Total_load_per_hour_W):
    """
    This function estimates the average thermal losses of a distribution for an hour of the year
    :param Tnet_K: current temperature of the pipe
    :param m_max_kgpers: maximum mass flow rate in the pipe
    :param m_min_kgpers: minimum mass flow rate in the pipe
    :param L: length of the pipe
    :param Tg: ground temperature
    :param K: linear transmittance coefficient (it accounts for insulation and pipe diameter)
    :param cp: specific heat capacity
    :type Tnet_K: float
    :type m_max_kgpers: float
    :type m_min_kgpers: float
    :type L: float
    :type Tg: float
    :type K: float
    :type cp: float
    :return: Qloss: thermal lossess in the pipe.
    :rtype: float
    """
    Qloss = 0.05 * Total_load_per_hour_W #FixMe: Link the value directly to the thermal network matrix
    return Qloss


# ============================
# Mass flow rates
# ============================

def calc_min_flow(m0, m1):
    """
    This function calculates the minimum flow of a distribution by comparison of two vectors.
    this is useful when looking up at multiple buildings in a for loop.
    :param m0: last minimum mass flow rate
    :param m1: current minimum mass flow rate
    :type m0: float
    :type m1: float
    :return: mmin: new minimum mass flow rate
    :rtype: float
    """
    if m0 == 0:
        m0 = 1E6
    if m1 > 0:
        mmin = min(m0, m1)
    else:
        mmin = m0
    return mmin


def find_index_of_max(array):
    """
    Returns the index of an array on which the maximum value is at.
    :param array: ndarray, Array of observations. Each row represents a day and each column
    the hourly data of that day
    :type array: list
    :return: max_index_hour : integer, max_index_hour : tells on what hour it happens (hour of the year)
     to use: e.g. data_array[max_index_hour] will give the maximum data of the year
    :rtype: list
    """

    max_value = -abs(np.amax(array))

    max_index_hour = 0

    for k in range(len(array)):
        if array[k] > max_value:
            max_value = array[k]
            max_index_hour = k

    return max_index_hour