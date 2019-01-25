"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import time

import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.solar_potential.solar_radiation import solar_radiation_district
from cea.plots.solar_potential.solar_radiation_curve import solar_radiation_curve
from cea.plots.solar_potential.solar_radiation_monthly import solar_radiation_district_monthly
from cea.utilities import epwreader

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

    # Local Variables
    buildings = config.plots.buildings
    weather = config.weather

    # initialize class
    plots = Plots(locator, buildings, weather)
    category = "basic//solar-potential"

    if len(buildings) == 1:  # when only one building is passed.
        plots.solar_radiation_curve(category)
        plots.solar_radiation_district_monthly(category)
        plots.solar_radiation_per_building(category)

    else:  # when two or more buildings are passed
        # generate plots
        plots.solar_radiation_curve(category)
        plots.solar_radiation_district_monthly(category)
        plots.solar_radiation_per_building(category)

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots(object):

    def __init__(self, locator, buildings, weather):
        # local variables
        self.locator = locator
        self.weather = weather
        self.analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                                'walls_east', 'walls_west', 'walls_south', 'walls_north', 'roofs_top']
        self.buildings = self.preprocess_buildings(buildings)
        self.data_processed_district = self.preprocessing(self.analysis_fields, self.buildings, self.locator,
                                                          self.weather)
        self.plot_title_tail = self.preprocess_plot_title(buildings)
        self.plot_output_path_header = self.preprocess_plot_outputpath(buildings)

    def preprocess_buildings(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return self.locator.get_zone_building_names()
        else:
            return buildings

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

    def preprocessing(self, analysis_fields, buildings, locator, weather):

        # get extra data of weather and date
        weather_data = epwreader.epw_reader(weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        # get data of buildings
        input_data_not_aggregated_MW = []
        dict_not_aggregated = {}
        for i, building in enumerate(buildings):
            geometry = pd.read_csv(locator.get_radiation_metadata(building))
            geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation']
            insolation = pd.read_json(locator.get_radiation_building(building))
            if i == 0:
                for field in analysis_fields:
                    select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                    array_field = np.array(
                        [select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in
                         select_sensors.index]).sum(axis=0)  #
                    dict_not_aggregated[field] = array_field

                # add date and resample into months
                df_not_aggregated = pd.DataFrame(dict_not_aggregated)
                resample_data_frame = (df_not_aggregated.sum(axis=0) / 1000000).round(2)  # into MWh
                input_data_not_aggregated_MW = pd.DataFrame({building: resample_data_frame},
                                                            index=resample_data_frame.index).T

            else:
                dict_not_aggregated_2 = {}
                for field in analysis_fields:
                    select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                    array_field = np.array(
                        [select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in
                         select_sensors.index]).sum(axis=0)
                    dict_not_aggregated_2[field] = array_field  # W
                    dict_not_aggregated[field] = dict_not_aggregated[field] + array_field

                    # add date and resample into months
                df_not_aggregated = pd.DataFrame(dict_not_aggregated_2)
                resample_data_frame = (df_not_aggregated.sum(axis=0) / 1000000).round(2)  # into MWh
                intermediate_dataframe = pd.DataFrame({building: resample_data_frame},
                                                      index=resample_data_frame.index).T
                input_data_not_aggregated_MW = input_data_not_aggregated_MW.append(intermediate_dataframe)

        # round and add weather vars and date
        input_data_aggregated_kW = (pd.DataFrame(dict_not_aggregated) / 1000).round(2)  # in kW
        input_data_aggregated_kW["T_ext_C"] = weather_data["drybulb_C"].values
        input_data_aggregated_kW["DATE"] = weather_data["date"]
        input_data_not_aggregated_MW["Name"] = input_data_not_aggregated_MW.index.values

        return {'input_data_aggregated_kW': input_data_aggregated_kW,
                "input_data_not_aggregated_MW": input_data_not_aggregated_MW}

    def solar_radiation_curve(self, category):
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_solar_radiation_curve',
                                                             category)
        title = "Solar radiation curve" + self.plot_title_tail
        data = self.data_processed_district['input_data_aggregated_kW'].copy()
        plot = solar_radiation_curve(data, self.analysis_fields + ["T_ext_C"], title, output_path)

        return plot

    def solar_radiation_district_monthly(self, category):
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_solar_radiation_monthly',
                                                             category)
        title = "Solar radiation per month" + self.plot_title_tail
        data = self.data_processed_district['input_data_aggregated_kW'].copy()
        plot = solar_radiation_district_monthly(data, self.analysis_fields, title, output_path)

        return plot

    def solar_radiation_per_building(self, category):
        output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + '_solar_radiation_per_building', category)
        title = "Solar radiation per building" + self.plot_title_tail
        data = self.data_processed_district['input_data_not_aggregated_MW']
        plot = solar_radiation_district(data, self.analysis_fields, title, output_path)

        return plot


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running plots with scenario = %s" % config.scenario)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
