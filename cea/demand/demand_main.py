"""
===========================
Analytical energy demand model algorithm
===========================

"""
from __future__ import division

import multiprocessing as mp
import pandas as pd
import time

import cea.globalvar
import cea.inputlocator
from cea.demand import occupancy_model
from cea.demand import thermal_loads
from cea.demand.thermal_loads import BuildingProperties
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

"""
=========================================
demand calculation
=========================================
"""


def demand_calculation(locator, weather_path, gv):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of Fonseca et al. 2015. Applied energy.
    (http://dx.doi.org/10.1016/j.apenergy.2014.12.068)

    PARAMETERS
    ----------
    :param locator: An InputLocator to locate input files
    :type locator: inputlocator.InputLocator

    :param weather_path: A path to the EnergyPlus weather data file (.epw)
    :type weather_path: str

    :param gv: A GlobalVariable (context) instance
    :type gv: globalvar.GlobalVariable


    RETURNS
    -------

    :returns: None
    :rtype: NoneType


    INPUT / OUTPUT FILES
    --------------------

    - get_radiation: c:\reference-case\baseline\outputs\data\solar-radiation\radiation.csv
    - get_surface_properties: c:\reference-case\baseline\outputs\data\solar-radiation\properties_surfaces.csv
    - get_building_geometry: c:\reference-case\baseline\inputs\building-geometry\zone.shp
    - get_building_hvac: c:\reference-case\baseline\inputs\building-properties\technical_systems.shp
    - get_building_thermal: c:\reference-case\baseline\inputs\building-properties\thermal_properties.shp
    - get_building_occupancy: c:\reference-case\baseline\inputs\building-properties\occupancy.shp
    - get_building_architecture: c:\reference-case\baseline\inputs\building-properties\architecture.shp
    - get_building_age: c:\reference-case\baseline\inputs\building-properties\age.shp
    - get_building_comfort: c:\reference-case\baseline\inputs\building-properties\indoor_comfort.shp
    - get_building_internal: c:\reference-case\baseline\inputs\building-properties\internal_loads.shp


    SIDE EFFECTS
    ------------

    Produces a demand file per building and a total demand file for the whole zone of interest.

    B153767T.csv: csv file for every building with hourly demand data
    Total_demand.csv: csv file of yearly demand data per buidling.
    """
    t0 = time.clock()

    date = pd.date_range(gv.date_start, periods=8760, freq='H')

    # weather model
    weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms']]

    # building properties model
    building_properties = BuildingProperties(locator, gv)

    # schedules model
    list_uses = list(building_properties._prop_occupancy.drop('PFloor', axis=1).columns)
    schedules = occupancy_model.schedule_maker(date, locator, list_uses)
    schedules_dict = {'list_uses': list_uses, 'schedules': schedules}

    # demand model
    num_buildings = len(building_properties)
    if gv.multiprocessing and mp.cpu_count() > 1:
        thermal_loads_all_buildings_multiprocessing(building_properties, date, gv, locator, num_buildings,
                                                    schedules_dict,
                                                    weather_data)
    else:
        thermal_loads_all_buildings(building_properties, date, gv, locator, num_buildings, schedules_dict,
                                    weather_data)
    write_totals_csv(building_properties, locator, gv)
    gv.log('done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)


def write_totals_csv(building_properties, locator, gv):
    """read in the temporary results files and append them to the Totals.csv file."""
    counter = 0
    for name in building_properties.list_building_names():
        temporary_file = locator.get_temporary_file('%(name)sT.csv' % locals())
        if counter == 0:
            df = pd.read_csv(temporary_file)
            counter += 1
        else:
            df2 = pd.read_csv(temporary_file)
            df = df.append(df2, ignore_index=True)
    df.to_csv(locator.get_total_demand(), columns=gv.demand_totals_csv_columns, index=False, float_format='%.3f')


"""
=========================================
multiple or single core calculation
=========================================
"""


def thermal_loads_all_buildings(building_properties, date, gv, locator, num_buildings, usage_schedules,
                                weather_data):
    for i, building in enumerate(building_properties.list_building_names()):
        bpr = building_properties[building]
        thermal_loads.calc_thermal_loads(
            building, bpr, weather_data, usage_schedules, date, gv, locator)
        gv.log('Building No. %(bno)i completed out of %(num_buildings)i: %(building)s', bno=i + 1,
               num_buildings=num_buildings, building=building)


def thermal_loads_all_buildings_multiprocessing(building_properties, date, gv, locator, num_buildings, usage_schedules,
                                                weather_data):
    pool = mp.Pool()
    gv.log("Using %i CPU's" % mp.cpu_count())
    joblist = []
    for building in building_properties.list_building_names():
        bpr = building_properties[building]
        job = pool.apply_async(thermal_loads.calc_thermal_loads,
                               [building, bpr, weather_data, usage_schedules, date, gv, locator])
        joblist.append(job)
    for i, job in enumerate(joblist):
        job.get(240)
        gv.log('Building No. %(bno)i completed out of %(num_buildings)i', bno=i + 1, num_buildings=num_buildings)


"""
=========================================
test
=========================================
"""


def run_as_script(scenario_path=None, weather_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    if weather_path is None:
        weather_path = locator.get_default_weather()

    gv.log('Running demand calculation for scenario %(scenario)s', scenario=scenario_path)
    gv.log('Running demand calculation with weather file %(weather)s', weather=weather_path)
    demand_calculation(locator=locator, weather_path=weather_path, gv=gv)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('-w', '--weather', help='Path to the weather file')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario, weather_path=args.weather)
