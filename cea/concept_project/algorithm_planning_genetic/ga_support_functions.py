from ga_config import *
import random
import get_initial_network as gia
import csv
import generate_testcase
import pandas as pd
import errno
import os
import ga_plotting as pf
import matplotlib.pyplot as plt

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def initial_network():
    """
    Initiate data of main problem

    :param None
    :type Nonetype

    :returns: df_nodes_processed: information about every node in study case
    :rtype: GeoDataFrame
    :returns: tranches: information about every tranch in study case (splitted street network)
    :rtype: GeoDataFrame
    :returns: dict_length: length on street network between every node
    :rtype: dictionary
    :returns: dict_path: list of edges between two nodes
    :rtype: dictionary
    :returns: idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :rtype: list(startnode, endnode)
    """

    gia.calc_substation_location()
    df_nodes, tranches = gia.connect_building_to_grid()
    df_nodes_processed = gia.process_network(df_nodes)
    dict_length, dict_path = gia.create_length_dict(df_nodes_processed, tranches)

    # df_nodes_processed, tranches, dict_length, dict_path = generate_testcase.main()

    idx_nodes_sub = df_nodes_processed[df_nodes_processed['Type'] == 'PLANT'].index
    idx_nodes_consum = df_nodes_processed[df_nodes_processed['Type'] == 'CONSUMER'].index
    idx_nodes = idx_nodes_sub.append(idx_nodes_consum)

    # Diagonal edge index matrix
    idx_edge = []
    for i in idx_nodes:
        for j in idx_nodes:
            if i != j and i < j:
                idx_edge.append((i, j))

    return df_nodes_processed, tranches, dict_length, dict_path, idx_edge


def generate_pop(idx_edge, df_line_parameter):
    """
    Creates an individual configuration for the evolutionary algorithm

    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame

    :returns: individual: Contents list of genes and fitness
    :rtype: individual (DEAP object)
    """
    # get the number of possible trenches in network
    n_trench = len(idx_edge)
    n_linetype = len(df_line_parameter) - 1

    individual = []
    for line in range(n_trench):
        individual.append(random.randint(0, n_linetype))
        # individual.append(random.randint(0, 0))

    return individual


def calc_annuity_factor(n, i):
    """
    Calculates the annuity factor derived by formula (1+i)**n * i / ((1+i)**n - 1)

    :param n: depreciation period (40 = 40 years)
    :type int
    :param i: interest rate (0.06 = 6%)
    :type float

    :returns: a: annuity factor
    :rtype: float
    """

    a = (1 + i) ** n * i / ((1 + i) ** n - 1)

    return a


# +++++++++++++++++++++++++++++++++++++
# Main objective function evaluation
# ++++++++++++++++++++++++++++++++++++++

def evaluate_individual(individual, idx_ind, idx_edge, dict_length, ind_power_loss, df_line_parameter):
    """
    Evaluates an individual regarding investment cost, operation and maintenance cost and power losses

    :param individual: Contents list of genes and fitness
    :type individual (DEAP object)
    :param: idx_ind: index number of the individual
    :type: int
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: dict_length: length on street network between every node
    :type: dictionary
    :param: ind_power_loss: length on street network between every node
    :type: float
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame

    :returns: fitness: annuity factor
    :rtype: float
    """

    c_invest = 0.0
    c_om = 0.0
    c_power = 0.0
    n_lines = 0  # number of lines in network

    for idx_gene, gene in enumerate(individual):
        if gene > 0:
            start_node = idx_edge[idx_gene][0]
            end_node = idx_edge[idx_gene][1]

            # Calculation of investment cost
            length = dict_length[start_node][end_node]
            lifetime = df_line_parameter.loc[gene, 'lifetime_a']
            annuity_factor = calc_annuity_factor(lifetime, INTEREST_RATE)  # annuity factor (years, interest)
            c_line = length * df_line_parameter.loc[gene, 'price_sgd_per_m'] * annuity_factor
            c_invest += 2.0 * c_line

            # Calculation of operation and maintenance cost
            om_factor = df_line_parameter.loc[gene, 'om_factor']
            c_om += c_line * om_factor

            # Tracking number of lines in network
            n_lines += 1

    # Calculation of cost for power losses
    c_power += ind_power_loss * APPROX_LOSS_HOURS * (ELECTRICITY_COST / 1000.0)  # W to kW

    # Sum of costs is fitness of individual 
    fitness = c_invest + c_om + c_power

    print 'Ind No. %02i | CAPEX: %.2f | OPEX: %.2f | LOSSES: %.2f | Fitness: %.2f | nLines: %.2i' \
          % (idx_ind, c_invest, c_om, c_power, fitness, n_lines)

    return fitness


def evaluate_best(individual, idx_edge, dict_length, ind_power_loss, df_line_parameter):
    """
    Evaluates an individual regarding investment cost, operation and maintenance cost and power losses

    :param individual: Contents list of genes and fitness
    :type individual (DEAP object)
    :param: idx_ind: index number of the individual
    :type: int
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: dict_length: length on street network between every node
    :type: dictionary
    :param: ind_power_loss: length on street network between every node
    :type: float
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame

    :returns: fitness: annuity factor
    :rtype: float
    """

    c_invest = 0.0
    c_om = 0.0
    c_power = 0.0
    n_lines = 0  # number of lines in network

    for idx_gene, gene in enumerate(individual):
        if gene > 0:
            start_node = idx_edge[idx_gene][0]
            end_node = idx_edge[idx_gene][1]

            # Calculation of investment cost
            length = dict_length[start_node][end_node]
            lifetime = df_line_parameter.loc[gene, 'lifetime_a']
            annuity_factor = calc_annuity_factor(lifetime, INTEREST_RATE)  # annuity factor (years, interest)
            c_line = length * df_line_parameter.loc[gene, 'price_sgd_per_m'] * annuity_factor
            c_invest += 2.0 * c_line

            # Calculation of operation and maintenance cost
            om_factor = df_line_parameter.loc[gene, 'om_factor']
            c_om += c_line * om_factor

            # Tracking number of lines in network
            n_lines += 1

    # Calculation of cost for power losses
    c_power += ind_power_loss * APPROX_LOSS_HOURS * (ELECTRICITY_COST / 1000.0)  # W to kW

    # Sum of costs is fitness of individual
    fitness = c_invest + c_om + c_power

    print 'Best IND | CAPEX: %.2f | OPEX: %.2f | LOSSES: %.2f | Fitness: %.2f | nLines: %.2i' \
          % (c_invest, c_om, c_power, fitness, n_lines)

    return [fitness, c_invest, c_om, c_power, n_lines]


def write_csv(fitness_hist, best_ind, datetime, time_gen_hist, time_accumulated_hist, fitness_change_hist, eval_best):
    list_fitness_hist = list(fitness_hist)
    best_chromosome = str(best_ind)

    str_csvname = '%4i%02i%02i_%2i%02i%02i_ga_results.csv' \
                  % (datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute, datetime.second)

    filename = LOCATOR + '/ga_output/' + str_csvname

    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(filename, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        writer.writerow(['SCENARIO', SCENARIO])
        writer.writerow(['POP_SIZE', POP_SIZE])
        writer.writerow(['N_GENERATIONS', N_GENERATIONS])
        writer.writerow(['IND_CROSS_RATE', IND_CROSS_RATE])
        writer.writerow(['CROSS_RATE', CROSS_RATE])
        writer.writerow(['IND_MUTATE_RATE', IND_MUTATE_RATE])
        writer.writerow(['MUTATE_RATE', MUTATE_RATE])
        writer.writerow(['TOURNAMENT_SIZE', TOURNAMENT_SIZE])
        writer.writerow(['LINE_PROBABILITY', LINE_PROBABILITY])
        writer.writerow(['INTEREST_RATE', INTEREST_RATE])
        writer.writerow(['ELECTRICITY_COST', ELECTRICITY_COST])
        writer.writerow(['APPROX_LOSS_HOURS', APPROX_LOSS_HOURS])

        writer.writerow([''])

        writer.writerow(['Best Fitness', eval_best[0]])
        writer.writerow(['CAPEX', eval_best[1]])
        writer.writerow(['OPEX', eval_best[2]])
        writer.writerow(['LOSSES', eval_best[3]])
        writer.writerow(['nLines', eval_best[4]])
        writer.writerow(['Best Chromosome', best_chromosome])

        writer.writerow([''])

        writer.writerow(['Fitness History'])
        writer.writerow(['idx_fitness', 'time_gen_hist', 'time_accumulated_hist', 'fitness', 'fitness_change_hist'])
        for idx_fitness, fitness in enumerate(list_fitness_hist):
            writer.writerow([idx_fitness,
                             time_gen_hist[idx_fitness],
                             time_accumulated_hist[idx_fitness],
                             fitness,
                             fitness_change_hist[idx_fitness]])

        writer.writerow([''])

        df_nodes, tranches, dict_length, dict_path, idx_edge = initial_network()
        df_line_parameter = pd.read_csv(LOCATOR + '/electric_line_data.csv')
        
        writer.writerow(['Node index', 'Demand in kW'])
        for node_idx, node in df_nodes.iterrows():
            if node['GRID0_kW'] > 0:
                writer.writerow(['Node ' + str(node_idx), node['GRID0_kW'] * 3.0])

        writer.writerow([''])

        writer.writerow(['Linetype', 'Crosssection in mm2'])
        for idx_line, line in df_line_parameter.iterrows():
            writer.writerow(['Linetype ' + str(idx_line), line['cross_section_mm2']])


def save_png(best_ind, datetime):
    str_datetime = '%4i%02i%02i_%2i%02i%02i' \
                  % (datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute, datetime.second)

    df_nodes, tranches, dict_length, dict_path, idx_edge = initial_network()

    filename_street = LOCATOR + '/ga_output/' + str_datetime + '_ga_plot_street.png'
    filename_graph = LOCATOR + '/ga_output/' + str_datetime + '_ga_plot_graph.png'

    pf.plot_network_on_street_save(df_nodes, tranches, idx_edge, dict_path, best_ind)
    plt.savefig(filename_street, dpi=1200)

    pf.plot_network_graph_save(df_nodes, tranches, idx_edge, dict_path, best_ind)
    plt.savefig(filename_graph, dpi=1200)
