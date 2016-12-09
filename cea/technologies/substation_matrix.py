"""
===============
Substation Model
===============

"""
from __future__ import division
import pandas as pd
import time
import numpy as np
import scipy

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


def substation_HEX_design_main(locator, total_demand, building_names, gv):
    '''
    this function calculates the temperatures and mass flow rates of the district heating network
    at every costumer. Based onthis, the script calculates the hourly temperature of the network at the plant.
    This temperature needs to be equal to that of the customer with the highest temperature requirement plus thermal
    losses in the network.

    :param locator: path to locator function
    :param total_demand: dataframe with total demand and names of all building in the area
    :param building_names:  dataframe with names of all buildings in the area
    :param gv: path to global variables class
    :param Flag: boolean, True if the function is called by the master optimizaiton. False if the fucntion is
    called during preprocessing
    :return:

    '''

    t0 = time.clock()
    # # generate empty vectors
    # Ths = np.zeros(8760)
    # Tww = np.zeros(8760)
    # Tcs = np.zeros(8760) + 1E6
    # Q_all_substations = []

    # determine thermal network target temperatures (T_supply_DH,T_supply_DC) at costumer side.
    iteration = 0
    buildings = []
    Tsupply_all_bui_df = pd.DataFrame()
    Tsupply_bui_df = pd.DataFrame()
    A = []
    for name in building_names:
        buildings.append(pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                     usecols=['Name', 'Thsf_sup_C', 'Thsf_re_C', 'Tcsf_sup_C', 'Tcsf_re_C',
                                              'Twwf_sup_C', 'Twwf_re_C', 'Qhsf_kWh', 'Qcsf_kWh', 'Qwwf_kWh',
                                              'mcphsf_kWC', 'mcpwwf_kWC', 'mcpcsf_kWC', 'Ef_kWh']))
        Q_substation_heating = buildings[iteration].Qhsf_kWh + buildings[iteration].Qwwf_kWh
        T_supply_heating = np.vectorize(calc_DH_supply)(buildings[iteration].Thsf_sup_C.values, buildings[iteration].Twwf_sup_C.values)
        T_supply_cooling = buildings[iteration].Tcsf_sup_C.values
        T_supply_DH = np.where(Q_substation_heating > 0, T_supply_heating + gv.dT_heat, 0)
        T_supply_DC = np.where(abs(buildings[iteration].Qcsf_kWh) > 0, T_supply_cooling - gv.dT_cool, 0)
        buildings[iteration]['T_sup_target_DH'] = T_supply_DH
        buildings[iteration]['T_sup_target_DC'] = T_supply_DC

        # Tsupply_bui_df['T_DH'] = T_supply_DH
        # Tsupply_bui_df['T_DC'] = T_supply_DC
        # Tsupply_bui_df.sort_index(axis=1)
        # Tsupply_bui_df.columns = [['%s'%name, '%s' %name], Tsupply_bui_df.columns]
        # Tsupply_all_bui_df[Tsupply_bui_df.columns]=Tsupply_bui_df.iloc[:]
        # Tsupply_all_bui_df = pd.concat([Tsupply_all_bui_df,Tsupply_bui_df], axis=1)

        # Ths = np.vectorize(calc_DH_supply)(Ths.copy(), buildings[iteration].Thsf_sup_C.values)
        # Tww = np.vectorize(calc_DH_supply)(Tww.copy(), buildings[iteration].Twwf_sup_C.values)
        # Tcs = np.vectorize(calc_DC_supply)(Tcs.copy(), buildings[iteration].Tcsf_sup_C.values)
        #Q_all_substations = calc_total_network_flow(Q_all_substations, buildings[iteration].mcphsf_kWC)
        iteration += 1

    # buildings[0].Qwwf_kWh[0]

    # substation design
    # T_DCS_supply = np.where(Tcs != 1E6, Tcs - gv.dT_cool, 0)
    # T_DHS = np.vectorize(calc_DH_supply)(Ths, Tww)
    # T_DHS_supply = np.where(T_DHS > 0, T_DHS + gv.dT_heat, T_DHS)

    #Q_max_network_flow = max(Q_all_substations)
    #index_max_network_flow =  np.where(Q_all_substations >= Q_max_network_flow)

    # Calculate disconnected buildings files and substation operation.
    index = 0
    combi = [0] * len(building_names)
    substations_HEX_specs = pd.DataFrame(columns=['HEX_area_SH', 'HEX_area_DHW','HEX_area_SC', 'HEX_UA_SH', 'HEX_UA_DHW', 'HEX_UA_SC'])
    for name in building_names:
        print name
        dfRes = total_demand[(total_demand.Name == name)]
        combi[index] = 1
        key = "".join(str(e) for e in combi)
        fName_result = "Total_" + key + ".csv"
        dfRes.to_csv(locator.pathSubsRes + '//' + fName_result, sep=',', float_format='%.3f')
        combi[index] = 0

        # calculate substation parameters (A,UA) per building and store to .csv (target)
        substation_HEX = substation_HEX_sizing(locator, gv, buildings[index])
        # write into dataframe
        substations_HEX_specs.ix[name]= substation_HEX
        index += 1

    print time.clock() - t0, "seconds process time for the Substation Routine \n"
    return substations_HEX_specs, buildings

def substation_HEX_sizing(locator, gv, building):
    '''

    :param locator: path to locator function
    :param gv: path to global variables class
    :param building: dataframe with consumption data per building
    :param t_DH: vector with hourly temperature of the district heating network without losses
    :param t_DH_supply: vector with hourly temperature of the district heating netowork with losses
    :param t_DC_supply: vector with hourly temperature of the district cooling network with losses
    :param t_HS: maximum hourly temperature for all buildings connected due to space heating
    :param t_WW: maximum hourly temperature for all buildings connected due to domestic hot water
    :return:
        Dataframe stored for every building with the mass flow rates and temperatures district heating and cooling
        side in:

        locator.pathSubsRes+'\\'+fName_result.

        where fName_result: ID of the building accounting for the individual at which it belongs to.

    '''
    t_DH_supply = building.T_sup_target_DH
    t_DC_supply = building.T_sup_target_DC

    thi = t_DH_supply + 273  # In K
    Qhsf = building.Qhsf_kWh.values * 1000  # in W
    Qnom = max(Qhsf)  # in W
    if Qnom > 0:
        tco = building.Thsf_sup_C.values + 273  # in K
        tci = building.Thsf_re_C.values + 273  # in K
        cc = building.mcphsf_kWC.values * 1000  # in W/K
        index = np.where(Qhsf == Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        A_hex_hs, UA_heating_hs = calc_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0, gv)
    else:
        A_hex_hs, UA_heating_hs = 0

    # calculate HEX area and UA for DHW
    Qwwf = building.Qwwf_kWh.values * 1000  # in W
    Qnom = max(Qwwf)  # in W
    if Qnom > 0:
        tco = building.Twwf_sup_C.values + 273  # in K
        tci = building.Twwf_re_C.values + 273  # in K
        cc = building.mcpwwf_kWC.values * 1000  # in W/K
        index = np.where(Qwwf == Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        A_hex_ww, UA_heating_ww = calc_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0, gv)
    else:
        A_hex_ww, UA_heating_ww = 0


    # calculate HEX area and UA for cooling costumers incl refrigeration and processes
    Qcf = (abs(building.Qcsf_kWh.values)) * 1000  # in W
    Qnom = max(Qcf)  # in W
    if Qnom > 0:
        tci = t_DC_supply + 273  # in K
        tho = building.Tcsf_sup_C.values + 273  # in K
        thi = building.Tcsf_re_C.values + 273  # in K
        ch = (abs(building.mcpcsf_kWC.values)) * 1000  # in W/K
        index = np.where(Qcf == Qnom)[0][0]
        tci_0 = tci[index]  # in K
        thi_0 = thi[index]
        tho_0 = tho[index]
        ch_0 = ch[index]
        A_hex_cs, UA_cooling_cs = calc_substation_heat_exchange(ch_0, Qnom, thi_0, tci_0, tho_0, gv)
    else:
        A_hex_cs, UA_cooling_cs = 0

    # TODO: write results later
    # # converting units and quantities:
    # T_supply_DH_result_flat = t_DH_supply + 273.0  # convert to K
    # T_supply_DC_result_flat = t_DC_supply + 273.0  # convert to K
    # #  T_return_DH_result_flat = t_DH_return + 273.0  # convert to K
    # # mdot_DH_result_flat = mcp_DH * 1000 / gv.cp  # convert from kW/K to kg/s
    # # mdot_heating_result_flat = mcp_DH_hs * 1000 / gv.cp  # convert from kW/K to kg/s
    # # mdot_dhw_result_flat = mcp_DH_ww * 1000 / gv.cp  # convert from kW/K to kg/s
    # # mdot_cool_result_flat = mcp_DC_cs * 1000 / gv.cp  # convert from kW/K to kg/s
    # # T_r1_dhw_result_flat = t_DH_return_ww + 273.0  # convert to K
    # # T_r1_heating_result_flat = t_DH_return_hs + 273.0  # convert to K
    # # T_r1_cool_result_flat = t_DC_return_cs + 273.0  # convert to K
    # # T_supply_max_all_buildings_flat = t_DH + 273.0  # convert to K
    # # T_hotwater_max_all_buildings_flat = t_WW + 273.0  # convert to K
    # # T_heating_sup_max_all_buildings_flat = t_HS + 273.0  # convert to K
    # Electr_array_all_flat = building.Ef_kWh.values * 1000  # convert to #to W
    #
    # # save the results into a .csv file
    # results = pd.DataFrame({"T_supply_DH_result": T_supply_DH_result_flat,
    #                         "T_supply_DC_result": T_supply_DC_result_flat,
    #                         "A_hex_heating_design": A_hex_hs,
    #                         "A_hex_dhw_design": A_hex_ww,
    #                         "A_hex_cooling_design": A_hex_cs,
    #                         "UA_hex_heating_design": UA_heating_hs,
    #                         "UA_hex_dhw_design": UA_heating_ww,
    #                         "UA_hex_cooling_design": UA_cooling_cs,
    #                         "Q_heating": Qhsf,
    #                         "Q_dhw": Qwwf,
    #                         "Q_cool": Qcf,
    #                         "Electr_array_all_flat": Electr_array_all_flat })
    #                         # "mdot_DH_result": mdot_DH_result_flat,
    #                         # "T_return_DH_result": T_return_DH_result_flat,
    #                         # "mdot_heating_result": mdot_heating_result_flat,
    #                         # "mdot_dhw_result": mdot_dhw_result_flat,
    #                         # "mdot_DC_result": mdot_cool_result_flat,
    #                         # "T_r1_dhw_result": T_r1_dhw_result_flat,
    #                         # "T_r1_heating_result": T_r1_heating_result_flat,
    #                         # "T_return_DC_result": T_r1_cool_result_flat,
    #                         # "T_total_supply_max_all_buildings_intern": T_supply_max_all_buildings_flat,
    #                         # "T_hotwater_max_all_buildings_intern": T_hotwater_max_all_buildings_flat,
    #                         # "T_heating_max_all_buildings_intern": T_heating_sup_max_all_buildings_flat,})
    #
    # fName_result = building.Name.values[0] + "_result.csv"
    # result_substation = locator.pathSubsRes + '\\' + fName_result
    # results.to_csv(result_substation, sep=',', index=False, float_format='%.3f')
    return [A_hex_hs, A_hex_ww, A_hex_cs, UA_heating_hs, UA_heating_ww, UA_cooling_cs]

def substation_return_model_main(locator, building_names, gv, buildings, substations_HEX_specs, T_DH, t):
    """
    calculate all substation return temperature and required flow rate
    :param locator:
    :param building_names:
    :param gv:
    :param buildings:
    :param substation_HEX_specs:
    :param T_DH:
    :param t:
    :return:

    """
    index = 0
    combi = [0] * len(building_names)
    T_DH_return_all = []
    mdot_DH_all = []
    for name in building_names:
        print name
        building = buildings[index]
        building_i = building.loc[[t]]
        t_DH_return, mcp_DH = calc_substation_return_DH(locator, gv, building_i, T_DH, substations_HEX_specs.ix[name])
        T_DH_return_all.append(t_DH_return)
        mdot_DH_all.append(mcp_DH/gv.Cpw)
        # t_DC_return, mcp_DC = calc_substation_return_DC(locator, gv, buildings[index], T_DC, substation_HEX_specs)
        index += 1
    return T_DH_return_all, mdot_DH_all

def calc_substation_return_DH(locator, gv, building, T_DH_supply_matrix, substation_HEX_specs):
    """
    calculate substation return temperature and required flow rate a one time step

    :param locator:
    :param gv:
    :param building:
    :param T_DH_supply_matrix:
    :param substation_HEX_specs:
    :return:
    """
    UA_heating_hs = substation_HEX_specs.HEX_UA_SH
    UA_heating_ww = substation_HEX_specs.HEX_UA_DHW

    thi = T_DH_supply_matrix + 273  # In k  #todo: replace with supply temperature at node
    Qhsf = building.Qhsf_kWh.values * 1000  # in W
    if Qhsf.max > 0:
        tco = building.Thsf_sup_C.values + 273  # in K
        tci = building.Thsf_re_C.values + 273  # in K
        cc = building.mcphsf_kWC.values * 1000  # in W/K
        t_DH_return_hs, mcp_DH_hs = calc_required_flow_and_t_return(Qhsf, UA_heating_hs, thi, tco, tci, cc)
    else:
        t_DH_return_hs = T_DH_supply_matrix
        mcp_DH_hs = 0

    Qwwf = building.Qwwf_kWh.values * 1000  # in W
    if Qwwf.max > 0:
        tco = building.Twwf_sup_C.values + 273  # in K
        tci = building.Twwf_re_C.values + 273  # in K
        cc = building.mcpwwf_kWC.values * 1000  # in W/K
        t_DH_return_ww, mcp_DH_ww = calc_required_flow_and_t_return(Qwwf, UA_heating_ww, thi, tco, tci, cc)
    else:
        t_DH_return_ww = T_DH_supply_matrix
        mcp_DH_ww = 0

    # calculate mix temperature of return DH
    t_DH_return = calc_HEX_mix(Qhsf, Qwwf, t_DH_return_ww, mcp_DH_ww, t_DH_return_hs, mcp_DH_hs)
    mcp_DH = mcp_DH_ww + mcp_DH_hs

    return t_DH_return, mcp_DH

def calc_substation_return_DC(locator, gv, building, T_DC_supply_matrix, substation_HEX_specs):
    UA_heating_cs = substation_HEX_specs

    Qcf = (abs(building.Qcsf_kWh.values)) * 1000  # in W
    if Qcf.max > 0:
        tci = T_DC_supply_matrix + 273  # in K   #todo:replaced with tsupply at each time-step
        tho = building.Tcsf_sup_C.values + 273  # in K
        thi = building.Tcsf_re_C.values + 273  # in K
        ch = (abs(building.mcpcsf_kWC.values)) * 1000  # in W/K
        t_DC_return_cs, mcp_DC_cs = calc_required_flow_and_t_return(Qcf, UA_heating_cs, thi, tho, tci, ch)
    else:
        t_DC_return_cs = T_DC_supply_matrix
        mcp_DC_cs = 0

    return t_DC_return_cs, mcp_DC_cs

def calc_max_network_flowrate(locator, total_demand, building_names, gv):
    for name in building_names:
        print name
        dfRes = total_demand[(total_demand.Name == name)]
        combi[index] = 1
        key = "".join(str(e) for e in combi)
        fName_result = "Total_" + key + ".csv"
        dfRes.to_csv(locator.pathSubsRes + '//' + fName_result, sep=',', float_format='%.3f')
        combi[index] = 0
        # calculate substation parameters per building
        substation_model(locator, gv, buildings[index], T_DHS, T_DHS_supply, T_DCS_supply, Ths, Tww)
        index += 1

# ============================
# substation cooling
# ============================


def calc_substation_cooling(Q, thi, tho, tci, ch, ch_0, Qnom, thi_0, tci_0, tho_0, gv):
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
    :param gv: path to global variables class
    :return:
        tco = out temperature of secondary side (district cooling network)
        cc = capacity mass flow rate secondary side
        Area_HEX_cooling = are of heat excahnger.
    '''

    # nominal conditions network side
    cc_0 = ch_0 * (thi_0 - tho_0) / ((thi_0 - tci_0) * 0.9)
    tco_0 = Qnom / cc_0 + tci_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0, 'cool')
    # Area heat exchange and UA_heating
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom, dTm_0, gv.U_cool)
    tco, cc = np.vectorize(calc_HEX_cooling)(Q, UA_cooling, thi, tho, tci, ch)

    return tco, cc, Area_HEX_cooling


# ============================
# substation heating
# ============================


def calc_substation_heat_exchange(cc_0, Qnom, thi_0, tci_0, tco_0, gv):
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
    :param gv: path to global variables class
    :return:
        tho = out temperature of secondary side (district cooling network)
        ch = capacity mass flow rate secondary side
        Area_HEX_heating = are of heat excahnger.
    '''
    # nominal conditions network side
    ch_0 = cc_0 * (tco_0 - tci_0) / ((thi_0 - tci_0) * 0.9)
    tho_0 = thi_0 - Qnom / ch_0
    dTm_0 = calc_dTm_HEX(thi_0, tho_0, tci_0, tco_0, 'heat')
    # Area heat excahnge and UA_heating
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom, dTm_0, gv.U_heat)
    return Area_HEX_heating, UA_heating

def calc_required_flow_and_t_return(Q, UA_heating, thi, tco, tci, cc):
    tho, ch = calc_HEX_heating(Q, UA_heating, thi, tco, tci, cc)
    return tho, ch

# ============================
# Heat exchanger model
# ============================


def calc_HEX_cooling(Q, UA, thi, tho, tci, ch):
    '''
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
    :return:
        tco: out temperature of secondary side (district cooling network)
        cc: capacity mass flow rate secondary side
    '''

    if ch > 0:
        eff = [0.1, 0]
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
        tco = tco - 273
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
    :param m1: mas flow rate secondary side of heat exchanger for space heating
    :param t2: out temperature of heat exchanger for domestic hot water
    :param m2: mas flow rate secondary side of heat exchanger for domestic hot water
    :return:
        tavg: average out temperature.
    '''
    if Q1 > 0 or Q2 > 0:
        tavg = (t1 * m1 + t2 * m2) / (m1 + m2)
    else:
        tavg = 0
    return np.float(tavg)  #FIXME:change back to float


def calc_HEX_heating(Q, UA, thi, tco, tci, cc):
    '''
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

    :return:
        tho = out temperature of secondary side (district cooling network)
        ch = capacity mass flow rate secondary side
    '''

    if Q > 0:
        eff = [0.1, 0]
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

        tho = tho - 273
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
    '''
    Thi function calculates the area of a het exchanger at nominal conditions.
    :param Qnom: nominal load
    :param dTm_0: nominal logarithmic temperature difference
    :param U: coeffiicent of transmissivity
    :return:
        area: area of heat exchange
        UA: coefficient representing the area of heat exchanger times the coefficient of transmittance of the
    heat exchanger
    '''
    area = Qnom / (dTm_0 * U)  # Qnom in W
    UA = U * area
    return area, UA

# ============================
# Other functions
# ============================
def calc_DC_supply(t_0, t_1):
    '''
    This function calculates the temperature of the district cooling network according to the minimum observed
    (different to zero) in all buildings connected to the grid.
    :param t_0: last minimum temperature
    :param t_1:  current minimum temperature to evaluate
    :return:
        tmin: new minimum temperature
    '''
    if t_0 == 0:
        t_0 = 1E6
    if t_1 > 0:
        tmin = min(t_0, t_1)
    else:
        tmin = t_0
    return tmin


def calc_DH_supply(t_0, t_1):
    '''
    This function calculates the temperature of the district heating network according to the maximum observed
    in all buildings connected to the grid.
    :param t_0: last maximum temperature
    :param t_1: current maximum temperature
    :return:
        tmax: new maximum temperature
    '''
    tmax = max(t_0, t_1)
    return tmax


def calc_total_network_flow(Q_all, flowrate):
    return Q_all + flowrate

# ============================
# Test
# ============================
def run_as_script(scenario_path=None):
    """
    run the whole network summary routine
    """
    import cea.globalvar
    import cea.inputlocator as inputlocator
    from geopandas import GeoDataFrame as gpdf
    from cea.utilities import epwreader
    from cea.resources import geothermal

    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = pd.read_csv(locator.get_total_demand())['Name']
    weather_file = locator.get_default_weather()
    # add geothermal part of preprocessing
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)
    #substation_main(locator, total_demand, total_demand['Name'], gv, False)

    substation_HEX_design_main(locator, total_demand, building_names, gv, Flag = True)

    print 'substation_main() succeeded'

if __name__ == '__main__':
    run_as_script()
















