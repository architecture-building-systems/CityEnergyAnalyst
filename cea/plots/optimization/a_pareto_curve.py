"""
Show a Pareto curve plot for individuals in a given generation.
"""




import plotly.graph_objs as go

import cea.plots.optimization

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi", "Daren Thomas", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ParetoCurveForOneGenerationPlot(cea.plots.optimization.GenerationPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Pareto curve"
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'normalization': 'plots:normalization',
        'scenario-name': 'general:scenario-name',
        'annualized-capital-costs': 'multi-criteria:annualized-capital-costs',
        'total-capital-costs': 'multi-criteria:total-capital-costs',
        'annual-operation-costs': 'multi-criteria:annual-operation-costs',
        'annual-emissions': 'multi-criteria:annual-emissions',
    }

    def __init__(self, project, parameters, cache):
        super(ParetoCurveForOneGenerationPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ['individual_name',
                                'TAC_sys_USD',
                                'GHG_sys_tonCO2',
                                'Capex_total_sys_USD',
                                'Opex_a_sys_USD']
        self.objectives = ['TAC_sys_USD', 'GHG_sys_tonCO2', 'Capex_total_sys_USD']
        self.normalization = self.parameters['normalization']
        self.input_files = [(self.locator.get_optimization_generation_total_performance_pareto, [self.generation])]
        self.titlex, self.titley, self.titlez = self.calc_titles()
        self.weight_annualized_capital_costs = self.parameters['annualized-capital-costs']
        self.weight_total_capital_costs = self.parameters['total-capital-costs']
        self.weight_annual_operation_costs = self.parameters['annual-operation-costs']
        self.weight_annual_emissions = self.parameters['annual-emissions']

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titlex = 'Equivalent annual costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
        elif self.normalization == "net floor area":
            titlex = 'Equivalent annual costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
        elif self.normalization == "air conditioned floor area":
            titlex = 'Equivalent annual costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2.yr]'
        elif self.normalization == "building occupancy":
            titlex = 'Equivalent annual costs [USD$(2015)/p.yr]'
            titley = 'GHG emissions [kg CO2-eq/p.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/p]'
        else:
            titlex = 'Equivalent annual costs [USD$(2015)/yr]'
            titley = 'GHG emissions [ton CO2-eq/yr]'
            titlez = 'Investment costs <br>[USD$(2015)]'

        return titlex, titley, titlez

    @property
    def layout(self):
        return go.Layout(legend=dict(orientation="v", x=0.8, y=0.95),
                         xaxis=dict(title=self.titlex),
                         yaxis=dict(title=self.titley))

    @property
    def title(self):
        if self.normalization != "none":
            return "Pareto curve for best individuals after {generation} {generation_noun} normalized to {normalized}".format(
                generation=self.generation, normalized=self.normalization, generation_noun=self.generation_noun)
        else:
            return "Pareto curve for best individuals after {generation} {generation_noun}".format(
                generation=self.generation, generation_noun=self.generation_noun)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('gen{generation}_pareto_curve'.format(generation=self.generation),
                                                      self.category_name)

    def calc_graph(self):
        graph = []

        # This includes the point of today's emissions
        data_today = self.process_today_system_performance()
        data_today = self.normalize_data(data_today, self.normalization, self.objectives)
        xs = data_today[self.objectives[0]].values
        ys = data_today[self.objectives[1]].values
        name = "Today"
        trace = go.Scattergl(x=xs, y=ys, mode='markers', name="Today's system", text=name,
                             marker=dict(size=18, color='black', line=dict(color='black',width=2)))
        graph.append(trace)

        # PUT THE PARETO CURVE INSIDE
        data = self.process_generation_total_performance_pareto_with_multi()
        data = self.normalize_data(data, self.normalization, self.objectives)
        xs = data[self.objectives[0]].values
        ys = data[self.objectives[1]].values
        zs = data[self.objectives[2]].values

        individual_names = data['individual_name'].values

        trace = go.Scattergl(x=xs, y=ys, mode='markers', name='Pareto optimal systems', text=individual_names,
                             marker=dict(size=18, color=zs,
                                         colorbar=go.scattergl.marker.ColorBar(title=self.titlez, titleside='bottom'),
                                         colorscale='Jet', showscale=True, opacity=0.8))
        graph.append(trace)

        # This includes the points of the multicriteria assessment in here
        final_dataframe = calc_final_dataframe(data)
        xs = final_dataframe[self.objectives[0]].values
        ys = final_dataframe[self.objectives[1]].values
        name = final_dataframe["Attribute"].values
        trace = go.Scattergl(x=xs, y=ys, mode='markers', name="Multi-criteria system", text=name,
                             marker=dict(size=18, color='white', line=dict(
                                 color='black',
                                 width=2)))
        graph.append(trace)

        return graph


def calc_final_dataframe(individual_data):
    user_defined_mcda = individual_data.loc[individual_data["user_MCDA_rank"] < 2]
    # FIXME: comment out as the action is unclear and the dataframe shape does not match the expected outputs
    # if user_defined_mcda.shape[0] > 1:
    #     individual = str(user_defined_mcda["individual_name"].values)
    #     user_defined_mcda = user_defined_mcda.reset_index(drop=True)
    #     user_defined_mcda = user_defined_mcda.iloc[0].T
    #     user_defined_mcda["System option"] = individual
    # Now extend all dataframes
    final_dataframe = user_defined_mcda.copy()
    final_dataframe.reset_index(drop=True, inplace=True)
    final_dataframe["Attribute"] = "user defined MCDA"
    return final_dataframe


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ParetoCurveForOneGenerationPlot(config.project,
                                    {'scenario-name': config.scenario_name,
                                     'generation': config.plots_optimization.generation,
                                     'normalization': config.plots.normalization,
                                     'annualized-capital-costs': config.multi_criteria.annualized_capital_costs,
                                     'total-capital-costs': config.multi_criteria.total_capital_costs,
                                     'annual-operation-costs': config.multi_criteria.annual_operation_costs,
                                     'annual-emissions': config.multi_criteria.annual_emissions,
                                     },
                                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
