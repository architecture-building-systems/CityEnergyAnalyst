
import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
from pandas.plotting import parallel_coordinates
import pandas as pd
import math
import re
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

from directories_files_handler import (calculate_percentage_change, line_plot_dataframe_preprocessing,
                                       combine_excel_sheets, compute_mean_and_std, calculate_self_solar)

                                                ### Generate plots and save ###
def generate_and_save_plots_separated(dataframes, plots_path):
    # Generate and save bar plots for each column in the DataFrame (except the 'Supply_System' column)
    for column in dataframes.columns:
        if column != 'Supply_System':
            plt.figure()
            dataframes[column].plot(kind='bar', title=column)
            plt.ylabel(column)
            plt.xlabel('Supply System')
            plt.tight_layout()

            # Save the plot
            plot_file_path = os.path.join(plots_path, f"{column}_plot.png")
            plt.savefig(plot_file_path)
            plt.close()

def generate_and_save_plots(dataframes, plots_path):

    dataframes = dataframes.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                                                              'System_Energy_Demand_kWh': 'Energy_Demand',
                                                              'GHG_Emissions_kgCO2': 'GHG_Emissions',
                                                              'Cost_USD': 'Cost'})

    # Determine the number of columns to plot (excluding 'Supply_System')
    columns_to_plot = [col for col in dataframes.columns if col != 'Supply_System']
    df_percentage = calculate_percentage_change(dataframes)

    # Create a 2x2 grid for subplots
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 10))

    unit_dict = {'Heat_Emissions': 'GWh', 'Energy_Demand': 'GWh', 'GHG_Emissions': 'ktonCO2', 'Cost': 'Mln USD'}

    # Flatten the axes array for easy indexing
    axes = axes.flatten()

    # Base case is the first row
    base_case = dataframes.iloc[0]

    # Colors for the bars
    colors = plt.cm.viridis(np.linspace(0, 1, len(dataframes)))

    for idx, column in enumerate(columns_to_plot):
        ax = axes[idx]
        base_value = base_case[column] / 1e6
        values = dataframes[column] / 1e6
        font_size = 10 - len(values) * 0.3

        # Plot the base part of each bar
        for i, value in enumerate(values):
            ax.bar(i, min(value, base_value), color=colors[i])
            diff_percentage = df_percentage[column][i]

            # Plot the difference part of each bar
            if value > base_value:
                ax.bar(i, value - base_value, bottom=base_value, color='red', hatch='//')  # Above base value
                ax.text(i, value, f"{diff_percentage:.1f}%", ha='center', va='bottom', fontsize=font_size)
            elif value < base_value and value > 0:
                ax.bar(i, base_value - value, bottom=value, color='green', hatch='\\\\')  # Below base value
                ax.text(i, base_value, f"{diff_percentage:.1f}%", ha='center', va='bottom', fontsize=font_size)
            elif value < 0:
                ax.text(i, 0, f"{diff_percentage:.1f}%", ha='center', va='bottom', fontsize=font_size)

        ax.set_ylabel(f'{column} [{unit_dict[column]}]')
        ax.set_xlabel('Supply System')
        ax.set_title(column)
        ax.set_xticks(range(len(dataframes.index)))
        ax.set_xticklabels(dataframes['Supply_System'], rotation=45, ha='right')

    # Remove any empty subplots if there are less than 4 columns to plot
    for idx in range(len(columns_to_plot), len(axes)):
        fig.delaxes(axes[idx])

    plt.tight_layout()
    fig.suptitle('Comparison of Objective Functions', x=0.5, y=0.99, fontsize=16, fontweight='bold')

    # Adjust the layout again to account for the title
    fig.subplots_adjust(top=0.93)

    # Save the combined plot
    plot_file_path = os.path.join(plots_path, "combined_plots.png")
    plt.savefig(plot_file_path)
    plt.close('all')

def parallel_coordinates_plot(df, path):

    labels = df['Supply_System']
    plt.figure()
    parallel_coordinates(df, 'Supply_System')
    plt.title('Parallel Coordinates Plot', pad=40)
    plt.xticks(rotation=0)
    plt.legend(labels=labels, loc='lower center', bbox_to_anchor=(0.5, 1), ncol=len(labels))
    plot_file_path = os.path.join(path, "Parallel_coordinates_plot.png")
    plt.savefig(plot_file_path)

def stacked_bar_chart(df, path, scenario):

    df = df.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                            'System_Energy_Demand_kWh': 'Energy_Demand',
                            'GHG_Emissions_kgCO2': 'GHG_Emissions',
                            'Cost_USD': 'Cost'})

    # Set the global figure size
    plt.rcParams['figure.figsize'] = (15, 8)

    # Set the global font size for x and y axis labels
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 12

    scenario_selection = df[df['Scenario'] == scenario].reset_index(drop=True)
    scenario_selection = scenario_selection.dropna(axis=1, how='all').fillna(0)
    labels = sorted(scenario_selection.columns[3:].tolist())
    numeric_values = scenario_selection.iloc[:, 3:].sort_index(axis=1)

    # Normalize the values to percentage
    numeric_values = numeric_values.div(numeric_values.sum(axis=0), axis=1) * 100
    multi_line_labels = [f'{scena}\n{aval}' for aval, scena in
                         zip(scenario_selection['Availability'], scenario_selection['System_name'])]

    # Create a colormap or dictionary for fixed colors
    cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0,1,len(numeric_values))) # Use a colormap with enough distinct colors

    fig, ax = plt.subplots()

    # Track the labels to avoid duplicates in the legend
    legend_labels = {}
    hatch_patterns = ['/', '\\', '', '-', '|', '/', '\\', '', '-', '|', '/', '\\', '', '-', '|']

    # Plot the stacked bar chart
    bottom_values = np.zeros(len(numeric_values.columns))
    for i, label in enumerate(labels):
        for j, value in enumerate(numeric_values[label]):
            # Split the string based on the separator "_"
            code = label.split('_')[0]
            bar = ax.bar(code, numeric_values[label][j], bottom=bottom_values[i],
                         label=multi_line_labels[j] if multi_line_labels[j] not in legend_labels else "",
                         color=colors[j], edgecolor='black', hatch=hatch_patterns[j])
            bottom_values[i] += numeric_values[label][j]
            # Add label to legend_labels if it's not already there
            if multi_line_labels[j] not in legend_labels:
                legend_labels[multi_line_labels[j]] = bar

    # Create a custom legend with unique labels
    unique_labels = list(legend_labels.keys())
    unique_handles = [legend_labels[label] for label in unique_labels]
    ax.legend(unique_handles, unique_labels, loc='upper left', bbox_to_anchor=(1, 1))

    box = ax.get_position()
    ax.set_position([box.x0 - 0.05, box.y0, box.width, box.height])

    ax.set_ylabel('Percentage')
    ax.set_title(f'Stacked Bar Chart_{scenario}')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    plot_file_path = os.path.join(path, scenario)
    if not os.path.exists(plot_file_path):
        os.makedirs(plot_file_path)
    plt.savefig(plot_file_path + "/Stacked_bar_chart.png")

    # Close all figures at once
    plt.close('all')

def stellar_chart(df, path, scenario):
    df = df.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                            'System_Energy_Demand_kWh': 'Energy_Demand',
                            'GHG_Emissions_kgCO2': 'GHG_Emissions',
                            'Cost_USD': 'Cost'})

    # Set the global figure size
    plt.rcParams['figure.figsize'] = (12, 8)

    # Set the global font size for x and y axis labels
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12

    selection = df[df['Scenario'] == scenario]

    scenario_selection = selection.loc[:, (selection != 0).any(axis=0)].reset_index(drop=True)
    labels = scenario_selection.columns[3:].tolist()
    for label in labels:
        parts = label.split('_')
        labels[labels.index(label)] = parts[0]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    for availability in selection['Availability'].unique():
        scenario_avail_selection = scenario_selection[scenario_selection['Availability'] == availability].reset_index(drop=True)
        numeric_values = scenario_avail_selection.iloc[:, 3:].reset_index(drop=True) / 1000  # Convert unit from kW to MW

        for i in range(len(scenario_avail_selection)):
            fig, ax = plt.subplots(subplot_kw=dict(polar=True))

            values = numeric_values.iloc[i].values.flatten().tolist()
            values += values[:1]

            max_value = max(values[:-1])  # Exclude the repeated first point
            max_limit = max_value * 1.15  # Slightly higher than the highest value

            # Adjust radial limits
            ax.set_ylim(-max_value * 0.15, max_limit)

            ax.set_yticklabels([])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, weight='bold')

            for j, (angle, value) in enumerate(zip(angles, values)):
                if j < len(values) - 1:  # Exclude the repeated first point
                    ax.plot([angle - angles[1] / 2, angle], [0, value], color='red', linewidth=2)
                    ax.plot([angle + angles[1] / 2, angle], [0, value], color='red', linewidth=2)
                    ax.fill_between([angle - angles[1] / 2, angle, angle + angles[1] / 2], [0, value, 0], color='red', alpha=0.25)
                    if value != 0:
                        ax.text(angle, value, f'{value:.2f}', horizontalalignment='center', size=9, color='white',
                                weight='semibold', backgroundcolor='black',
                                bbox=dict(boxstyle="circle,pad=0.1", edgecolor='none', facecolor='darkred'))
                    else:
                        ax.text(angle, value, '0', horizontalalignment='center', size=5, color='white',
                                weight='semibold', backgroundcolor='white',
                                bbox=dict(boxstyle="circle,pad=0.1", edgecolor='red', facecolor='white'))
            system_name = scenario_avail_selection.iloc[i]['System_name']
            plt.title(f'Stellar Chart {system_name} - {scenario} - {availability}\nValues expressed in MW', pad=30)
            plt.xticks(rotation=0)

            plot_file_path = os.path.join(path, scenario, 'Stellar_charts_systems')
            if not os.path.exists(plot_file_path):
                os.makedirs(plot_file_path)
            plt.savefig(os.path.join(plot_file_path, f"Stellar_chart_{availability}_{system_name}.png"))

            # Close the figure to avoid memory issues
            plt.close(fig)

def radar_chart(df, path, scenario):

    df = df.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                            'System_Energy_Demand_kWh': 'Energy_Demand',
                            'GHG_Emissions_kgCO2': 'GHG_Emissions',
                            'Cost_USD': 'Cost'})

    # Set the global figure size
    plt.rcParams['figure.figsize'] = (12, 8)

    # Set the global font size for x and y axis labels
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12

    scenario_selection = df[df['Scenario'] == scenario]
    scenario_selection = scenario_selection.dropna(axis=1, how='all').fillna(0)
    labels = scenario_selection.columns[3:].tolist()
    numeric_values = scenario_selection.iloc[:, 3:]
    multi_line_labels = [f'{scena}\n{aval}' for aval, scena in
                         zip(scenario_selection['Availability'], scenario_selection['System_name'])]

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    for i in range(len(scenario_selection)):
        values = numeric_values.iloc[i].values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, label=multi_line_labels[i])
        ax.fill(angles, values, alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.title(f'Radar Chart_{scenario}')
    plt.xticks(rotation=0)
    plot_file_path = os.path.join(path, scenario)
    if not os.path.exists(plot_file_path):
        os.makedirs(plot_file_path)
    plt.savefig(plot_file_path + "/Radar_chart.png")

    # Close all figures at once
    plt.close('all')

def scatter_plot(df_base, df_what_if, path, scenario):

    # Assuming the 4 columns of interest are named consistently in both dataframes
    df_base = df_base.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                                                              'System_Energy_Demand_kWh': 'Energy_Demand',
                                                              'GHG_Emissions_kgCO2': 'GHG_Emissions',
                                                              'Cost_USD': 'Cost'})
    df_what_if = df_what_if.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                                                              'System_Energy_Demand_kWh': 'Energy_Demand',
                                                              'GHG_Emissions_kgCO2': 'GHG_Emissions',
                                                              'Cost_USD': 'Cost'})
    Unit_dict = {'Heat_Emissions': 'GWh', 'Energy_Demand': 'GWh', 'GHG_Emissions': 'ktonCO2', 'Cost': 'Mln USD'}
    objective_columns = df_base.columns[2:]

    # Set the global figure size
    plt.rcParams['figure.figsize'] = (12, 8)

    # Set the global font size for x and y axis labels
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12

    scenario_selection_base = df_base[df_base['Scenario'] == scenario]
    scenario_selection_what_if = df_what_if[df_what_if['Scenario'] == scenario].reset_index(drop=True)

    # Define the custom order for 'Criteria' column
    custom_order = ['No_renewables', 'All_renewables']
    marker_shape = {custom_order[0]: '*', custom_order[1]: 'x'}

    # Convert 'Criteria' column to categorical data type with custom order
    scenario_selection_what_if['Availability'] = pd.Categorical(scenario_selection_what_if['Availability'],
                                                                categories=custom_order, ordered=True)

    # Sort DataFrame by 'Criteria' column
    scenario_selection_what_if = scenario_selection_what_if.sort_values(by='Availability').reset_index(drop=True)

    multi_line_labels = [f'{scena}\n{aval}' for aval, scena in
                         zip(scenario_selection_what_if['Availability'], scenario_selection_what_if['Supply_System'])]

    # Create a colormap or dictionary for fixed colors
    cmap = plt.get_cmap('plasma')
    colors = cmap(np.linspace(0, 1, len(multi_line_labels)))  # Use a colormap with enough distinct colors

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    handles, labels = [], []

    for i, column in enumerate(objective_columns):
        ax = axes[i // 2, i % 2]
        ax.scatter(0, scenario_selection_base[column]/1e6, s=100, color='blue', label='Base Case')
        for j in range(len(scenario_selection_what_if[column])):
            ax.scatter(scenario_selection_what_if.index[j] + 1, scenario_selection_what_if[column][j] / 1e6,
                       s=100, color=colors[j], label=multi_line_labels[j],
                       marker=marker_shape[scenario_selection_what_if['Availability'][j]])

        ax.set_xlabel('Index')
        ax.set_ylabel(f'{column} [{Unit_dict[column]}]')
        ax.set_title(f'Scatter Plot of {column}')

        # Collect handles and labels
        if i == 0:
            handles, labels = ax.get_legend_handles_labels()

    # Calculate the maximum number of labels per row
    max_labels_per_row = int(fig.get_figwidth() // 1.75)  # Adjust the divisor to control the spacing
    num_rows = math.ceil((len(labels) + 1) / max_labels_per_row)  # Ceiling division

    # Add the legend to the figure
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=max_labels_per_row)
    plt.suptitle(f'Scatter Plots of Objective Functions for {scenario}')
    plt.tight_layout(rect=[0, 0, 1, 0.95 - 0.05 * num_rows])  # Adjust the layout to make room for the legend

    plot_file_path = os.path.join(path, scenario)
    if not os.path.exists(plot_file_path):
        os.makedirs(plot_file_path)
    plt.savefig(plot_file_path + "/Scatter_plots.png")

    # Close all figures at once
    plt.close('all')

def scatter_plot_matrix(df, path):

    sns.pairplot(df.drop(columns=['Supply_System']))
    plt.suptitle('Scatter Plot Matrix', y=1.02)  # Adjust title position
    plt.xticks(rotation=45)
    plot_file_path = os.path.join(path, "Scatter_plot_matrix.png")
    plt.savefig(plot_file_path)

def heatmap(df, path, scenario):

    df = df.rename(columns={'Heat_Emissions_kWh': 'Heat_Emissions',
                                                              'System_Energy_Demand_kWh': 'Energy_Demand',
                                                              'GHG_Emissions_kgCO2': 'GHG_Emissions',
                                                              'Cost_USD': 'Cost'})

    scenario_selection = df[df['Scenario'] == scenario]
    numeric_values = scenario_selection.iloc[:, 3:]

    # Calculate the number of rows and columns
    num_rows, num_cols = numeric_values.shape

    # Determine figure size based on the number of rows and columns
    fig_width = max(8, num_cols * 1.1)  # Width depends on the number of columns
    fig_height = max(6, num_rows * 0.5)  # Height depends on the number of rows

    # Scaling factors for font sizes
    base_fontsize = 9
    font_scaling_factor = min(fig_width / 8, fig_height / 6)

    plt.figure(figsize=(fig_width, fig_height))
    annot = numeric_values.applymap(lambda x: f'{x:.1f}%')
    sns.heatmap(numeric_values, annot=annot, fmt='', cmap='viridis', cbar=True, linewidths=0.5, linecolor='black',
                annot_kws={"fontsize": base_fontsize * font_scaling_factor, "fontweight": "bold"})

    # Customise plot features
    multi_line_labels = [f'{scena}\n{aval}' for aval, scena in
                         zip(scenario_selection['Availability'], scenario_selection['Supply_System'])]
    plt.yticks(ticks=np.arange(0.5, len(numeric_values) + 0.5, 1), labels=multi_line_labels, rotation=0,
               fontsize=base_fontsize * font_scaling_factor)
    plt.title(f'Heatmap_{scenario}', fontsize=base_fontsize * font_scaling_factor)
    # Adjust the subplot parameters to move the plot to the right
    plt.subplots_adjust(left=0.2, right=1, top=0.9, bottom=0.1)
    plt.xticks(rotation=0)
    plot_file_path = os.path.join(path, scenario)
    if not os.path.exists(plot_file_path):
        os.makedirs(plot_file_path)
    plt.savefig(plot_file_path + "/Heatmap.png")

    # Close all figures at once
    plt.close('all')

def line_graph_plot(base_path, carriers_directory, systems, output_path, scenario):

    categories = {
        'cooling': 'T10W',
        'electricity': 'E230AC',
        'heat_release': ['T100A', 'T25A', 'T30W', 'T27LW', 'T27GW', 'T27SW'],
        'heat_production': ['T100W', 'T70W']
    }

    # Define a color dictionary for specific labels
    color_dict = {
        'CH': 'blue', 'ACH': 'red', 'HEXSW': 'green', 'HEXGW': 'green',
        'HEXLW': 'green', 'TES': 'purple', 'PV': 'darkorange', 'SC': 'brown',
        'BT': 'darkred', 'FU': 'gray', 'OEHR': 'gray', 'CCGT': 'gray',
        'BO': 'black', 'CT': 'cyan', 'demand': 'lime', 'bought': 'olive',
        'sold': 'darkslateblue', 'TW':'magenta'
    }

    for system in systems:
        file_path = os.path.join(base_path, system, carriers_directory)

        # Check if the path exists
        if not os.path.exists(file_path):
            print(f"Path {file_path} does not exist.")
            return

        combined_df = combine_excel_sheets(file_path)

        # Preprocessing of data before plotting
        carriers_to_plot = line_plot_dataframe_preprocessing(combined_df, hours_to_plot=24)

        # Plotting the data
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        i = 0

        for cat, carrier in categories.items():
            plot_with_info = False
            ax = axes[i]

            has_secondary_y_axis = False

            for column in carriers_to_plot.columns:
                for car in carrier if isinstance(carrier, list) else [carrier]:
                    if car in column:
                        plot_with_info = True
                        parts = column.split('_')
                        if parts[0] == 'E230AC':
                            code = re.sub(r'\d+', '', parts[1])
                        else:
                            code = re.sub(r'\d+', '', parts[0])

                        if 'BT' in column or 'TES' in column:
                            ax2 = ax.twinx()  # Create a secondary y-axis if it doesn't exist
                            has_secondary_y_axis = True
                            ax2.plot(carriers_to_plot.index, carriers_to_plot[column] / 1000, label=column, linewidth=2, linestyle='--', color= color_dict[code])
                        else:
                            if (carrier == 'E230AC' and ('demand' in column or 'sold' in column)) or (cat == 'heat_release' and not 'CH' in column) or (cat == 'heat_production' and 'input' in column):
                                ax.plot(carriers_to_plot.index, carriers_to_plot[column] / 1000, label=column, linewidth=2, linestyle='--', color= color_dict[code])
                            else:
                                ax.plot(carriers_to_plot.index, carriers_to_plot[column] / 1000, label=column, linewidth=2, color= color_dict[code])

            if not plot_with_info:
                ax.axis('off')
                continue

            # Set y-limits to match both y-axes
            if has_secondary_y_axis:
                # Get y-limits of both axes
                y_limits = ax.get_ylim()
                y2_limits = ax2.get_ylim()
                # Determine the new y-limits based on the maximum range
                new_y_limits = (min(y_limits[0], y2_limits[0]), max(y_limits[1], y2_limits[1]))
                # Set new y-limits for both axes
                ax.set_ylim(new_y_limits)
                ax2.set_ylim(new_y_limits)

            # Add legends
            if has_secondary_y_axis:
                lines, labels = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize='small', frameon=False)
                ax2.set_ylabel('Storage State of Charge [MWh]')
            else:
                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize='small', frameon=False)

            ax.set_title(f'{cat.capitalize()} profiles')
            ax.set_xlabel('Hours')
            ax.set_ylabel('Energy Carriers Daily profile [MW]')

            i += 1

        # Centered title
        fig.suptitle(f'Line Plot of Combined Data for {system} in scenario {scenario}', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust the plot to leave space for the title
        fig.subplots_adjust(top=0.9, bottom=0.15)

        # Save the plot
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        plot_file_path = os.path.join(output_path, f'Line_plot_{system}_{scenario}.png')
        plt.savefig(plot_file_path)

def yearly_profile_plot(base_path, carriers_directory, systems, output_path, scenario, solar_consumption):
    categories = {
        'cooling': 'T10W',
        'electricity': 'E230AC',
        'heat_release': ['T100A', 'T25A', 'T30W', 'T27LW', 'T27GW', 'T27SW'],
        'heat_production': ['T100W', 'T70W']
    }

    color_dict = {
        'CH': 'blue', 'ACH': 'red', 'HEXSW': 'green', 'HEXGW': 'green',
        'HEXLW': 'green', 'TES': 'purple', 'PV': 'darkorange', 'SC': 'brown',
        'BT': 'darkred', 'FU': 'gray', 'OEHR': 'gray', 'CCGT': 'gray',
        'BO': 'black', 'CT': 'cyan', 'demand': 'lime', 'bought': 'olive',
        'sold': 'darkslateblue', 'TW':'magenta'
    }
    self_consumption = []

    for system in systems:
        file_path = os.path.join(base_path, system, carriers_directory)

        # Check if the path exists
        if not os.path.exists(file_path):
            print(f"Path {file_path} does not exist.")
            return

        combined_df = combine_excel_sheets(file_path)
        # Preprocessing of data before plotting
        if 'THESIS_TEST_CASES_RENEWABLES' in file_path:
            self_consumption = calculate_self_solar(combined_df)
            self_consumption['System'] = system
            self_consumption['Scenario'] = scenario
            solar_consumption = pd.concat([solar_consumption, self_consumption.to_frame().T], axis=0).reset_index(drop=True)

        combined_df = line_plot_dataframe_preprocessing(combined_df, hours_to_plot=8760)

        daily_means, daily_stds = compute_mean_and_std(combined_df)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        i = 0

        for cat, carrier in categories.items():
            ax = axes[i]
            plot_with_info = False

            has_secondary_y_axis = False

            for column in combined_df.columns:
                for car in carrier if isinstance(carrier, list) else [carrier]:
                    if car in column:
                        plot_with_info = True
                        parts = column.split('_')
                        if parts[0] == 'E230AC':
                            code = re.sub(r'\d+', '', parts[1])
                        else:
                            code = re.sub(r'\d+', '', parts[0])

                        if 'BT' in column or 'TES' in column:
                            ax2 = ax.twinx()  # Create a secondary y-axis if it doesn't exist
                            has_secondary_y_axis = True
                            ax2.plot(range(24), daily_means[column] / 1000, label=column, linewidth=2, linestyle='--', color= color_dict[code])
                        else:
                            if (carrier == 'E230AC' and ('demand' in column or 'sold' in column)) or (cat == 'heat_release' and not 'CH' in column) or (cat == 'heat_production' and 'input' in column):
                                ax.plot(range(24), daily_means[column] / 1000, label=column, linewidth=2, linestyle='--', color= color_dict[code])
                            else:
                                ax.plot(range(24), daily_means[column] / 1000, label=column, linewidth=2, color=color_dict[code])

                        ax.fill_between(range(24), ((daily_means[column] - daily_stds[column]) / 1000).clip(lower=0),
                                        (daily_means[column] + daily_stds[column]) / 1000, color=color_dict[code], alpha=0.3)

            if not plot_with_info:
                ax.axis('off')
                continue

            # Set y-limits to match both y-axes
            if has_secondary_y_axis:
                # Get y-limits of both axes
                y_limits = ax.get_ylim()
                y2_limits = ax2.get_ylim()
                # Determine the new y-limits based on the maximum range
                new_y_limits = (min(y_limits[0], y2_limits[0]), max(y_limits[1], y2_limits[1]))
                # Set new y-limits for both axes
                ax.set_ylim(new_y_limits)
                ax2.set_ylim(new_y_limits)

            # Add legends
            if has_secondary_y_axis:
                lines, labels = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.1),
                          ncol=3, fontsize='small', frameon=False)
                ax2.set_ylabel('Storage State of Charge [MWh]')
            else:
                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize='small',
                          frameon=False)

            ax.set_title(f'{cat.capitalize()} profiles')
            ax.set_xlabel('Hours')
            ax.set_ylabel('Demand and production [MW]')
            i += 1

        fig.suptitle(f'Mean and Standard deviation Profile Analysis for {system} in scenario {scenario}', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fig.subplots_adjust(top=0.9, bottom=0.15)

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        plot_file_path = os.path.join(output_path, f'Mean_Std_{system}_{scenario}.png')
        plt.savefig(plot_file_path)
        plt.close('all')

    return solar_consumption

def plot_clusters(X_scaled, labels, medoids, path):

    # Plot the clusters
    plt.figure(figsize=(10, 6))
    colors = ['r', 'g', 'b', 'y', 'c', 'm', 'k', 'orange', 'purple', 'brown']
    for i in range(len(medoids)):
        plt.scatter(X_scaled[labels == i, 0], X_scaled[labels == i, 1], s=100, c=colors[i], label=f'Cluster {i + 1}',
                    alpha=0.6)
    plt.scatter(medoids[:, 0], medoids[:, 1], c='k', marker='x', s=100, label='Medoids')

    plt.title('K-Medoids Clustering')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.legend()
    plt.savefig(os.path.join(path, 'kmedoids_clusters.png'))

def plot_connectivity(connectivity, scenario_name, plot_save_path):

    results = connectivity[connectivity['scenario'] == scenario_name].reset_index(drop=True)
    district_buildings = results[results['availability']=='No_renewables']['district_buildings'].values[0]
    # Calculate figure size based on the amount of data
    fig_width = max(12, np.ceil(len(district_buildings)*0.5))  # Width depends on the number of buildings
    fig_height = max(8, len(results))  # Height depends on the number of results

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Scaling factors for font sizes
    base_fontsize = 12  # Base font size
    font_scaling_factor = fig_width / 20  # Scale font size based on figure width

    # Calculate bbox_to_anchor dynamically based on figure height
    legend_y_position = 1 + (fig_height / 8 * 0.2)

    # Prepare the grid data
    grid_data = np.zeros((len(results), len(district_buildings)))
    for i, result in results.iterrows():
        connected_buildings = result['connected_buildings']
        for j, building in enumerate(district_buildings):
            if building in connected_buildings:
                grid_data[i, j] = 1  # Green for connected, 1 means connected, 0 means not connected

    # Create the grid plot with green and red colors
    cmap = mcolors.ListedColormap(['red', 'green'])
    bounds = [0, 0.5, 1]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Use pcolor to create the plot with grid lines
    cax = ax.pcolor(grid_data, cmap=cmap, norm=norm, edgecolors='k', linewidths=1)

    # Set aspect ratio to equal to maintain square cells
    ax.set_aspect('equal')

    # Set x-axis labels (district buildings)
    ax.set_xticks(np.arange(len(district_buildings)) + 0.5, minor=False)
    ax.set_xticklabels(district_buildings, rotation=90, fontsize=base_fontsize * font_scaling_factor)

    # Set y-axis labels (availability cases)
    multi_line_labels = [f'{availability}\n({result})' for availability, result in zip(results['availability'], results['system'])]
    ax.set_yticks(np.arange(len(multi_line_labels)) + 0.5, minor=False)
    ax.set_yticklabels(multi_line_labels, fontsize=base_fontsize * font_scaling_factor)

    # Annotate the percentage of connection
    for i, result in results.iterrows():
        percentage_connected = result['connected_percentage']
        ax.text(len(district_buildings)+0.1, i + 0.5, f'{percentage_connected:.1f}%', va='center', ha='left',
                fontsize=base_fontsize * font_scaling_factor)
    '''
    # Add a legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Connected'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Disconnected')]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, legend_y_position), ncol=2,
              fontsize=base_fontsize * font_scaling_factor, frameon=False)
    '''
    # Set title
    ax.set_title(f'Network Connection for {scenario_name}', pad=20, fontsize=base_fontsize * font_scaling_factor)
    plt.tight_layout()

    # Save the plot
    plot_path = os.path.join(plot_save_path, scenario_name, f'{scenario_name}_connectivity_plot.png')
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()

def scatter_plot_self(df, path):
    """
    Create a scatter plot from a DataFrame with self-consumption and self-sufficiency values,
    where the color represents different scenarios.

    Parameters:
    df (pd.DataFrame): The input DataFrame with columns 'Self-Consumption', 'Self-Sufficiency', 'System', and 'Scenario'.
    path (str): The path to save the scatter plot image.

    Returns:
    None
    """
    # Set the plot style
    sns.set(style="whitegrid")

    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    scatter = sns.scatterplot(data=df, x='Self_consumption', y='Self_sufficiency',
                              s=100, hue='Scenario', palette='tab10', legend='full', alpha=0.6)

    # Legend
    scatter.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), ncol=1)

    # Add titles and labels
    plt.title('Self-Consumption vs. Self-Sufficiency by Scenario', fontsize=16, pad=20)
    plt.xlabel('Self-Consumption', fontsize=14)
    plt.ylabel('Self-Sufficiency', fontsize=14)

    # Adjust layout to make room for the legend
    plt.tight_layout(rect=[0,0,0.85,1])

    # Save the plot
    final_path = os.path.join(path, "scenario_representations", 'self_analysis_solar.png')
    plt.savefig(final_path, bbox_inches='tight')
    plt.close()