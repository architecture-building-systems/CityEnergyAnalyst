""" Slave Sub Function - Treat solar power!"""

"""

In this file, all sub-functions are stored that are used for storage design and operation. 
They are called by either the operation or optimization of storage.
"""

import numpy as np

from cea.optimization.constants import *


def StorageGateway(Q_PVT_gen_W, Q_SC_gen_W, Q_server_gen_W, Q_compair_gen_W, Q_network_demand_W, P_HP_max_W):
    """
    This function is a first filter for solar energy handling: 
        If there is excess solar power, this will be specified and stored.
        If there is not enough solar power, the lack will be calculated.

    :param Q_solar_available_Wh: solar energy available at a given time step
    :param Q_network_demand_W: network load at a given time step
    :param P_HP_max_W: storage??
    :param gv: global variables
    :type Q_solar_available_Wh: float
    :type Q_network_demand_W: float
    :type P_HP_max_W: float
    :type gv: class
    :return:Q_to_storage: Thermal Energy going to the Storage Tanks (excl. conversion losses)
            Q_from_storage: Thermal Energy required from storage (excl conversion losses)
            to__storage: = 1 --> go to storage
            = 0 --> ask energy from storage or other plant
    :rtype: float, float, int
    """

    Q_server_to_directload_W = 0
    Q_server_to_storage_W = 0
    Q_compair_to_directload_W = 0
    Q_compair_to_storage_W = 0
    Q_PVT_to_directload_W = 0
    Q_PVT_to_storage_W = 0
    Q_SC_to_directload_W = 0
    Q_SC_to_storage_W = 0
    Q_to_storage_W = 0
    to_storage = 0

    if Q_server_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_server_gen_W
        Q_server_to_directload_W = Q_server_gen_W
        Q_server_to_storage_W = 0

    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_server_gen_W, 0)
        Q_to_storage_W = Q_server_gen_W - Q_network_demand_W + Q_compair_gen_W + Q_PVT_gen_W + Q_SC_gen_W
        to_storage = 1
        Q_server_to_directload_W = Q_network_demand_W
        Q_server_to_storage_W = Q_server_gen_W - Q_network_demand_W
        Q_compair_to_directload_W = 0
        Q_compair_to_storage_W = Q_compair_gen_W
        Q_PVT_to_directload_W = 0
        Q_PVT_to_storage_W = Q_PVT_gen_W
        Q_SC_to_directload_W = 0
        Q_SC_to_storage_W = Q_SC_gen_W

    if Q_compair_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_compair_gen_W
        Q_compair_to_directload_W = Q_compair_gen_W
        Q_compair_to_storage_W = 0

    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_compair_gen_W, 0)
        Q_to_storage_W = Q_compair_gen_W - Q_network_demand_W + Q_PVT_gen_W + Q_SC_gen_W
        to_storage = 1
        Q_compair_to_directload_W = Q_network_demand_W
        Q_compair_to_storage_W = Q_compair_gen_W - Q_network_demand_W
        Q_PVT_to_directload_W = 0
        Q_PVT_to_storage_W = Q_PVT_gen_W
        Q_SC_to_directload_W = 0
        Q_SC_to_storage_W = Q_SC_gen_W

    if Q_PVT_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_PVT_gen_W
        Q_PVT_to_directload_W = Q_PVT_gen_W
        Q_PVT_to_storage_W = 0
    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_PVT_gen_W, 0)
        Q_to_storage_W = Q_PVT_gen_W - Q_network_demand_W + Q_SC_gen_W
        to_storage = 1
        Q_PVT_to_directload_W = Q_network_demand_W
        Q_PVT_to_storage_W = Q_PVT_gen_W - Q_network_demand_W
        Q_SC_to_directload_W = 0
        Q_SC_to_storage_W = Q_SC_gen_W

    if Q_SC_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_SC_gen_W
        Q_SC_to_directload_W = Q_SC_gen_W
        Q_SC_to_storage_W = 0
    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_SC_gen_W, 0)
        Q_to_storage_W = Q_SC_gen_W - Q_network_demand_W
        to_storage = 1
        Q_SC_to_directload_W = Q_network_demand_W
        Q_SC_to_storage_W = Q_SC_gen_W - Q_network_demand_W

    Q_from_storage_W = Q_network_demand_W

    if StorageMaxUptakeLimitFlag == 1:
        if Q_to_storage_W >= P_HP_max_W:
            Q_to_storage_W = P_HP_max_W
            # print "Storage charging at full power!"

        if Q_from_storage_W >= P_HP_max_W:
            Q_from_storage_W = P_HP_max_W
            # print "Storage discharging at full power!"

    return Q_to_storage_W, Q_from_storage_W, to_storage, Q_server_to_directload_W, Q_server_to_storage_W, Q_compair_to_directload_W, Q_compair_to_storage_W, Q_PVT_to_directload_W, Q_PVT_to_storage_W, Q_SC_to_directload_W, Q_SC_to_storage_W


def Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_return_DH, gv):
    """
    USE ONLY IF Q solar is not sufficient!
    This function derives the temperature just before the power plant, after solar energy is injected.

    :param Q_network_demand: network load at a given time step
    :param Q_solar_available: solar energy available at a given time step
    :param mdot_DH: ??
    :param T_return_DH: ??
    :param gv: global variables
    :type Q_network_demand: float
    :type Q_solar_available: float
    :type mdot_DH: float
    :type T_return_DH: float
    :type gv: class
    :return: temperature before powerplant
    :rtype: float
    """

    if Q_network_demand < Q_solar_available:
        T_before_PP = T_return_DH

    T_before_PP = T_return_DH + Q_solar_available / (mdot_DH * gv.cp)

    return T_before_PP


def Storage_Charger(T_storage_old_K, Q_to_storage_lossfree_W, T_DH_ret_K, Q_in_storage_old_W, STORAGE_SIZE_m3, context,
                    gv):
    """
    calculates the temperature of storage when charging
    Q_to_storage_new = including losses

    :param T_storage_old_K:
    :param Q_to_storage_lossfree_W:
    :param T_DH_ret_K:
    :param Q_in_storage_old_W:
    :param STORAGE_SIZE_m3:
    :param context:
    :param gv:
    :type T_storage_old_K: float
    :type Q_to_storage_lossfree_W: float
    :type T_DH_ret_K: float
    :type Q_in_storage_old_W: float
    :type STORAGE_SIZE_m3: float
    :type context: string
    :type gv: class
    :return: T_storage_new, Q_to_storage_new, E_aux, Q_in_storage_new ??
    :rtype: float, float, float, float ??
    """
    MS_Var = context

    if T_storage_old_K > T_DH_ret_K:
        COP_th = T_storage_old_K / (T_storage_old_K - T_DH_ret_K)
        COP = HP_etaex * COP_th
        E_aux_W = Q_to_storage_lossfree_W * (1 + MS_Var.Storage_conv_loss) * (
                1 / COP)  # assuming the losses occur after the heat pump
        Q_to_storage_new = (E_aux_W + Q_to_storage_lossfree_W) * (1 - MS_Var.Storage_conv_loss)
        # print "HP operation Charging"
    else:
        E_aux_W = 0
        Q_to_storage_new = Q_to_storage_lossfree_W * (1 - MS_Var.Storage_conv_loss)
        # print "HEX charging"

    Q_in_storage_new_W = Q_in_storage_old_W + Q_to_storage_new

    T_storage_new_K = MS_Var.T_storage_zero + Q_in_storage_new_W * gv.Wh_to_J / (
            float(STORAGE_SIZE_m3) * float(gv.cp) * float(gv.rho_60))

    return T_storage_new_K, Q_to_storage_new, E_aux_W, Q_in_storage_new_W


def Storage_DeCharger(T_storage_old_K, Q_from_storage_req_W, T_DH_sup_K, Q_in_storage_old_W, STORAGE_SIZE, context, gv):
    """
    discharging of the storage, no outside thermal losses  in the model

    :param T_storage_old_K:
    :param Q_from_storage_req_W:
    :param T_DH_sup_K:
    :param Q_in_storage_old_W:
    :param STORAGE_SIZE:
    :param context:
    :param gv:
    :type T_storage_old_K:
    :type Q_from_storage_req_W:
    :type T_DH_sup_K:
    :type Q_in_storage_old_W:
    :type STORAGE_SIZE:
    :type context:
    :type gv:
    :return:
    :rtype:
    """

    MS_Var = context
    if T_DH_sup_K > T_storage_old_K:  # using a heat pump if the storage temperature is below the desired distribution temperature

        COP_th = T_DH_sup_K / (T_DH_sup_K - T_storage_old_K)  # take average temp of old and new as low temp
        COP = HP_etaex * COP_th
        # print COP
        E_aux_W = Q_from_storage_req_W / COP * (1 + MS_Var.Storage_conv_loss)
        Q_from_storage_used_W = Q_from_storage_req_W * (1 - 1 / COP) * (1 + MS_Var.Storage_conv_loss)
        # print "HP operation de-Charging"
        # print  "Wh used from Storage", Q_from_storage_used



    else:  # assume perfect heat exchanger that provides the heat to the distribution
        Q_from_storage_used_W = Q_from_storage_req_W * (1 + MS_Var.Storage_conv_loss)
        E_aux_W = 0.0
        COP = 0.0
        # print "HEX-Operation Decharging"

    Q_in_storage_new_W = Q_in_storage_old_W - Q_from_storage_used_W

    T_storage_new_K = MS_Var.T_storage_zero + Q_in_storage_new_W * gv.Wh_to_J / (
            float(STORAGE_SIZE) * float(gv.cp) * float(gv.rho_60))

    # print Q_in_storage_new, "energy in storage left"

    return E_aux_W, Q_from_storage_used_W, Q_in_storage_new_W, T_storage_new_K, COP


def Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, gv):
    """
    Calculates the storage Loss for every time step, assume  D : H = 3 : 1
    
    :param T_storage_old_K: temperature of storage at time step, without any losses
    :param T_amb_K: ambient temperature
    :param STORAGE_SIZE_m3:
    :param context:
    :param gv: global variables
    :type T_storage_old_K: float
    :type T_amb_K: float
    :type STORAGE_SIZE_m3: float
    :type context:
    :type gv: class
    :return: Energy loss due to non perfect insulation in Wh/h
    :rtype: float
    """
    MS_Var = context

    V_storage_m3 = STORAGE_SIZE_m3

    H_storage_m = (2.0 * V_storage_m3 / (9.0 * np.pi)) ** (1.0 / 3.0)  # assume 3 : 1 (D : H)
    # D_storage = 3.0 * H_storage

    A_storage_ground_m2 = V_storage_m3 / H_storage_m

    if V_storage_m3 == 0:
        A_storage_rest_m2 = 0
    else:
        A_storage_rest_m2 = 2.0 * (H_storage_m * np.pi * V_storage_m3) ** (1.0 / 2.0)

    Q_loss_uppersurf_W = MS_Var.alpha_loss * A_storage_ground_m2 * (T_storage_old_K - T_amb_K)
    Q_loss_rest_W = MS_Var.alpha_loss * A_storage_rest_m2 * (T_storage_old_K - TGround)  # calculated by EnergyPRO
    Q_loss_W = float(Q_loss_uppersurf_W + Q_loss_rest_W)
    T_loss_K = float(Q_loss_W / (STORAGE_SIZE_m3 * gv.cp * gv.rho_60 * gv.Wh_to_J))

    return Q_loss_W, T_loss_K


def Storage_Operator(Q_PVT_gen_W, Q_SC_gen_W, Q_server_gen_W, Q_compair_gen_W, Q_network_demand_W, T_storage_old_K,
                     T_DH_sup_K, T_amb_K, Q_in_storage_old_W,
                     T_DH_return_K, \
                     mdot_DH_kgpers, STORAGE_SIZE_m3, context, P_HP_max_W, gv):
    """
    :param Q_solar_available_Wh:
    :param Q_network_demand_W:
    :param T_storage_old_K:
    :param T_DH_sup_K:
    :param T_amb_K:
    :param Q_in_storage_old_W:
    :param T_DH_return_K:
    :param mdot_DH_kgpers:
    :param STORAGE_SIZE_m3:
    :param context:
    :param P_HP_max_W:
    :param gv:
    :type Q_solar_available_Wh:
    :type Q_network_demand_W:
    :type T_storage_old_K:
    :type T_DH_sup_K:
    :type T_amb_K:
    :type Q_in_storage_old_W:
    :type T_DH_return_K:
    :type mdot_DH_kgpers:
    :type STORAGE_SIZE_m3:
    :type context:
    :type P_HP_max_W:
    :type gv:
    :return:
    :rtype:
    """

    Q_to_storage_W, Q_from_storage_req_W, to_storage, Q_server_to_directload_W, Q_server_to_storage_W, Q_compair_to_directload_W, Q_compair_to_storage_W, Q_PVT_to_directload, Q_PVT_to_storage_W, Q_SC_to_directload_W, Q_SC_to_storage_W = StorageGateway(
        Q_PVT_gen_W, Q_SC_gen_W, Q_server_gen_W,
        Q_compair_gen_W, Q_network_demand_W,
        P_HP_max_W)
    Q_missing_W = 0
    Q_from_storage_used_W = 0
    E_aux_dech_W = 0
    E_aux_ch_W = 0
    mdot_DH_missing_kgpers = Q_network_demand_W

    if to_storage == 1:  # charging the storage

        T_storage_new_K, Q_to_storage_new_W, E_aux_ch_W, Q_in_storage_new_W = \
            Storage_Charger(T_storage_old_K, Q_to_storage_W, T_DH_return_K, Q_in_storage_old_W, STORAGE_SIZE_m3,
                            context, gv)
        Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, gv)
        T_storage_new_K -= T_loss_K
        Q_in_storage_new_W -= Q_loss_W
        Q_from_storage_used_W = 0
        mdot_DH_missing_kgpers = 0


    else:  # DECHARGE     #elif Q_in_storage_old > 0: #and T_storage_old > gv.T_storage_min: # de-charging the storage is possible

        if Q_in_storage_old_W > 0:  # Start de-Charging
            E_aux_dech_W, Q_from_storage_used_W, Q_in_storage_new_W, T_storage_new_K, COP = \
                Storage_DeCharger(T_storage_old_K, Q_from_storage_req_W, T_DH_sup_K, Q_in_storage_old_W,
                                  STORAGE_SIZE_m3, context, gv)

            Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, gv)
            T_storage_new_K -= T_loss_K
            Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W - Q_from_storage_used_W

            if Q_network_demand_W == 0:
                mdot_DH_missing_kgpers = 0
            else:
                mdot_DH_missing_kgpers = mdot_DH_kgpers * (
                        Q_network_demand_W - Q_from_storage_used_W) / Q_network_demand_W

            if Q_in_storage_new_W < 0:  # if storage is almost empty, to not go below 10 degC, just do not provide more energy than possible.
                # T_storage_new = gv.T_storage_min
                # Q_from_storage_1 = math.floor((MS_Var.STORAGE_SIZE * gv.cp * gv.rho_60 * 1/gv.Wh_to_J) * (T_storage_old - T_storage_new))
                Q_from_storage_poss = Q_in_storage_old_W
                Q_missing_W = Q_network_demand_W - (
                        Q_PVT_gen_W + Q_SC_gen_W + Q_server_gen_W + Q_compair_gen_W) - Q_from_storage_poss
                # Q_from_storage_poss = min(Q_from_storage_1, Q_from_storage_2)
                # print Q_from_storage_poss, "taken from storage as max"

                if Q_missing_W < 0:  # catch numerical errors (leading to very low (absolute) negative numbers)
                    Q_missing_W = 0

                E_aux_dech_W, Q_from_storage_used_W, Q_in_storage_new_W, T_storage_new_K, COP = \
                    Storage_DeCharger(T_storage_old_K, Q_from_storage_poss, T_DH_sup_K, Q_in_storage_old_W,
                                      STORAGE_SIZE_m3, context, gv)

                # print "limited decharging"

                Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, gv)

                """
                # CURRENTLY NOT USED
                if T_storage_new < gv.T_storage_min:
                    print "error at limited decharging"
                    print T_storage_old -273, "T_storage_old"
                    Q_from_storage_used = 0 
                """

                Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W - Q_from_storage_used_W
                T_storage_new_K -= T_loss_K

                if Q_network_demand_W == 0:
                    mdot_DH_missing_kgpers = 0
                else:
                    mdot_DH_missing_kgpers = mdot_DH_kgpers * Q_missing_W / Q_network_demand_W

        else:  # neither storage  charging nor decharging
            E_aux_ch_W = 0
            E_aux_dech_W = 0
            Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, gv)
            T_storage_new_K = T_storage_old_K - T_loss_K
            Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W
            Q_missing_W = Q_network_demand_W - (Q_PVT_gen_W + Q_SC_gen_W + Q_server_gen_W + Q_compair_gen_W)
            if Q_missing_W < 0:  # catch numerical errors (leading to very low (absolute) negative numbers)
                Q_missing_W = 0
            if Q_network_demand_W == 0:
                mdot_DH_missing_kgpers = 0
            else:
                mdot_DH_missing_kgpers = mdot_DH_kgpers * (Q_missing_W) / Q_network_demand_W

            # print "mdot_DH_missing", mdot_DH_missing

    return Q_in_storage_new_W, T_storage_new_K, Q_from_storage_req_W, Q_to_storage_W, E_aux_ch_W, E_aux_dech_W, \
           Q_missing_W, Q_from_storage_used_W, Q_loss_W, mdot_DH_missing_kgpers, Q_server_to_directload_W, Q_server_to_storage_W, \
           Q_compair_to_directload_W, Q_compair_to_storage_W, Q_PVT_to_directload, Q_PVT_to_storage_W, Q_SC_to_directload_W, Q_SC_to_storage_W
