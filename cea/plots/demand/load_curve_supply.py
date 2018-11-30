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

    def __init__(self, project, parameters):
        super(LoadCurveSupplyPlot, self).__init__(project, parameters)
        self.data = self.hourly_loads[self.hourly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = self.remove_unused_fields(self.data,
                                                         ["DH_hs_kWh", "DH_ww_kWh",
                                                          'SOLAR_ww_kWh', 'SOLAR_hs_kWh',
                                                          "DC_cs_kWh", 'DC_cdata_kWh', 'DC_cre_kWh',
                                                          'GRID_kWh', 'PV_kWh',
                                                          'NG_hs_kWh',
                                                          'COAL_hs_kWh',
                                                          'OIL_hs_kWh',
                                                          'WOOD_hs_kWh',
                                                          'NG_ww_kWh',
                                                          'COAL_ww_kWh',
                                                          'OIL_ww_kWh',
                                                          'WOOD_ww_kWh'])
        self.layout = dict(yaxis=dict(title='Load [kW]'),
                           yaxis2=dict(title='Temperature [C]', overlaying='y', side='right'), xaxis=dict(
                rangeselector=dict(buttons=list([dict(count=1, label='1d', step='day', stepmode='backward'),
                                                 dict(count=1, label='1w', step='week', stepmode='backward'),
                                                 dict(count=1, label='1m', step='month', stepmode='backward'),
                                                 dict(count=6, label='6m', step='month', stepmode='backward'),
                                                 dict(count=1, label='1y', step='year', stepmode='backward'),
                                                 dict(step='all')])), rangeslider=dict(), type='date',
                range=[self.data.index[0], self.data.index[168]], fixedrange=False))

    def calc_graph(self):
        traces = []
        for field in self.analysis_fields:
            y = self.data[field].values
            name = NAMING[field]
            if field in ["T_int_C", "T_ext_C"]:
                trace = go.Scatter(x=self.data.index, y=y, name=name, yaxis='y2', opacity=0.2)
            else:
                trace = go.Scatter(x=self.data.index, y=y, name=name,
                                   marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    buildings = config.plots.buildings

    LoadCurveSupplyPlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    LoadCurveSupplyPlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    LoadCurveSupplyPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)