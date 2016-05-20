# -*- coding: utf-8 -*-


## Name the buildings of your network:

fName = "TH03.csv"
fName2 = "AA16.csv"
fName3 = "AA01.csv"
fName4 = "AA02.csv"
fName5 = "AA03.csv"
fName6 = "AA04.csv"
fName7 = "AA05.csv"
fName8 = "AA06.csv"
fName9 = "AA07.csv"
fName10 = "AA08.csv"
fName11 = "AA09.csv"
fName12 = "AA10.csv"
fName13 = "AA11.csv"
fName14 = "AA12.csv"
fName16 = "AA14.csv"
fName17 = "AA15.csv"
fName18 = "AA17.csv"
fName19 = "DA16.csv"
fName20 = "DA18.csv"
fName21 = "DA19.csv"
fName22 = "DA20.csv"
fName23 = "DA21.csv"
fName24 = "GU22.csv"
fName25 = "LG01.csv"
fName26 = "LG03.csv"
fName27 = "NS02.csv"
fName28 = "TH01.csv"
fName29 = "TH02.csv"
fName30 = "ZW04.csv"
fName31 = "ZW06.csv"
fName32 = "ZW08.csv"
fName33 = "ZW10.csv"
fName34 = "ZW11.csv"
fName35 = "ZW12.csv"
fName36 = "ZW14.csv"
fName37 = "ZW39.csv"

# do by pd.csv_read(..) 

building_list = (fName, fName2, fName3, fName4, fName5,fName6,fName7,fName8,fName9,
                 fName10,fName11,fName12,fName13,fName14,fName16,fName17,fName18,fName19,
                 fName20,fName21,fName22,fName23,fName24,fName25,fName26,fName27,fName28,fName29,
                 fName30,fName31,fName32,fName33,fName34,fName35,fName36,fName37)


import csv
import os
import scipy
from scipy import optimize
from scipy import log
import matplotlib.pyplot as plt
import numpy as np
os.chdir("/Users/Tim/Desktop/ETH/Masterarbeit/Tools/Python_Testcases")
import building_thermal_translator_functions as fn
import pandas as pd
from pickle import Pickler





reload(fn)


''' Global variables '''

hex_type  = "MT" # heat exchanger type
U = 840
CP_WATER = 4185.5 # J/KgK
cp = CP_WATER
T_ground = 10 + 273 # ground temperature, currently not used
HOURS_IN_DAY = 24
DAYS_IN_YEAR = 365

""" find all buildings in the network"""

building_list_dataframe = pd.read_csv("Total.csv", sep=",", usecols=["Name"])
building_list_array_helper = np.array(building_list_dataframe) 
building_list_array = building_list_array_helper[:]


for i in range(len(building_list_array)):
    fName = building_list_array[i,0] + ".csv"
    print "currently working on :", fName
    result_arrays = fn.translator_master(fName, DAYS_IN_YEAR, HOURS_IN_DAY,hex_type, U, building_list)
    mdot_DH_result = result_arrays[0]
    T_return_DH_result = result_arrays[1]
    T_supply_DH_result = result_arrays[2]
    mdot_bld_result = result_arrays[3]
    T_r2_bld_result = result_arrays[4]
    mdot_heating_result = result_arrays[5]
    mdot_dhw_result = result_arrays[6]


    with open(building_list_array[i,0] + "_demand_result.pkl", "wb") as cluster_write:
        cluster_pick = Pickler(cluster_write)

        cluster_pick.dump(mdot_DH_result)
        cluster_pick.dump(T_return_DH_result)
        cluster_pick.dump(T_supply_DH_result)
        cluster_pick.dump(mdot_bld_result)
        cluster_pick.dump(T_r2_bld_result)
        cluster_pick.dump(mdot_heating_result)
        cluster_pick.dump(mdot_dhw_result)
    
    


#result_arrays = fn.translator_master(fName, DAYS_IN_YEAR, HOURS_IN_DAY,hex_type, U, building_list)

#unpack result_arrays
mdot_DH_result = result_arrays[0]
T_return_DH_result = result_arrays[1]
T_supply_DH_result = result_arrays[2]
mdot_bld_result = result_arrays[3]
T_r2_bld_result = result_arrays[4]
mdot_heating_result = result_arrays[5]
mdot_dhw_result = result_arrays[6]

#create load curve

Q_heating_final_load_curve = fn.load_curve(mdot_DH_result)

""" visualize the results """

plt.subplot(3,2,1)
plt.plot(Q_heating_final_load_curve.T)
plt.title("load curve of massflow in DH network")
plt.xlim([0, HOURS_IN_DAY])

plt.subplot(3,2,2)
plt.plot((T_supply_DH_result- 273).T)
plt.title("required supply temperature from DH network")
plt.xlim([0, HOURS_IN_DAY])
plt.ylim([0, np.amax(T_supply_DH_result-273)*1.1])

plt.subplot(3,2,3) 
plt.plot((T_return_DH_result-273).T)
plt.title("return temperature to DH network")
plt.xlim([0, HOURS_IN_DAY])

plt.subplot(3,2,4) 
plt.plot(mdot_DH_result.T)
plt.title("massflow in DH network to building :" + fName)
plt.xlim([0, HOURS_IN_DAY])

plt.subplot(3,2,5)
plt.plot(mdot_heating_result.T)
plt.title("massflow for heating purposes")
plt.xlim([0, HOURS_IN_DAY])

plt.subplot(3,2,6)
plt.plot((T_r2_bld_result-273).T)
plt.title("return temperature of building ciruit")
plt.xlim([0, HOURS_IN_DAY])

# 0, np.amax(Q_heating_final_load_curve)*1.1 ])
plt.show()
