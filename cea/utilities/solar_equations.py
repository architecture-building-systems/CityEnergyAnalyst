"""
solar equations
"""


from __future__ import division
import numpy as np
import pandas as pd
import ephem
import datetime
import collections
from math import degrees, radians, cos, acos, tan, atan, sin, asin, pi


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# import ephem library

def _ephem_setup(latitude, longitude, altitude, pressure, temperature):
    # observer
    obs = ephem.Observer()
    obs.lat = str(latitude)
    obs.lon = str(longitude)
    obs.elevation = altitude
    obs.pressure = pressure / 100.
    obs.temp = temperature

    #sun
    sun = ephem.Sun()
    return obs, sun


def pyephem(time, latitude, longitude, altitude=0, pressure=101325,
            temperature=12):

    # Written by Will Holmgren (@wholmgren), University of Arizona, 2014

    try:
        time_utc = time.tz_convert('UTC')
    except TypeError:
        time_utc = time

    sun_coords = pd.DataFrame(index=time)

    obs, sun = _ephem_setup(latitude, longitude, altitude,
                            pressure, temperature)

    # make and fill lists of the sun's altitude and azimuth
    # this is the pressure and temperature corrected apparent alt/az.
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['apparent_elevation'] = alts
    sun_coords['apparent_azimuth'] = azis

    # redo it for p=0 to get no atmosphere alt/az
    obs.pressure = 0
    alts = []
    azis = []
    for thetime in time_utc:
        obs.date = ephem.Date(thetime)
        sun.compute(obs)
        alts.append(sun.alt)
        azis.append(sun.az)

    sun_coords['elevation'] = alts
    sun_coords['azimuth'] = azis

    # convert to degrees. add zenith
    sun_coords = np.rad2deg(sun_coords)
    sun_coords['apparent_zenith'] = 90 - sun_coords['apparent_elevation']
    sun_coords['zenith'] = 90 - sun_coords['elevation']

    return sun_coords

# solar properties
SunProperties = collections.namedtuple('SunProperties',  ['g', 'Sz', 'Az', 'ha', 'trr_mean', 'worst_sh', 'worst_Az'])


def calc_sun_properties(latitude, longitude, weather_data, date_start, solar_window_solstice):

    date = pd.date_range(date_start, periods=8760, freq='H')
    hour_date = date.hour
    min_date = date.minute
    day_date = date.dayofyear
    worst_hour = calc_worst_hour(latitude, weather_data, solar_window_solstice)

    # solar elevation, azuimuth and values for the 9-3pm period of no shading on the solar solstice
    sun_coords = pyephem(date, latitude, longitude)
    sun_coords['declination'] = np.vectorize(declination_degree)(day_date, 365)
    sun_coords['hour_angle'] = np.vectorize(get_hour_angle)(longitude, min_date, hour_date, day_date)
    worst_sh = sun_coords['elevation'].loc[date[worst_hour]]
    worst_Az = sun_coords['azimuth'].loc[date[worst_hour]]

    # mean transmissivity
    weather_data['diff'] = weather_data.difhorrad_Whm2 / weather_data.glohorrad_Whm2
    T_G_hour = weather_data[np.isfinite(weather_data['diff'])]
    T_G_day = np.round(T_G_hour.groupby(['dayofyear']).mean(), 2)
    T_G_day['diff'] = T_G_day['diff'].replace(1, 0.90)
    transmittivity = (1 - T_G_day['diff']).mean()

    return SunProperties(g=sun_coords['declination'], Sz=sun_coords['zenith'], Az=sun_coords['azimuth'],
                         ha=sun_coords['hour_angle'], trr_mean=transmittivity, worst_sh=worst_sh, worst_Az=worst_Az)


def calc_sunrise(sunrise, Yearsimul, longitude, latitude):
    o, s = _ephem_setup(latitude, longitude, altitude=0, pressure=101325, temperature=12)
    for day in range(1, 366):  # Calculated according to NOAA website
        o.date = datetime.datetime(Yearsimul, 1, 1) + datetime.timedelta(day - 1)
        next_event = o.next_rising(s)
        sunrise[day - 1] = next_event.datetime().hour
    return sunrise


def declination_degree(day_date, TY):
    """The declination of the sun is the angle between Earth's equatorial plane and a line
    between the Earth and the sun. It varies between 23.45 degrees and -23.45 degrees,
    hitting zero on the equinoxes and peaking on the solstices. [1]_

    :param when: datetime.datetime, date/time for which to do the calculation
    :param TY: float, Total number of days in a year. eg. 365 days per year,(no leap days)
    :param DEC: float,  The declination of the Sun

    .. [1] http://pysolar.org/
    """

    return 23.45 * np.vectorize(sin)((2 * pi / (TY)) * (day_date - 81))


def get_hour_angle(longitude_deg, min_date, hour_date, day_date):
    solar_time = get_solar_time(longitude_deg, min_date, hour_date, day_date)
    return 15 * (12 - solar_time)


def get_solar_time(longitude_deg, min_date, hour_date, day_date):
    """
    returns solar time in hours for the specified longitude and time,
    accurate only to the nearest minute.
    longitude_deg
    min_date
    hour_date
    day_date
    """
    solar_time_min = hour_date * 60 + min_date + 4 * longitude_deg + get_equation_of_time(day_date)

    return solar_time_min/60


def get_equation_of_time(day_date):
    B = (day_date-1)*360/365
    E = 229.2 * (0.000075 + 0.001868 * cos(B) - 0.032077 * sin(B) - 0.014615 * cos(2 * B) - 0.04089 * sin(2 * B))
    return E


# filter sensor points with low solar potential

def filter_low_potential(weather_data, radiation_json_path, metadata_csv_path, min_radiation, panel_on_roof, panel_on_wall):
    """
    To filter the sensor points/hours with low radiation potential.

    #. keep sensors above min radiation
    #. eliminate points when hourly production < 50 W/m2

    :param weather_data: weather data read from the epw file
    :type weather_data: dataframe
    :param radiation_csv: solar insulation data on all surfaces of each building
    :type radiation_csv: .csv
    :param metadata_csv: solar insulation sensor data of each building
    :type metadata_csv: .csv
    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables
    :return max_yearly_radiation: yearly horizontal radiation [Wh/m2/year]
    :rtype max_yearly_radiation: float
    :return min_yearly_radiation: minimum yearly radiation threshold for sensor selection [Wh/m2/year]
    :rtype min_yearly_radiation: float
    :return sensors_rad_clean: radiation data of the filtered sensors [Wh/m2]
    :rtype sensors_rad_clean: dataframe
    :return sensors_metadata_clean: data of filtered sensor points measuring solar insulation of each building
    :rtype sensors_metadata_clean: dataframe

    Following assumptions are made:

    #. Sensor points with low yearly radiation are deleted. The threshold (minimum yearly radiation) is a percentage
       of global horizontal radiation. The percentage threshold (min_radiation) is a global variable defined by users.
    #. For each sensor point kept, the radiation value is set to zero when radiation value is below 50 W/m2.
    #. No solar panels on windows.
    """
    # get max radiation potential from global horizontal radiation
    yearly_horizontal_rad = weather_data.glohorrad_Whm2.sum()  # [Wh/m2/year]

    # read radiation file
    sensors_rad = pd.read_json(radiation_json_path)
    sensors_metadata = pd.read_csv(metadata_csv_path)

    # join total radiation to sensor_metadata

    sensors_rad_sum = sensors_rad.sum(0).to_frame('total_rad_Whm2') # add new row with yearly radiation
    sensors_metadata.set_index('SURFACE', inplace=True)
    sensors_metadata = sensors_metadata.merge(sensors_rad_sum, left_index=True, right_index=True)    #[Wh/m2]

    # remove window surfaces
    sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'windows']

    # keep sensors if allow pv installation on walls or on roofs
    if panel_on_roof is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'roofs']
    if panel_on_wall is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'walls']

    # keep sensors above min production in sensors_rad
    max_yearly_radiation = yearly_horizontal_rad
    # set min yearly radiation threshold for sensor selection
    min_yearly_radiation = max_yearly_radiation * min_radiation
    sensors_metadata_clean = sensors_metadata[sensors_metadata.total_rad_Whm2 >= min_yearly_radiation]
    sensors_rad_clean = sensors_rad[sensors_metadata_clean.index.tolist()] # keep sensors above min radiation

    sensors_rad_clean[sensors_rad_clean[:] <= 50] = 0   # eliminate points when hourly production < 50 W/m2

    return max_yearly_radiation, min_yearly_radiation, sensors_rad_clean, sensors_metadata_clean


# optimal tilt angle and spacing of solar panels

def optimal_angle_and_tilt(sensors_metadata_clean, latitude, solar_properties, Max_Isol_Whperm2yr, panel_properties):
    """
    This function first determines the optimal tilt angle, row spacing and surface azimuth of panels installed at each
    sensor point. Secondly, the installed PV module areas at each sensor point are calculated. Lastly, all the modules
    are categorized with its surface azimuth, tilt angle, and yearly radiation. The output will then be used to
    calculate the absorbed radiation.

    :param sensors_metadata_clean: data of filtered sensor points measuring solar insulation of each building
    :type sensors_metadata_clean: dataframe
    :param latitude: latitude of the case study location
    :type latitude: float
    :param solar_properties: A SunProperties, using worst_sh: solar elevation at the worst hour [degree], worst_Az: solar azimuth at the worst hour [degree]
                           and trr_mean: transmissivity / clearness index [-]
    :type solar_properties: cea.utilities.solar_equations.SunProperties
    :param module_length_m: length of the PV module [m]
    :type module_length_m: float
    :param Max_Isol_Whperm2yr: max radiation potential (equals to global horizontal radiation) [Wh/m2/year]
    :type Max_Isol_Whperm2yr: float

    :returns sensors_metadata_clean: data of filtered sensor points categorized with module tilt angle, array spacing,
        surface azimuth, installed PV module area of each sensor point and the categories
    :rtype sensors_metadata_clean: dataframe

    Assumptions:

    #. Tilt angle: If the sensor is on tilted roof, the panel will have the same tilt as the roof. If the sensor is on
       a wall, the tilt angle is 90 degree. Tilt angles for flat roof is determined using the method from Quinn et al.
    #. Row spacing: Determine the row spacing by minimizing the shadow according to the solar elevation and azimuth at
       the worst hour of the year. The worst hour is a global variable defined by users.
    #. Surface azimuth (orientation) of panels: If the sensor is on a tilted roof, the orientation of the panel is the
        same as the roof. Sensors on flat roofs are all south facing.
    """
    # calculate panel tilt angle (B) for flat roofs (tilt < 5 degrees), slope roofs and walls.
    optimal_angle_flat_deg = calc_optimal_angle(180, latitude, solar_properties.trr_mean) # assume surface azimuth = 180 (N,E), south facing
    sensors_metadata_clean['tilt_deg']= np.vectorize(acos)(sensors_metadata_clean['Zdir']) #surface tilt angle in rad
    sensors_metadata_clean['tilt_deg'] = np.vectorize(degrees)(sensors_metadata_clean['tilt_deg']) #surface tilt angle in degrees
    sensors_metadata_clean['B_deg'] = np.where(sensors_metadata_clean['tilt_deg'] >= 5, sensors_metadata_clean['tilt_deg'],
                                           degrees(optimal_angle_flat_deg)) # panel tilt angle in degrees

    # calculate spacing and surface azimuth of the panels for flat roofs
    module_length_m = panel_properties['module_length_m']
    optimal_spacing_flat_m = calc_optimal_spacing(solar_properties, optimal_angle_flat_deg, module_length_m)
    sensors_metadata_clean['array_spacing_m'] = np.where(sensors_metadata_clean['tilt_deg'] >= 5, 0, optimal_spacing_flat_m)
    sensors_metadata_clean['surface_azimuth_deg'] = np.vectorize(calc_surface_azimuth)(sensors_metadata_clean['Xdir'],
                                                                                       sensors_metadata_clean['Ydir'],
                                                                                       sensors_metadata_clean['B_deg'])  # degrees

    # calculate the surface area required to install one pv panel on flat roofs with defined tilt angle and array spacing
    if panel_properties['type'] == 'PV':
        module_width_m = module_length_m  # for PV
    else:
        module_width_m = panel_properties['module_area_m2']/module_length_m # for FP, ET
    module_flat_surface_area_m2 = module_width_m * (sensors_metadata_clean.array_spacing_m / 2 +
                                                    module_length_m * cos(optimal_angle_flat_deg))
    area_per_module_m2 = module_width_m * module_length_m

    # calculate the pv/solar collector module area within the area of each sensor point
    sensors_metadata_clean['area_installed_module_m2'] = np.where(sensors_metadata_clean['tilt_deg'] >= 5,
                                                                  sensors_metadata_clean.AREA_m2,
                                                                  area_per_module_m2 *
                                                                  (sensors_metadata_clean.AREA_m2 / module_flat_surface_area_m2))

    # categorize the sensors by surface_azimuth, B, GB
    result = np.vectorize(calc_categoriesroof)(sensors_metadata_clean.surface_azimuth_deg, sensors_metadata_clean.B_deg,
                                               sensors_metadata_clean.total_rad_Whm2, Max_Isol_Whperm2yr)
    sensors_metadata_clean['CATteta_z'] = result[0]
    sensors_metadata_clean['CATB'] = result[1]
    sensors_metadata_clean['CATGB'] = result[2]
    return sensors_metadata_clean

def calc_optimal_angle(teta_z, latitude, transmissivity):
    """
    To calculate the optimal tilt angle of the solar panels.

    :param teta_z: surface azimuth, 0 degree south (east negative) or 0 degree north (east positive)
    :type teta_z: float
    :param latitude: latitude of the case study site
    :type latitude: float
    :param transmissivity: clearness index [-]
    :type transmissivity: float
    :return abs(b): optimal tilt angle [radians]
    :rtype abs(b): float

    ..[Quinn et al., 2013] S.W.Quinn, B.Lehman.A simple formula for estimating the optimum tilt angles of photovoltaic
    panels. 2013 IEEE 14th Work Control Model Electron, Jun, 2013, pp.1-8
    """
    if transmissivity <= 0.15:
        gKt = 0.977
    elif 0.15 < transmissivity <= 0.7:
        gKt = 1.237 - 1.361 * transmissivity
    else:
        gKt = 0.273
    Tad = 0.98  # transmittance-absorptance product of the diffuse radiation
    Tar = 0.97  # transmittance-absorptance product of the reflected radiation
    Pg = 0.2    # ground reflectance of 0.2
    l = radians(latitude)
    a = radians(teta_z)
    b = atan((cos(a) * tan(l)) * (1 / (1 + ((Tad * gKt - Tar * Pg) / (2 * (1 - gKt))))))  # eq.(11)
    return abs(b)

def calc_optimal_spacing(sun_properties, tilt_angle, module_length):
    """
    To calculate the optimal spacing between each panel to avoid shading.

    :param sun_properties: SunProperties, using worst_sh (Solar elevation at the worst hour [degree]) and worst_Az
                           (Solar Azimuth [degree] at the worst hour)
    :type sun_properties: SunProperties
    :param tilt_angle: optimal tilt angle for panels on flat surfaces [degree]
    :type tilt_angle: float
    :param module_length: [m]
    :type module_length: float
    :return D: optimal distance in [m]
    :rtype D: float
    """
    h = module_length * sin(tilt_angle)
    D1 = h / tan(radians(sun_properties.worst_sh))
    D = max(D1 * cos(radians(180 - sun_properties.worst_Az)), D1 * cos(radians(sun_properties.worst_Az - 180)))
    return D

def calc_categoriesroof(teta_z, B, GB, Max_Isol):
    """
    To categorize solar panels by the surface azimuth, tilt angle and yearly radiation.

    :param teta_z: surface azimuth [degree], 0 degree north (east positive, west negative)
    :type teta_z: float
    :param B: solar panel tile angle [degree]
    :type B: float
    :param GB: yearly radiation of sensors [Wh/m2/year]
    :type GB: float
    :param Max_Isol: yearly global horizontal radiation [Wh/m2/year]
    :type Max_Isol: float
    :return CATteta_z: category of surface azimuth
    :rtype CATteta_z: float
    :return CATB: category of tilt angle
    :rtype CATB: float
    :return CATBG: category of yearly radiation
    :rtype CATBG: float
    """
    if -122.5 < teta_z <= -67:
        CATteta_z = 1
    elif -67 < teta_z <= -22.5:
        CATteta_z = 3
    elif -22.5 < teta_z <= 22.5:
        CATteta_z = 5
    elif 22.5 < teta_z <= 67:
        CATteta_z = 4
    elif 67 <= teta_z <= 122.5:
        CATteta_z = 2
    else:
        CATteta_z = 6
    B = degrees(B)
    if 0 < B <= 5:
        CATB = 1  # flat roof
    elif 5 < B <= 15:
        CATB = 2  # tilted 5-15 degrees
    elif 15 < B <= 25:
        CATB = 3  # tilted 15-25 degrees
    elif 25 < B <= 40:
        CATB = 4  # tilted 25-40 degrees
    elif 40 < B <= 60:
        CATB = 5  # tilted 40-60 degrees
    elif B > 60:
        CATB = 6  # tilted >60 degrees
    else:
        CATB = None
        print('B not in expected range')

    GB_percent = GB / Max_Isol
    if 0 < GB_percent <= 0.25:
        CATGB = 1
    elif 0.25 < GB_percent <= 0.50:
        CATGB = 2
    elif 0.50 < GB_percent <= 0.75:
        CATGB = 3
    elif 0.75 < GB_percent <= 0.90:
        CATGB = 4
    elif 0.90 < GB_percent:
        CATGB = 5
    else:
        CATGB = None
        print('GB not in expected range')

    return CATteta_z, CATB, CATGB

def calc_surface_azimuth(xdir, ydir, B):
    """
    Calculate surface azimuth from the surface normal vector (x,y,z) and tilt angle (B).
    Following the geological sign convention, an azimuth of 0 and 360 degree represents north, 90 degree is east.

    :param xdir: surface normal vector x in (x,y,z) representing east-west direction
    :param ydir: surface normal vector y in (x,y,z) representing north-south direction
    :param B: surface tilt angle in degree
    :type xdir: float
    :type ydir: float
    :type B: float
    :returns surface azimuth: the azimuth of the surface of a solar panel in degree
    :rtype surface_azimuth: float

    """
    B = radians(B)
    teta_z = degrees(asin(xdir / sin(B)))
    # set the surface azimuth with on the sing convention (E,N)=(+,+)
    if xdir < 0:
        if ydir <0:
            surface_azimuth = 180 + teta_z     # (xdir,ydir) = (-,-)
        else: surface_azimuth = 360 + teta_z   # (xdir,ydir) = (-,+)
    elif ydir < 0:
        surface_azimuth = 180 + teta_z         # (xdir,ydir) = (+,-)
    else: surface_azimuth = teta_z             # (xdir,ydir) = (+,+)
    return surface_azimuth  # degree

# calculate angle of incident

def calc_incident_angle_beam(g, lat, ha, tilt, teta_z):
    # calculate incident angle beam radiation
    part1 = sin(lat) * sin(g) * cos(tilt) - cos(lat) * sin(g) * sin(tilt) * cos(teta_z)
    part2 = cos(lat) * cos(g) * cos(ha) * cos(tilt) + sin(lat) * cos(g) * cos(ha) * sin(tilt) * cos(teta_z)
    part3 = cos(g) * sin(ha) * sin(tilt) * sin(teta_z)
    teta_B = acos(part1 + part2 + part3)
    return teta_B  # in radains

def calc_angle_of_incidence(g, lat, ha, tilt, teta_z):
    """
    To calculate angle of incidence from solar vector and surface normal vector.
    (Validated with Sandia pvlib.irrandiance.aoi)

    :param lat: latitude of the loacation of case study [radians]
    :param g: declination of the solar position [radians]
    :param ha: hour angle [radians]
    :param tilt: panel surface tilt angle [radians]
    :param teta_z: panel surface azimuth angle [radians]
    :type lat: float
    :type g: float
    :type ha: float
    :type tilt: float
    :type teta_z: float
    :return teta_B: angle of incidence [radians]
    :rtype teta_B: float

    .. [Sproul, A. B., 2017] Sproul, A.B. (2007). Derivation of the solar geometric relationships using vector analysis.
       Renewable Energy, 32(7), 1187-1205.
    """
    # surface normal vector
    n_E = sin(tilt)*sin(teta_z)
    n_N = sin(tilt)*cos(teta_z)
    n_Z = cos(tilt)
    # solar vector
    s_E = -cos(g)*sin(ha)
    s_N = sin(g)*cos(lat) - cos(g)*sin(lat)*cos(ha)
    s_Z = cos(g)*cos(lat)*cos(ha) + sin(g)*sin(lat)

    # angle of incidence
    teta_B = acos(n_E*s_E + n_N*s_N + n_Z*s_Z)
    return teta_B

# calculate sensor properties in each group

def calc_groups(sensors_rad_clean, sensors_metadata_cat):
    """
    To calculate the mean hourly radiation of sensors in each group.

    :param sensors_rad_clean: radiation data of the filtered sensors
    :type sensors_rad_clean: dataframe
    :param sensors_metadata_cat: data of filtered sensor points categorized with module tilt angle, array spacing,
                                 surface azimuth, installed PV module area of each sensor point
    :type sensors_metadata_cat: dataframe
    :return number_groups: number of groups of sensor points
    :rtype number_groups: float
    :return hourlydata_groups: mean hourly radiation of sensors in each group
    :rtype hourlydata_groups: dataframe
    :return number_points: number of sensor points in each group
    :rtype number_points: array
    :return prop_observers: mean values of sensor properties of each group of sensors
    :rtype prop_observers: dataframe
    """
    # calculate number of groups as number of optimal combinations.
    sensors_metadata_cat['type_orientation'] = sensors_metadata_cat['TYPE'] + '_' +sensors_metadata_cat['orientation']
    groups_ob = sensors_metadata_cat.groupby(['CATB', 'CATGB', 'CATteta_z', 'type_orientation']) # group the sensors by categories
    prop_observers = groups_ob.mean().reset_index()
    prop_observers = pd.DataFrame(prop_observers)
    total_area_installed_module_m2 = groups_ob['area_installed_module_m2'].sum().reset_index()['area_installed_module_m2']
    prop_observers['total_area_module_m2'] = total_area_installed_module_m2
    number_groups = groups_ob.size().count()
    sensors_list = groups_ob.groups.values()

    # calculate mean hourly radiation of sensors in each group
    rad_group_mean = np.empty(shape=(number_groups,8760))
    number_points = np.empty(shape=(number_groups,1))
    for x in range(0, number_groups):
        sensors_rad_group = sensors_rad_clean[sensors_list[x]]
        rad_mean = sensors_rad_group.mean(axis=1).as_matrix().T
        rad_group_mean[x] = rad_mean
        number_points[x] = len(sensors_list[x])
    hourlydata_groups = pd.DataFrame(rad_group_mean).T

    return number_groups, hourlydata_groups, number_points, prop_observers

# calculate the worst hour

def calc_worst_hour(latitude, weather_data, solar_window_solstice):
    """
    Calculate the first hour of solar window of the winter solstice for panel spacing.
    http://www.affordable-solar.com/learning-center/building-a-system/calculating-tilted-array-spacing/

    :param latitude: latitude of the site [degree]
    :type latitude: float
    :param weather_data: weather data of the site
    :type weather_data: pd.dataframe
    :param solar_window_solstice: the desired hour of shade-free solar window on the winter solstice.
    :type solar_window_solstice: floar
    :return worst_hour: the hour to calculate minimum spacing
    :rtype worst_hour: float


    """
    if latitude > 0:
        northern_solstice = weather_data.query('month == 12 & day == 21')
        worst_hour = northern_solstice[northern_solstice.hour == (12 - round(solar_window_solstice/2))].index[0]
    else:
        southern_solstice = weather_data.query('month == 6 & day == 21')
        worst_hour = southern_solstice[southern_solstice.hour == (12 - round(solar_window_solstice/2))].index[0]

    return worst_hour