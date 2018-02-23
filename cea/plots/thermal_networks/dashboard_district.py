"""
This file runs all plots of the CEA
"""

from __future__ import division
from __future__ import print_function

import time

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.thermal_networks.load_curve import load_curve

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # initialize timer
    t0 = time.clock()

    # local variables
    network_type = config.dashboard.network_type
    network_name = config.dashboard.network_name

    # initialize class
    plots = Plots(locator, network_type, network_name)

    if len(buildings) == 1:  # when only one building is passed.
        plots.load_curve()
    else:  # when two or more buildings are passed
        plots.load_curve()

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots():

    def __init__(self, locator, network_type, network_name):
        self.locator = locator
        self.demand_analysis_fields = ['I_sol_kWh',
                                       'Qgain_light_kWh',
                                       'Qgain_app_kWh',
                                       'Qgain_data_kWh',
                                       'Qgain_pers_kWh',
                                       'Qgain_roof_kWh',
                                       'Qgain_wall_kWh',
                                       'Qgain_wind_kWh',
                                       'Qgain_base_kWh',
                                       'Qgain_vent_kWh',
                                       'I_rad_kWh',
                                       'Qcsf_lat_kWh',
                                       'Q_cool_ref_kWh',
                                       "Ef_kWh",
                                       "Qhsf_kWh",
                                       "Qwwf_kWh",
                                       "Qcsf_kWh"]
        self.network_name = self.preprocess_buildings(network_name)
        self.data_processed = self.preprocessing_building_demand()
        self.plot_title_tail = self.preprocess_plot_title(network_type)
        self.plot_output_path_header = self.preprocess_plot_outputpath(network_type, self.network_name)

    def preprocess_plot_outputpath(self, network_type, network_name):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return "District"
        elif len(buildings) == 1:
            return "Building_" + str(buildings[0])
        else:
            return "District"

    def preprocess_plot_title(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return " for District"
        elif len(buildings) == 1:
            return " for Building " + str(buildings[0])
        else:
            return " for Selected Buildings"

    def preprocess_buildings(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return self.locator.get_zone_building_names()
        else:
            return buildings

    def preprocessing_building_demand(self):
        for i, building in enumerate(self.buildings):
            if i == 0:
                df = pd.read_csv(self.locator.get_demand_results_file(building))
            else:
                df2 = pd.read_csv(self.locator.get_demand_results_file(building))
                for field in self.demand_analysis_fields:
                    df[field] = df[field].values + df2[field].values

        df3 = pd.read_csv(self.locator.get_total_demand())

        return {"hourly_loads": df.set_index("DATE"), "yearly_loads": df3}

    def load_curve(self):
        title = "Load Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_curve')
        analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
        data = self.data_processed['hourly_loads']
        plot = load_curve(data, analysis_fields, title, output_path)
        return plot

 def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
