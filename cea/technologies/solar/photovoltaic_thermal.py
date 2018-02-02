"""
Photovoltaic thermal panels
"""

from __future__ import division
import geopandas as gpd
import numpy as np
import pandas as pd
import time
import fiona
import os
from math import *
import cea.inputlocator
from cea.technologies.solar.photovoltaic import calc_properties_PV_db, calc_PV_power, calc_diffuseground_comp, \
    calc_Sm_PV
from cea.technologies.solar.solar_collector import calc_properties_SC_db, calc_IAM_beam_SC, calc_q_rad, calc_q_gain, \
    calc_Eaux_SC, \
    calc_optimal_mass_flow, calc_optimal_mass_flow_2, calc_qloss_network
from cea.utilities import dbf
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar import settings

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca, Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_PVT(locator, config, radiation_json_path, metadata_csv_path, latitude, longitude, weather_path, building_name):
    """
    This function first determines the surface area with sufficient solar radiation, and then calculates the optimal
    tilt angles of panels at each surface location. The panels are categorized into groups by their surface azimuths,
    tilt angles, and global irradiation. In the last, electricity and heat generation from PVT panels of each group are calculated.

    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator
    :param radiation_json_path: path to solar insulation data on all surfaces of each building
    :type radiation_json_path: string
    :param metadata_csv_path: path to data of sensor points measuring solar insulation of each building
    :type metadata_csv_path: string
    :param latitude: latitude of the case study location
    :type latitude: float
    :param longitude: longitude of the case study location
    :type longitude: float
    :param weather_path: path to the weather data file of the case study location
    :type weather_path: .epw
    :param building_name: list of building names in the case study
    :type building_name: Series
    :param T_in: inlet temperature to the solar collectors [C]
    :return: Building_PVT.csv with solar collectors heat generation potential of each building, Building_PVT_sensors.csv
             with sensor data of each PVT panel.
    """

    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    print 'reading weather data done'

    # solar properties
    solar_properties = solar_equations.calc_sun_properties(latitude, longitude, weather_data,
                                                           settings.date_start, settings.solar_window_solstice)
    print 'calculating solar properties done'

    # get properties of the panel to evaluate # TODO: find a PVT module reference
    panel_properties_PV = calc_properties_PV_db(locator.get_supply_systems(config.region), settings.type_PVpanel)
    panel_properties_SC = calc_properties_SC_db(locator.get_supply_systems(config.region), settings.type_SCpanel)
    print 'gathering properties of PVT collector panel'

    # select sensor point with sufficient solar radiation
    max_yearly_radiation, min_yearly_production, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(weather_data, radiation_json_path, metadata_csv_path,
                                             settings.min_radiation,
                                             settings.panel_on_roof, settings.panel_on_wall)

    print 'filtering low potential sensor points done'

    # Calculate the heights of all buildings for length of vertical pipes
    height = gpd.read_file(locator.get_zone_geometry())['height_ag'].sum()

    if not sensors_metadata_clean.empty:

        # calculate optimal angle and tilt for panels according to PV module size
        sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude,
                                                                      solar_properties,
                                                                      max_yearly_radiation, panel_properties_PV)

        print 'calculating optimal tile angle and separation done'

        # group the sensors with the same tilt, surface azimuth, and total radiation
        number_groups, hourlydata_groups, number_points, prop_observers = solar_equations.calc_groups(sensors_rad_clean,
                                                                                                      sensors_metadata_cat)

        print 'generating groups of sensor points done'

        Final = calc_PVT_generation(hourlydata_groups, weather_data, number_groups, prop_observers,
                                            solar_properties, settings.T_in_PVT, latitude, height, panel_properties_SC,
                                            panel_properties_PV)

        Final.to_csv(locator.PVT_results(building_name=building_name), index=True, float_format='%.2f')
        sensors_metadata_cat.to_csv(locator.PVT_metadata_results(building_name=building_name), index=True,
                                    index_label='SURFACE',
                                    float_format='%.2f')  # print selected metadata of the selected sensors

        print 'Building', building_name, 'done - time elapsed:', (time.clock() - t0), ' seconds'

    else:  # This loop is activated when a building has not sufficient solar potential
        Final = pd.DataFrame(
            {'Q_PVT_gen_kWh': 0, 'T_PVT_sup_C': 0, 'T_PVT_re_C': 0,
             'mcp_PVT_kWperC': 0, 'Eaux_PVT_kWh': 0,
             'Q_PVT_l_kWh': 0, 'E_PVT_gen_kWh': 0, 'Area_PVT_m2': 0,
             'radiation_kWh': 0}, index=range(8760))
        Final.to_csv(locator.PVT_results(building_name=building_name), index=True, float_format='%.2f')
        sensors_metadata_cat = pd.DataFrame(
            {'SURFACE': 0, 'AREA_m2': 0, 'BUILDING': 0, 'TYPE': 0, 'Xcoor': 0, 'Xdir': 0, 'Ycoor': 0, 'Ydir': 0,
             'Zcoor': 0, 'Zdir': 0, 'orientation': 0, 'total_rad_Whm2': 0, 'tilt_deg': 0, 'B_deg': 0,
             'array_spacing_m': 0, 'surface_azimuth_deg': 0, 'area_installed_module_m2': 0,
             'CATteta_z': 0, 'CATB': 0, 'CATGB': 0, 'type_orientation': 0}, index=range(2))
        sensors_metadata_cat.to_csv(locator.PVT_metadata_results(building_name=building_name), index=True,
                                    float_format='%.2f')

    return


def calc_PVT_generation(hourly_radiation_Wh, weather_data, number_groups, prop_observers, solar_properties, Tin_C,
                        latitude,
                        height, panel_properties_SC, panel_properties_PV):
    """
    To calculate the heat and electricity generated from PVT panels.

    :param hourly_radiation_Wh: mean hourly radiation of sensors in each group [Wh/m2]
    :type hourly_radiation_Wh: dataframe
    :param prop_observers: mean values of sensor properties of each group of sensors
    :type prop_observers: dataframe
    :param number_groups: number of groups of sensor points
    :type number_groups: float
    :param weather_data: weather data read from the epw file
    :type weather_data: dataframe
    :param g: declination
    :type g: float
    :param Sz: zenith angle
    :type Sz: float
    :param Az: solar azimuth
    :type Az: float
    :param ha: hour angle
    :param Tin_C: Fluid inlet temperature (C)
    :param height: height of the building [m]
    :param panel_properties_SC: properties of solar collector part
    :param panel_properties_PV: properties of the pv modules
    :return:
    """

    ## prepare data for electricity production calculation

    # convert degree to radians
    lat_rad = radians(latitude)
    g_rad = np.radians(solar_properties.g)
    ha_rad = np.radians(solar_properties.ha)
    Sz_rad = np.radians(solar_properties.Sz)
    Az_rad = np.radians(solar_properties.Az)

    # empty lists to store results
    Sum_radiation_kWh = np.zeros(8760)
    list_results = list(range(number_groups))
    list_areas_groups = list(range(number_groups))

    n = 1.526  # refractive index of glass
    Pg = 0.2  # ground reflectance
    K = 0.4  # glazing extinction coefficient
    eff_nom = panel_properties_PV['PV_n']
    NOCT = panel_properties_PV['PV_noct']
    Bref = panel_properties_PV['PV_Bref']
    a0 = panel_properties_PV['PV_a0']
    a1 = panel_properties_PV['PV_a1']
    a2 = panel_properties_PV['PV_a2']
    a3 = panel_properties_PV['PV_a3']
    a4 = panel_properties_PV['PV_a4']
    L = panel_properties_PV['PV_th']
    misc_losses = panel_properties_PV['misc_losses']

    ## prepare data for heat production calculation
    n0 = panel_properties_SC['n0']
    c1 = panel_properties_SC['c1']
    c2 = panel_properties_SC['c2']
    mB0_r = panel_properties_SC['mB0_r']
    mB_max_r = panel_properties_SC['mB_max_r']
    mB_min_r = panel_properties_SC['mB_min_r']
    C_eff = panel_properties_SC['C_eff']
    t_max = panel_properties_SC['t_max']
    IAM_d = panel_properties_SC['IAM_d']
    Aratio = panel_properties_SC['aperture_area_ratio']
    Apanel = panel_properties_PV['module_length_m'] ** 2
    dP1 = panel_properties_SC['dP1']
    dP2 = panel_properties_SC['dP2']
    dP3 = panel_properties_SC['dP3']
    dP4 = panel_properties_SC['dP4']
    Cp_fluid = panel_properties_SC['Cp_fluid']  # J/kgK

    ## prepare data for SC heat generation
    Sum_mcp_kWperC = np.zeros(8760)
    Sum_qout_kWh = np.zeros(8760)
    Sum_Eaux_kWh = np.zeros(8760)
    Sum_qloss_kWh = np.zeros(8760)
    Sum_E_gen_kWh = np.zeros(8760)
    potential = pd.DataFrame(index=[range(8760)])

    Tin_array_C = np.zeros(8760) + Tin_C
    aperature_area_m2 = Aratio * Apanel
    total_area_module_m2 = prop_observers['total_area_module_m2'].sum()  # total area for panel installation

    if panel_properties_SC['type'] == 'ET':  # for evacuated tubes
        Nseg = 100  # default number of subsdivisions for the calculation
    else:
        Nseg = 10  # default number of subsdivisions for the calculation

    # calculate equivalent length
    lv = panel_properties_PV['module_length_m']  # module length, same as PV
    number_modules = round(total_area_module_m2 / Apanel)
    l_ext_mperm2 = (
        2 * lv * number_modules / (total_area_module_m2 * Aratio))  # length of pipe connecting between panels
    l_int_mperm2 = 2 * height / (
        total_area_module_m2 * Aratio)  # length of pipe that connects panels to the thermal network
    Leq_mperm2 = l_int_mperm2 + l_ext_mperm2  # in m/m2 aperture

    for group in range(number_groups):
        # read panel properties of each group
        teta_z_deg = prop_observers.loc[group, 'surface_azimuth_deg']
        area_per_group_m2 = prop_observers.loc[group, 'total_area_module_m2']
        tilt_angle_deg = prop_observers.loc[group, 'B_deg']

        # degree to radians
        tilt_rad = radians(tilt_angle_deg)  # tilt angle
        teta_z_rad = radians(teta_z_deg)  # surface azimuth

        # read irradiation from group
        radiation_Wperm2 = pd.DataFrame({'I_sol': hourly_radiation_Wh[group]})
        radiation_Wperm2[
            'I_diffuse'] = weather_data.ratio_diffhout * radiation_Wperm2.I_sol  # calculate diffuse radiation
        radiation_Wperm2['I_direct'] = radiation_Wperm2['I_sol'] - radiation_Wperm2[
            'I_diffuse']  # calculate direct radiation
        radiation_Wperm2.fillna(0, inplace=True)  # set nan to zero

        ## calculate absorbed solar irradiation on tilt surfaces
        # calculate effective indicent angles necessary
        teta_rad = np.vectorize(solar_equations.calc_angle_of_incidence)(g_rad, lat_rad, ha_rad, tilt_rad, teta_z_rad)
        teta_ed_rad, teta_eg_rad = calc_diffuseground_comp(tilt_rad)

        results_Sm_PV = np.vectorize(calc_Sm_PV)(weather_data.drybulb_C, radiation_Wperm2.I_sol,
                                                 radiation_Wperm2.I_direct,
                                                 radiation_Wperm2.I_diffuse, tilt_rad, Sz_rad, teta_rad, teta_ed_rad,
                                                 teta_eg_rad, n, Pg,
                                                 K, NOCT, a0, a1, a2, a3, a4, L)

        ## SC heat generation
        # calculate incidence angle modifier for beam radiation
        IAM_b = calc_IAM_beam_SC(solar_properties, teta_z_deg, tilt_angle_deg, panel_properties_SC['type'], latitude)
        list_results[group] = calc_PVT_module(tilt_angle_deg, IAM_b.copy(), IAM_d,
                                              radiation_Wperm2.I_direct.copy(),
                                              radiation_Wperm2.I_diffuse.copy(),
                                              weather_data.drybulb_C, n0, c1, c2, mB0_r,
                                              mB_max_r, mB_min_r, C_eff, t_max,
                                              aperature_area_m2, dP1, dP2, dP3, dP4,
                                              Cp_fluid, Tin_C, Leq_mperm2, l_ext_mperm2,
                                              l_int_mperm2, Nseg, eff_nom, Bref,
                                              results_Sm_PV[0].copy(), results_Sm_PV[1].copy(),
                                              misc_losses, area_per_group_m2)

        # calculate results from each group
        name_group = prop_observers.loc[group, 'type_orientation']
        number_modules_per_group = area_per_group_m2 / Apanel
        list_areas_groups[group] = area_per_group_m2
        potential['PVT_' + name_group + '_Q_kWh'] = list_results[group][1] * number_modules_per_group
        potential['PVT_' + name_group + '_Tout_C'] = \
                list_results[group][1] / list_results[group][5] + Tin_C  # assume parallel connections in this group
        potential['PVT_' + name_group + '_E_kWh'] = list_results[group][6]
        potential['PVT_' + name_group + '_m2'] = area_per_group_m2

        # aggregate results from all modules
        Sum_mcp_kWperC = Sum_mcp_kWperC + list_results[group][5] * number_modules_per_group
        Sum_qloss_kWh = Sum_qloss_kWh + list_results[group][0] * number_modules_per_group
        Sum_qout_kWh = Sum_qout_kWh + list_results[group][1] * number_modules_per_group
        Sum_Eaux_kWh = Sum_Eaux_kWh + list_results[group][2] * number_modules_per_group
        Sum_E_gen_kWh = Sum_E_gen_kWh + list_results[group][6]
        Sum_radiation_kWh = Sum_radiation_kWh + hourly_radiation_Wh[group] * area_per_group_m2 / 1000

    potential['Area_PVT_m2'] = sum(list_areas_groups)
    potential['radiation_kWh'] = Sum_radiation_kWh
    potential['E_PVT_gen_kWh'] = Sum_E_gen_kWh
    potential['Q_PVT_gen_kWh'] = Sum_qout_kWh
    potential['Eaux_PVT_kWh'] = Sum_Eaux_kWh
    potential['Q_PVT_l_kWh'] = Sum_qloss_kWh
    potential['T_PVT_sup_C'] =  Tin_array_C
    potential['T_PVT_re_C'] = (Sum_qout_kWh / Sum_mcp_kWperC) + Tin_C  # assume parallel connections for all panels
    potential['mcp_PVT_kWperC'] = Sum_mcp_kWperC

    return potential


def calc_PVT_module(tilt_angle_deg, IAM_b_vector, IAM_d, I_direct_vector, I_diffuse_vector, Tamb_vector_C, n0, c1, c2,
                    mB0_r, mB_max_r, mB_min_r, C_eff_Jperm2K, t_max, aperture_area_m2, dP1, dP2, dP3, dP4,
                    Cp_fluid_JperkgK,
                    Tin_C, Leq, l_ext, l_int, Nseg, eff_nom, Bref, Sm_PV_Wperm2, Tcell_PV_C, misc_losses,
                    area_per_group):
    """
    This function calculates the heat & electricity production from PVT collectors. 
    The heat production calculation is adapted from calc_SC_module and then the updated cell temperature is used to 
    calculate PV electricity production.
    
    :param tilt_angle_deg: solar panel tilt angle [rad]
    :param IAM_b_vector: incident angle modifier for beam radiation [-]
    :param I_direct_vector: direct radiation [W/m2]
    :param I_diffuse_vector: diffuse radiation [W/m2]
    :param Tamb_vector_C: dry bulb temperature [C]
    :param n0: zero loss efficiency at normal incidence [-]
    :param c1: collector heat loss coefficient at zero temperature difference and wind speed [W/m2K]
    :param c2: temperature difference dependency of the heat loss coefficient [W/m2K2]
    :param mB0_r: nominal flow rate per aperture area [kg/h/m2 aperture]
    :param mB_max_r: maximum flow rate per aperture area
    :param mB_min_r: minimum flow rate per aperture area
    :param C_eff_Jperm2K: thermal capacitance of module [J/m2K]
    :param t_max: stagnation temperature [C]
    :param IAM_d_vector: incident angle modifier for diffuse radiation [-]
    :param aperture_area_m2: collector aperture area [m2]
    :param dP1: pressure drop [Pa/m2] at zero flow rate
    :param dP2: pressure drop [Pa/m2] at nominal flow rate (mB0)
    :param dP3: pressure drop [Pa/m2] at maximum flow rate (mB_max)
    :param dP4: pressure drop [Pa/m2] at minimum flow rate (mB_min)
    :param Tin_C: Fluid inlet temperature (C)
    :param Leq: equivalent length of pipes per aperture area [m/m2 aperture)
    :param Le: equivalent length of collector pipes per aperture area [m/m2 aperture]
    :param Nseg: Number of collector segments in flow direction for heat capacitance calculation
    :param eff_nom: nominal efficiency of PV module [-]
    :param Bref: cell maximum power temperature coefficient [degree C^(-1)]
    :param Sm_PV_Wperm2: absorbed solar radiation of PV module [Wh/m2]
    :param Tcell_PV_C: PV cell temperature [C]
    :param misc_losses: expected system loss [-]
    :param area_per_group: PV module area [m2]
    :return:

    ..[J. Allan et al., 2015] J. Allan, Z. Dehouche, S. Stankovic, L. Mauricette. "Performance testing of thermal and
    photovoltaic thermal solar collectors." Energy Science & Engineering 2015; 3(4): 310-326
    """

    # local variables
    msc_max_kgpers = mB_max_r * aperture_area_m2 / 3600  # maximum mass flow [kg/s]

    # Do the calculation of every time step for every possible flow condition
    # get states where highly performing values are obtained.
    specific_flows_kgpers = [np.zeros(8760), (np.zeros(8760) + mB0_r) * aperture_area_m2 / 3600,
                             (np.zeros(8760) + mB_max_r) * aperture_area_m2 / 3600,
                             (np.zeros(8760) + mB_min_r) * aperture_area_m2 / 3600, np.zeros(8760),
                             np.zeros(8760)]  # in kg/s
    specific_pressure_losses_Pa = [np.zeros(8760), (np.zeros(8760) + dP2) * aperture_area_m2,
                                   (np.zeros(8760) + dP3) * aperture_area_m2,
                                   (np.zeros(8760) + dP4) * aperture_area_m2, np.zeros(8760), np.zeros(8760)]  # in Pa

    # generate empty lists to store results
    temperature_out = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    temperature_in = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_losses_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    auxiliary_electricity_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760),
                                np.zeros(8760)]
    temperature_mean = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out_pre = np.zeros(8760)
    supply_out_total_kW = np.zeros(8760)
    mcp_kWperK = np.zeros(8760)
    T_module_C = []

    # calculate absorbed radiation
    tilt_rad = radians(tilt_angle_deg)
    q_rad_vector = np.vectorize(calc_q_rad)(n0, IAM_b_vector, I_direct_vector, IAM_d, I_diffuse_vector,
                                            tilt_rad)  # absorbed solar radiation in W/m2 is a mean of the group
    counter = 0
    Flag = False
    Flag2 = False
    for flow in range(6):
        Mo_seg = 1  # mode of segmented heat loss calculation. only one mode is implemented.
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
            c1_pvt = c1 - eff_nom * Bref * Sm_PV_Wperm2[time]  # _[J. Allan et al., 2015] eq.(18)
            Mfl_kgpers = specific_flows_kgpers[flow][time]
            if time < TIME0 + DELT / 2:
                for Iseg in range(101, 501):  # 400 points with the data
                    STORED[Iseg] = Tin_C
            else:
                for Iseg in range(1, Nseg):  # 400 points with the data
                    STORED[100 + Iseg] = STORED[200 + Iseg]
                    STORED[300 + Iseg] = STORED[400 + Iseg]

            # calculate stability criteria
            if Mfl_kgpers > 0:
                stability_criteria = Mfl_kgpers * Cp_fluid_JperkgK * Nseg * (DELT * 3600) / (
                    C_eff_Jperm2K * aperture_area_m2)
                if stability_criteria <= 0.5:
                    print ('ERROR: stability criteria' + str(stability_criteria) + 'is not reached. aperture_area: '
                           + str(aperture_area_m2) + 'mass flow: ' + str(Mfl_kgpers))

            # calculate average fluid temperature and average absorber temperature at the beginning of the time-step
            Tamb_C = Tamb_vector_C[time]
            q_rad_Wperm2 = q_rad_vector[time]
            Tfl[1] = 0  # mean fluid temperature
            Tabs[1] = 0  # mean absorber temperature
            for Iseg in range(1, Nseg + 1):
                Tfl[1] = Tfl[1] + STORED[100 + Iseg] / Nseg  # mean fluid temperature
                Tabs[1] = Tabs[1] + STORED[300 + Iseg] / Nseg  # mean absorber temperature

            # first guess for Delta T
            if Mfl_kgpers > 0:
                Tout = Tin_C + (q_rad_Wperm2 - ((c1_pvt) + 0.5) * (Tin_C - Tamb_C)) / (
                    Mfl_kgpers * Cp_fluid_JperkgK / aperture_area_m2)
                Tfl[2] = (Tin_C + Tout) / 2  # mean fluid temperature at present time-step
            else:
                Tout = Tamb_C + q_rad_Wperm2 / (c1_pvt + 0.5)
                Tfl[2] = Tout  # fluid temperature same as output
            DT[1] = Tfl[2] - Tamb_C  # difference between mean absorber temperature and the ambient temperature

            # calculate q_gain with the guess for DT[1]
            q_gain_Wperm2 = calc_q_gain(Tfl, Tabs, q_rad_Wperm2, DT, Tin_C, Tout, aperture_area_m2, c1_pvt, c2,
                                        Mfl_kgpers, delts, Cp_fluid_JperkgK, C_eff_Jperm2K, Tamb_C)

            Aseg_m2 = aperture_area_m2 / Nseg  # aperture area per segment
            for Iseg in range(1, Nseg + 1):
                # get temperatures of the previous time-step
                TflA[Iseg] = STORED[100 + Iseg]
                TabsA[Iseg] = STORED[300 + Iseg]
                if Iseg > 1:
                    TinSeg = ToutSeg
                else:
                    TinSeg = Tin_C
                if Mfl_kgpers > 0 and Mo_seg == 1:  # same heat gain/ losses for all segments
                    ToutSeg = ((Mfl_kgpers * Cp_fluid_JperkgK * (TinSeg + 273.15)) / Aseg_m2 - (
                        C_eff_Jperm2K * (TinSeg + 273.15)) / (2 * delts) + q_gain_Wperm2 +
                               (C_eff_Jperm2K * (TflA[Iseg] + 273.15) / delts)) / (
                                  Mfl_kgpers * Cp_fluid_JperkgK / Aseg_m2 + C_eff_Jperm2K / (2 * delts))
                    ToutSeg = ToutSeg - 273.15  # in [C]
                    TflB[Iseg] = (TinSeg + ToutSeg) / 2
                else:  # heat losses based on each segment's inlet and outlet temperatures.
                    Tfl[1] = TflA[Iseg]
                    Tabs[1] = TabsA[Iseg]
                    q_gain_Wperm2 = calc_q_gain(Tfl, Tabs, q_rad_Wperm2, DT, TinSeg, Tout, Aseg_m2, c1_pvt, c2,
                                                Mfl_kgpers, delts, Cp_fluid_JperkgK, C_eff_Jperm2K, Tamb_C)
                    ToutSeg = Tout
                    if Mfl_kgpers > 0:
                        TflB[Iseg] = (TinSeg + ToutSeg) / 2
                        ToutSeg = TflA[Iseg] + (q_gain_Wperm2 * delts) / C_eff_Jperm2K
                    else:
                        TflB[Iseg] = ToutSeg

                    # TflB[Iseg] = ToutSeg
                    q_fluid_Wperm2 = (ToutSeg - TinSeg) * Mfl_kgpers * Cp_fluid_JperkgK / Aseg_m2
                    q_mtherm_Wperm2 = (TflB[Iseg] - TflA[Iseg]) * C_eff_Jperm2K / delts
                    q_balance_error = q_gain_Wperm2 - q_fluid_Wperm2 - q_mtherm_Wperm2
                    if abs(q_balance_error) > 1:
                        time = time  # re-enter the iteration when energy balance not satisfied
                q_gain_Seg[Iseg] = q_gain_Wperm2  # in W/m2

            # resulting energy output
            q_out_kW = Mfl_kgpers * Cp_fluid_JperkgK * (ToutSeg - Tin_C) / 1000  # [kW]
            Tabs[2] = 0
            # storage of the mean temperature
            for Iseg in range(1, Nseg + 1):
                STORED[200 + Iseg] = TflB[Iseg]
                STORED[400 + Iseg] = TabsB[Iseg]
                Tabs[2] = Tabs[2] + TabsB[Iseg] / Nseg

            # outputs
            temperature_out[flow][time] = ToutSeg
            temperature_in[flow][time] = Tin_C
            supply_out_kW[flow][time] = q_out_kW
            temperature_mean[flow][time] = (Tin_C + ToutSeg) / 2  # Mean absorber temperature at present

            q_gain_Wperm2 = 0
            TavgB = 0
            TavgA = 0
            for Iseg in range(1, Nseg + 1):
                q_gain_Wperm2 = q_gain_Wperm2 + q_gain_Seg * Aseg_m2  # W
                TavgA = TavgA + TflA[Iseg] / Nseg
                TavgB = TavgB + TflB[Iseg] / Nseg

                # # OUT[9] = qgain/Area_a # in W/m2
                # q_mtherm_Wperm2 = (TavgB - TavgA) * C_eff_Jperm2K * aperture_area_m2 / delts
                # q_balance_error = q_gain_Wperm2 - q_mtherm_Wperm2 - q_out_kW

                # OUT[11] = q_mtherm
                # OUT[12] = q_balance_error
        if flow < 4:
            auxiliary_electricity_kW[flow] = np.vectorize(calc_Eaux_SC)(specific_flows_kgpers[flow],
                                                                        specific_pressure_losses_Pa[flow],
                                                                        Leq, l_int, aperture_area_m2)  # in kW
        if flow == 3:
            q1 = supply_out_kW[0]
            q2 = supply_out_kW[1]
            q3 = supply_out_kW[2]
            q4 = supply_out_kW[3]
            E1 = auxiliary_electricity_kW[0]
            E2 = auxiliary_electricity_kW[1]
            E3 = auxiliary_electricity_kW[2]
            E4 = auxiliary_electricity_kW[3]
            specific_flows_kgpers[4], specific_pressure_losses_Pa[4] = calc_optimal_mass_flow(q1, q2, q3, q4, E1, E2,
                                                                                              E3, E4, 0, mB0_r,
                                                                                              mB_max_r, mB_min_r, 0,
                                                                                              dP2, dP3, dP4,
                                                                                              aperture_area_m2)
        if flow == 4:
            auxiliary_electricity_kW[flow] = np.vectorize(calc_Eaux_SC)(specific_flows_kgpers[flow],
                                                                        specific_pressure_losses_Pa[flow],
                                                                        Leq, l_int, aperture_area_m2)  # in kW
            dp5 = specific_pressure_losses_Pa[flow]
            q5 = supply_out_kW[flow]
            m5 = specific_flows_kgpers[flow]
            # set points to zero when load is negative
            specific_flows_kgpers[5], specific_pressure_losses_Pa[5] = calc_optimal_mass_flow_2(m5, q5, dp5)

        if flow == 5:  # optimal mass flow
            supply_losses_kW[flow] = np.vectorize(calc_qloss_network)(specific_flows_kgpers[flow], l_ext,
                                                                      aperture_area_m2, temperature_mean[flow],
                                                                      Tamb_vector_C, msc_max_kgpers)
            supply_out_pre = supply_out_kW[flow].copy() + supply_losses_kW[flow].copy()
            auxiliary_electricity_kW[flow] = np.vectorize(calc_Eaux_SC)(specific_flows_kgpers[flow],
                                                                        specific_pressure_losses_Pa[flow],
                                                                        Leq, l_int, aperture_area_m2)  # in kW
            supply_out_total_kW = supply_out_kW + 0.5 * auxiliary_electricity_kW[flow] - supply_losses_kW[flow]
            mcp_kWperK = specific_flows_kgpers[flow] * (Cp_fluid_JperkgK / 1000)  # mcp in kW/c

    for x in range(8760):
        if supply_out_total_kW[5][x] <= 0:  # the demand is zero
            supply_out_total_kW[5][x] = 0
            auxiliary_electricity_kW[5][x] = 0
            temperature_out[5][x] = 0
            temperature_in[5][x] = 0
        T_module_C.append((temperature_out[5][x] + temperature_in[5][x]) / 2)

        if T_module_C[x] == 0:
            T_module_C[x] = Tcell_PV_C[x]

    PV_generation = np.vectorize(calc_PV_power)(Sm_PV_Wperm2, T_module_C, eff_nom, area_per_group, Bref, misc_losses)
    result = [supply_losses_kW[5], supply_out_total_kW[5], auxiliary_electricity_kW[5], temperature_out[5],
              temperature_in[5], mcp_kWperK,
              PV_generation]

    return result


# investment and maintenance costs

def calc_Cinv_PVT(PVT_peak_kW, locator, config, technology=0):
    """
    P_peak in kW
    result in CHF
    technology = 0 represents the first technology when there are multiple technologies.
    FIXME: handle multiple technologies when cost calculations are done
    """
    PVT_peak_W = PVT_peak_kW * 1000  # converting to W from kW
    PVT_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="PV")
    technology_code = list(set(PVT_cost_data['code']))
    PVT_cost_data[PVT_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if PVT_peak_W < PVT_cost_data['cap_min'][0]:
        PVT_peak_W = PVT_cost_data['cap_min'][0]
    PVT_cost_data = PVT_cost_data[
        (PVT_cost_data['cap_min'] <= PVT_peak_W) & (PVT_cost_data['cap_max'] > PVT_peak_W)]
    Inv_a = PVT_cost_data.iloc[0]['a']
    Inv_b = PVT_cost_data.iloc[0]['b']
    Inv_c = PVT_cost_data.iloc[0]['c']
    Inv_d = PVT_cost_data.iloc[0]['d']
    Inv_e = PVT_cost_data.iloc[0]['e']
    Inv_IR = (PVT_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = PVT_cost_data.iloc[0]['LT_yr']
    Inv_OM = PVT_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (PVT_peak_W) ** Inv_c + (Inv_d + Inv_e * PVT_peak_W) * log(PVT_peak_W)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    return Capex_a, Opex_fixed


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running photovoltaic-thermal with scenario = %s' % config.scenario)
    print('Running photovoltaic-thermal with date-start = %s' % config.solar.date_start)
    print('Running photovoltaic-thermal with dpl = %s' % config.solar.dpl)
    print('Running photovoltaic-thermal with eff-pumping = %s' % config.solar.eff_pumping)
    print('Running photovoltaic-thermal with fcr = %s' % config.solar.fcr)
    print('Running photovoltaic-thermal with k-msc-max = %s' % config.solar.k_msc_max)
    print('Running photovoltaic-thermal with min-radiation = %s' % config.solar.min_radiation)
    print('Running photovoltaic-thermal with panel-on-roof = %s' % config.solar.panel_on_roof)
    print('Running photovoltaic-thermal with panel-on-wall = %s' % config.solar.panel_on_wall)
    print('Running photovoltaic-thermal with ro = %s' % config.solar.ro)
    print('Running photovoltaic-thermal with solar-window-solstice = %s' % config.solar.solar_window_solstice)
    print('Running photovoltaic-thermal with t-in-pvt = %s' % config.solar.t_in_pvt)
    print('Running photovoltaic-thermal with t-in-sc = %s' % config.solar.t_in_sc)
    print('Running photovoltaic-thermal with type-pvpanel = %s' % config.solar.type_pvpanel)
    print('Running photovoltaic-thermal with type-scpanel = %s' % config.solar.type_scpanel)

    list_buildings_names = locator.get_zone_building_names()

    with fiona.open(locator.get_zone_geometry()) as shp:
        longitude = shp.crs['lon_0']
        latitude = shp.crs['lat_0']

    # list_buildings_names =['B026', 'B036', 'B039', 'B043', 'B050'] for missing buildings
    for building in list_buildings_names:
        radiation = locator.get_radiation_building(building_name=building)
        radiation_metadata = locator.get_radiation_metadata(building_name=building)
        calc_PVT(locator=locator, config=config, radiation_json_path=radiation, metadata_csv_path=radiation_metadata,
                 latitude=latitude, longitude=longitude, weather_path=config.weather, building_name=building)

    for i, building in enumerate(list_buildings_names):
        data = pd.read_csv(locator.PVT_results(building))
        if i == 0:
            df = data
        else:
            df = df + data
    del df[df.columns[0]]
    df.to_csv(locator.PVT_totals(), index=True, float_format='%.2f')


if __name__ == '__main__':
    main(cea.config.Configuration())
