"""
===============
Substation Main
===============

"""
from __future__ import division
import pandas as pd
import time
import numpy as np
import substationFn as sfn
import substationModel as sModel

def subsMain(data_path, path_to_path, results_path, TotalNamefile, disconected_buildings, gv):
    t0 = time.clock()
    # import total file data
    total_file = pd.read_csv(path_to_path+'//'+TotalNamefile)
    # generate list of names
    names = total_file.Name.values
    # generate empty vectors
    t_HS = np.zeros(8760)
    t_WW = np.zeros(8760)
    t_DC = np.zeros(8760)
    t_DH = np.zeros(8760)
    t_CS = np.zeros(8760)+1E6
    buildings = []
    # determine grid target temperatures at costumer side.
    iteration = 0
    for name in names:
        print name
        buildings.append(pd.read_csv(data_path+'//'+name+".csv",usecols = ['tshs','trhs','tscs','trcs','tsww','trww','Qhsf','Qcsf','Qwwf','mcphs','mcpww','mcpcs','Ealf','Name',
                                        'mcpdata','Ecaf','Qcdataf','Qcicef','Qcpf','mcpice','mcpcp','Eauxf','Epf']))
        t_HS = np.vectorize(calc_DH_supply)(t_HS.copy(),buildings[iteration].tshs.values)
        t_WW = np.vectorize(calc_DH_supply)(t_WW.copy(),buildings[iteration].tsww.values)
        t_CS = np.vectorize(calc_DC_supply)(t_CS.copy(),buildings[iteration].tscs.values)
        iteration +=1
    t_DH = np.vectorize(calc_DH_supply)(t_HS,t_WW)
    t_DH_supply = np.where(t_DH>0,t_DH+gv.dT_heat,t_DH)
    t_DC_supply = np.where(t_CS!=1E6,t_CS-gv.dT_cool,0)
    # Calculate disconnected buildings files and substation operation.
    if disconected_buildings == 1:
        index = 0
        combi = [0]*len(names)
        for name in names:
            print name
            # calculate file for disconnected building buildings
            dfTemp = total_file[(total_file.Name == name)]
            dfRes = dfTemp.drop(['Unnamed: 0'], axis =1 )
            combi[index] = 1
            key = "".join(str(e) for e in combi)
            fName_result = "Total_" + key + ".csv"
            dfRes.to_csv(results_path+'//'+fName_result, sep= ',')
            combi[index] = 0
            # calculate substation parameters per building
            sModel.subsModel(path_to_path, results_path, gv, buildings[index],t_DH,t_DH_supply,t_DC_supply,t_HS,t_WW,t_CS)
            index +=1
    else:
        index = 0
        # calculate substation parameters per building
        for name in names:
            sModel.subsModel(path_to_path, results_path, gv, buildings[index],t_DH,t_DH_supply,t_DC_supply,t_HS,t_WW,t_CS)
            index +=1
    print time.clock() - t0, "seconds process time for the Substation Routine \n"


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
