from __future__ import division
from __future__ import print_function

from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO, COLOR, NAMING
import cea.plots.demand


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

    def __init__(self, project, parameters):
        super(LoadCurvePlot, self).__init__(project, parameters)
        self.data = self.hourly_loads
        self.analysis_fields = ["E_sys_kWh",
                                "Qhs_sys_kWh", "Qww_sys_kWh",
                                "Qcs_sys_kWh", 'Qcdata_sys_kWh', 'Qcre_sys_kWh']
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


def load_curve(data_frame, analysis_fields, title, output_path):

    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        if field in ["T_int_C", "T_ext_C"]:
            trace = go.Scatter(x=data_frame.index, y= y, name = name, yaxis='y2', opacity = 0.2)
        else:
            trace = go.Scatter(x=data_frame.index, y= y, name = name,
                               marker=dict(color=COLOR[field]))

        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Load [kW]'), yaxis2=dict(title='Temperature [C]', overlaying='y',
                   side='right'),xaxis=dict(rangeselector=dict(buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all')])),rangeslider=dict(),type='date',range= [data_frame.index[0],
                                                                                 data_frame.index[168]],
                                                                          fixedrange=False))

    fig = dict(data=traces, layout=layout)
    plot(fig,  auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    LoadCurvePlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    LoadCurvePlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    LoadCurvePlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)
