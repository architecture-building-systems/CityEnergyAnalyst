"""
cehck perfromacne of pareto curve
https://arxiv.org/pdf/1901.00577.pdf
"""
from __future__ import division
from __future__ import print_function

import json

import plotly.graph_objs as go

import cea.plots.optimization

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class OptimizationPerformance(cea.plots.optimization.GenerationPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Perfromance of optimization algorithm"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(OptimizationPerformance, self).__init__(project, parameters, cache)
        self.analysis_fieldsy = ['Generational Distance']
        self.input_files = [(self.locator.get_optimization_checkpoint, [self.generation])]

    def calc_convergence_metrics(self):
        with open(self.locator.get_optimization_checkpoint(self.generation), 'rb') as f:
            data_checkpoint = json.load(f)
        convergence_metrics = {'generation': range(1, self.generation + 1),
                               'Generational Distance': data_checkpoint['generational_distances'],
                               'Delta of Generational Distance': data_checkpoint['difference_generational_distances']}
        return convergence_metrics

    @property
    def layout(self):
        return go.Layout(legend=dict(orientation="v", x=0.75, y=0.95),
                         xaxis=dict(title='Generation No. [-]'),
                         yaxis=dict(title='Generational Distance [-]'),
                         yaxis2=dict(title='Cumulative Generational Distance [%]', overlaying='y', side='right')
                         )

    @property
    def title(self):
        return "Performance of optimization algorithm until generation {generation}".format(generation=self.generation)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_performance_optimization'.format(generation=self.generation),
            self.category_name)

    def calc_graph(self):
        data = self.calc_convergence_metrics()
        traces = []
        for field in self.analysis_fieldsy:
            x = data['generation']
            y = data[field]
            trace = go.Scattergl(x=x, y=y, name=field)
            traces.append(trace)

        total_distance = sum(data['Delta of Generational Distance'])
        y_cumulative = []
        for i in range(len(data['generation'])):
            if i == 0:
                y_acum =  data['Delta of Generational Distance'][i]/total_distance *100
            else:
                y_acum += data['Delta of Generational Distance'][i]/total_distance *100
            y_cumulative.append(y_acum)

        x = data['generation']
        trace = go.Scattergl(x=x, y=y_cumulative, yaxis='y2', name='Cumulative Generational Distance')
        traces.append(trace)

        return traces


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    OptimizationPerformance(config.project,
                            {'scenario-name': config.scenario_name,
                             'generation': config.plots_optimization.generation},
                            cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
