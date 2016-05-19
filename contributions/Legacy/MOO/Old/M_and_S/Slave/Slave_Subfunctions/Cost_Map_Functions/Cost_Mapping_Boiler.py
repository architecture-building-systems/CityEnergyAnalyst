"""    Cost Mapping    """  

"""
this script aims to map the cost of each plant
"""


Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import os
import numpy as np
os.chdir(Energy_Models_path)
import Model_Boiler_condensing as MBc
reload (MBc)

import globalVar as gV
reload (gV)

os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload (MS_Var)

os.chdir(Energy_Models_path)




Q_design = MS_Var.Boiler_P_max


def BoilerCond_op_cost(Q_therm, Q_design, T_return_to_boiler):
    """ 
    Calculates the operation cost of a Condensing Boiler (only operation, no annualized cost!)
    
    Parameters
    ----------
    P_design : float
        Design Power of Boiler Plant (Boiler Thermal power!!)
        
    Q_annual : float
        annual thermal Power output
        
    T_return_to_boiler : float
        return temperature to Boiler (from DH network) 
    
    Returns
    -------
    C_boil_therm : float
        Total generation cost for required load (per hour) in CHF
    
    C_boil_per_Wh : float
        cost per Wh in CHF / kWh
     
    Q_primary : float
        required thermal energy per hour (in Wh Natural Gas) 
    """

    """ Iterating for efficiency as Q_thermal_required is given as input """
    
    #if float(Q_therm) / float(Q_design) < gV.Boiler_min:
    #    print "error expected in Boiler operation, below min part load!"
        
    #print float(Q_therm) / float(Q_design)
    eta_boiler = MBc.Cond_Boiler_operation(Q_therm, Q_design, T_return_to_boiler)
  
    C_boil_therm = Q_therm / eta_boiler * gV.NG_PRICE #  CHF / Wh - cost of thermal energy
    C_boil_per_Wh = 1/ eta_boiler * gV.NG_PRICE + gV.Boiler_P_aux* gV.ELEC_PRICE + gV.Boiler_C_maintainance_faz

    
    Q_primary = Q_therm / eta_boiler
    
    return C_boil_therm, C_boil_per_Wh, Q_primary
    
    
"""
it_len = 100
Q_min = 20E3 # 20kW
Q_max = 10.0E6 # 10 MW
Q_design = Q_min

Q_design_range = np.linspace(max(Q_min, Q_design), Q_max, it_len)



import matplotlib.pyplot as plt
phi_min = 0.051

T_return_to_boiler_range = np.linspace(273 + 20.0, 273 + 80.0, it_len)

C_boil = np.zeros( (len(Q_design_range),len(T_return_to_boiler_range)) )
C_boil_per_kWh = np.zeros( (len(Q_design_range),len(T_return_to_boiler_range)) )
Q_primary_req = np.zeros( (len(Q_design_range),len(T_return_to_boiler_range)) )


print "process Started - Furnace Cost Mapping"

for T_it in range(len(T_return_to_boiler_range)):
    T_return_to_boiler = T_return_to_boiler_range[T_it]
    Q_therm = np.linspace(phi_min * Q_design, Q_design, it_len)
    #print Q_therm[0]
    k = 0
    for Q_therm_it in range(len(Q_therm)):
        Q_therm_in = Q_therm[Q_therm_it]

        Furnace_Cost = BoilerCond_op_cost(Q_therm_in, Q_design, T_return_to_boiler)
        C_boil[T_it,Q_therm_it] = Furnace_Cost[0]
        C_boil_per_kWh[T_it,Q_therm_it] = Furnace_Cost[1]
        Q_primary_req[T_it,Q_therm_it] = Furnace_Cost[2]
        k+= 1

            

from scipy import interpolate
from mpl_toolkits.mplot3d import Axes3D

# Create Continious Functions  by interpolating!
f1 = interpolate.interp2d(Q_therm, T_return_to_boiler_range, C_boil, kind = 'cubic')
f2 = interpolate.interp2d(Q_therm, T_return_to_boiler_range, C_boil_per_kWh, kind = 'cubic')
f3 = interpolate.interp2d(Q_therm, T_return_to_boiler_range, Q_primary_req, kind = 'cubic')



#C_furn_interp = f1(Q_therm, y1,






""" #PLOTTING """
"""
fig = plt.figure()
ax = Axes3D(fig)
phi_range = np.linspace(0.05, 1, it_len)
X1,Y1 = np.meshgrid(phi_range,T_return_to_boiler_range-273)
Z = f2(Q_therm, T_return_to_boiler_range)
#ax.plot_surface(X1, Y1, Z)

ax.set_xlabel("Part Load [-]")
ax.set_ylabel("Return Temperature [degC] ")
ax.set_zlabel("Cost per kWh [Rp/kWh]")
ax.plot_surface(X1, Y1, Z*100*1000, rstride=1, cstride=1, cmap='RdYlBu_r', linewidth = 0, antialiased = False)

#fig.colorbar(ax, shrink=0.5, aspect=5)

plt.show()














""" #OLD PLOT
"""
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
    