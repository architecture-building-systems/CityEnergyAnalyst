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
import EnergySystem_Models.Model_CC as MCC
reload (MCC)
#os.chdir(Energy_Models_path)
import globalVar as gV
#reload(gV)
#os.chdir(M_to_S_Var_path)
#import Master_to_Slave_Variables as MS_Var
#reload(MS_Var)
#os.chdir(Energy_Models_path)

from contributions.Legacy.MOO.optimization.master import MasterToSlaveVariables

reload(MasterToSlaveVariables)
context = MasterToSlaveVariables.MasterSlaveVariables()
MS_Var = context 



#TO BE ITERATED!
fuel = MS_Var.gt_fuel
Q_design = MS_Var.gt_size 

# TRY 2 - iterating and mapping the thermal output

it_len = 50
 
phi_min = gV.GT_minload


import matplotlib.pyplot as plt
from scipy import interpolate

  
        

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


def CC_Find_Operation_Point(GT_SIZE, T_DH_Supply, fuel, Q_therm_request):
    """
    Retruns Cost Function and Operation Point of CC for a requested Q_therm
    """
    tDH = T_DH_Supply
    it_len = 100
    wdot_range = np.linspace(GT_SIZE*gV.GT_minload, GT_SIZE, it_len)
    qdot = np.zeros(it_len)
    
    for wdot_it in range(len(wdot_range)):
        wdot_in = wdot_range[wdot_it]
            
        CC_OpInfo = MCC.CC_Op(wdot_in, GT_SIZE, fuel, tDH)
    
        qdot[wdot_it] = CC_OpInfo[1] # Thermal output

    Q_therm_interpol = interpolate.interp1d(qdot, wdot_range, kind = "linear")
    wdot_required = Q_therm_interpol(Q_therm_request)
    """
    wdot_possible_range = np.linspace(GT_SIZE*gV.GT_minload, wdot_required, it_len)
    wdot_req_it = 0
    
    for wdot_req_it in range(it_len):
        wdot_possible = wdot_possible_range[wdot_req_it]
        
        CC_OpInfo = MCC.CC_Op(wdot_possible, GT_SIZE, fuel, tDH)
        
        wdotfin= CC_OpInfo[0]
        qdot = CC_OpInfo[1] # Thermal output
        eta_elec = CC_OpInfo[2]
        eta_heat = CC_OpInfo[3]
        eta_all= CC_OpInfo[4]
        
        Q_used_prim = CC_OpInfo[1] / CC_OpInfo[3] # = qdot  / eta_heat  
        Q_loss = (1 - CC_OpInfo[4] )  
        cost_per_kWh_th= gV.NG_PRICE / CC_OpInfo[3] # = gV.NG_PRICE / eta_heat
        cost_per_kWh_th_incl_el = gV.NG_PRICE / CC_OpInfo[3] - CC_OpInfo[0] * gV.ELEC_PRICE / CC_OpInfo[1]  # gV.NG_PRICE / eta_heat - wdotfin * gV.ELEC_PRICE / qdot
        total_cost_per_kWh_th_incl_el = cost_per_kWh_th_incl_el* CC_OpInfo[1]
    """
        
            
    return wdot_required, Q_therm_interpol
    

            

from mpl_toolkits.mplot3d import Axes3D


f1 = interpolate.interp2d(tDH_range, wdot_range, wdotfin/10E3, kind = 'linear')
f2 = interpolate.interp2d(tDH_range, wdot_range, qdot, kind = 'cubic')
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



