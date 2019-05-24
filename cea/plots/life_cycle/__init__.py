from __future__ import division
from __future__ import print_function

import pandas as pd
import numpy as np
import os
import cea.inputlocator
from cea.utilities import epwreader

"""
Implements py:class:`cea.plots.LifeCycleAnalysisPlotBase` as a base class for all plots in the category 
"life-cycle-analysis" and also set's the label for that category.
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
label = 'Life Cycle Analysis'


class LifeCycleAnalysisPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "life-cycle-analysis"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(LifeCycleAnalysisPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('new_basic', 'life-cycle-anaylsis')
        self.analysis_fields_costs = ['DC_cs_cost_yr', 'DC_cdata_cost_yr', 'DC_cre_cost_yr', 'DH_ww_cost_yr',
                                      'DH_hs_cost_yr', 'SOLAR_ww_cost_yr', 'SOLAR_hs_cost_yr', 'GRID_cost_yr',
                                      'PV_cost_yr', 'NG_hs_cost_yr', 'COAL_hs_cost_yr', 'OIL_hs_cost_yr',
                                      'WOOD_hs_cost_yr', 'NG_ww_cost_yr', 'COAL_ww_cost_yr', 'OIL_ww_cost_yr',
                                      'WOOD_ww_cost_yr']
        self.analysis_fields_emissions = ['E_ghg_ton', 'O_ghg_ton', 'M_ghg_ton']
        self.analysis_fields_emissions_m2 = ['E_ghg_kgm2', 'O_ghg_kgm2', 'M_ghg_kgm2']
        self.analysis_fields_primary_energy = ['E_nre_pen_GJ', 'O_nre_pen_GJ', 'M_nre_pen_GJ']
        self.analysis_fields_primary_energy_m2 = ['E_nre_pen_MJm2', 'O_nre_pen_MJm2', 'M_nre_pen_MJm2']
        self.input_files = [(self.locator.get_lca_embodied, []),
                            (self.locator.get_lca_operation, []),
                            (self.locator.get_lca_mobility, [])]

    @property
    def data_processed_emissions(self):
        """ Returns the preprocessed emissions data used for the life-cycle-analysis plots. Uses the PlotCache to
        speed up ``self._calculate_data_processed_emissions()`` """
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'data_processed_emissions'),
                                 plot=self, producer=self._calculate_data_processed_emissions)

    def _calculate_data_processed_emissions(self):
        data_raw_embodied_emissions = pd.read_csv(self.locator.get_lca_embodied()).set_index('Name')
        data_raw_operation_emissions = pd.read_csv(self.locator.get_lca_operation()).set_index('Name')
        data_raw_mobility_emissions = pd.read_csv(self.locator.get_lca_mobility()).set_index('Name')
        data_processed = data_raw_embodied_emissions.join(data_raw_operation_emissions, lsuffix='y').join(
            data_raw_mobility_emissions, lsuffix='y2')
        return data_processed.ix[self.buildings]
