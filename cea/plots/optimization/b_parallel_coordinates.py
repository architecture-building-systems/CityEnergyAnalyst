"""
Show a Pareto curve plot for individuals in a given generation.
"""




import plotly.graph_objs as go

import cea.plots.optimization

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ParallelCoordinatesForOneGenerationPlot(cea.plots.optimization.GenerationPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Parallel coordinates"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'normalization': 'plots:normalization',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(ParallelCoordinatesForOneGenerationPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ['individual_name',
                                'GHG_sys_tonCO2',
                                'TAC_sys_USD',
                                'Opex_a_sys_USD',
                                'Capex_total_sys_USD',
                                ]
        self.objectives = ['GHG_sys_tonCO2', 'TAC_sys_USD', 'Opex_a_sys_USD', 'Capex_total_sys_USD']
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_optimization_generation_total_performance_pareto, [self.generation])]
        self.titles = self.calc_titles()

    def calc_titles(self):
        title = 'System No.'
        if self.normalization == "gross floor area":
            titlex = 'Equivalent annual costs <br>[USD$(2015)/m2.yr]'
            titley = 'GHG emissions <br>[kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
            titlel = 'Operation costs <br>[USD$(2015)/m2.yr]'
        elif self.normalization == "net floor area":
            titlex = 'Equivalent annual costs <br>[USD$(2015)/m2.yr]'
            titley = 'GHG emissions <br>[kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
            titlel = 'Operation costs <br>[USD$(2015)/m2.yr]'
        elif self.normalization == "air conditioned floor area":
            titlex = 'Equivalent annual costs <br>[USD$(2015)/m2.yr]'
            titley = 'GHG emissions <br>[kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2.yr]'
            titlel = 'Operation costs <br>[USD$(2015)/m2.yr]'
        elif self.normalization == "building occupancy":
            titlex = 'Equivalent annual costs <br>[USD$(2015)/p.yr]'
            titley = 'GHG emissions <br>[kg CO2-eq/p.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/p]'
            titlel = 'Operation costs <br>[USD$(2015)/p.yr]'
        else:
            titlex = 'Equivalent annual costs <br>[USD$(2015)/yr]'
            titley = 'GHG emissions <br>[ton CO2-eq/yr]'
            titlez = 'Investment costs <br>[USD$(2015)]'
            titlel = 'Operation costs <br>[USD$(2015)/yr]'

        return title, titley, titlex, titlel, titlez

    @property
    def layout(self):
        return go.Layout()

    @property
    def title(self):
        if self.normalization != "none":
            return "Parallel Plot for generation {generation} normalized to {normalized}".format(
                generation=self.generation, normalized=self.normalization)
        else:
            return "Parallel Plot for generation {generation}".format(generation=self.generation)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('gen{generation}_parallelplot'.format(generation=self.generation),
                                                      self.category_name)

    def calc_graph(self):
        graph = []
        # PUT THE PARETO CURVE INSIDE
        data = self.process_generation_total_performance_pareto()
        data = self.normalize_data(data, self.normalization, self.objectives)
        data = data.sort_values(['GHG_sys_tonCO2'])

        dimensions = list([dict(label=label, values=data[field]) if field != 'individual_name' else dict(
            ticktext=data[field], label=label, tickvals=list(range(data.shape[0])), values=list(range(data.shape[0])))
                           for field, label in zip(self.analysis_fields, self.titles)])
        line = dict(color= data['Capex_total_sys_USD'], colorscale='Jet', showscale=True)

        trace = go.Parcoords(line=line, dimensions=dimensions, labelfont=dict(size=10), rangefont=dict(size=8), tickfont=dict(size=10))

        graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ParallelCoordinatesForOneGenerationPlot(config.project,
                                            {'scenario-name': config.scenario_name,
                                             'generation': config.plots_optimization.generation,
                                             'normalization': config.plots.normalization},
                                            cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
