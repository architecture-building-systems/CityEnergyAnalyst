from __future__ import division
from __future__ import print_function

import os
import pandas as pd
import cea.inputlocator

"""
Implements py:class:`cea.plots.ThermalNetworksPlotBase` as a base class for all plots in the category 
"thermal-networks" and also set's the label for that category.
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
label = 'Thermal networks'


class ThermalNetworksPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "thermal-networks"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'scenario-name': 'general:scenario-name',
        'network-type': 'thermal-network:network-type',
        'network-names': 'thermal-network:network-names',
    }

    def __init__(self, project, parameters, cache):
        super(ThermalNetworksPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', self.category_name)
        self.network_name = parameters['network-names'][0] if parameters['network-names'] else ''  # FIXME: why is this plural?!
        self.network_type = parameters['network-type']

    @property
    def title(self):
        """Override the version in PlotBase"""
        if not self.network_name:  # different plot titles if a network name is specified, here without network name
            return '{name} for {network_type}'.format(name=self.name, network_type=self.network_type)
        else:
            # plot title including network name
            return '{name} for {network_type} in {network_name}'.format(name=self.name, network_type=self.network_type,
                                                                        network_name = self.network_name)

    @property
    def output_path(self):
        file_name = '{network_type}_{network_name}_{name}'.format(network_type=self.network_type,
                                                                     network_name=self.network_name, name=self.id())
        return self.locator.get_timeseries_plots_file(file_name, self.category_path)

    @property
    def buildings_hourly(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'buildings_hourly'),
                                 plot=self, producer=self._calculate_buildings_hourly)

    def _calculate_buildings_hourly(self):
        thermal_demand_df = pd.read_csv(self.locator.get_thermal_demand_csv_file(self.network_type, self.network_name),
                                        index_col=0)
        thermal_demand_df.set_index(self.date)
        thermal_demand_df = thermal_demand_df / 1000
        return thermal_demand_df

    @property
    def hourly_loads(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'hourly_loads'),
                                 plot=self, producer=self._calculate_hourly_loads)

    def _calculate_hourly_loads(self):
        hourly_loads = pd.DataFrame(self.buildings_hourly.sum(axis=1))
        if self.network_type == 'DH':
            hourly_loads.columns = ['Q_dem_heat']
        else:
            hourly_loads.columns = ['Q_dem_cool']
        return hourly_loads

    @property
    def date(self):
        """A pandas.Series of datetime values to be used as an index into the hourly data"""
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'date'),
                                 plot=self, producer=self._read_date_column_from_demand_results)

    def _read_date_column_from_demand_results(self):
        """Read in the date information from demand results of the first building in the zone"""
        buildings = self.locator.get_zone_building_names()
        df_date = pd.read_csv(self.locator.get_demand_results_file(buildings[0]))
        return df_date["DATE"]

    @property
    def hourly_pressure_loss(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'hourly_pressure_loss'),
                                 plot=self, producer=self._calculate_hourly_pressure_loss)

    def _calculate_hourly_pressure_loss(self):
        hourly_pressure_loss = pd.read_csv(
            self.locator.get_thermal_network_layout_pressure_drop_kw_file(self.network_type, self.network_name))
        hourly_pressure_loss = hourly_pressure_loss['pressure_loss_total_kW']
        return pd.DataFrame(hourly_pressure_loss)

    @property
    def yearly_pressure_loss(self):
        return self.hourly_pressure_loss.values.sum()

    @property
    def hourly_heat_loss(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'hourly_heat_loss'),
                                 plot=self, producer=self._calculate_hourly_heat_loss)

    def _calculate_hourly_heat_loss(self):
        hourly_heat_loss = pd.read_csv(self.locator.get_thermal_network_qloss_system_file(self.network_type, self.network_name))
        hourly_heat_loss = abs(hourly_heat_loss).sum(axis=1)  # aggregate heat losses of all edges
        return pd.DataFrame(hourly_heat_loss)

    @property
    def yearly_heat_loss(self):
        return abs(self.hourly_heat_loss.values).sum()
