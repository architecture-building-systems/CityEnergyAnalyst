from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
import cea.plots.demand
from cea.plots.variable_naming import LOGO, COLOR, NAMING


class EnergySupplyIntensityPlot(cea.plots.demand.DemandPlotBase):
    name = "Energy Supply Intensity"

    def __init__(self, project, parameters):
        super(EnergySupplyIntensityPlot, self).__init__(project, parameters)
        self.data = self.yearly_loads[self.yearly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = self.remove_unused_fields(self.data, ["DH_hs_MWhyr", "DH_ww_MWhyr", 'SOLAR_ww_MWhyr',
                                                                     'SOLAR_hs_MWhyr', "DC_cs_MWhyr", 'DC_cdata_MWhyr',
                                                                     'DC_cre_MWhyr', 'PV_MWhyr', 'GRID_MWhyr',
                                                                     'NG_hs_MWhyr', 'COAL_hs_MWhyr', 'OIL_hs_MWhyr',
                                                                     'WOOD_hs_MWhyr', 'NG_ww_MWhyr', 'COAL_ww_MWhyr',
                                                                     'OIL_ww_MWhyr', 'WOOD_ww_MWhyr', ])
        self.layout = go.Layout(barmode='stack',
                                yaxis=dict(title='Energy Supply Intensity [kWh/m2.yr]'), showlegend=True)

    def calc_graph(self):
        if len(self.buildings) == 1:
            assert len(self.data) == 1, 'Expected DataFrame with only one row'
            building_data = self.data.iloc[0]
            traces = []
            area = building_data["GFA_m2"]
            x = ["Absolute [MWh/yr]", "Relative [kWh/m2.yr]"]
            for field in self.analysis_fields:
                name = NAMING[field]
                y = [building_data[field], building_data[field] / area * 1000]
                trace = go.Bar(x=x, y=y, name=name, marker=dict(color=COLOR[field]))
                traces.append(trace)
            return traces
        else:
            # district version of this plot
            traces = []
            self.data['total'] = self.data[self.analysis_fields].sum(axis=1)
            for field in self.analysis_fields:
                self.data[field] = self.data[field] * 1000 / self.data["GFA_m2"]  # in kWh/m2y
                self.data = self.data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
            x = self.data["Name"].tolist()
            for field in self.analysis_fields:
                y = self.data[field]
                name = NAMING[field]
                trace = go.Bar(x=x, y=y, name=name, marker=dict(color=COLOR[field]))
                traces.append(trace)
            return traces


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergySupplyIntensityPlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    EnergySupplyIntensityPlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    EnergySupplyIntensityPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)