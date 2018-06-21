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
from cea.plots.demand.comfort_chart import comfort_chart
from cea.plots.variable_naming import NAMING

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
    buildings = config.plots.buildings

    # initialize class
    plots = Plots(locator, config, buildings)

    if len(buildings) == 1:  # when only one building is passed.
        plots.heating_reset_schedule()
        plots.energy_balance()
        plots.load_duration_curve()
        plots.load_curve()
        plots.peak_load()
        plots.energy_use_intensity()
        plots.comfort_chart()
        plots.load_duration_curve_final()
        plots.load_curve_final()
        plots.peak_load_final()
        plots.energy_use_intensity_final()
        plots.energy_demand_final()
    else:  # when two or more buildings are passed
        plots.load_duration_curve()
        plots.load_curve()
        plots.peak_load()
        plots.energy_use_intensity()
        plots.energy_demand()
        plots.load_duration_curve_final()
        plots.load_curve_final()
        plots.peak_load_final()
        plots.energy_use_intensity_final()
        plots.energy_demand_final()


    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots():

    def __init__(self, locator, config, buildings):
        self.locator = locator
        self.config = config
        self.demand_analysis_fields = ['I_sol_kWh',
                                       'Q_gain_sen_light_kWh',
                                       'Q_gain_sen_app_kWh',
                                       'Q_gain_sen_data_kWh',
                                       'Q_gain_sen_peop_kWh',
                                       'Q_gain_sen_wall_kWh',
                                       'Q_gain_sen_base_kWh',
                                       'Q_gain_sen_roof_kWh',
                                       'Q_gain_sen_wind_kWh',
                                       'Q_gain_sen_vent_kWh',
                                       'I_rad_kWh',
                                       'Qcs_lat_sys_kWh',
                                       'Q_loss_sen_ref_kWh',
                                       "GRID_kWh",
                                       "PV_kWh",
                                       "DH_hs_kWh",
                                       "DH_ww_kWh",
                                       "E_sys_kWh",
                                       "Qhs_sys_kWh",
                                       "Qww_sys_kWh",
                                       "Qcs_sys_kWh",
                                       'DC_cdata_kWh',
                                       'DC_cre_kWh',
                                       "DC_cs_kWh",
                                       'NG_hs_kWh',
                                       'COAL_hs_kWh',
                                       'OIL_hs_kWh',
                                       'WOOD_hs_kWh',
                                       'NG_ww_kWh',
                                       'COAL_ww_kWh',
                                       'OIL_ww_kWh',
                                       'WOOD_ww_kWh',
                                       'SOLAR_ww_kWh',
                                       'SOLAR_hs_kWh',
                                       'E_ww_kWh',
                                       'E_hs_kWh',
                                       'E_cs_kWh',
                                       'E_cdata_kWh',
                                       'E_cre_kWh'
                                       ]
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

    def erase_zeros(self, data, fields):
        analysis_fields_no_zero = []
        for field in fields:
            sum = data[field].sum()
            if sum >0 :
                analysis_fields_no_zero += [field]
        return analysis_fields_no_zero


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
        analysis_fields = ["E_sys_kWh",
                           "Qhs_sys_kWh", "Qww_sys_kWh",
                           "Qcs_sys_kWh",'Qcdata_sys_kWh', 'Qcre_sys_kWh']
        data = self.data_processed['hourly_loads'].copy()
        plot = load_duration_curve(data, analysis_fields, title, output_path)
        return plot

    def load_curve(self):
        title = "Load Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_curve')
        analysis_fields = ["E_sys_kWh",
                           "Qhs_sys_kWh", "Qww_sys_kWh",
                           "Qcs_sys_kWh",'Qcdata_sys_kWh', 'Qcre_sys_kWh']
        data = self.data_processed['hourly_loads'].copy()
        plot = load_curve(data, analysis_fields + self.temperature_field, title, output_path)
        return plot

    def peak_load(self):
        title = "Peak Load" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_peak_load')
        analysis_fields = ["E_sys0_kW",
                           "Qhs_sys0_kW", "Qww_sys0_kW",
                           "Qcs_sys0_kW", 'Qcdata_sys0_kW', 'Qcre_sys0_kW']
        data = self.data_processed['yearly_loads'].copy()
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = peak_load_building(data, analysis_fields, title, output_path)
        else:
            plot = peak_load_district(data, analysis_fields, title, output_path)
        return plot

    def energy_use_intensity(self):
        title = "Energy Use Intensity" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_use_intensity')
        analysis_fields = ["E_sys_MWhyr",
                           "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                           "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        data = self.data_processed['yearly_loads'].copy()
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = energy_use_intensity(data, analysis_fields, title, output_path)
        else:
            plot = energy_use_intensity_district(data, analysis_fields, title, output_path)
        return plot

    def energy_demand(self):
        title = "Energy Demand" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_demand')
        analysis_fields = ["E_sys_MWhyr",
                           "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                           "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        data = self.data_processed['yearly_loads'].copy()
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def load_duration_curve_final(self):
        title = "Load Duration Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_duration_curve_supply')
        analysis_fields = ["DH_hs_kWh", "DH_ww_kWh",
                           'SOLAR_ww_kWh','SOLAR_hs_kWh',
                           "DC_cs_kWh",'DC_cdata_kWh','DC_cre_kWh',
                           'GRID_kWh','PV_kWh',
                           'NG_hs_kWh',
                           'COAL_hs_kWh',
                           'OIL_hs_kWh',
                           'WOOD_hs_kWh',
                           'NG_ww_kWh',
                           'COAL_ww_kWh',
                           'OIL_ww_kWh',
                           'WOOD_ww_kWh']
        data = self.data_processed['hourly_loads'].copy()
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = load_duration_curve(data, analysis_fields, title, output_path)
        return plot

    def load_curve_final(self):
        title = "Load Curve" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_load_curve_supply')
        analysis_fields = ["DH_hs_kWh", "DH_ww_kWh",
                           'SOLAR_ww_kWh','SOLAR_hs_kWh',
                           "DC_cs_kWh",'DC_cdata_kWh','DC_cre_kWh',
                           'GRID_kWh','PV_kWh',
                           'NG_hs_kWh',
                           'COAL_hs_kWh',
                           'OIL_hs_kWh',
                           'WOOD_hs_kWh',
                           'NG_ww_kWh',
                           'COAL_ww_kWh',
                           'OIL_ww_kWh',
                           'WOOD_ww_kWh']
        data = self.data_processed['hourly_loads'].copy()
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = load_curve(data, analysis_fields + self.temperature_field, title, output_path)
        return plot

    def peak_load_final(self):
        title = "Peak Load" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_peak_load_supply')
        analysis_fields = ["DH_hs0_kW", "DH_ww0_kW",
                           'SOLAR_ww0_kW','SOLAR_hs0_kW',
                           "DC_cs0_kW",'DC_cdata0_kW','DC_cre0_kW',
                           'GRID0_kW', 'PV0_kW',
                           'NG_hs0_kW',
                           'COAL_hs0_kW',
                           'OIL_hs0_kW',
                           'WOOD_hs0_kW',
                           'NG_ww0_kW',
                           'COAL_ww0_kW',
                           'OIL_ww0_kW',
                           'WOOD_ww0_kW',]
        data = self.data_processed['yearly_loads'].copy()
        analysis_fields = self.erase_zeros(data, analysis_fields)
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = peak_load_building(data, analysis_fields, title, output_path)
        else:
            plot = peak_load_district(data, analysis_fields, title, output_path)
        return plot

    def energy_use_intensity_final(self):
        title = "Energy Use Intensity" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_use_intensity_supply')
        analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr', 'GRID_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr',
                           ]
        data = self.data_processed['yearly_loads'].copy()
        analysis_fields = self.erase_zeros(data, analysis_fields)
        if len(self.buildings) == 1:
            data = data.set_index("Name").ix[self.buildings[0]]
            plot = energy_use_intensity(data, analysis_fields, title, output_path)
        else:
            plot = energy_use_intensity_district(data, analysis_fields, title, output_path)
        return plot

    def energy_demand_final(self):
        title = "Energy Demand" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_demand_supply')
        analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr",
                           'SOLAR_ww_MWhyr','SOLAR_hs_MWhyr',
                           "DC_cs_MWhyr",'DC_cdata_MWhyr','DC_cre_MWhyr',
                           'PV_MWhyr', 'GRID_MWhyr',
                           'NG_hs_MWhyr',
                           'COAL_hs_MWhyr',
                           'OIL_hs_MWhyr',
                           'WOOD_hs_MWhyr',
                           'NG_ww_MWhyr',
                           'COAL_ww_MWhyr',
                           'OIL_ww_MWhyr',
                           'WOOD_ww_MWhyr']
        data = self.data_processed['yearly_loads'].copy()
        analysis_fields = self.erase_zeros(data, analysis_fields)
        plot = energy_demand_district(data, analysis_fields, title, output_path)
        return plot

    def energy_balance(self):
        title = "Energy balance" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_energy_balance')
        analysis_fields = ['I_sol_kWh',
                           'Qhs_tot_sen_kWh',
                           'Qhs_loss_sen_kWh',
                           'Q_gain_lat_peop_kWh',
                           'Q_gain_sen_light_kWh',
                           'Q_gain_sen_app_kWh',
                           'Q_gain_sen_data_kWh',
                           'Q_gain_sen_peop_kWh',
                           'Q_gain_sen_wall_kWh',
                           'Q_gain_sen_base_kWh',
                           'Q_gain_sen_roof_kWh',
                           'Q_gain_sen_wind_kWh',
                           'Q_gain_sen_vent_kWh',
                           'Q_gain_lat_vent_kWh',
                           'I_rad_kWh',
                           'Qcs_tot_sen_kWh',
                           'Qcs_tot_lat_kWh',
                           'Qcs_loss_sen_kWh',
                           'Q_loss_sen_wall_kWh',
                           'Q_loss_sen_base_kWh',
                           'Q_loss_sen_roof_kWh',
                           'Q_loss_sen_wind_kWh',
                           'Q_loss_sen_vent_kWh',
                           'Q_loss_sen_ref_kWh']
        data = self.data_processed['hourly_loads'].copy()
        building_data = self.data_processed['yearly_loads'].copy()
        normalize_value = building_data.set_index("Name").ix[self.buildings[0]]['GFA_m2']
        plot = energy_balance(data, analysis_fields, normalize_value, title, output_path)
        return plot

    def heating_reset_schedule(self):
        title = "Heating Reset Schedule" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_heating_reset_schedule')
        analysis_fields = ["Tww_sys_sup_C", "Tww_sys_re_C", 'Tcs_sys_re_ahu_C', 'Tcs_sys_re_aru_C', 'Tcs_sys_re_scu_C', 'Tcs_sys_sup_ahu_C', 'Tcs_sys_sup_aru_C',
                           'Tcs_sys_sup_scu_C', 'Ths_sys_re_ahu_C', 'Ths_sys_re_aru_C', 'Ths_sys_re_shu_C', 'Ths_sys_sup_ahu_C', 'Ths_sys_sup_aru_C',
                            'Ths_sys_sup_shu_C', ]
        data = self.data_processed['hourly_loads'].copy()
        plot = heating_reset_schedule(data, analysis_fields, title, output_path)
        return plot

    def comfort_chart(self):
        title = "Comfort Chart" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_comfort_chart')
        data = self.data_processed['hourly_loads'].copy()
        config = self.config
        locator = self.locator
        plot = comfort_chart(data, title, output_path, config, locator)
        return plot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
