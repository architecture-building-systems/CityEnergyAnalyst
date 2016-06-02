"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant
"""


# Mapping Furnace Cost


Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave/Trials"

import os
import numpy as np
os.chdir(Energy_Models_path)
import Model_Furnace as MF
import globalVar as gV

os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
os.chdir(Energy_Models_path)

reload (gV)
reload (MF)
reload (MS_Var)


Q_load = 3000
Q_design = MS_Var.Furnace_P_max
T_return_to_boiler = 273 + 60.0

MOIST_TYPE = MS_Var.Furn_Moist_type

def Furnace_op_cost(Q_therm, Q_design, T_return_to_boiler, MOIST_TYPE):
    """ 
    Calculates the operation cost of a furnace plant (only operation, no annualized cost!)
    
    
    
    Parameters
    ----------
    P_design : float
        Design Power of Furnace Plant (Boiler Thermal power!!)
        
    Q_annual : float
        annual thermal Power output
    
    Returns
    -------
    C_furn : float
        Total generation cost for required load (per hour) in CHF, including profits from electricity Sold
    
    C_furn_per_kWh : float
        cost per kWh in Rp / kWh, Including profits from electricity sold
     
    Q_primary : float
        required thermal energy per hour (in Wh of wood chips) 
    """
    
    #if Q_load / Q_design < 0.3:
    #    raise ModelError
    """ Iterating for efficiency as Q_thermal_required is given as input """
    eta_therm_in = 0.5
    eta_therm_real = 1.0
    i = 0
    
    while 0.999 >= abs(eta_therm_in/eta_therm_real): # Iterating for thermal efficiency and required load
        if i != 0:
            eta_therm_in = eta_therm_real 
        i += 1
        Q_load = Q_therm / eta_therm_real # primary energy needed
        if Q_design < Q_load:
            Q_load = Q_design - 1
        
        Furnace_eff = MF.Furnace_eff(Q_load, Q_design, T_return_to_boiler, MOIST_TYPE)

        eta_therm_real, eta_el, Q_aux = Furnace_eff
        if eta_therm_real == 0:
            print "error found"
            break

        
    if MOIST_TYPE == "dry":
        C_furn_therm = Q_load / eta_therm_real * gV.Furn_FuelCost_dry #  CHF / Wh - cost of thermal energy
        C_furn_el_sold = (Q_load * eta_el - Q_aux)* gV.ELEC_PRICE #  CHF / Wh  - directly sold to the grid, as a cost gain
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_kWh = C_furn / Q_therm

        
    else:
        C_furn_therm = Q_therm * 1 / eta_therm_real * gV.Furn_FuelCost_wet 
        C_furn_el_sold = (Q_load * eta_el - Q_aux) * gV.ELEC_PRICE
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_kWh = C_furn / Q_therm # in Rp / kWh
    
    Q_primary = Q_load
    
    return C_furn, C_furn_per_kWh, Q_primary


it_len = 50
Q_min = 0.1E6
Q_max = 1E6
Q_design_range = np.linspace(Q_min, Q_max, it_len)
import matplotlib.pyplot as plt
phi_min = 0.3
T_return_to_boiler_range = np.linspace(273 + 20, 273 + 80, it_len)

C_furn = np.zeros( (it_len,it_len) )
C_furn_per_kWh = np.zeros( (it_len,it_len) )
Q_primary_req = np.zeros( (it_len,it_len) )



#Q_therm = np.linspace(phi_min*np.amin(Q_design_range), np.amax(Q_design_range), 10)

x = 0
"""for Q_design_it in range(len(Q_design_range)):
    Q_design = Q_design_range[Q_design_it]

    x += 1
    print x 
    """
print "process Started - Furnace Cost Mapping"

for T_it in range(len(T_return_to_boiler_range)):
    
    T_return_to_boiler = T_return_to_boiler_range[T_it]
    Q_therm = np.linspace(phi_min * Q_design, Q_design, it_len)
    k = 0
    x+= 1
    for Q_therm_it in range(len(Q_therm)):
        Q_therm_in = Q_therm[Q_therm_it]
        #print Q_therm_in, Q_design, Q_therm_in / Q_design, T_return_to_boiler
        Furnace_Cost = Furnace_op_cost(Q_therm_in, Q_design, T_return_to_boiler, MOIST_TYPE)
        C_furn[T_it,Q_therm_it,] = Furnace_Cost[0]
        C_furn_per_kWh[T_it,Q_therm_it] = Furnace_Cost[1]
        Q_primary_req[T_it,Q_therm_it] = Furnace_Cost[2]
        k+= 1
        #print x,k
            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D


f1 = interpolate.interp2d(T_return_to_boiler_range,Q_therm, C_furn, kind = 'cubic')
f2 = interpolate.interp2d(T_return_to_boiler_range,Q_therm, C_furn_per_kWh*100*1000, kind = 'cubic')
f3 = interpolate.interp2d(T_return_to_boiler_range,Q_therm, Q_primary_req, kind = 'cubic')



#C_furn_interp = f1(Q_therm, y1,






""" PLOTTING """

fig = plt.figure()
ax = Axes3D(fig)

X1,Y1 = np.meshgrid(Q_therm/10E6, T_return_to_boiler_range-273)
Z = f2(T_return_to_boiler_range,Q_therm)

ax.set_xlabel("Part Load [-]")
ax.set_ylabel("Return Temperature in K")
ax.set_zlabel("Thermal Energy Cost [Rp/kWh]")
ax.plot_surface(X1, Y1, Z, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()














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
    