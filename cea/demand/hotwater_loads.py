"""
Hotwater load (it also calculates fresh water needs)
"""

from __future__ import division
from cea.constants import *
import numpy as np
import scipy
import math
from math import pi
from cea.demand import constants
from cea.technologies import storage_tank as storage_tank
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# import constants
D = constants.D
B_F = constants.B_F
P_WATER = P_WATER_KGPERM3
FLOWTAP = constants.FLOWTAP
CP_KJPERKGK = HEAT_CAPACITY_OF_WATER_JPERKGK / 1000
TWW_SETPOINT = constants.TWW_SETPOINT


def calc_mww(schedule, water_lpd):
    """
    Algorithm to calculate the hourly mass flow rate of water

    :param schedule: hourly DHW demand profile [person/d.h]
    :param water_lpd: water emand per person per day in [L/person/day]
    """

    if schedule > 0:

        volume = schedule * water_lpd / 1000  # m3/h
        massflow = volume * P_WATER / 3600  # in kg/s

    else:
        volume = 0
        massflow = 0

    return massflow, volume


# final hot water demand calculation


def calc_water_temperature(T_ambient_C, depth_m):
    """
    Calculates hourly ground temperature fluctuation over a year following [Kusuda, T. et al., 1965]_.
    ..[Kusuda, T. et al., 1965] Kusuda, T. and P.R. Achenbach (1965). Earth Temperatures and Thermal Diffusivity at
    Selected Stations in the United States. ASHRAE Transactions. 71(1):61-74
    """
    heat_capacity_soil = 2000  # _[A. Kecebas et al., 2011]
    conductivity_soil = 1.6  # _[A. Kecebas et al., 2011]
    density_soil = 1600  # _[A. Kecebas et al., 2011]

    T_max = max(T_ambient_C) + 273.15  # to K
    T_avg = np.mean(T_ambient_C) + 273.15  # to K
    e = depth_m * math.sqrt(
        (math.pi * heat_capacity_soil * density_soil) / (8760 * conductivity_soil))  # soil constants
    Tg = [(T_avg + (T_max - T_avg) * math.exp(-e) * math.cos((2 * math.pi * (i + 1) / 8760) - e)) - 274
          for i in range(8760)]

    return Tg  # in C


def calc_Qww_sys(bpr, tsd):
    # Refactored from CalcThermalLoads
    """
    This function calculates the distribution heat loss and final energy consumption of domestic hot water.
    Final energy consumption of dhw includes dhw demand, sensible heat loss in hot water storage tank, and heat loss in the distribution network.
    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :return: modifies tsd
    :rtype: None
    :return: mcp_tap_water_kWperK: tap water capacity masss flow rate in kW_C
    """

    Lcww_dis = bpr.building_systems['Lcww_dis']
    Lsww_dis = bpr.building_systems['Lsww_dis']
    Lvww_c = bpr.building_systems['Lvww_c']
    Lvww_dis = bpr.building_systems['Lvww_dis']
    T_ext_C = tsd['T_ext']
    T_int_C = tsd['T_int']
    Tww_sup_0_C = bpr.building_systems['Tww_sup_0']
    Y = bpr.building_systems['Y']
    Qww_nom_W = tsd['Qww'].max()

    # distribution and circulation losses
    V_dist_pipes_m3 = Lsww_dis * ((D / 1000) / 2) ** 2 * pi  # m3, volume inside distribution pipe
    Qww_dis_ls_r_W = np.vectorize(calc_Qww_dis_ls_r)(T_int_C, tsd['Qww'].copy(), Lsww_dis, Lcww_dis, Y[1], Qww_nom_W,
                                                 V_dist_pipes_m3,Tww_sup_0_C)
    Qww_dis_ls_nr_W = np.vectorize(calc_Qww_dis_ls_nr)(T_int_C, tsd['Qww'].copy(), Lvww_dis, Lvww_c, Y[0], Qww_nom_W,
                                                   V_dist_pipes_m3,Tww_sup_0_C, T_ext_C)
    # storage losses
    Tww_tank_C, tsd['Qww_sys'] = calc_DH_ww_with_tank_losses(T_ext_C, T_int_C, tsd['Qww'].copy(), tsd['vww_m3perh'],
                                                            Qww_dis_ls_r_W, Qww_dis_ls_nr_W)

    tsd['mcpww_sys'] = tsd['Qww_sys'] / abs(Tww_tank_C - tsd['Tww_re'])

    # erase points where the load is zero
    tsd['Tww_sys_sup'] = [0.0 if x <= 0.0 else y for x, y in zip(tsd['Qww'], Tww_tank_C)]
    tsd['Tww_sys_re'] = [0.0 if x <= 0.0 else y for x, y in zip(tsd['Qww'], tsd['Tww_re'])]

    return tsd

# end-use hot water demand calculation

def calc_Qww(bpr, tsd, schedules):
    """
    Calculates the DHW demand according to the supply temperature and flow rate.
    :param mdot_dhw_kgpers: required DHW flow rate in [kg/s]
    :param T_dhw_sup_C: Domestic hot water supply set point temperature.
    :param T_dhw_re_C: Domestic hot water tank return temperature in C, this temperature is the ground water temperature, set according to norm.
    :param Cpw: heat capacity of water [kJ/kgK]
    :return Q_dhw_W: Heat demand for DHW in [W]
    """

    def function(mdot_dhw_kgpers, T_dhw_sup_C, T_dhw_re_C):
        mcp_dhw_WperK = mdot_dhw_kgpers * CP_KJPERKGK * 1000  # W/K
        return mcp_dhw_WperK * (T_dhw_sup_C - T_dhw_re_C)  # heating for dhw in W

    tsd['Tww_re'] = calc_water_temperature(tsd['T_ext'], depth_m=1)
    Tww_sup_0_C = bpr.building_systems['Tww_sup_0']

    # calc end-use demand
    tsd['vww_m3perh'] = schedules['Vww'] * bpr.internal_loads['Vww_lpd'] / 1000  # m3/h
    tsd['mww'] = tsd['vww_m3perh'] * P_WATER / 3600  # kg/s
    tsd['mcptw'] = (tsd['vfw_m3perh'] - tsd['vww_m3perh']) * CP_KJPERKGK * P_WATER / 3600  # kW_K tap water

    tsd['Qww'] = np.vectorize(function)(tsd['mww'], Tww_sup_0_C, tsd['Tww_re'])

    return tsd


# final hot water demand calculation
def calc_Qwwf(bpr, tsd):

    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply["source_dhw"]
    scale_technology = bpr.supply['scale_dhw']
    efficiency_average_year = bpr.supply["eff_dhw"]

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            tsd['E_ww'] =  tsd['Qww_sys']/ efficiency_average_year
            tsd['SOLAR_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
        elif energy_source == "NATURALGAS":
            tsd['NG_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
        elif energy_source == "OIL":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
        elif energy_source == "COAL":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
        elif energy_source == "WOOD":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
        elif energy_source == "SOLAR":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
        elif energy_source == "NONE":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / HOTWATER')
    elif scale_technology == "DISTRICT":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = tsd['Qww_sys'] / efficiency_average_year
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
    elif scale_technology == "NONE":
            tsd['NG_ww'] = np.zeros(8760)
            tsd['COAL_ww'] = np.zeros(8760)
            tsd['OIL_ww'] = np.zeros(8760)
            tsd['WOOD_ww'] = np.zeros(8760)
            tsd['DH_ww'] = np.zeros(8760)
            tsd['E_ww'] = np.zeros(8760)
            tsd['SOLAR_ww'] = np.zeros(8760)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / HOTWATER')


    return tsd


def calc_Qww_dis_ls_r(Tair, Qww, Lsww_dis, Lcww_dis, Y, Qww_0, V, twws):
    if Qww > 0:
        # Calculate tamb in basement according to EN
        tamb = Tair

        # Circulation circuit losses
        circ_ls = (twws - tamb) * Y * Lcww_dis * (Qww / Qww_0)

        # Distribtution circuit losses
        dis_ls = calc_disls(tamb, Qww, V, twws, Lsww_dis, Y)

        Qww_d_ls_r = circ_ls + dis_ls
    else:
        Qww_d_ls_r = 0
    return Qww_d_ls_r


def calc_Qww_dis_ls_nr(tair, Qww, Lvww_dis, Lvww_c, Y, Qww_0, V, twws, te):
    """

    :param tair:
    :param Qww:
    :param Lvww_dis:
    :param Lvww_c:
    :param Y:
    :param Qww_0:
    :param V:
    :param twws:
    :param te:
    :return:
    """
    # TODO: documentation
    # date: legacy

    if Qww > 0:
        # Calculate tamb in basement according to EN
        tamb = tair - B_F * (tair - te)

        # Circulation losses
        d_circ_ls = (twws - tamb) * Y * (Lvww_c) * (Qww / Qww_0)

        # Distribution losses
        d_dis_ls = calc_disls(tamb, Qww, V, twws, Lvww_dis, Y)
        Qww_d_ls_nr = d_dis_ls + d_circ_ls
    else:
        Qww_d_ls_nr = 0
    return Qww_d_ls_nr


def calc_disls(tamb, Vww, V, twws, Lsww_dis, Y):
    """
    Calculates distribution losses in Wh according to Fonseca & Schlueter (2015) Eq. 24, which is in turn based
    on Annex A of ISO EN 15316 with pipe mass m_p,dis = 0.
    
    :param tamb: Room temperature in C
    :param Vww: volumetric flow rate of hot water demand (in m3)
    :param V: volume of water accumulated in the distribution network in m3
    :param twws: Domestic hot water supply set point temperature in C
    :param Lsww_dis: length of circulation/distribution pipeline in m
    :param p: water density kg/m3
    :param cpw: heat capacity of water in kJ/kgK
    :param Y: linear trasmissivity coefficient of piping in distribution network in W/m*K

    :return losses: recoverable/non-recoverable losses due to distribution of DHW
    """
    if Vww > 0:
        TR = 3600 / ((Vww / 1000) / FLOWTAP)  # Thermal response of insulated piping
        if TR > 3600:
            TR = 3600
        try:
            exponential = scipy.exp(-(Y * Lsww_dis * TR) / (P_WATER * CP_KJPERKGK * V * 1000))
        except ZeroDivisionError:
            print('twws: {twws:.2f}, tamb: {tamb:.2f}, p: {p:.2f}, cpw: {cpw:.2f}, V: {V:.2f}'.format(
                twws=twws, tamb=tamb, p=P_WATER, cpw=CP_KJPERKGK, V=V))
            raise ZeroDivisionError

        tamb = tamb + (twws - tamb) * exponential
        losses = (twws - tamb) * V * CP_KJPERKGK * P_WATER / 3.6  # in Wh
    else:
        losses = 0
    return losses


def calc_DH_ww_with_tank_losses(T_ext_C, T_int_C, Qww, Vww, Qww_dis_ls_r, Qww_dis_ls_nr):
    """
    Calculates the heat flows within a fully mixed water storage tank for 8760 time-steps.
    :param T_ext_C: external temperature in [C]
    :param T_int_C: room temperature in [C]
    :param Qww: hourly DHW demand in [Wh]
    :param Vww: hourly DHW demand in [m3]
    :param Qww_dis_ls_r: recoverable loss in distribution in [Wh]
    :param Qww_dis_ls_nr: non-recoverable loss in distribution in [Wh]
    :type T_ext_C: ndarray
    :type T_int_C: ndarray
    :type Qww: ndarray
    :type Vww: ndarray
    :type Qww_dis_ls_r: ndarray
    :type Qww_dis_ls_nr: ndarray
    :return:
    """
    Qww_sys = np.zeros(8760)
    Qww_st_ls = np.zeros(8760)
    Tww_tank_C = np.zeros(8760)
    Qd = np.zeros(8760)
    # calculate DHW tank size [in m3] based on the peak DHW demand in the building
    V_tank_m3 = Vww.max()  # size the tank with the highest flow rate
    T_tank_start_C = TWW_SETPOINT  # assume the tank temperature at timestep 0 is at the dhw set point

    if V_tank_m3 > 0:
        for k in range(8760):
            area_tank_surface_m2 = storage_tank.calc_tank_surface_area(V_tank_m3)
            Q_tank_discharged_W = Qww[k] + Qww_dis_ls_r[k] + Qww_dis_ls_nr[k]
            Qww_st_ls[k], Qd[k], Qww_sys[k] = storage_tank.calc_dhw_tank_heat_balance(T_int_C[k], T_ext_C[k],
                                                                                   T_tank_start_C, V_tank_m3,
                                                                                   Q_tank_discharged_W,
                                                                                   area_tank_surface_m2)
            Tww_tank_C[k] = storage_tank.calc_tank_temperature(T_tank_start_C, Qww_st_ls[k], Qd[k], Qww_sys[k], V_tank_m3,
                                                               'hot_water')
            T_tank_start_C = Tww_tank_C[k]  # update the tank temperature at the beginning of the next time step
    else:
        for k in range(8760):
            Tww_tank_C[k] = np.nan
    return Tww_tank_C, Qww_sys


def has_hot_water_technical_system(bpr):
    """
    Checks if building has a hot water system

    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
        """

    if bpr.hvac['type_dhw'] in {'T1', 'T2', 'T3', 'T4'}:  # 3for2
        return True
    elif bpr.hvac['type_dhw'] in {'T0'}:
        return False
    else:
        raise ValueError('Invalid value for type_dhw: %s' % bpr.hvac['type_dhw'])
