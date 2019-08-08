from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.demand
from cea.plots.variable_naming import COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class LoadCurvePlot(cea.plots.demand.DemandPlotBase):
    name = "Load Curve"
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
    }

    def __init__(self, project, parameters, cache):
        super(LoadCurvePlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Eal_kWh",
                                "Edata_kWh",
                                "Epro_kWh",
                                "Eaux_kWh",
                                "Qhs_sys_kWh",
                                "Qww_sys_kWh",
                                "Qcs_sys_kWh",
                                'Qcdata_sys_kWh',
                                'Qcre_sys_kWh']
        self.timeframe = self.parameters['timeframe']

    @property
    def layout(self):
        # computing this instead of initializing, because it's dependent on self.data...
        return dict(yaxis=dict(title='End-Use Energy Demand [MWh]'),
                    yaxis2=dict(title='Outdoor Temperature [C]', overlaying='y', side='right'))

    @property
    def title(self):
        """Override the version in PlotBase"""
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                return "%s for Building %s (%s)" % (self.name, self.buildings[0], self.timeframe)
            else:
                return "%s for Selected Buildings (%s)" % (self.name, self.timeframe)
        return "%s for District (%s)" % (self.name, self.timeframe)

    def calc_graph(self):
        data = self.calculate_hourly_loads()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.analysis_fields)
        for field in analysis_fields:
            y = data[field].values / 1E3  # to MW
            name = NAMING[field]
            trace = go.Scatter(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]))
            traces.append(trace)

        data_T = self.calculate_external_temperature()
        for field in ["T_ext_C"]:
            y = data_T[field].values
            name = NAMING[field]
            trace = go.Scatter(x=data_T.index, y=y, name=name, yaxis='y2', opacity=0.2)
            traces.append(trace)
        return traces


if __name__ == '__main__':
    import cea.config
    import cea.plots.cache
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()

    LoadCurvePlot(config.project,
                  {'buildings': locator.get_zone_building_names(),
                   'scenario-name': config.scenario_name,
                   'timeframe': config.plots.timeframe},
                  cache).plot(auto_open=True)

    LoadCurvePlot(config.project,
                  {'buildings': locator.get_zone_building_names()[1:2],
                   'scenario-name': config.scenario_name,
                   'timeframe': config.plots.timeframe},
                  cache).plot(auto_open=True)
