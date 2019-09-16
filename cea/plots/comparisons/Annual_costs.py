from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.comparisons
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ComparisonsAnnualCostsPlot(cea.plots.comparisons.ComparisonsPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Comparisons annual costs"

    def __init__(self, project, parameters, cache):
        super(ComparisonsAnnualCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_a_sys_connected_USD",
                                "Capex_a_sys_disconnected_USD",
                                "Opex_a_sys_connected_USD",
                                "Opex_a_sys_disconnected_USD"
                                ]
        self.input_files = []

    @property
    def title(self):
        return "Comparison Annual Costs"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('%s%s%s_annualized_costs' % (self.urban_scenarios, \
                                                                                   self.energy_system_scenarios_generation, \
                                                                                   self.energy_system_scenarios_individual))

    @property
    def layout(self):
        return go.Layout(barmode='relative',
                         yaxis=dict(title='Annualized cost [USD$(2015)/year]'))

    def calc_graph(self):
        data = self.preprocessing_annual_costs_scenarios()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data['scenario_name'], y=y, name=NAMING[field],
                               marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ComparisonsAnnualCostsPlot(config.project,
                               {
                                   'urban-energy-system-scenarios': config.plots_scenario_comparisons.urban_energy_system_scenarios},
                               cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
