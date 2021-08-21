"""
This script calculates:
BIA annualized capital expenditure [CAPEX] on equipment(panels) in [USD/year], and
CAPEX on seeds in [USD/year];

BIA annual operational expenditure [OPEX] on water in [USD/year],
OPEX on electricity use in water irrigation system in [USD/year], and
OPEX on equipment maintenance in [USD/year].
"""

import os
import time
from itertools import repeat
from math import *
from multiprocessing import Pool

import pandas as pd

import cea.config
import cea.inputlocator
import cea.utilities.parallel
from cea.constants import HOURS_IN_YEAR
from cea.utilities import agriculture_equations
from cea.resources.radiation_daysim import daysim_main, geometry_generator


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2021, Future Cities Laboratory, Singapore - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "shi@arch.ethz.ch"
__status__ = "Production"


def calc_DLI(locator, config, building_name):
    """
    This function first determines the surface area with sufficient solar radiation, and then calculates the optimal
    tilt angles of panels at each surface location. The panels are categorized into groups by their surface azimuths,
    tilt angles, and global irradiation. In the last, electricity generation from PV panels of each group is calculated.

    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator
    :param radiation_path: solar insulation data on all surfaces of each building (path
    :type radiation_path: String
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
    :return: Building_PV.csv with PV generation potential of each building, Building_sensors.csv with sensor data of
        each PV panel.

    """

    t0 = time.perf_counter()
    radiation_path = locator.get_radiation_building_sensors(building_name)
    metadata_csv_path = locator.get_radiation_metadata(building_name)
    #print('reading solar radiation simulation results done')

    # select sensor point with sufficient solar radiation
    max_annual_radiation, annual_radiation_threshold, sensors_rad_clean, sensors_metadata_clean = \
        agriculture_equations.filter_low_potential(radiation_path, metadata_csv_path, config)
    #print('filtering low potential sensor points done')


    if not sensors_metadata_clean.empty:
        # convert solar radiation to DLI
        sensors_DLI_daily = calc_Whperm2_molperm2(sensors_rad_clean).T
        #print('calculating (daily) DLI for each sensor')

        # label the sensors by their #floor and wall type (lower, upper, and sideX2)
        sensors_wall_type = calc_sensor_wall_type(locator, sensors_metadata_clean, building_name)
        sensors_metadata_clean['wall_type'] = sensors_wall_type

        # merge the calculated results
        sensors_metadata_clean_DLI_daily = pd.merge(sensors_metadata_clean, sensors_DLI_daily, left_index=True,
                                                    right_index=True, how="left")

        # write the daily DLI results
        sensors_metadata_clean_DLI_daily.to_csv(locator.BIA_daily_DLI(building=building_name), index=True,
                                    float_format='%.2f',
                                    na_rep=0)  # print sensors metadata and daily DLI

        print('Calculations of DLI for each sensor on Building', building_name, 'done - time elapsed: %.2f seconds' % (time.perf_counter() - t0))

    else:  # This loop is activated when a building has not sufficient solar potential
        print("Unfortunately, Building", building_name, "has no BIA potential.")
        pass

def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running Day Light Integral with scenario = %s' % config.scenario)
    print('Running Day Light Integral with annual-radiation-threshold-kWh/m2 = %s' % config.agriculture.annual_radiation_threshold_BIA)
    print('Running Day Light Integral with crop-on-roof = %s' % config.agriculture.crop_on_roof)
    print('Running Day Light Integral with crop-on-wall = %s' % config.agriculture.crop_on_wall)

    building_names = locator.get_zone_building_names()
    num_process = config.get_number_of_processes()
    n = len(building_names)
    cea.utilities.parallel.vectorize(calc_DLI, num_process)(repeat(locator, n), repeat(config, n), building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())
