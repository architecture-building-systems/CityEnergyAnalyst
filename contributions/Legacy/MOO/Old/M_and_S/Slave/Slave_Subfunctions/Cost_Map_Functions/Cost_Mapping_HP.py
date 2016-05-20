# -*- coding: utf-8 -*-
"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant
"""


# Mapping Furnace Cost


Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import os
import numpy as np
os.chdir(Energy_Models_path)
import Model_HP as MHP
reload (MHP)

import globalVar as gV
reload (gV)

os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload (MS_Var)

os.chdir(Energy_Models_path)






def HPLake_op_cost(mdot, tsup, tret, tlake):
    """ 
    Calculates the operation cost of a Lake Heat Pump, no Pumping Cost included (neither on the lake-side nor on the DH side) 
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply for the DHN (hot)
    tret : float
        temperature of return for the DHN (cold)
    tlake : float
        temperature of the lake
    
    Returns
    -------
    
    C_HPL_el : float
        Total electricity cost for required parameters (per hour) in CHF
    
    C_HPL_per_kWh_th : float
        cost per kWh_thermal_out in Rp / kWh
     
    Q_cold_primary : float
        required thermal (cold side, from the lake) energy per hour (in Wh of cold water)
        
    Q_therm : float
        thermal energy yield from HP operation (hot water stream) 
    """

    """ Iterating for efficiency as Q_thermal_required is given as input """
    wdot, qcolddot = MHP.HPLake_Op(mdot, tsup, tret, tlake)
    
    
    Q_therm = mdot * gV.cp *(tsup - tret)
        

    C_HPL_el = wdot * gV.ELEC_PRICE #  CHF / Wh - cost of thermal energy
    C_HPL_per_kWh_th = C_HPL_el / Q_therm
    
    Q_cold_primary = qcolddot
    
    return C_HPL_el, C_HPL_per_kWh_th, Q_cold_primary, Q_therm
    
 
def HPSew_op_cost(mdot, tsup, tret, mdotsew, tsupsew):
    """ 
    Calculates the operation cost of a Lake Heat Pump
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply to the DHN (hot)
    tret : float
        temperature of return of the DHN (cold),going to Sewage
    mdotsew : float
        mass flow rate in the sewage
    tsupsew : float
        temperature of supply of the sewage (hot)
        
        
    Returns
    -------
  
    C_HPSew_el_pure
        total cost of HP operation (might be limited Q_therm), not fulfilled to maximum
   
    C_HPSew_per_kWh_th_pure : float
        Marginal Cost of HP operation (might be limited Q_therm), not fulfilled to maximum
    
    Q_cold_primary_sew : float
        cooling energy required
        
    Q_therm : float
        Thermal Energy delivered by Sewage Plant
    """

    """ Iterating for efficiency as Q_thermal_required is given as input """
    
    
    wdot, qcolddot, tsup_calc, qhotdot_missing = MHP.HPSew_Op(mdot, tsup, tret, mdotsew, tsupsew)

    Q_therm = mdot * gV.cp *(tsup_calc - tret) # Thermal Energy Provided
    C_extra_for_missing = qhotdot_missing * gV.ELEC_PRICE * 1.2 # Assuming electric resistance heating for the time being! can be replaced by boilers or similar
    
    C_HPSew_el_pure =wdot * gV.ELEC_PRICE 
    C_HPSew_el = C_HPSew_el_pure + C_extra_for_missing #  CHF / Wh - cost of thermal energy
    C_HPSew_per_kWh_th = C_HPSew_el / (Q_therm) 
    C_HPSew_per_kWh_th_pure = C_HPSew_el_pure / (Q_therm) 

    Q_cold_primary_sew = qcolddot
    
    return C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_cold_primary_sew, Q_therm
     
    
    

def GHP_op_cost(mdot, tsup, tret, tground):
    """ 
    Calculates the operation cost of a Lake Heat Pump
    
    Parameters
    ----------
    mdot : float
        mass flow rate in the district heating network
    tsup : float
        temperature of supply to the DHN (hot)
    tret : float
        temperature of return from the DHN (cold)
    tground : float
        temperature of the ground
        
    Returns
    -------
    C_GHP_el : float
        total electricity cost of a HP
    C_GHP_per_kWh_th
    Q_cold_primary_ghp
    Q_therm
    """

    """ Iterating for efficiency as Q_thermal_required is given as input """
    
    
    wdot, qcolddot, qhotdot_missing, tsup2 = MHP.GHP_Op(mdot, tsup, tret, tground)
    
    Q_therm = mdot * gV.cp *(tsup2 - tret) # Thermal Energy Provided
    
    C_extra_for_missing = qhotdot_missing * gV.ELEC_PRICE * 1.2 # Assuming electric resistance heating for the time being! can be replaced by boilers or similar

    C_GHP_el = wdot * gV.ELEC_PRICE + C_extra_for_missing #  CHF / Wh - cost of thermal energy
    C_GHP_per_kWh_th = C_GHP_el / (Q_therm) 

    Q_cold_primary_ghp = qcolddot
    
    return C_GHP_el, C_GHP_per_kWh_th, Q_cold_primary_ghp, Q_therm
 
    
       
             
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
    