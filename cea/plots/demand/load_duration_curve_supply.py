"""
Implements the Load Duration Curve Supply plot.
"""
from __future__ import division
from __future__ import print_function

import cea.plots.demand.load_duration_curve
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, COLOR
from cea.constants import HOURS_IN_YEAR


class LoadDurationCurveSupplyPlot(cea.plots.demand.load_duration_curve.LoadDurationCurvePlot):
    """Implement the load-duration-curve-supply plot"""
    name = "Load Duration Curve Supply"

    def __init__(self, project, parameters, cache):
        super(LoadDurationCurveSupplyPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["DH_hs_kWh", "DH_ww_kWh", 'SOLAR_ww_kWh', 'SOLAR_hs_kWh', "DC_cs_kWh", 'DC_cdata_kWh',
                                'DC_cre_kWh', 'GRID_kWh', 'PV_kWh', 'NG_hs_kWh', 'COAL_hs_kWh', 'OIL_hs_kWh',
                                'WOOD_hs_kWh', 'NG_ww_kWh', 'COAL_ww_kWh', 'OIL_ww_kWh', 'WOOD_ww_kWh']

    @property
    def layout(self):
        return go.Layout(xaxis=dict(title='Duration Normalized [%]'),
                         yaxis=dict(title='Load [kW]'), showlegend=True)

    def calc_graph(self):
        graph = []
        duration = range(HOURS_IN_YEAR)
        x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
        self.analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        for field in self.remove_unused_fields(self.data, self.analysis_fields):
            name = NAMING[field]
            data = self.data.sort_values(by=field, ascending=False)
            y = data[field].values
            trace = go.Scatter(x=x, y=y, name=name, fill='tozeroy', opacity=0.8, marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    buildings = config.plots.buildings
    cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()

    LoadDurationCurveSupplyPlot(config.project, {'buildings': None,
                                                 'scenario-name': config.scenario_name},
                                cache).plot(auto_open=True)
    LoadDurationCurveSupplyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                                 'scenario-name': config.scenario_name},
                                cache).plot(auto_open=True)
    LoadDurationCurveSupplyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                                 'scenario-name': config.scenario_name},
                                cache).plot(auto_open=True)
