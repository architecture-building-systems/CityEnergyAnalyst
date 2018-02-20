"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.demand.energy_use_intensity import energy_use_intensity_district
from cea.plots.demand.load_curve import load_curve
from cea.plots.demand.load_duration_curve import load_duration_curve
from cea.plots.demand.peak_load import peak_load_district
from cea.plots.demand.energy_demand import energy_demand_district
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def aggregate(analysis_fields, buildings, locator):
    for i, building in enumerate(buildings):
        if i == 0:
            df = pd.read_csv(locator.get_demand_results_file(building))
        else:
            df2 = pd.read_csv(locator.get_demand_results_file(building))
            for field in analysis_fields:
                df[field] = df[field].values + df2[field].values
    return df


def dashboard(locator, config):
    # GET LOCAL VARIABLES
    buildings = config.dashboard.buildings

    if buildings == []:
        buildings = pd.read_csv(locator.get_total_demand()).Name.values

    # CREATE LOAD DURATION CURVE
    output_path = locator.get_timeseries_plots_file("District" + '_load_duration_curve')
    title = "Load Duration Curve for District"
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    df = aggregate(analysis_fields, buildings, locator)
    load_duration_curve(df, analysis_fields, title, output_path)

    # CREATE LOAD CURVE
    output_path = locator.get_timeseries_plots_file("District" + '_load_curve')
    title = "Load Curve for District"

    # GET LOCAL WEATHER CONDITIONS
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh","T_ext_C"]
    load_curve(df, analysis_fields, title, output_path)

    # CREATE PEAK LOAD
    df2 = pd.read_csv(locator.get_total_demand())
    output_path = locator.get_timeseries_plots_file("District" + '_peak_load')
    title = "Peak load for District"
    analysis_fields = ["Ef0_kW", "Qhsf0_kW", "Qwwf0_kW", "Qcsf0_kW"]
    peak_load_district(df2, analysis_fields,  title, output_path)

    # CREATE ENERGY USE INTENSITY
    output_path = locator.get_timeseries_plots_file("District"+ '_energy_use_intensity')
    title = "Energy Use Intensity for District"
    analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
    energy_use_intensity_district(df2, analysis_fields, title, output_path)

    # CREATE ENERGY DEMAND
    output_path = locator.get_timeseries_plots_file("District"+ '_energy_demand')
    title = "Energy Demand for District"
    analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
    energy_demand_district(df2, analysis_fields, title, output_path)

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
