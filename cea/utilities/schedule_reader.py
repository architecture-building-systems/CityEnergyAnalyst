from __future__ import division
from __future__ import print_function

import csv

import pandas as pd

import cea
import cea.config
import cea.inputlocator

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

COLUMNS_SCHEDULES = ['DAY',
                     'HOUR',
                     'OCCUPANCY',
                     'APPLIANCES'
                     'LIGHTING',
                     'WATER',
                     'HEATING',
                     'COOLING',
                     'PROCESSES',
                     'SERVERS']

DAY = ['WEEKDAY'] * 24 + ['SATURDAY'] * 24 + ['SUNDAY'] * 24
HOUR = range(1, 25) + range(1, 25) + range(1, 25)


def read_cea_schedule(path_to_cea_schedule):
    """
    reader for the files ``locator.get_building_weekly_schedules``

    :param str path_to_cea_schedule: path to the cea schedule file to read.
                                     (E.g. inputs/building-properties/schedules/B001.csv)
    :return: schedule data, schedule complementary data
    """

    with open(path_to_cea_schedule) as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                metadata = row[1]
            elif i == 1:
                monthly_multiplier = [round(float(x), 2) for x in row[1:]]
            else:
                # skip all the other rows
                break

    schedule_data = pd.read_csv(path_to_cea_schedule, skiprows=2).T
    schedule_data = dict(zip(schedule_data.index, schedule_data.values))
    schedule_complementary_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}

    return schedule_data, schedule_complementary_data


def save_cea_schedule(schedule_data, schedule_complementary_data, path_to_building_schedule):

    METADATA = ['METADATA']+[schedule_complementary_data['METADATA']]
    MULTIPLIER = ['MONTHLY_MULTIPLIER'] + list(schedule_complementary_data['MONTHLY_MULTIPLIER'])
    COLUMNS_SCHEDULES = schedule_data.keys()
    RECORDS_SCHEDULES = map(list, zip(*schedule_data.values()))
    with open(path_to_building_schedule, "wb") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        csvwriter.writerow(METADATA)
        csvwriter.writerow(MULTIPLIER)
        csvwriter.writerow(COLUMNS_SCHEDULES)
        for row in RECORDS_SCHEDULES:
            csvwriter.writerow(row)


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    path_to_building_schedule = locator.get_database_standard_schedules_use('MULTI_RES')
    read_cea_schedule(path_to_building_schedule)


if __name__ == '__main__':
    main(cea.config.Configuration())
