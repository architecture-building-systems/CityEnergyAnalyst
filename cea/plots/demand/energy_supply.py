"""
Implements the Energy Supply pot.
"""
from __future__ import division
from __future__ import print_function

import cea.plots.demand
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, LOGO, COLOR


class EnergySupplyPlot(cea.plots.demand.DemandPlotBase):
    """Implement the energy-supply plot"""
    name = "Energy Supply"

    def __init__(self, project, parameters):
        super(EnergySupplyPlot, self).__init__(project, parameters)
        self.analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr", 'SOLAR_ww_MWhyr', 'SOLAR_hs_MWhyr', "DC_cs_MWhyr",
                                'DC_cdata_MWhyr', 'DC_cre_MWhyr', 'PV_MWhyr', 'GRID_MWhyr', 'NG_hs_MWhyr',
                                'COAL_hs_MWhyr', 'OIL_hs_MWhyr', 'WOOD_hs_MWhyr', 'NG_ww_MWhyr', 'COAL_ww_MWhyr',
                                'OIL_ww_MWhyr', 'WOOD_ww_MWhyr']
        self.data = self.yearly_loads
        self.analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        self.layout = go.Layout(barmode='stack',
                                yaxis=dict(title='Energy Demand [MWh/yr]', domain=[0.35, 1]),
                                xaxis=dict(title='Building Name'), showlegend=True)

    def calc_graph(self):
        graph = []
        self.data['total'] = self.data[self.analysis_fields].sum(axis=1)
        data = self.data.sort_values(by='total', ascending=False)
        for field in self.analysis_fields:
            y = data[field]
            name = NAMING[field]
            total_percent = (y / data['total'] * 100).round(2).values
            total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
            trace = go.Bar(x=data["Name"], y=y, name=name, text=total_percent_txt, orientation='v',
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    buildings = config.plots.buildings

    EnergySupplyPlot(config, locator, buildings).plot(auto_open=True)
    EnergySupplyPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)