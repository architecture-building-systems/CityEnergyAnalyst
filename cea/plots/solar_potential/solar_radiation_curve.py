from __future__ import division

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING
import cea.plots.solar_potential

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class SolarRadiationCurvePlot(cea.plots.solar_potential.SolarPotentialPlotBase):
    """implements the solar-radiation-curve plot"""
    name = "Solar radiation curve"

    @property
    def layout(self):
        return dict(
                    yaxis=dict(title='Solar Radiation [kW]'),
                    yaxis2=dict(title='Temperature [C]', overlaying='y', side='right'))
    def calc_graph(self):
        graph = []
        data_frame = self.input_data_aggregated_kW
        analysis_fields = self.analysis_fields + ["T_ext_C"]
        x = data_frame.DATE
        for field in analysis_fields:
            y = data_frame[field].values
            name = NAMING[field]
            if field == "T_ext_C":
                trace = go.Scattergl(x=x, y=y, name=name, yaxis='y2', opacity=0.2)
            else:
                trace = go.Scattergl(x=x, y=y, name=name,
                                   marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph

def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    import cea.plots.cache
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    weather_path = locator.get_weather_file()
    SolarRadiationCurvePlot(config.project, {'buildings': None,
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)
    SolarRadiationCurvePlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)
    SolarRadiationCurvePlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
