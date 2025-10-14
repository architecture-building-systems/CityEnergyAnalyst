"""
Print the set of non-dominated solutions that were identified by the optimization algorithm. This plot integrates an
option to choose the objective function space in which the solutions are plotted. The user must choose exactly 2  of the
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

import os
import tempfile
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import imageio.v2 as imageio

import cea.config
from cea.inputlocator import InputLocator




def read_fitnesses_from_file(file_path):
    """
    Read the system identifiers (supply system code & connectivity code), as well as the objective function values
    for each generation of the genetic algorithm from the fitness tracker file.
    """
    # Open the fitness tracker .csv-file and store its content in a pandas DataFrame
    full_fitness_tracker = pd.read_csv(file_path, header=0)

    # Get the objective function names
    headers = full_fitness_tracker.columns.values.tolist()
    objectives = headers[5:]

    # Sort the intermediary optimization results by generation and front
    sorted_fitness_tracker = {}

    max_generation = full_fitness_tracker['Generation'].max()
    for generation in range(max_generation + 1):
        sorted_fitness_tracker[generation] = {}
        solutions_in_generation = full_fitness_tracker[full_fitness_tracker['Generation'] == generation]
        max_front = solutions_in_generation['Front'].max()
        for front in range(1, max_front + 1):
            solutions_in_front = solutions_in_generation[solutions_in_generation['Front'] == front]
            sorted_fitness_tracker[generation][front] = solutions_in_front[['Ind_Code'] + objectives]

    # Replace the objectives with their exact descriptions
    objectives = [objective.replace('cost', 'Total annualized system cost [USD]')
                  for objective in objectives]
    objectives = [objective.replace('GHG_emissions', 'Total annual GHG emissions [kg CO2-eq]')
                  for objective in objectives]
    objectives = [objective.replace('system_energy_demand', 'Total annual system energy demand [kWh]')
                  for objective in objectives]
    objectives = [objective.replace('anthropogenic_heat', 'Total annual heat emissions [kWh]')
                  for objective in objectives]

    return objectives, sorted_fitness_tracker

def plot_fitness_tracker(objectives, sorted_fitness_tracker):
    """
    Plot objective function values for each generation of the genetic algorithm.
    """
    # Initialize the figure
    traces = []
    objective_codes = sorted_fitness_tracker[0][1].columns.values.tolist()[1:]
    colorscale = px.colors.sequential.Viridis

    # Add the objective function values for each generation front and each generation
    for generation, fronts in sorted_fitness_tracker.items():
        for front, objective_function_values in fronts.items():
            traces.append(go.Scatter( # Add a trace for each objective function
                x=list(objective_function_values[objective_codes[0]]),
                y=list(objective_function_values[objective_codes[1]]),
                name='Generation ' + str(generation) + ', Front ' + str(front),
                mode='lines+markers',
                marker=dict(
                    size=10,
                    color=colorscale[divmod(generation, len(colorscale))[1]],
                    showscale=False
                )
            ))

    # Create the drop-down menus to select the objective functions to be plotted against each other.
    # Each plot displays the selected non-dominated solutions for each generation and front in that 
    # objective function space.
    update_menus = [dict(
        buttons=list([
            dict(
                args=[{'x': [sorted_fitness_tracker[i][j][objective_codes[k]]
                             for i in range(len(sorted_fitness_tracker))
                             for j in range(1, len(sorted_fitness_tracker[i])+1)],
                       'y': [sorted_fitness_tracker[i][j][objective_codes[l]]
                             for i in range(len(sorted_fitness_tracker))
                             for j in range(1, len(sorted_fitness_tracker[i])+1)],
                       'title': 'Pareto Front: ' + objectives[k] + ' vs ' + objectives[l],
                       'name': ['Generation ' + str(i) + ', Front ' + str(j)
                                for i in range(len(sorted_fitness_tracker))
                                for j in range(1, len(sorted_fitness_tracker[i])+1)]}],
                label=objectives[k] + ' vs ' + objectives[l],
                method='update'
            ) for k in range(len(objectives)) for l in range(k+1, len(objectives))
        ]),
        direction='down',
        pad={'r': 10, 't': 10},
        showactive=True,
        x=0.5,
        xanchor='left',
        y=1.1,
        yanchor='top'
    ) ]

    # Create the layout of the figure with the drop-down menus to select the objective functions
    layout = go.Layout(
        updatemenus=update_menus,
        title='Pareto Front: A vs B',
        xaxis=dict(title='Objective Function A'),
        yaxis=dict(title='Objective Function B'),
        width=1200,
        height=900,
        showlegend=True
    )

    # Create the figure
    fig = go.Figure(data=traces, layout=layout)
    fig.show()

def plot_generation_evolution(sorted_fitness_tracker, objectives, output_gif_path):
    """Plot the evolution of the Pareto front across generations and save as a GIF."""
    images = []
    max_generation = max(sorted_fitness_tracker.keys())
    colors = plt.cm.viridis(np.linspace(0, 1, max_generation + 1))
    objective_codes = sorted_fitness_tracker[0][1].columns.values.tolist()[1:]

    with tempfile.TemporaryDirectory() as temp_dir:
        for generation in range(max_generation + 1):
            plt.figure(figsize=(10, 8))
            plt.xlabel(objectives[0])
            plt.ylabel(objectives[1])
            plt.title(f'Pareto Front Evolution - Generation {generation}')

            # Plot each generation with increasing opacity
            for gen in range(generation + 1):
                data = sorted_fitness_tracker[gen][1]
                # Sort the points to make the line connection meaningful
                sorted_data = data.sort_values(by=objective_codes[0])

                # Plot points
                plt.scatter(sorted_data[objective_codes[0]], sorted_data[objective_codes[1]], color=colors[gen],
                            alpha=(gen + 1) / (generation + 1))

                # Plot lines connecting the points
                plt.plot(sorted_data[objective_codes[0]], sorted_data[objective_codes[1]], color=colors[gen],
                         alpha=(gen + 1) / (generation + 1))

            # Save the frame to a temporary file
            temp_file_path = os.path.join(temp_dir, f'gen_{generation}.png')
            plt.savefig(temp_file_path)
            plt.close()
            images.append(imageio.imread(temp_file_path))

        # Create the GIF
        imageio.mimsave(output_gif_path, images, duration=0.5)


def main(config=cea.config.Configuration()):
    """Test this plot"""
    # Read the fitness tracker file
    locator = InputLocator(scenario=config.scenario)
    fitness_tracker = locator.get_new_optimization_debugging_fitness_tracker_file()
    objectives, objective_function_values = read_fitnesses_from_file(fitness_tracker)

    # Plot the non-dominated solutions chosen at each generation of the genetic algorithm
    plot_fitness_tracker(objectives, objective_function_values)

    # Plot the evolution and save as GIF
    output_gif_path = os.path.join(locator.get_new_optimization_debugging_folder(), 'pareto_front_evolution.gif')
    plot_generation_evolution(objective_function_values, objectives, output_gif_path)
    print(f"GIF saved as {output_gif_path}")


if __name__ == '__main__':
    main(cea.config.Configuration())
