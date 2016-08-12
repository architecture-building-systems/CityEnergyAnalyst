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

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Tim Vollrath", "Thuy-An Nguyen"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""

============================
substation model
============================

"""

def subsMain(locator, total_file, building_names, gv, Flag):
    """
    this calculates the temperatures and mass flow rates of the network (plant side)
    at every customer. the temperature of operation of the network will be that required by the
    customer with the highest temperature. This temperature will be updated to account for thermal losses.
    these thermal losses are case specific and depend on the network configuration.

    :param data_path:
    :param results_path:
    :param total_demand_file:
    :param Flag:
    :param gv:
    :return:
    """
    t0 = time.clock()
    # generate empty vectors
    Ths = np.zeros(8760)
    Tww = np.zeros(8760)
    Tcs = np.zeros(8760)+1E6

    # determine grid target temperatures at costumer side.
    iteration = 0
    buildings = []
    for name in building_names:
        buildings.append(pd.read_csv(locator.get_demand_results_folder()+'//'+name+".csv", usecols = ['Name','Tshs_C','Trhs_C','Tscs_C','Trcs_C','Tsww_C',
                                                                            'Trww_C','Qhsf_kWh','Qcsf_kWh','Qwwf_kWh',
                                                                            'mcphs_kWC','mcpww_kWC','mcpcs_kWC',
                                                                            'Ef_kWh']))
        Ths = np.vectorize(calc_DH_supply)(Ths.copy(),buildings[iteration].Tshs_C.values)
        Tww = np.vectorize(calc_DH_supply)(Tww.copy(),buildings[iteration].Tsww_C.values)
        Tcs = np.vectorize(calc_DC_supply)(Tcs.copy(),buildings[iteration].Tscs_C.values)
        iteration +=1
    T_DHS = np.vectorize(calc_DH_supply)(Ths,Tww)
    T_DHS_supply = np.where(T_DHS>0,T_DHS+gv.dT_heat,T_DHS)
    t_DCS_supply = np.where(Tcs!=1E6,Tcs-gv.dT_cool,0)

    # Calculate disconnected buildings files and substation operation.
    index = 0
    if Flag:
        combi = [0]*len(building_names)
        for name in building_names:
            dfRes = total_file[(total_file.Name == name)]
            combi[index] = 1
            key = "".join(str(e) for e in combi)
            fName_result = "Total_" + key + ".csv"
            dfRes.to_csv(locator.pathSubsRes+'//'+fName_result, sep= ',', index=False, float_format='%.3f')
            # calculate substation parameters per building
            subsModel(locator, gv, buildings[index],T_DHS,T_DHS_supply,t_DCS_supply,Ths,Tww)
            index +=1
    else:
        # calculate substation parameters per building
        for name in building_names:
            subsModel(locator, gv, buildings[index],T_DHS,T_DHS_supply,t_DCS_supply,Ths,Tww)
            index += 1
    print time.clock() - t0, "seconds process time for the Substation Routine \n"


def subsModel(locator, gv, building, t_DH, t_DH_supply, t_DC_supply, t_HS, t_WW):

    #calculate temperatures and massflow rates HEX for space heating costumers.
    thi = t_DH_supply + 273 # In k
    Qhsf = building.Qhsf_kWh.values*1000 # in W
    Qnom = max(Qhsf) #in W
    if Qnom> 0:
        tco = building.Tshs_C.values+273 #in K
        tci = building.Trhs_C.values+273 #in K
        cc = building.mcphs_kWC.values*1000 #in W/K
        index = np.where(Qhsf==Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_hs, mcp_DH_hs, A_hex_hs = \
        calc_substation_heating(Qhsf,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv)
    else:
        t_DH_return_hs = np.zeros(8760)
        mcp_DH_hs = np.zeros(8760)
        A_hex_hs = 0
    #calculate temperatures and massflow rates HEX for dhW costumers.
    Qwwf = building.Qwwf_kWh.values*1000  # in W
    Qnom = max(Qwwf) #in W
    if Qnom> 0:
        tco = building.Tsww_C.values+273  #in K
        tci = building.Trww_C.values+273  #in K
        cc = building.mcpww_kWC.values*1000  #in W/K
        index = np.where(Qwwf==Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_ww, mcp_DH_ww,A_hex_ww = \
        calc_substation_heating(Qwwf,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv)
    else:
        t_DH_return_ww = np.zeros(8760)
        A_hex_ww = 0
        mcp_DH_ww = np.zeros(8760)

    #calculate mix temperature of return DH
    t_DH_return = np.vectorize(calc_HEX_mix)(Qhsf,Qwwf,t_DH_return_ww, mcp_DH_ww,t_DH_return_hs, mcp_DH_hs)
    mcp_DH = (mcp_DH_ww + mcp_DH_hs)
    #calculate temperatures and massflow rates HEX for cooling costumers incl refrigeration and processes
    Qcf = (abs(building.Qcsf_kWh.values))*1000  # in W
    Qnom = max(Qcf) #in W
    if Qnom> 0:
        tci = t_DC_supply+273 # in K
        tho = building.Tscs_C.values+273 #in K
        thi = building.Trcs_C.values+273 #in K
        ch = (abs(building.mcpcs_kWC.values))*1000 #in W/K
        index = np.where(Qcf==Qnom)[0][0]
        tci_0 = tci[index] # in K
        thi_0 = thi[index]
        tho_0 = tho[index]
        ch_0 = ch[index]
        t_DC_return_cs, mcp_DC_cs,A_hex_cs = \
        calc_substation_cooling(Qcf,thi,tho,tci,ch,ch_0,Qnom,thi_0,tci_0,tho_0,gv)
    else:
        t_DC_return_cs = t_DC_supply
        mcp_DC_cs = 0
        A_hex_cs = 0

    # converting units and quantities:
    T_return_DH_result_flat = t_DH_return+273 #convert to K
    T_supply_DH_result_flat = t_DH_supply+273 #convert to K
    mdot_DH_result_flat = mcp_DH*1000/gv.cp #convert from kW/K to kg/s
    mdot_heating_result_flat = mcp_DH_hs*1000/gv.cp #convert from kW/K to kg/s
    mdot_dhw_result_flat =  mcp_DH_ww*1000/gv.cp #convert from kW/K to kg/s
    mdot_cool_result_flat = mcp_DC_cs*1000/gv.cp #convert from kW/K to kg/s
    T_r1_dhw_result_flat = t_DH_return_ww+273 #convert to K
    T_r1_heating_result_flat = t_DH_return_hs+273 #convert to K
    T_r1_cool_result_flat = t_DC_return_cs+273 #convert to K
    T_supply_DC_result_flat = t_DC_supply+273 #convert to K
    T_supply_max_all_buildings_flat = t_DH+273 #convert to K
    T_hotwater_max_all_buildings_flat = t_WW+273 #convert to K
    T_heating_sup_max_all_buildings_flat = t_HS+273 #convert to K
    Electr_array_all_flat = building.Ef_kWh.values*1000 #convert to #to W

    # save the results into a .csv file
    results = pd.DataFrame({"mdot_DH_result":mdot_DH_result_flat,
                            "T_return_DH_result":T_return_DH_result_flat,
                            "T_supply_DH_result":T_supply_DH_result_flat,
                            "mdot_heating_result":mdot_heating_result_flat,
                            "mdot_dhw_result":mdot_dhw_result_flat,
                            "mdot_DC_result":mdot_cool_result_flat,
                            "T_r1_dhw_result":T_r1_dhw_result_flat,
                            "T_r1_heating_result":T_r1_heating_result_flat,
                            "T_return_DC_result":T_r1_cool_result_flat,
                            "T_supply_DC_result":T_supply_DC_result_flat,
                            "A_hex_heating_design":A_hex_hs,
                            "A_hex_dhw_design":A_hex_ww,
                            "A_hex_cool_design":A_hex_cs,
                            "Q_heating":Qhsf,
                            "Q_dhw":Qwwf,
                            "Q_cool":Qcf,
                            "T_total_supply_max_all_buildings_intern":T_supply_max_all_buildings_flat,
                            "T_hotwater_max_all_buildings_intern":T_hotwater_max_all_buildings_flat,
                            "T_heating_max_all_buildings_intern":T_heating_sup_max_all_buildings_flat,
                            "Electr_array_all_flat":Electr_array_all_flat})

    fName_result = building.Name.values[0]+"_result.csv"
    result_substation = locator.pathSubsRes+'\\'+fName_result
    results.to_csv(result_substation, sep= ',', index=False, float_format='%.3f')
    return results


"""

============================
substation cooling
============================

"""
def calc_substation_cooling(Q, thi, tho, tci, ch, ch_0, Qnom, thi_0, tci_0, tho_0,gv):

    #nominal conditions network side
    cc_0 = ch_0*(thi_0-tho_0)/((thi_0-tci_0)*0.9)
    tco_0 = Qnom/cc_0+tci_0
    dTm_0 = calc_dTm_HEX(thi_0,tho_0,tci_0,tco_0,'cool')
    #Area heat exchange and UA_heating
    Area_HEX_cooling, UA_cooling = calc_area_HEX(Qnom,dTm_0,gv.U_cool)
    tco, cc = np.vectorize(calc_HEX_cooling)(Q, UA_cooling, thi, tho, tci, ch)

    return tco, cc, Area_HEX_cooling

"""

============================
substation heating
============================

"""

def calc_substation_heating(Q,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv):
    #nominal conditions network side
    ch_0 = cc_0*(tco_0-tci_0)/((thi_0-tci_0)*0.9)
    tho_0 = thi_0-Qnom/ch_0
    dTm_0 = calc_dTm_HEX(thi_0,tho_0,tci_0,tco_0,'heat')
    #Area heat excahnge and UA_heating
    Area_HEX_heating, UA_heating = calc_area_HEX(Qnom,dTm_0,gv.U_heat)
    tho, ch = np.vectorize(calc_HEX_heating)(Q, UA_heating,thi,tco,tci,cc)
    return tho, ch, Area_HEX_heating


"""

============================
Heat exchanger model
============================

"""

def calc_HEX_cooling(Q, UA,thi,tho,tci,ch):

    def calc_plate_HEX(NTU, cr):
        eff = 1 - scipy.exp((1 / cr) * (NTU ** 0.22) * (scipy.exp(-cr * (NTU) ** 0.78) - 1))
        return eff
    if ch>0:
        eff = [0.1,0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0]-eff[1])/eff[0])>tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = ch*(thi-tho)/((thi-tci)*eff[0])
            if cmin < ch:
                cc = cmin
                cmax = ch
            else:
                cc = cmin
                cmax = cc
                cmin = ch
            cr =  cmin/cmax
            NTU = UA/cmin
            eff[1] =  calc_plate_HEX(NTU,cr)
            cmin = ch*(thi-tho)/((thi-tci)*eff[1])
            tco = tci+eff[1]*cmin*(thi-tci)/cc
            Flag = True
        cc = Q/abs(tci-tco)
        tco = tco-273
    else:
        tco = 0
        cc = 0
    return tco, cc/1000

def calc_HEX_mix(Q1,Q2, t1,m1,t2, m2):
    if Q1 >0 or Q2>0:
        tavg = (t1*m1+t2*m2)/(m1+m2)
    else:
        tavg = 0
    return tavg

def calc_HEX_heating(Q, UA,thi,tco,tci,cc):
    def calc_shell_HEX(NTU, cr):
        eff = 2 * ((1 + cr + (1 + cr ** 2) ** (1 / 2)) * (
        (1 + scipy.exp(-(NTU) * (1 + cr ** 2))) / (1 - scipy.exp(-(NTU) * (1 + cr ** 2))))) ** -1
        return eff
    if Q>0:
        eff = [0.1,0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0]-eff[1])/eff[0])>tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = cc*(tco-tci)/((thi-tci)*eff[0])
            if cmin < cc:
                ch = cmin
                cmax = cc
            else:
                ch = cmin
                cmax = cmin
                cmin = cc
            cr =  cmin/cmax
            NTU = UA/cmin
            eff[1] =  calc_shell_HEX(NTU,cr)
            cmin = cc*(tco-tci)/((thi-tci)*eff[1])
            tho = thi-eff[1]*cmin*(thi-tci)/ch
            Flag = True

        tho = tho-273
    else:
        tho = 0
        ch = 0
    return tho, ch/1000

def calc_dTm_HEX(thi,tho,tci,tco, flag):
    dT1 = thi-tco
    dT2 = tho-tci
    if flag == 'heat':
        dTm = (dT1-dT2)/scipy.log(dT1/dT2)
    else:
        dTm = (dT2-dT1)/scipy.log(dT2/dT1)
    return abs(dTm.real)

def calc_area_HEX(Qnom,dTm_0, U):
    area = Qnom/(dTm_0*U) #Qnom in W
    UA = U*area
    return area, UA

def calc_DC_supply(t_0,t_1):
    if t_0 == 0:
        t_0 = 1E6
    if t_1 > 0:
        tmin = min(t_0,t_1)  
    else:
        tmin = t_0    
    return tmin


def calc_DH_supply(t_0,t_1):
    tmax = max(t_0,t_1)
    return tmax
