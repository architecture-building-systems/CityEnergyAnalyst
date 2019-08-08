"""
Implements the Load Curve Supply plot.
"""
from __future__ import division
from __future__ import print_function

import cea.plots.demand
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, COLOR


class LoadCurveSupplyPlot(cea.plots.demand.DemandPlotBase):
    """Implement the load-curve-supply plot"""
    name = "Load Curve Supply"
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
    }

    def __init__(self, project, parameters, cache):
        super(LoadCurveSupplyPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["DH_hs_kWh", "DH_ww_kWh", 'SOLAR_ww_kWh', 'SOLAR_hs_kWh', "DC_cs_kWh", 'DC_cdata_kWh',
                                'DC_cre_kWh', 'GRID_kWh', 'PV_kWh', 'NG_hs_kWh', 'COAL_hs_kWh', 'OIL_hs_kWh',
                                'WOOD_hs_kWh', 'NG_ww_kWh', 'COAL_ww_kWh', 'OIL_ww_kWh', 'WOOD_ww_kWh']
        self.timeframe = self.parameters['timeframe']

    @property
    def layout(self):
        return dict(yaxis=dict(title='Final Energy Demand [MW]'),
                    yaxis2=dict(title='Temperature [C]', overlaying='y', side='right'))

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
            y = data[field].values / 1E3# to MW
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

    LoadCurveSupplyPlot(config.project,
                  {'buildings': locator.get_zone_building_names(),
                   'scenario-name': config.scenario_name,
                   'timeframe': config.plots.timeframe},
                  cache).plot(auto_open=True)

    LoadCurveSupplyPlot(config.project,
                  {'buildings': locator.get_zone_building_names()[1:2],
                   'scenario-name': config.scenario_name,
                   'timeframe': config.plots.timeframe},
                  cache).plot(auto_open=True)