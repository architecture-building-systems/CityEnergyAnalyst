"""
Hotwater load (it also calculates fresh water needs)
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3
from cea.constants import HOURS_IN_YEAR
from cea.demand import constants
from cea.technologies import storage_tank as storage_tank

if TYPE_CHECKING:
    import numpy.typing as npt

    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

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


def calc_water_temperature(T_ambient_C: npt.NDArray[np.float64], depth_m: float) -> npt.NDArray[np.float64]:
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
    e = depth_m * np.sqrt(
        (np.pi * heat_capacity_soil * density_soil) / (HOURS_IN_YEAR * conductivity_soil))  # soil constants
    
    i = np.arange(HOURS_IN_YEAR)
    Tg = (T_avg + (T_max - T_avg) * np.exp(-e) * np.cos((2 * np.pi * (i + 1) / HOURS_IN_YEAR) - e)) - 274

    return Tg  # in C


def calc_Qww_sys(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    # Refactored from CalcThermalLoads
    """
    This function calculates the distribution heat loss and final energy consumption of domestic hot water.
    Final energy consumption of dhw includes dhw demand, sensible heat loss in hot water storage tank,
    and heat loss in the distribution network.
    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :return: modifies tsd
    :rtype: cea.demand.time_series_data.TimeSeriesData
    :return: mcp_tap_water_kWperK: tap water capacity masss flow rate in kW_C
    """

    Lcww_dis = bpr.building_systems['Lcww_dis']
    Lsww_dis = bpr.building_systems['Lsww_dis']
    Lvww_c = bpr.building_systems['Lvww_c']
    Lvww_dis = bpr.building_systems['Lvww_dis']
    T_ext_C = tsd.weather.T_ext
    T_int_C = tsd.rc_model_temperatures.T_int
    Tww_sup_0_C = bpr.building_systems['Tww_sup_0']
    Y = bpr.building_systems['Y']
    Qww_nom_W = tsd.heating_loads.Qww.max()

    # distribution and circulation losses
    V_dist_pipes_m3 = Lsww_dis * ((D / 1000) / 2) ** 2 * np.pi  # m3, volume inside distribution pipe
    Qww_dis_ls_r_W = np.vectorize(calc_Qww_dis_ls_r)(T_int_C, tsd.heating_loads.Qww.copy(), Lsww_dis, Lcww_dis, Y[1], Qww_nom_W,
                                                 V_dist_pipes_m3,Tww_sup_0_C)
    Qww_dis_ls_nr_W = np.vectorize(calc_Qww_dis_ls_nr)(T_int_C, tsd.heating_loads.Qww.copy(), Lvww_dis, Lvww_c, Y[0], Qww_nom_W,
                                                   V_dist_pipes_m3,Tww_sup_0_C, T_ext_C)
    # storage losses
    Tww_tank_C, tsd.heating_loads.Qww_sys = calc_DH_ww_with_tank_losses(T_ext_C, T_int_C, tsd.heating_loads.Qww.copy(), tsd.water.vww_m3perh,
                                                            Qww_dis_ls_r_W, Qww_dis_ls_nr_W)

    tsd.heating_system_mass_flows.mcpww_sys = tsd.heating_loads.Qww_sys / abs(Tww_tank_C - tsd.heating_system_temperatures.Tww_re)

    # erase points where the load is zero
    zero_load_mask = tsd.heating_loads.Qww <= 0.0
    tsd.heating_system_temperatures.Tww_sys_sup = np.where(zero_load_mask, 0.0, Tww_tank_C)
    tsd.heating_system_temperatures.Tww_sys_re = np.where(zero_load_mask, 0.0, tsd.heating_system_temperatures.Tww_re)

    return tsd

# end-use hot water demand calculation

def calc_Qww(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, schedules) -> TimeSeriesData:
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

    tsd.heating_system_temperatures.Tww_re = calc_water_temperature(tsd.weather.T_ext, depth_m=1)
    Tww_sup_0_C = bpr.building_systems['Tww_sup_0']

    # calc end-use demand
    tsd.water.vww_m3perh = schedules['Vww_lph'] / 1000  # m3/h
    tsd.heating_system_mass_flows.mww_kgs = tsd.water.vww_m3perh * P_WATER / 3600  # kg/s
    tsd.heating_system_mass_flows.mcptw = (tsd.water.vfw_m3perh - tsd.water.vww_m3perh) * CP_KJPERKGK * P_WATER / 3600  # kW_K tap water

    tsd.heating_loads.Qww = np.vectorize(function)(tsd.heating_system_mass_flows.mww_kgs, Tww_sup_0_C, tsd.heating_system_temperatures.Tww_re)

    return tsd


# final hot water demand calculation
def calc_Qwwf(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:

    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply["source_dhw"]
    scale_technology = bpr.supply['scale_dhw']
    efficiency_average_year = bpr.supply["eff_dhw"]

    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            tsd.electrical_loads.E_ww =  tsd.heating_loads.Qww_sys/ efficiency_average_year
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NATURALGAS":
            tsd.fuel_source.NG_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "OIL":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "COAL":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "WOOD":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "SOLAR":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.SOLAR_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / HOTWATER')
    elif scale_technology == "DISTRICT":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = tsd.heating_loads.Qww_sys / efficiency_average_year
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
    elif scale_technology == "NONE":
            tsd.fuel_source.NG_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.COAL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.OIL_ww = np.zeros(HOURS_IN_YEAR)
            tsd.fuel_source.WOOD_ww = np.zeros(HOURS_IN_YEAR)
            tsd.heating_loads.DH_ww = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_ww = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / HOTWATER')


    return tsd


def calc_Qww_dis_ls_r(Tair, Qww, Lsww_dis, Lcww_dis, Y, Qww_0, V, twws):
    if Qww > 0:
        # Calculate tamb in basement according to EN
        tamb = Tair

        # Circulation circuit losses
        circ_ls = (twws - tamb) * Y * Lcww_dis * (Qww / Qww_0)

        # Distribution circuit losses
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
            exponential = np.exp(-(Y * Lsww_dis * TR) / (P_WATER * CP_KJPERKGK * V * 1000))
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
    Calculates the heat flows within a fully mixed water storage tank for HOURS_IN_YEAR time-steps.
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
    Qww_sys = np.zeros(HOURS_IN_YEAR)
    Qww_st_ls = np.zeros(HOURS_IN_YEAR)
    Tww_tank_C = np.zeros(HOURS_IN_YEAR)
    Qd = np.zeros(HOURS_IN_YEAR)
    # calculate DHW tank size [in m3] based on the peak DHW demand in the building
    V_tank_m3 = Vww.max()  # size the tank with the highest flow rate
    T_tank_start_C = TWW_SETPOINT  # assume the tank temperature at timestep 0 is at the dhw set point

    if V_tank_m3 > 0:
        for k in range(HOURS_IN_YEAR):
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
        for k in range(HOURS_IN_YEAR):
            Tww_tank_C[k] = np.nan
    return Tww_tank_C, Qww_sys


def has_hot_water_technical_system(bpr: BuildingPropertiesRow):
    """
    Checks if building has a hot water system

    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
        """
    supported = ['HIGH_TEMP', 'MEDIUM_TEMP', 'LOW_TEMP']
    unsupported = ['NONE']

    if bpr.hvac['class_dhw'] in supported:
        return True
    elif bpr.hvac['class_dhw'] in unsupported:
        return False
    else:
        raise ValueError('Invalid value for type_dhw: %s. CEA supports only the next systems %s' %(bpr.hvac['class_dhw'], supported))
