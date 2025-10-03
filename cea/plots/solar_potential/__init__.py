import functools
import os

import pandas as pd

from cea.plots.base import PlotBase

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


class SolarPotentialPlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "solar-potential"

    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
        'normalization': 'plots:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(SolarPotentialPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('special', 'solar-potential')
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_radiation_metadata, [building]) for building in self.buildings] + \
                           [(self.locator.get_radiation_building_sensors, [building]) for building in self.buildings]
        self.weather = self.locator.get_weather_file()
        self.solar_analysis_fields = ['windows_east_kW',
                                      'windows_west_kW',
                                      'windows_south_kW',
                                      'windows_north_kW',
                                      'walls_east_kW',
                                      'walls_west_kW',
                                      'walls_south_kW',
                                      'walls_north_kW',
                                      'roofs_top_kW']
        self.solar_analysis_fields_area = ['windows_east_m2',
                                           'windows_west_m2',
                                           'windows_south_m2',
                                           'windows_north_m2',
                                           'walls_east_m2',
                                           'walls_west_m2',
                                           'walls_south_m2',
                                           'walls_north_m2',
                                           'roofs_top_m2']

    def normalize_data(self, data_processed, buildings, analysis_fields, analysis_fields_area):
        if self.normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('name')
            normalizatioon_factor = data.loc[buildings]['GFA_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('name')
            normalizatioon_factor = data.loc[buildings]['Aocc_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('name')
            normalizatioon_factor = data.loc[buildings]['Af_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('name')
            normalizatioon_factor = data.loc[buildings]['people0'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "surface area":
            for energy, area in zip(analysis_fields, analysis_fields_area):
                if data_processed[area][0] > 0.0:
                    data_processed[energy] = data_processed[energy] / data_processed[area]
        return data_processed

    def add_solar_fields(self, df1, df2):
        """Add the demand analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        fields = self.solar_analysis_fields + self.solar_analysis_fields_area
        df1[fields] = df2[fields] + df1[fields]
        return df1

    def solar_hourly_aggregated_kW(self):
        data = self._calculate_input_data_aggregated_kW()
        data_normalized = self.normalize_data(data,
                                              self.buildings,
                                              self.solar_analysis_fields,
                                              self.solar_analysis_fields_area)
        solar_hourly_aggregated_kW = self.resample_time_data(data_normalized)

        return solar_hourly_aggregated_kW

    def _calculate_input_data_aggregated_kW(self):
        """This is the data all the solar-potential plots are based on."""
        # get extra data of weather and date
        input_data_aggregated_kW = functools.reduce(self.add_solar_fields,
                                                    (pd.read_csv(self.locator.get_radiation_building(building), parse_dates=["Date"])
                                                     for building in self.buildings)).set_index('Date')

        # Fix for TMY weather
        if len(input_data_aggregated_kW.index.year.unique() > 1):
            year = input_data_aggregated_kW.index[0].year
            input_data_aggregated_kW.index = input_data_aggregated_kW.index.map(lambda dt: dt.replace(year=year))

        return input_data_aggregated_kW
