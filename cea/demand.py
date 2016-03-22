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
reload(globalvar)
import arcpy
import tempfile
import os
from geopandas import GeoDataFrame as gpdf

gv = globalvar.GlobalVariables()
reload(f)

def demand_calculation(path_radiation, path_schedules, path_temporary_folder, path_weather, path_results,
                       path_HVAC_shp, path_supply_shp, path_thermal_shp, path_occupancy_shp,
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
    WeatherData = pd.read_csv(path_weather, usecols=['te', 'RH'])
    list_uses = gv.list_uses
    radiation_file = pd.read_csv(path_radiation)
    prop_HVAC = gpdf.from_file(path_HVAC_shp)
    prop_supply= gpdf.from_file(path_supply_shp)
    prop_thermal = gpdf.from_file(path_thermal_shp)
    prop_occupancy = gpdf.from_file(path_occupancy_shp)
    prop_geometry = gpdf.from_file(path_geometry_shp)
    prop_architecture = gpdf.from_file(path_architecture_shp)
    prop_age = gpdf.from_file(path_age_shp)

    # weather conditions
    T_ext = np.array(WeatherData.te)
    RH_ext = np.array(WeatherData.RH)
    T_ext_max = T_ext.max()
    T_ext_min = T_ext.min()

    # obtain schedules per building
    rows = len(list_uses)
    Profiles = list(range(rows))
    for use in range(rows):
        Profiles[use] = pd.read_csv(path_schedules + '\\' + 'Occupancy_' +list_uses[use] + '.csv', nrows=8760)

    # calculate file with all properties @ daren:
    all_properties = f.get_all_properties(prop_occupancy, prop_architecture, prop_thermal, prop_geometry, prop_age,
                                          prop_supply, prop_HVAC, radiation_file, gv)

    # calculate clean file of radiation - @ daren: this is a A BOTTLE NECK
    Solar = f.CalcIncidentRadiation(all_properties, radiation_file)

    # compute demand
    buildings = all_properties.Name.count() #how many buildings are there to analyze
    list_buildings =  range(3) #buildings
    for building in list_buildings:
        total = f.CalcThermalLoads(building, all_properties.ix[building], Solar.ix[building], path_results, Profiles,
                                    list_uses, T_ext, T_ext_max, RH_ext, T_ext_min, path_temporary_folder,  gv, 0, 0)
        message = 'Building No. ' + str(building+1) + ' completed out of ' + str(buildings)
        arcpy.AddMessage(message)

    # put together all rows of the total file
    counter = 0
    for x in list_buildings:
        name = all_properties.Name[x]
        if counter ==0:
            df = pd.read_csv(path_temporary_folder+'\\'+name+'T'+'.csv')
            counter +=1
        else:
            df2 = pd.read_csv(path_temporary_folder+'\\'+name+'T'+'.csv')
            df = df.append(df2,ignore_index=True)
    df.to_csv(os.path.join(path_results,'Total_demand.csv'), index=False, float_format='%.2f')

    print 'finished'


def test_demand():
    path_radiation = r'C:\reference-case\stautus-quo\intermediate-output\vertical-insolation\Radiation2000-2009.csv'  # noqa
    path_schedules = os.path.join(os.path.dirname(__file__), 'db', 'Schedules')
    path_weather = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\weather_design_hour.csv'  # noqa
    path_results = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\expected-output\demand'  # noqa
    path_HVAC_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\expected-output\properties\building_HVAC.shp'
    path_supply_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\feature-classes\building_supply.shp'
    path_thermal_shp =  r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\expected-output\properties\building_thermal.shp'
    path_occupancy_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\feature-classes\building_occupancy.shp'
    path_geometry_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\feature-classes\building_geometry.shp'
    path_age_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\feature-classes\building_age.shp'
    path_architecture_shp = r'C:\Users\Jimeno\AppData\Roaming\ESRI\Desktop10.3\ArcToolbox\My Toolboxes\test\reference-case\expected-output\properties\building_architecture.shp'
    path_temporary_folder = tempfile.gettempdir()
    demand_calculation(path_radiation, path_schedules, path_temporary_folder, path_weather, path_results,
                       path_HVAC_shp, path_supply_shp, path_thermal_shp, path_occupancy_shp,
                       path_geometry_shp, path_age_shp, path_architecture_shp, gv)

if __name__ == '__main__':
    test_demand()
