"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
import os
import cea.config
import cea.inputlocator
from cea.plots.solar_technology_potentials.all_tech_yearly import all_tech_district_yearly
from cea.plots.solar_technology_potentials.all_tech_hourly_curve import all_tech_district_hourly
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

    # create plots
    if len(buildings) == 1:  # when only one building is passed.
        x = 1  # do nothing for now! to be improved!
    else:  # when two or more buildings are passed
        plots.pv_district_monthly()
        plots.pvt_district_monthly()
        plots.sc_fp_district_monthly()
        plots.sc_et_district_monthly()
        plots.all_tech_district_yearly()
        plots.all_tech_district_hourly()



class Plots():
    def __init__(self, locator, buildings, weather, config):
        """

        :param cea.inputlocator.InputLocator locator: locate input files
        :param cea.config.Configuration config: stores the CEA configuration
        :param weather:
        """
        self.weather = weather
        self.locator = locator
        self.buildings = self.preprocess_buildings(buildings)
        self.analysis_fields = {'PV':['PV_walls_east_E_kWh', 'PV_walls_west_E_kWh', 'PV_walls_south_E_kWh',
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
        self.data_processed = self.preprocessing_data(self.all_tech_analysis_fields, self.sc_analysis_fields, self.buildings)

    def get_analysis_fields(self, analysis_fields):

        tech_to_plot = []
        if os.path.exists(self.locator.PV_totals()):
            tech_to_plot.extend(['PV'])
        if os.path.exists(self.locator.PVT_totals()):
            tech_to_plot.extend(['PVT'])
        if os.path.exists(self.locator.SC_totals(panel_type = 'FP')):
            tech_to_plot.extend(['SC_FP'])
        if os.path.exists(self.locator.SC_totals(panel_type = 'ET')):
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

        tech_to_analyze = all_tech_analysis_fields.keys()

        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        # get data for all buildings
        annual_results_all_buildings_kW = []

        # get data of buildings
        for i, building in enumerate(buildings):
            if i == 0:
                input_data_dict_kW = {}
                # read data from the first building
                if 'PV' in all_tech_analysis_fields:
                    PV_input_data_aggregated_kW = pd.read_csv(self.locator.PV_results(building), usecols=all_tech_analysis_fields['PV'])
                    input_data_dict_kW['PV'] = pd.read_csv(self.locator.PV_results(building), usecols=all_tech_analysis_fields['PV'])
                if 'PVT' in all_tech_analysis_fields:
                    PVT_input_data_aggregated_kW = pd.read_csv(self.locator.PVT_results(building),
                                                               usecols=all_tech_analysis_fields['PVT'])
                    input_data_dict_kW['PVT'] = pd.read_csv(self.locator.PVT_results(building),
                                                            usecols=all_tech_analysis_fields['PVT'])
                if 'SC_FP' in all_tech_analysis_fields:
                    SC_FP_input_data_aggregated_kW = pd.read_csv(self.locator.SC_results(building, panel_type='FP'),
                                                                 usecols=SC_analysis_fields)
                    SC_FP_input_data_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_FP_walls_east_Q_kWh',
                                                                   'SC_walls_west_Q_kWh': 'SC_FP_walls_west_Q_kWh',
                                                                   'SC_walls_south_Q_kWh': 'SC_FP_walls_south_Q_kWh',
                                                                   'SC_walls_north_Q_kWh': 'SC_FP_walls_north_Q_kWh',
                                                                   'SC_roofs_top_Q_kWh': 'SC_FP_roofs_top_Q_kWh'},
                                                          inplace=True)
                    input_data_dict_kW['SC_FP'] = SC_FP_input_data_aggregated_kW

                if 'SC_ET' in all_tech_analysis_fields:
                    SC_ET_input_data_aggregated_kW = pd.read_csv(self.locator.SC_results(building, panel_type='ET'),
                                                                 usecols=SC_analysis_fields)
                    SC_ET_input_data_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_ET_walls_east_Q_kWh',
                                                                   'SC_walls_west_Q_kWh': 'SC_ET_walls_west_Q_kWh',
                                                                   'SC_walls_south_Q_kWh': 'SC_ET_walls_south_Q_kWh',
                                                                   'SC_walls_north_Q_kWh': 'SC_ET_walls_north_Q_kWh',
                                                                   'SC_roofs_top_Q_kWh': 'SC_ET_roofs_top_Q_kWh'},
                                                          inplace=True)
                    input_data_dict_kW['SC_ET'] = SC_ET_input_data_aggregated_kW

                annual_results_kW = pd.Series()
                for tech in input_data_dict_kW.keys():
                    annual_results_kW = annual_results_kW.append(input_data_dict_kW[tech].sum(axis=0))
                annual_results_all_buildings_kW = pd.DataFrame({building: annual_results_kW},
                                                          index=annual_results_kW.index).T
            else:
                # read data from each building
                if 'PV' in all_tech_analysis_fields:
                    PV_input_kW = pd.read_csv(self.locator.PV_results(building), usecols=all_tech_analysis_fields['PV'])
                    PV_input_data_aggregated_kW = PV_input_data_aggregated_kW + PV_input_kW
                if 'PVT' in all_tech_analysis_fields:
                    PVT_input_kW = pd.read_csv(self.locator.PVT_results(building), usecols=all_tech_analysis_fields['PVT'])
                    PVT_input_data_aggregated_kW = PVT_input_data_aggregated_kW + PVT_input_kW
                if 'SC_FP' in all_tech_analysis_fields:
                    SC_FP_input_kW = pd.read_csv(self.locator.SC_results(building, panel_type='FP'),
                                                 usecols=SC_analysis_fields)
                    SC_FP_input_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_FP_walls_east_Q_kWh',
                                                   'SC_walls_west_Q_kWh': 'SC_FP_walls_west_Q_kWh',
                                                   'SC_walls_south_Q_kWh': 'SC_FP_walls_south_Q_kWh',
                                                   'SC_walls_north_Q_kWh': 'SC_FP_walls_north_Q_kWh',
                                                   'SC_roofs_top_Q_kWh': 'SC_FP_roofs_top_Q_kWh'}, inplace=True)
                    SC_FP_input_data_aggregated_kW = SC_FP_input_data_aggregated_kW + SC_FP_input_kW
                if 'SC_ET' in all_tech_analysis_fields:
                    SC_ET_input_kW = pd.read_csv(self.locator.SC_results(building, panel_type='ET'),
                                                 usecols=SC_analysis_fields)
                    SC_ET_input_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_ET_walls_east_Q_kWh',
                                                   'SC_walls_west_Q_kWh': 'SC_ET_walls_west_Q_kWh',
                                                   'SC_walls_south_Q_kWh': 'SC_ET_walls_south_Q_kWh',
                                                   'SC_walls_north_Q_kWh': 'SC_ET_walls_north_Q_kWh',
                                                   'SC_roofs_top_Q_kWh': 'SC_ET_roofs_top_Q_kWh'}, inplace=True)
                    SC_ET_input_data_aggregated_kW = SC_ET_input_data_aggregated_kW + SC_ET_input_kW
                # aggregate data of all buildings

                annual_results_kW = pd.Series()
                for tech in all_tech_analysis_fields:
                    annual_results_kW = annual_results_kW.append(input_data_dict_kW[tech].sum(axis=0))
                df_annual_results_kW = pd.DataFrame({building: annual_results_kW}, index=annual_results_kW.index).T
                annual_results_all_buildings_kW = annual_results_all_buildings_kW.append(df_annual_results_kW)

        dfs = []
        dfs.append(PV_input_data_aggregated_kW) if 'PV' in all_tech_analysis_fields else dfs
        dfs.append(PVT_input_data_aggregated_kW) if 'PVT' in all_tech_analysis_fields else dfs
        dfs.append(SC_FP_input_data_aggregated_kW) if 'SC_FP' in all_tech_analysis_fields else dfs
        dfs.append(SC_ET_input_data_aggregated_kW) if 'SC_ET' in all_tech_analysis_fields else dfs

        def join_dfs(ldf, rdf):
            return ldf.join(rdf, how='inner')

        input_data_aggregated_kW = reduce(join_dfs, dfs)

        # input_data_aggregated_kW = PV_input_data_aggregated_kW.join(PVT_input_data_aggregated_kW).join(
        #     SC_FP_input_data_aggregated_kW).join(SC_ET_input_data_aggregated_kW)

        input_data_aggregated_kW['DATE'] = weather_data["date"]

        return {"data_hourly": input_data_aggregated_kW, "data_yearly": annual_results_all_buildings_kW}

    def pv_district_monthly(self):
        if 'PV' in self.all_tech_analysis_fields:
            pv_output_path = self.locator.get_timeseries_plots_file('District_photovoltaic_monthly')
            pv_title = "PV Electricity Potential for District"
            data = self.data_processed["data_hourly"].copy()
            plot = pv_district_monthly(data, self.pv_analysis_fields, pv_title, pv_output_path)
            print ('Photovoltaic panel results plotted')
        return

    def pvt_district_monthly(self):
        if 'PVT' in self.all_tech_analysis_fields:
            pvt_output_path = self.locator.get_timeseries_plots_file('District_photovoltaic_thermal_monthly')
            pvt_title = "PVT Electricity/Thermal Potential in District"
            data = self.data_processed["data_hourly"].copy()
            plot = pvt_district_monthly(data, self.pvt_analysis_fields, pvt_title, pvt_output_path)
            print ('Photovoltaic-thermal panel results plotted')
        return

    def sc_fp_district_monthly(self):
        if 'SC_FP' in self.all_tech_analysis_fields:
            sc_output_path = self.locator.get_timeseries_plots_file('District_FP_solar_collector_monthly')
            sc_title = "Flat Plate SC Thermal Potential in District"
            data = self.data_processed["data_hourly"].copy()
            plot = sc_district_monthly(data, self.sc_fp_analysis_fields, sc_title, sc_output_path)
            print ('Flat-plate Solar Collectors results plotted')
        return

    def sc_et_district_monthly(self):
        if 'SC_ET' in self.all_tech_analysis_fields:
            sc_output_path = self.locator.get_timeseries_plots_file('District_ET_solar_collector_monthly')
            sc_title = "Evacuated Tube SC Thermal Potential in District"
            data = self.data_processed["data_hourly"].copy()
            plot = sc_district_monthly(data, self.sc_et_analysis_fields, sc_title, sc_output_path)
            print ('Evacuated-tube Solar Collectors results plotted')
        return 


    def all_tech_district_yearly(self):
        all_tech_output_path = self.locator.get_timeseries_plots_file('District_solar_tech_yearly')
        all_tech_title = "PV/SC/PVT Potential in District"
        data = self.data_processed["data_yearly"].copy()
        all_tech_district_yearly(data, self.pv_analysis_fields, self.pvt_analysis_fields, self.sc_fp_analysis_fields,
                                 self.sc_et_analysis_fields, all_tech_title, all_tech_output_path)

    def all_tech_district_hourly(self):
        all_tech_output_path = self.locator.get_timeseries_plots_file('District_solar_tech_hourly')
        all_tech_title = "PV/SC/PVT Potential in District"
        data = self.data_processed["data_hourly"].copy()
        all_tech_district_hourly(data, self.all_tech_analysis_fields, all_tech_title, all_tech_output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plot_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
