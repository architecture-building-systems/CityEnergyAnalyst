"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function


import cea.config
import cea.inputlocator
from cea.plots.life_cycle.operation_costs import operation_costs_district
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def data_processing(analysis_fields, analysis_fields_m2, buildings, locator):

    data_raw = pd.read_csv(locator.get_costs_operation_file()).set_index('Name')
    data_processed = data_raw[analysis_fields+analysis_fields_m2]

    return data_processed.ix[buildings]

def dashboard(locator, config):

    # Local Variables
    # GET LOCAL VARIABLES
    buildings = config.dashboard.buildings

    if buildings == []:
        buildings = pd.read_csv(locator.get_total_demand()).Name.values

    #CREATE RADIATION BUILDINGS

    analysis_fields = ['Qhsf_cost_yr', 'Qwwf_cost_yr' ,'QCf_cost_yr','Ef_cost_yr']
    analysis_fields_m2 = ['Qhsf_cost_m2yr', 'Qwwf_cost_m2yr', 'QCf_cost_m2yr', 'Ef_cost_m2yr']
    data_processed = data_processing(analysis_fields, analysis_fields_m2, buildings, locator)
    output_path = locator.get_timeseries_plots_file("District" + '_operation_costs')
    title = "Operation costs for District"
    operation_costs_district(data_processed, analysis_fields, analysis_fields_m2, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
