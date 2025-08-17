"""
Network topology operations for thermal network flow direction initialization.

This module contains functions for performing topological analysis and initialization
of flow directions in thermal networks using graph algorithms like Breadth-First Search (BFS).

These are NOT physics-based calculations, but rather fast heuristic approaches
to provide reasonable initial guesses for flow directions based on network topology.
"""

import time


def fix_flow_directions_bfs_topology(edge_node_df, all_nodes_df, edge_df):
    """
    Initialize flow directions using Breadth-First Search (BFS) from plant nodes.
    
    BFS (Breadth-First Search) is a graph traversal algorithm that explores the network
    topology level by level, starting from plant nodes and working outward. This provides
    a reasonable initial guess for flow directions based on network topology.
    
    NOTE: This is NOT a physics-based flow calculation. It's a purely topological approach
    that assumes flow goes from plants outward through the network to consumers. The actual
    flow directions and magnitudes will be calculated later using proper hydraulic equations.
    
    This replaces the problematic infinite loop with a fast O(N+E) deterministic approach.

    :param edge_node_df: edge-node incidence matrix
    :param all_nodes_df: node information (type, building)  
    :param edge_df: edge information (start node, end node, length)
    :return: edge_node_df and edge_df with initial flow directions set
    """
    print(f'PERFORMANCE: Starting topology-based flow direction initialization (BFS)...')
    timer_start = time.perf_counter()

    # Make copies to avoid modifying originals
    edge_node_df = edge_node_df.copy()
    edge_df = edge_df.copy()

    # Build adjacency information once (fast O(E) operation)
    adjacency, edge_lookup = build_network_adjacency_and_lookup(edge_df)

    # Get plant nodes
    plant_nodes = all_nodes_df[all_nodes_df['type'] == 'PLANT'].index.tolist()
    print(f'PERFORMANCE: Found {len(plant_nodes)} plant nodes for BFS traversal')

    # BFS from each plant to set initial flow directions
    visited = set()
    for plant in plant_nodes:
        if plant not in visited:
            bfs_traverse_and_set_directions(plant, adjacency, edge_lookup, edge_node_df, edge_df, visited)

    print(f'PERFORMANCE: Topology-based flow direction initialization took {time.perf_counter() - timer_start:.2f} seconds')
    return edge_node_df, edge_df


def build_network_adjacency_and_lookup(edge_df):
    """
    Build network adjacency list and edge lookup table in single pass.
    
    Creates data structures for fast network traversal:
    - adjacency: {node: [(neighbor, edge_name), ...]} for graph traversal
    - edge_lookup: {(node1, node2): edge_name} for O(1) edge access
    
    :param edge_df: DataFrame with edge information (start node, end node)
    :return: tuple of (adjacency dict, edge_lookup dict)
    """
    adjacency = {}
    edge_lookup = {}
    
    for edge_name, edge_info in edge_df.iterrows():
        start_node = edge_info['start node']
        end_node = edge_info['end node']
        
        # Build adjacency list
        if start_node not in adjacency:
            adjacency[start_node] = []
        if end_node not in adjacency:
            adjacency[end_node] = []
            
        adjacency[start_node].append((end_node, edge_name))
        adjacency[end_node].append((start_node, edge_name))
        
        # Build edge lookup table (O(1) access instead of O(E) search)
        edge_lookup[(start_node, end_node)] = edge_name
        edge_lookup[(end_node, start_node)] = edge_name
    
    return adjacency, edge_lookup


def bfs_traverse_and_set_directions(start_plant, adjacency, edge_lookup, edge_node_df, edge_df, visited):
    """
    Perform Breadth-First Search (BFS) traversal from a plant node to set initial flow directions.
    
    BFS explores the network level by level, setting flow directions from parent to child
    as it traverses. This creates a tree-like flow pattern from each plant outward.
    
    :param start_plant: Plant node to start BFS traversal from
    :param adjacency: Network adjacency list {node: [(neighbor, edge_name), ...]}
    :param edge_lookup: Fast edge lookup {(node1, node2): edge_name} 
    :param edge_node_df: Edge-node incidence matrix to update
    :param edge_df: Edge dataframe to update
    :param visited: Set of visited nodes (shared across multiple BFS calls)
    """
    queue = [start_plant]
    visited.add(start_plant)
    nodes_processed = 0
    
    while queue:
        current_node = queue.pop(0)
        
        # Process all unvisited neighbors
        for neighbor_node, edge_name in adjacency.get(current_node, []):
            if neighbor_node not in visited:
                # Set topological flow direction: current_node → neighbor_node
                set_edge_flow_direction(current_node, neighbor_node, edge_name, edge_node_df, edge_df)
                
                queue.append(neighbor_node)
                visited.add(neighbor_node)
                nodes_processed += 1
    
    print(f'PERFORMANCE: BFS traversal from plant {start_plant} processed {nodes_processed} nodes')


def set_edge_flow_direction(from_node, to_node, edge_name, edge_node_df, edge_df):
    """
    Set initial flow direction from from_node to to_node for the given edge.
    
    This sets the edge-node incidence matrix values and updates the edge dataframe
    to reflect the assumed flow direction. Note: This is only an initial guess
    based on network topology - actual flow directions will be determined later
    by the hydraulic solver.
    
    :param from_node: Node where flow is assumed to originate  
    :param to_node: Node where flow is assumed to go to
    :param edge_name: Name of the edge to update
    :param edge_node_df: Edge-node incidence matrix to update
    :param edge_df: Edge dataframe to update
    """
    # Set edge_node_df directions
    edge_node_df.loc[from_node, edge_name] = -1  # outgoing from from_node
    edge_node_df.loc[to_node, edge_name] = 1     # incoming to to_node
    
    # Update edge_df to match assumed flow direction
    edge_df.loc[edge_name, 'start node'] = from_node
    edge_df.loc[edge_name, 'end node'] = to_node