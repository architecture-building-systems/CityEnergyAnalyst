"""
Slave Sub Function - Treat solar power!
In this file, all sub-functions are stored that are used for storage design and operation. 
They are called by either the operation or optimization of storage.
"""

import numpy as np

from cea.constants import *
from cea.optimization.constants import *


def StorageGateway(Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W, Q_server_gen_W, Q_network_demand_W, P_HP_max_W):
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

    Q_SC_FP_to_directload_W = 0
    Q_SC_FP_to_storage_W = 0
    Q_to_storage_W = 0
    storage_active_flag = 0

    if Q_server_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_server_gen_W
        Q_server_to_directload_W = Q_server_gen_W
        Q_server_to_storage_W = 0

    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_server_gen_W, 0)
        Q_to_storage_W = Q_to_storage_W + Q_server_gen_W - Q_network_demand_W  + Q_PVT_gen_W + Q_SC_ET_gen_W + Q_SC_FP_gen_W
        storage_active_flag = 1
        Q_server_to_directload_W = Q_network_demand_W
        Q_server_to_storage_W = Q_server_gen_W - Q_network_demand_W
        Q_PVT_to_directload_W = 0
        Q_PVT_to_storage_W = Q_PVT_gen_W
        Q_SC_ET_to_directload_W = 0
        Q_SC_ET_to_storage_W = Q_SC_ET_gen_W
        Q_SC_FP_to_directload_W = 0
        Q_SC_FP_to_storage_W = Q_SC_FP_gen_W

    if Q_PVT_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_PVT_gen_W
        Q_PVT_to_directload_W = Q_PVT_gen_W
        Q_PVT_to_storage_W = 0
    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_PVT_gen_W, 0)
        Q_to_storage_W = Q_to_storage_W +  Q_PVT_gen_W - Q_network_demand_W + Q_SC_ET_gen_W + Q_SC_FP_gen_W
        storage_active_flag = 1
        Q_PVT_to_directload_W = Q_network_demand_W
        Q_PVT_to_storage_W = Q_PVT_gen_W - Q_network_demand_W
        Q_SC_ET_to_directload_W = 0
        Q_SC_ET_to_storage_W = Q_SC_ET_gen_W
        Q_SC_FP_to_directload_W = 0
        Q_SC_FP_to_storage_W = Q_SC_FP_gen_W

    if Q_SC_ET_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_SC_ET_gen_W
        Q_SC_ET_to_directload_W = Q_SC_ET_gen_W
        Q_SC_ET_to_storage_W = 0
    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_SC_ET_gen_W, 0)
        Q_to_storage_W = Q_to_storage_W + Q_SC_ET_gen_W - Q_network_demand_W
        storage_active_flag = 1
        Q_SC_ET_to_directload_W = Q_network_demand_W
        Q_SC_ET_to_storage_W = Q_SC_ET_gen_W - Q_network_demand_W
        Q_SC_FP_to_directload_W = 0
        Q_SC_FP_to_storage_W = Q_SC_FP_gen_W

    if Q_SC_FP_gen_W <= Q_network_demand_W:
        Q_network_demand_W = Q_network_demand_W - Q_SC_FP_gen_W
    else:
        Q_network_demand_W = max(Q_network_demand_W - Q_SC_FP_gen_W, 0)
        Q_to_storage_W = Q_to_storage_W + Q_SC_FP_gen_W - Q_network_demand_W
        storage_active_flag = 1
        Q_SC_FP_to_directload_W = Q_network_demand_W
        Q_SC_FP_to_storage_W = Q_SC_FP_gen_W - Q_network_demand_W

    Q_from_storage_W = Q_network_demand_W

    if Q_to_storage_W < (Q_PVT_to_storage_W + Q_SC_FP_to_storage_W + Q_SC_ET_to_storage_W):
        print (Q_to_storage_W)

    if STORAGE_MAX_UPTAKE_LIMIT_FLAG == 1:
        if Q_to_storage_W >= P_HP_max_W:
            Q_to_storage_W = P_HP_max_W
            # print "Storage charging at full power!"

        if Q_from_storage_W >= P_HP_max_W:
            Q_from_storage_W = P_HP_max_W
            # print "Storage discharging at full power!"
    return Q_to_storage_W, \
           Q_from_storage_W, \
           storage_active_flag, \
           Q_server_to_directload_W, \
           Q_server_to_storage_W, \
           Q_PVT_to_directload_W, \
           Q_PVT_to_storage_W, \
           Q_SC_ET_to_directload_W, \
           Q_SC_ET_to_storage_W, \
           Q_SC_FP_to_directload_W, \
           Q_SC_FP_to_storage_W


def Temp_before_Powerplant(Q_network_demand, Q_solar_available, mdot_DH, T_return_DH):
    """
    USE ONLY IF Q solar is not sufficient!
    This function derives the temperature just before the power plant, after solar energy is injected.

    :param Q_network_demand: network load at a given time step
    :param Q_solar_available: solar energy available at a given time step
    :param mdot_DH: ??
    :param T_return_DH: ??
    :type Q_network_demand: float
    :type Q_solar_available: float
    :type mdot_DH: float
    :type T_return_DH: float
    :return: temperature before powerplant
    :rtype: float
    """

    if Q_network_demand < Q_solar_available:
        T_before_PP = T_return_DH

    T_before_PP = T_return_DH + Q_solar_available / (mdot_DH * HEAT_CAPACITY_OF_WATER_JPERKGK)

    return T_before_PP


def Storage_Charger(T_storage_old_K, Q_to_storage_lossfree_W, T_DH_ret_K, Q_in_storage_old_W, STORAGE_SIZE_m3, context):
    """
    calculates the temperature of storage when charging
    Q_to_storage_new_W = including losses

    :param T_storage_old_K:
    :param Q_to_storage_lossfree_W:
    :param T_DH_ret_K:
    :param Q_in_storage_old_W:
    :param STORAGE_SIZE_m3:
    :param context:
    :type T_storage_old_K: float
    :type Q_to_storage_lossfree_W: float
    :type T_DH_ret_K: float
    :type Q_in_storage_old_W: float
    :type STORAGE_SIZE_m3: float
    :type context: string
    :return: T_storage_new, Q_to_storage_new_W, E_aux, Q_in_storage_new ??
    :rtype: float, float, float, float ??
    """
    MS_Var = context

    if T_storage_old_K > T_DH_ret_K:
        COP_th = T_storage_old_K / (T_storage_old_K - T_DH_ret_K)
        COP = HP_ETA_EX * COP_th
        E_aux_W = Q_to_storage_lossfree_W * (1 + MS_Var.Storage_conv_loss) * (
                1 / COP)  # assuming the losses occur after the heat pump
        Q_to_storage_new_W = (E_aux_W + Q_to_storage_lossfree_W) * (1 - MS_Var.Storage_conv_loss)
        # print "HP operation Charging"
    else:
        E_aux_W = 0
        Q_to_storage_new_W = Q_to_storage_lossfree_W * (1 - MS_Var.Storage_conv_loss)
        # print "HEX charging"

    Q_in_storage_new_W = Q_in_storage_old_W + Q_to_storage_new_W

    T_storage_new_K = MS_Var.T_storage_zero + Q_in_storage_new_W * WH_TO_J / (
            float(STORAGE_SIZE_m3) * float(HEAT_CAPACITY_OF_WATER_JPERKGK) * float(DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3))

    return T_storage_new_K, Q_to_storage_new_W, E_aux_W, Q_in_storage_new_W


def Storage_DeCharger(T_storage_old_K, Q_from_storage_req_W, T_DH_sup_K, Q_in_storage_old_W, STORAGE_SIZE, context):
    """
    discharging of the storage, no outside thermal losses  in the model

    :param T_storage_old_K:
    :param Q_from_storage_req_W:
    :param T_DH_sup_K:
    :param Q_in_storage_old_W:
    :param STORAGE_SIZE:
    :param context:
    :type T_storage_old_K:
    :type Q_from_storage_req_W:
    :type T_DH_sup_K:
    :type Q_in_storage_old_W:
    :type STORAGE_SIZE:
    :type context:
    :return:
    :rtype:
    """

    MS_Var = context
    if T_DH_sup_K > T_storage_old_K:  # using a heat pump if the storage temperature is below the desired distribution temperature

        COP_th = T_DH_sup_K / (T_DH_sup_K - T_storage_old_K)  # take average temp of old and new as low temp
        COP = HP_ETA_EX * COP_th
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

    T_storage_new_K = MS_Var.T_storage_zero + Q_in_storage_new_W * WH_TO_J / (
            float(STORAGE_SIZE) * float(HEAT_CAPACITY_OF_WATER_JPERKGK) * float(DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3))

    # print Q_in_storage_new, "energy in storage left"

    return E_aux_W, Q_from_storage_used_W, Q_in_storage_new_W, T_storage_new_K, COP


def Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, T_ground):
    """
    Calculates the storage Loss for every time step, assume  D : H = 3 : 1
    
    :param T_storage_old_K: temperature of storage at time step, without any losses
    :param T_amb_K: ambient temperature
    :param STORAGE_SIZE_m3:
    :param context:
    :type T_storage_old_K: float
    :type T_amb_K: float
    :type STORAGE_SIZE_m3: float
    :type context:
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
    Q_loss_rest_W = MS_Var.alpha_loss * A_storage_rest_m2 * (T_storage_old_K - T_ground)  # calculated by EnergyPRO
    Q_loss_W = abs(float(Q_loss_uppersurf_W + Q_loss_rest_W))
    T_loss_K = abs(float(Q_loss_W / (STORAGE_SIZE_m3 * HEAT_CAPACITY_OF_WATER_JPERKGK * DENSITY_OF_WATER_AT_60_DEGREES_KGPERM3 * WH_TO_J)))

    return Q_loss_W, T_loss_K


def Storage_Operator(Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W, Q_server_gen_W, Q_network_demand_W,
                     T_storage_old_K, T_DH_sup_K, T_amb_K, Q_in_storage_old_W, T_DH_return_K,
                     mdot_DH_kgpers, STORAGE_SIZE_m3, context, P_HP_max_W, T_ground_K):
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
    :return:
    :rtype:
    """

    Q_to_storage_W, \
    Q_from_storage_W, \
    storage_active_flag, \
    Q_server_to_directload_W, \
    Q_server_to_storage_W, \
    Q_PVT_to_directload_W, \
    Q_PVT_to_storage_W, \
    Q_SC_ET_to_directload_W, \
    Q_SC_ET_to_storage_W, \
    Q_SC_FP_to_directload_W, \
    Q_SC_FP_to_storage_W = StorageGateway(Q_PVT_gen_W, Q_SC_ET_gen_W, Q_SC_FP_gen_W,
                                                                   Q_server_gen_W, Q_network_demand_W,
                                                                   P_HP_max_W)

    Q_missing_W = 0 # amount of heat required from heating plants
    Q_from_storage_req_W = 0
    E_aux_dech_W = 0
    E_aux_ch_W = 0
    # mdot_DH_missing_kgpers = Q_network_demand_W # TODO: TO DELETE

    if storage_active_flag == 1:  # charging the storage

        T_storage_new_K, Q_to_storage_new_W, E_aux_ch_W, Q_in_storage_new_W = \
            Storage_Charger(T_storage_old_K, Q_to_storage_W, T_DH_return_K, Q_in_storage_old_W, STORAGE_SIZE_m3,
                            context)
        # calculating thermal loss
        Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, T_ground_K)
        T_storage_new_K -= T_loss_K
        Q_in_storage_new_W -= Q_loss_W

        Q_from_storage_req_W = 0
        mdot_DH_missing_kgpers = 0
    else:  # discharging the storage
        if Q_in_storage_old_W > 0.0:  # Start de-Charging
            E_aux_dech_W, Q_from_storage_req_W, Q_in_storage_new_W, T_storage_new_K, COP = \
                Storage_DeCharger(T_storage_old_K, Q_from_storage_W, T_DH_sup_K, Q_in_storage_old_W,
                                  STORAGE_SIZE_m3, context)
            # calculating thermal loss
            Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, T_ground_K)
            T_storage_new_K -= T_loss_K
            Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W - Q_from_storage_req_W

            if Q_network_demand_W == 0:
                mdot_DH_missing_kgpers = 0
            else:
                mdot_DH_missing_kgpers = mdot_DH_kgpers * (Q_network_demand_W - Q_from_storage_req_W) / Q_network_demand_W # TODO: CHECK CALCULATION

            if Q_in_storage_new_W < 0:
                # if storage is almost empty after the discharge calculation, only discharge the amount that is possible
                # to not go below 10 degC
                Q_from_storage_poss = Q_in_storage_old_W
                E_aux_dech_W, Q_from_storage_req_W, Q_in_storage_new_W, T_storage_new_K, COP = \
                    Storage_DeCharger(T_storage_old_K, Q_from_storage_poss, T_DH_sup_K, Q_in_storage_old_W,
                                      STORAGE_SIZE_m3, context)

                Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, T_ground_K)
                Q_missing_W = Q_network_demand_W - (Q_PVT_to_directload_W +
                                                    Q_SC_ET_to_directload_W +
                                                    Q_SC_FP_to_directload_W +
                                                    Q_server_to_directload_W) - Q_from_storage_req_W

                Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W - Q_from_storage_req_W
                T_storage_new_K -= T_loss_K

                if Q_network_demand_W == 0:
                    mdot_DH_missing_kgpers = 0
                else:
                    mdot_DH_missing_kgpers = mdot_DH_kgpers * (Q_missing_W / Q_network_demand_W)

        else:  # neither storage  charging nor decharging
            E_aux_ch_W = 0
            E_aux_dech_W = 0
            Q_loss_W, T_loss_K = Storage_Loss(T_storage_old_K, T_amb_K, STORAGE_SIZE_m3, context, T_ground_K)
            T_storage_new_K = T_storage_old_K - T_loss_K
            Q_in_storage_new_W = Q_in_storage_old_W - Q_loss_W
            Q_missing_W = Q_network_demand_W - (Q_PVT_to_directload_W +
                                                Q_SC_ET_to_directload_W +
                                                Q_SC_FP_to_directload_W +
                                                Q_server_to_directload_W
                                                )
            if Q_missing_W < 0:  # catch numerical errors (leading to very low (absolute) negative numbers)
                Q_missing_W = 0
            if Q_network_demand_W == 0:
                mdot_DH_missing_kgpers = 0
            else:
                mdot_DH_missing_kgpers = mdot_DH_kgpers * (Q_missing_W / Q_network_demand_W)

            # print "mdot_DH_missing", mdot_DH_missing

    return Q_in_storage_new_W, \
           T_storage_new_K,\
           Q_from_storage_req_W,\
           Q_to_storage_W, \
           E_aux_ch_W,\
           E_aux_dech_W, \
           Q_missing_W, \
           Q_loss_W,\
           mdot_DH_missing_kgpers, \
           Q_server_to_directload_W,\
           Q_server_to_storage_W, \
           Q_PVT_to_directload_W, \
           Q_PVT_to_storage_W, \
           Q_SC_ET_to_directload_W,\
           Q_SC_ET_to_storage_W, \
           Q_SC_FP_to_directload_W, \
           Q_SC_FP_to_storage_W
