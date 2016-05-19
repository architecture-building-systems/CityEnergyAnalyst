""" Slave Sub Function - Treat solar power!""" 



Energy_Models_path ="/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/EnergySystem_Models"
M_to_S_Var_path = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/M_and_S/Slave"

import os
os.chdir(Energy_Models_path)
import globalVar as gV
os.chdir(M_to_S_Var_path)
import Master_to_Slave_Variables as MS_Var
reload(MS_Var)
os.chdir(Energy_Models_path)
reload (gV)



def StorageGateway(Q_solar_available, Q_network_demand):
    
    """
    This function is a first filter for solar energy handling: 
        If there is excess solar power, this will specified and stored.
        
        If there is not enough solar power, the lack will be calculated.
    
    
    Parameters
    ----------
    Q_solar_available : float
        Solar Energy available at given time step
        
    Q_network_demand : float
        Network Load at given time step
    
    Returns
    -------
    Q_to_storage : float
        Thermal Energy going to the Storage Tanks
        
    Q_from_storage : float
        Thermal Energy required from storage
        
    to__storage : int
        = 1 --> go to storage
        = 0 --> ask energy from storage or other plant
    """
    if Q_solar_available > Q_network_demand:
        Q_to_storage = (Q_solar_available - Q_network_demand) * (1-MS_Var.Storage_conv_loss) 
        to_storage = 1
        Q_Network_lack = 0
        
    else:
        Q_to_storage = 0
        to_storage = 0
        Q_Network_lack = Q_network_demand - Q_solar_available
    
    Q_from_storage = 1.1 * Q_Network_lack
    
    return Q_to_storage, Q_from_storage, to_storage
    
    
def Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_return_DH):
    """ 
    USE ONLY IF Q solar is not sufficient! 
    This function derives the temperature just before the power plant, after solar energy is injected.
    """
    if Q_network_demand < Q_solar_available:
        print "ERROR AT Temp_before_Powerplant"
        T_before_PP = T_return_DH
        
    T_before_PP = T_return_DH  + Q_solar_available / (mdot_DH * gV.cp)
    
    return T_before_PP

def Storage_Charger(T_storage_old, Q_to_storage, T_DH_return):
    """
    calculates the temperature of storage when charging 
    
    Q_to_storage_new = including losses
    """
    T_storage_new = T_storage_old + Q_to_storage *gV.Wh_to_J / (float(MS_Var.STORAGE_SIZE) * float(gV.cp) * float(gV.rho_60))
    
    if T_storage_old > T_DH_return:
        
        COP_th = T_storage_old / (T_storage_old - T_DH_return) # take average temp of old and new as low temp
        COP = gV.HP_etaex * COP_th
        Q_aux = Q_to_storage * (1 + MS_Var.Storage_conv_loss) * (1-1/COP)
        Q_to_storage_new = Q_aux * (1- MS_Var.Storage_conv_loss) + Q_to_storage 
        
    else: 
        Q_aux = 0
        Q_to_storage_new = Q_to_storage 
    
    return T_storage_new, Q_to_storage_new, Q_aux
    
def Storage_DeCharger(T_storage_old, Q_from_storage_req, T_DH_sup):
    
    if T_DH_sup > T_storage_old: # using a heat pump if the storage temperature is below the desired network temperature

        COP_th = T_DH_sup / (T_DH_sup-T_storage_old ) # take average temp of old and new as low temp
        COP = gV.HP_etaex * COP_th
        Q_from_storage_used = Q_from_storage_req * (1 - 1/COP)
        Q_aux = Q_from_storage_req / COP
        
    else:  # assume perfect heat exchanger that provides the heat to the network
        Q_from_storage_used = Q_from_storage_req
        Q_aux = 0.0
        COP = 0.0
    
    T_storage_new = T_storage_old - Q_from_storage_used *gV.Wh_to_J / (MS_Var.STORAGE_SIZE * gV.cp * gV.rho_60)

    return Q_aux, Q_from_storage_used, T_storage_new, COP
    
    
def Storage_Loss(T_storage_old,T_amb):
    """
    Calculates the storage Loss for every time step
    
    Parameters
    ----------
    T_storage_old : float
        temperature of storage at time step, without any losses
    
    T_amb : float
        Ambient temperature
        
    Returns
    -------
    Q_loss : float
        Energy Loss due to non-perfect insulation
    
    """
    
    Q_loss = MS_Var.A_storage_outside * MS_Var.alpha_loss * (T_storage_old - T_amb)
    T_loss = Q_loss / (MS_Var.STORAGE_SIZE * gV.cp * gV.rho_60) 

    return Q_loss, T_loss
    
"""
 E_storage : float
        Thermal Energy in storage
"""




def Storage_Operator(Q_solar_available, Q_network_demand, T_storage_old, T_DH_sup, T_amb, Q_in_storage_old, T_DH_return, mdot_DH):
    
    Q_to_storage, Q_from_storage_req, to_storage = StorageGateway(Q_solar_available, Q_network_demand)
    print to_storage, Q_solar_available, " =solar power; ", Q_network_demand, "=Network Demand"
    
    Q_missing = 0
    T_before_PP = T_DH_sup
    Q_sto_to_netw = 0
    
    if to_storage == 1: # charging the storage
        T_storage_new, Q_to_storage, Q_aux = Storage_Charger(T_storage_old, Q_to_storage, T_DH_return)
        Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb)
        print Q_to_storage, "Q_to_storage"
        T_storage_new -= T_loss
        Q_from_storage = 0
        print "charging" 
    
    elif Q_in_storage_old > 0: # de-charging the storage is possible
        if T_storage_old > gV.T_storage_min:
            Q_aux, Q_from_storage, T_storage_new, COP = Storage_DeCharger(T_storage_old, Q_from_storage_req, T_DH_sup)
            Q_sto_to_netw = (Q_from_storage + Q_aux ) / (1.0 + MS_Var.Storage_conv_loss)
            Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb)
            T_storage_new -= T_loss
            Q_in_storage_new = Q_in_storage_old - Q_loss - Q_sto_to_netw + Q_to_storage 
             
            print "decharging"
            
            if T_storage_new < gV.T_storage_min or Q_in_storage_new < 0: # if storage is almost empty, to not go below 10 degC, just do not provide more energy than possible.
                T_storage_new = gV.T_storage_min
                Q_from_storage_1 = (MS_Var.STORAGE_SIZE * gV.cp * gV.rho_60) * (T_storage_old - T_storage_new) 
                Q_from_storage_2 = Q_in_storage_old
                    
                Q_from_storage = min(Q_from_storage_1, Q_from_storage_2)
                print Q_from_storage, "taken from storage as max"
                
                COP_th = T_DH_sup / (T_DH_sup-T_storage_old) 
                COP = gV.HP_etaex * COP_th
                Q_aux = Q_sto_to_netw / COP
                print "limited decharging"
                
                Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb)
                Q_sto_to_netw = (Q_from_storage + Q_aux) * (1.0 - MS_Var.Storage_conv_loss) - Q_loss
                T_storage_new -= T_loss
        """
        else:
            Q_from_storage = 0
            Q_aux = 0
            Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb)
            T_storage_new -= T_loss
            Q_sto_to_netw = 0
            """
            
    else: # Storage is empty, de-charging not possible
        Q_missing = Q_network_demand - Q_solar_available
        T_before_PP = Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_DH_return)
        Q_aux = 0
        Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb)
        T_storage_new = T_storage_old - T_loss
        Q_sto_to_netw = 0
        Q_to_storage = 0
        Q_from_storage = 0
        print "storage is empty"
    
    Q_in_storage_new = Q_in_storage_old - Q_loss + Q_to_storage - Q_from_storage
    print Q_in_storage_new, "= Q_in_storage_new"

    #deltaQ_storage = Q_in_storage_new - Q_in_storage_old
    
    return Q_in_storage_new, T_storage_new, Q_from_storage_req, Q_to_storage, Q_aux, to_storage, Q_missing, T_before_PP
    
# T_before_PP = Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_return_DH)

""" Testing and Plotting """

Q_solar_available = [10000, 40000, 60000, 30000, 0, 0 ,0, 4000]
Q_network_demand = [2000, 45000, 50000, 50000, 2000, 1000, 1000,0]
T_storage_old = 20  + 273.0
T_amb = 10 + 273.0
Q_in_storage_old = 100.0
T_DH_sup = 65 + 273.0 # K
T_DH_return = 40 + 273.0 # K
mdot_DH = 10 # kg/s

HOUR_MAX = len(Q_network_demand)
HOUR = 0

import numpy as np
Q_in_storage = np.zeros(HOUR_MAX)
T_storage =np.zeros(HOUR_MAX)
Q_from_storage = np.zeros(HOUR_MAX)
Q_to_storage = np.zeros(HOUR_MAX)
Q_aux = np.zeros(HOUR_MAX)
to_storage = np.zeros(HOUR_MAX)

while HOUR < HOUR_MAX:
    
    storage_data = Storage_Operator(Q_solar_available[HOUR], Q_network_demand[HOUR], T_storage_old, T_DH_sup, T_amb, Q_in_storage_old, mdot_DH, T_DH_return)
    
    # Storing Data
    Q_in_storage[HOUR] = storage_data[0]
    T_storage[HOUR] = storage_data[1]
    Q_from_storage[HOUR] = storage_data[2]
    Q_to_storage[HOUR] =storage_data[3]
    Q_aux[HOUR] =storage_data[4]
    to_storage[HOUR] = storage_data[5]
       
    # preparing for new time step
    T_storage_old = storage_data[1]
    Q_in_storage_old = storage_data[0]
    print Q_in_storage_old
    HOUR += 1
    print HOUR
