



import plotly.graph_objs as go

import cea.plots.comparisons
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ComparisonsAnnualEmissionsPlot(cea.plots.comparisons.ComparisonsPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Annualized emissions"

    def __init__(self, project, parameters, cache):
        super(ComparisonsAnnualEmissionsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["GHG_sys_district_scale_tonCO2",
                                "GHG_sys_building_scale_tonCO2",
                                "GHG_sys_embodied_tonCO2yr",
                                ]
        self.normalization = self.parameters['normalization']
        self.input_files = [(x[4].get_optimization_slave_total_performance, [x[3], x[2]]) if x[2] != "today" else
                            (x[4].get_lca_embodied, []) for x in self.scenarios_and_systems]
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
        if self.normalization != "none":
            return "Annual Emissions per Scenario normalized to {normalized}".format(normalized=self.normalization)
        else:
            return "Annual Emissions per Scenario"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('scenarios_annualized_emissions')

    @property
    def layout(self):
        return go.Layout(barmode='relative',
                         yaxis=dict(title=self.titley))

    def calc_graph(self):
        data = self.preprocessing_annual_emissions_scenarios()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data['scenario_name'], y=y, name=NAMING[field],
                               marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ComparisonsAnnualEmissionsPlot(config.project,
                                   {'scenarios-and-systems': config.plots_comparisons.scenarios_and_systems,
                                    'normalization': config.plots.normalization},
                                   cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
