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
    name = "Annualized costs"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'normalization': 'plots-optimization:normalization',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(AnnualCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_a_sys_connected_USD",
                                "Capex_a_sys_disconnected_USD",
                                "Opex_a_sys_connected_USD",
                                "Opex_a_sys_disconnected_USD"
                                ]
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_optimization_generation_total_performance_pareto, [self.generation])]
        self.titley = self.calc_titles()
        self.data_clean = None

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "net floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "building occupancy":
            titley = 'Annualized cost [USD$(2015)/pax.yr]'
        else:
            titley = 'Annualized cost [USD$(2015)/yr]'
        return titley

    @property
    def title(self):
        if self.normalization != "none":
            return "Annual Costs for generation {generation} normalized to {normalized}".format(
                generation=self.generation, normalized=self.normalization)
        else:
            return "Annual Costs for generation {generation}".format(generation=self.generation)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_annualized_costs'.format(generation=self.generation),
            self.category_name)

    @property
    def layout(self):
        return go.Layout(barmode='relative',
                         yaxis=dict(title=self.titley),
                         xaxis=dict(categoryorder = 'array',
                                    categoryarray = [x for _, x in sorted(zip(self.data_clean['TAC_sys_USD'], self.data_clean['individual_name']))])
        )

    def calc_graph(self):
        data = self.process_generation_total_performance_pareto()
        self.data_clean = data
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
    AnnualCostsPlot(config.project,
                    {'scenario-name': config.scenario_name,
                     'generation': config.plots_optimization.generation,
                     'normalization': config.plots_optimization.normalization
                     },
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
