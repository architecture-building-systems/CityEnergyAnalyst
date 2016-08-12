""" Slave Sub Function - Treat solar power!""" 


"""

In this file, all sub-functions are stored that are used for storage design and operation. 
They are called by either the operation or optimization of storage.
"""


import numpy as np
 

def StorageGateway(Q_solar_available, Q_network_demand, P_HP_max, gv):
    
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
        Thermal Energy going to the Storage Tanks (excl. conversion losses)
        
    Q_from_storage : float
        Thermal Energy required from storage (excl conversion losses)
        
    to__storage : int
        = 1 --> go to storage
        = 0 --> ask energy from storage or other plant
    """
    
    if Q_solar_available > Q_network_demand:
        Q_to_storage = (Q_solar_available - Q_network_demand) 
        to_storage = 1
        Q_from_storage = 0
        
    else:
        Q_to_storage = 0
        to_storage = 0
        Q_from_storage = Q_network_demand - Q_solar_available
    
    
    if gv.StorageMaxUptakeLimitFlag == 1:
        if Q_to_storage >= P_HP_max:
            Q_to_storage = P_HP_max
            #print "Storage charging at full power!"
            
        if Q_from_storage >= P_HP_max:
            Q_from_storage= P_HP_max    
            #print "Storage decharging at full power!"
            
    return Q_to_storage, Q_from_storage, to_storage


def Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_return_DH, gv):
    """ 
    USE ONLY IF Q solar is not sufficient! 
    This function derives the temperature just before the power plant, after solar energy is injected.
    """
    if Q_network_demand < Q_solar_available:
        print "ERROR AT Temp_before_Powerplant ( see SolarPowerHandler, line 83)"
        T_before_PP = T_return_DH
        
    T_before_PP = T_return_DH  + Q_solar_available / (mdot_DH * gv.cp)
    
    return T_before_PP


def Storage_Charger(T_storage_old, Q_to_storage_lossfree, T_DH_ret, Q_in_storage_old, STORAGE_SIZE, context, gv):
    """
    calculates the temperature of storage when charging 
    
    Q_to_storage_new = including losses
    """
    
    MS_Var = context
    
    if T_storage_old > T_DH_ret:
        COP_th = T_storage_old / (T_storage_old - T_DH_ret) 
        COP = gv.HP_etaex * COP_th
        E_aux = Q_to_storage_lossfree * (1 + MS_Var.Storage_conv_loss) * (1/COP) # assuming the losses occur after the heat pump
        Q_to_storage_new = (E_aux + Q_to_storage_lossfree)  * (1- MS_Var.Storage_conv_loss)
        #print "HP operation Charging"
    else: 
        E_aux = 0
        Q_to_storage_new = Q_to_storage_lossfree * (1- MS_Var.Storage_conv_loss)
        #print "HEX charging"
    
    Q_in_storage_new = Q_in_storage_old + Q_to_storage_new

    T_storage_new = MS_Var.T_storage_zero + Q_in_storage_new * gv.Wh_to_J / (float(STORAGE_SIZE) * float(gv.cp) * float(gv.rho_60))

    
    return T_storage_new, Q_to_storage_new, E_aux, Q_in_storage_new


def Storage_DeCharger(T_storage_old, Q_from_storage_req, T_DH_sup, Q_in_storage_old, STORAGE_SIZE, context, gv):
    """
    de charging of the storage, no outside thermal losses  in the model 
    """
    MS_Var = context
    if T_DH_sup > T_storage_old: # using a heat pump if the storage temperature is below the desired network temperature

        COP_th = T_DH_sup / (T_DH_sup-T_storage_old ) # take average temp of old and new as low temp
        COP = gv.HP_etaex * COP_th
        #print COP
        E_aux = Q_from_storage_req / COP * (1 + MS_Var.Storage_conv_loss)
        Q_from_storage_used = Q_from_storage_req * (1 - 1/COP) * (1 + MS_Var.Storage_conv_loss)
        #print "HP operation de-Charging"
        #print  "Wh used from Storage", Q_from_storage_used
    
        
        
    else:  # assume perfect heat exchanger that provides the heat to the network
        Q_from_storage_used = Q_from_storage_req * (1 + MS_Var.Storage_conv_loss)
        E_aux = 0.0
        COP = 0.0
        #print "HEX-Operation Decharging"
    
    
    Q_in_storage_new = Q_in_storage_old - Q_from_storage_used

    T_storage_new = MS_Var.T_storage_zero + Q_in_storage_new * gv.Wh_to_J / (float(STORAGE_SIZE) * float(gv.cp) * float(gv.rho_60))


    #print Q_in_storage_new, "energy in storage left"

    return E_aux, Q_from_storage_used, Q_in_storage_new, T_storage_new, COP
    

def Storage_Loss(T_storage_old, T_amb, STORAGE_SIZE, context, gv):
    """
    Calculates the storage Loss for every time step, assume  D : H = 3 : 1
    
    Parameters
    ----------
    T_storage_old : float
        temperature of storage at time step, without any losses
    
    T_amb : float
        Ambient temperature
        
    Returns
    -------
    Q_loss : float
        Energy Loss due to non-perfect insulation  in Wh / h
    
    """
    MS_Var = context
    
    V_storage = STORAGE_SIZE
   
    H_storage = (2.0 * V_storage / (9.0 * np.pi ))**(1.0/3.0)  #assume 3 : 1 (D : H) 
    # D_storage = 3.0 * H_storage
    
    A_storage_ground = V_storage / H_storage 
    A_storage_rest = 2.0 * ( H_storage * np.pi * V_storage)**(1.0 / 2.0)

    Q_loss_uppersurf = MS_Var.alpha_loss * A_storage_ground * (T_storage_old - T_amb)
    Q_loss_rest = MS_Var.alpha_loss * A_storage_rest* (T_storage_old - gv.TGround) # calculated by EnergyPRO
    Q_loss = float(Q_loss_uppersurf + Q_loss_rest)
    T_loss = float(Q_loss / (STORAGE_SIZE * gv.cp * gv.rho_60 * gv.Wh_to_J))
    
    
    return Q_loss, T_loss


def Storage_Operator(Q_solar_available, Q_network_demand, T_storage_old, T_DH_sup, T_amb, Q_in_storage_old, T_DH_return, \
        mdot_DH, STORAGE_SIZE, context, P_HP_max, gv):
        
    Q_to_storage, Q_from_storage_req, to_storage = StorageGateway(Q_solar_available, Q_network_demand, P_HP_max, gv)
    Q_missing = 0
    Q_from_storage_used = 0
    E_aux_dech = 0
    E_aux_ch = 0
    mdot_DH_missing = Q_network_demand
   

    if to_storage == 1: # charging the storage
        
        T_storage_new, Q_to_storage_new, E_aux_ch, Q_in_storage_new = \
                                Storage_Charger(T_storage_old, Q_to_storage,T_DH_return, Q_in_storage_old, STORAGE_SIZE, context, gv)
        Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb, STORAGE_SIZE,context, gv)
        T_storage_new -= T_loss
        Q_in_storage_new -= Q_loss
        Q_from_storage_used = 0
        mdot_DH_missing = 0
    
    
    else: # DECHARGE     #elif Q_in_storage_old > 0: #and T_storage_old > gv.T_storage_min: # de-charging the storage is possible
        
        if Q_in_storage_old > 0: # Start de-Charging
            E_aux_dech, Q_from_storage_used, Q_in_storage_new, T_storage_new, COP = \
                                Storage_DeCharger(T_storage_old, Q_from_storage_req, T_DH_sup, Q_in_storage_old, STORAGE_SIZE, context, gv)
            
            Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb, STORAGE_SIZE,context, gv)
            T_storage_new -= T_loss
            Q_in_storage_new = Q_in_storage_old - Q_loss - Q_from_storage_used
            
            mdot_DH_missing = mdot_DH * (Q_network_demand - Q_from_storage_used)/ Q_network_demand

            if Q_in_storage_new < 0: # if storage is almost empty, to not go below 10 degC, just do not provide more energy than possible.
                #T_storage_new = gv.T_storage_min
                #Q_from_storage_1 = math.floor((MS_Var.STORAGE_SIZE * gv.cp * gv.rho_60 * 1/gv.Wh_to_J) * (T_storage_old - T_storage_new))
                Q_from_storage_poss = Q_in_storage_old
                Q_missing = Q_network_demand - Q_solar_available - Q_from_storage_poss
                #Q_from_storage_poss = min(Q_from_storage_1, Q_from_storage_2)
                #print Q_from_storage_poss, "taken from storage as max"
                
                if Q_missing < 0: #catch numerical errors (leading to very low (absolute) negative numbers) 
                    Q_missing = 0
                
                E_aux_dech, Q_from_storage_used, Q_in_storage_new, T_storage_new, COP = \
                            Storage_DeCharger(T_storage_old, Q_from_storage_poss, T_DH_sup, Q_in_storage_old, STORAGE_SIZE,context, gv)
    
                #print "limited decharging"
                
                Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb, STORAGE_SIZE, context, gv)
                
                """
                # CURRENTLY NOT USED
                if T_storage_new < gv.T_storage_min:
                    print "error at limited decharging"
                    print T_storage_old -273, "T_storage_old"
                    Q_from_storage_used = 0 
                """
                    
                Q_in_storage_new = Q_in_storage_old - Q_loss - Q_from_storage_used
                #print "currently Decharging with :", Q_loss + Q_from_storage_used, "Wh"
                #print "Q_in_storage_old", Q_in_storage_old
                #print "Q_in_storage_new", Q_in_storage_new
                T_storage_new -= T_loss
                
                mdot_DH_missing = mdot_DH * (Q_missing)/ Q_network_demand
            
        else: # neither storage  charging nor decharging
            E_aux_ch = 0
            E_aux_dech = 0
            Q_loss, T_loss = Storage_Loss(T_storage_old,T_amb, STORAGE_SIZE,context, gv)
            T_storage_new = T_storage_old - T_loss
            Q_in_storage_new = Q_in_storage_old - Q_loss
            Q_missing = Q_network_demand - Q_solar_available
            if Q_missing < 0: #catch numerical errors (leading to very low (absolute) negative numbers) 
                Q_missing = 0
            mdot_DH_missing = mdot_DH * (Q_missing)/ Q_network_demand
            
            #print "mdot_DH_missing", mdot_DH_missing
                 
    return Q_in_storage_new, T_storage_new, Q_from_storage_req, Q_to_storage, E_aux_ch, E_aux_dech, \
                        Q_missing, Q_from_storage_used, Q_loss, mdot_DH_missing
