"""
Implements the substation model.
"""
from __future__ import division
import pandas as pd
import time
import numpy as np
import scipy
import cea.config
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.technologies.constants import DT_COOL, DT_HEAT, U_COOL, U_HEAT
from cea.technologies.thermal_network.demand_inputs_thermal_network import calc_demand_aggregation

BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Thsf_sup_aru_C', 'Thsf_sup_ahu_C', 'Thsf_sup_shu_C', 'Twwf_sup_C', 'Twwf_re_C',
                             'Tcdataf_sup_C', 'Thsf_re_aru_C', 'Thsf_re_ahu_C', 'Thsf_re_shu_C', 'Tcdataf_re_C',
                             'Tcref_sup_C', 'Tcref_re_C', 'Tcsf_sup_ahu_C',
                             'Tcsf_sup_aru_C', 'Tcsf_sup_scu_C', 'Tcsf_re_ahu_C', 'Tcsf_re_aru_C', 'Tcsf_re_scu_C',
                             'Qhsf_aru_kWh', 'Qhsf_ahu_kWh', 'Qhsf_shu_kWh', 'Qwwf_kWh', 'Qcsf_lat_kWh', 'Qcdataf_kWh',
                             'Qcref_kWh', 'Qcsf_ahu_kWh', 'Qcsf_aru_kWh', 'Qcsf_scu_kWh', 'mcphsf_aru_kWperC',
                             'mcphsf_ahu_kWperC', 'mcphsf_shu_kWperC', 'mcpwwf_kWperC', 'mcpcsf_ahu_kWperC',
                             'mcpcsf_aru_kWperC', 'mcpcsf_scu_kWperC', 'Ef_kWh']

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


def substation_HEX_design_main(buildings_demands, substation_systems):
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
    substations_HEX_specs = pd.DataFrame(columns=['HEX_areas', 'HEX_UA'])
    for name in buildings_demands.keys():
        print name
        # calculate substation parameters (A,UA) per building and store to .csv (target)
        substation_HEX = substation_HEX_sizing(buildings_demands[name], substation_systems)
        # write into dataframe
        substations_HEX_specs.ix[name]= substation_HEX

    print time.clock() - t0, "seconds process time for the Substation Routine \n"
    return substations_HEX_specs


def determine_building_supply_temperatures(building_names, locator, substation_systems):
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
        Q_substation_heating = 0
        T_supply_heating = np.nan
        for system in substation_systems['heating']:
            if system == 'ww':
                Q_substation_heating = Q_substation_heating + buildings_demands[name].Qwwf_kWh
                T_supply_heating = np.vectorize(calc_DH_supply)(T_supply_heating,
                                                                np.where(buildings_demands[name].Qwwf_kWh > 0,
                                                                         buildings_demands[name].Twwf_sup_C,
                                                                         np.nan))
            else:
                Q_substation_heating = Q_substation_heating + buildings_demands[name]['Qhsf_'+system+'_kWh']
                # set the building side heating supply temperature
                T_supply_heating = np.vectorize(calc_DH_supply)(T_supply_heating,
                                                            np.where(buildings_demands[name]['Qhsf_'+system+'_kWh'] > 0,
                                                                     buildings_demands[name]['Thsf_sup_'+system+'_C'],
                                                                     np.nan))

        Q_substation_cooling = 0
        T_supply_cooling = np.nan
        for system in substation_systems['cooling']:
            if system == 'data':
                Q_substation_cooling = Q_substation_cooling + buildings_demands[name].Qcdataf_kWh
                T_supply_cooling = np.vectorize(calc_DC_supply)(T_supply_cooling,
                                                                np.where(abs(buildings_demands[name].Qcdataf_kWh) > 0,
                                                                         buildings_demands[name].Tcdataf_sup_C,
                                                                         np.nan))
            elif system == 'ref':
                Q_substation_cooling = Q_substation_cooling + buildings_demands[name].Qcref_kWh
                T_supply_cooling = np.vectorize(calc_DC_supply)(T_supply_cooling,
                                                                np.where(abs(buildings_demands[name].Qcref_kWh) > 0,
                                                                         buildings_demands[name].Tcref_sup_C,
                                                                         np.nan))
            else:
                Q_substation_cooling = Q_substation_cooling + buildings_demands[name]['Qcsf_'+system+'_kWh']
                T_supply_cooling = np.vectorize(calc_DC_supply)(T_supply_cooling,
                                                                np.where(abs(buildings_demands[name]['Qcsf_'+system+'_kWh']) > 0,
                                                                         buildings_demands[name]['Tcsf_sup_'+system+'_C'],
                                                                         np.nan))

        # find the target substation supply temperature
        T_supply_DH = np.where(Q_substation_heating > 0, T_supply_heating + DT_HEAT, np.nan)
        T_supply_DC = np.where(abs(Q_substation_cooling) > 0, T_supply_cooling - DT_COOL, np.nan)

        buildings_demands[name]['Q_substation_heating'] = Q_substation_heating
        buildings_demands[name]['Q_substation_cooling'] = Q_substation_cooling
        buildings_demands[name]['T_sup_target_DH'] = T_supply_DH
        buildings_demands[name]['T_sup_target_DC'] = T_supply_DC

    return buildings_demands


def substation_HEX_sizing(building_demand, substation_systems):
    """
    This function size the substation heat exchanger area and the UA values.

    :param building_demand: dataframe with building demand properties
    :return: A list of substation heat exchanger properties (Area & UA) for heating, cooling and DHW
    """
    t_DH_supply = building_demand.T_sup_target_DH
    t_DC_supply = building_demand.T_sup_target_DC

    area_columns = []
    UA_columns = []
    for system in substation_systems['heating']:
        area_columns.append('A_hex_hs_'+system)
        UA_columns.append('UA_heating_hs_'+system)

    for system in substation_systems['cooling']:
        area_columns.append('A_hex_cs_'+system)
        UA_columns.append('UA_cooling_cs_'+system)

    #Dataframes for storage
    hex_areas = pd.DataFrame(columns = area_columns, index = ['0'])
    UA_data = pd.DataFrame(columns = UA_columns, index = ['0'])

    ## Heating
    for system in substation_systems['heating']:
        if system == 'ww':
            # calculate HEX area and UA for DHW
            hex_areas.A_hex_hs_ww, UA_data.UA_heating_hs_ww = calc_hex_area_from_demand(building_demand, 'wwf', '',
                                                                                        t_DH_supply)
        else:
            # calculate HEX area and UA for SH ahu, aru, shu
            hex_areas['A_hex_hs_'+system], UA_data['UA_heating_hs_'+system] = calc_hex_area_from_demand(building_demand, 'hsf', system+'_', t_DH_supply)

    ## Cooling
    for system in substation_systems['cooling']:
        if system == 'data':
            # calculate HEX area and UA for the data centers
            hex_areas.A_hex_cs_data, UA_data.UA_cooling_cs_data = calc_hex_area_from_demand(building_demand, 'dataf',
                                                                                            '', t_DC_supply)
        elif system == 'ref':
            # calculate HEX area and UA for cre
            hex_areas.A_hex_cs_ref, UA_data.UA_cooling_cs_ref = calc_hex_area_from_demand(building_demand, 'cref', '',
                                                                                          t_DC_supply)
        else:
            # calculate HEX area and UA for the aru of cooling costumers
            hex_areas['A_hex_cs_'+system], UA_data['UA_cooling_cs_'+system] = calc_hex_area_from_demand(building_demand, 'csf',
                                                                                          system+'_', t_DC_supply)

    return [hex_areas, UA_data]


def calc_hex_area_from_demand(building_demand, type, name, t_supply):
    '''
    This function returns the heat exchanger specifications for given building demand, HEX type and supply temperature.

    :param building_demand: DataFrame with demand values
    :param type: 'csf' or 'hsf' for cooling or heating
    :param name: 'aru', 'ahu', 'scu', 'dataf'
    :param t_supply: Supply temperature
    :return: HEX area and UA
    '''
    # calculate HEX area and UA for customers
    m = 'mcp'+type+'_'+name+'kWperC'
    if type == 'dataf': # necessary because column name for m is "mcpdataf" but for T is "Tcdataf" and Q is "Qcdataf"
        type = 'cdataf'
    Q = 'Q'+type+'_'+name+'kWh'
    T_sup = 'T'+type+'_sup_'+name+'C'
    T_ret = 'T'+type+'_re_'+name+'C'

    Qf = (abs(building_demand[Q].values)) * 1000  # in W
    Qnom = max(Qf)  # in W
    if Qnom > 0:
        tci = t_supply + 273  # in K
        tho = building_demand[T_sup].values + 273  # in K
        thi = building_demand[T_ret].values + 273  # in K
        ch = (abs(building_demand[m].values)) * 1000  # in W/K
        index = np.where(Qf == Qnom)[0][0]
        tci_0 = tci[index]  # in K
        thi_0 = thi[index]
        tho_0 = tho[index]
        ch_0 = ch[index]
        A_hex, UA = calc_cooling_substation_heat_exchange(ch_0, Qnom, thi_0, tci_0, tho_0)
    else:
        A_hex = 0
        UA = 0

    return A_hex, UA


def substation_return_model_main(thermal_network, T_substation_supply, t, consumer_building_names):
    """
    Calculate all substation return temperature and required flow rate at each time-step.

    :param locator: an InputLocator instance set to the scenario to work on
    :param buildings_demands: dictionarz of building demands
    :param substations_HEX_specs: list of dataframes for substation heat exchanger Area and UA for heating, cooling and DHW
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
        mdot_sum_all_kgs[name] = [mcp_sub/(HEAT_CAPACITY_OF_WATER_JPERKGK/1000)]   # [kg/s]
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

    temperatures = []
    mass_flows = []
    heat = []

    # Heating ahu
    if 'UA_heating_hs_ahu' in substation_HEX_specs.HEX_UA.columns:
        Qhsf_ahu, t_DH_return_hs_ahu, mcp_DH_hs_ahu = calc_HEX_heating(building, 'hsf', 'ahu_', T_DH_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_heating_hs_ahu['0'])
        temperatures.append(t_DH_return_hs_ahu)
        mass_flows.append(mcp_DH_hs_ahu)
        heat.append(Qhsf_ahu[0])

    # Heating aru
    if 'UA_heating_hs_aru' in substation_HEX_specs.HEX_UA.columns:
        Qhsf_aru, t_DH_return_hs_aru, mcp_DH_hs_aru = calc_HEX_heating(building, 'hsf', 'aru_', T_DH_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_heating_hs_aru['0'])
        temperatures.append(t_DH_return_hs_aru)
        mass_flows.append(mcp_DH_hs_aru)
        heat.append(Qhsf_aru[0])

    # Heating shu
    if 'UA_heating_hs_shu' in substation_HEX_specs.HEX_UA.columns:
        Qhsf_shu, t_DH_return_hs_shu, mcp_DH_hs_shu = calc_HEX_heating(building, 'hsf', 'shu_', T_DH_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_heating_hs_shu['0'])
        temperatures.append(t_DH_return_hs_shu)
        mass_flows.append(mcp_DH_hs_shu)
        heat.append(Qhsf_shu[0])

    if 'UA_heating_hs_ww' in substation_HEX_specs.HEX_UA.columns:
        Qwwf, t_DH_return_ww, mcp_DH_ww = calc_HEX_heating(building, 'wwf', '', T_DH_supply_K,
                                                       substation_HEX_specs.HEX_UA.UA_heating_hs_ww['0'])
        temperatures.append(t_DH_return_ww)
        mass_flows.append(mcp_DH_ww)
        heat.append(Qwwf[0])

    # calculate mix temperature of return DH
    T_DH_return_K = calc_HEX_mix(heat, temperatures, mass_flows)
    mcp_DH_kWK = sum(mass_flows)  #[kW/K]

    return T_DH_return_K, mcp_DH_kWK


def calc_substation_return_DC(building, T_DC_supply_K, substation_HEX_specs):
    """
    calculate individual substation return temperature and required heat capacity (mcp) of the supply stream
    at each time step.
    :param building: list of building informations
    :param T_DC_supply_K: matrix of the substation supply temperatures in K
    :param substation_HEX_specs: substation heat exchanger properties

    :return t_return_DC: the substation return temperature
    :return mcp_DC: the required heat capacity (mcp) from the DH
    """

    temperatures = []
    mass_flows = []
    heat = []


    # Cooling ahu
    if 'UA_cooling_cs_ahu' in substation_HEX_specs.HEX_UA.columns:
        Qcsf_ahu, t_DC_return_cs_ahu, mcp_DC_hs_ahu = calc_HEX_cooling(building, 'csf', 'ahu_', T_DC_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_cooling_cs_ahu['0'])
        temperatures.append(t_DC_return_cs_ahu)
        mass_flows.append(mcp_DC_hs_ahu)
        heat.append(Qcsf_ahu[0])

    # Cooling aru
    if 'UA_cooling_cs_aru' in substation_HEX_specs.HEX_UA.columns:
        Qcsf_aru, t_DC_return_cs_aru, mcp_DC_hs_aru = calc_HEX_cooling(building, 'csf', 'aru_', T_DC_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_cooling_cs_aru['0'])
        temperatures.append(t_DC_return_cs_aru)
        mass_flows.append(mcp_DC_hs_aru)
        heat.append(Qcsf_aru[0])

    # Cooling scu
    if 'UA_cooling_cs_scu' in substation_HEX_specs.HEX_UA.columns:
        Qcsf_scu, t_DC_return_cs_scu, mcp_DC_hs_scu = calc_HEX_cooling(building, 'csf', 'scu_', T_DC_supply_K,
                                                                   substation_HEX_specs.HEX_UA.UA_cooling_cs_scu['0'])
        temperatures.append(t_DC_return_cs_scu)
        mass_flows.append(mcp_DC_hs_scu)
        heat.append(Qcsf_scu[0])

    if 'UA_cooling_cs_data' in substation_HEX_specs.HEX_UA.columns:
        Qcdataf, t_DC_return_data, mcp_DC_data = calc_HEX_cooling(building, 'dataf', '', T_DC_supply_K,
                                                       substation_HEX_specs.HEX_UA.UA_cooling_cs_data['0'])
        temperatures.append(t_DC_return_data)
        mass_flows.append(mcp_DC_data)
        heat.append(Qcdataf[0])

    if 'UA_cooling_cs_ref' in substation_HEX_specs.HEX_UA.columns:
        Qcref, t_DC_return_ref, mcp_DC_ref = calc_HEX_cooling(building, 'cref', '', T_DC_supply_K,
                                                       substation_HEX_specs.HEX_UA.UA_cooling_cs_ref['0'])
        temperatures.append(t_DC_return_ref)
        mass_flows.append(mcp_DC_ref)
        heat.append(Qcref[0])

    # calculate mix temperature of return DH
    T_DC_return_K = calc_HEX_mix(heat, temperatures, mass_flows)
    mcp_DC_kWK = sum(mass_flows)  #[kW/K]

    return T_DC_return_K, mcp_DC_kWK

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
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom, dTm_0, U_COOL)

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
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom, dTm_0, U_HEAT)
    return Area_HEX_heating, UA_heating


# ============================
# Heat exchanger model
# ============================


def calc_HEX_cooling(building, type, name, tci, UA):
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

    m_name = 'mcp'+type+'_'+name+'kWperC'
    if type == 'dataf': # necessary because column name for m is "mcpdataf" but for T is "Tcdataf" and Q is "Qcdataf"
        type = 'cdataf'
    Q_name = 'Q'+type+'_'+name+'kWh'
    T_sup_name = 'T'+type+'_sup_'+name+'C'
    T_ret_name = 'T'+type+'_re_'+name+'C'

    Q = building[Q_name].values * 1000  # in W
    if abs(Q).max() > 0:
        tho = building[T_sup_name].values + 273  # in K
        thi = building[T_ret_name].values + 273  # in K
        ch = building[m_name].values * 1000  # in W/K
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
            tco = 0.0
            cc = 0.0
        t_return = np.float(tco)
        mcp_return = np.float(cc / 1000)

    else:
        t_return = np.float(tci)
        mcp_return = 0.0

    if np.isnan(t_return):
        t_return = 0.0

    return Q, t_return, mcp_return


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


def calc_HEX_mix(heat, temperatures, mass_flows):
    '''
    This function computes the average  temperature between two vectors of heating demand.
    In this case, domestic hotwater and space heating.

    :param heat: load heating
    :param temperatures: out temperature of heat exchanger for different heating modes
    :param mass_flows: mass flows for each heating mode
    :return:
        tavg: average out temperature.
    '''
    if sum(mass_flows) > 0:
        weighted = [0]*len(heat)
        for g in range(len(heat)):
            if not abs(heat[g]) > 0: #check if we have a heat load
                mass_flows[g] = 0
            weighted[g] = temperatures[g] * mass_flows[g] / sum(mass_flows)
        tavg = sum(weighted)
    else:
        tavg = np.nanmean(temperatures)
    return np.float(tavg)


def calc_HEX_heating(building, type, name, thi, UA):
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
    m_name = 'mcp'+type+'_'+name+'kWperC'
    if type == 'dataf': # necessary because column name for m is "mcpdataf" but for T is "Tcdataf" and Q is "Qcdataf"
        type = 'cdataf'
    Q_name = 'Q'+type+'_'+name+'kWh'
    T_sup_name = 'T'+type+'_sup_'+name+'C'
    T_ret_name = 'T'+type+'_re_'+name+'C'

    Q = building[Q_name].values * 1000  # in W
    if Q.max() > 0:
        tco = building[T_sup_name].values + 273  # in K
        tci = building[T_ret_name].values + 273  # in K
        cc = building[m_name].values * 1000  # in W/K
        if cc.max() > 0:
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
            tho = 0.0
            ch = 0.0
        t_return = np.float(tho)
        mcp_return = np.float(ch / 1000)

    else:
        t_return = np.float(thi)
        mcp_return = 0.0

    if np.isnan(t_return):
        t_return = 0.0
    return Q, t_return, mcp_return


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
def calc_DC_supply(t_0, t_1):
    """
    This function calculates the temperature of the district cooling network according to the minimum observed
    (different to zero) in all buildings connected to the grid.
    :param t_0: last minimum temperature
    :param t_1:  current minimum temperature to evaluate
    :return tmin: new minimum temperature
    """
    a = np.array([t_0, t_1])
    tmin = np.nanmin(a)
    return tmin


def calc_DH_supply(t_0, t_1):
    """
    This function calculates the heating temperature requirement of the building side according to the maximum
    temperature requirement at that time-step.
    :param t_0: temperature requirement from one heating application
    :param t_1: temperature requirement from another heating application
    :return: ``tmax``: maximum temperature requirement
    """
    a = np.array([t_0, t_1])
    tmax = np.nanmax(a)
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

