"""
This file runs all plots of the CEA
"""

from __future__ import division
from __future__ import print_function

import time

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.demand.energy_balance import energy_balance
from cea.plots.demand.energy_demand import energy_demand_district
from cea.plots.demand.energy_use_intensity import energy_use_intensity_district, energy_use_intensity
from cea.plots.demand.heating_reset_schedule import heating_reset_schedule
from cea.plots.demand.load_curve import load_curve
from cea.plots.demand.load_duration_curve import load_duration_curve
from cea.plots.demand.peak_load import peak_load_district, peak_load_building

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
    buildings = config.dashboard.buildings

    # initialize class
    plots = Plots(locator, buildings)

    if len(buildings) == 1:  # when only one building is passed.
        plots.heating_reset_schedule()
        plots.energy_balance()
        plots.load_duration_curve()
        plots.load_curve()
        plots.peak_load()
        plots.energy_use_intensity()
    else:  # when two or more buildings are passed
        plots.load_duration_curve()
        plots.load_curve()
        plots.peak_load()
        plots.energy_use_intensity()
        plots.energy_demand()

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots():

    def __init__(self, locator, buildings):
        self.locator = locator
        self.demand_analysis_fields = ['I_sol_kWh',
                                       'Q_gain_sen_light_kWh',
                                       'Q_gain_sen_app_kWh',
                                       'Q_gain_sen_data_kWh',
                                       'Q_gain_sen_peop_kWh',
                                       'Q_gain_sen_env_kWh',
                                       'Q_gain_sen_wind_kWh',
                                       'Q_gain_sen_vent_kWh',
                                       'I_rad_kWh',
                                       'Qcsf_lat_kWh',
                                       'Q_loss_sen_ref_kWh',
                                       "Ef_kWh",
                                       "Qhsf_kWh",
                                       "Qwwf_kWh",
                                       "Qcsf_kWh"]
        self.temperature_field = ["T_ext_C"]
        self.buildings = self.preprocess_buildings(buildings)
        self.data_processed = self.preprocessing_building_demand()
        self.plot_title_tail = self.preprocess_plot_title(buildings)
        self.plot_output_path_header = self.preprocess_plot_outputpath(buildings)

    def preprocess_plot_outputpath(self, buildings):
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

    def load_duration_curve(self):
        title = "Load Duration Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_duration_curve')
        analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
        data = self.data_processed['hourly_loads']
        plot = load_duration_curve(data, analysis_fields, title, output_path)
        return plot

    def load_curve(self):
        title = "Load Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_curve')
        analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
        data = self.data_processed['hourly_loads']
        plot = load_curve(data, analysis_fields + self.temperature_field, title, output_path)
        return plot

    def peak_load(self):
        title = "Peak Load" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_peak_load')
        analysis_fields = ["Ef0_kW", "Qhsf0_kW", "Qwwf0_kW", "Qcsf0_kW"]
        data = self.data_processed['yearly_loads']
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = peak_load_building(data, analysis_fields, title, output_path)
        else:
            plot = peak_load_district(data, analysis_fields, title, output_path)
        return plot

    def energy_use_intensity(self):
        title = "Energy Use Intensity" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_use_intensity')
        analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        data = self.data_processed['yearly_loads']
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = energy_use_intensity(data, analysis_fields, title, output_path)
        else:
            plot = energy_use_intensity_district(data, analysis_fields, title, output_path)
        return plot

    def energy_demand(self):
        title = "Energy Demand" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_demand')
        analysis_fields = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        data = self.data_processed['yearly_loads']
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def energy_balance(self):
        title = "Energy balance" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_balance')
        analysis_fields = ['I_sol_kWh',
                           'Qhsf_sen_kWh',
                           'Qhs_loss_sen_kWh',
                           'Q_gain_lat_peop_kWh',
                           'Q_gain_sen_light_kWh',
                           'Q_gain_sen_app_kWh',
                           'Q_gain_sen_data_kWh',
                           'Q_gain_sen_peop_kWh',
                           'Q_gain_sen_env_kWh',
                           'Q_gain_sen_wind_kWh',
                           'Q_gain_sen_vent_kWh',
                           'Q_gain_lat_vent_kWh',
                           'I_rad_kWh',
                           'Qcsf_sen_kWh',
                           'Qcsf_lat_kWh',
                           'Qcs_loss_sen_kWh',
                           'Q_loss_sen_env_kWh',
                           'Q_loss_sen_wind_kWh',
                           'Q_loss_sen_vent_kWh',
                           'Q_loss_sen_ref_kWh']
        data = self.data_processed['hourly_loads']
        plot = energy_balance(data, analysis_fields, title, output_path)
        return plot

    def heating_reset_schedule(self):
        title = "Heating Reset Schedule" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_heating_reset_schedule')
        analysis_fields = ["Twwf_sup_C", "Twwf_re_C", "Thsf_sup_C", "Thsf_re_C", "Tcsf_sup_C", "Tcsf_re_C"]
        data = self.data_processed['hourly_loads']
        plot = heating_reset_schedule(data, analysis_fields, title, output_path)
        return plot


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
