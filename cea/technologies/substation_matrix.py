"""
Implements the substation model.
"""
from __future__ import division
import pandas as pd
import time
import numpy as np
import scipy
import cea.config
import cea.technologies.constants as constants

BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Thsf_sup_C', 'Thsf_re_C', 'Twwf_sup_C', 'Twwf_re_C', 'Tcsf_sup_C', 'Tcsf_re_C',
                   'Tcdataf_sup_C', 'Tcdataf_re_C', 'Tcref_sup_C', 'Tcref_re_C', 'Qhsf_kWh', 'Qwwf_kWh', 'Qcsf_kWh',
                   'Qcsf_lat_kWh', 'Qcdataf_kWh', 'Qcref_kWh', 'mcphsf_kWperC', 'mcpwwf_kWperC', 'mcpcsf_kWperC',
                   'Ef_kWh']

__author__ = "Jimeno A. Fonseca, Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Tim Vollrath", "Thuy-An Nguyen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# ============================
# Substation model
# ============================


def substation_HEX_design_main(buildings_demands):
    """
    This function calculates the temperatures and mass flow rates of the district heating network
    at every costumer. Based on this, the script calculates the hourly temperature of the network at the plant.
    This temperature needs to be equal to that of the customer with the highest temperature requirement plus thermal
    losses in the network.

    :param buildings_demands: Dictionary of DataFrames with all buildings_demands in the area

    :return: ``(substations_HEX_specs, buildings_demands)`` - substations_HEX_specs: dataframe with substation heat
        exchanger specs at each building,  buildings_demands: lists of heating demand/flowrate/supply temperature of all
        buildings connected to the network.
    """

    t0 = time.clock()

    # Calculate disconnected buildings_demands files and substation operation.
    substations_HEX_specs = pd.DataFrame(columns=['HEX_area_SH', 'HEX_area_DHW','HEX_area_SC', 'HEX_UA_SH', 'HEX_UA_DHW', 'HEX_UA_SC'])
    for name in buildings_demands.keys():
        print name
        # calculate substation parameters (A,UA) per building and store to .csv (target)
        substation_HEX = substation_HEX_sizing(buildings_demands[name])
        # write into dataframe
        substations_HEX_specs.ix[name]= substation_HEX

    print time.clock() - t0, "seconds process time for the Substation Routine \n"
    return substations_HEX_specs


def determine_building_supply_temperatures(building_names, locator):
    """
    determine thermal network target temperatures (T_supply_DH,T_supply_DC) at costumer side.

    :param building_names:
    :param locator:
    :return:
    """
    buildings_demands = {}
    for name in building_names:
        name = str(name)
        buildings_demands[name]=pd.read_csv(locator.get_demand_results_file(name),
                                             usecols=(BUILDINGS_DEMANDS_COLUMNS))
        Q_substation_heating = buildings_demands[name].Qhsf_kWh + buildings_demands[name].Qwwf_kWh
        Q_substation_cooling = buildings_demands[name].Qcsf_kWh + buildings_demands[name].Qcsf_lat_kWh + \
                               buildings_demands[name].Qcdataf_kWh + buildings_demands[name].Qcref_kWh
        # set the building side heating supply temperature
        T_supply_heating = np.vectorize(calc_DH_supply)(buildings_demands[name].Thsf_sup_C,
                                                        np.where(buildings_demands[name].Qwwf_kWh > 0,
                                                                 buildings_demands[name].Twwf_sup_C,
                                                                 np.nan))
        # set the building side cooling supply temperature
        T_supply_cooling = np.vectorize(calc_DC_supply)(np.where(buildings_demands[name].Qcsf_kWh > 0,
                                                                 buildings_demands[name].Tcsf_sup_C,
                                                                 np.nan),
                                                        np.where(buildings_demands[name].Qcdataf_kWh > 0,
                                                                 buildings_demands[name].Tcdataf_sup_C,
                                                                 np.nan),
                                                        np.where(buildings_demands[name].Qcref_kWh > 0,
                                                                 buildings_demands[name].Tcref_sup_C,
                                                                 np.nan))

        # find the target substation supply temperature
        T_supply_DH = np.where(Q_substation_heating > 0, T_supply_heating + constants.dT_heat, np.nan)
        T_supply_DC = np.where(abs(Q_substation_cooling) > 0, T_supply_cooling - constants.dT_cool, np.nan)

        buildings_demands[name]['Q_substation_heating'] = Q_substation_heating
        buildings_demands[name]['Q_substation_cooling'] = Q_substation_cooling
        buildings_demands[name]['T_sup_target_DH'] = T_supply_DH
        buildings_demands[name]['T_sup_target_DC'] = T_supply_DC

    return buildings_demands


def substation_HEX_sizing(building_demand):
    """
    This function size the substation heat exchanger area and the UA values.

    :param building_demand: dataframe with building demand properties
    :return: A list of substation heat exchanger properties (Area & UA) for heating, cooling and DHW
    """
    t_DH_supply = building_demand.T_sup_target_DH
    t_DC_supply = building_demand.T_sup_target_DC

    thi = t_DH_supply + 273  # In K
    Qhsf = building_demand.Qhsf_kWh.values * 1000  # in W
    Qnom = max(Qhsf)  # in W
    if Qnom > 0:
        tco = building_demand.Thsf_sup_C.values + 273  # in K
        tci = building_demand.Thsf_re_C.values + 273  # in K
        cc = building_demand.mcphsf_kWperC.values * 1000  # in W/K
        index = np.where(Qhsf == Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        A_hex_hs, UA_heating_hs = calc_heating_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0)
    else:
        A_hex_hs = 0
        UA_heating_hs = 0

    # calculate HEX area and UA for DHW
    Qwwf = building_demand.Qwwf_kWh.values * 1000  # in W
    Qnom = max(Qwwf)  # in W
    if Qnom > 0:
        tco = building_demand.Twwf_sup_C.values + 273  # in K
        tci = building_demand.Twwf_re_C.values + 273  # in K
        cc = building_demand.mcpwwf_kWperC.values * 1000  # in W/K
        index = np.where(Qwwf == Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        A_hex_ww, UA_heating_ww = calc_heating_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0)
    else:
        A_hex_ww = 0
        UA_heating_ww = 0


    # calculate HEX area and UA for cooling costumers incl refrigeration and processes
    Qcf = (abs(building_demand.Qcsf_kWh.values)) * 1000  # in W
    Qnom = max(Qcf)  # in W
    if Qnom > 0:
        tci = t_DC_supply + 273  # in K
        tho = building_demand.Tcsf_sup_C.values + 273  # in K
        thi = building_demand.Tcsf_re_C.values + 273  # in K
        ch = (abs(building_demand.mcpcsf_kWperC.values)) * 1000  # in W/K
        index = np.where(Qcf == Qnom)[0][0]
        tci_0 = tci[index]  # in K
        thi_0 = thi[index]
        tho_0 = tho[index]
        ch_0 = ch[index]
        A_hex_cs, UA_cooling_cs = calc_cooling_substation_heat_exchange(ch_0, Qnom, thi_0, tci_0, tho_0)
    else:
        A_hex_cs = 0
        UA_cooling_cs = 0

    return [A_hex_hs, A_hex_ww, A_hex_cs, UA_heating_hs, UA_heating_ww, UA_cooling_cs]


def substation_return_model_main(thermal_network, T_substation_supply, t, consumer_building_names):
    """
    Calculate all substation return temperature and required flow rate at each time-step.

    :param locator: an InputLocator instance set to the scenario to work on
    :param buildings_demands: dictionarz of building demands
    :param substations_HEX_specs: list of substation heat exchanger Area and UA for heating, cooling and DHW
    :param T_substation_supply: supply temperature at each substation in [K]
    :param t: time-step
    :param network_type: a string that defines whether the network is a district heating ('DH') or cooling ('DC')
                         network
    :param use_same_temperature_for_all_nodes: flag for calculating nominal flow rate, using one target temperature

    :param thermal_network: container for all the
           thermal network data.
    :type thermal_network: cea.technologies.thermal_network.thermal_network_matrix.ThermalNetwork

    :return:

    """
    index = 0
    # combi = [0] * len(building_names)
    T_return_all_K = pd.DataFrame()
    mdot_sum_all_kgs = pd.DataFrame()

    for name in consumer_building_names:
        building = thermal_network.buildings_demands[name].loc[[t]]

        # find substation supply temperature
        T_substation_supply_K = T_substation_supply.loc['T_supply', name]

        if thermal_network.network_type == 'DH':
            # calculate DH substation return temperature and substation flow rate
            T_substation_return_K, mcp_sub = calc_substation_return_DH(building, T_substation_supply_K,
                                                                       thermal_network.substations_HEX_specs.ix[name])
        else:
            # calculate DC substation return temperature and substation flow rate
            T_substation_return_K, mcp_sub = calc_substation_return_DC(building, T_substation_supply_K,
                                                                       thermal_network.substations_HEX_specs.ix[name])

        T_return_all_K[name] = [T_substation_return_K]
        mdot_sum_all_kgs[name] = [mcp_sub/(constants.cp/1000)]   # [kg/s]
        index += 1
    mdot_sum_all_kgs = np.round(mdot_sum_all_kgs, 5)
    return T_return_all_K, mdot_sum_all_kgs

def calc_substation_return_DH(building, T_DH_supply_K, substation_HEX_specs):
    """
    calculate individual substation return temperature and required heat capacity (mcp) of the supply stream
    at each time step.
    :param building: list of building informations
    :param T_DH_supply_K: matrix of the substation supply temperatures in K
    :param substation_HEX_specs: substation heat exchanger properties

    :return t_return_DH: the substation return temperature
    :return mcp_DH: the required heat capacity (mcp) from the DH
    """
    UA_heating_hs = substation_HEX_specs.HEX_UA_SH
    UA_heating_ww = substation_HEX_specs.HEX_UA_DHW

    thi = T_DH_supply_K  # In [K]
    Qhsf = building.Qhsf_kWh.values * 1000  # in W
    if Qhsf.max() > 0:
        tco = building.Thsf_sup_C.values + 273  # in K
        tci = building.Thsf_re_C.values + 273  # in K
        cc = building.mcphsf_kWperC.values * 1000  # in W/K
        t_DH_return_hs, mcp_DH_hs = calc_HEX_heating(Qhsf, UA_heating_hs, thi, tco, tci, cc)
            # calc_required_flow_and_t_return(Qhsf, UA_heating_hs, thi, tco, tci, cc)
    else:
        t_DH_return_hs = T_DH_supply_K
        mcp_DH_hs = 0

    Qwwf = building.Qwwf_kWh.values * 1000  # in W
    if Qwwf.max() > 0:
        tco = building.Twwf_sup_C.values + 273  # in K
        tci = building.Twwf_re_C.values + 273  # in K
        cc = building.mcpwwf_kWperC.values * 1000  # in W/K
        t_DH_return_ww, mcp_DH_ww = calc_HEX_heating(Qwwf, UA_heating_ww, thi, tco, tci, cc)   #[kW/K]
    else:
        t_DH_return_ww = T_DH_supply_K
        mcp_DH_ww = 0

    # calculate mix temperature of return DH
    T_DH_return_K = calc_HEX_mix(Qhsf, Qwwf, t_DH_return_ww, mcp_DH_ww, t_DH_return_hs, mcp_DH_hs)
    mcp_DH_kWK = mcp_DH_ww + mcp_DH_hs  #[kW/K]

    return T_DH_return_K, mcp_DH_kWK

def calc_substation_return_DC(building, T_DC_supply, substation_HEX_specs):
    """
    calculate individual substation return temperature and required heat capacity (mcp) of the supply stream
    at each time step
    :param building: list of building information
    :param T_DC_supply: substation supply temperature in K
    :param substation_HEX_specs: substation heat exchanger properties
    :return:
    """
    UA_cooling_cs = substation_HEX_specs.HEX_UA_SC
    Qcf = (abs(building.Qcsf_kWh.values)) * 1000  # in W
    if Qcf.max() > 0:
        tci = T_DC_supply  # in K
        tho = building.Tcsf_sup_C.values + 273  # in K
        thi = building.Tcsf_re_C.values + 273  # in K
        ch = (abs(building.mcpcsf_kWperC.values)) * 1000  # in W/K
        t_DC_return_cs, mcp_DC_cs = calc_HEX_cooling(Qcf, UA_cooling_cs, thi, tho, tci, ch)
    else:
        t_DC_return_cs = T_DC_supply
        mcp_DC_cs = 0

    return t_DC_return_cs, mcp_DC_cs

# ============================
# substation cooling
# ============================


def calc_cooling_substation_heat_exchange(ch_0, Qnom, thi_0, tci_0, tho_0):
    """
    this function calculates the state of the heat exchanger at the substation of every customer with cooling needs
    :param Q: cooling load
    :param thi: in temperature of primary side
    :param tho: out temperature of primary side
    :param tci: in temperature of secondary side
    :param ch: capacity mass flow rate primary side
    :param ch_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of primary side
    :param tci_0: nominal in temperature of secondary side
    :param tho_0: nominal out temperature of primary side
    :return: ``(Area_HEX_cooling, UA_cooling)``, area of heat excahnger, ..?
    """

    # nominal conditions network side
    cc_0 = ch_0 * (thi_0 - tho_0) / ((thi_0 - tci_0) * 0.9)  # FIXME
    tco_0 = Qnom / cc_0 + tci_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0, 'cool')
    # Area heat exchange and UA_heating
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom, dTm_0, constants.U_cool)

    return Area_HEX_cooling, UA_cooling



# ============================
# substation heating
# ============================


def calc_heating_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0):
    '''
    This function capculates the Area and UA of each substation heat exchanger.

    :param cc_0: nominal capacity mass flow rate primary side
    :param Qnom: nominal cooling load
    :param thi_0: nominal in temperature of secondary side
    :param tci_0: nominal in temperature of primary side
    :param tco_0: nominal out temperature of primary side

    :return Area_HEX_heating: Heat exchanger area in [m2]
    :return UA_heating: UA [
    '''
    # nominal conditions network side
    ch_0 = cc_0 * (tco_0 - tci_0) / ((thi_0 - tci_0) * 0.9)  # FIXME
    tho_0 = thi_0 - Qnom / ch_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0, 'heat')
    # Area heat exchange and UA_heating
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom, dTm_0, constants.U_heat)
    return Area_HEX_heating, UA_heating


# ============================
# Heat exchanger model
# ============================


def calc_HEX_cooling(Q, UA, thi, tho, tci, ch):
    """
    This function calculates the mass flow rate, temperature of return (secondary side)
    and heat exchanger area for a plate heat exchanger.
    Method of Number of Transfer Units (NTU)

    :param Q: cooling load
    :param UA: coefficient representing the area of heat exchanger times the coefficient of transmittance of the
        heat exchanger
    :param thi: in temperature of primary side
    :param tho: out temperature of primary side
    :param tci: in temperature of secondary side
    :param ch: capacity mass flow rate primary side
    :return: ``(tco, cc)`` out temperature of secondary side (district cooling network), capacity mass flow rate
        secondary side
    """

    if ch > 0:
        eff = [0.1, 0]  # FIXME
        Flag = False
        tol = 0.00000001
        while abs((eff[0] - eff[1]) / eff[0]) > tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = ch * (thi - tho) / ((thi - tci) * eff[0])
            if cmin < ch:
                cc = cmin
                cmax = ch
            else:
                cc = cmin
                cmax = cc
                cmin = ch
            cr = cmin / cmax
            NTU = UA / cmin
            eff[1] = calc_plate_HEX(NTU, cr)
            cmin = ch * (thi - tho) / ((thi - tci) * eff[1])
            tco = tci + eff[1] * cmin * (thi - tci) / cc
            Flag = True
        cc = Q / abs(tci - tco)
        tco = tco   # in [K]
    else:
        tco = 0
        cc = 0
    return np.float(tco), np.float(cc / 1000)


def calc_plate_HEX(NTU, cr):
    '''
    This function calculates the efficiency of exchange for a plate heat exchanger according to the NTU method of
    AShRAE 90.1

    :param NTU: number of transfer units
    :param cr: ratio between min and max capacity mass flow rates
    :return:
        eff: efficiency of heat exchange
    '''
    eff = 1 - scipy.exp((1 / cr) * (NTU ** 0.22) * (scipy.exp(-cr * (NTU) ** 0.78) - 1))
    return eff


def calc_shell_HEX(NTU, cr):
    '''
    This function calculates the efficiency of exchange for a tube-shell heat exchanger according to the NTU method of
    AShRAE 90.1

    :param NTU: number of transfer units
    :param cr: ratio between min and max capacity mass flow rates
    :return:
        eff: efficiency of heat exchange
    '''
    eff = 2 * ((1 + cr + (1 + cr ** 2) ** (1 / 2)) * (
        (1 + scipy.exp(-(NTU) * (1 + cr ** 2))) / (1 - scipy.exp(-(NTU) * (1 + cr ** 2))))) ** -1
    return eff


def calc_HEX_mix(Q1, Q2, t1, m1, t2, m2):
    '''
    This function computes the average  temperature between two vectors of heating demand.
    In this case, domestic hotwater and space heating.

    :param Q1: load heating
    :param Q2: load domestic hot water
    :param t1: out temperature of heat exchanger for space heating
    :param m1: mass flow rate secondary side of heat exchanger for space heating
    :param t2: out temperature of heat exchanger for domestic hot water
    :param m2: mass flow rate secondary side of heat exchanger for domestic hot water
    :return:
        tavg: average out temperature.
    '''
    if Q1.max() > 0 or Q2.max() > 0:
        tavg = (t1 * m1 + t2 * m2) / (m1 + m2)
    else:
        tavg = (t1+t2)/2  # if there is no flow rate, tavg = t1 = t2
    return np.float(tavg)


def calc_HEX_heating(Q, UA, thi, tco, tci, cc):
    """
    This function calculates the mass flow rate, temperature of return (secondary side)
    and heat exchanger area for a shell-tube pleat exchanger in the heating case.

    Method of Number of Transfer Units (NTU)

    :param Q: load
    :param UA: coefficient representing the area of heat exchanger times the coefficient of transmittance of the
        heat exchanger
    :param thi: in temperature of secondary side
    :param tco: out temperature of primary side
    :param tci: in temperature of primary side
    :param cc: capacity mass flow rate primary side

    :return: tho = out temperature of secondary side (district cooling network), ch = capacity mass flow rate secondary side
    """

    if Q > 0:
        eff = [0.1, 0]  # FIXME
        Flag = False
        tol = 0.00000001
        while abs((eff[0] - eff[1]) / eff[0]) > tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = cc * (tco - tci) / ((thi - tci) * eff[0])
            if cmin < cc:
                ch = cmin
                cmax = cc
            else:
                ch = cmin
                cmax = cmin
                cmin = cc
            cr = cmin / cmax
            NTU = UA / cmin
            eff[1] = calc_shell_HEX(NTU, cr)
            cmin = cc * (tco - tci) / ((thi - tci) * eff[1])
            tho = thi - eff[1] * cmin * (thi - tci) / ch
            Flag = True

    else:
        tho = 0
        ch = 0
    return np.float(tho), np.float(ch / 1000)


def calc_dTm_HEX(thi, tho, tci, tco, flag):
    '''
    This function estimates the logarithmic temperature difference between two streams

    :param thi: in temperature hot stream
    :param tho: out temperature hot stream
    :param tci: in temperature cold stream
    :param tco: out temperature cold stream
    :param flag: heat: when using for the heating case, 'cool' otherwise
    :return:
        dtm = logaritimic temperature difference
    '''
    dT1 = thi - tco
    dT2 = tho - tci
    if flag == 'heat':
        dTm = (dT1 - dT2) / scipy.log(dT1 / dT2)
    else:
        dTm = (dT2 - dT1) / scipy.log(dT2 / dT1)
    return abs(dTm.real)


def calc_area_HEX(Qnom, dTm_0, U):
    """
    This function calculates the area of a het exchanger at nominal conditions.

    :param Qnom: nominal load
    :param dTm_0: nominal logarithmic temperature difference
    :param U: coeffiicent of transmissivity
    :return: ``(area, UA)``: area: area of heat exchange,  UA: coefficient representing the area of heat exchanger times
        the coefficient of transmittance of the heat exchanger
    """
    area = Qnom / (dTm_0 * U)  # Qnom in W
    UA = U * area
    return area, UA

# ============================
# Other functions
# ============================
def calc_DC_supply(t_0, t_1, t_2):
    """
    This function calculates the temperature of the district cooling network according to the minimum observed
    (different to zero) in all buildings connected to the grid.
    :param t_0: last minimum temperature
    :param t_1:  current minimum temperature to evaluate
    :return tmin: new minimum temperature
    """

    tmin = min(t_0,t_1,t_2)
    return tmin


def calc_DH_supply(t_0, t_1):
    """
    This function calculates the heating temperature requirement of the building side according to the maximum
    temperature requirement at that time-step.
    :param t_0: temperature requirement from one heating application
    :param t_1: temperature requirement from another heating application
    :return: ``tmax``: maximum temperature requirement
    """
    tmax = max(t_0, t_1)
    return tmax


def calc_total_network_flow(Q_all, flowrate):
    return Q_all + flowrate

# ============================
# Test
# ============================
def main(config):
    """
    run the whole network summary routine
    """
    from cea.technologies.thermal_network.thermal_network_matrix import ThermalNetwork
    import cea.inputlocator as inputlocator

    locator = cea.inputlocator.InputLocator(config.scenario)

    network_type = config.thermal_network.network_type
    network_name = ''
    file_type = config.thermal_network.file_type
    thermal_network = ThermalNetwork(locator, network_type, network_name, file_type)


    t = 1000  # FIXME
    T_DH = 60  # FIXME
    network = 'DH'  # FIXME

    thermal_network.buildings_demands = determine_building_supply_temperatures(thermal_network.building_names, locator)
    thermal_network.substations_HEX_specs = substation_HEX_design_main(thermal_network.buildings_demands)
    T_substation_supply_K = pd.DataFrame([[T_DH + 273.0] * len(thermal_network.building_names)],
                                         columns=thermal_network.building_names, index=['T_supply'])
    substation_return_model_main(thermal_network, T_substation_supply_K, t, thermal_network.building_names)

    print('substation_main() succeeded')


if __name__ == '__main__':
    main(cea.config.Configuration())
