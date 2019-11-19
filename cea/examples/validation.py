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

__author__ = "Luis Santos"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Luis Santos, Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def validation(locator, archetypes): #confirm what goes in parenthesis here
    """
    This tool compares observed (real life measured data) and predicted (output of the model data) values.
    Annual data is compared in terms of MBE and monthly data in terms of NMBE and CvRMSE (follwing ASHRAE Guideline 14-2002).
    A new input folder with measurements has to be created, with a csv each for monthly and annual data provided as input for this tool.
    A new output csv is generated providing for each building (if measured data is available): building ID | ZIP Code | Measured data (observed) | Modelled data (predicted) | Model errors
    """
    
    #type of validation to run (select only the ones that have a corresponding csv in the inputs folder)
    annual = False
    monthly = True

    ## annual validation
    if annual == True:
        print("annual validation")
        
        # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | Annual energy consumed (kWh)
        measured_data_path = locator.get_measurements()
        annual_measured_data= pd.read_csv(measured_data_path + '/annual_measurements.csv')

        #extract model output
        demand_path = locator.get_demand_results_folder()
        annual_modelled_data = pd.read_csv(demand_path + '/Total_demand.csv')

        #mege the datasets
        merged_annual = annual_modelled_data.merge(annual_measured_data, how='inner', on=['Name']) # extract the modelled buildings that have a corresponding Name (Building ID) simulated by CEA
        annual_modelled_demand = merged_annual.GRID_MWhyr
        annual_measured_demand = merged_annual.Ec_measured

        # calculate errors
        mbe_annual = ((annual_modelled_demand - annual_measured_demand) / annual_modelled_demand) * 100 #mean bias error (%)
        print(mbe_annual)

    ## monthly validation
    if monthly == True:
        print("monthly validation")

        measured_data_path = locator.get_measurements()
        monthly_measured_data = pd.read_csv(measured_data_path + '/monthly_measurements.csv')

        for i in range(0, len(monthly_measured_data.Name)):  # number of buildings that have real data available

            # extract measured data (format: BuildingID (corresponding to CEA model) | ZipCode (optional) | monthly energy consumed (kWh) (Jan-Dec)
            measured_names = monthly_measured_data.Name.values[i]
            print(measured_names)
            monthly_measured_demand = monthly_measured_data.loc[:, 'Ec_m1':'Ec_m12']
            monthly_measured_demand = monthly_measured_demand.values[i]

            # extract model output
            demand_path = locator.get_demand_results_folder()
            building_demand = str(demand_path) + "\\" + str(measured_names) + '.csv'
            hourly_modelled_data = pd.read_csv(building_demand)
            date_idx = pd.to_datetime(hourly_modelled_data.DATE)    #this step is required to have allow the conversion from hourly to monthly data
            hourly_modelled_data['datetime'] = date_idx
            monthly_modelled_data = hourly_modelled_data.resample('M', on ='datetime').sum()
            monthly_modelled_demand = [monthly_modelled_data.GRID_kWh]
            monthly_modelled_demand = pd.DataFrame(monthly_modelled_demand)
            monthly_modelled_demand = monthly_modelled_demand.values[0]

            # calculate errors
            be = monthly_measured_demand - monthly_modelled_demand #bias error
            nmbe = (be.sum()/12) / monthly_measured_demand.mean() #normalized mean bias error
            print(nmbe)
            mse = mean_squared_error(monthly_measured_demand, monthly_modelled_demand) #mean squared error
            rmse = sqrt(mse) #root mean squared error
            cvrmse = rmse * 100 / monthly_measured_demand.mean() #root mean squared error
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
