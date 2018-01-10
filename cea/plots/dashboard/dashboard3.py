"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator

import pandas as pd
from cea.utilities import epwreader
from cea.plots.dashboard.load_duration_curve import load_duration_curve
from cea.plots.dashboard.heating_reset_schedule import heating_reset_schedule
from cea.plots.dashboard.load_curve import load_curve
from cea.plots.dashboard.load_year_stacked import load_year_stacked

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def dashboard_demand(locator, config):

    #GET LOCAL VARIABLES
    building = "B05"

    #GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    #GET LOCAL WEATHER CONDITIONS
    weather_data = epwreader.epw_reader(config.weather)[["drybulb_C", "wetbulb_C", "skytemp_C"]]
    df["T_out_dry_C"] = weather_data["drybulb_C"].values
    df["T_out_wet_C"] = weather_data["wetbulb_C"].values
    df["T_sky_C"] = weather_data["skytemp_C"].values

    #CREATE LOAD DURATION CURVE
    output_path = locator.get_timeseries_plots_file(building+'_load_duration_curve')
    title = "Load Duration Curve for Building " +building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    load_duration_curve(df, analysis_fields, title, output_path)

    #CREATE HEATING RESET SCHEDULE
    output_path = locator.get_timeseries_plots_file(building+'_heating_reset_schedule')
    title = "Heating Reset Schedule for Building " +building
    analysis_fields = ["Twwf_sup_C", "Twwf_re_C", "Thsf_sup_C", "Thsf_re_C", "Tcsf_sup_C", "Tcsf_re_C"]
    heating_reset_schedule(df, analysis_fields, title, output_path)

    #CREATE LOAD CURVE
    output_path = locator.get_timeseries_plots_file(building+'_load_curve')
    title = "Load Curve for Building " +building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh", "T_int_C", "T_out_dry_C"]
    load_curve(df, analysis_fields, title, output_path)

    #CREATE TOTAL LOAD STACKED
    output_path = locator.get_timeseries_plots_file(building+'_total_load')
    title = "Load Curve for Building " +building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    load_year_stacked(df, analysis_fields, title, output_path)

def main(config):

    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running template with scenario = %s" % config.scenario)

    dashboard_demand(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
