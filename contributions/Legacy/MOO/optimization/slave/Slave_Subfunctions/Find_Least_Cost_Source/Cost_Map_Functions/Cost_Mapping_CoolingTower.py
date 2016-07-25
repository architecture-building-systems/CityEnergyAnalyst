"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant

WORK IN PROCESS 

"""


######################
#WARNING : TO BE DONE
#########################






# Mapping CC Cost


#Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
#M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Trials"

#import os
import numpy as np
#os.chdir(Energy_Models_path)
import EnergySystem_Models.Model_VCC as MVCC
import EnergySystem_Models.Model_CT as MCT
import globalVar as gV

#os.chdir(M_to_S_Var_path)
#import Master_to_Slave_Variables as MS_Var
#reload(MS_Var)
#os.chdir(Energy_Models_path)


#import MasterToSlaveVariables
##reload(MasterToSlaveVariables)
#context = MasterToSlaveVariables.MasterSlaveVariables()
#MS_Var = context

#reload (gV)
reload (MVCC)
reload (MCT)

#TO BE ITERATED!



# TRY 2 - iterating and mapping the thermal output

it_len = 50


import matplotlib.pyplot as plt


mdot_min =0.3
mdot_max = 0.6

tret_min = 1 + 273.0
tret_max = 10 + 273.0

mdot_range = np.linspace(mdot_min, mdot_max, it_len)
tret_range = np.linspace(tret_min, tret_max, it_len)

wdotfin = np.zeros( (it_len, it_len) )
qdot = np.zeros( (it_len, it_len) )
eta_elec = np.zeros( (it_len, it_len) )
cost_per_kWh_th = np.zeros( (it_len, it_len) )
total_cost_per_kWh_th = np.zeros( (it_len, it_len) )

tsup = 4.1 + 273.0 # K
Qdesign = MS_Var.CT_Qdesign

i = 0
for mdot_it in range(len(mdot_range)):
    mdot_in = mdot_range[mdot_it]
    
    for tret_it in range(len(tret_range)):
        tret_in = tret_range[tret_it]
        wdot1, qhotdot = MVCC.VCC_Op(mdot_in, tsup, tret_in)
        wdot2 = MCT.CT_Op(qhotdot, Qdesign)
        if tret_in >= tsup:
            Qnetw = 0.0
            
        else:
            Qnetw = mdot_in * gV.cp * (tsup-tret_in)
        
        
        wdotfin[mdot_it, tret_it] = wdot1 + wdot2
        qdot[mdot_it, tret_it] = Qnetw
        eta_elec[mdot_it, tret_it] = Qnetw / (wdot1 + wdot2) 
        if tret_in >= tsup:
            cost_per_kWh_th[mdot_it, tret_it] = 0
        else:
            cost_per_kWh_th[mdot_it, tret_it] = gV.ELEC_PRICE *(wdot1 + wdot2) / Qnetw
            
        total_cost_per_kWh_th[mdot_it, tret_it] = gV.ELEC_PRICE *(wdot1 + wdot2)
        
        
        i += 1
        print i


            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D


f1 = interpolate.interp2d(mdot_range, tret_range, wdotfin/10E3, kind = 'cubic')
f2 = interpolate.interp2d(mdot_range, tret_range, qdot/10E3, kind = 'cubic')
f3 = interpolate.interp2d(mdot_range, tret_range, eta_elec, kind = 'cubic')
f4 = interpolate.interp2d(mdot_range, tret_range, cost_per_kWh_th*100* 1000, kind = 'cubic')
f5 = interpolate.interp2d(mdot_range, tret_range, total_cost_per_kWh_th, kind = 'cubic')




#C_furn_interp = f1(Q_therm, y1,




"""# PLOTTING """

fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(mdot_range, tret_range-273)
Z = f4(mdot_range, tret_range)


ax.set_xlabel("Mass Flow in Network")
ax.set_ylabel("Return Temperature [degC]")
ax.set_zlabel("Primary Energy [kWh/h]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)
#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()



