



import plotly.graph_objs as go
import pandas as pd

from cea.plots.variable_naming import NAMING, COLOR
import cea.plots.lifecycle

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class AnnualEmissionsPlot(cea.plots.lifecycle.LifecyclePlotBase):
    """Implement the "CAPEX vs. OPEX of a building system"""
    name = "Annualized Emissions"
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'normalization': 'plots-schedules:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(AnnualEmissionsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["GHG_sys_district_scale_tonCO2",
                                "GHG_sys_building_scale_tonCO2",
                                "GHG_sys_embodied_tonCO2",
                                ]
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_lca_embodied, []),
                            (self.locator.get_lca_operation, [])]
        self.titley = self.calc_titles()

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Annual emissions [kg CO2-eq/m2.yr]'
        elif self.normalization == "net floor area":
            titley = 'Annual emissions [kg CO2-eq/m2.yr]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Annual emissions [kg CO2-eq/m2.yr]'
        elif self.normalization == "building occupancy":
            titley = 'Annual emissions [kg CO2-eq/p.yr]'
        else:
            titley = 'Annual emissions [ton CO2-eq/yr]'
        return titley

    @property
    def title(self):
        """Override the version in PlotBase"""
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                return "%s for Building %s " % (self.name, self.buildings[0])
            else:
                return "%s for Selected Buildings" % (self.name)
        return "%s for District" % (self.name)

    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.titley))

    @cea.plots.cache.cached
    def data_building(self):
        data_embodied = pd.read_csv(self.locator.get_lca_embodied())
        data_operations = pd.read_csv(self.locator.get_lca_operation())
        all_data = data_embodied.merge(data_operations, on="Name").set_index('Name')
        if len(self.buildings) == 1:
            data_raw_df = pd.DataFrame(all_data.loc[self.buildings]).T
        else:
            data_raw_df = pd.DataFrame(all_data.loc[self.buildings])
        data_normalized = self.normalize_data(data_raw_df, self.normalization, self.analysis_fields)
        return data_normalized

    def calc_graph(self):
        data = self.data_building()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()
    AnnualEmissionsPlot(config.project,
                    {'buildings': locator.get_zone_building_names(),
                     'scenario-name': config.scenario_name},
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
