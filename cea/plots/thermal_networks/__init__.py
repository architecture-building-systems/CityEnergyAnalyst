from __future__ import division
from __future__ import print_function

import os
import numpy as np
import pandas as pd
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR

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
        'network-type': 'plots:network-type',
        'network-name': 'plots:network-name',
    }

    def __init__(self, project, parameters, cache):
        super(ThermalNetworksPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', self.category_name)
        self.network_name = parameters['network-name'] if parameters['network-name'] else ''
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
    def hourly_relative_pressure_loss(self):
        relative_loss = self._calculate_relative_loss(self.hourly_pressure_loss)
        return pd.DataFrame(np.round(relative_loss, 2))

    @property
    def mean_pressure_loss_relative(self):
        relative_loss = self._calculate_relative_loss(self.hourly_pressure_loss)
        mean_loss = np.nanmean(relative_loss)  # calculate average loss of nonzero values
        mean_loss = np.round(mean_loss, 2)
        return mean_loss

    @property
    def hourly_relative_heat_loss(self):
        relative_loss = self._calculate_relative_loss(self.hourly_heat_loss)
        return pd.DataFrame(np.round(relative_loss, 2))

    @property
    def mean_heat_loss_relative(self):
        relative_loss = self._calculate_relative_loss(self.hourly_heat_loss)
        mean_loss = np.nanmean(relative_loss)  # calculate average loss of nonzero values
        mean_loss = np.round(mean_loss, 2)
        return mean_loss

    def _calculate_relative_loss(self, absolute_loss):
        """
                Calculate relative heat or pressure loss:
                1. Sum up all plant heat produced in each time step
                2. Divide absolute losses by that value
                """
        # read plant heat supply
        plant_heat_supply = pd.read_csv(self.locator.get_thermal_network_plant_heat_requirement_file(self.network_type,
                                                                                                     self.network_name))
        plant_heat_supply = abs(plant_heat_supply)  # make sure values are positive
        if len(plant_heat_supply.columns.values) > 1:  # sum of all plants
            plant_heat_supply = plant_heat_supply.sum(axis=1)
        plant_heat_supply[plant_heat_supply == 0] = np.nan
        # necessary to avoid errors from shape mismatch
        plant_heat_supply = np.reshape(plant_heat_supply.values, (HOURS_IN_YEAR, 1))
        relative_loss = absolute_loss.values / plant_heat_supply * 100  # calculate relative value in %
        relative_loss = np.nan_to_num(relative_loss)  # remove nan or inf values to avoid runtime error
        # if relative losses are more than 100% temperature requirements are not met. All produced heat is lost.
        relative_loss[relative_loss > 100] = 100
        # don't show 0 values
        relative_loss[relative_loss == 0] = np.nan
        return relative_loss

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
