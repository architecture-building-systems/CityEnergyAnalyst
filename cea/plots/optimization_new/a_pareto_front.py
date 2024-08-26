"""
Print the set of non-dominated solutions identified by the optimization algorithm. This plot integrates an option
to chose the objective function space in which the solutions are plotted. The user must chose exactly 2  of the
objective functions used to run the optimization.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


import csv
import os
import pandas as pd
import plotly.graph_objects as go

import cea.config
from cea.inputlocator import InputLocator


def read_objective_values(file_path):
    """
    Read the objective function and the solution's objective function values from the optimization results file.
    """
    with open(file_path, 'r') as file:
        # Read the file
        reader = csv.reader(file)
        headers = next(reader)  # Read header row
        objectives = headers[1:] # Get the objective function names

        # Read the objective function values
        for row in reader:
            if row[0] == 'Total':
                values = [float(value) for value in row[1:]]

        return objectives, values

def read_network_costs(file_path):
    """
    Read the network costs from the detailed optimization results file.
    """
    if not os.path.isfile(file_path):
        return 0

    with open(file_path, 'r') as file:
        # Read the file
        reader = csv.reader(file)
        network_data_headers = next(reader)  # Read header row
        cost_column = network_data_headers.index('Network cost [USD]')  # Read network

        # Read network costs
        total_network_cost_usd = 0
        for row in reader:
            total_network_cost_usd += float(row[cost_column])

        return total_network_cost_usd

def read_objective_values_from_file(file_paths):
    """
    Extract the selected objective functions and the non-dominated solutions' objective function values from the
    optimization results files.
    """
    # Initialize objects to store the objectives and the solutions' objective function values
    objectives = []
    objective_function_values_df = pd.DataFrame()

    # Read the objective function values from the optimization results file
    for file_path in file_paths:
        new_objectives, values = read_objective_values(file_path)

        # Check if the objective functions are the same for all the optimization results
        if not objectives:
            objectives = new_objectives
        else:
            assert objectives == new_objectives, 'There is a mismatch in the objective functions used for the '\
                                                 'optimization. Please check the optimization results.'

        # Get the DCS-solution code from the file path and use it as a key to store the objective function values
        objective_function_values_df = \
            pd.concat([objective_function_values_df, pd.DataFrame([file_path.split(os.sep)[-3]] + values).T],
                      axis=0, sort=False,  ignore_index=False)

    # Rename the columns of the dataframe and reset the indexes
    objective_function_values_df.reset_index(inplace=True, drop=True)
    objective_function_values_df.columns = ['DCS-solution'] + objectives

    return objectives, objective_function_values_df

def read_network_costs_from_file(file_paths):
    """
    Extract the network costs from the results files for each non-dominated solution.
    """
    # Read the supply system code and the network costs from the optimization results files
    network_lifetime = 20 # Todo: properly implement the network lifetime
    system_id = [file_path.split(os.sep)[-3] for file_path in file_paths]
    network_costs = [read_network_costs(file_path)/network_lifetime for file_path in file_paths]

    # Create a dataframe with the supply system code and the network costs
    network_costs_df = pd.DataFrame({'DCS-solution': system_id, 'Network cost [USD]': network_costs})

    return network_costs_df

def plot_pareto_front(objectives, objective_values):
    """
    Create a series of scatter plots to visualize the Pareto fronts of the optimization. The user can chose the
    combination of two of the objective functions to plot, by selecting them from the drop-down menus.
    """
    # Initialize the list of traces to plot
    traces = []

    # Create a scatter for the first set of two objective functions
    traces.append(go.Scatter(
        x=objective_values[objectives[0]],
        y=objective_values[objectives[1]],
        mode='markers',
        name='DCS-solution',
        text=objective_values['DCS-solution'],
        marker=dict(
            size=20,
            color=[int(code.split('_')[-1]) for code in objective_values['DCS-solution']
                   if code.split('_')[-1].isdigit()],
            colorscale='Viridis',
            line=dict(width=2,
                      color='black'),
            opacity=0.8
        )
    ))

    # Create the layout of the figure with the drop-down menus to select the objective functions
    # and update the figure when the user selects a new combination of objective functions
    update_menus = [dict(
        buttons=list([
            dict(
                args=[{'x': [objective_values[objectives[i]]],
                       'y': [objective_values[objectives[j]]]}],
                label=objectives[i] + ' vs ' + objectives[j],
                method='update'
            ) for i in range(len(objectives)) for j in range(i+1, len(objectives))
        ]),
        direction='down',
        pad={'r': 10, 't': 10},
        showactive=True,
        x=0.1,
        xanchor='left',
        y=1.13,
        yanchor='top'
    ) ]

    # Create the layout of the figure with the drop-down menus to select the objective functions
    layout = go.Layout(
        updatemenus= update_menus,
        title='Pareto Front: A vs B',
        xaxis=dict(title='Objective Function A'),
        yaxis=dict(title='Objective Function B'),
        width=800,
        height=600,
        showlegend=False,
        plot_bgcolor = 'rgb(190, 235, 243)',
    )

    # Create the figure
    fig = go.Figure(data=traces, layout=layout)

    fig.update_xaxes(
        ticks='outside',
        gridcolor='grey'
    )
    fig.update_yaxes(
        ticks='outside',
        gridcolor='grey'
    )
    fig.show()

def add_3D_scatter_plot(objectives, objective_values):
        # Create 3D scatter plots if there are 3 or more objective functions, introduce corresponding elements to the
    #   drop-down menu and add them to the list of traces

    if len(objectives) >= 3:
        data = go.Scatter3d(x=objective_values[objectives[0]],
                            y=objective_values[objectives[1]],
                            z=objective_values[objectives[3]],
                            mode='markers',
                            name='DCS-solution',
                            text=objective_values['DCS-solution'],
                            marker=dict(
                                size=15,
                                color=[int(code.split('_')[-1]) for code in objective_values['DCS-solution']
                                       if code.split('_')[-1].isdigit()],
                                colorscale='Viridis',
                                opacity=0.9,
                                line=dict(width=4,
                                          color='black')
                            )
                            )


        # Customize the layout
        layout = go.Layout(scene=dict(xaxis_title=objectives[0],
                                      yaxis_title=objectives[1],
                                      zaxis_title=objectives[3],
                                      xaxis=dict(
                                          ticks='outside',
                                          backgroundcolor="rgb(254, 253, 224)",
                                          gridcolor="grey",
                                          showbackground=True),
                                      yaxis=dict(
                                          ticks='outside',
                                          backgroundcolor="rgb(255, 238, 217)",
                                          gridcolor="grey",
                                          showbackground=True),
                                      zaxis=dict(
                                          ticks='outside',
                                          backgroundcolor="rgb(190, 235, 243)",
                                          gridcolor="grey",
                                          showbackground=True)
                                      )
                           )

        # Show the plot
        fig = go.Figure(data=data, layout=layout)
        fig.show()


def main(config=cea.config.Configuration()):
    """Test this plot"""
    locator = InputLocator(scenario=config.scenario)
    optimisation_results = locator.get_new_optimization_results_folder()
    individual_supply_system_results = \
        [locator.get_new_optimization_optimal_supply_systems_summary_file(district_energy_system_id=subfolder)
         for subfolder in os.listdir(optimisation_results) if not subfolder == 'debugging']
    objectives, objective_function_values = read_objective_values_from_file(individual_supply_system_results)
    if 'Cost_USD' in objectives:
        individual_network_results = [locator.get_new_optimization_detailed_network_performance_file(subfolder)
                                      for subfolder in os.listdir(optimisation_results) if not subfolder == 'debugging']
        network_costs = read_network_costs_from_file(individual_network_results)
        total_system_cost = network_costs['Network cost [USD]'] + objective_function_values['Cost_USD']
        objective_function_values['Cost_USD'] = total_system_cost

    plot_pareto_front(objectives, objective_function_values)
    add_3D_scatter_plot(objectives, objective_function_values)


if __name__ == '__main__':
    main(cea.config.Configuration())