



import functools
import os

import pandas as pd

import cea.config
import cea.inputlocator
import cea.plots
import cea.plots.cache
from cea.plots.base import PlotBase

"""
Implements py:class:`cea.plots.DemandPlotBase` as a base class for all plots in the category "demand" and also
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
label = 'Energy demand'


class DemandPlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "demand"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(DemandPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('special', 'demand')

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
                                       'GRID_a_kWh',
                                       'GRID_v_kWh',
                                       'GRID_ve_kWh',
                                       'GRID_l_kWh',
                                       'GRID_data_kWh',
                                       'GRID_pro_kWh',
                                       'GRID_aux_kWh',
                                       'GRID_ww_kWh',
                                       'GRID_hs_kWh',
                                       'GRID_cs_kWh',
                                       'GRID_cdata_kWh',
                                       'GRID_cre_kWh',
                                       "PV_kWh",
                                       "DH_hs_kWh",
                                       "DH_ww_kWh",
                                       "E_sys_kWh",
                                       "Eal_kWh",
                                       "El_kWh",
                                       "Ea_kWh",
                                       "Eve_kWh",
                                       "Ev_kWh",
                                       "Edata_kWh",
                                       "Epro_kWh",
                                       "Eaux_kWh",
                                       "Qhs_sys_kWh",
                                       "Qww_sys_kWh",
                                       "Qcs_sys_kWh",
                                       'Qcdata_sys_kWh',
                                       'Qcre_sys_kWh',
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

        self.input_files = [(self.locator.get_total_demand, [])]  # all these scripts depend on demand
        # Add building to input files if buildings are selected
        if self.buildings:
            self.input_files += [(self.locator.get_demand_results_file, [building]) for building in self.buildings]

    @property
    def hourly_loads(self):
        """
        Returns the hourly loads, summed up for all the builidngs being considered by the plot. Uses the PlotCache
        to speed up ``self._calculate_hourly_loads()``
        """
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'hourly_loads'),
                                 plot=self, producer=self._calculate_hourly_loads)

    def add_fields(self, df1, df2):
        """Add the demand analysis fields together - use this in reduce to sum up the summable parts of the dfs"""
        df1[self.demand_analysis_fields] = df2[self.demand_analysis_fields] + df1[self.demand_analysis_fields]
        return df1

    def _calculate_hourly_loads(self):
        data_demand = functools.reduce(self.add_fields, (pd.read_csv(self.locator.get_demand_results_file(building))
                                                         for building in self.buildings)).set_index('date')
        return data_demand

    def calculate_hourly_loads(self):
        data = self._calculate_hourly_loads()
        data_demand = self.resample_time_data(data)
        return data_demand

    def calculate_external_temperature(self):
        data_path = self.locator.get_demand_results_file(self.buildings[0])
        data = pd.read_csv(data_path)
        data = self.resample_time_data(data)
        return data

    @property
    def yearly_loads(self):
        return pd.read_csv(self.locator.get_total_demand())

    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = self.yearly_loads[self.yearly_loads['name'].isin(self.buildings)]
        return self._data


class DemandSingleBuildingPlotBase(DemandPlotBase):
    """A base class for demand plots that only work on a single building"""
    expected_parameters = {
        'building': 'plots:building',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(DemandSingleBuildingPlotBase, self).__init__(project, parameters, cache)
        self.building = parameters['building']
        self.buildings = [self.building]  # some parts of DemandPlotBase require this


def main():
    """
    Run all the plots in this category and time the caches.
    :return:
    """
    # run all the plots in this category
    config = cea.config.Configuration()
    from cea.plots.categories import list_categories
    from cea.plots.cache import PlotCache, MemoryPlotCache
    import time

    def plot_the_whole_category(cache):
        for category in list_categories(plugins=[]):
            if category.label != label:
                # skip other categories
                continue
            print('category:', category.name, ':', category.label)
            for plot_class in category.plots:
                print('plot_class:', plot_class)
                parameters = {
                    k: config.get(v) for k, v in plot_class.expected_parameters.items()
                }
                plot = plot_class(config.project, parameters=parameters, cache=cache)
                assert plot.name, 'plot missing name: %s' % plot
                assert plot.category_name == category.name
                print('plot:', plot.name, '/', plot.id(), '/', plot.title)

                missing_input_files = plot.missing_input_files()
                if missing_input_files:
                    for locator_method, args in missing_input_files:
                        print('Input file not found: {}'.format(locator_method(*args)))
                else:
                    # plot the plot!
                    plot.plot()

    # null_plot_cache = NullPlotCache()
    plot_cache = PlotCache(config.project)
    memory_plot_cache = MemoryPlotCache(config.project)
    # test plots with cache
    t0 = time.time()
    for i in range(3):
        plot_the_whole_category(plot_cache)
    time_with_cache = (time.time() - t0) / 3
    # test plots with memory cache
    t0 = time.time()
    for i in range(3):
        plot_the_whole_category(memory_plot_cache)
    time_with_memory_cache = (time.time() - t0) / 3
    # test plots without cache
    # t0 = time.time()
    # for i in range(3):
    #     plot_the_whole_category(null_plot_cache)
    # time_without_cache = (time.time() - t0) / 3
    # print('Average without cache: %.2f seconds' % time_without_cache)
    print('Average with cache: %.2f seconds' % time_with_cache)
    print('Average with memory cache: %.2f seconds' % time_with_memory_cache)


if __name__ == '__main__':
    main()
