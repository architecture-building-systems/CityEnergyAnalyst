"""
Implements the Load Duration Curve Supply plot.
"""
from __future__ import division
from __future__ import print_function

import cea.plots.demand
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, COLOR


class LoadDurationCurveSupplyPlot(cea.plots.demand.DemandPlotBase):
    """Implement the load-duration-curve-supply plot"""
    name = "Load Duration Curve Supply"

    def __init__(self, project, parameters):
        super(LoadDurationCurveSupplyPlot, self).__init__(project, parameters)
        self.data = self.hourly_loads[self.hourly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = self.remove_unused_fields(self.data,
                                                         ["DH_hs_kWh", "DH_ww_kWh", 'SOLAR_ww_kWh', 'SOLAR_hs_kWh',
                                                          "DC_cs_kWh", 'DC_cdata_kWh', 'DC_cre_kWh', 'GRID_kWh',
                                                          'PV_kWh', 'NG_hs_kWh', 'COAL_hs_kWh', 'OIL_hs_kWh',
                                                          'WOOD_hs_kWh', 'NG_ww_kWh', 'COAL_ww_kWh', 'OIL_ww_kWh',
                                                          'WOOD_ww_kWh'])
        self.layout = go.Layout(xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                                yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]), showlegend=True)

    def calc_graph(self):
        graph = []
        duration = range(8760)
        x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
        for field in self.analysis_fields:
            name = NAMING[field]
            self.data = self.data.sort_values(by=field, ascending=False)
            y = self.data[field].values
            trace = go.Scatter(x=x, y=y, name=name, fill='tozeroy', opacity=0.8, marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    buildings = config.plots.buildings

    LoadDurationCurveSupplyPlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    LoadDurationCurveSupplyPlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    LoadDurationCurveSupplyPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)