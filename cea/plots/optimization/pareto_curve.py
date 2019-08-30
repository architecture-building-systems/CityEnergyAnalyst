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
    name = "Costs, emissions and primary energy"

    def __init__(self, project, parameters, cache):
        super(ParetoCurveForOneGenerationPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ['individual_name',
                                'TAC_sys_USD',
                                'GHG_sys_tonCO2',
                                'PEN_sys_MJoil',
                                'Capex_total_sys_USD',
                                'Opex_a_sys_USD']
        self.objectives = ['TAC_sys_USD', 'GHG_sys_tonCO2', 'PEN_sys_MJoil']
        self.input_files = [(self.locator.get_optimization_generation_total_performance, [self.generation])]
        self.multi_criteria = self.parameters['multicriteria']

    @property
    def layout(self):
        data = self.process_generation_total_performance()
        xs = data[self.objectives[0]].values
        ys = data[self.objectives[1]].values
        zs = data[self.objectives[2]].values
        xmin = min(xs)
        ymin = min(ys)
        zmin = min(zs)
        xmax = max(xs)
        ymax = max(ys)
        zmax = max(zs)
        ranges_some_room_for_graph = [[xmin - ((xmax - xmin) * 0.1), xmax + ((xmax - xmin) * 0.1)],
                                      [ymin - ((ymax - ymin) * 0.1), ymax + ((ymax - ymin) * 0.1)], [zmin, zmax]]
        return go.Layout(legend=dict(orientation="v", x=0.8, y=0.7),
                         xaxis=dict(title='Total annualized costs [USD$(2015)/yr]', domain=[0, 1],
                                    range=ranges_some_room_for_graph[0]),
                         yaxis=dict(title='GHG emissions [ton CO2-eq]', domain=[0.3, 1.0],
                                    range=ranges_some_room_for_graph[1]))


    @property
    def title(self):
        return "Costs, emissions, and primary energy"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('gen{generation}_pareto_curve'.format(generation=self.generation),
                                                      self.category_name)

    def calc_graph(self):
        data = self.process_generation_total_performance()
        xs = data[self.objectives[0]].values
        ys = data[self.objectives[1]].values
        zs = data[self.objectives[2]].values
        individual_names = data['individual_name'].values


        graph = []
        trace = go.Scatter(x=xs, y=ys, mode='markers', name='data', text=individual_names,
                           marker=dict(size='12', color=zs,
                                       colorbar=go.ColorBar(title='Primary Energy [MJoil]', titleside='bottom'),
                                       colorscale='Jet', showscale=True, opacity=0.8))
        graph.append(trace)

        # This includes the points of the multicriteria assessment in here
        if self.multi_criteria:
            # Insert scatter points of MCDA assessment.
            final_dataframe = calc_final_dataframe(data)
            xs = final_dataframe[self.objectives[0]].values
            ys = final_dataframe[self.objectives[1]].values
            name = final_dataframe["Attribute"].values
            trace = go.Scatter(x=xs, y=ys, mode='markers', name="multi-criteria-analysis", text=name,
                               marker=dict(size='20', color='white', line=dict(
                                   color='black',
                                   width=2)))
            graph.append(trace)

        return graph

    # def calc_table(self):
    #     final_dataframe = calc_final_dataframe(self.process_generation_total_performance())
    #
    #     # transform data into currency
    #     for column in final_dataframe.columns:
    #         if '_USD' in column or '_MJoil' in column or '_tonCO2' in column:
    #             final_dataframe[column] = final_dataframe[column].apply(lambda x: '{:20,.2f}'.format(x))
    #
    #     columns = ["Attribute"] + self.analysis_fields
    #     values = []
    #     for field in columns:
    #         if field in ["Attribute", "individual_name"]:
    #             values.append(final_dataframe[field].values)
    #         else:
    #             values.append(final_dataframe[field].values)
    #
    #     columns = ["Attribute"] + [NAMING[field] for field in self.analysis_fields]
    #     table_df = pd.DataFrame({cn: cv for cn, cv in zip(columns, values)}, columns=columns)
    #     return table_df


def calc_final_dataframe(individual_data):
    least_annualized_cost = individual_data.loc[
        individual_data["TAC_rank"] < 2]  # less than two because in the case there are two individuals MCDA calculates 1.5
    least_emissions = individual_data.loc[individual_data["GHG_rank"] < 2]
    least_primaryenergy = individual_data.loc[individual_data["PEN_rank"] < 2]
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
    if least_primaryenergy.shape[0] > 1:
        individual = str(least_primaryenergy["individual_name"].values)
        least_primaryenergy = least_primaryenergy.reset_index(drop=True)
        least_primaryenergy = least_primaryenergy.iloc[0].T
        least_primaryenergy["System option"] = individual
    if user_defined_mcda.shape[0] > 1:
        individual = str(user_defined_mcda["individual_name"].values)
        user_defined_mcda = user_defined_mcda.reset_index(drop=True)
        user_defined_mcda = user_defined_mcda.iloc[0].T
        user_defined_mcda["System option"] = individual
    # Now extend all dataframes
    final_dataframe = least_annualized_cost.append(least_emissions).append(least_primaryenergy).append(
        user_defined_mcda)
    final_dataframe.reset_index(drop=True, inplace=True)
    final_dataframe["Attribute"] = ["least annualized costs", "least emissions", "least primary energy",
                                    "user defined MCDA"]
    return final_dataframe


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ParetoCurveForOneGenerationPlot(config.project,
                                    {'buildings': None,
                                     'scenario-name': config.scenario_name,
                                     'generation': config.plots_optimization.generation,
                                     'multicriteria': config.plots_optimization.multicriteria},
                                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
