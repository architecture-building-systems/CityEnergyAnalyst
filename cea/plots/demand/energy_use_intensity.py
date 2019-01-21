from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import cea.plots.demand
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EnergyUseIntensityPlot(cea.plots.demand.DemandPlotBase):
    name = "Energy Use Intensity"

    def __init__(self, project, parameters):
        super(EnergyUseIntensityPlot, self).__init__(project, parameters)
        self.data = self.yearly_loads[self.yearly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = ["E_sys_MWhyr",
                                "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        self.layout = go.Layout(barmode='stack',
                                yaxis=dict(title='Energy Use Intensity [kWh/m2.yr]'), showlegend=True)

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

def energy_use_intensity(data_frame, analysis_fields, title, output_path):
    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    area = data_frame["GFA_m2"]
    x = ["Absolute [MWh/yr]", "Relative [kWh/m2.yr]"]
    for field in analysis_fields:
        name = NAMING[field]
        y = [data_frame[field], data_frame[field] / area * 1000]
        trace = go.Bar(x=x, y=y, name=name,
                       marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title, barmode='stack', showlegend=True)
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def energy_use_intensity_district(data_frame, analysis_fields, title, output_path):
    traces = []
    data_frame_copy = data_frame.copy()  # make a copy to avoid passing new data of the dataframe around the class
    for field in analysis_fields:
        data_frame_copy[field] = data_frame_copy[field] * 1000 / data_frame_copy["GFA_m2"]  # in kWh/m2y
        data_frame_copy['total'] = data_frame_copy[analysis_fields].sum(axis=1)
        data_frame_copy = data_frame_copy.sort_values(by='total',
                                                      ascending=False)  # this will get the maximum value to the left
    x = data_frame_copy["Name"].tolist()
    for field in analysis_fields:
        y = data_frame_copy[field]
        name = NAMING[field]
        trace = go.Bar(x=x, y=y, name=name, marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='Energy Use Intensity [kWh/m2.yr]'),
                       showlegend=True)
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergyUseIntensityPlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    EnergyUseIntensityPlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    EnergyUseIntensityPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)