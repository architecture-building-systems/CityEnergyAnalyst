
""" 

Network Summary:
    this file summarizes the network demands and will give them as:
        - absolute values (design values = extreme values)
        - hourly operation scheme of input/output of network
By J. Fonseca, based on T2           
"""
from __future__ import division
import time
import numpy as np
import pandas as pd
import summarize_network_functions as fn
import math

def Network_Summary(data_path, path_to_path, substation_results_path, results_path, path_pipes, TotalNamefile, gv):
    t0 = time.clock()
    # import total file names
    total_file = pd.read_csv(path_to_path+'//'+TotalNamefile)
    names = total_file.Name.values
    
    # import properties of network
    num_buildings_network = total_file.Name.count()
    pipes_tot_length = pd.read_csv(path_pipes+'//'+"PipesData_DH.csv", usecols = ['LENGTH'])
    ntwk_length = pipes_tot_length.sum()*num_buildings_network/gv.num_tot_buildings
    
    # empty vectors
    buildings = []
    substations = []
    Qcdata_netw_total = np.zeros(8760)
    mdotdata_netw_total = np.zeros(8760)
    Ecaf_netw_total =  np.zeros(8760)
    Electr_netw_total = np.zeros(8760)
    mdot_heat_netw_all = np.zeros(8760)
    mdot_cool_netw_all = np.zeros(8760)
    Q_DH_building_netw_total =  np.zeros(8760)
    Q_DC_building_netw_total = np.zeros(8760)
    sum_tret_mdot_heat = np.zeros(8760)
    sum_tret_mdot_cool = np.zeros(8760)
    mdot_heat_netw_min = np.zeros(8760)+1E6
    mdot_cool_netw_min = np.zeros(8760)+1E6
    iteration = 0
    for name in names:
        buildings.append(pd.read_csv(data_path+'//'+name+".csv",usecols = ['mcpdata','Ecaf','Qcdataf']))
        substations.append(pd.read_csv(substation_results_path+'//'+name+'_result'+".csv",usecols = ['Electr_array_all_flat','mdot_DH_result','mdot_DC_result','Q_heating','Q_dhw','Q_cool',
                                        'T_return_DH_result','T_return_DC_result','T_supply_DH_result']))

        Qcdata_netw_total += buildings[iteration].Qcdataf.values
        mdotdata_netw_total += buildings[iteration].mcpdata.values
        Ecaf_netw_total += buildings[iteration].Ecaf.values
        Electr_netw_total += substations[iteration].Electr_array_all_flat.values
        mdot_heat_netw_all += substations[iteration].mdot_DH_result.values
        mdot_cool_netw_all += substations[iteration].mdot_DC_result.values
        Q_DH_building_netw_total += (substations[iteration].Q_heating.values + substations[iteration].Q_dhw.values)
        Q_DC_building_netw_total += (substations[iteration].Q_cool.values)
        sum_tret_mdot_heat += substations[iteration].T_return_DH_result.values*substations[iteration].mdot_DH_result.values
        sum_tret_mdot_cool += substations[iteration].T_return_DC_result.values*substations[iteration].mdot_DC_result.values
        
        # evaluate minimum flows
        mdot_heat_netw_min = np.vectorize(calc_min_flow)(mdot_heat_netw_min,substations[iteration].mdot_DH_result.values)
        mdot_cool_netw_min = np.vectorize(calc_min_flow)(mdot_cool_netw_min,substations[iteration].mdot_DC_result.values)
        iteration +=1
    
    #calculate thermal losses of network
    T_sst_heat_return_netw_total = np.vectorize(calc_return_temp)(sum_tret_mdot_heat, mdot_heat_netw_all)
    T_sst_heat_supply_netw_total = np.vectorize(calc_supply_temp)(T_sst_heat_return_netw_total, Q_DH_building_netw_total, mdot_heat_netw_all, gv.cp, "DH") 
    
    T_sst_cool_return_netw_total = np.vectorize(calc_return_temp)(sum_tret_mdot_cool, mdot_cool_netw_all)
    T_sst_cool_supply_netw_total = np.vectorize(calc_supply_temp)(T_sst_cool_return_netw_total, Q_DC_building_netw_total, mdot_cool_netw_all, gv.cp, "DC")
       
    Q_DH_losses_supply = np.vectorize(calc_piping_thermal_losses)(T_sst_heat_supply_netw_total, mdot_heat_netw_all, mdot_heat_netw_min, ntwk_length, gv.Tg, gv.K_DH, gv.cp)
    Q_DH_losses_return = np.vectorize(calc_piping_thermal_losses)(T_sst_heat_return_netw_total, mdot_heat_netw_all, mdot_heat_netw_min, ntwk_length, gv.Tg, gv.K_DH, gv.cp)
    Q_DH_losses = Q_DH_losses_supply + Q_DH_losses_return
    Q_DH_building_netw_total_inclLosses = Q_DH_building_netw_total + Q_DH_losses

    print mdot_cool_netw_min
    Q_DC_losses_supply = np.vectorize(calc_piping_thermal_losses)(T_sst_cool_supply_netw_total, mdot_cool_netw_all, mdot_cool_netw_min, ntwk_length, gv.Tg, gv.K_DH, gv.cp)
    Q_DC_losses_return = np.vectorize(calc_piping_thermal_losses)(T_sst_heat_return_netw_total, mdot_cool_netw_all, mdot_cool_netw_min, ntwk_length, gv.Tg, gv.K_DH, gv.cp)
    Q_DC_losses = Q_DC_losses_supply + Q_DC_losses_return
    Q_DC_building_netw_total_inclLosses = Q_DC_building_netw_total + Q_DC_losses

    T_sst_heat_return_netw_total_inclLosses = np.vectorize(calc_temp_withlosses)(T_sst_heat_return_netw_total, Q_DH_losses_return, mdot_heat_netw_all, gv.cp, "negative")
    T_sst_heat_supply_netw_total_inclLosses = np.vectorize(calc_temp_withlosses)(T_sst_heat_supply_netw_total, Q_DH_losses_supply,mdot_heat_netw_all, gv.cp, "positive")

    T_sst_cool_return_netw_total_inclLosses = np.vectorize(calc_temp_withlosses)(T_sst_cool_return_netw_total, Q_DC_losses_return, mdot_cool_netw_all, gv.cp, "positive")
    T_sst_cool_supply_netw_total_inclLosses = np.vectorize(calc_temp_withlosses)(T_sst_cool_supply_netw_total, Q_DC_losses_supply, mdot_cool_netw_all, gv.cp, "negative")

    day_of_max_heatmassflow_fin = np.zeros(8760)
    day_of_max_heatmassflow = fn.find_index_of_max(mdot_heat_netw_all)
    day_of_max_heatmassflow_fin[:] = day_of_max_heatmassflow

    results = pd.DataFrame({"mdot_DH_netw_total":mdot_heat_netw_all,
                            "mdot_cool_netw_total":mdot_cool_netw_all,
                            "Q_DH_building_netw_total":Q_DH_building_netw_total_inclLosses,
                            "Q_DC_building_netw_total":Q_DC_building_netw_total_inclLosses,
                            "T_sst_heat_return_netw_total":T_sst_heat_return_netw_total_inclLosses,
                            "T_sst_cool_return_netw_total":T_sst_cool_return_netw_total_inclLosses,
                            "T_sst_heat_supply_netw_total":T_sst_heat_supply_netw_total_inclLosses,
                            "T_sst_cool_supply_netw_total":T_sst_cool_supply_netw_total_inclLosses,
                            "Qcdata_netw_total":Qcdata_netw_total,
                            "Ecaf_netw_total":Ecaf_netw_total,
                            "day_of_max_heatmassflow":day_of_max_heatmassflow,
                            "mdotdata_netw_total":mdotdata_netw_total,
                            "Electr_netw_total":Electr_netw_total,
                            "Q_DH_losses":Q_DH_losses,
                            "Q_DC_losses":Q_DC_losses})
    
    temp = TotalNamefile.replace("Total", "")
    key = temp.replace(".csv", "")
    
    if key == "":
        key = "_all"    
    fName_result = "Network_summary_result" + key + ".csv"    
    results.to_csv(results_path+'//'+fName_result, sep= ',')
    
    print "Results saved in :", results_path
    
    print time.clock() - t0, "seconds process time for Network summary for configuration", key, "\n"
    

def calc_return_temp(sum_t_m, sum_m):
    if sum_m >0:
        tr = sum_t_m/sum_m
    else:
        tr = 0
    return tr

def calc_temp_withlosses(t0,Q,m,cp, case):
    if m > 0:
        if case == "positive":
            t1 = t0 + Q/(m*cp)
        else:
            t1 = t0 - Q/(m*cp) 
    else:
        t1 = 0
    return t1

def calc_supply_temp(tr,Q,m,cp, case):
    if m > 0:
        if case == "DH":
            ts = tr + Q/(m*cp)
        else:
            ts = tr - Q/(m*cp) 
    else:
        ts = 0
    return ts

def calc_piping_thermal_losses(Tnet, mmax, mmin, L, Tg, K, cp):
    if mmin != 1E6: # control variable see function fn.calc_min_flow
        mavg = (mmax+mmin)/2
        Tx = Tg+(Tnet-Tg)*math.exp(-K*L/(mavg*cp))
        Qloss = (Tnet-Tx)*mavg*cp
    else:
        Qloss = 0
    return Qloss

def calc_min_flow(m0,m1):
    if m0 ==0:
        m0 = 1E6
    if m1>0:
        mmin = min(m0,m1)
    else:
        mmin = m0
    return mmin