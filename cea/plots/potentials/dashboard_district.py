"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.potentials.PV_monthly import pv_district_monthly
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_processing(PV_analysis_fields, PVT_analysis_fields, SC_analysis_fields, buildings, locator, weather):
    # get extra data of weather and date
    weather_data = epwreader.epw_reader(weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

    # get data of buildings
    for i, building in enumerate(buildings):
        if i == 0:
            PV_input_data_aggregated_kW = pd.read_csv(locator.PV_results(building), usecols=PV_analysis_fields)
            PVT_input_data_aggregated_kW = pd.read_csv(locator.PVT_results(building), usecols=PVT_analysis_fields)
            SC_input_data_aggregated_kW = pd.read_csv(locator.SC_results(building), usecols=SC_analysis_fields)

        else:
            PV_input_data_aggregated_kW = PV_input_data_aggregated_kW + pd.read_csv(locator.PV_results(building),
                                                                                    usecols=PV_analysis_fields)
            PVT_input_data_aggregated_kW = PVT_input_data_aggregated_kW + pd.read_csv(locator.PVT_results(building),
                                                                                      usecols=PVT_analysis_fields)
            SC_input_data_aggregated_kW = SC_input_data_aggregated_kW + pd.read_csv(locator.SC_results(building),
                                                                                    usecols=SC_analysis_fields)

    input_data_aggregated_kW = PV_input_data_aggregated_kW.join(PVT_input_data_aggregated_kW).join(SC_input_data_aggregated_kW)
    input_data_aggregated_kW['DATE'] = weather_data["date"]

    return input_data_aggregated_kW


def dashboard(locator, config):
    # Local Variables
    # GET LOCAL VARIABLES
    weather = config.weather
    buildings = config.dashboard.buildings

    if buildings == []:
        buildings = pd.read_csv(locator.get_total_demand()).Name.values

    # CREATE RADIATION CURVE_MONTHLY
    output_path = locator.get_timeseries_plots_file("District" + '_photovoltaic_monthly')
    title = "PV Electricity Potential for District"
    PV_analysis_fields = ['PV_walls_east_E_kWh', 'PV_walls_west_E_kWh', 'PV_walls_south_E_kWh', 'PV_walls_north_E_kWh',
                       'PV_roofs_top_E_kWh']
    PVT_analysis_fields = ['walls_east_E_kWh', 'walls_west_E_kWh', 'walls_south_E_kWh', 'walls_north_E_kWh',
                       'roofs_top_E_kWh']
    SC_analysis_fields = ['walls_east_E_kWh', 'walls_west_E_kWh', 'walls_south_E_kWh', 'walls_north_E_kWh',
                       'roofs_top_E_kWh']
    input_data_not_aggregated_kW = data_processing(PV_analysis_fields, PVT_analysis_fields, SC_analysis_fields, buildings, locator, weather)

    #plot for pV
    pv_district_monthly(input_data_not_aggregated_kW, PV_analysis_fields, title, output_path)
    # plot for pVT

    # plot for SC

    # plot for PV, PVT, SC

def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
