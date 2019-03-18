from __future__ import division
from __future__ import print_function

import functools
import cea.plots
import pandas as pd
import os
import cea.config
import cea.inputlocator

"""
Implements py:class:`cea.plots.OptimizationOverviewPlotBase` as a base class for all plots in the category "optimization-overview" and also
set's the label for that category.
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
label = 'Optimization overview'


class OptimizationOverviewPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "optimization-overview"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'network-type': 'plots-optimization:network-type',
        'multicriteria': 'plots-optimization:multicriteria',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters):
        super(OptimizationOverviewPlotBase, self).__init__(project, parameters)
        self.category_path = os.path.join('testing', 'optimization-overview')