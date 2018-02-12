"""
This file runs all plots of the CEA
"""

from __future__ import division
from __future__ import print_function


import cea.config
import cea.inputlocator
from cea.plots.demand.load_duration_curve import load_duration_curve
from cea.plots.demand.load_curve import load_curve
from cea.plots.demand.peak_load import peak_load_district
from cea.plots.demand.energy_use_intensity import energy_use_intensity_district
from cea.plots.demand.energy_demand import energy_demand_district
import time


import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):

    # INITIALIZE TIMER
    t0 = time.clock()

    #local variables
    buildings = config.dashboard.buildings
    if buildings == []: # get all buildings of the district if it is not indicated
        buildings = pd.read_csv(locator.get_total_demand()).Name.values

    #initialize class
    plots = Plots(locator, buildings)

    #Demand Plots
    load_duration_curve_html = plots.load_duration_curve()
    load_curve_html = plots.load_curve()
    peak_load_html = plots.peak_load()
    energy_use_intensity_html = plots.energy_use_intensity()
    energy_demand_html = plots.energy_use_intensity()

    #print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return

class Plots():

    def __init__(self, locator, buildings):
        self.buildings = buildings
        self.locator = locator
        self.demand_analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
        self.temperature_field = ["T_ext_C"]
        self.data_processed = self.preprocessing_building_demand()

    def preprocessing_building_demand(self):
        for i, building in enumerate(self.buildings):
            if i == 0:
                df = pd.read_csv(self.locator.get_demand_results_file(building))
            else:
                df2 = pd.read_csv(self.locator.get_demand_results_file(building))
                for field in self.demand_analysis_fields:
                    df[field] = df[field].values + df2[field].values

        df2 = pd.read_csv(self.locator.get_total_demand())

        return {"hourly_loads":df, "yearly_loads": df2}

    def load_duration_curve(self):
        title = "Load Duration Curve for District"
        output_path = self.locator.get_timeseries_plots_file("District" + '_load_duration_curve')
        data = self.data_processed['hourly_loads']
        plot = load_duration_curve(data, self.demand_analysis_fields, title, output_path)
        return plot

    def load_curve(self):
        title = "Load Curve for District"
        output_path = self.locator.get_timeseries_plots_file("District" + '_load_curve')
        data = self.data_processed['hourly_loads']
        plot = load_curve(data, self.demand_analysis_fields + self.temperature_field, title, output_path)
        return plot

    def peak_load(self):
        title = "Peak load for District"
        output_path = self.locator.get_timeseries_plots_file("District" + '_peak_load')
        analysis_fields = ["Ef0_kW", "Qhsf0_kW", "Qwwf0_kW", "Qcsf0_kW"]
        data = self.data_processed['yearly_loads']
        plot = peak_load_district(data, analysis_fields,  title, output_path)
        return plot

    def energy_use_intensity(self):
        title = "Energy Use Intensity for District"
        output_path = self.locator.get_timeseries_plots_file("District"+ '_energy_use_intensity')
        analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        data = self.data_processed['yearly_loads']
        plot = energy_use_intensity_district(data, analysis_fields, title, output_path)
        return plot

    def energy_demand(self):
        title = "Energy Demand for District"
        output_path = self.locator.get_timeseries_plots_file("District"+ '_energy_demand')
        analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        data = self.data_processed['yearly_loads']
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot


def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)
    plots_main(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
