"""
Show a Pareto curve plot for individuals in a given generation.
"""




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


class DispatchCurveDistrictElectricityPlot(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Dispatch curve electricity"
    expected_parameters = {
        'system': 'plots-supply-system:system',
        'timeframe': 'plots:timeframe',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(DispatchCurveDistrictElectricityPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["E_CHP_gen_directload_W",
                                "E_Trigen_gen_directload_W",
                                "E_Furnace_dry_gen_directload_W",
                                "E_Furnace_wet_gen_directload_W",
                                "E_PV_gen_directload_W",
                                "E_PVT_gen_directload_W",
                                "E_GRID_directload_W",
                                ]
        self.analysis_fields_exports = ["E_CHP_gen_export_W",
                                        "E_Trigen_gen_export_W",
                                        "E_Furnace_dry_gen_export_W",
                                        "E_Furnace_wet_gen_export_W",
                                        "E_PV_gen_export_W",
                                        "E_PVT_gen_export_W",
                                        ]
        self.analysis_field_demand = ['E_electricalnetwork_sys_req_W']
        self.input_files = [(self.locator.get_optimization_slave_electricity_activation_pattern,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Dispatch curve for electricity system %s (%s)" % (self.system, self.timeframe)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            '{system}_dispatch_electricity'.format(system=self.system), self.category_name)

    @property
    def layout(self):
        return dict(barmode='relative', yaxis=dict(title='Energy Generation [MWh]'))

    def calc_graph(self):
        # main data about technologies
        data = self.process_individual_dispatch_curve_electricity()
        graph = []
        analysis_fields = self.remove_unused_fields(data, self.analysis_fields)
        for field in analysis_fields:
            y = (data[field].values) / 1E6  # into MWh
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        # data about demand
        data_req = self.process_individual_requirements_curve_electricity()
        for field in self.analysis_field_demand:
            y = (data_req[field].values) / 1E6 # into MWh
            trace = go.Scattergl(x=data.index, y=y, name=NAMING[field],
                               line=dict(width=1, color=COLOR[field]))

            graph.append(trace)

        # data about exports
        analysis_fields_exports = self.remove_unused_fields(data, self.analysis_fields_exports)
        for field in analysis_fields_exports:
            y = (data[field].values) / 1E6  # into MWh
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))

            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    DispatchCurveDistrictElectricityPlot(config.project,
                                         {'scenario-name': config.scenario_name,
                                          'system': config.plots_supply_system.system,
                                          'timeframe': config.plots.timeframe},
                                         cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
