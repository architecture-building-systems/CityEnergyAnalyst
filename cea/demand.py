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
import maker as m
import globalvar
from geopandas import GeoDataFrame as gpdf
import inputlocator

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
    print "reading input files"
    weather_data = pd.read_csv(locator.get_weather_hourly(), usecols=['te', 'RH'])
    solar = pd.read_csv(locator.get_radiation())
    surfaces = pd.read_csv(locator.get_surfaces())
    prop_geometry = gpdf.from_file(locator.get_building_geometry())
    prop_geometry['footprint'] = prop_geometry.area
    prop_geometry['perimeter'] = prop_geometry.length
    prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
    prop_HVAC = gpdf.from_file(locator.get_building_hvac()).drop('geometry', axis=1)
    prop_thermal = gpdf.from_file(locator.get_building_thermal()).drop('geometry', axis=1).set_index('Name')
    prop_occupancy_df = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1).set_index('Name')
    prop_occupancy = prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(axis=0)] # trick to erase occupancies that are not being used (it speeds up the code)
    prop_architecture = gpdf.from_file(locator.get_building_architecture()).drop('geometry', axis=1).set_index('Name')
    prop_age = gpdf.from_file(locator.get_building_age()).drop('geometry', axis=1).set_index('Name')
    prop_comfort = gpdf.from_file(locator.get_building_comfort()).drop('geometry', axis=1).set_index('Name')
    prop_internal_loads = gpdf.from_file(locator.get_building_internal()).drop('geometry', axis=1).set_index('Name')
    # get temperatures of operation
    prop_HVAC_result= get_temperatures(locator, prop_HVAC).set_index('Name')
    # weather conditions
    T_ext = np.array(weather_data.te)
    RH_ext = np.array(weather_data.RH)
    #get list of uses
    list_uses = list(prop_occupancy.drop('PFloor', axis=1).columns)
    #get date
    date = pd.date_range(gv.date_start, periods=8760, freq='H')
    print "done"

    print "reading occupancy schedules"
    # get schedules
    schedules = m.schedule_maker(date, locator, list_uses)
    print "done"

    print "calculating thermal properties"
    # get thermal properties for RC model
    prop_RC_model = f.get_prop_RC_model(prop_occupancy, prop_architecture, prop_thermal, prop_geometry,
                                        prop_HVAC_result, surfaces, gv)
    print "done"

    # get timeseries of demand
    num_buildings = len(prop_RC_model.index)
    counter = 0
    for building in prop_RC_model.index[:2]:
        gv.models['calc-thermal-loads'](building, prop_occupancy.ix[building], prop_architecture.ix[building],
                           prop_geometry.ix[building], prop_HVAC_result.ix[building], prop_RC_model.ix[building],
                           prop_comfort.ix[building],prop_internal_loads.ix[building],
                           prop_age.ix[building], solar.ix[building], locator.get_demand_results_folder(),
                           schedules, T_ext, RH_ext, locator.get_temporary_folder(), gv, date, list_uses)
        gv.log('Building No. %(bno)i completed out of %(btot)i', bno=counter + 1, btot=num_buildings)
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

    gv.log('finished')

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
    gv = globalvar.GlobalVariables()
    demand_calculation(locator=locator, gv=gv)


if __name__ == '__main__':
    test_demand()
