from __future__ import division
from __future__ import print_function

import pandas as pd
import os
import cea.inputlocator
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
label = 'Solar technology potentials'


class SolarTechnologyPotentialsPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "solar-technology-potentials"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SolarTechnologyPotentialsPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', self.category_name)
        self.weather = self.locator.get_weather_file()
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

    @property
    def PV_hourly_aggregated_kW(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'PV_hourly_aggregated_kW'),
                                 plot=self, producer=self._calculate_PV_hourly_aggregated_kW)

    def _calculate_PV_hourly_aggregated_kW(self):
        # get extra data of weather and date
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]

        pv_hourly_aggregated_kW = sum(pd.read_csv(self.locator.PV_results(building), usecols=self.pv_analysis_fields)
                                      for building in self.buildings)
        pv_hourly_aggregated_kW['DATE'] = weather_data["date"]
        return pv_hourly_aggregated_kW

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

    @property
    def SC_ET_hourly_aggregated_kW(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'SC_ET_hourly_aggregated_kW'),
                                 plot=self, producer=self._calculate_SC_ET_hourly_aggregated_kW)

    def _calculate_SC_ET_hourly_aggregated_kW(self):
        weather_data = epwreader.epw_reader(self.weather)[["date", "drybulb_C", "wetbulb_C", "skytemp_C"]]
        sc_et_hourly_aggregated_kW = sum(
            pd.read_csv(self.locator.SC_results(building, panel_type='FP'), usecols=self.sc_analysis_fields) for
            building in self.buildings)
        sc_et_hourly_aggregated_kW.rename(columns={'SC_walls_east_Q_kWh': 'SC_ET_walls_east_Q_kWh',
                                                   'SC_walls_west_Q_kWh': 'SC_ET_walls_west_Q_kWh',
                                                   'SC_walls_south_Q_kWh': 'SC_ET_walls_south_Q_kWh',
                                                   'SC_walls_north_Q_kWh': 'SC_ET_walls_north_Q_kWh',
                                                   'SC_roofs_top_Q_kWh': 'SC_ET_roofs_top_Q_kWh'},
                                          inplace=True)
        sc_et_hourly_aggregated_kW['DATE'] = weather_data["date"]
        return sc_et_hourly_aggregated_kW

