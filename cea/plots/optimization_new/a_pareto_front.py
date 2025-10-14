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
import numpy as np
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

        # Get the DES-solution code from the file path and use it as a key to store the objective function values
        objective_function_values_df = \
            pd.concat([objective_function_values_df, pd.DataFrame([file_path.split(os.sep)[-3]] + values).T],
                      axis=0, sort=False,  ignore_index=False)

    # Rename the columns of the dataframe and reset the indexes
    objective_function_values_df.reset_index(inplace=True, drop=True)
    objective_function_values_df.columns = ['DES-solution'] + objectives

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
    network_costs_df = pd.DataFrame({'DES-solution': system_id, 'Network cost [USD]': network_costs})

    return network_costs_df

def _create_expanded_rectangle(x, y, expansion_factor=0.2):
    """Create a simple expanded rectangle around points."""
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    x_range = x_max - x_min if x_max != x_min else 1.0
    y_range = y_max - y_min if y_max != y_min else 1.0
    
    x_expanded = [
        x_min - x_range * expansion_factor, 
        x_max + x_range * expansion_factor, 
        x_max + x_range * expansion_factor, 
        x_min - x_range * expansion_factor, 
        x_min - x_range * expansion_factor
    ]
    y_expanded = [
        y_min - y_range * expansion_factor, 
        y_min - y_range * expansion_factor,
        y_max + y_range * expansion_factor, 
        y_max + y_range * expansion_factor,
        y_min - y_range * expansion_factor
    ]
    
    return x_expanded, y_expanded


def create_solution_space_boundary(x, y):
    """
    Create a boundary around solution points using convex hull approach.
    For projected multi-objective Pareto fronts, this represents the solution space
    rather than claiming to be an optimal boundary.
    """
    if len(x) < 3:
        return _create_expanded_rectangle(x, y, expansion_factor=0.2)
    
    try:
        from scipy.spatial import ConvexHull
        
        points = np.column_stack([x, y])
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        
        # Close the polygon
        hull_x = np.append(hull_points[:, 0], hull_points[0, 0])
        hull_y = np.append(hull_points[:, 1], hull_points[0, 1])
        
        return hull_x.tolist(), hull_y.tolist()
        
    except Exception as e:
        print(f"Warning: Could not create solution space boundary: {e}")
        return _create_expanded_rectangle(x, y, expansion_factor=0.0)


def create_extended_problem_space(x, y, extension_factor=0.5):
    """
    Create a rectangle showing the extended problem space direction.
    Extends in positive directions (typically representing worse objective values).
    """
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    x_range = x_max - x_min if x_max != x_min else 1.0
    y_range = y_max - y_min if y_max != y_min else 1.0
    
    # Extend in positive directions (typically worse for optimization objectives)
    x_extension = x_max + x_range * extension_factor
    y_extension = y_max + y_range * extension_factor
    
    rect_x = [x_min, x_extension, x_extension, x_min, x_min]
    rect_y = [y_min, y_min, y_extension, y_extension, y_min]
    
    return rect_x, rect_y


def _create_space_visualization_traces(other_solutions, objectives, i, j, color, run_name):
    """
    Create visualization traces for solution space boundaries and extended problem space.
    Returns a list of plotly traces to be added to the plot.
    """
    traces = []
    
    if len(other_solutions) < 3:
        return traces
    
    try:
        x_data = np.array(other_solutions[objectives[i]], dtype=float)
        y_data = np.array(other_solutions[objectives[j]], dtype=float)
        
        # Create solution space boundary
        boundary_x, boundary_y = create_solution_space_boundary(x_data, y_data)
        traces.append(go.Scatter(
            x=boundary_x,
            y=boundary_y,
            fill='toself',
            fillcolor=color,
            line=dict(color=color, width=1, dash='dash'),
            name=f'Solution Space {run_name}',
            visible=False,
            opacity=0.2,
            hovertemplate=f'Solution Space Projection<br>{run_name}<extra></extra>'
        ))
        
        # Create extended problem space
        rect_x, rect_y = create_extended_problem_space(x_data, y_data)
        traces.append(go.Scatter(
            x=rect_x,
            y=rect_y,
            fill='toself',
            fillcolor=color,
            line=dict(color=color, width=1, dash='dot'),
            name=f'Extended Problem Space {run_name}',
            visible=False,
            opacity=0.1,
            hovertemplate=f'Extended Problem Space<br>{run_name}<br>(Indicative Direction)<extra></extra>'
        ))
        
    except Exception as e:
        print(f"Warning: Solution space visualization failed for run {run_name} with objectives {objectives[i]} and {objectives[j]}: {e}")
    
    return traces


def plot_pareto_front(objectives, objective_values_dict):
    """
    Create a series of 2D scatter plots to visualize projections of multi-objective optimization solutions.
    Shows solution space boundaries for projected non-dominated solutions from multiple optimization runs.
    Note: 2D projections of multi-objective Pareto fronts may contain apparently dominated points.
    """
    nbr_traces = len(objectives) * (len(objectives) - 1) * len(objective_values_dict) * 2
    base_visibility = [False] * nbr_traces
    traces = []
    buttons = []
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'yellow']

    for i in range(len(objectives)):
        for j in range(i + 1, len(objectives)):
            current_traces = []
            for run_id, objective_values in objective_values_dict.items():
                run_name = 'main' if not run_id else 'run ' + str(run_id)
                color = colors[0] if not run_id else colors[run_id % len(colors)]

                # Separate current_DES from other solutions
                current_des_data = objective_values[objective_values['DES-solution'] == 'current_DES']
                other_solutions = objective_values[objective_values['DES-solution'] != 'current_DES']
                
                # Scatter plot for other solutions
                if not other_solutions.empty:
                    current_traces.append(go.Scatter(
                        x=other_solutions[objectives[i]],
                        y=other_solutions[objectives[j]],
                        mode='markers',
                        name=f'DES-solution {run_name}',
                        text=other_solutions['DES-solution'],
                        marker=dict(
                            size=12,
                            color=color,
                            line=dict(width=2, color='black'),
                            opacity=0.8
                        ),
                        visible=False
                    ))
                
                # Scatter plot for current_DES with special styling
                if not current_des_data.empty:
                    current_traces.append(go.Scatter(
                        x=current_des_data[objectives[i]],
                        y=current_des_data[objectives[j]],
                        mode='markers',
                        name=f'Current DES {run_name}',
                        text=current_des_data['DES-solution'],
                        marker=dict(
                            size=10,
                            color='grey',
                            line=dict(width=4, color=color),
                            opacity=1.0
                        ),
                        visible=False
                    ))

                # Add solution space visualizations
                current_traces.extend(
                    _create_space_visualization_traces(other_solutions, objectives, i, j, color, run_name)
                )

            visibility = base_visibility.copy()
            visibility[len(traces):len(traces) + len(current_traces)] = [True] * len(current_traces)
            buttons.append(dict(
                args=[{'visible': visibility},
                      {'xaxis.title.text': objectives[i],
                       'yaxis.title.text': objectives[j]}],
                label=f'{objectives[i]} vs {objectives[j]}',
                method='update'
            ))
            traces.extend(current_traces)

    for trace in traces[:len(objective_values_dict) * 2]:
        trace.visible = True

    layout = go.Layout(
        title='Multi-Objective Solution Comparison (2D Projections)',
        xaxis=dict(title=objectives[0]),
        yaxis=dict(title=objectives[1]),
        width=800,
        height=600,
        showlegend=True,
        plot_bgcolor='rgb(190, 235, 243)',
        updatemenus=[dict(
            buttons=buttons,
            direction='down',
            pad={'r': 10, 't': 10},
            showactive=True,
            x=0.1,
            xanchor='left',
            y=1.13,
            yanchor='top'
        )]
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.update_xaxes(ticks='outside', gridcolor='grey')
    fig.update_yaxes(ticks='outside', gridcolor='grey')
    return fig

def add_3D_scatter_plot(objectives, objective_values_dict):
    """
    Create 3D scatter plots for all combinations of 3 objectives from multiple optimization runs.
    """
    if len(objectives) < 3:
        return
    
    from itertools import combinations
    
    traces = []
    buttons = []
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'yellow']
    
    # Generate all combinations of 3 objectives
    objective_combinations = list(combinations(range(len(objectives)), 3))
    
    for combo_idx, (i, j, k) in enumerate(objective_combinations):
        current_traces = []
        
        for run_id, objective_values in objective_values_dict.items():
            run_name = 'main' if not run_id else 'run ' + str(run_id)
            color = colors[0] if not run_id else colors[run_id % len(colors)]
            
            # Separate current_DES from other solutions
            current_des_data = objective_values[objective_values['DES-solution'] == 'current_DES']
            other_solutions = objective_values[objective_values['DES-solution'] != 'current_DES']
            
            # Scatter plot for other solutions
            if not other_solutions.empty:
                current_traces.append(go.Scatter3d(
                    x=other_solutions[objectives[i]],
                    y=other_solutions[objectives[j]],
                    z=other_solutions[objectives[k]],
                    mode='markers',
                    name=f'DES-solution {run_name}',
                    text=other_solutions['DES-solution'],
                    marker=dict(
                        size=8,
                        color=color,
                        line=dict(width=2, color='black'),
                        opacity=0.8
                    ),
                    visible=False
                ))
            
            # Scatter plot for current_DES with special styling
            if not current_des_data.empty:
                current_traces.append(go.Scatter3d(
                    x=current_des_data[objectives[i]],
                    y=current_des_data[objectives[j]],
                    z=current_des_data[objectives[k]],
                    mode='markers',
                    name=f'Current DES {run_name}',
                    text=current_des_data['DES-solution'],
                    marker=dict(
                        size=6,
                        color='grey',
                        line=dict(width=4, color=color),
                        opacity=1.0
                    ),
                    visible=False
                ))
        
        # Create button for this combination
        visibility = [False] * len(traces) + [True] * len(current_traces) + [False] * (len(objective_combinations) - combo_idx - 1) * len(current_traces) * len(objective_values_dict)
        
        buttons.append(dict(
            args=[{'visible': visibility},
                  {'scene.xaxis.title.text': objectives[i],
                   'scene.yaxis.title.text': objectives[j],
                   'scene.zaxis.title.text': objectives[k]}],
            label=f'{objectives[i]} vs {objectives[j]} vs {objectives[k]}',
            method='update'
        ))
        
        traces.extend(current_traces)
    
    # Make first combination visible by default
    if traces:
        for trace_idx in range(len(objective_values_dict) * 2):  # 2 traces per run (solutions + current_DES)
            if trace_idx < len(traces):
                traces[trace_idx].visible = True
    
    # Customize the layout
    layout = go.Layout(
        title='3D Pareto Front Comparison',
        scene=dict(
            xaxis_title=objectives[0],
            yaxis_title=objectives[1],
            zaxis_title=objectives[2],
            xaxis=dict(
                ticks='outside',
                backgroundcolor="rgb(254, 253, 224)",
                gridcolor="grey",
                showbackground=True
            ),
            yaxis=dict(
                ticks='outside',
                backgroundcolor="rgb(255, 238, 217)",
                gridcolor="grey",
                showbackground=True
            ),
            zaxis=dict(
                ticks='outside',
                backgroundcolor="rgb(190, 235, 243)",
                gridcolor="grey",
                showbackground=True
            )
        ),
        showlegend=True,
        updatemenus=[dict(
            buttons=buttons,
            direction='down',
            pad={'r': 10, 't': 10},
            showactive=True,
            x=0.1,
            xanchor='left',
            y=1.0,
            yanchor='top'
        )]
    )

    # Show the plot
    fig = go.Figure(data=traces, layout=layout)
    return fig


def main(config=cea.config.Configuration()):
    """Test this plot"""
    locator = InputLocator(scenario=config.scenario)
    objective_values_dict = {}
    
    # Identify all potential optimization run folders and extract run_ids
    optimization_base_folder = locator.get_optimization_results_folder()
    run_ids = []
    
    if os.path.exists(optimization_base_folder):
        for folder_name in os.listdir(optimization_base_folder):
            folder_path = os.path.join(optimization_base_folder, folder_name)
            if os.path.isdir(folder_path):
                # Check for 'centralized' (default) or 'centralized_run_{X}' patterns
                if folder_name == 'centralized':
                    run_ids.append(None)
                elif folder_name.startswith('centralized_run_'):
                    run_id = folder_name.replace('centralized_run_', '')
                    run_ids.append(int(run_id))

    if run_ids:
        print(f"Found optimization run_ids: {run_ids}")
    else:
        raise ValueError("No optimization results found! Please run the centralised optimisation script before plotting.")

    objectives = []
    for run_id in run_ids:
        locator.optimization_run = run_id
        optimisation_results = locator.get_centralized_optimization_results_folder()
        individual_supply_system_results = [
            locator.get_new_optimization_optimal_supply_systems_summary_file(subfolder)
            for subfolder in os.listdir(optimisation_results) if not subfolder == 'debugging'
        ]
        objectives, objective_function_values = read_objective_values_from_file(individual_supply_system_results)

        if 'Cost_USD' in objectives:
            individual_network_results = [
                locator.get_new_optimization_detailed_network_performance_file(subfolder)
                for subfolder in os.listdir(optimisation_results) if not subfolder == 'debugging'
            ]
            network_costs = read_network_costs_from_file(individual_network_results)
            total_system_cost = network_costs['Network cost [USD]'] + objective_function_values['Cost_USD']
            objective_function_values['Cost_USD'] = total_system_cost

        objective_values_dict[run_id] = objective_function_values

    plot_2d = plot_pareto_front(objectives, objective_values_dict)
    plot_3d = add_3D_scatter_plot(objectives, objective_values_dict)

    return plot_2d, plot_3d


if __name__ == '__main__':
    plot2d, plot_3d = main(cea.config.Configuration())

    plot2d.show(renderer="browser")
    if plot_3d is not None:
        plot_3d.show(renderer="browser")
