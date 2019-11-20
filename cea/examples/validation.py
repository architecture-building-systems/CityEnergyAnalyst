"""
This tool compares measured data (observed) with model outputs (predicted), used in procedures of calibration and validation
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
import pandas as pd
from sklearn.metrics import mean_squared_error
from math import sqrt
from cea.constants import MONTHS_IN_YEAR, MONTHS_IN_YEAR_NAMES

__author__ = "Luis Santos"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def validation(locator, archetypes):  # confirm what goes in parenthesis here
    """
    This tool compares observed (real life measured data) and predicted (output of the model data) values.
    Annual data is compared in terms of MBE and monthly data in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2002).
    A new input folder with measurements has to be created, with a csv each for monthly and annual data provided as input for this tool.
    A new output csv is generated providing for each building (if measured data is available): building ID | ZIP Code | Measured data (observed) | Modelled data (predicted) | Model errors
    """

    # type of validation to run (select only the ones that have a corresponding csv in the inputs folder)
    annual = True
    monthly = False
    load = 'GRID'

    ## annual validation
    if annual:
        print("annual validation")

        # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | Annual energy consumed (kWh)
        annual_measured_data = pd.read_csv(locator.get_annual_measurements())

        # extract model output
        annual_modelled_data = pd.read_csv(locator.get_demand_results_file())

        # mege the datasets
        merged_annual = annual_modelled_data.merge(annual_measured_data, how='inner',
                                                   on='Name', suffixes=('_model','_measured'))  # extract the modelled buildings that have a corresponding Name (Building ID) simulated by CEA
        annual_modelled_demand = merged_annual[load+'_MWhyr'+'_model']
        annual_measured_demand = merged_annual[load+'_Mwhyr'+'_measured']

        # calculate errors
        biased_error_annual_data = ((annual_modelled_demand - annual_measured_demand) / annual_measured_demand) * 100
        print(biased_error_annual_data)

    ## monthly validation
    if monthly:
        print("monthly validation")
        monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
        measured_building_names = monthly_measured_data.Name.values
        for building_name in measured_building_names:  # number of buildings that have real data available

            # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | monthly energy consumed (kWh) (Jan-Dec)
            print(building_name)
            fields_to_extract = ['Name'] + MONTHS_IN_YEAR_NAMES
            monthly_measured_demand = monthly_measured_data[fields_to_extract].set_index('Name')
            monthly_measured_demand = monthly_measured_demand.loc[building_name]
            monthly_measured_demand = pd.DataFrame({'Month':monthly_measured_demand.index.values,
                                                    'measurements':monthly_measured_demand.values})

            # extract model output
            hourly_modelled_data = pd.read_csv(locator.get_demand_results_file(building_name), usecols=['DATE',load+'_kWh'])
            hourly_modelled_data['DATE'] = pd.to_datetime(hourly_modelled_data['DATE'])

            look_up = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL', 5: 'MAY',
                       6: 'JUNE', 7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER',
                       12: 'DECEMBER'}

            # this step is required to have allow the conversion from hourly to monthly data
            monthly_modelled_data = hourly_modelled_data.resample('M', on='DATE').sum()# because data is in kWh
            monthly_modelled_data['Month'] = monthly_modelled_data.index.month
            monthly_modelled_data['Month'] = monthly_modelled_data.apply(lambda x: look_up[x['Month']], axis=1)
            monthly_data = monthly_modelled_data.merge(monthly_measured_demand, on='Month')

            # calculate errors
            #monthly_data.rename({'GRID_kWh': 'GRID_MWh'}, inplace=True)
            be = monthly_data['measurements'] - monthly_data[load+'_kWh']  # bias error
            nmbe = ((be.sum() / 12) / monthly_data['measurements'].mean()) * 100  # normalized mean bias error (%)
            print(nmbe)
            mse = mean_squared_error(monthly_data['measurements'], monthly_data[load+'_kWh'])  # mean squared error
            rmse = sqrt(mse)  # root mean squared error
            cvrmse = rmse * 100 / monthly_data['measurements'].mean()  # coefficient of variation of the root mean squared error (%)
            print(cvrmse)

    pass


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line - this is how the ArcGIS interface interacts with the scripts
    BTW.

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    validation(locator, config.scenario)


if __name__ == '__main__':
    main(cea.config.Configuration())
