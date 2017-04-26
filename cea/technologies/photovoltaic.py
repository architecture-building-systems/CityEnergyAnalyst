"""
photovoltaic
"""


from __future__ import division
import numpy as np
import pandas as pd
import math
from math import *
from cea.utilities import dbfreader
from scipy import interpolate

from cea.utilities import epwreader
from cea.utilities import solar_equations
import time

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca, Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# PV electricity generation

def calc_PV(locator, radiation_csv, metadata_csv, latitude, longitude, gv, weather_path, building_name):
    """
    This function first determine the surface area with sufficient solar radiation, and then decide the optimal tilt
    angles of panels at each surface location. The panels are categorized by their azimuths and tilt angles into groups
    of panels. The energy generation from PV panels of each group is then calculated.
    Parameters
    ----------
    locator
    radiation_csv
    metadata_csv
    latitude
    longitude
    gv
    weather_path
    building_name
    Returns
    -------
    """
    t0 = time.clock()

    # weather data
    weather_data = epwreader.epw_reader(weather_path)
    gv.log('reading weather data done')

    # solar properties
    g, Sz, Az, ha, trr_mean, worst_sh, worst_Az = solar_equations.calc_sun_properties(latitude, longitude, weather_data,
                                                                         gv)
    gv.log('calculating solar properties done')

    # select sensor point with sufficient solar radiation
    max_yearly_radiation, min_yearly_production, sensors_rad_clean, sensors_metadata_clean = \
        filter_low_potential(weather_data, radiation_csv, metadata_csv, gv)

    gv.log('filtering low potential sensor points done')

    if not sensors_metadata_clean.empty:
        # calculate optimal angle and tilt for panels
        sensors_metadata_cat = optimal_angle_and_tilt(sensors_metadata_clean, latitude, worst_sh, worst_Az, trr_mean,
                                                      gv.module_length_PV, max_yearly_radiation)
        gv.log('calculating optimal tile angle and separation done')

        # group the sensors with the same tilt, surface azimuth, and total radiation
        Number_groups, hourlydata_groups, number_points, prop_observers = calc_groups(sensors_rad_clean, sensors_metadata_cat)

        gv.log('generating groups of sensor points done')

        results, Final = calc_pv_generation(gv.type_PVpanel, hourlydata_groups, Number_groups, number_points,
                                        prop_observers, weather_data, g, Sz, Az, ha, latitude, gv.misc_losses)


        Final.to_csv(locator.PV_results(building_name= building_name), index=True, float_format='%.2f')  # print PV generation potential
        sensors_metadata_cat.to_csv(locator.metadata_results(building_name= building_name), index=True, float_format='%.2f')  # print selected metadata of the selected sensors
        gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)
    return

def filter_low_potential(weather_data, radiation_csv, metadata_csv, gv):
    """
    To filter the sensor points/hours with low radiation potential.
    Parameters
    ----------
    weather_data
    radiation_csv: radiation script generated from Paul's code (to be merged)
    metadata_csv: information of each radiation sensor (tilt angle, surface azimuth...)
    gv
    Returns
    -------
    Assumptions
    -----------
    1) Sensor points with low yearly radiation are deleted. The threshold (minimum yearly radiation) is a percentage
    of global horizontal radiation. The percentage threshold (min_radiation) is a global variable defined by users.
    2) For each sensor point kept, the radiation value is set to zero when radiation value is below 50 W/m2
    """
    # get max radiation potential from global horizontal radiation
    yearly_horizontal_rad = weather_data.glohorrad_Whm2.sum()  # [Wh/m2/year]

    # read radiation file
    sensors_rad = pd.read_csv(radiation_csv)
    sensors_metadata = pd.read_csv(metadata_csv)

    # join total radiation to sensor_metadata
    sensors_rad_sum = sensors_rad.sum(0).values # add new row with yearly radiation
    sensors_metadata['total_rad'] = sensors_rad_sum

    # remove window surfaces
    sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'window']

    # keep sensors if allow pv installation on walls or on roofs
    if gv.pvonroof is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'roof']
    if gv.pvonwall is False:
        sensors_metadata = sensors_metadata[sensors_metadata.TYPE != 'wall']

    # keep sensors above min production in sensors_rad
    sensors_metadata = sensors_metadata.set_index('SURFACE')
    max_yearly_radiation = yearly_horizontal_rad
    min_yearly_radiation = max_yearly_radiation * gv.min_radiation # set min yearly radiation threshold for sensor selection

    sensors_metadata_clean = sensors_metadata[sensors_metadata.total_rad >= min_yearly_radiation]
    sensors_rad_clean = sensors_rad[sensors_metadata_clean.index.tolist()] # keep sensors above min radiation

    sensors_rad_clean[sensors_rad_clean[:] <= 50] = 0   # eliminate points when hourly production < 50 W/m2

    return max_yearly_radiation, min_yearly_radiation, sensors_rad_clean, sensors_metadata_clean

  
def calc_pv_generation(type_panel, hourly_radiation, number_groups, number_points, prop_observers, weather_data,
                       g, Sz, Az, ha, latitude, misc_losses):


    lat = radians(latitude)
    g_vector = np.radians(g)
    ha_vector = np.radians(ha)
    Sz_vector = np.radians(Sz)
    Az_vector = np.radians(Az)
    result = list(range(number_groups))
    groups_area = list(range(number_groups))
    Sum_PV = np.zeros(8760)

    n = 1.526 # refractive index of galss
    Pg = 0.2  # ground reflectance
    K = 0.4   # extinction coefficien
    eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L = calc_properties_PV(type_panel)

    for group in range(number_groups):
        teta_z = prop_observers.loc[group,'orientation'] #azimuth of paneles of group
        area_per_group = prop_observers.loc[group,'total_area_pv']
        tilt_angle = prop_observers.loc[group,'tilt'] #tilt angle of panels
        radiation = pd.DataFrame({'I_sol':hourly_radiation[group]}) #choose vector with all values of Isol
        radiation['I_diffuse'] = weather_data.ratio_diffhout.fillna(0)*radiation.I_sol      #calculate diffuse radiation
        radiation['I_direct'] = radiation['I_sol'] - radiation['I_diffuse']   #direct radaition

        #to radians of properties - solar position and tilt angle
        tilt = radians(tilt_angle) #slope of panel
        teta_z = radians(teta_z) #azimuth of panel

        #calculate effective indicent angles necessary
        teta_vector = np.vectorize(Calc_incidenteangleB)(g_vector, lat, ha_vector, tilt, teta_z)
        teta_ed, teta_eg  = Calc_diffuseground_comp(tilt)

        results = np.vectorize(Calc_Sm_PV)(weather_data.drybulb_C,radiation.I_sol, radiation.I_direct, radiation.I_diffuse, tilt,
                                              Sz_vector, teta_vector, teta_ed, teta_eg,
                                              n, Pg, K,NOCT,a0,a1,a2,a3,a4,L)
        result[group] = np.vectorize(Calc_PV_power)(results[0], results[1], eff_nom, area_per_group, Bref,misc_losses)
        groups_area[group] = area_per_group

        Sum_PV = Sum_PV + result[group] # in kWh
    total_area = sum(groups_area)
    Final = pd.DataFrame({'PV_kWh':Sum_PV,'Area':total_area})
    return result, Final

def Calc_incidenteangleB(g, lat, ha, tilt, teta_z):
    # calculate incident angle beam radiation
    part1 = sin(lat) * sin(g) * cos(tilt) - cos(lat) * sin(g) * sin(tilt) * cos(teta_z)
    part2 = cos(lat) * cos(g) * cos(ha) * cos(tilt) + sin(lat) * cos(g) * cos(ha) * sin(tilt) * cos(teta_z)
    part3 = cos(g) * sin(ha) * sin(tilt) * sin(teta_z)
    teta_B = acos(part1 + part2 + part3)
    return teta_B  # in radains


def Calc_diffuseground_comp(tilt_radians):
    """
    To calculate reflected radiation and diffuse radiation.

    Parameters
    ----------
    tilt_radians

    Returns
    -------
    teta_ed: groups-reflected radiation
    teta_eg: diffuse radiation

    References
    ----------
    Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
    Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
    doi: 10.1002/9781118671603.ch5

    """
    tilt = degrees(tilt_radians)
    teta_ed = 59.68 - 0.1388 * tilt + 0.001497 * tilt ** 2  # angle in degrees
    teta_eG = 90 - 0.5788 * tilt + 0.002693 * tilt ** 2  # angle in degrees
    return radians(teta_ed), radians(teta_eG)

def Calc_Sm_PV(te, I_sol, I_direct, I_diffuse, tilt, Sz, teta, tetaed, tetaeg,
               n, Pg, K, NOCT, a0, a1, a2, a3, a4, L):
    """
    To calculate the absorbed solar radiation on tilted surface.

    Parameters
    ----------
    te
    I_sol
    I_direct
    I_diffuse
    tilt
    Sz
    teta
    tetaed
    tetaeg
    n
    Pg
    K
    NOCT
    a0
    a1
    a2
    a3
    a4
    L

    Returns
    -------

    References
    ----------
    Duffie, J. A. and Beckman, W. A. (2013) Radiation Transmission through Glazing: Absorbed Radiation, in
    Solar Engineering of Thermal Processes, Fourth Edition, John Wiley & Sons, Inc., Hoboken, NJ, USA.
    doi: 10.1002/9781118671603.ch5

    """

    # calcualte ratio of beam radiation on a tilted plane
    # to avoid inconvergence when I_sol = 0
    lim1 = radians(0)
    lim2 = radians(90)
    lim3 = radians(89.999)

    if teta < lim1:
        teta = min(lim3, abs(teta))
    if teta >= lim2:
        teta = lim3

    if Sz < lim1:
        Sz = min(lim3, abs(Sz))
    if Sz >= lim2:
        Sz = lim3
    # Rb: ratio of beam radiation of tilted surface to that on horizontal surface
    Rb = cos(teta) / cos(Sz)  # Sz is Zenith angle

    # calculate the specific air mass, m
    m = 1 / cos(Sz)
    M = a0 + a1 * m + a2 * m ** 2 + a3 * m ** 3 + a4 * m ** 4

    # angle refractive  (aproximation accrding to Soteris A.)
    teta_r = asin(sin(teta) / n)  # in radians
    Ta_n = exp(-K * L) * (1 - ((n - 1) / (n + 1)) ** 2)
    # calculate parameters of anlge modifier #first for the direct radiation
    if teta < 1.5707:  # 90 degrees in radians
        part1 = teta_r + teta
        part2 = teta_r - teta
        Ta_B = exp((-K * L) / cos(teta_r)) * (
        1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
        kteta_B = Ta_B / Ta_n
    else:
        kteta_B = 0

    # angle refractive for diffuse radiation
    teta_r = asin(sin(tetaed) / n)  # in radians
    part1 = teta_r + tetaed
    part2 = teta_r - tetaed
    Ta_D = exp((-K * L) / cos(teta_r)) * (
    1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
    kteta_D = Ta_D / Ta_n

    # angle refractive for global radiatoon
    teta_r = asin(sin(tetaeg) / n)  # in radians
    part1 = teta_r + tetaeg
    part2 = teta_r - tetaeg
    Ta_eG = exp((-K * L) / cos(teta_r)) * (
    1 - 0.5 * ((sin(part2) ** 2) / (sin(part1) ** 2) + (tan(part2) ** 2) / (tan(part1) ** 2)))
    kteta_eG = Ta_eG / Ta_n

    # absorbed solar radiation
    S = M * Ta_n * (kteta_B * I_direct * Rb + kteta_D * I_diffuse * (1 + cos(tilt)) / 2 + kteta_eG * I_sol * Pg * (
    1 - cos(tilt)) / 2)  # in W/m2
    if S <= 0:  # when points are 0 and too much losses
        S = 0
    # temperature of cell
    Tcell = te + S * (NOCT - 20) / (800)   # assuming linear temperature rise vs radiation according to NOCT condition

    return S, Tcell

def Calc_PV_power(S, Tcell, eff_nom, areagroup, Bref,misc_losses):
    """

    Parameters
    ----------
    S: absorbed radiation [W/m2]
    Tcell: cell temperature [degree]
    eff_nom
    areagroup: panel area [m2]
    Bref
    misc_losses: expected system loss

    Returns
    -------
    P: Power production [kWh]

    """
    P = eff_nom*areagroup*S*(1-Bref*(Tcell-25))*(1-misc_losses)/1000 # Osterwald, 1986) in kWatts
    return P


"""
============================
optimal angle and tilt
============================

"""


def Calc_optimal_angle(teta_z, latitude, transmissivity):
    """
    To calculate the optimal tilt angle of the solar panels.

    Parameters
    ----------
    teta_z: surface azimuth, 0 degree south (east negative, west positive) according to the paper of Quinn et al., 2013
    latitude
    transmissivity

    Returns
    -------
    S.W.Quinn, B.Lehman.A simple formula for estimating the optimum tilt angles of photovoltaic panels.
    2013 IEEE 14th Work Control Model Electron, Jun, 2013, pp.1-8
    """
    if transmissivity <= 0.15:
        gKt = 0.977
    elif 0.15 < transmissivity <= 0.7:
        gKt = 1.237 - 1.361 * transmissivity
    else:
        gKt = 0.273
    Tad = 0.98
    Tar = 0.97
    Pg = 0.2  # ground reflectance of 0.2
    l = radians(latitude)
    a = radians(teta_z)
    b = atan((cos(a) * tan(l)) * (1 / (1 + ((Tad * gKt - Tar * Pg) / (2 * (1 - gKt))))))  # eq.(11)
    return abs(b)  # radians


def Calc_optimal_spacing(Sh, Az, tilt_angle, module_length):
    """
    To calculate the optimal spacing between each panel to avoid shading.

    Parameters
    ----------
    Sh: Solar elevation at the worst hour [degree]
    Az: Azimuth [degree]
    tilt_angle: optimal tilt angle for panels on flat surfaces [degree]
    module_length: [m]

    Returns
    -------
    D: optimal distance in [m]
    """
    h = module_length * sin(tilt_angle)
    D1 = h / tan(radians(Sh))
    D = max(D1 * cos(radians(180 - Az)), D1 * cos(radians(Az - 180)))
    return D


def Calc_categoriesroof(teta_z, B, GB, Max_Isol):
    """
    To categorize solar panels by the surface azimuth, tilt angle and yearly radiation.

    Parameters
    ----------
    teta_z: surface azimuth, 0 degree south (east negative, west positive)
    B: solar panel tile angle
    GB: yearly radiation of sensors
    Max_Isol: yearly global horizontal radiation

    Returns
    -------
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

def optimal_angle_and_tilt(sensors_metadata_clean, latitude, worst_sh, worst_Az, transmissivity,
                           module_length, Max_Isol):
    """
    First determine the optimal tilt angle of the solar panels, row spacing, and surface azimuth.
    Secondly, the total PV module area is calculated.
    And then all the modules are categorized with its surface azimuth, tilt angle, and yearly radiation to calculate the
    absorbed radiation.

    Parameters
    ----------
    sensors_metadata_clean
    latitude
    worst_sh
    worst_Az
    transmissivity
    module_length
    Max_Isol

    Returns
    -------
    Assumptions
    -----------
    1) Tilt angle: If the sensor is on tilted roof, the panel will have the same tilt as the roof. If the sensor is on
       a wall, the tilt angle is 90 degree. Tilt angles for flat roof is determined using the method from Quinn et al.
    2) Row spacing: Determine the row spacing by minimizing the shadow according to the solar elevation and azimuth at
       the worst hour of the year. The worst hour is a global variable defined by users.
    3) Surface azimuth (orientation) of panels: If the sensor is on a tilted roof, the orientation of the panel is the
        same as the roof. Sensors on flat roofs are all south facing (orientation = 0).
    """
    # calculate panel tilt angle (B) for flat roofs (tilt < 5 degrees), slope roofs (B = tilt) and walls (B = tilt).
    optimal_angle_flat = Calc_optimal_angle(180, latitude, transmissivity) # assume surface azimuth, teta_z = 180, south facing #FIXME: change to singapore
    sensors_metadata_clean['tilt']= np.vectorize(math.acos)(sensors_metadata_clean['Zdir']) #surface tilt angle in rad
    sensors_metadata_clean['tilt'] = np.vectorize(math.degrees)(sensors_metadata_clean['tilt']) #surface tilt angle in degrees
    sensors_metadata_clean['B'] = np.where(sensors_metadata_clean['tilt'] >= 5, sensors_metadata_clean['tilt'],
                                           degrees(optimal_angle_flat)) # panel tilt angle in degrees

    # calculate spacing and surface azimuth of the panels for flat roofs
    optimal_spacing_flat = Calc_optimal_spacing(worst_sh, worst_Az, optimal_angle_flat, module_length)
    sensors_metadata_clean['array_s'] = np.where(sensors_metadata_clean['tilt'] >= 5, 0, optimal_spacing_flat)
    sensors_metadata_clean['surface_azimuth'] = np.vectorize(calc_surface_azimuth)(sensors_metadata_clean['Xdir'], sensors_metadata_clean['B'])

    # TODO: improve calculation.
    # sensors_metadata_clean['area_netpv'] = (grid_side - sensors_metadata_clean.array_s) / [cos(x) for x in sensors_metadata_clean.B] * grid_side
    # calculate the surface area to install one pv panel on flat roofs with defined tilt angle and array spacing
    #surface_area_flat = module_length*(sensors_metadata_clean.array_s/2 + module_length*[cos(radians(x)) for x in sensors_metadata_clean.B])
    surface_area_flat = module_length * (
    sensors_metadata_clean.array_s / 2 + module_length * [cos(optimal_angle_flat)])

    # calculate the pv module area for each sensor
    sensors_metadata_clean['area_netpv'] = np.where(sensors_metadata_clean['tilt'] >= 5, sensors_metadata_clean.AREA_m2,
                                                    module_length**2 * (sensors_metadata_clean.AREA_m2/surface_area_flat))

    # categorize the sensors by surface_azimuth, B, GB
    result = np.vectorize(Calc_categoriesroof)(sensors_metadata_clean.surface_azimuth, sensors_metadata_clean.B,
                                               sensors_metadata_clean.total_rad, Max_Isol) # orientation = teta_z
    sensors_metadata_clean['CATteta_z'] = result[0]
    sensors_metadata_clean['CATB'] = result[1]
    sensors_metadata_clean['CATGB'] = result[2]
    return sensors_metadata_clean

def calc_surface_azimuth(xdir, B):
    B = math.radians(B)
    surface_azimuth = math.asin(xdir / math.sin(B))
    return surface_azimuth

def calc_groups(sensors_rad_clean, sensors_metadata_cat):
    # calculate number of optimal groups as number of optimal combinations.
    # group the sensors by categories
    groups_ob = sensors_metadata_cat.groupby(['CATB', 'CATGB', 'CATteta_z'])
    prop_observers = groups_ob.mean().reset_index()
    prop_observers = pd.DataFrame(prop_observers)
    total_area_pv = groups_ob['area_netpv'].sum().reset_index()['area_netpv']
    prop_observers['total_area_pv'] = total_area_pv
    number_groups = groups_ob.size().count()
    sensors_list = groups_ob.groups.values()

    # calculate mean hourly radiation among the sensors in each group
    rad_group_mean = np.empty(shape=(number_groups,8760))
    number_points = np.empty(shape=(number_groups,1))
    for x in range(0, number_groups):
        sensors_rad_group = sensors_rad_clean[sensors_list[x]]
        rad_mean = sensors_rad_group.mean(axis=1).as_matrix().T
        rad_group_mean[x] = rad_mean
        number_points[x] = len(sensors_list[x])
    hourlydata_groups = pd.DataFrame(rad_group_mean).T

    return number_groups, hourlydata_groups, number_points, prop_observers

#============================
#properties of module
#============================


def calc_properties_PV(type_PVpanel):
    if type_PVpanel == 1:#     # assuming only monocrystalline panels.
        eff_nom = 0.16 # GTM 2014
        NOCT = 43.5 # Fanney et al.,
        Bref = 0.0035  # Fuentes et al.,Luque and Hegedus, 2003).
        a0 = 0.935823
        a1 = 0.054289
        a2 = -0.008677
        a3 = 0.000527
        a4 = -0.000011
        L = 0.002 # glazing tickness
    if type_PVpanel == 2:#     # polycristalline
        eff_nom = 0.15 # GTM 2014
        NOCT = 43.9 # Fanney et al.,
        Bref = 0.0044
        a0 = 0.918093
        a1 = 0.086257
        a2 = -0.024459
        a3 = 0.002816
        a4 = -0.000126
        L = 0.002 # glazing tickness
    if type_PVpanel == 3:#     # amorphous
        eff_nom = 0.08  # GTM 2014
        NOCT = 38.1 # Fanney et al.,
        Bref = 0.0026
        a0 = 1.10044085
        a1 = -0.06142323
        a2 = -0.00442732
        a3 = 0.000631504
        a4 = -0.000019184
        L = 0.0002 # glazing tickness

    return eff_nom,NOCT,Bref,a0,a1,a2,a3,a4,L

# investment and maintenance costs

def calc_Cinv_pv(P_peak):
    """
    P_peak in kW
    result in CHF
    Lifetime 20 y
    """
    if P_peak < 10:
        InvCa = 3500.07 * P_peak /20
    else:
        InvCa = 2500.07 * P_peak /20

    return InvCa # [CHF/y]


# remuneration scheeme

def calc_Crem_pv(E_nom):
    """
    Calculates KEV (Kostendeckende Einspeise - Verguetung) for solar PV and PVT.
    Therefore, input the nominal capacity of EACH installation and get the according KEV as return in Rp/kWh

    :param E_nom: Nominal Capacity of solar panels (PV or PVT) in Wh
    :return:
        KEV_obtained_in_RpPerkWh : float
        KEV remuneration in Rp / kWh
    """

    KEV_regime = [0,
                  0,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  20.4,
                  19.7,
                  19.3,
                  19,
                  18.9,
                  18.7,
                  18.6,
                  18.5,
                  18.1,
                  17.9,
                  17.8,
                  17.8,
                  17.7,
                  17.7,
                  17.7,
                  17.6,
                  17.6]
    P_installed_in_kW = [0,
                         9.99,
                         10,
                         12,
                         15,
                         20,
                         29,
                         30,
                         40,
                         50,
                         60,
                         70,
                         80,
                         90,
                         100,
                         200,
                         300,
                         400,
                         500,
                         750,
                         1000,
                         1500,
                         2000,
                         1000000]
    KEV_interpolated_kW = interpolate.interp1d(P_installed_in_kW, KEV_regime, kind="linear")
    KEV_obtained_in_RpPerkWh = KEV_interpolated_kW(E_nom / 1000.0)
    return KEV_obtained_in_RpPerkWh


def test_photovoltaic():
    import cea.inputlocator
    import cea.globalvar

    locator = cea.inputlocator.InputLocator(r'C:\reference-case-open\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()
    list_buildings_names = dbfreader.dbf2df(locator.get_building_occupancy())['Name']
    #pd.read_csv(locator.get_building_list()).Name.values
    gv = cea.globalvar.GlobalVariables()
    for building in list_buildings_names:
        radiation = locator.get_radiation_building(building_name= building)
        radiation_metadata = locator.get_radiation_metadata(building_name= building)
        calc_PV(locator=locator, radiation_csv= radiation, metadata_csv= radiation_metadata, latitude=46.95240555555556,
                longitude=7.439583333333333, gv=gv, weather_path=weather_path, building_name = building)

#         calc_pv_main(locator=locator, radiation = radiation, latitude=46.95240555555556, longitude=7.439583333333333, year=2014, gv=gv,
#                  weather_path=weather_path) #FIXME: check naming convention



if __name__ == '__main__':
    test_photovoltaic()