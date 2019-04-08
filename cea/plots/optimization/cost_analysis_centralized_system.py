from __future__ import division
from __future__ import print_function

import cea.plots.optimization
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CostAnalysisCentralizedSystemPlot(cea.plots.optimization.OptimizationOverviewPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Cost analysis of centralized system"

    def __init__(self, project, parameters, cache):
        super(CostAnalysisCentralizedSystemPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_Centralized_USD",
                                "Capex_Decentralized_USD",
                                "Opex_Centralized_USD",
                                "Opex_Decentralized_USD"]
        self.layout = go.Layout(title=self.title, barmode='relative',
                                yaxis=dict(title='Cost [USD$(2015)/year]', domain=[0.0, 1.0]))
        self.input_files = [self.locator.get_total_demand(),
                            self.locator.get_preprocessing_costs(),
                            self.locator.get_optimization_checkpoint(self.generation)]

    @property
    def title(self):
        return "CAPEX vs. OPEX of centralized system in generation {generation}".format(
            generation=self.parameters['generation'])

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_centralized_and_decentralized_costs_total'.format(generation=self.generation),
            self.category_name)

    def calc_graph(self):
        data = self.preprocessing_final_generation_data_cost_centralized()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data.index, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph
