from __future__ import division
from __future__ import print_function

import pandas as pd
import numpy as np
import os
import cea.inputlocator
from cea.utilities import epwreader

"""
Implements py:class:`cea.plots.SolarPotentialPlotBase` as a base class for all plots in the category "solar-potential"
and also set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Solar Potentials'


class SolarPotentialPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "solar-potential"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SolarPotentialPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', 'solar-potential')
        self.weather = self.locator.get_weather_file()
        self.analysis_fields = ['windows_east', 'windows_west', 'windows_south', 'windows_north',
                                'walls_east', 'walls_west', 'walls_south', 'walls_north', 'roofs_top']

        # make sure we have radiation output for all the buildings
        self.input_files = [(self.locator.get_radiation_metadata, [building_name]) for building_name in
                            self.buildings] + [(self.locator.get_radiation_building, [building_name]) for building_name
                                               in self.buildings]

    @property
    def input_data_aggregated_kW(self):
        """
        Returns the preprocessed data used for the solar-potential plots. Uses the PlotCache
        to speed up ``self._calculate_input_data_aggregated_kW()``
        """
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'input_data_aggregated_kW'),
                                 plot=self, producer=self._calculate_input_data_aggregated_kW)

    @property
    def input_data_not_aggregated_MW(self):
        """
        Returns the preprocessed data used for the solar-potential plots. Uses the PlotCache
        to speed up ``self._calculate_input_data_aggregated_kW()``
        """
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'input_data_not_aggregated_MW'),
                                 plot=self, producer=self._calculate_input_data_not_aggregated_MW)

    def _calculate_input_data_aggregated_kW(self):
        """This is the data all the solar-potential plots are based on."""
        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        # get data of buildings
        dict_not_aggregated = {}
        for i, building in enumerate(self.buildings):
            geometry = pd.read_csv(self.locator.get_radiation_metadata(building))
            geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation']
            insolation = pd.read_json(self.locator.get_radiation_building(building))
            if i == 0:
                for field in self.analysis_fields:
                    select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                    array_field = np.array(
                        [select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in
                         select_sensors.index]).sum(axis=0)  #
                    dict_not_aggregated[field] = array_field
            else:
                dict_not_aggregated_2 = {}
                for field in self.analysis_fields:
                    select_sensors = geometry.loc[geometry['code'] == field].set_index('SURFACE')
                    array_field = np.array(
                        [select_sensors.ix[surface, 'AREA_m2'] * insolation[surface] for surface in
                         select_sensors.index]).sum(axis=0)
                    dict_not_aggregated_2[field] = array_field  # W
                    dict_not_aggregated[field] = dict_not_aggregated[field] + array_field

        # round and add weather vars and date
        input_data_aggregated_kW = (pd.DataFrame(dict_not_aggregated) / 1000).round(2)  # in kW
        input_data_aggregated_kW["T_ext_C"] = weather_data["drybulb_C"].values
        input_data_aggregated_kW["DATE"] = weather_data["date"]

        return input_data_aggregated_kW

    def _calculate_input_data_not_aggregated_MW(self):
        """This is the data all the solar-potential plots are based on."""
        # get data of buildings
        input_data_not_aggregated_MW = []
        dict_not_aggregated = {}
        for i, building in enumerate(self.buildings):
            geometry = pd.read_csv(self.locator.get_radiation_metadata(building))
            geometry['code'] = geometry['TYPE'] + '_' + geometry['orientation']
            insolation = pd.read_json(self.locator.get_radiation_building(building))
            if i == 0:
                for field in self.analysis_fields:
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
                for field in self.analysis_fields:
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
        input_data_not_aggregated_MW["Name"] = input_data_not_aggregated_MW.index.values
        return input_data_not_aggregated_MW
