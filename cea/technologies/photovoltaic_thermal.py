"""
Photovoltaic thermal panels
"""


from __future__ import division
import numpy as np
import pandas as pd
import geopandas as gpd
import cea.globalvar
import cea.inputlocator
import time
from math import *
from cea.utilities import dbfreader
from cea.utilities import epwreader
from cea.utilities import solar_equations

from cea.technologies.solar_collector import calc_properties_SC, calc_IAM_beam_SC, calc_q_rad, calc_q_gain, calc_Eaux_SC,\
    calc_optimal_mass_flow, calc_optimal_mass_flow_2, calc_qloss_network
from cea.technologies.photovoltaic import calc_properties_PV, calc_PV_power, calc_diffuseground_comp, calc_Sm_PV

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_PVT(locator, radiation_csv, metadata_csv, latitude, longitude, weather_path, building_name,
             panel_on_roof, panel_on_wall, misc_losses, worst_hour, type_SCpanel, type_PVpanel, T_in, min_radiation, date_start):

    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    print 'reading weather data done'

    # solar properties
    g, Sz, Az, ha, trr_mean, worst_sh, worst_Az = solar_equations.calc_sun_properties(latitude,longitude, weather_data,
                                                                                                        date_start,
                                                                                                        worst_hour)
    print 'calculating solar properties done'

    # get properties of the panel to evaluate
    panel_properties = calc_properties_PV(locator.get_supply_systems_database(), type_PVpanel)
    print 'gathering properties of PV collector panel'

    # select sensor point with sufficient solar radiation
    max_yearly_radiation, min_yearly_production, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(weather_data, radiation_csv, metadata_csv, min_radiation, panel_on_roof, panel_on_wall)

    print 'filtering low potential sensor points done'

    # Calculate the heights of all buildings for length of vertical pipes
    height = gpd.read_file(locator.get_building_geometry())['height_ag'].sum()

    if not sensors_metadata_clean.empty:

        # calculate optimal angle and tilt for panels according to PV module size
        sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude, worst_sh, worst_Az, trr_mean,
                                                      max_yearly_radiation, panel_properties)
        print 'calculating optimal tile angle and separation done'

        # group the sensors with the same tilt, surface azimuth, and total radiation
        number_groups, hourlydata_groups, number_points, prop_observers = solar_equations.calc_groups(sensors_rad_clean, sensors_metadata_cat)

        print 'generating groups of sensor points done'

        result, Final = calc_PVT_generation(type_PVpanel, hourlydata_groups, number_groups, number_points, prop_observers,
                                        weather_data, g, Sz, Az, ha, latitude, misc_losses, type_SCpanel, T_in, height, panel_properties)

        Final.to_csv(locator.PVT_results(building_name= building_name), index=True, float_format='%.2f')
        sensors_metadata_cat.to_csv(locator.PVT_metadata_results(building_name= building_name), index=True, float_format='%.2f')  # print selected metadata of the selected sensors

        print 'Building', building_name,'done - time elapsed:', (time.clock() - t0), ' seconds'

    return


def calc_PVT_generation(type_panel, group_radiation, number_groups, number_points, prop_observers, weather_data,
                        g, Sz, Az, ha, latitude, misc_losses, type_SCpanel, Tin, height, panel_properties):

    n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, Aratio, Apanel, dP1, dP2, dP3, dP4 = calc_properties_SC(
        type_SCpanel=1) #TODO: move out when testing is done

    list_results_PVT = list(range(number_groups))
    list_groups_areas = list(range(number_groups))

    ## prepare data for SC heat generation
    Sum_mcp = np.zeros(8760)
    Sum_qout = np.zeros(8760)
    Sum_Eaux = np.zeros(8760)
    Sum_qloss = np.zeros(8760)
    Sum_PV = np.zeros(8760)

    Tin_array = np.zeros(8760) + Tin
    aperature_area = Aratio * Apanel
    total_area_module = prop_observers['total_area_module'].sum() # total area for panel installation

    if type_SCpanel == 'SC2':  # for evacuated tubes #TODO:change to panel_properties['type']=='ET'
        Nseg = 100  # default number of subsdivisions for the calculation #TODO: find reference
    else:
        Nseg = 10  # default number of subsdivisions for the calculation

    # calculate equivalent length
    lv = 2  # grid length module length # TODO: change to module length, and make sure it's the same as PV
    number_modules = round(total_area_module/Apanel)
    l_ext = (2 * lv * number_modules/ (total_area_module * Aratio))
    l_int = 2 * height / (total_area_module * Aratio)
    Leq = l_int + l_ext  # in m/m2 aperture


    ## prepare data for PV electricity generation

    # convert degree to radians
    lat = radians(latitude)
    g_vector = np.radians(g)
    ha_vector = np.radians(ha)
    Sz_vector = np.radians(Sz)
    Az_vector = np.radians(Az)

    # empty lists to store results
    result_PV = list(range(number_groups))
    Sum_PV = np.zeros(8760)

    n = 1.526  # refractive index of glass
    Pg = 0.2  # ground reflectance
    K = 0.4  # glazing extinction coefficient
    eff_nom = panel_properties['PV_n']
    NOCT = panel_properties['PV_noct']
    Bref = panel_properties['PV_Bref']
    a0 = panel_properties['PV_a0']
    a1 = panel_properties['PV_a1']
    a2 = panel_properties['PV_a2']
    a3 = panel_properties['PV_a3']
    a4 = panel_properties['PV_a4']
    L = panel_properties['PV_th']   # fixme: check if it's the same as SC grid length

    for group in range(number_groups):
        # read panel properties of each group
        teta_z = prop_observers.loc[group,'surface_azimuth']
        area_per_group = prop_observers.loc[group,'total_area_module']
        tilt_angle = prop_observers.loc[group,'B']
        # degree to radians
        tilt = radians(tilt_angle) #tilt angle
        teta_z = radians(teta_z) #surface azimuth

        # read irradiation from group
        radiation = pd.DataFrame({'I_sol': group_radiation[group]})
        radiation['I_diffuse'] = weather_data.ratio_diffhout * radiation.I_sol  # calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']     # calculate direct radiation
        radiation.fillna(0, inplace=True)                                       # set nan to zero

        ## calculate absorbed solar irradiation on tilt surfaces
        # calculate effective indicent angles necessary
        teta_vector = np.vectorize(solar_equations.calc_angle_of_incidence)(g_vector, lat, ha_vector, tilt, teta_z)
        teta_ed, teta_eg = calc_diffuseground_comp(tilt)

        results_Sm = np.vectorize(calc_Sm_PV)(weather_data.drybulb_C, radiation.I_sol, radiation.I_direct,
                                           radiation.I_diffuse, tilt, Sz_vector, teta_vector, teta_ed, teta_eg, n, Pg,
                                           K, NOCT, a0, a1, a2, a3, a4, L)

        ## SC heat generation
        # calculate incidence angle modifier for beam radiation
        IAM_b = calc_IAM_beam_SC(Az, g, ha, teta_z, tilt_angle, type_SCpanel, latitude, Sz)

        list_results_PVT[group] = Calc_PVT_module(tilt_angle, IAM_b.copy(), radiation.I_direct.copy(),
                                             radiation.I_diffuse.copy(), weather_data.drybulb_C,
                                             n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, aperature_area, dP1,
                                             dP2, dP3, dP4, Tin, Leq, l_ext, Nseg,
                                             eff_nom, Bref, results_Sm[0].copy(), results_Sm[1].copy(), misc_losses,
                                             area_per_group)

        number_of_panels = area_per_group / Apanel
        Sum_mcp = Sum_mcp + list_results_PVT[group][5] * number_of_panels
        Sum_qloss = Sum_qloss + list_results_PVT[group][0] * number_of_panels
        Sum_qout = Sum_qout + list_results_PVT[group][1] * number_of_panels
        Sum_Eaux = Sum_Eaux + list_results_PVT[group][2] * number_of_panels
        Sum_PV = Sum_PV + list_results_PVT[group][6]
        list_groups_areas[group] = area_per_group

    Tout_group = (Sum_qout / Sum_mcp) + Tin  # in C
    Final = pd.DataFrame(
        {'Qsc_KWh': Sum_qout, 'Tscs': Tin_array, 'Tscr': Tout_group, 'mcp_kW/C': Sum_mcp, 'Eaux_kWh': Sum_Eaux,
         'Qsc_l_KWh': Sum_qloss, 'PV_kWh': Sum_PV, 'Area': sum(list_groups_areas)}, index=range(8760))

    return list_results_PVT, Final


def Calc_PVT_module(tilt_angle, IAM_b_vector, I_direct_vector, I_diffuse_vector, Tamb_vector,
                    n0, c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max, IAM_d, aperture_area, dP1, dP2, dP3, dP4, Tin,
                    Leq, l_ext, Nseg, eff_nom, Bref, Sm_PV, Tcell_PV, misc_losses, area_per_group):
    """
    This function calculates the heat & electricity production from PVT collectors. 
    The heat production calculation is adapted from calc_SC_module and then the updated cell temperature is used to 
    calculate PV electricity production.
    
    :param tilt_angle: 
    :param IAM_b_vector: 
    :param I_direct_vector: 
    :param I_diffuse_vector: 
    :param Tamb_vector:
    :param n0: 
    :param c1: 
    :param c2: 
    :param mB0_r: 
    :param mB_max_r: 
    :param mB_min_r: 
    :param C_eff: 
    :param t_max: 
    :param IAM_d: 
    :param aperture_area: 
    :param dP1: 
    :param dP2: 
    :param dP3: 
    :param dP4: 
    :param Tin: 
    :param Leq: 
    :param l_ext: 
    :param Nseg: 
    :param eff_nom: 
    :param Bref: 
    :param Sm_PV: 
    :param Tcell_PV: 
    :param misc_losses: 
    :param area_per_group: 
    :return: 
    """

    # local variables
    Cp_waterglycol = 3680  # J/kgK  water glycol  specific heat #TODO: move to gv, CHECK UNIT
    msc_max = mB_max_r * aperture_area / 3600  # maximum mass flow [kg/s] #TODO: move into the equation

    # Do the calculation of every time step for every possible flow condition
    # get states where highly performing values are obtained.
    specific_flows = [np.zeros(8760), (np.zeros(8760) + mB0_r) * aperture_area / 3600,
                      (np.zeros(8760) + mB_max_r) * aperture_area / 3600,
                      (np.zeros(8760) + mB_min_r) * aperture_area / 3600, np.zeros(8760), np.zeros(8760)]  # in kg/s
    specific_pressurelosses = [np.zeros(8760), (np.zeros(8760) + dP2) * aperture_area, (np.zeros(8760) + dP3) * aperture_area,
                               (np.zeros(8760) + dP4) * aperture_area, np.zeros(8760), np.zeros(8760)]  # in Pa

    # generate empty lists to store results
    temperature_out = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    temperature_in = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_losses = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    auxiliary_electricity = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    temperature_mean = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out_pre = np.zeros(8760)
    supply_out_total = np.zeros(8760)
    mcp = np.zeros(8760)
    T_module = []

    # calculate absorbed radiation
    tilt = radians(tilt_angle)
    q_rad_vector = np.vectorize(calc_q_rad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector,
                                            tilt)  # absorbed solar radiation in W/m2 is a mean of the group
    counter = 0
    Flag = False
    Flag2 = False
    for flow in range(6):
        Mo_seg = 1 # mode of segmented heat loss calculation. only one mode is implemented.
        TIME0 = 0
        DELT = 1  # timestep 1 hour
        delts = DELT * 3600  # convert time step in seconds
        Tfl = np.zeros([3, 1])  # create vector to store value at previous [1] and present [2] time-steps
        DT = np.zeros([3, 1])
        Tabs = np.zeros([3, 1])
        STORED = np.zeros([600, 1])
        TflA = np.zeros([600, 1])
        TflB = np.zeros([600, 1])
        TabsB = np.zeros([600, 1])
        TabsA = np.zeros([600, 1])
        q_gain_Seg = np.zeros([101, 1])  # maximum Iseg = maximum Nseg + 1 = 101

        for time in range(8760):
            c1_pvt = c1 - eff_nom * Bref * Sm_PV[time]    #TODO: reference
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
                stability_criteria = Mfl * Cp_waterglycol * Nseg * (DELT * 3600) / (C_eff * aperture_area)
                if stability_criteria <= 0.5:
                    print ('ERROR: stability criteria' + str(stability_criteria) + 'is not reached. aperture_area: '
                           + str(aperture_area) + 'mass flow: ' + str(Mfl))

            # calculate average fluid temperature and average absorber temperature at the beginning of the time-step
            Tamb = Tamb_vector[time]
            q_rad = q_rad_vector[time]
            Tfl[1] = 0  # mean absorber temp
            Tabs[1] = 0  # mean absorber initial tempr
            for Iseg in range(1, Nseg + 1):
                Tfl[1] = Tfl[1] + STORED[100 + Iseg] / Nseg  # mean fluid temperature
                Tabs[1] = Tabs[1] + STORED[300 + Iseg] / Nseg  # mean absorber temperature

            # first guess for Delta T
            if Mfl > 0:
                Tout = Tin + (q_rad - ((c1_pvt) + 0.5) * (Tin - Tamb)) / (Mfl * Cp_waterglycol / aperture_area)
                Tfl[2] = (Tin + Tout) / 2 # mean fluid temperature at present time-step
            else:
                Tout = Tamb + q_rad / (c1_pvt + 0.5)
                Tfl[2] = Tout  # fluid temperature same as output
            DT[1] = Tfl[2] - Tamb # difference between mean absorber temperature and the ambient temperature

            # calculate q_gain with the guess for DT[1]
            q_gain = calc_q_gain(Tfl, Tabs, q_rad, DT, Tin, Tout, aperture_area, c1_pvt, c2, Mfl, delts, Cp_waterglycol, C_eff, Tamb)

            Aseg = aperture_area / Nseg # aperture area per segment
            for Iseg in range(1, Nseg + 1):
                # get temperatures of the previous time-step
                TflA[Iseg] = STORED[100 + Iseg]
                TabsA[Iseg] = STORED[300 + Iseg]
                if Iseg > 1:
                    TinSeg = ToutSeg
                else:
                    TinSeg = Tin
                if Mfl > 0 and Mo_seg == 1:  # same heat gain/ losses for all segments
                    ToutSeg = ((Mfl * Cp_waterglycol * (TinSeg + 273)) / Aseg - (C_eff * (TinSeg + 273)) / (2 * delts) + q_gain +
                               (C_eff * (TflA[Iseg] + 273) / delts)) / (Mfl * Cp_waterglycol / Aseg + C_eff / (2 * delts))
                    ToutSeg = ToutSeg - 273  # in [C]
                    TflB[Iseg] = (TinSeg + ToutSeg) / 2
                else: # heat losses based on each segment's inlet and outlet temperatures.
                    Tfl[1] = TflA[Iseg]
                    Tabs[1] = TabsA[Iseg]
                    q_gain = calc_q_gain(Tfl, Tabs, q_rad, DT, TinSeg, Tout, Aseg, c1_pvt, c2, Mfl, delts, Cp_waterglycol, C_eff, Tamb)
                    ToutSeg = Tout
                    if Mfl > 0:
                        TflB[Iseg] = (TinSeg + ToutSeg) / 2
                        ToutSeg = TflA[Iseg] + (q_gain * delts) / C_eff
                    else:
                        TflB[Iseg] = ToutSeg

                    # TflB[Iseg] = ToutSeg
                    qfluid = (ToutSeg - TinSeg) * Mfl * Cp_waterglycol / Aseg
                    q_mtherm = (TflB[Iseg] - TflA[Iseg]) * C_eff / delts
                    qbal = q_gain - qfluid - q_mtherm
                    if abs(qbal) > 1:
                        time = time # re-enter the iteration when energy balance not satisfied
                q_gain_Seg[Iseg] = q_gain  # in W/m2 # fixme: redundant?

            # resulting energy output
            q_out = Mfl * Cp_waterglycol * (ToutSeg - Tin) / 1000 #[kW]
            Tabs[2] = 0
            # storage of the mean temperature
            for Iseg in range(1, Nseg + 1):
                STORED[200 + Iseg] = TflB[Iseg]
                STORED[400 + Iseg] = TabsB[Iseg]
                Tabs[2] = Tabs[2] + TabsB[Iseg] / Nseg

            # outputs
            temperature_out[flow][time] = ToutSeg
            temperature_in[flow][time] = Tin
            supply_out[flow][time] = q_out
            temperature_mean[flow][time] = (Tin + ToutSeg) / 2  # Mean absorber temperature at present

            q_gain = 0
            TavgB = 0
            TavgA = 0
            for Iseg in range(1, Nseg + 1):
                q_gain = q_gain + q_gain_Seg * Aseg  # W
                TavgA = TavgA + TflA[Iseg] / Nseg
                TavgB = TavgB + TflB[Iseg] / Nseg

            # OUT[9] = qgain/Area_a # in W/m2
            q_mtherm = (TavgB - TavgA) * C_eff * aperture_area / delts
            q_balance_error = q_gain - q_mtherm - q_out

            # OUT[11] = q_mtherm
            # OUT[12] = q_balance_error
        if flow < 4:
            auxiliary_electricity[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                         aperture_area)  # in kW
        if flow == 3:
            q1 = supply_out[0]
            q2 = supply_out[1]
            q3 = supply_out[2]
            q4 = supply_out[3]
            E1 = auxiliary_electricity[0]
            E2 = auxiliary_electricity[1]
            E3 = auxiliary_electricity[2]
            E4 = auxiliary_electricity[3]
            specific_flows[4], specific_pressurelosses[4] = calc_optimal_mass_flow(q1, q2, q3, q4, E1, E2, E3, E4, 0, mB0_r,
                                                                                   mB_max_r, mB_min_r, 0, dP2, dP3, dP4,
                                                                                   aperture_area)
        if flow == 4:
            auxiliary_electricity[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                         aperture_area)  # in kW
            dp5 = specific_pressurelosses[flow]
            q5 = supply_out[flow]
            m5 = specific_flows[flow]
            # set points to zero when load is negative
            specific_flows[5], specific_pressurelosses[5] = calc_optimal_mass_flow_2(m5, q5, dp5)

        if flow == 5: # optimal mass flow
            supply_losses[flow] = np.vectorize(calc_qloss_network)(specific_flows[flow], l_ext, aperture_area, temperature_mean[flow],
                                                                   Tamb_vector, msc_max)
            supply_out_pre = supply_out[flow].copy() + supply_losses[flow].copy()
            auxiliary_electricity[flow] = np.vectorize(calc_Eaux_SC)(specific_flows[flow], specific_pressurelosses[flow], Leq,
                                                         aperture_area)  # in kW
            supply_out_total = supply_out + 0.5 * auxiliary_electricity[flow] - supply_losses[flow]
            mcp = specific_flows[flow] * (Cp_waterglycol / 1000)  # mcp in kW/c

    for x in range(8760):
        if supply_out_total[5][x] <= 0:  # the demand is zero
            supply_out_total[5][x] = 0
            auxiliary_electricity[5][x] = 0
            temperature_out[5][x] = 0  # FIXME: change to np.nan
            temperature_in[5][x] = 0
        T_module.append((temperature_out[5][x] + temperature_in[5][x]) / 2)

        if T_module[x] == 0:
            T_module[x] = Tcell_PV[x]

    PV_generation = np.vectorize(calc_PV_power)(Sm_PV, T_module, eff_nom, area_per_group, Bref, misc_losses)
    result = [supply_losses[5], supply_out_total[5], auxiliary_electricity[5], temperature_out[flow], temperature_in[flow], mcp,
              PV_generation]
    return result

# investment and maintenance costs

def calc_Cinv_PVT(P_peak, gv):
    """
    P_peak in kW
    result in CHF
    """
    InvCa = 5000 * P_peak / gv.PVT_n # CHF/y
    # 2sol

    return InvCa

def test_PVT():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    list_buildings_names = dbfreader.dbf2df(locator.get_building_occupancy())['Name']


    min_radiation = 0.75  # points are selected with at least a minimum production of this % from the maximum in the area.
    type_SCpanel = 'SC1'  # monocrystalline, T2 is poly and T3 is amorphous. it relates to the database of technologies
    type_PVpanel = 'PV1'  # PV1: monocrystalline, PV2: poly, PV3: amorphous. please refer to supply system database.
    T_in = 35 # average temeperature #FIXME:defininition, find reference
    worst_hour = 8744  # first hour of sun on the solar solstice
    misc_losses = 0.1  # cabling, resistances etc.. #TODO:delete
    panel_on_roof = True  # flag for considering PV on roof #FIXME: define
    panel_on_wall = True  # flag for considering PV on wall #FIXME: define
    longitude = 7.439583333333333
    latitude = 46.95240555555556
    date_start = gv.date_start

    for building in list_buildings_names:
        radiation = locator.get_radiation_building(building_name= building)
        radiation_metadata = locator.get_radiation_metadata(building_name= building)
        calc_PVT(locator=locator, radiation_csv=radiation, metadata_csv=radiation_metadata, latitude=latitude,
                longitude=longitude, weather_path=weather_path, building_name=building,
                panel_on_roof = panel_on_roof, panel_on_wall = panel_on_wall, misc_losses=misc_losses, worst_hour=worst_hour,
                type_SCpanel=type_SCpanel, type_PVpanel=type_PVpanel, T_in=T_in, min_radiation=min_radiation, date_start=date_start)

if __name__ == '__main__':
    test_PVT()
