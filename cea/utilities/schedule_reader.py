import collections
import csv
import glob
import os

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

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def read_cea_schedule(locator, use_type=None, building=None):
    """
    reader for the files ``locator.get_building_weekly_schedules``

    :param str path_to_cea_schedule: path to the cea schedule file to read.
                                     (E.g. inputs/building-properties/schedules/B001.csv)
    :return: schedule data, schedule complementary data
    """

    metadata = 'meta-data'
    # Get the twelve numbers of monthly multiplier as a list
    if use_type:
        path_to_monthly_multiplier = locator.get_database_archetypes_schedules_monthly_multiplier()
        path_to_schedule = locator.get_database_archetypes_schedules(use_type)
        df_monthly_multiplier = pd.read_csv(path_to_monthly_multiplier)
        df_monthly_multiplier_row = df_monthly_multiplier[df_monthly_multiplier['use_type'] == use_type]
        monthly_multiplier = df_monthly_multiplier_row[months].values.flatten().tolist()
        schedule_complementary_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}

    elif building:
        path_to_monthly_multiplier = locator.get_building_weekly_schedules_monthly_multiplier_csv()
        path_to_schedule = locator.get_building_weekly_schedules(building)
        df_monthly_multiplier = pd.read_csv(path_to_monthly_multiplier)
        df_monthly_multiplier_row = df_monthly_multiplier[df_monthly_multiplier['name'] == building]
        monthly_multiplier = df_monthly_multiplier_row[months].values.flatten().tolist()
        schedule_complementary_data = {'METADATA': metadata, 'MONTHLY_MULTIPLIER': monthly_multiplier}

    else:
        raise ValueError('Either use_type or building has to be not None.')

    # Get the schedule data as a dictionary
    schedule_data = pd.read_csv(path_to_schedule).T
    schedule_data = dict(zip(schedule_data.index, schedule_data.values))

    return schedule_data, schedule_complementary_data


def save_cea_schedules(schedule_data, path_to_building_schedule):
    # schedules
    df_schedules = pd.DataFrame.from_dict(schedule_data)
    if 'hour' in df_schedules.columns:
        columns = ['hour'] + [col for col in df_schedules.columns if col != 'hour']
        df_schedules = df_schedules[columns]
    df_schedules.to_csv(path_to_building_schedule, index=False, float_format='%.2f')


def save_cea_monthly_multipliers(lists_monthly_multiplier, path_to_monthly_multiplier):

    # monthly multiplier
    header = ['name'] + months
    df_monthly_multiplier = pd.DataFrame(data=lists_monthly_multiplier, columns=header)
    df_monthly_multiplier.to_csv(path_to_monthly_multiplier, index=False, float_format='%.2f')



def get_all_schedule_names(schedules_folder):
    """Get all schedule names from path"""
    schedule_files = glob.glob(os.path.join(schedules_folder, "*.csv"))
    return [os.path.splitext(os.path.basename(schedule_file))[0] for schedule_file in schedule_files]


# TODO: Replace usages of `read_cea_schedule` to this function
def schedule_to_dataframe(schedule_path):
    out = collections.OrderedDict()

    with open(schedule_path) as f:
        reader = csv.reader(f)
        out['METADATA'] = pd.DataFrame({'metadata': [next(reader)[1]]})
        out['MONTHLY_MULTIPLIER'] = pd.DataFrame({m + 1: [round(float(v), 2)] for m, v in enumerate(next(reader)[1:])},
                                                 columns=[m for m in range(1, 13)])
        # Filter empty columns
        columns = [col for col in next(reader) if col != '']

    schedule_data = pd.read_csv(schedule_path, skiprows=2, usecols=columns).set_index(
        ['DAY', 'HOUR']).unstack().reindex(['WEEKDAY', 'SATURDAY', 'SUNDAY'])
    for t, df in schedule_data.groupby(axis=1, level=0, sort=False):
        df.columns = [i for i in range(1, 25)]
        out[t] = df.reset_index()

    return out


def schedule_to_file(schedule, schedule_path):
    schedule_df = pd.DataFrame()
    metadata = ['METADATA']
    multiplier = ['MONTHLY_MULTIPLIER']
    for key, data in schedule.items():
        if key == 'METADATA':
            metadata += [schedule['METADATA']['metadata'].iloc[0]]
        elif key == 'MONTHLY_MULTIPLIER':
            multiplier += [i for i in schedule['MONTHLY_MULTIPLIER'].iloc[0].values]
        else:
            schedule_column_data = data.set_index(['DAY']).reindex(['WEEKDAY', 'SATURDAY', 'SUNDAY']).stack()
            schedule_column_data.index.names = ['DAY', 'HOUR']
            schedule_df[key] = schedule_column_data
    schedule_df = schedule_df.reset_index()

    with open(schedule_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(metadata)
        csv_writer.writerow(multiplier)
        csv_writer.writerow(schedule_df.columns)
        for row in schedule_df.values:
            csv_writer.writerow(row)
    print('Schedule file written to {}'.format(schedule_path))


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    path_to_building_schedule = locator.get_database_standard_schedules_use('MULTI_RES')
    # print(read_cea_schedule(path_to_building_schedule))
    print(schedule_to_dataframe(path_to_building_schedule))


if __name__ == '__main__':
    main(cea.config.Configuration())
