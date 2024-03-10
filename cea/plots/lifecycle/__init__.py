



import functools
import os

import pandas as pd
from cea.plots.base import PlotBase

"""
Implements py:class:`cea.plots.OccupancyPlotBase` as a base class for all plots in the category "solar-potential"
and also set's the label for that category.
"""

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Jimeno Fonseca"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'lifecycle'

class LifecyclePlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "lifecycle"

    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'normalization': 'plots-schedules:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(LifecyclePlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', 'lifecycle')
        self.input_files = [(self.locator.get_demand_results_file, [building]) for building in self.buildings]


    def normalize_data(self, data_processed, buildings, analysis_fields):
        if self.normalization == "gross floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['GFA_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "net floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['Aocc_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "air conditioned floor area":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['Af_m2'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)
        elif self.normalization == "building occupancy":
            data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
            normalizatioon_factor = data.loc[buildings]['people0'].sum()
            data_processed = data_processed.apply(
                lambda x: x / normalizatioon_factor if x.name in analysis_fields else x)

        return data_processed

