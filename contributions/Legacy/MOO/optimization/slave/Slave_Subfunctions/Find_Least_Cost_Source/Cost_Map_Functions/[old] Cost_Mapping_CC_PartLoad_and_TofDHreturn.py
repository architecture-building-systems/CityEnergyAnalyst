"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant

WORK IN PROCESS 

"""


# Mapping CC Cost


#Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
#M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Trials"

#import os
import numpy as np
#os.chdir(Energy_Models_path)
import Model_CC as MCC
import globalVar as gV

from contributions.Legacy.MOO.optimization.master import MasterToSlaveVariables

context = MasterToSlaveVariables.MasterSlaveVariables()
MS_Var = context


#os.chdir(M_to_S_Var_path)
#import Master_to_Slave_Variables as MS_Var
#reload(MS_Var)
#os.chdir(Energy_Models_path)

#reload (gV)
reload (MCC)

#TO BE ITERATED!
fuel = MS_Var.gt_fuel
Q_design = MS_Var.gt_size 

# TRY 2 - iterating and mapping the thermal output

it_len = 50
 
phi_min = gV.GT_minload


import matplotlib.pyplot as plt

  
        

tDH_min = 30 + 273.0 # K 
tDH_max = 90 + 273.0 # K 

tDH_range = np.linspace(tDH_min, tDH_max, it_len)
wdot_range = np.linspace(Q_design*phi_min, Q_design, it_len)

wdotfin = np.zeros( (it_len, it_len) )
qdot = np.zeros( (it_len, it_len) )
eta_elec = np.zeros( (it_len, it_len) )
eta_heat = np.zeros( (it_len, it_len) )
eta_all = np.zeros( (it_len, it_len) )
Q_used_prim = np.zeros( (it_len, it_len) )
cost_per_kWh_th = np.zeros( (it_len, it_len) )
cost_per_kWh_th_incl_el =  np.zeros( (it_len, it_len) )
total_cost_per_kWh_th_incl_el = np.zeros( (it_len, it_len) )
Q_loss = np.zeros( (it_len, it_len) )


i = 0
for tDH_it in range(len(tDH_range)):
    tDH = tDH_range[tDH_it]
    
    for wdot_it in range(len(wdot_range)):
        wdot_in = wdot_range[wdot_it]
        
        if wdot_in <= phi_min * Q_design:
            wdot_in = phi_min * Q_design + 0.001 
            print "changed"
            
        CC_OpInfo = MCC.CC_Op(wdot_in, Q_design, fuel, tDH)
        
        if wdot_in <= phi_min * Q_design:
            CC_OpInfo = [0,0,0,0,0]
        wdotfin[tDH_it, wdot_it] = CC_OpInfo[0]
        qdot[tDH_it, wdot_it] = CC_OpInfo[1]
        eta_elec[tDH_it, wdot_it] = CC_OpInfo[2]
        eta_heat[tDH_it, wdot_it] = CC_OpInfo[3]
        eta_all[tDH_it, wdot_it] = CC_OpInfo[4]
        
        Q_used_prim[tDH_it, wdot_it] = CC_OpInfo[1] / CC_OpInfo[3] # = qdot  / eta_heat  
        Q_loss[tDH_it, wdot_it] = (1 - CC_OpInfo[4] )  
        cost_per_kWh_th[tDH_it, wdot_it] = gV.NG_PRICE / CC_OpInfo[3] # = gV.NG_PRICE / eta_heat
        cost_per_kWh_th_incl_el[tDH_it, wdot_it] = gV.NG_PRICE / CC_OpInfo[3] - CC_OpInfo[0] * gV.ELEC_PRICE / CC_OpInfo[1]  # gV.NG_PRICE / eta_heat - wdotfin * gV.ELEC_PRICE / qdot
        total_cost_per_kWh_th_incl_el[tDH_it, wdot_it] = cost_per_kWh_th_incl_el[tDH_it, wdot_it] * CC_OpInfo[1]
        
        i += 1
        print i

        #print x,k
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D


f1 = interpolate.interp2d(tDH_range, wdot_range, wdotfin/10E3, kind = 'cubic')
f2 = interpolate.interp2d(tDH_range, wdot_range, qdot/10E3, kind = 'cubic')
f3 = interpolate.interp2d(tDH_range, wdot_range, eta_elec, kind = 'cubic')
f4 = interpolate.interp2d(tDH_range, wdot_range, eta_heat, kind = 'cubic')
f5 = interpolate.interp2d(tDH_range, wdot_range, eta_all, kind = 'cubic')
f6 = interpolate.interp2d(tDH_range, wdot_range, total_cost_per_kWh_th_incl_el, kind = 'cubic')
f7 = interpolate.interp2d(tDH_range, wdot_range, cost_per_kWh_th_incl_el*100*1000, kind = 'cubic')
f8 = interpolate.interp2d(tDH_range, wdot_range, cost_per_kWh_th*100* 1000, kind = 'cubic')
f9 = interpolate.interp2d(tDH_range, wdot_range, Q_used_prim/10E3, kind = 'cubic')


# for checking the numbers
f10 = interpolate.interp2d(tDH_range, wdot_range, Q_loss, kind = 'cubic')

#C_furn_interp = f1(Q_therm, y1,




"""# PLOTTING """

fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(wdot_range/ 1E6,tDH_range-273.0)
Z = f7(tDH_range, wdot_range)
#Z1 = f1(tDH_range, wdot_range)
#Z3 = Z1 + Z
# for checking the numbers: 
# Z1 = 1 - ((f1(tDH_range, wdot_range) + f2(tDH_range, wdot_range) ) / f9(tDH_range, wdot_range)) # calculated losses by output loads
#Z1 = f1(tDH_range, wdot_range) / f3(tDH_range, wdot_range)
#Z = f2(tDH_range, wdot_range) / f4(tDH_range, wdot_range)
#ax.plot_surface(X1, Y1, Z)


ax.set_xlabel("Electric Partload of GT [-]")
ax.set_ylabel("DH Supply Temp. [degC]")
ax.set_zlabel("Cost of Thermal Energy [Rp/kWh]")
#ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)
#ax.plot_surface(X1, Y1, Z1, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()



