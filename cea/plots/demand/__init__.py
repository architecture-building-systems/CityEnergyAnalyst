from __future__ import division
from __future__ import print_function

import functools
import cea.plots
import pandas as pd
import os

"""
Implements py:class:`cea.plots.DemandPlotBase` as a base class for all plots in the category "demand" and also
set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Energy demand'


class DemandPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "demand"

    # cache hourly_loads results to avoid recalculating it every time
    _cache = {}

    def __init__(self, config, locator, buildings):
        super(DemandPlotBase, self).__init__(config, locator, buildings)
        self.category_path = os.path.join('new_basic', 'demand')


        # FIXME: this should probably be worked out from a declarative description of the demand outputs
        self.demand_analysis_fields = ['I_sol_kWh',
                                       'Q_gain_sen_light_kWh',
                                       'Q_gain_sen_app_kWh',
                                       'Q_gain_sen_data_kWh',
                                       'Q_gain_sen_peop_kWh',
                                       'Q_gain_sen_wall_kWh',
                                       'Q_gain_sen_base_kWh',
                                       'Q_gain_sen_roof_kWh',
                                       'Q_gain_sen_wind_kWh',
                                       'Q_gain_sen_vent_kWh',
                                       'I_rad_kWh',
                                       'Qcs_lat_sys_kWh',
                                       'Q_loss_sen_ref_kWh',
                                       "GRID_kWh",
                                       "PV_kWh",
                                       "DH_hs_kWh",
                                       "DH_ww_kWh",
                                       "E_sys_kWh",
                                       "Qhs_sys_kWh",
                                       "Qww_sys_kWh",
                                       "Qcs_sys_kWh",
                                       'DC_cdata_kWh',
                                       'DC_cre_kWh',
                                       "DC_cs_kWh",
                                       'NG_hs_kWh',
                                       'COAL_hs_kWh',
                                       'OIL_hs_kWh',
                                       'WOOD_hs_kWh',
                                       'NG_ww_kWh',
                                       'COAL_ww_kWh',
                                       'OIL_ww_kWh',
                                       'WOOD_ww_kWh',
                                       'SOLAR_ww_kWh',
                                       'SOLAR_hs_kWh',
                                       'E_ww_kWh',
                                       'E_hs_kWh',
                                       'E_cs_kWh',
                                       'E_cdata_kWh',
                                       'E_cre_kWh']

    @property
    def hourly_loads(self):
        """
        Returns the hourly loads, summed up for all the builidngs being considered by the plot.
        Stores the result in ``self._cache`` since the reduce operation takes a lot of time.
        """
        m_time = os.path.getmtime(self.locator.get_total_demand())  # when was demand script last run?
        buildings_key = ','.join(self.buildings)  # key for looking up in the cache
        if buildings_key in self._cache:
            # only load hourly_loads once, based on {buildings, mtime}
            cache_mtime, result = self._cache[buildings_key]
            if m_time == cache_mtime:
                # cached result is still up-to-date!
                return result

        # no cached result - calculate from scratch and cache for further use
        print('no cache found for', buildings_key, m_time)
        def add_fields(df1, df2):
            """Add the demand analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
            df1[self.demand_analysis_fields] += df2[self.demand_analysis_fields]
            return df1

        # cache these results for later
        result = functools.reduce(add_fields,
                                 (pd.read_csv(self.locator.get_demand_results_file(building)) for building in
                                  self.buildings)).set_index('DATE')
        self._cache[buildings_key] = (m_time, result)
        return result

    @property
    def yearly_loads(self):
        return pd.read_csv(self.locator.get_total_demand())