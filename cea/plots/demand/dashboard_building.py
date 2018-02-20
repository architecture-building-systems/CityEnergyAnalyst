"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.demand.energy_use_intensity import energy_use_intensity
from cea.plots.demand.heating_reset_schedule import heating_reset_schedule
from cea.plots.demand.load_curve import load_curve
from cea.plots.demand.load_duration_curve import load_duration_curve
from cea.plots.demand.peak_load import peak_load_building
from cea.plots.demand.energy_balance import energy_balance
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def dashboard(locator, config):
    # GET LOCAL VARIABLES
    building = config.dashboard.buildings
    if len(building) > 1:
        raise Exception("cannot run dashboard of demand_buildings for more than one building at the time")
    else:
        building = building[0]

    # GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    # CREATE ENERGY BALANCE
    output_path = locator.get_timeseries_plots_file(building + '_energy_balance')
    title = 'Energy balance for Building ' + building
    analysis_fields = ['I_sol_kWh',
                       'Qhsf_kWh',
                       'Qhsf_sys_loss_kWh',
                       'Qgain_lat_peop_kWh',
                       'Qgain_light_kWh',
                       'Qgain_app_kWh',
                       'Qgain_data_kWh',
                       'Qgain_pers_kWh',
                       'Qgain_roof_kWh',
                       'Qgain_wall_kWh',
                       'Qgain_wind_kWh',
                       'Qgain_base_kWh',
                       'Qgain_vent_kWh',
                       'Qgain_lat_vent_kWh',
                       'I_rad_kWh',
                       'Qcsf_sen_kWh',
                       'Qcsf_lat_kWh',
                       'Qcsf_sys_loss_kWh',
                       'Qloss_roof_kWh',
                       'Qloss_wall_kWh',
                       'Qloss_wind_kWh',
                       'Qloss_base_kWh',
                       'Qloss_vent_kWh',
                       'Q_cool_ref_kWh']
    energy_balance(df, analysis_fields, title, output_path)

    # CREATE LOAD CURVE
    output_path = locator.get_timeseries_plots_file(building + '_load_curve')
    title = "Load Curve for Building " + building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh", "T_int_C", "T_ext_C"]
    load_curve(df, analysis_fields, title, output_path)

    # CREATE LOAD DURATION CURVE
    output_path = locator.get_timeseries_plots_file(building + '_load_duration_curve')
    title = "Load Duration Curve for Building " + building
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    load_duration_curve(df, analysis_fields, title, output_path)

    # CREATE HEATING RESET SCHEDULE
    output_path = locator.get_timeseries_plots_file(building + '_heating_reset_schedule')
    title = "Heating Reset Schedule for Building " + building
    analysis_fields = ["Twwf_sup_C", "Twwf_re_C", "Thsf_sup_C", "Thsf_re_C", "Tcsf_sup_C", "Tcsf_re_C"]
    heating_reset_schedule(df, analysis_fields, title, output_path)

    # CREATE TOTAL LOAD STACKED
    df2 = pd.read_csv(locator.get_total_demand()).set_index("Name")
    df2 = df2.ix[building]
    output_path = locator.get_timeseries_plots_file(building + '_energy_use_intensity')
    title = "Energy Use Intensity for Building " + building
    analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
    energy_use_intensity(df2, analysis_fields, title, output_path)

    # CREATE PEAK LOAD STACKED
    output_path = locator.get_timeseries_plots_file(building + '_peak_load')
    title = "Peak load for Building " + building
    analysis_fields = ["Ef0_kW", "Qhsf0_kW", "Qwwf0_kW", "Qcsf0_kW"]
    peak_load_building(df2, analysis_fields, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
