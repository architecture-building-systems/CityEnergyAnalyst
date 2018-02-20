"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import pandas as pd

import cea.config
import cea.inputlocator
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


def plot_main(locator, config):
    # local variables
    buildings = config.dashboard.buildings
    weather = config.weather

    # initialize class
    plots = Plots(locator, buildings, weather)

    # create plots
    if len(buildings) == 1:  # when only one building is passed.
        x = 1  # do nothing for now! to be improved!
    else:  # when two or more buildings are passed
        plots.pv_district_monthly()
        plots.pvt_district_monthly()
        plots.sc_district_monthly()
        plots.all_tech_district_yearly()


class Plots():

    def __init__(self, locator, buildings, weather):
        self.weather = weather
        self.locator = locator
        self.buildings = self.preprocess_buildings(buildings)
        self.pv_analysis_fields = ['PV_walls_east_E_kWh', 'PV_walls_west_E_kWh', 'PV_walls_south_E_kWh',
                                   'PV_walls_north_E_kWh',
                                   'PV_roofs_top_E_kWh']
        self.sc_analysis_fields = ['SC_walls_east_Q_kWh', 'SC_walls_west_Q_kWh', 'SC_walls_south_Q_kWh',
                                   'SC_walls_north_Q_kWh',
                                   'SC_roofs_top_Q_kWh']
        self.pvt_analysis_fields = ['PVT_walls_east_E_kWh', 'PVT_walls_west_E_kWh', 'PVT_walls_south_E_kWh',
                                    'PVT_walls_north_E_kWh',
                                    'PVT_roofs_top_E_kWh', 'PVT_walls_east_Q_kWh', 'PVT_walls_west_Q_kWh',
                                    'PVT_walls_south_Q_kWh', 'PVT_walls_north_Q_kWh',
                                    'PVT_roofs_top_Q_kWh']
        self.data_processed = self.preprocessing_data(self.pv_analysis_fields, self.pvt_analysis_fields,
                                                      self.sc_analysis_fields, self.buildings)

    def preprocess_buildings(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return self.locator.get_zone_building_names()
        else:
            return buildings

    def preprocessing_data(self, PV_analysis_fields, PVT_analysis_fields, SC_analysis_fields, buildings):
        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        # get data for all buildings
        input_data_per_building_kW = []

        # get data of buildings
        for i, building in enumerate(buildings):
            if i == 0:
                # read data from the first building
                PV_input_data_aggregated_kW = pd.read_csv(self.locator.PV_results(building), usecols=PV_analysis_fields)
                PVT_input_data_aggregated_kW = pd.read_csv(self.locator.PVT_results(building),
                                                           usecols=PVT_analysis_fields)
                SC_input_data_aggregated_kW = pd.read_csv(self.locator.SC_results(building), usecols=SC_analysis_fields)

                # combine annual resutls of all technologies for the first building
                annual_results_kW = PV_input_data_aggregated_kW.sum(axis=0).append(
                    PVT_input_data_aggregated_kW.sum(axis=0)).append(SC_input_data_aggregated_kW.sum(axis=0))
                input_data_per_building_kW = pd.DataFrame({building: annual_results_kW},
                                                          index=annual_results_kW.index).T
            else:
                # read data from each building
                PV_input_kW = pd.read_csv(self.locator.PV_results(building), usecols=PV_analysis_fields)
                PVT_input_kW = pd.read_csv(self.locator.PVT_results(building), usecols=PVT_analysis_fields)
                SC_input_kW = pd.read_csv(self.locator.SC_results(building), usecols=SC_analysis_fields)

                # aggregate data of all buildings
                PV_input_data_aggregated_kW = PV_input_data_aggregated_kW + PV_input_kW
                PVT_input_data_aggregated_kW = PVT_input_data_aggregated_kW + PVT_input_kW
                SC_input_data_aggregated_kW = SC_input_data_aggregated_kW + SC_input_kW

                # combine annual resutls of all technologies for each building
                annual_results_kW = PV_input_kW.sum(axis=0).append(PVT_input_kW.sum(axis=0)).append(
                    SC_input_kW.sum(axis=0))
                df_annual_results_kW = pd.DataFrame({building: annual_results_kW}, index=annual_results_kW.index).T
                input_data_per_building_kW = input_data_per_building_kW.append(df_annual_results_kW)

        input_data_aggregated_kW = PV_input_data_aggregated_kW.join(PVT_input_data_aggregated_kW).join(
            SC_input_data_aggregated_kW)
        input_data_aggregated_kW['DATE'] = weather_data["date"]

        return {"data_hourly": input_data_aggregated_kW, "data_yearly": input_data_per_building_kW}

    def pv_district_monthly(self):
        pv_output_path = self.locator.get_timeseries_plots_file("District" + '_photovoltaic_monthly')
        pv_title = "PV Electricity Potential for District"
        data = self.data_processed["data_hourly"]
        plot = pv_district_monthly(data, self.pv_analysis_fields, pv_title, pv_output_path)
        return plot

    def pvt_district_monthly(self):
        pvt_output_path = self.locator.get_timeseries_plots_file("District" + '_photovoltaic_thermal_monthly')
        pvt_title = "PVT Electricity/Thermal Potential for District"
        data = self.data_processed["data_hourly"]
        plot = pvt_district_monthly(data, self.pvt_analysis_fields, pvt_title, pvt_output_path)
        return plot

    def sc_district_monthly(self):
        sc_output_path = self.locator.get_timeseries_plots_file("District" + '_solar_collector_monthly')
        sc_title = "SC Thermal Potential for District"
        data = self.data_processed["data_hourly"]
        plot = sc_district_monthly(data, self.sc_analysis_fields, sc_title, sc_output_path)
        return plot

    def all_tech_district_yearly(self):
        all_tech_output_path = self.locator.get_timeseries_plots_file("District" + '_solar_tech_yearly')
        all_tech_title = "PV/SC/PVT Electricity/Thermal Potential for District"
        data = self.data_processed["data_yearly"]
        all_tech_district_yearly(data, self.pv_analysis_fields, self.pvt_analysis_fields, self.sc_analysis_fields,
                                 all_tech_title, all_tech_output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plot_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
