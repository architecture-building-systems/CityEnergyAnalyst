



import functools
import os

import pandas as pd

import cea.inputlocator
from cea.plots.base import PlotBase
from cea.utilities import epwreader

"""
Implements py:class:`cea.plots.SolarTechnologyPotentialsPlotBase` as a base class for all plots in the category 
"solar-technology-potentials" and also set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Technology potentials'


class SolarTechnologyPotentialsPlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "technology-potentials"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SolarTechnologyPotentialsPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('special', self.category_name)
        self.weather = self.locator.get_weather_file()
        self.pv_analysis_fields = ['PV_walls_east_E_kWh',
                                   'PV_walls_west_E_kWh',
                                   'PV_walls_south_E_kWh',
                                   'PV_walls_north_E_kWh',
                                   'PV_roofs_top_E_kWh']
        self.pv_analysis_fields_area = ['PV_walls_east_m2',
                                        'PV_walls_west_m2',
                                        'PV_walls_south_m2',
                                        'PV_walls_north_m2',
                                        'PV_roofs_top_m2']
        self.sc_et_analysis_fields = ['SC_ET_walls_east_Q_kWh',
                                      'SC_ET_walls_west_Q_kWh',
                                      'SC_ET_walls_south_Q_kWh',
                                      'SC_ET_walls_north_Q_kWh',
                                      'SC_ET_roofs_top_Q_kWh']
        self.sc_et_analysis_fields_area = ['SC_ET_walls_east_m2',
                                           'SC_ET_walls_west_m2',
                                           'SC_ET_walls_south_m2',
                                           'SC_ET_walls_north_m2',
                                           'SC_ET_roofs_top_m2']
        self.sc_fp_analysis_fields = ['SC_FP_walls_east_Q_kWh',
                                      'SC_FP_walls_west_Q_kWh',
                                      'SC_FP_walls_south_Q_kWh',
                                      'SC_FP_walls_north_Q_kWh',
                                      'SC_FP_roofs_top_Q_kWh']
        self.sc_fp_analysis_fields_area = ['SC_FP_walls_east_m2',
                                           'SC_FP_walls_west_m2',
                                           'SC_FP_walls_south_m2',
                                           'SC_FP_walls_north_m2',
                                           'SC_FP_roofs_top_m2']

        self.pvt_analysis_fields = ['PVT_walls_east_E_kWh', 'PVT_walls_west_E_kWh', 'PVT_walls_south_E_kWh',
                                    'PVT_walls_north_E_kWh',
                                    'PVT_roofs_top_E_kWh', 'PVT_walls_east_Q_kWh', 'PVT_walls_west_Q_kWh',
                                    'PVT_walls_south_Q_kWh', 'PVT_walls_north_Q_kWh',
                                    'PVT_roofs_top_Q_kWh']

    def normalize_data(self, data_processed, buildings, analysis_fields, analysis_fields_area):
        if self.normalization == "surface area":
            for energy, area in zip(analysis_fields, analysis_fields_area):
                if data_processed[area][0] > 0.0:
                    data_processed[energy] = data_processed[energy] / data_processed[area]
            return data_processed

        data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')

        if self.normalization == "gross floor area":
            normalizatioon_factor = data.loc[buildings]['GFA_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "net floor area":
            normalizatioon_factor = data.loc[buildings]['Aocc_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "air conditioned floor area":
            normalizatioon_factor = data.loc[buildings]['Af_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "building occupancy":
            normalizatioon_factor = data.loc[buildings]['people0'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        return data_processed

    def add_pv_fields(self, df1, df2):
        """Add the demand analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        fields = self.pv_analysis_fields + self.pv_analysis_fields_area
        df1[fields] = df2[fields] + df1[fields]
        return df1

    # FOR SOLAR COLLECTORS
    def SC_ET_hourly_aggregated_kW(self):
        data = self._calculate_SC_ET_hourly_aggregated_kW()
        data_normalized = self.normalize_data(data,
                                              self.buildings,
                                              self.sc_et_analysis_fields,
                                              self.sc_et_analysis_fields_area)
        SC_et_hourly_aggregated_kW = self.resample_time_data(data_normalized)

        return SC_et_hourly_aggregated_kW

    def add_sc_et_fields(self, df1, df2):
        """Add the demand analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        fields = self.sc_et_analysis_fields + self.sc_et_analysis_fields_area
        df1[fields] = df2[fields] + df1[fields]
        return df1

    @cea.plots.cache.cached
    def _calculate_SC_ET_hourly_aggregated_kW(self):
        sc_et_hourly_aggregated_kW = functools.reduce(self.add_sc_et_fields,
                                                      (pd.read_csv(self.locator.SC_results(building, panel_type='ET'))
                                                       for building in self.buildings)).set_index('Date')
        return sc_et_hourly_aggregated_kW

    @property
    def PVT_hourly_aggregated_kW(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'PVT_hourly_aggregated_kW'),
                                 plot=self, producer=self._calculate_PVT_hourly_aggregated_kW)

    def _calculate_PVT_hourly_aggregated_kW(self):
        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        pvt_hourly_aggregated_kW = sum(pd.read_csv(self.locator.PVT_results(building), usecols=self.pvt_analysis_fields)
                                       for building in self.buildings)
        pvt_hourly_aggregated_kW['DATE'] = weather_data["date"]
        return pvt_hourly_aggregated_kW

    @property
    def SC_FP_hourly_aggregated_kW(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'SC_FP_hourly_aggregated_kW'),
                                 plot=self, producer=self._calculate_SC_FP_hourly_aggregated_kW)

    def _calculate_SC_FP_hourly_aggregated_kW(self):
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]
        sc_fp_hourly_aggregated_kW = sum(
            pd.read_csv(self.locator.SC_results(building, panel_type='FP'), usecols=self.sc_analysis_fields) for
            building in self.buildings)
        sc_fp_hourly_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_FP_walls_east_Q_kWh',
                                                   'SC_walls_west_Q_kWh': 'SC_FP_walls_west_Q_kWh',
                                                   'SC_walls_south_Q_kWh': 'SC_FP_walls_south_Q_kWh',
                                                   'SC_walls_north_Q_kWh': 'SC_FP_walls_north_Q_kWh',
                                                   'SC_roofs_top_Q_kWh': 'SC_FP_roofs_top_Q_kWh'},
                                          inplace=True)
        sc_fp_hourly_aggregated_kW['DATE'] = weather_data["date"]
        return sc_fp_hourly_aggregated_kW
