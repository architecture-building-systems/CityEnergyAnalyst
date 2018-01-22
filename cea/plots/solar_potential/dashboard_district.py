"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
from cea.plots.solar_potential.solar_radiation_curve import solar_radiation_curve
from cea.plots.solar_potential.solar_radiation import solar_radiation_district
from cea.plots.solar_potential.solar_radiation_monthly import solar_radiation_district_monthly
from cea.utilities import epwreader
import pandas as pd
import numpy as np

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def data_processing(analysis_fields, buildings, locator, weather):

    # get extra data of weather and date
    weather_data = epwreader.epw_reader(weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

    # get data of buildings
    input_data_not_aggregated_MW = []
    for i, building in enumerate(buildings):
        df_not_aggregated = {}
        geometry = pd.read_csv(locator.get_radiation_metadata(building))
        geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation']
        insolation = pd.read_json(locator.get_radiation_building(building))
        if i == 0:
            df = {}
            for field in analysis_fields:
                select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                df_not_aggregated[field] = np.array([select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in select_sensors.index]).sum(
                    axis=0)  # W
                df[field] = np.array([select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in select_sensors.index]).sum(axis=0)# W

            # add date and resample into months
            df_not_aggregated = pd.DataFrame(df_not_aggregated)
            resample_data_frame = (df_not_aggregated.sum(axis=0) / 1000000).round(2)  # into MWh
            input_data_not_aggregated_MW = pd.DataFrame({building: resample_data_frame}, index=resample_data_frame.index).T

        else:
            for field in analysis_fields:
                select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                df[field] = df[field] + np.array([select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in select_sensors.index]).sum(axis=0)# W
                df_not_aggregated[field] = np.array([select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in select_sensors.index]).sum(
                    axis=0)  # W

            # add date and resample into months
            df_not_aggregated = pd.DataFrame(df_not_aggregated)
            resample_data_frame = (df_not_aggregated.sum(axis=0) / 1000000).round(2)  # into MWh
            intermediate_dataframe = pd.DataFrame({building: resample_data_frame}, index=resample_data_frame.index).T
            input_data_not_aggregated_MW = input_data_not_aggregated_MW.append(intermediate_dataframe)


    # round and add weather vars and date
    input_data_aggregated_kW = (pd.DataFrame(df) / 1000).round(2) # in kW
    input_data_aggregated_kW["T_out_dry_C"] = weather_data["drybulb_C"].values
    input_data_aggregated_kW["DATE"] = weather_data["date"]

    return input_data_aggregated_kW, input_data_not_aggregated_MW

def dashboard(locator, config):

    # Local Variables
    # GET LOCAL VARIABLES
    weather = config.weather
    buildings = config.dashboard.buildings

    if buildings == []:
        buildings = pd.read_csv(locator.get_total_demand()).Name.values

    #CREATE RADIATION CURVE
    output_path = locator.get_timeseries_plots_file("District" + '_solar_radiation_curve')
    title = "Solar Radiation Curve for District"
    analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                       'walls_east','walls_west','walls_south','walls_north','roofs_top']
    input_data_aggregated_kW, input_data_not_aggregated_MW = data_processing(analysis_fields, buildings, locator, weather)
    solar_radiation_curve(input_data_aggregated_kW, analysis_fields+["T_out_dry_C"], title, output_path)

    #CREATE RADIATION CURVE_MONTHLY
    output_path = locator.get_timeseries_plots_file("District" + '_solar_radiation_monthly')
    title = "Solar Radiation for District"
    analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                       'walls_east','walls_west','walls_south','walls_north','roofs_top']
    solar_radiation_district_monthly(input_data_aggregated_kW, analysis_fields, title, output_path)

    #CREATE RADIATION BUILDINGS
    output_path = locator.get_timeseries_plots_file("District" + '_solar_radiation')
    title = "Solar Radiation for District"
    analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                       'walls_east','walls_west','walls_south','walls_north','roofs_top']
    solar_radiation_district(input_data_not_aggregated_MW, analysis_fields, title, output_path)




def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
