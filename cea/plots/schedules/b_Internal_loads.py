



import plotly.graph_objs as go

import cea.plots.schedules
from cea.plots.variable_naming import COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class InternalLoadsPlot(cea.plots.schedules.SchedulesPlotBase):
    """implements the solar-radiation-curve plot"""
    name = "Internal Loads"

    def __init__(self, project, parameters, cache):
        """Override the version in OccupancyPlotBase"""
        super(InternalLoadsPlot, self).__init__(project, parameters, cache)
        self.schedule_analysis_fields = ['Ql_W',
                                      'Qs_W',
                                      'Ea_W',
                                      'El_W',
                                      'Ed_W',
                                      'Qcpro_W',
                                      'Epro_W',
                                      'Qcre_W',
                                      'Qhpro_W']

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Internal Loads [W/m2]'
        elif self.normalization == "net floor area":
            titley = 'Internal Loads [W/m2]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Internal Loads [W/m2]'
        elif self.normalization == "building occupancy":
            titley = 'Internal Loads [W/p]'
        else:
            titley = 'Internal Loads [kW]'
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
                    return "%s for Building %s (%s)" % (self.name, self.buildings[0], self.timeframe)
                else:
                    return "%s for Building %s normalized to %s (%s)" % (
                        self.name, self.buildings[0], self.normalization, self.timeframe)
            else:
                if self.normalization == "none":
                    return "%s for Selected Buildings (%s)" % (self.name, self.timeframe)
                else:
                    return "%s for Selected Buildings normalized to %s (%s)" % (
                        self.name, self.normalization, self.timeframe)
        else:
            if self.normalization == "none":
                return "%s for District (%s)" % (self.name, self.timeframe)
            else:
                return "%s for District normalized to %s (%s)" % (self.name, self.normalization, self.timeframe)

    def calc_graph(self):
        data = self.schedule_data_aggregated()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.schedule_analysis_fields)
        for field in analysis_fields:
            if self.normalization != "none":
                y = data[field].values  # in W
            else:
                y = data[field].values / 1E3 # in kW

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
    cache = cea.plots.cache.NullPlotCache()
    InternalLoadsPlot(config.project, {'buildings': None,
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots_schedules.normalization},
                       cache).plot(auto_open=True)
    InternalLoadsPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots_schedules.normalization},
                       cache).plot(auto_open=True)
    InternalLoadsPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots_schedules.normalization},
                       cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
