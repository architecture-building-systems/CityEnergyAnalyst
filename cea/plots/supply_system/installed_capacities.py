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


class InstalledCapacities(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Installed Capacities"
    expected_parameters = {
        'generation': 'plots-supply-system:generation',
        'individual': 'plots-supply-system:individual',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(InstalledCapacities, self).__init__(project, parameters, cache)
        self.analysis_fields_connected_heating = []
        self.analysis_fields_connected_cooling = []
        self.analysis_fields_connected_electricity = []
        self.analysis_fields_disconnected_heating = []
        self.analysis_fields_disconnected_cooling =  []
        self.input_files = [(self.locator.get_optimization_slave_electricity_requirements_data,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Installed Capacities for system %s" % (self.individual)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_ind{individual}installed_capacities'.format(individual=self.individual,
                                                                           generation=self.generation),
            self.category_name)

    @property
    def layout(self):
        return dict(barmode='relative', yaxis=dict(title='Installed Capacity [kW]'))

    def calc_graph(self):
        # GET BARCHART OF CONNECTED BUILDINGS
        data_connected = self.process_individual_ramping_capacity()
        data_disconnected = self.process_individual_ramping_capacity()

        analysis_fields_connected_heating = self.analysis_fields_connected_heating
        analysis_fields_connected_cooling = self.analysis_fields_connected_cooling
        analysis_fields_connected_electricity = self.analysis_fields_connected_electricity
        analysis_fields_disconnected_heating = self.analysis_fields_disconnected_heating
        analysis_fields_disconnected_cooling = self.analysis_fields_disconnected_cooling
        analysis_fields_connected = analysis_fields_connected_heating + analysis_fields_connected_cooling + analysis_fields_connected_electricity
        analysis_fields_disconnected = analysis_fields_disconnected_heating + analysis_fields_disconnected_cooling

        # iterate through annual_consumption to plot
        total_connected = data_connected[analysis_fields_connected].sum()
        graph = []
        for field in analysis_fields_connected_heating + analysis_fields_connected_cooling + analysis_fields_connected_electricity:
            x = ['Technology for connected buildings']
            y = data_connected[field]
            total_perc = (y / total_connected * 100).round(2)
            total_perc_txt = [str(y.round(1)) + " MWh (" + str(total_perc) + " %)"]
            trace = go.Bar(x=x, y=[y], name=NAMING[field],
                           text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        total_disconnected = data_disconnected[analysis_fields_disconnected].sum()
        for field in analysis_fields_disconnected_heating + analysis_fields_disconnected_cooling:
            x = data_disconnected.index
            y = data_disconnected[field]
            total_perc = (y / total_disconnected * 100).round(2)
            total_perc_txt = [str(y.round(1)) + " MWh (" + str(total_perc) + " %)"]
            trace = go.Bar(x=x,
                           y=[y],
                           name=NAMING[field],
                           text=total_perc_txt,
                           marker=dict(color=COLOR[field]),
                           xaxis='x2',
                           yaxis='y2',
                           showlegend=False)
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    InstalledCapacities(config.project,
                        {'scenario-name': config.scenario_name,
                                      'generation': config.plots_supply_system.generation,
                                      'individual': config.plots_supply_system.individual},
                        cache).plot(auto_open=True)


if __name__ == '__main__':
    main()


