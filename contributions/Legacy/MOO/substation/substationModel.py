"""
============================
substation model
============================
by J. Fonseca
"""

from __future__ import division
from math import exp, log
import pandas as pd
import numpy as np
import substationFn as sfn
import os

def subsModel(data_path,results_path, gv, building,t_DH,t_DH_supply,t_DC_supply,t_HS,t_WW,t_CS):
      
    #calculate temperatures and massflow rates HEX for space heating costumers.
    thi = t_DH_supply + 273 # In k
    Qhsf = building.Qhsf.values*1000 # in W
    Qnom = max(Qhsf) #in W  
    if Qnom> 0:
        tco = building.tshs.values+273 #in K
        tci = building.trhs.values+273 #in K
        cc = building.mcphs.values*1000 #in W/K
        index = np.where(Qhsf==Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_hs, mcp_DH_hs, A_hex_hs = \
        sfn.calc_substation_heating(Qhsf,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv)
    else:
        t_DH_return_hs = np.zeros(8760)
        mcp_DH_hs = np.zeros(8760)
        A_hex_hs = 0
        
    #calculate temperatures and massflow rates HEX for dhW costumers. 
    Qwwf = building.Qwwf.values*1000  # in W
    Qnom = max(Qwwf) #in W
    if Qnom> 0:
        tco = building.tsww.values+273  #in K
        tci = building.trww.values+273  #in K
        cc = building.mcpww.values*1000  #in W/K
        index = np.where(Qwwf==Qnom)[0][0]
        thi_0 = thi[index]
        tci_0 = tci[index]
        tco_0 = tco[index]
        cc_0 = cc[index]
        t_DH_return_ww, mcp_DH_ww,A_hex_ww = \
        sfn.calc_substation_heating(Qwwf,thi,tco,tci,cc,cc_0,Qnom,thi_0,tci_0,tco_0,gv)
    else:
        t_DH_return_ww = np.zeros(8760)
        A_hex_ww = 0
        mcp_DH_ww = np.zeros(8760)

    #calculate mix temperature of return DH
    t_DH_return = np.vectorize(sfn.calc_HEX_mix)(Qhsf,Qwwf,t_DH_return_ww, mcp_DH_ww,t_DH_return_hs, mcp_DH_hs)
    mcp_DH = (mcp_DH_ww + mcp_DH_hs)
    
    #calculate temperatures and massflow rates HEX for cooling costumers incl refrigeration and processes
    Qcf = (abs(building.Qcsf.values))*1000  # in W
    Qnom = max(Qcf) #in W
    if Qnom> 0:
        tci = t_DC_supply+273 # in K
        tho = building.tscs.values+273 #in K
        thi = building.trcs.values+273 #in K
        ch = (abs(building.mcpcs.values))*1000 #in W/K
        index = np.where(Qcf==Qnom)[0][0]
        tci_0 = tci[index] # in K
        thi_0 = thi[index]
        tho_0 = tho[index]
        ch_0 = ch[index]
        t_DC_return_cs, mcp_DC_cs,A_hex_cs = \
        sfn.calc_substation_cooling(Qcf,thi,tho,tci,ch,ch_0,Qnom,thi_0,tci_0,tho_0,gv)
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
    Electr_array_all_flat = (building.Ealf.values+building.Eauxf.values+building.Epf.values)*1000 #convert to #to W

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
    result_substation = results_path+'\\'+fName_result
    results.to_csv(result_substation, sep= ',')
    
    print "Results saved in :", results_path
    print "Substation model complete \n"
    return results