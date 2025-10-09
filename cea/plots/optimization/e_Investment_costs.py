



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


class InvestmentCostsPlot(cea.plots.optimization.GenerationPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Investment costs"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'normalization': 'plots:normalization',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(InvestmentCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_total_sys_district_scale_USD",
                                "Capex_total_sys_building_scale_USD",
                                ]
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_optimization_generation_total_performance_pareto, [self.generation])]
        self.titley = self.calc_titles()
        self.data_clean = None

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Investment cost [USD$(2015)/m2]'
        elif self.normalization == "net floor area":
            titley = 'Investment cost [USD$(2015)/m2]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Investment cost [USD$(2015)/m2]'
        elif self.normalization == "building occupancy":
            titley = 'Investment cost [USD$(2015)/p]'
        else:
            titley = 'Investment cost [USD$(2015)/m2]'
        return titley

    @property
    def title(self):
        if self.normalization != "none":
            return "Investment Costs for best individuals after {generation} {generation_noun} normalized to {normalized}".format(
                generation=self.generation, normalized=self.normalization, generation_noun=self.generation_noun)
        else:
            return "Investment Costs for best individuals after {generation} {generation_noun}".format(
                generation=self.generation, generation_noun=self.generation_noun)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_investment_costs'.format(generation=self.generation),
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
        data = self.normalize_data(data, self.normalization, self.analysis_fields)
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
    # locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    InvestmentCostsPlot(config.project,
                        {'buildings': None,
                         'scenario-name': config.scenario_name,
                         'generation': config.plots_optimization.generation,
                         'normalization': config.plots.normalization},
                        cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
