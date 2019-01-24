from __future__ import division
from __future__ import print_function

import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR
import cea.plots.demand

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class HeatingResetSchedulePlot(cea.plots.demand.DemandPlotBase):
    name = "Heating Reset Schedule"

    def __init__(self, project, parameters):
        super(HeatingResetSchedulePlot, self).__init__(project, parameters)
        if len(self.buildings) > 1:
            self.buildings = [self.buildings[0]]
        self.data = self.hourly_loads[self.hourly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = ["Tww_sys_sup_C", "Tww_sys_re_C", 'Tcs_sys_re_ahu_C', 'Tcs_sys_re_aru_C',
                                'Tcs_sys_re_scu_C', 'Tcs_sys_sup_ahu_C', 'Tcs_sys_sup_aru_C', 'Tcs_sys_sup_scu_C',
                                'Ths_sys_re_ahu_C', 'Ths_sys_re_aru_C', 'Ths_sys_re_shu_C', 'Ths_sys_sup_ahu_C',
                                'Ths_sys_sup_aru_C', 'Ths_sys_sup_shu_C', ]
        self.layout = go.Layout(xaxis=dict(title='Outdoor Temperature [C]'),
                                yaxis=dict(title='HVAC System Temperature [C]'))

    def calc_graph(self):
        traces = []
        x = self.data["T_ext_C"].values
        self.data = self.data.replace(0, np.nan)
        for field in self.analysis_fields:
            y = self.data [field].values
            name = NAMING[field]
            trace = go.Scatter(x=x, y=y, name=name, mode='markers', marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces

def heating_reset_schedule(data_frame, analysis_fields, title, output_path):
    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    x = data_frame["T_ext_C"].values
    data_frame = data_frame.replace(0, np.nan)
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        trace = go.Scatter(x=x, y=y, name=name, mode='markers',
                           marker=dict(color=COLOR[field]))
        traces.append(trace)

    layout = go.Layout(images=LOGO, title=title,
                       xaxis=dict(title='Outdoor Temperature [C]'),
                       yaxis=dict(title='HVAC System Temperature [C]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    HeatingResetSchedulePlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)
    HeatingResetSchedulePlot(config, locator, [locator.get_zone_building_names()[1]]).plot(auto_open=True)
    HeatingResetSchedulePlot(config, locator, [locator.get_zone_building_names()[2]]).plot(auto_open=True)