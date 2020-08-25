"""
This tool compares measured data (observed) with model outputs (predicted), used in procedures of calibration and validation
"""
from __future__ import division
from __future__ import print_function

import os
from math import sqrt

import pandas as pd
from sklearn.metrics import mean_squared_error as calc_mean_squared_error

import cea.config
import cea.inputlocator
from cea.constants import MONTHS_IN_YEAR_NAMES
import cea.examples.global_variables as global_variables

__author__ = "Luis Santos"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def validation(scenario_list,
               locators_of_scenarios,
               measured_building_names_of_scenarios,
               annual=False,
               monthly=True,
               load='GRID',
               ):
    """
    This tool compares observed (real life measured data) and predicted (output of the model data) values.
    Annual data is compared in terms of MBE and monthly data in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2002).
    A new input folder with measurements has to biased_error created, with a csv each for monthly and annual data provided as input for this tool.
    A new output csv is generated providing for each building (if measured data is available): building ID | ZIP Code | Measured data (observed) | Modelled data (predicted) | Model errors #missing
    """

    # type of validation to run (select only the ones that have a corresponding csv in the inputs folder)
    # ## annual validation
    # if annual:
    #     print("annual validation")
    #
    #     # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | Annual energy consumed (kWh)
    #     annual_measured_data = pd.read_csv(locator.get_annual_measurements())
    #
    #     # extract model output
    #     annual_modelled_data = pd.read_csv(locator.get_total_demand())
    #
    #     # mege the datasets
    #     merged_annual = annual_modelled_data.merge(annual_measured_data, how='inner',
    #                                                on='Name', suffixes=('_model',
    #                                                                     '_measured'))  # extract the modelled buildings that have a corresponding Name (Building ID) simulated by CEA
    #     annual_modelled_demand = merged_annual[load + '_MWhyr' + '_model']
    #     annual_measured_demand = merged_annual[load + '_MWhyr' + '_measured']
    #
    #     # calculate errors
    #     biased_error_annual_data = ((annual_modelled_demand - annual_measured_demand) / annual_measured_demand) * 100
    #     print(biased_error_annual_data)

    ## monthly validation
    if monthly:
        number_of_buildings = 0
        print("monthly validation")
        validation_output = pd.DataFrame(columns=['scenario', 'calibrated_buildings', 'score'])
        for scenario, locator, measured_building_names in zip(scenario_list, locators_of_scenarios,
                                                              measured_building_names_of_scenarios):
            list_of_scores = []
            number_of_calibrated = []
            number_of_buildings = number_of_buildings + len(measured_building_names)
            # get measured data for buiildings in this scenario
            monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())

            # loop in the measured buildings of this scenario
            for building_name in measured_building_names:  # number of buildings that have real data available
                # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | monthly energy consumed (kWh) (Jan-Dec)
                print('For building', building_name, 'the errors are')
                fields_to_extract = ['Name'] + MONTHS_IN_YEAR_NAMES
                monthly_measured_demand = monthly_measured_data[fields_to_extract].set_index('Name')
                monthly_measured_demand = monthly_measured_demand.loc[building_name]
                monthly_measured_demand = pd.DataFrame({'Month': monthly_measured_demand.index.values,
                                                        'measurements': monthly_measured_demand.values})

                # extract model output
                hourly_modelled_data = pd.read_csv(locator.get_demand_results_file(building_name),
                                                   usecols=['DATE', load + '_kWh'])
                hourly_modelled_data['DATE'] = pd.to_datetime(hourly_modelled_data['DATE'])

                look_up = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL', 5: 'MAY',
                           6: 'JUNE', 7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER',
                           12: 'DECEMBER'}

                # this step is required to have allow the conversion from hourly to monthly data
                monthly_modelled_data = hourly_modelled_data.resample('M', on='DATE').sum()  # because data is in kWh
                monthly_modelled_data['Month'] = monthly_modelled_data.index.month
                monthly_modelled_data['Month'] = monthly_modelled_data.apply(lambda x: look_up[x['Month']], axis=1)
                monthly_data = monthly_modelled_data.merge(monthly_measured_demand, on='Month')

                # calculate errors
                cv_root_mean_squared_error, normalized_mean_biased_error = calc_errors_per_building(load, monthly_data)

                ind_calib_building, ind_score_building = calc_building_score(cv_root_mean_squared_error, monthly_data,
                                                                             normalized_mean_biased_error)

                # appending list of variables for later use
                number_of_calibrated.append(ind_calib_building)
                list_of_scores.append(ind_score_building)
            n_scenario_calib = sum(number_of_calibrated)
            scenario_score = sum(list_of_scores)
            scenario_name = os.path.basename(scenario)
            validation_output = validation_output.append({'scenario': scenario_name, 'calibrated_buildings': n_scenario_calib, 'score': scenario_score}, ignore_index=True)
        n_calib = validation_output['calibrated_buildings'].sum()
        score = validation_output['score'].sum()

        global_variables.global_validation_n_calibrated.append(n_calib)
        global_variables.global_validation_percentage.append((n_calib/number_of_buildings)*100)

    print('The number of calibrated buildings is', n_calib)
    print('The final score is', score)
    return score


def calc_errors_per_building(load, monthly_data):
    biased_error = monthly_data['measurements'] - monthly_data[load + '_kWh']
    normalized_mean_biased_error = ((biased_error.sum() / 12) / monthly_data[
        'measurements'].mean()) * 100  # %
    print('NMBE:', normalized_mean_biased_error)
    mean_squared_error = calc_mean_squared_error(monthly_data['measurements'], monthly_data[load + '_kWh'])
    root_mean_squared_error = sqrt(mean_squared_error)  # root mean squared error
    cv_root_mean_squared_error = root_mean_squared_error * 100 / monthly_data['measurements'].mean()
    print('CVRMSE:', cv_root_mean_squared_error)
    return cv_root_mean_squared_error, normalized_mean_biased_error


def calc_building_score(cv_root_mean_squared_error, monthly_data, normalized_mean_biased_error):
    # indicates if the building is calibrated or not
    if abs(normalized_mean_biased_error) < 5 and cv_root_mean_squared_error < 15: #LS#NMBE<5 and CVRMSE <15 for ASHRAE monthly
        ind_calib_building = 1
    else:
        ind_calib_building = 0
    # weights the calibration by building energy consumption
    #ind_score_building = ind_calib_building * 1 #LS#to test max number of buildings calibrated
    ind_score_building = ind_calib_building * sum(monthly_data['measurements'])
    return ind_calib_building, ind_score_building


def get_measured_building_names(locator):
    monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
    measured_building_names = monthly_measured_data.Name.values
    measured_building_names = list(measured_building_names)
    return measured_building_names


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
    measured_building_names = get_measured_building_names(locator)
    scenario_list = [config.scenario]
    locators_of_scenarios = [locator]
    measured_building_names_of_scenarios = [measured_building_names]

    validation(scenario_list,
               locators_of_scenarios,
               measured_building_names_of_scenarios,
               annual=False,
               monthly=True,
               load='GRID',
               )


if __name__ == '__main__':
    main(cea.config.Configuration())
