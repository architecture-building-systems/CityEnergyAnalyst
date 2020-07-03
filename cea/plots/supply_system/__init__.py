from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

import pandas as pd
import pandas.errors

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
        'system': 'plots-supply-system:system',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SupplySystemPlotBase, self).__init__(project, parameters, cache)

        self.category_path = os.path.join('testing', 'supply-system-overview')
        self.system = self.parameters['system']
        self.generation = self.system.split("_")[1]
        self.individual = self.system.split("_")[2]
        self.input_files = []

    # FIXME: Temp fix for #2648
    def missing_input_files(self):
        if self.individual == 'today' and self.__class__.__name__ != 'SupplySystemMapPlot':
            raise NotImplementedError('Plot for `{}` has not been implemented. Try another system.'.format(self.system))
        else:
            super(SupplySystemPlotBase, self).missing_input_files()

    def process_individual_dispatch_curve_heating(self):
        data_path = self.locator.get_optimization_slave_heating_activation_pattern(self.individual, self.generation)
        data = pd.read_csv(data_path)
        data = self.resample_time_data(data)
        return data

    def process_individual_dispatch_curve_cooling(self):
        data_path = self.locator.get_optimization_slave_cooling_activation_pattern(self.individual, self.generation)
        data = pd.read_csv(data_path)
        data = self.resample_time_data(data)
        return data

    def process_individual_dispatch_curve_electricity(self):
        data_path = self.locator.get_optimization_slave_electricity_activation_pattern(self.individual, self.generation)
        data = pd.read_csv(data_path)
        data = self.resample_time_data(data)
        return data

    def process_individual_requirements_curve_electricity(self):
        data_path = self.locator.get_optimization_slave_electricity_requirements_data(self.individual, self.generation)
        data = pd.read_csv(data_path)
        data = self.resample_time_data(data)
        return data

    def process_individual_ramping_capacity(self):
        data_el_exports_imports = pd.read_csv(
            self.locator.get_optimization_slave_electricity_activation_pattern(self.individual,
                                                                               self.generation))
        lenght = data_el_exports_imports.shape[0]
        ramping = []  # store how much it needs to import or export
        ramping.append(data_el_exports_imports.loc[lenght - 1, "E_GRID_directload_W"]
                       - data_el_exports_imports.loc[0, "E_GRID_directload_W"])
        for hour in range(0, lenght - 1):
            ramping.append(data_el_exports_imports.loc[hour, "E_GRID_directload_W"]
                           - data_el_exports_imports.loc[hour + 1, "E_GRID_directload_W"])

        data_el_exports_imports = data_el_exports_imports.set_index('DATE')
        data_el_exports_imports.index = pd.to_datetime(data_el_exports_imports.index)
        data_el_exports_imports["E_GRID_ramping_W"] = ramping
        return data_el_exports_imports

    def process_district_scale_capacities_kW(self):
        try:
            heating_cap = pd.read_csv(self.locator.get_optimization_district_scale_heating_capacity(self.individual,
                                                                                                    self.generation))
        except pd.errors.EmptyDataError:
            heating_cap = pd.DataFrame()

        try:
            cooling_cap = pd.read_csv(self.locator.get_optimization_district_scale_cooling_capacity(self.individual,
                                                                                                    self.generation))
        except pd.errors.EmptyDataError:
            cooling_cap = pd.DataFrame()

        electricity_cap = pd.read_csv(self.locator.get_optimization_district_scale_electricity_capacity(self.individual,
                                                                                                        self.generation))

        district_capacities = pd.concat([heating_cap, cooling_cap, electricity_cap], axis=1, sort=False)
        return district_capacities / 1E3  # to kW

    def process_building_scale_capacities_kW(self):
        try:
            heating_cap = pd.read_csv(
                self.locator.get_optimization_building_scale_heating_capacity(self.individual,
                                                                              self.generation)).set_index('Name')
        except pd.errors.EmptyDataError:
            heating_cap = pd.DataFrame()

        try:
            cooling_cap = pd.read_csv(
                self.locator.get_optimization_building_scale_cooling_capacity(self.individual,
                                                                              self.generation)).set_index('Name')
        except pd.errors.EmptyDataError:
            cooling_cap = pd.DataFrame()

        building_capacities = pd.concat([heating_cap, cooling_cap], axis=1, sort=False).fillna(0.0)

        return building_capacities / 1E3  # to kW
