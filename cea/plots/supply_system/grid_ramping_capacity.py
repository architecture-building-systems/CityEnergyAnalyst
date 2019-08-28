"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.supply_system
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class RampingCapacity(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Electrical Grid Impact (ramp-rate)"
    expected_parameters = {
        'generation': 'plots-supply-system:generation',
        'individual': 'plots-supply-system:individual',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(RampingCapacity, self).__init__(project, parameters, cache)
        self.analysis_fields = ["E_GRID_ramping_W"]
        self.input_files = [(self.locator.get_optimization_slave_electricity_requirements_data,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Likelihood of intra-daily ramp rate at transformer for system %s" % (self.individual)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_ind{individual}ramping_capacity'.format(individual=self.individual,
                                                                           generation=self.generation),
            self.category_name)

    @property
    def layout(self):
        return dict(barmode='relative', yaxis=dict(title='Ramping Capacity required [MW]'))

    def calc_graph(self):
        # main data about technologies
        data = self.process_individual_ramping_capacity()
        hours = data.index.hour
        graph = []
        for field in self.analysis_fields:
            y = data[field].values / 1E6  # into MW
            trace = go.Box(x=hours, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    RampingCapacity(config.project,
                    {'scenario-name': config.scenario_name,
                                      'generation': config.plots_supply_system.generation,
                                      'individual': config.plots_supply_system.individual},
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()


