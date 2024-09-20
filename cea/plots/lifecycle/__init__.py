



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
        'normalization': 'plots-lifecycle:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(LifecyclePlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', 'lifecycle')


    def normalize_data_individual_emissions(self, data_processed, buildings, analysis_fields):
        data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
        data_processed_2 = data_processed.join(data)
        if self.normalization == "gross floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['GFA_m2'], axis=0)*1000
        elif self.normalization == "net floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['Aocc_m2'], axis=0)*1000
        elif self.normalization == "air conditioned floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['Af_m2'], axis=0)*1000
        elif self.normalization == "building occupancy":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['people0'], axis=0)*1000

        return data_processed_2

    def normalize_data_individual_costs(self, data_processed, buildings, analysis_fields):
        data = pd.read_csv(self.locator.get_total_demand()).set_index('Name')
        data_processed_2 = data_processed.join(data)
        if self.normalization == "gross floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['GFA_m2'], axis=0)
        elif self.normalization == "net floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['Aocc_m2'], axis=0)
        elif self.normalization == "air conditioned floor area":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['Af_m2'], axis=0)
        elif self.normalization == "building occupancy":
            data_processed_2.loc[:, analysis_fields] = data_processed_2.loc[:, analysis_fields].div(data_processed_2['people0'], axis=0)

        return data_processed_2

