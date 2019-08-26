from __future__ import division
from __future__ import print_function

import os
import plotly.graph_objs as go
from plotly.offline import plot
import cea.plots.solar_technology_potentials
from cea.plots.variable_naming import LOGO, COLOR

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class AllTechHourlyPlot(cea.plots.solar_technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Implement the pv-electricity-potential plot"""
    name = "PV/SC/PVT Potential"

    def __init__(self, project, parameters, cache):
        super(AllTechHourlyPlot, self).__init__(project, parameters, cache)
        self.map_technologies = {  # tech-name: (locator_method, args, data_attribute)
            'PV': (self.locator.PV_totals, [], 'PV_hourly_aggregated_kW'),
            'PVT': (self.locator.PVT_totals, [], 'PVT_hourly_aggregated_kW'),
            'SC_ET': (self.locator.SC_totals, ['ET'], 'SC_ET_hourly_aggregated_kW'),
            'SC_FP': (self.locator.SC_totals, ['FP'], 'SC_FP_hourly_aggregated_kW')
        }
        self.input_files = [self.map_technologies[t][:2] for t in self.map_technologies.keys()]
        self.__data_frame = None

    @property
    def layout(self):
        return dict(yaxis=dict(title='Hourly production [kWh]'))

    def missing_input_files(self):
        """Overriding the base version of this method, since for this plot, having at least one technology
        available is ok."""
        result = super(AllTechHourlyPlot, self).missing_input_files()
        if len(result) < len(self.input_files):
            # we know _at least_ some of the simulations have been made already, we can plot this
            return []
        return result

    @property
    def data_frame(self):
        """Combine all the (available) hourly tech data_frames by inner join"""
        if self.__data_frame is None:
            data_frame_list = [getattr(self, t[2]).set_index('DATE') for t in self.map_technologies.values()
                               if os.path.exists(t[0](*t[1]))]
            self.__data_frame = reduce(lambda ldf, rdf: ldf.join(rdf, how='inner', on='DATE'), data_frame_list)
        return self.__data_frame

    def calc_graph(self):
        graph = []
        data_frame = self.data_frame
        analysis_fields = [f for f in data_frame.columns if f.endswith('_kWh')]
        for field in analysis_fields:
            y = data_frame[field].values
            name = field.split('_kWh', 1)[0]
            if name.startswith('PV_'):
                trace = go.Scatter(x=data_frame.index, y=y, name=name, marker=dict(color=COLOR[field]))
            else:
                trace = go.Scatter(x=data_frame.index, y=y, name=name, visible='legendonly',
                                   marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph


def all_tech_district_hourly(data_frame, all_tech_analysis_fields, title, output_path):
    traces = []
    data_frame = data_frame.set_index('DATE')
    for tech in all_tech_analysis_fields:
        analysis_fields = all_tech_analysis_fields[tech]
        for field in analysis_fields:
            y = data_frame[field].values
            name = field.split('_kWh', 1)[0]
            if tech == 'PV':
                trace = go.Scatter(x=data_frame.index, y=y, name=name, marker=dict(color=COLOR[field]))
            else:
                trace = go.Scatter(x=data_frame.index, y=y, name=name, visible='legendonly',
                                   marker=dict(color=COLOR[field]))
            traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Hourly production [kWh]'),
                  xaxis=dict(rangeselector=dict(buttons=list([
                      dict(count=1, label='1d', step='day', stepmode='backward'),
                      dict(count=1, label='1w', step='week', stepmode='backward'),
                      dict(count=1, label='1m', step='month', stepmode='backward'),
                      dict(count=6, label='6m', step='month', stepmode='backward'),
                      dict(count=1, label='1y', step='year', stepmode='backward'),
                      dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.index[0],
                                                                                   data_frame.index[168]],
                      fixedrange=False))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    import cea.plots.cache
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()
    weather_path = locator.get_weather_file()
    AllTechHourlyPlot(config.project, {'buildings': None,
                                       'scenario-name': config.scenario_name,
                                       'weather': weather_path},
                      cache).plot(auto_open=True)
    AllTechHourlyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                       'scenario-name': config.scenario_name,
                                       'weather': weather_path},
                      cache).plot(auto_open=True)
    AllTechHourlyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                       'scenario-name': config.scenario_name,
                                       'weather': weather_path},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()

