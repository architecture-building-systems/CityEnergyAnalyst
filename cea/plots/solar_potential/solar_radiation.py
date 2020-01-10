from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.solar_potential
from cea.plots.variable_naming import COLOR

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SolarRadiationPlot(cea.plots.solar_potential.SolarPotentialPlotBase):
    """Implement the solar-radiation-per-building plot"""
    name = "Solar radiation per building"

    @property
    def layout(self):
        return go.Layout(title=self.title, barmode='stack',
                         yaxis=dict(title='Solar radiation [MWh/yr]'),
                         xaxis=dict(title='Building'))

    def calc_graph(self):
        # calculate graph
        graph = []
        data_frame = self.input_data_not_aggregated_MW
        data_frame['total'] = data_frame[self.analysis_fields].sum(axis=1)
        data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in self.analysis_fields:
            y = data_frame[field]
            total_perc = (y / data_frame['total'] * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace = go.Bar(x=data_frame["Name"], y=y, name=field, text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    weather_path = locator.get_weather_file()
    SolarRadiationPlot(config.project, {'buildings': None,
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
