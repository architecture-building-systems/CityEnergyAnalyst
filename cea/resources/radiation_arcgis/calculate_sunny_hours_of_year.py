import os
import pandas as pd
import numpy as np
import pickle
from simpledbf import Dbf5

import cea.inputlocator

def calculate_sunny_hours_of_year(locator, sunrise):
    # run the transformation of files appending all and adding non-sunshine hours
    temporary_folder = locator.get_temporary_folder()
    result_file_path = os.path.join(temporary_folder, 'sunny_hours_of_year.pickle')

    sunny_hours_per_day = []
    for day in range(1, 366):
        result = calculate_sunny_hours_of_day(day, sunrise, temporary_folder)
        result = result.apply(pd.to_numeric, downcast='integer')
        sunny_hours_per_day.append(result)
    sunny_hours_of_year = sunny_hours_per_day[0]
    for df in sunny_hours_per_day[1:]:
        for column in df.columns:
            if column.startswith('T'):
                sunny_hours_of_year[column] = df[column].copy()
                # sunny_hours_of_year = sunny_hours_of_year.merge(df, on='ID', how='outer')
    sunny_hours_of_year = sunny_hours_of_year.fillna(value=0)
    return sunny_hours_of_year


def calculate_sunny_hours_of_day(day, sunrise, temporary_folder):
    """
    :param day:
    :type day: int
    :param sunrise: what is this? seems to be a list of sunrise times, but for the ecocampus case, I get a list of
                    ints like 22 and 23... that can't be right, right?
    :type sunrise: list[int]
    :param temporary_folder: path to temporary folder with the radiations per day
    :return:
    """
    radiation_sunnyhours = np.round(Dbf5(os.path.join(temporary_folder, 'Day_%(day)i.dbf' % locals())).to_dataframe(),
                                    2)

    # Obtain the number of points modeled to do the iterations
    radiation_sunnyhours['ID'] = 0
    radiation_sunnyhours['ID'] = range(1, radiation_sunnyhours.ID.count() + 1)

    # Table with empty values with the same range as the points.
    Table = pd.DataFrame.copy(radiation_sunnyhours)
    listtimes = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15', 'T16',
                 'T17', 'T18', 'T19', 'T20', 'T21', 'T22', 'T23', 'T24']
    for x in listtimes:
        Table[x] = 0
    Table.drop('T0', axis=1, inplace=True)

    # Counter of Columns in the Initial Table
    Counter = radiation_sunnyhours.count(1)[0]
    values = Counter - 1
    # Calculation of Sunrise time
    Sunrise_time = sunrise[day - 1]
    # Calculation of table
    for x in range(values):
        Hour = int(Sunrise_time) + int(x)
        Table['T' + str(Hour)] = radiation_sunnyhours['T' + str(x)]

    # rename the table for every T to get in 1 to 8760 hours.
    if day <= 1:
        name = 1
    else:
        name = int(day - 1) * 24 + 1

    Table.rename(
        columns={'T1': 'T' + str(name), 'T2': 'T' + str(name + 1), 'T3': 'T' + str(name + 2), 'T4': 'T' + str(name + 3),
                 'T5': 'T' + str(name + 4),
                 'T6': 'T' + str(name + 5), 'T7': 'T' + str(name + 6), 'T8': 'T' + str(name + 7),
                 'T9': 'T' + str(name + 8), 'T10': 'T' + str(name + 9),
                 'T11': 'T' + str(name + 10), 'T12': 'T' + str(name + 11), 'T13': 'T' + str(name + 12),
                 'T14': 'T' + str(name + 13), 'T15': 'T' + str(name + 14),
                 'T16': 'T' + str(name + 15), 'T17': 'T' + str(name + 16), 'T18': 'T' + str(name + 17),
                 'T19': 'T' + str(name + 18), 'T20': 'T' + str(name + 19),
                 'T21': 'T' + str(name + 20), 'T22': 'T' + str(name + 21), 'T23': 'T' + str(name + 22),
                 'T24': 'T' + str(name + 23), 'ID': 'ID'}, inplace=True)

    return Table

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', help='path to the scenario')
    parser.add_argument('--sunrise-pickle', help='path to pickle of the sunrise array')
    parser.add_argument('--sunny-hours-pickle', help='path to pickle of the result (STORE result here)')
    args = parser.parse_args()

    locator = cea.inputlocator.InputLocator(scenario_path=args.scenario)
    sunrise = pickle.load(open(args.sunrise_pickle, 'r'))

    sunny_hours_of_year = calculate_sunny_hours_of_year(locator=locator, sunrise=sunrise)
    sunny_hours_of_year.to_pickle(args.sunny_hours_pickle)
