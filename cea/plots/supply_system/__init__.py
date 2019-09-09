from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.plots

"""
Implements py:class:`cea.plots.SupplySystemPlotBase` as a base class for all plots in the category "supply-system" and also
set's the label for that category.
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
label = 'Supply System'


class SupplySystemPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "supply-system"

    expected_parameters = {
        'generation': 'plots-supply-system:generation',
        'individual': 'plots-supply-system:individual',
        'timeframe': 'plots-supply-system:timeframe',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SupplySystemPlotBase, self).__init__(project, parameters, cache)

        self.category_path = os.path.join('testing', 'supply-system-overview')
        self.generation = self.parameters['generation']
        self.individual = self.parameters['individual']
        self.input_files = []

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_heating(self):
        data_heating = pd.read_csv(
            self.locator.get_optimization_slave_heating_activation_pattern(self.individual, self.generation)).set_index(
            'DATE')
        if self.timeframe == "daily":
            data_heating.index = pd.to_datetime(data_heating.index)
            data_heating = data_heating.resample('D').sum()
        elif self.timeframe == "weekly":
            data_heating.index = pd.to_datetime(data_heating.index)
            data_heating = data_heating.resample('W').sum()
        elif self.timeframe == "monthly":
            data_heating.index = pd.to_datetime(data_heating.index)
            data_heating = data_heating.resample('M').sum()
        return data_heating

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_cooling(self):
        data_cooling = pd.read_csv(
            self.locator.get_optimization_slave_cooling_activation_pattern(self.individual, self.generation)).set_index(
            'DATE')
        if self.timeframe == "daily":
            data_cooling.index = pd.to_datetime(data_cooling.index)
            data_cooling = data_cooling.resample('D').sum()
        elif self.timeframe == "weekly":
            data_cooling.index = pd.to_datetime(data_cooling.index)
            data_cooling = data_cooling.resample('W').sum()
        elif self.timeframe == "monthly":
            data_cooling.index = pd.to_datetime(data_cooling.index)
            data_cooling = data_cooling.resample('M').sum()
        return data_cooling

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_electricity(self):
        data_electricity = pd.read_csv(
            self.locator.get_optimization_slave_electricity_activation_pattern(self.individual,
                                                                               self.generation)).set_index('DATE')
        if self.timeframe == "daily":
            data_electricity.index = pd.to_datetime(data_electricity.index)
            data_electricity = data_electricity.resample('D').sum()
        elif self.timeframe == "weekly":
            data_electricity.index = pd.to_datetime(data_electricity.index)
            data_electricity = data_electricity.resample('W').sum()
        elif self.timeframe == "monthly":
            data_electricity.index = pd.to_datetime(data_electricity.index)
            data_electricity = data_electricity.resample('M').sum()
        return data_electricity

    @cea.plots.cache.cached
    def process_individual_requirements_curve_electricity(self):
        data_el_requirements = pd.read_csv(
            self.locator.get_optimization_slave_electricity_requirements_data(self.individual,
                                                                              self.generation)).set_index('DATE')
        if self.timeframe == "daily":
            data_el_requirements.index = pd.to_datetime(data_el_requirements.index)
            data_el_requirements = data_el_requirements.resample('D').sum()
        elif self.timeframe == "weekly":
            data_el_requirements.index = pd.to_datetime(data_el_requirements.index)
            data_el_requirements = data_el_requirements.resample('W').sum()
        elif self.timeframe == "monthly":
            data_el_requirements.index = pd.to_datetime(data_el_requirements.index)
            data_el_requirements = data_el_requirements.resample('M').sum()
        return data_el_requirements

    @cea.plots.cache.cached
    def process_individual_ramping_capacity(self):
        data_el_exports_imports = pd.read_csv(
            self.locator.get_optimization_slave_electricity_activation_pattern(self.individual,
                                                                               self.generation))
        lenght = data_el_exports_imports.shape[0]
        ramping = []  # store how much it needs to import or export
        ramping.append(data_el_exports_imports.loc[lenght - 1, "E_GRID_directload_W"]
                       - data_el_exports_imports.loc[0, "E_GRID_directload_W"])
        for hour in range(0, lenght-1):
            ramping.append(data_el_exports_imports.loc[hour, "E_GRID_directload_W"]
                           - data_el_exports_imports.loc[hour + 1, "E_GRID_directload_W"])

        data_el_exports_imports = data_el_exports_imports.set_index('DATE')
        data_el_exports_imports.index = pd.to_datetime(data_el_exports_imports.index)
        data_el_exports_imports["E_GRID_ramping_W"] = ramping
        return data_el_exports_imports
