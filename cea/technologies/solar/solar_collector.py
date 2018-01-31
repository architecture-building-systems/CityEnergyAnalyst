"""
solar collectors
"""

from __future__ import division
import numpy as np
import pandas as pd
import geopandas as gpd
import cea.globalvar
import cea.inputlocator
from math import *
import re
import time
import os
import fiona
import cea.config
from cea.utilities import dbf
from cea.utilities import epwreader
from cea.utilities import solar_equations
from cea.technologies.solar import settings

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh "]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# SC heat generation

def calc_SC(locator, config, radiation_csv, metadata_csv, latitude, longitude, weather_path, building_name):
    """
    This function first determines the surface area with sufficient solar radiation, and then calculates the optimal
    tilt angles of panels at each surface location. The panels are categorized into groups by their surface azimuths,
    tilt angles, and global irradiation. In the last, heat generation from SC panels of each group is calculated.

    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator
    :param radiation_csv: solar insulation data on all surfaces of each building
    :type radiation_csv: .csv
    :param metadata_csv: data of sensor points measuring solar insulation of each building
    :type metadata_csv: .csv
    :param latitude: latitude of the case study location
    :type latitude: float
    :param longitude: longitude of the case study location
    :type longitude: float
    :param weather_path: path to the weather data file of the case study location
    :type weather_path: .epw
    :param building_name: list of building names in the case study
    :type building_name: Series
    :param T_in: inlet temperature to the solar collectors [C]
    :return: Building_SC.csv with solar collectors heat generation potential of each building, Building_SC_sensors.csv
             with sensor data of each SC panel.
    """

    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    print 'reading weather data done'

    # solar properties
    solar_properties = solar_equations.calc_sun_properties(latitude, longitude, weather_data, settings.date_start,
                                                           settings.solar_window_solstice)
    print 'calculating solar properties done'

    # get properties of the panel to evaluate
    panel_properties = calc_properties_SC_db(locator.get_supply_systems(config.region), settings.type_SCpanel)
    print 'gathering properties of Solar collector panel'

    # select sensor point with sufficient solar radiation
    max_yearly_radiation, min_yearly_production, sensors_rad_clean, sensors_metadata_clean = \
        solar_equations.filter_low_potential(weather_data, radiation_csv, metadata_csv, settings.min_radiation,
                                             settings.panel_on_roof, settings.panel_on_wall)

    print 'filtering low potential sensor points done'

    # Calculate the heights of all buildings for length of vertical pipes
    height = gpd.read_file(locator.get_zone_geometry())['height_ag'].sum()

    if not sensors_metadata_clean.empty:
        # calculate optimal angle and tilt for panels
        sensors_metadata_cat = solar_equations.optimal_angle_and_tilt(sensors_metadata_clean, latitude,
                                                                      solar_properties, max_yearly_radiation,
                                                                      panel_properties)
        print 'calculating optimal tilt angle and separation done'

        # group the sensors with the same tilt, surface azimuth, and total radiation
        number_groups, hourlydata_groups, number_points, prop_observers = solar_equations.calc_groups(sensors_rad_clean,
                                                                                                      sensors_metadata_cat)

        print 'generating groups of sensor points done'

        # calculate heat production from solar collectors
        Final = calc_SC_generation(hourlydata_groups, prop_observers, number_groups, weather_data,
                                            solar_properties,
                                            settings.T_in_SC, height, panel_properties, latitude)

        # save SC generation potential and metadata of the selected sensors
        Final.to_csv(locator.SC_results(building_name=building_name), index=True, float_format='%.2f')
        sensors_metadata_cat.to_csv(locator.SC_metadata_results(building_name=building_name), index=True,
                                    index_label='SURFACE',
                                    float_format='%.2f')  # print selected metadata of the selected sensors

        print 'Building', building_name, 'done - time elapsed:', (time.clock() - t0), ' seconds'
    else:  # This loop is activated when a building has not sufficient solar potential
        Final = pd.DataFrame(
            {'Q_SC_gen_kWh': 0, 'T_SC_sup_C': 0, 'T_SC_re_C': 0,
             'mcp_SC_kWperC': 0, 'Eaux_SC_kWh': 0,
             'Q_SC_l_kWh': 0, 'Area_SC_m2': 0, 'radiation_kWh': 0},
            index=range(8760))
        Final.to_csv(locator.SC_results(building_name=building_name), index=True, float_format='%.2f')
        sensors_metadata_cat = pd.DataFrame(
            {'SURFACE': 0, 'AREA_m2': 0, 'BUILDING': 0, 'TYPE': 0, 'Xcoor': 0, 'Xdir': 0, 'Ycoor': 0, 'Ydir': 0,
             'Zcoor': 0, 'Zdir': 0, 'orientation': 0, 'total_rad_Whm2': 0, 'tilt_deg': 0, 'B_deg': 0,
             'array_spacing_m': 0, 'surface_azimuth_deg': 0, 'area_installed_module_m2': 0,
             'CATteta_z': 0, 'CATB': 0, 'CATGB': 0, 'type_orientation': 0}, index=range(2))
        sensors_metadata_cat.to_csv(locator.SC_metadata_results(building_name=building_name), index=True,
                                    float_format='%.2f')

    return


# =========================
# SC heat production
# =========================

def calc_SC_generation(hourly_radiation, prop_observers, number_groups, weather_data, solar_properties, Tin_C, height,
                       panel_properties, latitude):
    """
    To calculate the heat generated from SC panels.

    :param hourly_radiation: mean hourly radiation of sensors in each group [Wh/m2]
    :type hourly_radiation: dataframe
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
    :param panel_properties: properties of solar panels
    :type panel_properties: dataframe
    :return:
    """

    # read values from panel_properties and solar_properties
    n0 = panel_properties['n0']
    c1 = panel_properties['c1']
    c2 = panel_properties['c2']
    mB0_r = panel_properties['mB0_r']
    mB_max_r = panel_properties['mB_max_r']
    mB_min_r = panel_properties['mB_min_r']
    C_eff = panel_properties['C_eff']
    t_max = panel_properties['t_max']
    IAM_d = panel_properties['IAM_d']
    Aratio = panel_properties['aperture_area_ratio']
    Apanel = panel_properties['module_area_m2']
    dP1 = panel_properties['dP1']
    dP2 = panel_properties['dP2']
    dP3 = panel_properties['dP3']
    dP4 = panel_properties['dP4']
    Cp_fluid_JperkgK = panel_properties['Cp_fluid']  # J/kgK

    # create lists to store results
    list_results = [None] * number_groups
    list_areas_groups = [None] * number_groups
    Sum_mcp_kWperC = np.zeros(8760)
    Sum_qout_kWh = np.zeros(8760)
    Sum_Eaux_kWh = np.zeros(8760)
    Sum_qloss_kWh = np.zeros(8760)
    Sum_radiation_kWh = np.zeros(8760)
    potential = pd.DataFrame(index=[range(8760)])

    Tin_array_C = np.zeros(8760) + Tin_C
    aperature_area_per_module = Aratio * Apanel
    total_area_module = prop_observers['total_area_module_m2'].sum()  # total area for panel installation

    # calculate equivalent length of pipes
    lv = panel_properties['module_length_m']  # module length
    number_modules = round(total_area_module / Apanel)  # this is an estimation
    l_ext_mperm2 = (2 * lv * number_modules / (total_area_module * Aratio))  # pipe length within the collectors
    l_int_mperm2 = 2 * height / (
        total_area_module * Aratio)  # pipe length from building substation to roof top collectors
    Leq_mperm2 = l_int_mperm2 + l_ext_mperm2  # in m/m2 aperture

    if panel_properties['type'] == 'ET':  # for evacuated tubes
        Nseg = 100  # default number of subsdivisions for the calculation
    else:
        Nseg = 10  # default number of subsdivisions for the calculation

    for group in range(number_groups):
        # load panel angles from group
        teta_z_deg = prop_observers.loc[group, 'surface_azimuth_deg']  # azimuth of panels of group
        area_per_group_m2 = prop_observers.loc[group, 'total_area_module_m2']
        tilt_angle_deg = prop_observers.loc[group, 'tilt_deg']  # tilt angle of panels

        # create dataframe with irradiation from group

        radiation_Wh = pd.DataFrame({'I_sol': hourly_radiation[group]})
        radiation_Wh['I_diffuse'] = weather_data.ratio_diffhout * radiation_Wh.I_sol  # calculate diffuse radiation
        radiation_Wh['I_direct'] = radiation_Wh['I_sol'] - radiation_Wh['I_diffuse']  # calculate direct radiation
        radiation_Wh.fillna(0, inplace=True)  # set nan to zero

        # calculate incidence angle modifier for beam radiation
        IAM_b = calc_IAM_beam_SC(solar_properties, teta_z_deg, tilt_angle_deg, panel_properties['type'], latitude)

        # calculate heat production from a solar collector of each group
        list_results[group] = calc_SC_module(tilt_angle_deg, IAM_b, IAM_d, radiation_Wh.I_direct,
                                             radiation_Wh.I_diffuse, weather_data.drybulb_C, n0,
                                             c1, c2, mB0_r, mB_max_r, mB_min_r, C_eff, t_max,
                                             aperature_area_per_module, dP1, dP2, dP3, dP4,
                                             Cp_fluid_JperkgK, Tin_C, Leq_mperm2, l_ext_mperm2,
                                             l_int_mperm2, Nseg)
        # calculate results from each group
        name_group = prop_observers.loc[group, 'type_orientation']
        number_modules_per_group = area_per_group_m2 / Apanel
        list_areas_groups[group] = area_per_group_m2
        potential['SC_' + name_group + '_Q_kWh'] = list_results[group][1] * number_modules_per_group
        potential['SC_' + name_group + '_m2'] = area_per_group_m2
        potential['SC_' + name_group + '_Tout_C'] = \
                list_results[group][1] / list_results[group][5] + Tin_C  # assume parallel connections in this group

        # aggregate results from all modules
        Sum_qout_kWh = Sum_qout_kWh + list_results[group][1] * number_modules_per_group
        Sum_Eaux_kWh = Sum_Eaux_kWh + list_results[group][2] * number_modules_per_group
        Sum_qloss_kWh = Sum_qloss_kWh + list_results[group][0] * number_modules_per_group
        Sum_mcp_kWperC = Sum_mcp_kWperC + list_results[group][5] * number_modules_per_group
        Sum_radiation_kWh = Sum_radiation_kWh + radiation_Wh['I_sol'] * area_per_group_m2 / 1000

    potential['Area_SC_m2'] = sum(list_areas_groups)
    potential['radiation_kWh'] = Sum_radiation_kWh
    potential['Q_SC_gen_kWh'] = Sum_qout_kWh
    potential['Eaux_SC_kWh'] = Sum_Eaux_kWh
    potential['Q_SC_l_kWh'] = Sum_qloss_kWh
    potential['T_SC_sup_C'] =  Tin_array_C
    potential['T_SC_re_C'] = (Sum_qout_kWh / Sum_mcp_kWperC) + Tin_C  # assume parallel connections for all panels
    potential['mcp_SC_kWperC'] = Sum_mcp_kWperC

    return potential


def calc_SC_module(tilt_angle_deg, IAM_b_vector, IAM_d_vector, I_direct_vector, I_diffuse_vector, Tamb_vector_C, n0, c1,
                   c2, mB0_r, mB_max_r, mB_min_r, C_eff_Jperm2K, t_max, aperture_area_m2, dP1, dP2, dP3, dP4,
                   Cp_fluid_JperkgK, Tin_C, Leq, l_ext, l_int, Nseg):
    """
    This function calculates the heat production from a solar collector. The method is adapted from TRNSYS Type 832.
    Assume no no condensation gains, no wind or long-wave dependency, sky factor set to zero.

    :param tilt_angle_deg: solar panel tilt angle [degree]
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
    :param l_ext: equivalent length of pipes within the collectors per aperture area [m/m2 aperture]
    :param Nseg: Number of collector segments in flow direction for heat capacitance calculation
    :return:

    ..[M. Haller et al., 2012] Haller, M., Perers, B., Bale, C., Paavilainen, J., Dalibard, A. Fischer, S. & Bertram, E.
    (2012). TRNSYS Type 832 v5.00 " Dynamic Collector Model by Bengt Perers". Updated Input-Output Reference.
    ..[ J. Fonseca et al., 2016] Fonseca, J., Nguyen, T-A., Schlueter, A., Marechal, F. City Energy Analyst:
    Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts.
    Energy and Buildings, 2016.
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
    temperature_mean = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_out_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    supply_losses_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760)]
    auxiliary_electricity_kW = [np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760), np.zeros(8760),
                                np.zeros(8760)]
    supply_out_pre = np.zeros(8760)
    supply_out_total_kW = np.zeros(8760)
    mcp_kWperK = np.zeros(8760)

    # calculate absorbed radiation
    tilt = radians(tilt_angle_deg)
    q_rad_vector = np.vectorize(calc_q_rad)(n0, IAM_b_vector, I_direct_vector, IAM_d_vector, I_diffuse_vector,
                                            tilt)  # absorbed solar radiation in W/m2 is a mean of the group
    for flow in range(6):
        mode_seg = 1  # mode of segmented heat loss calculation. only one mode is implemented.
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
            Mfl_kgpers = specific_flows_kgpers[flow][time]  # [kg/s]
            if time < TIME0 + DELT / 2:
                # set output values to the appropriate initial values
                for Iseg in range(101, 501):  # 400 points with the data
                    STORED[Iseg] = Tin_C
            else:
                # write average temperature of all segments at the end of previous time-step
                # as the initial temperature of the present time-step
                for Iseg in range(1, Nseg + 1):  # 400 points with the data
                    STORED[100 + Iseg] = STORED[200 + Iseg]  # thermal capacitance node temperature
                    STORED[300 + Iseg] = STORED[400 + Iseg]  # absorber node temperature

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
            Tfl[1] = 0
            Tabs[1] = 0
            for Iseg in range(1, Nseg + 1):
                Tfl[1] = Tfl[1] + STORED[100 + Iseg] / Nseg  # mean fluid temperature
                Tabs[1] = Tabs[1] + STORED[300 + Iseg] / Nseg  # mean absorber temperature

            ## first guess for Delta T
            if Mfl_kgpers > 0:
                Tout_C = Tin_C + (q_rad_Wperm2 - (c1 + 0.5) * (Tin_C - Tamb_C)) / (
                    Mfl_kgpers * Cp_fluid_JperkgK / aperture_area_m2)
                Tfl[2] = (Tin_C + Tout_C) / 2  # mean fluid temperature at present time-step
            else:
                Tout_C = Tamb_C + q_rad_Wperm2 / (c1 + 0.5)
                Tfl[2] = Tout_C  # fluid temperature same as output
            DT[1] = Tfl[2] - Tamb_C  # difference between mean absorber temperature and the ambient temperature

            # calculate q_gain with the guess for DT[1]
            q_gain_Wperm2 = calc_q_gain(Tfl, Tabs, q_rad_Wperm2, DT, Tin_C, Tout_C, aperture_area_m2, c1, c2,
                                        Mfl_kgpers,
                                        delts, Cp_fluid_JperkgK, C_eff_Jperm2K, Tamb_C)

            A_seg_m2 = aperture_area_m2 / Nseg  # aperture area per segment
            # multi-segment calculation to avoid temperature jump at times of flow rate changes.
            for Iseg in range(1, Nseg + 1):
                # get temperatures of the previous time-step
                TflA[Iseg] = STORED[100 + Iseg]
                TabsA[Iseg] = STORED[300 + Iseg]
                if Iseg > 1:
                    Tin_Seg_C = Tout_Seg_C
                else:
                    Tin_Seg_C = Tin_C

                if Mfl_kgpers > 0 and mode_seg == 1:  # same heat gain/ losses for all segments
                    Tout_Seg_K = ((Mfl_kgpers * Cp_fluid_JperkgK * (Tin_Seg_C + 273.15)) / A_seg_m2 -
                                  (C_eff_Jperm2K * (Tin_Seg_C + 273.15)) / (2 * delts) + q_gain_Wperm2 +
                                  (C_eff_Jperm2K * (TflA[Iseg] + 273.15) / delts)) / (
                                     Mfl_kgpers * Cp_fluid_JperkgK / A_seg_m2 + C_eff_Jperm2K / (2 * delts))
                    Tout_Seg_C = Tout_Seg_K - 273.15  # in [C]
                    TflB[Iseg] = (Tin_Seg_C + Tout_Seg_C) / 2
                else:  # heat losses based on each segment's inlet and outlet temperatures.
                    Tfl[1] = TflA[Iseg]
                    Tabs[1] = TabsA[Iseg]
                    q_gain_Wperm2 = calc_q_gain(Tfl, Tabs, q_rad_Wperm2, DT, Tin_Seg_C, Tout_C, A_seg_m2, c1, c2,
                                                Mfl_kgpers, delts, Cp_fluid_JperkgK, C_eff_Jperm2K, Tamb_C)
                    Tout_Seg_C = Tout_C

                    if Mfl_kgpers > 0:
                        TflB[Iseg] = (Tin_Seg_C + Tout_Seg_C) / 2
                        Tout_Seg_C = TflA[Iseg] + (q_gain_Wperm2 * delts) / C_eff_Jperm2K
                    else:
                        TflB[Iseg] = Tout_Seg_C

                    # TflB[Iseg] = Tout_Seg
                    q_fluid_Wperm2 = (Tout_Seg_C - Tin_Seg_C) * Mfl_kgpers * Cp_fluid_JperkgK / A_seg_m2
                    q_mtherm_Whperm2 = (TflB[Iseg] - TflA[
                        Iseg]) * C_eff_Jperm2K / delts  # total heat change rate of thermal capacitance
                    q_balance_error = q_gain_Wperm2 - q_fluid_Wperm2 - q_mtherm_Whperm2
                    if abs(q_balance_error) > 1:
                        time = time  # re-enter the iteration when energy balance not satisfied
                q_gain_Seg[Iseg] = q_gain_Wperm2  # in W/m2

            # resulting net energy output
            q_out_kW = (Mfl_kgpers * Cp_fluid_JperkgK * (Tout_Seg_C - Tin_C)) / 1000  # [kW]
            Tabs[2] = 0
            # storage of the mean temperature
            for Iseg in range(1, Nseg + 1):
                STORED[200 + Iseg] = TflB[Iseg]
                STORED[400 + Iseg] = TabsB[Iseg]
                Tabs[2] = Tabs[2] + TabsB[Iseg] / Nseg

            # outputs
            temperature_out[flow][time] = Tout_Seg_C
            temperature_in[flow][time] = Tin_C
            supply_out_kW[flow][time] = q_out_kW
            temperature_mean[flow][time] = (Tin_C + Tout_Seg_C) / 2  # Mean absorber temperature at present

            # q_gain = 0
            # TavgB = 0
            # TavgA = 0
            # for Iseg in range(1, Nseg + 1):
            #     q_gain = q_gain + q_gain_Seg[Iseg] * A_seg_m2  # [W]
            #     TavgA = TavgA + TflA[Iseg] / Nseg
            #     TavgB = TavgB + TflB[Iseg] / Nseg
            #
            # # OUT[9] = q_gain/Area_a # in W/m2
            # q_mtherm = (TavgB - TavgA) * C_eff * aperture_area / delts
            # q_balance_error = q_gain - q_mtherm - q_out

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
            # calculate optimal mass flow and the corresponding pressure loss
            specific_flows_kgpers[4], specific_pressure_losses_Pa[4] = calc_optimal_mass_flow(q1, q2, q3, q4, E1, E2,
                                                                                              E3, E4, 0,
                                                                                              mB0_r, mB_max_r, mB_min_r,
                                                                                              0,
                                                                                              dP2, dP3, dP4,
                                                                                              aperture_area_m2)
        if flow == 4:
            # calculate pumping electricity when operatres at optimal mass flow
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
                                                                      aperture_area_m2,
                                                                      temperature_mean[flow], Tamb_vector_C,
                                                                      msc_max_kgpers)
            supply_out_pre = supply_out_kW[flow].copy() + supply_losses_kW[flow].copy()
            auxiliary_electricity_kW[flow] = np.vectorize(calc_Eaux_SC)(specific_flows_kgpers[flow],
                                                                        specific_pressure_losses_Pa[flow],
                                                                        Leq, l_int, aperture_area_m2)  # in kW
            supply_out_total_kW = supply_out_kW[flow].copy() + 0.5 * auxiliary_electricity_kW[flow].copy() - \
                                  supply_losses_kW[flow].copy()  # eq.(58) _[J. Fonseca et al., 2016]
            mcp_kWperK = specific_flows_kgpers[flow] * (Cp_fluid_JperkgK / 1000)  # mcp in kW/K

    result = [supply_losses_kW[5], supply_out_total_kW, auxiliary_electricity_kW[5], temperature_out[5],
              temperature_in[5], mcp_kWperK]
    q_rad_per_panel = q_rad_vector * aperture_area_m2
    return result


def calc_q_rad(n0, IAM_b, I_direct, IAM_d, I_diffuse, tilt):
    """
    Calculates the absorbed radiation for solar thermal collectors.

    :param n0: zero loss efficiency [-]
    :param IAM_b: incidence angle modifier for beam radiation [-]
    :param I_direct: direct/beam radiation [W/m2]
    :param IAM_d: incidence angle modifier for diffuse radiation [-]
    :param I_diffuse: diffuse radiation [W/m2]
    :param tilt: solar panel tilt angle [rad]
    :return q_rad: absorbed radiation [W/m2]
    """
    q_rad_Wperm2 = n0 * IAM_b * I_direct + n0 * IAM_d * I_diffuse * (1 + cos(tilt)) / 2
    return q_rad_Wperm2


def calc_q_gain(Tfl, Tabs, q_rad_Whperm2, DT, Tin, Tout, aperture_area_m2, c1, c2, Mfl, delts, Cp_waterglycol, C_eff,
                Te):
    """
    calculate the collector heat gain through iteration including temperature dependent thermal losses of the collectors.

    :param Tfl: mean fluid temperature
    :param Tabs: mean absorber temperature
    :param q_rad_Whperm2: absorbed radiation per aperture [Wh/m2]
    :param DT: temperature differences between collector and ambient [K]
    :param Tin: collector inlet temperature [K]
    :param Tout: collector outlet temperature [K]
    :param aperture_area_m2: aperture area [m2]
    :param c1: collector heat loss coefficient at zero temperature difference and wind speed [W/m2K]
    :param c2: temperature difference dependency of the heat loss coefficient [W/m2K2]
    :param Mfl: mass flow rate [kg/s]
    :param delts:
    :param Cp_waterglycol: heat capacity of water glycol [J/kgK]
    :param C_eff: thermal capacitance of module [J/m2K]
    :param Te: ambient temperature
    :return:

    ..[M. Haller et al., 2012] Haller, M., Perers, B., Bale, C., Paavilainen, J., Dalibard, A. Fischer, S. & Bertram, E.
    (2012). TRNSYS Type 832 v5.00 " Dynamic Collector Model by Bengt Perers". Updated Input-Output Reference.
    """

    xgain = 1
    xgainmax = 100
    exit = False
    while exit == False:
        qgain_Whperm2 = q_rad_Whperm2 - c1 * (DT[1]) - c2 * abs(DT[1]) * DT[
            1]  # heat production from solar collector, eq.(5)

        if Mfl > 0:
            Tout = ((Mfl * Cp_waterglycol * Tin) / aperture_area_m2 - (C_eff * Tin) / (2 * delts) + qgain_Whperm2 + (
                C_eff * Tfl[1]) / delts) / (Mfl * Cp_waterglycol / aperture_area_m2 + C_eff / (2 * delts))  # eq.(6)
            Tfl[2] = (Tin + Tout) / 2
            DT[2] = Tfl[2] - Te
            qdiff = Mfl / aperture_area_m2 * Cp_waterglycol * 2 * (DT[2] - DT[1])
        else:
            Tout = Tfl[1] + (qgain_Whperm2 * delts) / C_eff  # eq.(8)
            Tfl[2] = Tout
            DT[2] = Tfl[2] - Te
            qdiff = 5 * (DT[2] - DT[1])

        if abs(qdiff < 0.1):
            DT[1] = DT[2]
            exit = True
        else:
            if xgain > 40:
                DT[1] = (DT[1] + DT[2]) / 2
                if xgain == xgainmax:
                    exit = True
            else:
                DT[1] = DT[2]
        xgain += 1

    # FIXME: redundant...
    # qout = Mfl * Cp_waterglycol * (Tout - Tin) / aperture_area
    # qmtherm = (Tfl[2] - Tfl[1]) * C_eff / delts
    # qbal = qgain - qout - qmtherm
    # if abs(qbal) > 1:
    #     qbal = qbal
    return qgain_Whperm2


def calc_qloss_network(Mfl, Le, Area_a, Tm, Te, maxmsc):
    """
    calculate non-recoverable losses
    :param Mfl: mass flow rate [kg/s]
    :param Le: length per aperture area [m/m2 aperture]
    :param Area_a: aperture area [m2]
    :param Tm: mean temperature
    :param Te: ambient temperature
    :param maxmsc: maximum mass flow [kg/s]
    :return:

    ..[ J. Fonseca et al., 2016] Fonseca, J., Nguyen, T-A., Schlueter, A., Marechal, F. City Energy Analyst:
    Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts.
    Energy and Buildings, 2016.
    ..
    """
    qloss_kW = settings.k_msc_max_WpermK * Le * Area_a * (Tm - Te) * (
        Mfl / maxmsc) / 1000  # eq. (61) non-recoverable losses

    return qloss_kW  # in kW


def calc_IAM_beam_SC(solar_properties, teta_z_deg, tilt_angle_deg, type_SCpanel, latitude):
    """
    Calculates Incidence angle modifier for beam radiation.

    :param Az_rad: Solar azimuth angle [rad]
    :param g_rad: declination [rad]
    :param ha_rad: hour angle [rad]
    :param teta_z_rad: panel surface azimuth angle [rad]
    :param tilt_angle: panel tilt angle
    :param type_SCpanel: type of solar collector
    :param Sz_vector: solar zenith angle
    :return IAM_b_vector:
    """

    def calc_teta_L(Az, teta_z, tilt, Sz):
        teta_la = tan(Sz) * cos(teta_z - Az)
        teta_l_deg = degrees(abs(atan(teta_la) - tilt))
        if teta_l_deg < 0:
            teta_l_deg = min(89, abs(teta_l_deg))
        if teta_l_deg >= 90:
            teta_l_deg = 89.999
        return teta_l_deg  # longitudinal incidence angle in degrees

    def calc_teta_T(Az, Sz, teta_z):
        teta_ta = sin(Sz) * sin(abs(teta_z - Az))
        teta_T_deg = degrees(atan(teta_ta / cos(teta_ta)))
        if teta_T_deg < 0:
            teta_T_deg = min(89, abs(teta_T_deg))
        if teta_T_deg >= 90:
            teta_T_deg = 89.999
        return teta_T_deg  # transversal incidence angle in degrees

    def calc_teta_L_max(teta_L_deg):
        if teta_L_deg < 0:
            teta_L_deg = min(89, abs(teta_L_deg))
        if teta_L_deg >= 90:
            teta_L_deg = 89.999
        return teta_L_deg

    def calc_IAMb(teta_l, teta_T, type_SCpanel):
        if type_SCpanel == 'FP':  # # Flat plate collector   1636: SOLEX BLU, SPF, 2012
            IAM_b = -0.00000002127039627042 * teta_l ** 4 + 0.00000143550893550934 * teta_l ** 3 - 0.00008493589743580050 * teta_l ** 2 + 0.00041588966590833100 * teta_l + 0.99930069929920900000
        if type_SCpanel == 'ET':  # # evacuated tube   Zewotherm ZEWO-SOL ZX 30, SPF, 2012
            IAML = -0.00000003365384615386 * teta_l ** 4 + 0.00000268745143745027 * teta_l ** 3 - 0.00010196678321666700 * teta_l ** 2 + 0.00088830613832779900 * teta_l + 0.99793706293541500000
            IAMT = 0.000000002794872 * teta_T ** 5 - 0.000000534731935 * teta_T ** 4 + 0.000027381118880 * teta_T ** 3 - 0.000326340326281 * teta_T ** 2 + 0.002973799531468 * teta_T + 1.000713286764210
            IAM_b = IAMT * IAML  # overall incidence angle modifier for beam radiation
        return IAM_b

    # convert to radians
    g_rad = np.radians(solar_properties.g)
    ha_rad = np.radians(solar_properties.ha)
    Sz_rad = np.radians(solar_properties.Sz)
    Az_rad = np.radians(solar_properties.Az)
    lat_rad = radians(latitude)
    teta_z_rad = radians(teta_z_deg)
    tilt_rad = radians(tilt_angle_deg)

    Incidence_angle_rad = np.vectorize(solar_equations.calc_incident_angle_beam)(g_rad, lat_rad, ha_rad, tilt_rad,
                                                                                 teta_z_rad)  # incident angle in radians

    # calculate incident angles
    if type_SCpanel == 'FP':
        incident_angle_deg = np.degrees(Incidence_angle_rad)
        Teta_L_deg = np.vectorize(calc_teta_L_max)(incident_angle_deg)
        Teta_T_deg = 0  # not necessary for flat plate collectors
    if type_SCpanel == 'ET':
        Teta_L_deg = np.vectorize(calc_teta_L)(Az_rad, teta_z_rad, tilt_rad, Sz_rad)  # in degrees
        Teta_T_deg = np.vectorize(calc_teta_T)(Az_rad, Sz_rad, teta_z_rad)  # in degrees

    # calculate incident angle modifier for beam radiation
    IAM_b_vector = np.vectorize(calc_IAMb)(Teta_L_deg, Teta_T_deg, type_SCpanel)

    return IAM_b_vector


def calc_properties_SC_db(database_path, type_SCpanel):
    """
    To assign SC module properties according to panel types.

    :param type_SCpanel: type of SC panel used
    :type type_SCpanel: string
    :return: dict with Properties of the panel taken form the database
    """

    data = pd.read_excel(database_path, sheetname="SC")
    panel_properties = data[data['code'] == type_SCpanel].reset_index().T.to_dict()[0]

    return panel_properties


def calc_Eaux_SC(specific_flow_kgpers, dP_collector_Pa, Leq_mperm2, l_int_mperm2, Aa_m2):
    """
    Calculate auxiliary electricity for pumping heat transfer fluid in solar collectors.
    This include pressure losses from pipe friction, collector, and the building head.

    :param specific_flow_kgpers: mass flow [kg/s]
    :param dP_collector_Pa: pressure loss per module [Pa]
    :param Leq_mperm2: total pipe length per aperture area [m]
    :param Aa_m2: aperture area [m2]
    :return:
    """
    dP_friction_Pa = settings.dpl_Paperm * Leq_mperm2 * Aa_m2 * settings.fcr  # HANZENWILIAMSN PA
    dP_building_head_Pa = (l_int_mperm2 / 2) * Aa_m2 * settings.Ro_kgperm3 * 9.8  # dP = H*rho*g, g = 9.8 m/s^2
    Eaux_kW = (specific_flow_kgpers / settings.Ro_kgperm3) * (
        dP_collector_Pa + dP_friction_Pa + dP_building_head_Pa) / settings.eff_pumping / 1000  # kW from pumps
    return Eaux_kW  # energy spent in kW


def calc_optimal_mass_flow(q1, q2, q3, q4, E1, E2, E3, E4, m1, m2, m3, m4, dP1, dP2, dP3, dP4, Area_a):
    """
    This function determines the optimal mass flow rate and the corresponding pressure drop that maximize the
    total heat production in every time-step. It is done by maximizing the energy generation function (balance equation)
    assuming the electricity requirement is twice as valuable as the thermal output of the solar collector.

    :param q1: qout [kW] at zero flow rate
    :param q2: qout [kW] at nominal flow rate (mB0)
    :param q3: qout [kW] at maximum flow rate (mB_max)
    :param q4: qout [kW] at minimum flow rate (mB_min)
    :param E1: auxiliary electricity used at zero flow rate [kW]
    :param E2: auxiliary electricity used at nominal flow rate [kW]
    :param E3: auxiliary electricity used at max flow rate [kW]
    :param E4: auxiliary electricity used at min flow rate [kW]
    :param m1: zero flow rate [kg/hr/m2 aperture]
    :param m2: nominal flow rate (mB0) [kg/hr/m2 aperture]
    :param m3: maximum flow rate (mB_max) [kg/hr/m2 aperture]
    :param m4: minimum flow rate (mB_min) [kg/hr/m2 aperture]
    :param dP1: pressure drop [Pa/m2] at zero flow rate
    :param dP2: pressure drop [Pa/m2] at nominal flow rate (mB0)
    :param dP3: pressure drop [Pa/m2] at maximum flow rate (mB_max)
    :param dP4: pressure drop [Pa/m2] at minimum flow rate (mB_min)
    :param Area_a: aperture area [m2]
    :return mass_flow_opt: optimal mass flow at each hour [kg/s]
    :return dP_opt: pressure drop at optimal mass flow at each hour [Pa]

    ..[ J. Fonseca et al., 2016] Fonseca, J., Nguyen, T-A., Schlueter, A., Marechal, F. City Energy Analyst:
    Integrated framework for analysis and optimization of building energy systems in neighborhoods and city districts.
    Energy and Buildings, 2016.

    """

    mass_flow_opt = np.empty(8760)
    dP_opt = np.empty(8760)
    const = Area_a / 3600
    mass_flow_all_kgpers = [m1 * const, m2 * const, m3 * const, m4 * const]  # [kg/s]
    dP_all_Pa = [dP1 * Area_a, dP2 * Area_a, dP3 * Area_a, dP4 * Area_a]  # [Pa]
    balances = [q1 - E1 * 2, q2 - E2 * 2, q3 - E3 * 2, q4 - E4 * 2]  # energy generation function eq.(63)
    for time in range(8760):
        balances_time = [balances[0][time], balances[1][time], balances[2][time], balances[3][time]]
        max_heat_production = np.max(balances_time)
        ix_max_heat_production = np.where(balances_time == max_heat_production)
        mass_flow_opt[time] = mass_flow_all_kgpers[ix_max_heat_production[0][0]]
        dP_opt[time] = dP_all_Pa[ix_max_heat_production[0][0]]
    return mass_flow_opt, dP_opt


def calc_optimal_mass_flow_2(m, q, dp):
    """
    Set mass flow and pressure drop to zero if the heat balance is negative.

    :param m: mass flow rate [kg/s]
    :param q: qout [kW]
    :param dp: pressure drop [Pa]
    :return m: hourly mass flow rate [kg/s]
    :return dp: hourly pressure drop [Pa]
    """
    for time in range(8760):
        if q[time] <= 0:
            m[time] = 0
            dp[time] = 0
    return m, dp


# investment and maintenance costs
def calc_Cinv_SC(Area_m2, locator, config, technology=0):
    """
    Lifetime 35 years
    """

    SC_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="SC")
    technology_code = list(set(SC_cost_data['code']))
    SC_cost_data[SC_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if Area_m2 < SC_cost_data['cap_min'][0]:
        Area_m2 = SC_cost_data['cap_min'][0]
    SC_cost_data = SC_cost_data[
        (SC_cost_data['cap_min'] <= Area_m2) & (SC_cost_data['cap_max'] > Area_m2)]
    Inv_a = SC_cost_data.iloc[0]['a']
    Inv_b = SC_cost_data.iloc[0]['b']
    Inv_c = SC_cost_data.iloc[0]['c']
    Inv_d = SC_cost_data.iloc[0]['d']
    Inv_e = SC_cost_data.iloc[0]['e']
    Inv_IR = (SC_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = SC_cost_data.iloc[0]['LT_yr']
    Inv_OM = SC_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (Area_m2) ** Inv_c + (Inv_d + Inv_e * Area_m2) * log(Area_m2)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    return Capex_a, Opex_fixed


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running solar-collector with scenario = %s' % config.scenario)
    print('Running solar-collector with date-start = %s' % config.solar.date_start)
    print('Running solar-collector with dpl = %s' % config.solar.dpl)
    print('Running solar-collector with eff-pumping = %s' % config.solar.eff_pumping)
    print('Running solar-collector with fcr = %s' % config.solar.fcr)
    print('Running solar-collector with k-msc-max = %s' % config.solar.k_msc_max)
    print('Running solar-collector with min-radiation = %s' % config.solar.min_radiation)
    print('Running solar-collector with panel-on-roof = %s' % config.solar.panel_on_roof)
    print('Running solar-collector with panel-on-wall = %s' % config.solar.panel_on_wall)
    print('Running solar-collector with ro = %s' % config.solar.ro)
    print('Running solar-collector with solar-window-solstice = %s' % config.solar.solar_window_solstice)
    print('Running solar-collector with t-in-pvt = %s' % config.solar.t_in_pvt)
    print('Running solar-collector with t-in-sc = %s' % config.solar.t_in_sc)
    print('Running solar-collector with type-pvpanel = %s' % config.solar.type_pvpanel)
    print('Running solar-collector with type-scpanel = %s' % config.solar.type_scpanel)

    list_buildings_names = locator.get_zone_building_names()

    with fiona.open(locator.get_zone_geometry()) as shp:
        longitude = shp.crs['lon_0']
        latitude = shp.crs['lat_0']

    # list_buildings_names =['B026', 'B036', 'B039', 'B043', 'B050'] for missing buildings
    for building in list_buildings_names:
        radiation = locator.get_radiation_building(building_name=building)
        radiation_metadata = locator.get_radiation_metadata(building_name=building)
        calc_SC(locator=locator, config=config, radiation_csv=radiation, metadata_csv=radiation_metadata,
                latitude=latitude,
                longitude=longitude, weather_path=config.weather, building_name=building)

    for i, building in enumerate(list_buildings_names):
        data = pd.read_csv(locator.SC_results(building))
        if i == 0:
            df = data
        else:
            df = df + data
    del df[df.columns[0]]
    df.to_csv(locator.SC_totals(), index=True, float_format='%.2f')


if __name__ == '__main__':
    main(cea.config.Configuration())
