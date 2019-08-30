from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.optimization
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class AnnualCostsPlot(cea.plots.optimization.GenerationPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Annual costs"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(AnnualCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_a_sys_connected_USD",
                                "Capex_a_sys_disconnected_USD",
                                "Opex_a_sys_connected_USD",
                                "Opex_a_sys_disconnected_USD"
                                ]
        self.input_files = [(self.locator.get_optimization_generation_total_performance, [self.generation])]

    @property
    def title(self):
        return "Annual Costs for generation #%s" % self.generation

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_annualized_costs'.format(generation=self.generation),
            self.category_name)

    @property
    def layout(self):
        return go.Layout(barmode='relative',
                         yaxis=dict(title='Annualized cost [USD$(2015)/year]', domain=[0.0, 1.0]))

    def calc_graph(self):
        self.multi_criteria = False  # TODO: add capabilities to plot muticriteria in this plot too
        data = self.process_generation_total_performance()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data['individual_name'], y=y, name=NAMING[field],
                               marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    AnnualCostsPlot(config.project,
                    {'buildings': None,
                     'scenario-name': config.scenario_name,
                     'generation': config.plots_optimization.generation},
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
