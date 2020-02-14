from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.technology_potentials
from cea.plots.variable_naming import COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SCETPotentialPlot(cea.plots.technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Implement the pv-electricity-potential plot"""

    name = "Solar Collector (ET) Potential"

    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
        'normalization': 'plots:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(SCETPotentialPlot, self).__init__(project, parameters, cache)
        self.timeframe = self.parameters['timeframe']
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.SC_results, [building, 'ET']) for building in self.buildings]

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Thermal Energy [kWh/m2]'
        elif self.normalization == "net floor area":
            titley = 'Thermal Energy [kWh/m2]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Thermal Energy [kWh/m2]'
        elif self.normalization == "surface area":
            titley = 'Thermal Energy[kWh/m2]'
        elif self.normalization == "building occupancy":
            titley = 'Thermal Energy [kWh/pax]'
        else:
            titley = 'Thermal Energy [MWh]'
        return titley

    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.calc_titles()), showlegend=True)

    @property
    def title(self):
        """Override the version in PlotBase"""
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                if self.normalization == "none":
                    return "%s for Building %s " % (self.name, self.buildings[0])
                else:
                    return "%s for Building %s normalized to %s" % (self.name, self.buildings[0], self.normalization)
            else:
                if self.normalization == "none":
                    return "%s for Selected Buildings" % self.name
                else:
                    return "%s for Selected Buildings normalized to %s" % (self.name, self.normalization)
        else:
            if self.normalization == "none":
                return "%s for District" % self.name
            else:
                return "%s for District normalized to %s" % (self.name, self.normalization)

    def calc_graph(self):
        data = self.SC_ET_hourly_aggregated_kW()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.sc_et_analysis_fields)
        for field in analysis_fields:
            if self.normalization != "none":
                y = data[field].values  # in kW
            else:
                y = data[field].values / 1E3  # to MW

            name = NAMING[field]
            trace = go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]),showlegend=True)
            traces.append(trace)
        return traces


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    import cea.plots.cache
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    SCETPotentialPlot(config.project, {'buildings': None,
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                      cache).plot(auto_open=True)
    SCETPotentialPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                      cache).plot(auto_open=True)
    SCETPotentialPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
