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


class DispatchCurveDistrictHeatingPlot(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Dispatch curve heating plant"
    expected_parameters = {
        'system': 'plots-supply-system:system',
        'timeframe': 'plots:timeframe',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(DispatchCurveDistrictHeatingPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = [
            "Q_Storage_gen_directload_W",
            "Q_HP_Server_gen_directload_W",
            "Q_PVT_gen_directload_W",
            "Q_SC_ET_gen_directload_W",
            "Q_SC_FP_gen_directload_W",
            "Q_CHP_gen_directload_W",
            "Q_Furnace_dry_gen_directload_W",
            "Q_Furnace_wet_gen_directload_W",
            "Q_HP_Sew_gen_directload_W",
            "Q_HP_Lake_gen_directload_W",
            "Q_GHP_gen_directload_W",
            "Q_BaseBoiler_gen_directload_W",
            "Q_PeakBoiler_gen_directload_W",
            "Q_BackupBoiler_gen_directload_W",
        ]

        self.analysis_field_demand = ['Q_districtheating_sys_req_W']
        self.input_files = [(self.locator.get_optimization_slave_heating_activation_pattern,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Dispatch curve for heating plant in system %s (%s)" % (self.system, self.timeframe)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            '{system}_dispatch_curve_heating_plant'.format(system=self.system), self.category_name)

    @property
    def layout(self):
        return dict(barmode='relative', yaxis=dict(title='Energy Generation [MWh]'))

    def calc_graph(self):
        # main data about technologies
        data = self.process_individual_dispatch_curve_heating()
        graph = []
        analysis_fields = self.remove_unused_fields(data, self.analysis_fields)
        for field in analysis_fields:
            y = (data[field].values) / 1E6  # into MW
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        # data about demand
        for field in self.analysis_field_demand:
            y = (data[field].values) / 1E6  # into MW
            trace = go.Scattergl(x=data.index, y=y, name=NAMING[field],
                               line=dict(width=1, color=COLOR[field]))

            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    DispatchCurveDistrictHeatingPlot(config.project,
                                     {'scenario-name': config.scenario_name,
                                      'system': config.plots_supply_system.system,
                                      'timeframe': config.plots.timeframe},
                                     cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
