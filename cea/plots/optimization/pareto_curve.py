"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
import plotly.graph_objs as go

import cea.plots.optimization
from cea.plots.variable_naming import NAMING

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi", "Daren Thomas"]
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
        'normalization': 'plots-optimization:normalization',
        'multicriteria': 'plots-optimization:multicriteria',
        'scenario-name': 'general:scenario-name',
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
        self.input_files = [(self.locator.get_optimization_generation_total_performance, [self.generation])]
        self.multi_criteria = self.parameters['multicriteria']
        self.titlex, self.titley, self.titlez = self.calc_titles()

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titlex = 'Total annualized costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
        elif self.normalization == "net floor area":
            titlex = 'Total annualized costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2]'
        elif self.normalization == "air conditioned floor area":
            titlex = 'Total annualized costs [USD$(2015)/m2.yr]'
            titley = 'GHG emissions [kg CO2-eq/m2.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/m2.yr]'
        elif self.normalization == "building occupancy":
            titlex = 'Total annualized costs [USD$(2015)/pax.yr]'
            titley = 'GHG emissions [kg CO2-eq/pax.yr]'
            titlez = 'Investment costs <br>[USD$(2015)/pax]'
        else:
            titlex = 'Total annualized costs [USD$(2015)/yr]'
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
            return "Pareto curve for generation {generation} normalized to {normalized}".format(generation=self.generation, normalized=self.normalization)
        else:
            return "Pareto curve for generation {generation}".format(generation=self.generation)


    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('gen{generation}_pareto_curve'.format(generation=self.generation),
                                                      self.category_name)

    def calc_graph(self):
        graph = []

        # PUT THE PARETO CURVE INSIDE
        data = self.process_generation_total_performance_pareto_with_multi()
        data = self.normalize_data(data, self.normalization, self.objectives)
        xs = data[self.objectives[0]].values
        ys = data[self.objectives[1]].values
        zs = data[self.objectives[2]].values

        individual_names = data['individual_name'].values

        trace = go.Scattergl(x=xs, y=ys, mode='markers', name='Pareto curve', text=individual_names,
                           marker=dict(size='12', color=zs,
                                       colorbar=go.ColorBar(title=self.titlez, titleside='bottom'),
                                       colorscale='Jet', showscale=True, opacity=0.8))
        graph.append(trace)

        # This includes the points of the multicriteria assessment in here
        if self.multi_criteria:
            # Insert scatter points of MCDA assessment.
            final_dataframe = calc_final_dataframe(data)
            xs = final_dataframe[self.objectives[0]].values
            ys = final_dataframe[self.objectives[1]].values
            name = final_dataframe["Attribute"].values
            trace = go.Scattergl(x=xs, y=ys, mode='markers', name="Selected by Multi-criteria", text=name,
                               marker=dict(size='20', color='white', line=dict(
                                   color='black',
                                   width=2)))
            graph.append(trace)
        return graph

def calc_final_dataframe(individual_data):
    least_annualized_cost = individual_data.loc[
        individual_data["TAC_rank"] < 2]  # less than two because in the case there are two individuals MCDA calculates 1.5
    least_emissions = individual_data.loc[individual_data["GHG_rank"] < 2]
    user_defined_mcda = individual_data.loc[individual_data["user_MCDA_rank"] < 2]
    # do a check in the case more individuals had the same ranking.
    if least_annualized_cost.shape[0] > 1:
        individual = str(least_annualized_cost["individual_name"].values)
        least_annualized_cost = least_annualized_cost.reset_index(drop=True)
        least_annualized_cost = least_annualized_cost[:1]
        least_annualized_cost["System option"] = individual
    if least_emissions.shape[0] > 1:
        individual = str(least_emissions["individual_name"].values)
        least_emissions = least_emissions.reset_index(drop=True)
        least_emissions = least_emissions.iloc[0].T
        least_emissions["System option"] = individual
    if user_defined_mcda.shape[0] > 1:
        individual = str(user_defined_mcda["individual_name"].values)
        user_defined_mcda = user_defined_mcda.reset_index(drop=True)
        user_defined_mcda = user_defined_mcda.iloc[0].T
        user_defined_mcda["System option"] = individual
    # Now extend all dataframes
    final_dataframe = least_annualized_cost.append(least_emissions).append(
        user_defined_mcda)
    final_dataframe.reset_index(drop=True, inplace=True)
    final_dataframe["Attribute"] = ["least annualized costs",
                                    "least emissions",
                                    "user defined MCDA"]
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
                                     'multicriteria': config.plots_optimization.multicriteria,
                                     'normalization': config.plots_optimization.normalization},
                                    cache).plot(auto_open=True)
if __name__ == '__main__':
    main()
