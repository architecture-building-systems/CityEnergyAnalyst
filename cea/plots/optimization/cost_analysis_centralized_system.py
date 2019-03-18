from __future__ import division
from __future__ import print_function

import cea.plots.optimization
import plotly.graph_objs as go
from plotly.offline import plot


from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CostAnalysisCentralizedSystem(cea.plots.optimization.OptimizationOverviewPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Cost analysis of centralized system"

    def __init__(self, project, parameters):
        super(CostAnalysisCentralizedSystem, self).__init__(project, parameters)
        self.analysis_fields = ["Capex_Centralized_USD",
                                "Capex_Decentralized_USD",
                                "Opex_Centralized_USD",
                                "Opex_Decentralized_USD"]
        self.data = self.preprocessing_final_generation_data_cost_centralized()
        self.layout = go.Layout(images=LOGO, title=self.title, barmode='relative',
                                yaxis=dict(title='Cost [USD$(2015)/year]', domain=[0.0, 1.0]))

    @property
    def title(self):
        return "CAPEX vs. OPEX of centralized system in generation {generation}".format(
            generation=self.parameters['generation'])

    def calc_graph(self):
        graph = []
        for field in self.analysis_fields:
            y = self.data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=self.data.index, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph
