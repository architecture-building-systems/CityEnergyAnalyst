"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.solar_technology_potentials.all_tech_hourly_curve import all_tech_district_hourly
from cea.plots.solar_technology_potentials.all_tech_yearly import all_tech_district_yearly
from cea.plots.solar_technology_potentials.pv_monthly import pv_district_monthly
from cea.plots.solar_technology_potentials.pvt_monthly import pvt_district_monthly
from cea.plots.solar_technology_potentials.sc_monthly import sc_district_monthly
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca", "Shanshan Hsieh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

tech_to_plot = []


def plot_main(locator, config):
    """

    :param cea.inputlocator.InputLocator locator: locate input files
    :param cea.config.Configuration config: stores the CEA configuration
    :return:
    """
    # local variables
    buildings = config.plots.buildings
    weather = config.weather

    # initialize class
    plots = Plots(locator, buildings, weather, config)
    category = "basic//solar-technologies"
    # create plots
    # if len(buildings) == 1:  # when only one building is passed.
    #     raise Exception('THIS TOOL ONLY WORKS FOR TWO OR MORE BUILDINGS')
    #
    #     x = 1  # do nothing for now! to be improved!
    # else:  # when two or more buildings are passed
    plots.pv_district_monthly(category)
    plots.pvt_district_monthly(category)
    plots.sc_fp_district_monthly(category)
    plots.sc_et_district_monthly(category)
    plots.all_tech_district_yearly(category)
    plots.all_tech_district_hourly(category)


class Plots(object):
    def __init__(self, locator, buildings, weather, config):
        """

        :param cea.inputlocator.InputLocator locator: locate input files
        :param cea.config.Configuration config: stores the CEA configuration
        :param weather:
        """
        self.weather = weather
        self.locator = locator
        self.buildings = self.preprocess_buildings(buildings)
        self.analysis_fields = {'PV': ['PV_walls_east_E_kWh', 'PV_walls_west_E_kWh', 'PV_walls_south_E_kWh',
                                       'PV_walls_north_E_kWh', 'PV_roofs_top_E_kWh'],
                                'PVT': ['PVT_walls_east_E_kWh', 'PVT_walls_west_E_kWh', 'PVT_walls_south_E_kWh',
                                        'PVT_walls_north_E_kWh',
                                        'PVT_roofs_top_E_kWh', 'PVT_walls_east_Q_kWh', 'PVT_walls_west_Q_kWh',
                                        'PVT_walls_south_Q_kWh', 'PVT_walls_north_Q_kWh',
                                        'PVT_roofs_top_Q_kWh'],
                                'SC_FP': ['SC_FP_walls_east_Q_kWh', 'SC_FP_walls_west_Q_kWh', 'SC_FP_walls_south_Q_kWh',
                                          'SC_FP_walls_north_Q_kWh', 'SC_FP_roofs_top_Q_kWh'],
                                'SC_ET': ['SC_ET_walls_east_Q_kWh', 'SC_ET_walls_west_Q_kWh', 'SC_ET_walls_south_Q_kWh',
                                          'SC_ET_walls_north_Q_kWh', 'SC_ET_roofs_top_Q_kWh']}
        self.pv_analysis_fields = ['PV_walls_east_E_kWh', 'PV_walls_west_E_kWh', 'PV_walls_south_E_kWh',
                                   'PV_walls_north_E_kWh', 'PV_roofs_top_E_kWh']
        self.sc_fp_analysis_fields = ['SC_FP_walls_east_Q_kWh', 'SC_FP_walls_west_Q_kWh', 'SC_FP_walls_south_Q_kWh',
                                      'SC_FP_walls_north_Q_kWh', 'SC_FP_roofs_top_Q_kWh']
        self.sc_et_analysis_fields = ['SC_ET_walls_east_Q_kWh', 'SC_ET_walls_west_Q_kWh', 'SC_ET_walls_south_Q_kWh',
                                      'SC_ET_walls_north_Q_kWh', 'SC_ET_roofs_top_Q_kWh']
        self.sc_analysis_fields = ['SC_walls_east_Q_kWh', 'SC_walls_west_Q_kWh', 'SC_walls_south_Q_kWh',
                                   'SC_walls_north_Q_kWh', 'SC_roofs_top_Q_kWh']
        self.pvt_analysis_fields = ['PVT_walls_east_E_kWh', 'PVT_walls_west_E_kWh', 'PVT_walls_south_E_kWh',
                                    'PVT_walls_north_E_kWh',
                                    'PVT_roofs_top_E_kWh', 'PVT_walls_east_Q_kWh', 'PVT_walls_west_Q_kWh',
                                    'PVT_walls_south_Q_kWh', 'PVT_walls_north_Q_kWh',
                                    'PVT_roofs_top_Q_kWh']
        self.all_tech_analysis_fields = self.get_analysis_fields(self.analysis_fields)
        self.data_processed = self.preprocessing_data(self.all_tech_analysis_fields, self.sc_analysis_fields,
                                                      self.buildings)
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

    def get_analysis_fields(self, analysis_fields):

        tech_to_plot = []
        if os.path.exists(self.locator.PV_totals()):
            tech_to_plot.extend(['PV'])
        if os.path.exists(self.locator.PVT_totals()):
            tech_to_plot.extend(['PVT'])
        if os.path.exists(self.locator.SC_totals(panel_type='FP')):
            tech_to_plot.extend(['SC_FP'])
        if os.path.exists(self.locator.SC_totals(panel_type='ET')):
            tech_to_plot.extend(['SC_ET'])

        all_tech_analysis_fields = {}
        for tech in tech_to_plot:
            all_tech_analysis_fields[tech] = analysis_fields[tech]

        return all_tech_analysis_fields

    def preprocess_buildings(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return self.locator.get_zone_building_names()
        else:
            return buildings

    def preprocessing_data(self, all_tech_analysis_fields, SC_analysis_fields, buildings):

        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        # get data for all buildings
        annual_results_all_buildings_kW = []

        # get data of buildings
        for i, building in enumerate(buildings):
            if i == 0:
                hourly_data_per_building_kW = {}
                # read data from the first building
                if 'PV' in all_tech_analysis_fields:
                    PV_hourly_aggregated_kW = pd.read_csv(self.locator.PV_results(building),
                                                          usecols=all_tech_analysis_fields['PV'])
                    hourly_data_per_building_kW['PV'] = pd.read_csv(self.locator.PV_results(building),
                                                                    usecols=all_tech_analysis_fields['PV'])
                if 'PVT' in all_tech_analysis_fields:
                    PVT_hourly_aggregated_kW = pd.read_csv(self.locator.PVT_results(building),
                                                           usecols=all_tech_analysis_fields['PVT'])
                    hourly_data_per_building_kW['PVT'] = pd.read_csv(self.locator.PVT_results(building),
                                                                     usecols=all_tech_analysis_fields['PVT'])
                if 'SC_FP' in all_tech_analysis_fields:
                    SC_FP_hourly_aggregated_kW = pd.read_csv(self.locator.SC_results(building, panel_type='FP'),
                                                             usecols=SC_analysis_fields)
                    SC_FP_hourly_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_FP_walls_east_Q_kWh',
                                                               'SC_walls_west_Q_kWh': 'SC_FP_walls_west_Q_kWh',
                                                               'SC_walls_south_Q_kWh': 'SC_FP_walls_south_Q_kWh',
                                                               'SC_walls_north_Q_kWh': 'SC_FP_walls_north_Q_kWh',
                                                               'SC_roofs_top_Q_kWh': 'SC_FP_roofs_top_Q_kWh'},
                                                      inplace=True)
                    hourly_data_per_building_kW['SC_FP'] = SC_FP_hourly_aggregated_kW

                if 'SC_ET' in all_tech_analysis_fields:
                    SC_ET_hourly_aggregated_kW = pd.read_csv(self.locator.SC_results(building, panel_type='ET'),
                                                             usecols=SC_analysis_fields)
                    SC_ET_hourly_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_ET_walls_east_Q_kWh',
                                                               'SC_walls_west_Q_kWh': 'SC_ET_walls_west_Q_kWh',
                                                               'SC_walls_south_Q_kWh': 'SC_ET_walls_south_Q_kWh',
                                                               'SC_walls_north_Q_kWh': 'SC_ET_walls_north_Q_kWh',
                                                               'SC_roofs_top_Q_kWh': 'SC_ET_roofs_top_Q_kWh'},
                                                      inplace=True)
                    hourly_data_per_building_kW['SC_ET'] = SC_ET_hourly_aggregated_kW

                # calculate annual results of technologies
                annual_results_per_building_kW = pd.Series()
                for tech in hourly_data_per_building_kW.keys():
                    annual_results_per_building_kW = annual_results_per_building_kW.append(
                        hourly_data_per_building_kW[tech].sum(axis=0))
                annual_results_all_buildings_kW = pd.DataFrame({building: annual_results_per_building_kW},
                                                               index=annual_results_per_building_kW.index).T
            else:
                # read data from each building
                if 'PV' in all_tech_analysis_fields:
                    hourly_data_per_building_kW['PV'] = pd.read_csv(self.locator.PV_results(building),
                                                                    usecols=all_tech_analysis_fields['PV'])
                    PV_hourly_aggregated_kW = PV_hourly_aggregated_kW + hourly_data_per_building_kW['PV']
                if 'PVT' in all_tech_analysis_fields:
                    hourly_data_per_building_kW['PVT'] = pd.read_csv(self.locator.PVT_results(building),
                                                                     usecols=all_tech_analysis_fields['PVT'])
                    PVT_hourly_aggregated_kW = PVT_hourly_aggregated_kW + hourly_data_per_building_kW['PVT']
                if 'SC_FP' in all_tech_analysis_fields:
                    SC_FP_houlry_per_building_kW = pd.read_csv(self.locator.SC_results(building, panel_type='FP'),
                                                               usecols=SC_analysis_fields)
                    SC_FP_houlry_per_building_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_FP_walls_east_Q_kWh',
                                                                 'SC_walls_west_Q_kWh': 'SC_FP_walls_west_Q_kWh',
                                                                 'SC_walls_south_Q_kWh': 'SC_FP_walls_south_Q_kWh',
                                                                 'SC_walls_north_Q_kWh': 'SC_FP_walls_north_Q_kWh',
                                                                 'SC_roofs_top_Q_kWh': 'SC_FP_roofs_top_Q_kWh'},
                                                        inplace=True)
                    hourly_data_per_building_kW['SC_FP'] = SC_FP_houlry_per_building_kW
                    SC_FP_hourly_aggregated_kW = SC_FP_hourly_aggregated_kW + SC_FP_houlry_per_building_kW
                if 'SC_ET' in all_tech_analysis_fields:
                    SC_ET_hourly_per_building_kW = pd.read_csv(self.locator.SC_results(building, panel_type='ET'),
                                                               usecols=SC_analysis_fields)
                    SC_ET_hourly_per_building_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_ET_walls_east_Q_kWh',
                                                                 'SC_walls_west_Q_kWh': 'SC_ET_walls_west_Q_kWh',
                                                                 'SC_walls_south_Q_kWh': 'SC_ET_walls_south_Q_kWh',
                                                                 'SC_walls_north_Q_kWh': 'SC_ET_walls_north_Q_kWh',
                                                                 'SC_roofs_top_Q_kWh': 'SC_ET_roofs_top_Q_kWh'},
                                                        inplace=True)
                    hourly_data_per_building_kW['SC_ET'] = SC_ET_hourly_per_building_kW
                    SC_ET_hourly_aggregated_kW = SC_ET_hourly_aggregated_kW + SC_ET_hourly_per_building_kW

                # calculate annual result of technologies
                annual_results_per_building_kW = pd.Series()
                for tech in all_tech_analysis_fields:
                    annual_results_per_building_kW = annual_results_per_building_kW.append(
                        hourly_data_per_building_kW[tech].sum(axis=0))
                df_annual_results_per_building_kW = pd.DataFrame({building: annual_results_per_building_kW},
                                                                 index=annual_results_per_building_kW.index).T
                annual_results_all_buildings_kW = annual_results_all_buildings_kW.append(
                    df_annual_results_per_building_kW)

        # join hourly results of technologies
        dfs = []
        dfs.append(PV_hourly_aggregated_kW) if 'PV' in all_tech_analysis_fields else dfs
        dfs.append(PVT_hourly_aggregated_kW) if 'PVT' in all_tech_analysis_fields else dfs
        dfs.append(SC_FP_hourly_aggregated_kW) if 'SC_FP' in all_tech_analysis_fields else dfs
        dfs.append(SC_ET_hourly_aggregated_kW) if 'SC_ET' in all_tech_analysis_fields else dfs

        def join_dfs(ldf, rdf):
            return ldf.join(rdf, how='inner')

        hourly_results_aggregated_kW = reduce(join_dfs, dfs)
        hourly_results_aggregated_kW['DATE'] = weather_data["date"]

        return {"data_hourly": hourly_results_aggregated_kW, "data_yearly": annual_results_all_buildings_kW}

    def pv_district_monthly(self, category):
        pv_title = "PV Electricity Potential for" + self.plot_title_tail
        pv_output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_photovoltaic_monthly',
                                                                category)
        if 'PV' in self.all_tech_analysis_fields:
            data = self.data_processed["data_hourly"].copy()
            pv_district_monthly(data, self.pv_analysis_fields, pv_title, pv_output_path)
            print('Photovoltaic panel results plotted')
        return

    def pvt_district_monthly(self, category):
        pvt_title = "PVT Electricity/Thermal Potential for" + self.plot_title_tail
        pvt_output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_photovoltaic_thermal_monthly', category)
        if 'PVT' in self.all_tech_analysis_fields:
            data = self.data_processed["data_hourly"].copy()
            pvt_district_monthly(data, self.pvt_analysis_fields, pvt_title, pvt_output_path)
            print('Photovoltaic-thermal panel results plotted')
        return

    def sc_fp_district_monthly(self, category):
        sc_title = "Flat Plate SC Thermal Potential for" + self.plot_title_tail
        sc_output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_FP_solar_collector_monthly', category)
        if 'SC_FP' in self.all_tech_analysis_fields:
            data = self.data_processed["data_hourly"].copy()
            sc_district_monthly(data, self.sc_fp_analysis_fields, sc_title, sc_output_path)
            print('Flat-plate Solar Collectors results plotted')
        return

    def sc_et_district_monthly(self, category):
        sc_title = "Evacuated Tube SC Thermal Potential for" + self.plot_title_tail
        sc_output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_ET_solar_collector_monthly', category)
        if 'SC_ET' in self.all_tech_analysis_fields:
            data = self.data_processed["data_hourly"].copy()
            sc_district_monthly(data, self.sc_et_analysis_fields, sc_title, sc_output_path)
            print('Evacuated-tube Solar Collectors results plotted')
        return

    def all_tech_district_yearly(self, category):
        all_tech_title = "PV/SC/PVT Potential for" + self.plot_title_tail
        all_tech_output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_solar_tech_yearly', category)
        data = self.data_processed["data_yearly"].copy()
        all_tech_district_yearly(data, self.pv_analysis_fields, self.pvt_analysis_fields, self.sc_fp_analysis_fields,
                                 self.sc_et_analysis_fields, all_tech_title, all_tech_output_path)

    def all_tech_district_hourly(self, category):
        all_tech_title = "PV/SC/PVT Potential for" + self.plot_title_tail
        all_tech_output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_solar_tech_hourly', category)
        data = self.data_processed["data_hourly"].copy()
        all_tech_district_hourly(data, self.all_tech_analysis_fields, all_tech_title, all_tech_output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plot_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
