"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant

WORK IN PROCESS 

"""


# Mapping FC Operation Cost


#Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
#M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Trials"

#import os
import numpy as np
#os.chdir(Energy_Models_path)
#os.chdir(Energy_Models_path)

import EnergySystem_Models.Model_FuelCell_V2 as MFC
import globalVar as gV

#os.chdir(M_to_S_Var_path)
#import Master_to_Slave_Variables as MS_Var
#reload(MS_Var)
#os.chdir(Energy_Models_path)

#reload (gV)
reload (MFC)

from contributions.Legacy.MOO.optimization import MasterToSlaveVariables

#reload(MasterToSlaveVariables)
context = MasterToSlaveVariables.MasterSlaveVariables()
MS_Var = context

it_len = 50




import matplotlib.pyplot as plt

  

Q_design_range = np.linspace(1000, 10000, it_len)
Q_el_out = np.zeros( (it_len, it_len) )
qdot = np.zeros( (it_len, it_len) )
eta_elec = np.zeros( (it_len, it_len) )
eta_heat = np.zeros( (it_len, it_len) )
eta_all = np.zeros( (it_len, it_len) )

Q_therm_out = np.zeros( (it_len, it_len) )
cost_per_kWh_th = np.zeros( (it_len, it_len) )
cost_per_kWh_el = np.zeros( (it_len, it_len) )
cost_per_kWh_th_incl_el =  np.zeros( (it_len, it_len) )
total_cost_per_kWh_th_incl_el = np.zeros( (it_len, it_len) )
Q_loss = np.zeros( (it_len, it_len) )



i = 0
phi_threshold = 0.4
approach_call = "B"
phi_range = np.linspace(0, 1, it_len)

for Q_it in range(len(Q_design_range)):
    Q_design = Q_design_range[Q_it]

    
    for phi_it in range(len(phi_range)):
        Q_load_in = phi_range[phi_it]*Q_design
        
                
        eta_el, eta_therm = MFC.FC_operation(Q_load_in, Q_design, phi_threshold, approach_call)

        eta_elec[Q_it, phi_it] = eta_el
        eta_heat[Q_it, phi_it] = eta_therm
        eta_all[Q_it, phi_it] = eta_therm + eta_el
        
        Q_therm_out[Q_it, phi_it] =  Q_load_in* (eta_therm) # = load  / eta_all  
        Q_el_out[Q_it, phi_it] =  Q_load_in* (eta_el)
        if eta_therm == 0:
            eta_therm = 0.01
            print "used"
        cost_per_kWh_th[Q_it, phi_it] = gV.NG_PRICE / eta_therm # = gV.NG_PRICE / eta_heat
        if eta_el == 0:
            eta_el = 0.000001
        cost_per_kWh_el[Q_it, phi_it] = 1/ (eta_el * gV.ELEC_PRICE / gV.NG_PRICE) 
        cost_per_kWh_th_incl_el[Q_it, phi_it] = gV.NG_PRICE / eta_therm - eta_el /eta_therm* gV.ELEC_PRICE # gV.NG_PRICE / eta_heat - wdotfin * gV.ELEC_PRICE / qdot
        total_cost_per_kWh_th_incl_el[Q_it, phi_it] = cost_per_kWh_th_incl_el[Q_it, phi_it] * Q_therm_out[Q_it, phi_it]
        
        
        i += 1
        print i

        #print x,k
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

f1 = interpolate.interp2d(Q_design_range, phi_range, Q_el_out/10E3, kind = 'cubic')
f2 = interpolate.interp2d(Q_design_range, phi_range, qdot/10E3, kind = 'cubic')
f3 = interpolate.interp2d(Q_design_range, phi_range, eta_elec, kind = 'cubic')
f4 = interpolate.interp2d(Q_design_range, phi_range, eta_heat, kind = 'cubic')
f5 = interpolate.interp2d(Q_design_range, phi_range, eta_all, kind = 'cubic')
f6 = interpolate.interp2d(Q_design_range, phi_range, total_cost_per_kWh_th_incl_el, kind = 'cubic')
f7 = interpolate.interp2d(Q_design_range, phi_range, cost_per_kWh_th_incl_el*100* 1000, kind = 'cubic')
f8 = interpolate.interp2d(Q_design_range, phi_range, cost_per_kWh_th*100* 1000, kind = 'cubic')
f10 = interpolate.interp2d(Q_design_range, phi_range, cost_per_kWh_el, kind = 'cubic') 
f9 = interpolate.interp2d(Q_design_range, phi_range, Q_therm_out/10E3, kind = 'cubic')




#C_furn_interp = f1(Q_therm, y1,




"""# PLOTTING """

fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(Q_design_range / 10E3 ,phi_range)
Z = f7(Q_design_range, phi_range) 
#Z1 = f4(Q_design_range, phi_range)
#Z2 = f5(Q_design_range, phi_range)


#ax.plot_surface(X1, Y1, Z)

ax.set_ylabel("Design Size [kW]")
ax.set_xlabel("Partload of FC [-]")
ax.set_zlabel("Cost of Thermal Energy [Rp/kWh]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)
#ax.plot_surface(X1, Y1, Z1, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)
#ax.plot_surface(X1, Y1, Z2, rstride=1, cstride=1, cmap='hot', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()



