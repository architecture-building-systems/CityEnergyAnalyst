# -*- coding: utf-8 -*-
"""    Cost Mapping    """  

"""
this script aims to map the cost of each all Heat Pumps
"""


# Mapping Furnace Cost


#Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
#M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

#import os
#import numpy as np
#os.chdir(Energy_Models_path)
import EnergySystem_Models.Model_HP as MHP
reload (MHP)

import globalVar as gV
#reload (gV)

#os.chdir(M_to_S_Var_path)
#import Master_to_Slave_Variables as MS_Var
#reload (MS_Var)

#os.chdir(Energy_Models_path)

#import MasterToSlaveVariables
#context = MasterToSlaveVariables.MasterSlaveVariables()
#MS_Var = context




def HPLake_op_cost(mdot, tsup, tret, tlake, gV):

    wdot, qcolddot = MHP.HPLake_Op(mdot, tsup, tret, tlake, gV)
    
    Q_therm = mdot * gV.cp *(tsup - tret)
        
    C_HPL_el = wdot * gV.ELEC_PRICE 
    
    Q_cold_primary = qcolddot
    
    return C_HPL_el, wdot, Q_cold_primary, Q_therm
    
 
def HPSew_op_cost(mdot, tsup, tret, tsupsew, gV):

    COP = gV.HP_etaex*(tsup+gV.HP_deltaT_cond)/((tsup+gV.HP_deltaT_cond)-tsupsew)   
    q_therm = mdot * gV.cp *(tsup - tret)
    qcoldot = q_therm*(1-(1/COP))
    
    wdot = q_therm/COP
       
    C_HPSew_el_pure = wdot * gV.ELEC_PRICE 
    C_HPSew_el = C_HPSew_el_pure 
    C_HPSew_per_kWh_th_pure = C_HPSew_el_pure / (q_therm) 
    
    return C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, qcoldot, q_therm, wdot
     
    
def GHP_op_cost(mdot, tsup, tret, gV, COP):

    q_therm = mdot * gV.cp *(tsup - tret) # Thermal Energy generated
    qcoldot = q_therm*(1-(1/COP))
    wdot = q_therm/COP

    C_GHP_el = wdot * gV.ELEC_PRICE 
 
    return C_GHP_el, wdot, qcoldot, q_therm
 
     
""" Plots for GHP """


"""                 
it_len = 50
tground =  8 + 273.0 # K 

T_return_from_DH_range = np.linspace(273 + 20, 273 + 64.999, it_len)

C_GHP_el = np.zeros( (it_len,it_len) )
C_GHP_per_kWh_th = np.zeros( (it_len,it_len) )
Q_cold_primary_ghp = np.zeros( (it_len,it_len) )
Q_therm = np.zeros( (it_len,it_len) )
"""
""" iterating for return temperature """
"""

tret_min = 20 + 273.0
tret_max = 63.99 + 273.0 
tret_range =  np.linspace(tret_min, tret_max, it_len)
"""
""" iterating for supply temperature"""
"""
tsup_min = 30 + 273 # K 
tsup_max = 70 + 273 # K 
tsup_range = np.linspace(tsup_min, tsup_max, it_len)
"""

""" iterating for DH Mass Flow"""
"""
mdot_min = 0.01
mdot_max = 10
mdot_range = np.linspace(mdot_min, mdot_max, it_len)
tsup = 70.0 + 273 # K 

mdot_in = 8


#ITERATE OVER GHP  requirements for constant DH operation
# Set GHP variables


for T_it in range(len(tsup_range)):
    tsup = tsup_range[T_it]

    for tret_it in range(len(tret_range)):
       
        tret_in = tret_range[tret_it]
   
        GHP_cost = GHP_op_cost(mdot_in, tsup, tret_in, tground)                               
        if tret_in >= tsup:
            GHP_cost = [0,0,0,0]
        C_GHP_el[T_it, tret_it] = GHP_cost[0]
        C_GHP_per_kWh_th[T_it,tret_it] = GHP_cost[1]
        Q_cold_primary_ghp[T_it, tret_it] = GHP_cost[2]
        Q_therm[T_it, tret_it] = GHP_cost[3]
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


# Create Continious Functions  by interpolating!
f1 = interpolate.interp2d(tsup_range, tret_range, C_GHP_el, kind = 'cubic')
f2 = interpolate.interp2d(tsup_range, tret_range, C_GHP_per_kWh_th*100*1000, kind = 'cubic')
f3 = interpolate.interp2d(tsup_range, tret_range, Q_cold_primary_ghp, kind = 'linear')
f4 = interpolate.interp2d(tsup_range, tret_range, Q_therm, kind = 'cubic')

#C_furn_interp = f1(Q_therm, y1,






 #PLOTTING 



fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(tsup_range - 273.0,tret_range-273.0)
Z = f1(tsup_range, tret_range)
#ax.plot_surface(X1, Y1, Z)

ax.set_xlabel("Return Temperature [degC]")
ax.set_ylabel("Supply Temperature [degC]")
ax.set_zlabel("Cost of Energy [CHF]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()







"""






    
""" PLOTS FOR Sewage HP are below """

"""              
it_len = 50
mdot_min = 0.05 #kg/s
mdot_max = 20 # kg/s
mdot_design = mdot_min                      

mdot_design_range = np.linspace(max(mdot_min, mdot_design), mdot_max, it_len)

                                                                                

T_return_from_DH_range = np.linspace(273 + 20, 273 + 64.999, it_len)

C_HPSew_el = np.zeros( (len(mdot_design_range),len(T_return_from_DH_range)) )
C_HPSew_per_kWh_th = np.zeros( (len(mdot_design_range),len(T_return_from_DH_range)) )
Q_cold_primary_sew = np.zeros( (len(mdot_design_range),len(T_return_from_DH_range)) )
Q_therm = np.zeros( (len(mdot_design_range),len(T_return_from_DH_range)) )

"""
""" iterating for return temperature """
"""

tret_min = 20 + 273.0
tret_max = 60 + 273.0 
tret_range =  np.linspace(tret_min, tret_max, it_len)
"""
""" iterating for supply temperature"""
"""
tsup_min = 30 + 273 # K 
tsup_max = 70 + 273 # K 
tsup_range = np.linspace(tsup_min, tsup_max, it_len)
"""

""" iterating for DH Mass Flow"""
"""
mdot_min = 0.1 
mdot_max = 10.0 
mdot_range = np.linspace(mdot_min, mdot_max, it_len)



"""

""" iterating for supply temp sewage """
"""
tsup_sew_min = 10 + 273 # K 
tsup_sew_max = 40 + 273 # K 
tsup_sew_range = np.linspace(tsup_sew_min, tsup_sew_max, it_len)
"""

""" iterating for mdotsew - mass flow sewage plant"""
"""
mdotsew_min = 0.1
mdotsew_max = 20
mdotsew_range = np.linspace(mdotsew_min, mdotsew_max, it_len)

print "process Started - Cost Mapping"






"""
"""
#ITERATE OVER sewage  requirements for constant DH operation
# Set Sewage Variables 

mdot = 10.0
tret = 40 + 273.0
tsup = 65 + 273.0 # Supply Temperature of DH Network

for T_it in range(len(mdotsew_range)):
    mdotsew_in = mdotsew_range[T_it]

    for tret_it in range(len(tsup_sew_range)):
       
        tsupsew = tsup_sew_range[tret_it]
   
        HPSew_cost = HPSew_op_cost(mdot, tsup, tret, mdotsew_in, tsupsew)                                   


        
        C_HPSew_el[T_it, tret_it] = HPSew_cost[0]
        C_HPSew_per_kWh_th[T_it,tret_it] = HPSew_cost[1]
        Q_cold_primary_sew[T_it, tret_it] = HPSew_cost[2]
        Q_therm[T_it, tret_it] = HPSew_cost[3]
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

# Create Continious Functions  by interpolating!
f1 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, C_HPSew_el, kind = 'cubic')
f2 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, C_HPSew_per_kWh_th*100*1000, kind = 'cubic')
f3 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, Q_cold_primary_sew, kind = 'linear')
f4 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, Q_therm, kind = 'cubic')

#C_furn_interp = f1(Q_therm, y1,






""" #PLOTTING 
"""


fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(mdot_design_range,T_return_from_DH_range)
Z = f2(mdot_design_range, T_return_from_DH_range)
#ax.plot_surface(X1, Y1, Z)

ax.set_xlabel("Mass Flow in Sewage Plant [kg/s]")
ax.set_ylabel("Sewage Supply Temperature [K] ")
ax.set_zlabel("Cost of Energy [Rp / kWh]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()
"""







#ITERATE OVER changing DH requirements for constant sewage operation
# Set Sewage Variables 
""" 
mdotsew = 5.0
tsupsew = 20 + 273.0
tsup = 65 + 273.0 # Supply Temperature of DH Network
for T_it in range(len(T_return_from_DH_range)):
    tret_in = tret_range[T_it]

    for tret_it in range(len(tret_range)):
       
        mdot = mdot_range[tret_it]
   
        HPSew_cost = HPSew_op_cost(mdot, tsup, tret_in, mdotsew, tsupsew)                                   

        #Q_therm = mdot_in * gV.cp * (tsup - T_return_to_boiler) 
        
        if tsup < tret_in:
            HPSew_cost = [0,0,0,0]
        
        C_HPSew_el[T_it, tret_it] = HPSew_cost[0]
        C_HPSew_per_kWh_th[T_it,tret_it] = HPSew_cost[1]
        Q_cold_primary_sew[T_it, tret_it] = HPSew_cost[2]
        Q_therm[T_it, tret_it] = HPSew_cost[3]
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

# Create Continious Functions  by interpolating!
f1 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, C_HPSew_el, kind = 'cubic')
f2 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, C_HPSew_per_kWh_th*100*1000, kind = 'cubic')
f3 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, Q_cold_primary_sew, kind = 'linear')
f4 = interpolate.interp2d(mdot_design_range, T_return_from_DH_range, Q_therm, kind = 'cubic')

#C_furn_interp = f1(Q_therm, y1,






""" #PLOTTING 
"""


fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(mdot_design_range,T_return_from_DH_range)
Z = f2(mdot_design_range, T_return_from_DH_range)
#ax.plot_surface(X1, Y1, Z)

ax.set_xlabel("Mass Flow in DH Network [kg/s]")
ax.set_ylabel("Return Temperature [K] ")
ax.set_zlabel("Cost of Energy [Rp / kWh]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()

"""

                 
                            





















""" PLOTS FOR HP LAKE """




"""
it_len = 100
mdot_min = 0.05 #kg/s
mdot_max = 20 # kg/s
mdot_design = mdot_min

mdot_design_range = np.linspace(max(mdot_min, mdot_design), mdot_max, it_len)


import matplotlib.pyplot as plt


T_return_to_boiler_range = np.linspace(273 + 20, 273 + 64.999, it_len)

C_HP_tot = np.zeros( (len(mdot_design_range),len(T_return_to_boiler_range)) )
C_HPL_per_kWh = np.zeros( (len(mdot_design_range),len(T_return_to_boiler_range)) )
Q_cold_primary_req = np.zeros( (len(mdot_design_range),len(T_return_to_boiler_range)) )
Q_therm_tot = np.zeros( (len(mdot_design_range),len(T_return_to_boiler_range)) )

tlake = 5 + 273.0 # K
tsup = 65 + 273.0 # K 
"""

""" iterating for supply temperature and return temperature"""
"""
tret_min = 35 + 273.0
tret_max = 65 + 273.0 
tret_range =  np.linspace(tret_min, tret_max, it_len)
"""
""" iterating for return temperature"""
"""
tsup_min = 30 + 273 # K 
tsup_max = 70 + 273 # K 
tsup_range = np.linspace(tsup_min, tsup_max, it_len)

print "process Started - Furnace Cost Mapping"

for T_it in range(len(T_return_to_boiler_range)):
    tsup_in = tsup_range[T_it]
    mdot_in = 5
    #Q_therm = np.linspace(phi_min * Q_design, Q_design, it_len)

    for tret_it in range(len(tret_range)):
        tret_in = tret_range[tret_it]
        
        mdot_in = 5 

        HP_cost = HPLake_op_cost(mdot_in, tsup_in, tret_in, tlake)
        #Q_therm = mdot_in * gV.cp * (tsup - T_return_to_boiler) 
        
        if tsup_in < tret_in:
            HP_cost = [0,0,0,0]

        C_HP_tot[tret_it, T_it] = HP_cost[0]
        C_HPL_per_kWh[tret_it, T_it] = HP_cost[1]
        Q_cold_primary_req[tret_it, T_it] = HP_cost[2]
        Q_therm_tot[tret_it, T_it] = HP_cost[3]
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

# Create Continious Functions  by interpolating!
f1 = interpolate.interp2d(mdot_design_range, T_return_to_boiler_range, C_HP_tot, kind = 'cubic')
f2 = interpolate.interp2d(mdot_design_range, T_return_to_boiler_range, C_HPL_per_kWh*100*1000, kind = 'cubic')
f3 = interpolate.interp2d(mdot_design_range, T_return_to_boiler_range, Q_cold_primary_req, kind = 'linear')
f4 = interpolate.interp2d(mdot_design_range, T_return_to_boiler_range, Q_therm_tot, kind = 'cubic')

#C_furn_interp = f1(Q_therm, y1,




"""

""" PLOTTING """
"""

fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(tsup_range,T_return_to_boiler_range)
Z = f4(mdot_design_range, T_return_to_boiler_range)
#ax.plot_surface(X1, Y1, Z)

ax.set_xlabel("Supply Temperature [K]")
ax.set_ylabel("Return Temperature [K] ")
ax.set_zlabel("Heat Produced [kWh/h]")
ax.plot_surface(X1, Y1, Z/1000.0, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()
"""














""" OLD PLOT
plt.imshow(znew)
plt.colorbar(orientation='vertical')
plt.show()


"""

"""      

plt.plot(xnew, f(xnew), label='linear')
plt.plot(xnew, eff_of_phi(xnew), label='cubic')
plt.legend(['Electric Efficiency = f(phi)'], loc='best')
plt.xlabel("Part Load phi = Q / Q_max ")
plt.ylabel("Electric Efficiency at Part Load")
plt.xlim(np.amin(x), np.amax(x))
plt.ylim(0,0.15)
plt.show()
"""
    