"""
==================================================
Photovoltaic thermal panels
==================================================

"""


from __future__ import division
import numpy as np
import pandas as pd
from math import *
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar_collector import optimal_angle_and_tilt, \
    calc_groups, Calc_incidenteangleB, calc_properties_SC, calc_anglemodifierSC, calc_qrad, calc_qgain, calc_Eaux_SC,\
    SelectminimumenergySc, Selectminimumenergy2, Calc_qloss_net
from cea.technologies.photovoltaic import calc_properties_PV, Calc_PV_power, Calc_diffuseground_comp, Calc_Sm_PV

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_PVT(locator, sensors_data, radiation, latitude, longitude, year, gv, weather_path):
    # weather data

    weather_data = epwreader.epw_reader(weather_path)

    # solar properties
    g, Sz, Az, ha, trr_mean, worst_sh, worst_Az = solar_equations.calc_sun_properties(latitude, longitude, weather_data,
                                                                                      gv)

    # read radiation file
    hourly_data = pd.read_csv(radiation)

    # get only datapoints with production beyond min_production
    Max_Isol = hourly_data.total.max()
    Min_Isol = Max_Isol * gv.min_production  # 80% of the local average maximum in the area
    sensors_data_clean = sensors_data[sensors_data["total"] > Min_Isol]
    radiation_clean = radiation.loc[radiation['sensor_id'].isin(sensors_data_clean.sensor_id)]

    # get only datapoints with aminimum 50 W/m2 of radiation for energy production
    radiation_clean[radiation_clean[:] <= 50] = 0

    # Calculate the heights of all buildings for length of vertical pipes
    height = locator.get_total_demand().height.sum()

    # calculate optimal angle and tilt for panels
    optimal_angle_and_tilt(sensors_data, latitude, worst_sh, worst_Az, trr_mean, gv.grid_side,
                           gv.module_lenght_PV, gv.angle_north, Min_Isol, Max_Isol)

    Number_groups, hourlydata_groups, number_points, prop_observers = calc_groups(radiation_clean, sensors_data_clean)

    Tin = 35
    result, Final = calc_PVT_generation(gv.type_PVpanel, hourlydata_groups,Number_groups, number_points, prop_observers,
                                        weather_data, g, Sz, Az, ha, latitude, gv.misc_losses, gv.type_SCpanel, Tin, height)

    Final.to_csv(locator.PVT_result(), index=True, float_format='%.2f')
    return


def calc_PVT_generation(type_panel, hourly_radiation, Number_groups, number_points, prop_observers, weather_data,
                        g, Sz, Az, ha, latitude, misc_losses, type_SCpanel, Tin, height):

    lat = radians(latitude)
    g_vector = np.radians(g)
    ha_vector = np.radians(ha)
    Sz_vector = np.radians(Sz)
    Az_vector = np.radians(Az)

    # get properties of the panel to evaluate
    n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, Aratio, Apanel, dP1, dP2, dP3, dP4 = calc_properties_SC(
        type_SCpanel)
    Area_a = Aratio * Apanel
    listresults = list(range(Number_groups))
    listareasgroups = list(range(Number_groups))

    Sum_mcp = np.zeros(8760)
    Sum_qout = np.zeros(8760)
    Sum_Eaux = np.zeros(8760)
    Sum_qloss = np.zeros(8760)
    Sum_PV = np.zeros(8760)
    Tin_array = np.zeros(8760) + Tin
    Sum_Area_m = (prop_observers['area_netpv'] * number_points).sum()
    lv = 2  # grid lenght module length
    Le = (2 * lv * number_points.sum()) / (Sum_Area_m * Aratio)
    Li = 2 * height / (Sum_Area_m * Aratio)
    Leq = Li + Le  # in m/m2

    if type_SCpanel == 2:  # for vaccum tubes
        Nseg = 100  # default number of subsdivisions for the calculation
    else:
        Nseg = 10  # default number of subsdivisions for the calculation

    # get properties of PV panel
    n = 1.526  # refractive index of galss
    Pg = 0.2  # ground reflectance
    K = 0.4  # extinction coefficien
    eff_nom, NOCT, Bref, a0, a1, a2, a3, a4, L = calc_properties_PV(type_panel)

    for group in range(Number_groups):
        teta_z = prop_observers.loc[group, 'aspect']  # azimuth of paneles of group
        areagroup = prop_observers.loc[group, 'area_netpv'] * number_points[group]
        tilt_angle = prop_observers.loc[group, 'slope']  # tilt angle of panels
        radiation = pd.DataFrame({'I_sol': hourly_radiation[group]})  # choose vector with all values of Isol
        radiation['I_diffuse'] = weather_data.ratio_diffhout * radiation.I_sol  # calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']  # direct radaition

        # to radians of properties - solar position and tilt angle
        tilt = radians(tilt_angle)  # slope of panel
        teta_z = radians(teta_z)  # azimuth of panel

        # calculate angles necesary
        teta_vector = np.vectorize(Calc_incidenteangleB)(g_vector, lat, ha_vector, tilt, teta_z)
        teta_ed, teta_eG = Calc_diffuseground_comp(tilt)

        results = np.vectorize(Calc_Sm_PV)(weather_data.drybulb_C, radiation.I_sol, radiation.I_direct.copy(),
                                           radiation.I_diffuse.copy(), tilt, lat, teta_z, ha_vector, g_vector,
                                           Sz_vector, Az_vector, teta_vector, teta_ed, teta_eG, areagroup, type_panel,
                                           misc_losses,
                                           n, Pg, K, eff_nom, NOCT, Bref, a0, a1, a2, a3, a4, L)

        # calculate angle modifiers
        T_G_hour['IAM_b'] = calc_anglemodifierSC(T_G_hour.Az, T_G_hour.g, T_G_hour.ha, teta_z, tilt_angle, type_SCpanel,
                                                 latitude, T_G_hour.Sz)

        listresults[group] = Calc_PVT_module(tilt_angle, T_G_hour.IAM_b.copy(), radiation.I_direct.copy(),
                                             radiation.I_diffuse.copy(), T_G_hour.te,
                                             n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, Area_a, dP1, dP2,
                                             dP3, dP4, Tin, Leq, Le, Nseg,
                                             eff_nom, Bref, results[0].copy(), results[1].copy(), misc_losses, areagroup)

        Kons = areagroup / Apanel
        Sum_mcp = Sum_mcp + listresults[group][5] * Kons
        Sum_qloss = Sum_qloss + listresults[group][0] * Kons
        Sum_qout = Sum_qout + listresults[group][1] * Kons
        Sum_Eaux = Sum_Eaux + listresults[group][2] * Kons
        Sum_PV = Sum_PV + listresults[group][6]
        listareasgroups[group] = areagroup

    Tout_group = (Sum_qout / Sum_mcp) + Tin  # in C
    Final = pd.DataFrame(
        {'Qsc_KWh': Sum_qout, 'Tscs': Tin_array, 'Tscr': Tout_group, 'mcp_kW/C': Sum_mcp, 'Eaux_kWh': Sum_Eaux,
         'Qsc_l_KWh': Sum_qloss, 'PV_kWh': Sum_PV, 'Area': sum(listareasgroups)}, index=range(8760))

    return listresults, Final


def Calc_PVT_module(tilt_angle, IAM_b_vector, I_direct_vector, I_diffuse_vector, Te_vector,
                        n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, Area_a, dP1, dP2, dP3, dP4, Tin,
                        Leq, Le, Nseg,
                        eff_nom, Bref, Sm_pv, Tcell_pv, misc_losses, areagroup):


    # panel to store the results per flow
    # method with no condensaiton gains, no wind or long-wave dependency, sky factor set to zero.
    # calculate radiation part
    # local variables
    Cpwg = 3680  # J/kgK  water grlycol  specific heat
    maxmsc = mB_max_r * Area_a / 3600
    # Do the calculation of every time step for every possible flow condition
    # get states where highly performing values are obtained.
    mopt = 0  # para iniciar
    Tcell = []
    temperature_out = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    temperature_in = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_losses = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    Auxiliary = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    temperature_m = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    specific_flows = [np.zeros(8760), (np.zeros(8760) + mB0_r) * Area_a / 3600, (np.zeros(8760) + mB_max_r) * Area_a / 3600,
                      (np.zeros(8760) + mB_min_r) * Area_a / 3600, np.zeros(8760), np.zeros(8760)]  # in kg/s
    specific_pressurelosses = [np.zeros(8760), (np.zeros(8760) + dP2) * Area_a, (np.zeros(8760) + dP3) * Area_a,
                               (np.zeros(8760) + dP4) * Area_a, np.zeros(8760), np.zeros(8760)]  # in Pa
    supply_out_pre = np.zeros(8760)
    supply_out_total = np.zeros(8760)
    mcp = np.zeros(8760)

    # calculate net radiant heat (absorbed)
    tilt = radians(tilt_angle)
    qrad_vector = np.vectorize(calc_qrad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector,
                                          tilt)  # in W/m2 is a mean of the group
    counter = 0
    Flag = False
    Flag2 = False
    for flow in range(6):
        Mo = 1
        TIME0 = 0
        DELT = 1  # timestep 1 hour
        delts = DELT * 3600  # convert time step in seconds
        Tfl = np.zeros([3, 1])  # create vector
        DT = np.zeros([3, 1])
        Tabs = np.zeros([3, 1])
        STORED = np.zeros([600, 1])
        TflA = np.zeros([600, 1])
        TflB = np.zeros([600, 1])
        TabsB = np.zeros([600, 1])
        TabsA = np.zeros([600, 1])
        qgainSeg = np.zeros([100, 1])
        for time in range(8760):
            c1_pvt = c1 - eff_nom * Bref * Sm_pv[time]
            Mfl = specific_flows[flow][time]
            if time < TIME0 + DELT / 2:
                for Iseg in range(101, 501):  # 400 points with the data
                    STORED[Iseg] = Tin
            else:
                for Iseg in range(1, Nseg):  # 400 points with the data
                    STORED[100 + Iseg] = STORED[200 + Iseg]
                    STORED[300 + Iseg] = STORED[400 + Iseg]

            # calculate stability criteria
            if Mfl > 0:
                stabcrit = Mfl * Cpwg * Nseg * (DELT * 3600) / (C_eff * Area_a)
                if stabcrit <= 0.5:
                    print 'ERROR' + str(stabcrit) + ' ' + str(Area_a) + ' ' + str(Mfl)
            Te = Te_vector[time]
            qrad = qrad_vector[time]
            Tfl[1] = 0  # mean absorber temp
            Tabs[1] = 0  # mean absorber initial tempr
            for Iseg in range(1, Nseg + 1):
                Tfl[1] = Tfl[1] + STORED[100 + Iseg] / Nseg
                Tabs[1] = Tabs[1] + STORED[300 + Iseg] / Nseg
            # first guess for DeatT
            if Mfl > 0:
                Tout = Tin + (qrad - ((c1_pvt) + 0.5) * (Tin - Te)) / (Mfl * Cpwg / Area_a)
                Tfl[2] = (Tin + Tout) / 2
            else:
                Tout = Te + qrad / (c1_pvt + 0.5)
                Tfl[2] = Tout  # fluid temperature same as output
            DT[1] = Tfl[2] - Te

            # calculate qgain with the guess

            qgain = calc_qgain(Tfl, Tabs, qrad, DT, Tin, Tout, Area_a, c1_pvt, c2, Mfl, delts, Cpwg, C_eff, Te)

            Aseg = Area_a / Nseg
            for Iseg in range(1, Nseg + 1):
                TflA[Iseg] = STORED[100 + Iseg]
                TabsA[Iseg] = STORED[300 + Iseg]
                if Iseg > 1:
                    TinSeg = ToutSeg
                else:
                    TinSeg = Tin
                if Mfl > 0 and Mo == 1:
                    ToutSeg = ((Mfl * Cpwg * (TinSeg + 273)) / Aseg - (C_eff * (TinSeg + 273)) / (2 * delts) + qgain +
                               (C_eff * (TflA[Iseg] + 273) / delts)) / (Mfl * Cpwg / Aseg + C_eff / (2 * delts))
                    ToutSeg = ToutSeg - 273
                    TflB[Iseg] = (TinSeg + ToutSeg) / 2
                else:
                    Tfl[1] = TflA[Iseg]
                    Tabs[1] = TabsA[Iseg]
                    qgain = calc_qgain(Tfl, Tabs, qrad, DT, TinSeg, Tout, Aseg, c1_pvt, c2, Mfl, delts, Cpwg, C_eff, Te)
                    ToutSeg = Tout
                    if Mfl > 0:
                        TflB[Iseg] = (TinSeg + ToutSeg) / 2
                        ToutSeg = TflA[Iseg] + (qgain * delts) / C_eff
                    else:
                        TflB[Iseg] = ToutSeg
                    TflB[Iseg] = ToutSeg
                    qfluid = (ToutSeg - TinSeg) * Mfl * Cpwg / Aseg
                    qmtherm = (TflB[Iseg] - TflA[Iseg]) * C_eff / delts
                    qbal = qgain - qfluid - qmtherm
                    if abs(qbal) > 1:
                        time = time
                qgainSeg[Iseg] = qgain  # in W/m2
            # the resulting energy output
            qout = Mfl * Cpwg * (ToutSeg - Tin)
            Tabs[2] = 0
            # storage of the mean temperature
            for Iseg in range(1, Nseg + 1):
                STORED[200 + Iseg] = TflB[Iseg]
                STORED[400 + Iseg] = TabsB[Iseg]
                Tabs[2] = Tabs[2] + TabsB[Iseg] / Nseg

            # outputs
            temperature_out[flow][time] = ToutSeg
            temperature_in[flow][time] = Tin
            supply_out[flow][time] = qout / 1000  # in kW
            temperature_m[flow][time] = (Tin + ToutSeg) / 2  # Mean absorber temperature at present

            qgain = 0
            TavgB = 0
            TavgA = 0
            for Iseg in range(1, Nseg + 1):
                qgain = qgain + qgainSeg * Aseg  # W
                TavgA = TavgA + TflA[Iseg] / Nseg
                TavgB = TavgB + TflB[Iseg] / Nseg

            # OUT[9] = qgain/Area_a # in W/m2
            qmtherm = (TavgB - TavgA) * C_eff * Area_a / delts
            qbal = qgain - qmtherm - qout

            # OUT[11] = qmtherm
            # OUT[12] = qbal
        if flow < 4:
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                        Area_a)  # in kW
        if flow == 3:
            q1 = supply_out[0]
            q2 = supply_out[1]
            q3 = supply_out[2]
            q4 = supply_out[3]
            E1 = Auxiliary[0]
            E2 = Auxiliary[1]
            E3 = Auxiliary[2]
            E4 = Auxiliary[3]
            specific_flows[4], specific_pressurelosses[4] = SelectminimumenergySc(q1, q2, q3, q4, E1, E2, E3, E4, 0, mB0_r,
                                                                                  mB_max_r, mB_min_r, 0, dP2, dP3, dP4,
                                                                                  Area_a)
        if flow == 4:
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                        Area_a)  # in kW
            dp5 = specific_pressurelosses[flow]
            q5 = supply_out[flow]
            m5 = specific_flows[flow]
            ##poits where load is negative
            specific_flows[5], specific_pressurelosses[5] = Selectminimumenergy2(m5, q5, dp5)
        if flow == 5:
            supply_losses[flow] = np.vectorize(Calc_qloss_net)(specific_flows[flow], Le, Area_a, temperature_m[flow],
                                                               Te_vector, maxmsc)
            supply_out_pre = supply_out[flow].copy() + supply_losses[flow].copy()
            Auxiliary[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                        Area_a)  # in kW
            supply_out_total = supply_out + 0.5 * Auxiliary[flow] - supply_losses[flow]
            mcp = specific_flows[flow] * (Cpwg / 1000)  # mcp in kW/c

    for x in range(8760):
        if supply_out_total[5][x] <= 0:  # the demand is zero
            supply_out_total[5][x] = 0
            Auxiliary[5][x] = 0
            temperature_out[5][x] = 0
            temperature_in[5][x] = 0
        Tcell.append((temperature_out[5][x] + temperature_in[5][x]) / 2)
        if Tcell[x] == 0:
            Tcell[x] = Tcell_pv[x]

    PV_generation = np.vectorize(Calc_PV_power)(Sm_pv, Tcell, eff_nom, areagroup, Bref, misc_losses)
    result = [supply_losses[5], supply_out_total[5], Auxiliary[5], temperature_out[flow], temperature_in[flow], mcp,
              PV_generation]
    return result

"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_PVT(P_peak):
    """
    P_peak in kW
    result in CHF
    """
    InvCa = 5000 * P_peak /20 # CHF/y
    # 2sol

    return InvCa

"""
============================
test
============================

"""

def test_PVT():
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(r'C:\reference-case\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()
    radiation = locator.get_radiation()
    gv = cea.globalvar.GlobalVariables()

    calc_PVT(locator=locator, radiation = radiation, latitude=46.95240555555556, longitude=7.439583333333333, year=2014, gv=gv,
                             weather_path=weather_path)


if __name__ == '__main__':
    test_PVT()
