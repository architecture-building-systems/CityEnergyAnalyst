"""
====================================
Operation for disconnected buildings
====================================

"""
from __future__ import division
import os
import pandas as pd
import numpy as np


pathcluster = "C:/Users/Thuy-An/Documents/GitHub/urben/Masterarbeit/Clustering"
os.chdir(pathcluster)

import clusterMain as cM
reload (cM)

pathmodules = "C:/Users/Thuy-An/Documents/GitHub/urben/Masterarbeit/EnergySystem_Models/"
os.chdir(pathmodules)


import Model_Boiler_condensing as Boiler
import Model_FuelCell_V2 as FC
import Model_HP as HP
reload(Boiler)
reload(FC)
reload(HP)

pathdata = "C:/Users/Thuy-An/Documents/ETH/Arch Master Thesis/Python results/EA extract"
os.chdir(pathdata)


##################################
# For one building, heating demand
##################################

buildName = "TH01_result.csv"
margin = 0.1


##############################
# Extract and cluster the data
##############################

TsupHeat = np.array( pd.read_csv( buildName, usecols=["T_supply_DH_result"], nrows=1 ) ) [0][0]
(fileList, clusterDayRes, occListDay) = cM.clusterMain(pathdata, pathdata, fNameList = [buildName], featureList = ["mdot_DH_result","T_return_DH_result"])






#Q_load = 100E3
#Q_design = 150E3
#T_return_to_boiler = 273 + 40
#eff = Boiler.Cond_Boiler_operation(Q_load, Q_design, T_return_to_boiler)

