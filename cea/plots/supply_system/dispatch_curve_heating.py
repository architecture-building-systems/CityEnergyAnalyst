"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
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


class DispatchCurveOneOptionPlot(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Timeseries of energy dispatch for heating network"

    def __init__(self, project, parameters, cache):
        super(DispatchCurveOneOptionPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Q_PVT_to_directload_W",
                                "Q_SC_ET_to_directload_W",
                                "Q_SC_FP_to_directload_W",
                                "Q_HPServer_to_directload_W",
                                "Q_from_storage_used_W",

                                "Q_HPLake_gen_W",
                                "Q_HPSew_gen_W",
                                "Q_GHP_gen_W",
                                "Q_CHP_gen_W",
                                "Q_Furnace_gen_W",
                                "Q_BaseBoiler_gen_W",
                                "Q_PeakBoiler_gen_W",
                                "Q_AddBoiler_gen_W"]
        self.analysis_field_demand = ['Q_DHNf_W']
        self.input_files = [(self.locator.get_optimization_slave_heating_activation_pattern,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Dispatch curve for heating network"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('gen{generation}_ind{individual}dispatch_curve_heating'.format(individual=self.individual ,generation=self.generation),
                                                      self.category_name)

    @property
    def layout(self):
        data_frame = self.process_individual_dispatch_curves()['heating_network']
        return dict(barmode='relative', yaxis=dict(title='Energy Generation [kW]'),
             xaxis=dict(rangeselector=dict(buttons=list([
                 dict(count=1, label='1d', step='day', stepmode='backward'),
                 dict(count=1, label='1w', step='week', stepmode='backward'),
                 dict(count=1, label='1m', step='month', stepmode='backward'),
                 dict(count=6, label='6m', step='month', stepmode='backward'),
                 dict(count=1, label='1y', step='year', stepmode='backward'),
                 dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.index[0],
                                                                              data_frame.index[168]],
                 fixedrange=False))

    def calc_graph(self):
        # main data about technologies
        data = self.process_individual_dispatch_curves()['heating_network']
        graph = []
        for field in self.analysis_fields:
            y = (data[field].values) / 1000  # into kW
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        # data about demand
        for field in self.analysis_field_demand:
            y = (data[field].values) / 1000  # into kW
            trace = go.Scatter(x=data.index, y=y, name=NAMING[field],
                               line=dict(width=1, color=COLOR[field]))

            graph.append(trace)

        return graph

def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    DispatchCurveOneOptionPlot(config.project,
                                    {'scenario-name': config.scenario_name,
                                     'generation': config.plots_optimization.generation,
                                     'individual': config.plots_optimization.generation},
                                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
