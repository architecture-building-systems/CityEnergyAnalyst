"""
===========================
Analytical energy demand model algorithm
===========================
File history and credits:
J. Fonseca  script development          24.08.15
D. Thomas   formatting, refactoring, debugging and cleaning
D. Thomas   integration in toolbox
J. Fonseca  refactoring to new properties file   22.03.16
"""
from __future__ import division
import pandas as pd
import numpy as np
import functions as f
import globalvar
from geopandas import GeoDataFrame as gpdf
import inputlocator

gv = globalvar.GlobalVariables()
reload(f)
reload(globalvar)


def demand_calculation(locator, gv):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of Fonseca et al. 2015. Applied energy.

    Parameters
    ----------
    :param locator: An InputLocator to locate input files
    :type locator: inputlocator.InputLocator

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
    weather_data = pd.read_csv(locator.get_weather_hourly(), usecols=['te', 'RH'])
    list_uses = gv.list_uses
    radiation_file = pd.read_csv(locator.get_radiation())
    prop_geometry = gpdf.from_file(locator.get_building_geometry())
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['perimeter'] = prop_geometry.length
    prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
    prop_HVAC = gpdf.from_file(locator.get_building_hvac()).drop('geometry', axis=1)
    prop_thermal = gpdf.from_file(locator.get_building_thermal()).drop('geometry', axis=1).set_index('Name')
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1).set_index('Name')
    prop_architecture = gpdf.from_file(locator.get_building_architecture()).drop('geometry', axis=1).set_index('Name')
    prop_age = gpdf.from_file(locator.get_building_age()).drop('geometry', axis=1).set_index('Name')

    # get temperatures of operation
    prop_HVAC_result= get_temperatures(locator, prop_HVAC).set_index('Name')
    # weather conditions
    T_ext = np.array(weather_data.te)
    RH_ext = np.array(weather_data.RH)
    T_ext_max = T_ext.max()
    T_ext_min = T_ext.min()

    # get schedules
    schedules = get_schedules(locator, list_uses)

    # get thermal properties for RC model
    prop_RC_model = f.get_prop_RC_model(prop_occupancy, prop_architecture, prop_thermal, prop_geometry, prop_HVAC_result,
                                        radiation_file, gv)

    # get solar insolation @ daren: this is a A BOTTLE NECK
    Solar = f.CalcIncidentRadiation(radiation_file)

    # get timeseries of demand
    num_buildings = len(prop_RC_model.index)
    counter = 0
    for building in prop_RC_model.index:
        f.CalcThermalLoads(building, prop_occupancy.ix[building], prop_architecture.ix[building],
                           prop_thermal.ix[building],
                           prop_geometry.ix[building], prop_HVAC_result.ix[building], prop_RC_model.ix[building],
                           prop_age.ix[building], Solar.ix[building], locator.get_demand_results_folder(), schedules,
                           list_uses, T_ext, T_ext_max, RH_ext, T_ext_min, locator.get_temporary_folder(), gv, 0, 0)
        print 'Building No. ' + str(counter + 1) + ' completed out of ' + str(num_buildings)
        counter += 1

    # get total file


    counter = 0
    for name in prop_RC_model.index:
        temporary_file = locator.get_temporary_file('%(name)sT.csv' % locals())
        # TODO: check this logic
        if counter == 0:
            df = pd.read_csv(temporary_file)
            counter += 1
        else:
            df2 = pd.read_csv(temporary_file)
            df = df.append(df2, ignore_index=True)
    df.to_csv(locator.get_total_demand(), index=False, float_format='%.2f')

    print 'finished'


def get_schedules(locator, list_uses):
    rows = len(list_uses)
    result = list(range(rows))
    for row in range(rows):
        result[row] = pd.read_csv(locator.get_schedule(list_uses[row]), nrows=8760)
    return result

def get_temperatures(locator, prop_HVAC):
    prop_emission_heating = pd.read_excel(locator.get_technical_emission_systems(), 'heating')
    prop_emission_cooling = pd.read_excel(locator.get_technical_emission_systems(), 'cooling')
    prop_emission_dhw = pd.read_excel(locator.get_technical_emission_systems(), 'dhw')

    df = prop_HVAC.merge(prop_emission_heating, left_on='type_hs', right_on='code')
    df2 = prop_HVAC.merge(prop_emission_cooling, left_on='type_cs', right_on='code')
    df3 = prop_HVAC.merge(prop_emission_dhw, left_on='type_dhw', right_on='code')

    fields = ['Name', 'type_hs', 'type_cs', 'type_dhw',  'type_ctrl', 'Tshs0_C', 'dThs0_C', 'Qhsmax_Wm2']
    fields2 = ['Name', 'Tscs0_C', 'dTcs0_C', 'Qcsmax_Wm2']
    fields3 = ['Name', 'Tsww0_C', 'dTww0_C', 'Qwwmax_Wm2']

    result = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3], on='Name')
    return result

def test_demand():
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    demand_calculation(locator=locator, gv=gv)


if __name__ == '__main__':
    test_demand()
