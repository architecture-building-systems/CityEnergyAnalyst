import networkx as nx
from operator import itemgetter
import random
from ga_config import *
import concept.model_electric_network.emodel as emodel
import time
import matplotlib.pyplot as plt


def create_complete_graph(df_nodes, idx_edge, dict_length):
    """
    Create graph model with complete network

    :param: df_nodes: information about every node in study case
    :type: GeoDataFrame
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: dict_length: length on street network between every node
    :type: dictionary

    :returns: G_complete: graph of complete network
    :rtype: Graph (networkx object)
    """

    G_complete = nx.Graph()

    for idx, node in df_nodes.iterrows():
        G_complete.add_node(idx, type=node['Type'])

    for idx_line, lines in enumerate(idx_edge):
        start_node_index = lines[0]
        end_node_index = lines[1]
        tranch_length = dict_length[start_node_index][end_node_index]

        G_complete.add_edge(int(start_node_index),
                            int(end_node_index),
                            weight=tranch_length,
                            gene=idx_line,
                            startnode=start_node_index,
                            endnode=end_node_index)

    return G_complete


def create_individual_graph(list_ind, df_nodes, idx_edge, dict_length):
    """
    Create graph model with individual

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param: df_nodes: information about every node in study case
    :type: GeoDataFrame
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: dict_length: length on street network between every node
    :type: dictionary

    :returns: G_ind: graph of individual network
    :rtype: Graph (networkx object)
    """

    G_ind = nx.Graph()

    for node_idx, node in df_nodes.iterrows():
        # G_ind.add_node(node_idx, type=node['Type'], pos=(node.values[1].x, node.values[1].y))
        G_ind.add_node(node_idx, type=node['Type'])

    for line_idx, gene in enumerate(list_ind):
        if gene > 0:
            idx_startnode = idx_edge[line_idx][0]
            idx_endnode = idx_edge[line_idx][1]
            tranch_length = dict_length[idx_startnode][idx_endnode]

            G_ind.add_edge(int(idx_startnode),
                           int(idx_endnode),
                           weight=tranch_length,
                           gene=line_idx)

    return G_ind


def recursive_subnet(current_node, unprocessed_nodes, subnet_nodes, G_ind):
    """
    find all interconnected nodes in an intercconnected sub network with recursive function

    :param: current_node: index of current processed node
    :type: int
    :param: unprocessed_nodes: list of nodes which are not assigned to an interconnected subnet
    :type: list(int)
    :param subnet_nodes: list of nodes in interconnected subnet
    :type list(int)
    :param: G_ind: graph of individual network
    :type: Graph (networkx object)

    :returns: unprocessed_nodes: graph of individual network
    :rtype: list(int)
    :returns: subnet_nodes: list of nodes in interconnected subnet
    :rtype: list(int)
    """

    subnet_nodes.append(current_node)
    current_neighbourhood = G_ind.neighbors(current_node)
    if current_neighbourhood:
        for neighbour_idx, neighbour in enumerate(current_neighbourhood):
            if neighbour in unprocessed_nodes:
                unprocessed_nodes.remove(neighbour)
                recursive_subnet(neighbour, unprocessed_nodes, subnet_nodes, G_ind)

    return unprocessed_nodes, subnet_nodes


def process_individual_network(list_ind, G_complete, G_ind, df_line_parameter):
    """
    This function processes each individual regarding its network structure. Each demand node hast to be connected
    to at least one plant node

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param: G_complete: graph of complete network
    :type: Graph (networkx object)
    :param: G_ind: graph of individual network
    :type: Graph (networkx object)
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    """

    unprocessed_nodes = list(G_ind)
    subnet_list = []

    # Assign Plant/ consumer nodes in network of individual into lists
    plant_nodes = []
    consumer_nodes = []

    for nodes in G_ind.node.iteritems():
        if nodes[1]['type'] == 'PLANT':
            plant_nodes.append(nodes[0])
        elif nodes[1]['type'] == 'CONSUMER':
            consumer_nodes.append(nodes[0])

    # Assign nodes of unprocessed_nodes to subnet_list until list is empty
    while unprocessed_nodes:
        subnet_nodes = []
        current_node = unprocessed_nodes.pop()
        [unprocessed_nodes, subnet_nodes] = recursive_subnet(current_node, unprocessed_nodes, subnet_nodes, G_ind)
        subnet_list.append(subnet_nodes)

    # +++++++++++++++++++++++++++++++++++++
    # Interconnect subnets
    # ++++++++++++++++++++++++++++++++++++++

    # is plant in subnet?
    subnets_with_consumer = []
    subnets_with_plants = []
    subnets_without_plants = subnet_list[:]  # get copy of list. Not references

    # Divide list in subnets with and without plants
    for subnet_idx, subnet in enumerate(subnet_list):
        if set(plant_nodes).intersection(set(subnet)):
            subnets_with_plants.append(subnet)
            subnets_without_plants.remove(subnet)
        elif set(consumer_nodes).intersection(set(subnet)):
            subnets_with_consumer.append(subnet)
            subnets_without_plants.remove(subnet)

    # start with smallest network
    subnets_with_consumer_sorted = sorted(subnets_with_consumer, key=len)

    while subnets_with_consumer_sorted:
        # Size of lists are changing
        subnets_with_consumer_sorted = sorted(subnets_with_consumer_sorted, key=len)
        possible_connections = []

        subnet = subnets_with_consumer_sorted[0]
        for idx, node in enumerate(subnet):
            current_neighbourhood = G_complete.neighbors(node)

            for neighbour_idx, neighbour in enumerate(current_neighbourhood):
                if neighbour not in subnet:
                    edge = G_complete.edges[node, neighbour]
                    possible_connections.append(edge)

        possible_connections_sorted = sorted(possible_connections, key=itemgetter('weight'))

        # Take edge to connect subnets by random
        for edge_idx, rnd_shortest_edge in enumerate(possible_connections_sorted):
            if rnd_shortest_edge is not possible_connections_sorted[-1]:
                if random.random() < LINE_PROBABILITY:
                    shortest_edge = possible_connections_sorted[edge_idx]
                    break
            else:
                # if edge is last item in list
                shortest_edge = possible_connections_sorted[0]
                break

        # modify gene of individual and assign smallest component
        n_linetype = len(df_line_parameter) - 1

        # Assign random line type
        list_ind[shortest_edge['gene']] = random.randint(0, n_linetype)

        # identify node in other subnet
        if int(shortest_edge['startnode']) in subnet:
            other_node = int(shortest_edge['endnode'])
        else:
            other_node = int(shortest_edge['startnode'])

        subnet_copy = subnet[:]
        subnets_with_consumer_sorted.remove(subnet)

        # find list index with other node in subnets_with_plants Todo code better
        for other_subnet_idx, other_subnet in enumerate(subnets_with_plants):
            if other_node in other_subnet:
                subnets_with_plants[other_subnet_idx] = subnets_with_plants[other_subnet_idx] + subnet_copy

        # find list index with other in subnets_with_consumer_sorted
        for other_subnet_idx, other_subnet in enumerate(subnets_with_consumer_sorted):
            if other_node in other_subnet:
                subnets_with_consumer_sorted[other_subnet_idx] = subnets_with_consumer_sorted[
                                                                      other_subnet_idx] + subnet_copy

        # # find list index with other in subnets_without_plants
        for other_subnet_idx, other_subnet in enumerate(subnets_without_plants):
            if other_node in other_subnet:
                subnets_without_plants[other_subnet_idx] = subnets_without_plants[other_subnet_idx] + subnet_copy
                subnets_with_consumer_sorted.append(subnets_without_plants[other_subnet_idx])
                subnets_without_plants.remove(subnets_without_plants[other_subnet_idx])

    return list_ind


def delete_line_hard(list_ind, idx_edge, net):
    """
    This function deletes lines in network with a load less than 1 per cent with a probability of LINE_PROBABILITY

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: net: result of pandapower power flow calculation
    :type: pandapowerNET (PandaPower object)

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    """

    for idx_line, line in net.res_line.iterrows():
        if line['loading_percent'] < 1.0:
            if random.random() < LINE_PROBABILITY:
                idx_min = line.name
                line_min = net.line.loc[idx_min]
                node1 = line_min['from_bus']
                node2 = line_min['to_bus']

                idx_line = idx_edge.index((node1, node2))
                list_ind[idx_line] = 0  # delete line

    return list_ind


def delete_line_soft(list_ind, idx_edge, net):
    """
    This function deletes ONE line in network with a load less than 30.0 per cent with a probability of LINE_PROBABILITY

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: net: result of pandapower power flow calculation
    :type: pandapowerNET (PandaPower object)

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    """

    res_loadsorted = net.res_line.sort_values(by=['loading_percent'])

    if res_loadsorted.iloc[0]['loading_percent'] < 30.0:
        for idx_line, line in res_loadsorted.iterrows():
            if idx_line is not len(res_loadsorted):
                if random.random() < LINE_PROBABILITY:
                    idx_min = line.name
                    line_min = net.line.loc[idx_min]
                    node1 = line_min['from_bus']
                    node2 = line_min['to_bus']

                    idx_line = idx_edge.index((node1, node2))
                    list_ind[idx_line] = 0  # delete line
                    break
            else:
                idx_min = res_loadsorted.iloc[0].name
                line_min = net.line.loc[idx_min]
                node1 = line_min['from_bus']
                node2 = line_min['to_bus']

                idx_line = idx_edge.index((node1, node2))
                list_ind[idx_line] = 0  # delete line
                break

    return list_ind


def reinforce_lines(list_ind, idx_edge, df_line_parameter, net):
    """
    This function reinforces ALL lines in network with a load more than 90.0 per cent

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame
    :param: net: result of pandapower power flow calculation
    :type: pandapowerNET (PandaPower object)

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    """

    for idx_line, line in net.res_line.iterrows():
        if line['loading_percent'] > 90.0:
            line_min = net.line.loc[line.name]
            node1 = line_min['from_bus']
            node2 = line_min['to_bus']

            idx_line = idx_edge.index((node1, node2))

            if list_ind[idx_line] != len(df_line_parameter) - 1:
                list_ind[idx_line] = list_ind[idx_line] + 1  # enhance line

    return list_ind


def downsize_lines(list_ind, idx_edge, net):
    """
    This function downsizes ONE line in network with a less than 50.0 per cent with a probability of LINE_PROBABILITY.

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: net: result of pandapower power flow calculation
    :type: pandapowerNET (PandaPower object)

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    """

    res_loadsorted = net.res_line.sort_values(by=['loading_percent'], ascending=False)

    for idx_line, line in res_loadsorted.iterrows():
        if line['loading_percent'] < 50.0 and random.random() < LINE_PROBABILITY:
                line_max = net.line.loc[line.name]
                node1 = line_max['from_bus']
                node2 = line_max['to_bus']

                idx_line = idx_edge.index((node1, node2))

                if list_ind[idx_line] > 1:
                    list_ind[idx_line] = list_ind[idx_line] - 1  # enhance line
                    break

    return list_ind


def evaluate_emodel(list_ind, net):
    """
    This function evaluates technical properties of network. If ONE line or ONE node is overloaded or power_loss will
    be assigned infinite -> infinite fitness cost

    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param: net: result of pandapower power flow calculation
    :type: pandapowerNET (PandaPower object)

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    :returns: power_loss: power losses in Watt. Calculated with I^2*R
    :rtype: float
    """

    power_loss = 0.0

    if (net.res_line['loading_percent'] > 80.0).any():
        print 'line overloaded'
        power_loss = float('inf')
    elif (0.9 > net.res_bus['vm_pu']).any() or (1.1 < net.res_bus['vm_pu']).any():
        print 'node overloaded'
        power_loss = float('inf')
    elif net.res_line.isnull().values.any():
        print 'Powerflow infeasible'
        power_loss = float('inf')
    else:
        for idx_line, line in net.line.iterrows():
            power_loss_of_line = (line['r_ohm_per_km'] * line['length_km']) \
                                 * (net.res_line['i_from_ka'][idx_line]*1000)**2
            power_loss += power_loss_of_line  # in W

    return list_ind, power_loss


def main(idx_ind, list_ind, df_nodes, idx_edge, dict_length, df_line_parameter):
    """
    This function processes each individual regarding structural and technical properties. process_individual_network
    ensures that each demand node is electrically connected to at least one PLANT node. powerflow_mp transfers the
    networkx graph model into a pandapower model and runs a powerflow. delete_line_hard and delete_line_soft deletes
    unnecessary lines with a low load. reinforce_lines enhances lines which are near to maximum load.
    downsize_lines downsizes nodes to improve the fitness of the individual. evaluate_emodel ensures a feasible
    powerflow and calculates the power losses of the network

    :param: idx_ind: index number of the individual
    :type: int
    :param: list_ind: list of genes of an individual
    :type: list(int)
    :param: df_nodes: information about every node in study case
    :type: GeoDataFrame
    :param idx_edge: list of startnode and endnode of edges in upper triangular matrix without diagonal matrix
    :type list(startnode, endnode)
    :param: dict_length: length on street network between every node
    :type: dictionary
    :param df_line_parameter: Dataframe of electric line properties
    :type DataFrame

    :returns: list_ind: list of genes of an individual
    :rtype: list(int)
    :returns: power_loss: power losses in Watt. Calculated with I^2*R
    :rtype: float
    """

    time_start = time.time()

    # Filter intersections
    df_nodes = df_nodes[df_nodes['Type'].notnull()]

    G_complete = create_complete_graph(df_nodes, idx_edge, dict_length)

    G_ind = create_individual_graph(list_ind, df_nodes, idx_edge, dict_length)

    list_ind = process_individual_network(list_ind, G_complete, G_ind, df_line_parameter)

    net = emodel.powerflow_mp(list_ind, df_nodes, idx_edge, dict_length, df_line_parameter)

    # Not necessary block of functions for GA
    list_ind = delete_line_hard(list_ind, idx_edge, net)
    list_ind = delete_line_soft(list_ind, idx_edge, net)
    G_ind = create_individual_graph(list_ind, df_nodes, idx_edge, dict_length)
    list_ind = process_individual_network(list_ind, G_complete, G_ind, df_line_parameter)
    list_ind = reinforce_lines(list_ind, idx_edge, df_line_parameter, net)
    list_ind = downsize_lines(list_ind, idx_edge, net)
    net = emodel.powerflow_mp(list_ind, df_nodes, idx_edge, dict_length, df_line_parameter)

    list_ind, power_loss = evaluate_emodel(list_ind, net)

    print 'IND No. %02i completed out of %i in %.2f sec' % (idx_ind + 1, POP_SIZE, (time.time() - time_start))

    return list_ind, power_loss

# Draws networkx Graph
# G_ind = create_individual_graph(list_ind, df_nodes, idx_edge, dict_length)
# nx.draw(G_ind)
# plt.show()