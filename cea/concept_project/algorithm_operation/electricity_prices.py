
import pandas as pd
import numpy as np
import datetime
import os

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main_electricity_prices(scenario_data_path, scenario, year, date_and_time_prediction, prediction_horizon, time_start,
                            time_end):
    # Get monthly data
    common_path = os.path.join(
        scenario_data_path, scenario, 'concept', 'USEP_from_01-Jan-' + str(year) + '_to_31-Dec-' + str(year), ''
    )
    year_list = []
    for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
        this_month_df = pd.read_csv(common_path + 'USEP_' + month + '-' + str(year) + '.csv')
        year_list.append(this_month_df)

    # Put the 12 months data in the same file
    electricity_prices_year_period_df = pd.concat(year_list, ignore_index=True)
    electricity_prices_year_period_df.to_csv(os.path.join(
        scenario_data_path, scenario, 'concept', 'USEP_from_01-Jan-' + str(year) + '_to_31-Dec-' + str(year),
        'prices_all.csv'
    ))

    # Adding the datetime column
    electricity_prices_year_df = pd.DataFrame(
        np.zeros((electricity_prices_year_period_df.shape[0], 2)), electricity_prices_year_period_df.index, [
            'our_datetime', 'PRICE ($/MWh)'])
    for index, row in electricity_prices_year_period_df.iterrows():
        electricity_prices_year_df.loc[index, 'our_datetime'] = \
            datetime.datetime.strptime(row['DATE'], '%d %b %Y') + datetime.timedelta(
            hours=(row['PERIOD'] - 1) // 2, minutes=30 * ((row['PERIOD'] - 1) % 2))
        electricity_prices_year_df.loc[index, 'PRICE ($/MWh)'] = row['PRICE ($/MWh)']

    electricity_prices_year_df.set_index('our_datetime', inplace=True)
    electricity_prices_year_df.to_csv(os.path.join(
        scenario_data_path, scenario, 'concept', 'USEP_from_01-Jan-' + str(year) + '_to_31-Dec-' + str(year),
        '/prices_all.csv'
    ))

    # Take only the dates and times that correspond to the prediction horizon
    electricity_prices_year_df = electricity_prices_year_df[time_start:time_end]

    # Make means if the prediction horizon time step is not equal to 30 min
    if prediction_horizon == electricity_prices_year_df.shape[0]:
        electricity_prices_MWh = electricity_prices_year_df
    elif prediction_horizon == 0.5 * electricity_prices_year_df.shape[0]:
        # TODO: Make this reindexing in a more elegant way
        electricity_prices_MWh = pd.DataFrame(
            np.zeros((prediction_horizon, 1)), date_and_time_prediction, ['PRICE ($/MWh)'])
        for time in date_and_time_prediction:
            electricity_prices_MWh.loc[time]['PRICE ($/MWh)'] = \
                (electricity_prices_year_df.loc[time][
                    'PRICE ($/MWh)'] + electricity_prices_year_df.loc[time + datetime.timedelta(minutes=30)][
                    'PRICE ($/MWh)']) / 2
    else:
        print('Error: the length of the prediction horizon and the length of the electricity price vector do '
              'not match. Please fix the file electricity_prices.py.')
        quit()

    return electricity_prices_MWh
