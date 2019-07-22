from __future__ import division
from __future__ import print_function

import functools
import cea.plots
import pandas as pd
import os

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
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SupplySystemPlotBase, self).__init__(project, parameters, cache)

        self.category_path = os.path.join('testing', 'supply-system-overview')
        self.generation = self.parameters['generation']
        self.individual = self.parameters['individual']

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_heating(self):
        data_heating = pd.read_csv(
            self.locator.get_optimization_slave_heating_activation_pattern(self.individual, self.generation)).set_index(
            'DATE')
        return data_heating

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_cooling(self):
        data_cooling = pd.read_csv(
            self.locator.get_optimization_slave_cooling_activation_pattern(self.individual, self.generation)).set_index(
            'DATE')
        return data_cooling

    @cea.plots.cache.cached
    def process_individual_dispatch_curve_electricity(self):
        data_electricity = pd.read_csv(
            self.locator.get_optimization_slave_electricity_activation_pattern(self.individual,
                                                                               self.generation)).set_index('DATE')
        return data_electricity
