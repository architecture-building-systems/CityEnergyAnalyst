from __future__ import division

import plotly.graph_objs as go

import cea.plots.solar_potential
from cea.plots.variable_naming import COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SolarRadiationPlot(cea.plots.solar_potential.SolarPotentialPlotBase):
    """implements the solar-radiation-curve plot"""
    name = "Solar radiation"

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Solar radiation [kWh/m2]'
        elif self.normalization == "net floor area":
            titley = 'Solar radiation [kWh/m2]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Solar radiation [kWh/m2]'
        elif self.normalization == "surface area":
            titley = 'Solar radiation [kWh/m2]'
        elif self.normalization == "building occupancy":
            titley = 'Solar radiation [kWh/pax]'
        else:
            titley = 'Solar radiation [MWh]'
        return titley

    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.calc_titles()))

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
        data = self.solar_hourly_aggregated_kW()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.solar_analysis_fields)
        for field in analysis_fields:
            if self.normalization != "none":
                y = data[field].values  # in kW
            else:
                y = data[field].values / 1E3  # to MW

            name = NAMING[field]
            trace = go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]))
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
    SolarRadiationPlot(config.project, {'buildings': None,
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots.normalization},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots.normalization},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots.normalization},
                       cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
