"""
===========================
Analytical energy demand model algorithm
===========================
File history and credits:
J. Fonseca  script development          24.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox
J. Fonseca  refactoring to new properties file   22.03.16
"""
from __future__ import division
import pandas as pd
import numpy as np
import functions as f
import globalvar
import arcpy
import tempfile
import os
from geopandas import GeoDataFrame as gpdf

gv = globalvar.GlobalVariables()
reload(f)
reload(globalvar)


def demand_calculation(path_radiation, path_schedules, path_temporary_folder, path_weather, path_results,
                       path_hvac_shp, path_thermal_shp, path_occupancy_shp,
                       path_geometry_shp, path_age_shp, path_architecture_shp, gv):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of Fonseca et al. 2015. Appl. energy.

    Parameters
    ----------
    path_radiation:
        path to solar radiation file in vertical surfaces
        RadiationYearFinal.csv
    path_schedules: string
        path to folder containing occupancy profile schedules
    path_weather : string
        path to weather data file weather_design_hour.csv
    path_results : string
        path to demand results folder demand
    path_properties: string
        path to folder with .shp files created with the properties script there should be a total of 6

    Returns
    -------
    single_demand: .csv
        csv file for every building with hourly demand data
    total_demand: .csv
        csv file of yearly demand data per buidling.
    """

    # local variables
    weather_data = pd.read_csv(path_weather, usecols=['te', 'RH'])
    list_uses = gv.list_uses
    radiation_file = pd.read_csv(path_radiation)
    prop_geometry = gpdf.from_file(path_geometry_shp)
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['perimeter'] = prop_geometry.length
    prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
    prop_HVAC = gpdf.from_file(path_hvac_shp).drop('geometry', axis=1).set_index('Name')
    prop_thermal = gpdf.from_file(path_thermal_shp).drop('geometry', axis=1).set_index('Name')
    prop_occupancy = gpdf.from_file(path_occupancy_shp).drop('geometry', axis=1).set_index('Name')
    prop_architecture = gpdf.from_file(path_architecture_shp).drop('geometry', axis=1).set_index('Name')
    prop_age = gpdf.from_file(path_age_shp).drop('geometry', axis=1).set_index('Name')

    # weather conditions
    T_ext = np.array(weather_data.te)
    RH_ext = np.array(weather_data.RH)
    T_ext_max = T_ext.max()
    T_ext_min = T_ext.min()

    # obtain schedules per building
    rows = len(list_uses)
    profiles = list(range(rows))
    for row in range(rows):
        profiles[row] = pd.read_csv(os.path.join(path_schedules, 'Occupancy_%s.csv' % list_uses[row]), nrows=8760)

    # calculate file with thermal properties for RC model
    prop_RC_model = f.get_prop_RC_model(prop_occupancy, prop_architecture, prop_thermal, prop_geometry, prop_HVAC,
                                        radiation_file, gv)

    # calculate clean file of radiation - @ daren: this is a A BOTTLE NECK
    Solar = f.CalcIncidentRadiation(prop_RC_model, radiation_file)

    # compute demand
    num_buildings = len(prop_RC_model.index)
    counter = 0
    for building in prop_RC_model.index:
        f.CalcThermalLoads(building, prop_occupancy.ix[building], prop_architecture.ix[building],
                           prop_thermal.ix[building],
                           prop_geometry.ix[building], prop_HVAC.ix[building], prop_RC_model.ix[building],
                           prop_age.ix[building], Solar.ix[building], path_results, profiles, list_uses, T_ext,
                           T_ext_max, RH_ext, T_ext_min, path_temporary_folder, gv, 0, 0)
        message = 'Building No. ' + str(counter + 1) + ' completed out of ' + str(num_buildings)
        arcpy.AddMessage(message)
        counter += 1
    # put together all rows of the total file
    counter = 0
    for name in prop_RC_model.index:
        if counter == 0:
            df = pd.read_csv(path_temporary_folder + '\\' + name + 'T' + '.csv')
            counter += 1
        else:
            df2 = pd.read_csv(path_temporary_folder + '\\' + name + 'T' + '.csv')
            df = df.append(df2, ignore_index=True)
    df.to_csv(os.path.join(path_results, 'Total_demand.csv'), index=False, float_format='%.2f')

    print 'finished'


def test_demand():
    path_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test'))
    path_reference_case = os.path.join(path_test, 'reference-case')

    # path_radiation = os.path.join(path_reference_case, 'Radiation2000-2009.csv')
    path_radiation = os.path.join(path_reference_case, 'RadiationYearFinal.csv')
    path_schedules = os.path.join(os.path.dirname(__file__), 'db', 'Schedules')
    path_weather = os.path.join(path_reference_case, 'weather_design_hour.csv')
    path_results = os.path.join(path_reference_case, 'expected-output', 'demand')
    path_HVAC_shp = os.path.join(path_reference_case, 'expected-output', 'properties', 'building_HVAC.shp')
    path_thermal_shp = os.path.join(path_reference_case, 'expected-output', 'properties', 'building_thermal.shp')
    path_occupancy_shp = os.path.join(path_reference_case, 'feature-classes', 'building_occupancy.shp')
    path_geometry_shp = os.path.join(path_reference_case, 'feature-classes', 'building_geometry.shp')
    path_age_shp = os.path.join(path_reference_case, 'feature-classes', 'building_age.shp')
    path_architecture_shp = os.path.join(path_reference_case, 'expected-output', 'properties',
                                         'building_architecture.shp')
    path_temporary_folder = tempfile.gettempdir()
    demand_calculation(path_radiation=path_radiation, path_schedules=path_schedules,
                       path_temporary_folder=path_temporary_folder, path_weather=path_weather,
                       path_results=path_results, path_HVAC_shp=path_HVAC_shp, path_thermal_shp=path_thermal_shp,
                       path_occupancy_shp=path_occupancy_shp, path_geometry_shp=path_geometry_shp,
                       path_age_shp=path_age_shp, path_architecture_shp=path_architecture_shp, gv=gv)


if __name__ == '__main__':
    test_demand()
