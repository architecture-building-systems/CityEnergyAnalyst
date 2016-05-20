
from __future__ import division
import pandas as pd
import time
import numpy as np
import substationFn as sfn
import substationModel as sModel
import globalVar as glob
import supportFn as sFn

#reload(sfn)

def calc_DC_supply(t_0,t_1):
    if t_0 == 0:
        t_0 = 1E6
    if t_1 > 0:
        tmin = min(t_0,t_1)  
    else:
        tmin = t_0    
    return tmin

Header = "C:/ArcGIS/ESMdata/DataFinal/MOO/CAMP/"    # path to the input / output folders
data_path = r'C:\ArcGIS\ESMdata\DataFinal\MOO\CAMP\Raw'
total_file = pd.read_csv(data_path+'//'+'Total.csv')

gV = glob.globalVariables()
pathX = sFn.pathX(Header)
gV.Tg = sFn.calc_ground_temperature(pathX.pathRaw, gV)
gV.num_tot_buildings = sFn.calc_num_buildings(pathX.pathRaw, "Total.csv")


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
    buildings.append(pd.read_csv(data_path+'//'+name+".csv",usecols = ['tshs','trhs','tscs','trcs','tsww','trww','Qhsf','Qcsf','Qwwf','mcphs','mcpww','mcpcs','Ealf','Name',
                                    'mcpdata','Ecaf','Qcdataf','Qcicef','Qcpf','mcpice','mcpcp','Eauxf','Epf']))
    t_HS = np.vectorize(sfn.calc_DH_supply)(t_HS.copy(),buildings[iteration].tshs.values)
    t_WW = np.vectorize(sfn.calc_DH_supply)(t_WW.copy(),buildings[iteration].tsww.values)
    t_CS = np.vectorize(calc_DC_supply)(t_CS.copy(),buildings[iteration].tscs.values)
    iteration +=1
t_DH = np.vectorize(sfn.calc_DH_supply)(t_HS,t_WW)
t_DH_supply = np.where(t_DH>0,t_DH+gV.dT_heat,t_DH)
t_DC_supply = np.where(t_CS!=1E6,t_CS-gV.dT_cool,0)

