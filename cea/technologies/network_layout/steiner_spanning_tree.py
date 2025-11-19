"""
This script calculates the minimum spanning tree of a shapefile network
"""
import math
import os
from enum import StrEnum

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from networkx.algorithms.approximation.steinertree import steiner_tree
from shapely import LineString, Point

from cea.constants import SHAPEFILE_TOLERANCE
from cea.technologies.constants import TYPE_MAT_DEFAULT, PIPE_DIAMETER_DEFAULT

from cea.technologies.network_layout.graph_utils import gdf_to_nx, normalize_coords
from cea.datamanagement.graph_helper import GraphCorrector

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_next_node_name(nodes_gdf):
    """
    Generate the next unique node name by finding the maximum existing node number.

    This prevents duplicate node names when nodes are removed from the network during
    plant creation or other operations.

    :param nodes_gdf: GeoDataFrame containing existing nodes with 'name' column
    :return: Unique node name in format 'NODE{n}' where n is max existing number + 1
    """
    existing_node_numbers = [
        int(name.replace('NODE', ''))
        for name in nodes_gdf['name']
        if isinstance(name, str) and name.startswith('NODE')
    ]
    next_node_num = max(existing_node_numbers) + 1 if existing_node_numbers else 0
    return f'NODE{next_node_num}'


class SteinerAlgorithm(StrEnum):
    """
    Enum for the different algorithms that can be used to calculate the Steiner tree.

    This is based on the available algorithms for NetworkX Steiner tree function.
    Reference:
    https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.approximation.steinertree.steiner_tree.html
    """

    Kou = 'kou'
    """
    Kou algorithm: Higher quality Steiner tree approximation with better weight optimization.
    - Runtime: O(|S| |V|²) - slower for large networks
    - Memory: High consumption, can be excessive for large graphs
    - Quality: More optimal network layouts, better weight minimization
    - Use when: Network optimization quality is critical and computational resources are sufficient
    - Algorithm: Computes minimum spanning tree of the metric closure subgraph induced by terminal nodes
    """
    
    Mehlhorn = 'mehlhorn'
    """
    Mehlhorn algorithm: Fast Steiner tree approximation optimized for speed and memory efficiency.
    - Runtime: O(|E| + |V|log|V|) - very fast, scales well with network size
    - Memory: Minimal usage, suitable for large networks
    - Quality: Good approximation but sometimes noticeably suboptimal compared to Kou
    - Use when: Speed is prioritized over perfect optimization, or working with very large networks
    - Algorithm: Modified Kou approach that finds closest terminal node for each non-terminal first
    """

    def __str__(self):
        return self.value


def calc_steiner_spanning_tree(crs_projected,
                               building_centroids_df: gdf,
                               potential_network_graph: nx.Graph,

                               path_output_edges_shp,
                               path_output_nodes_shp,

                               type_network,
                               total_demand_location,
                               allow_looped_networks,
                               plant_building_names,
                               disconnected_building_names,
                               type_mat_default=TYPE_MAT_DEFAULT,
                               pipe_diameter_default=PIPE_DIAMETER_DEFAULT,
                               method: str = SteinerAlgorithm.Kou,
                               connection_candidates: int = 1):
    """
    Calculate the minimum spanning tree of the network. Note that this function can't be run in parallel in it's
    present form.

    :param str crs_projected: e.g. "+proj=utm +zone=48N +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    :param geopandas.GeoDataFrame building_centroids_df: GeoDataFrame of building centroids
    :param nx.Graph potential_network_graph: potential network as NetworkX graph with metadata
    :param str path_output_edges_shp: "{general:scenario}/inputs/networks/DC/edges.shp"
    :param str path_output_nodes_shp: "{general:scenario}/inputs/networks/DC/nodes.shp"
    :param str type_mat_default: e.g. "T1"
    :param float pipe_diameter_default: e.g. 150
    :param str type_network: "DC" or "DH"
    :param str total_demand_location: "{general:scenario}/outputs/data/demand/Total_demand.csv"
    :param bool create_plant: e.g. True
    :param bool allow_looped_networks:
    :param List[str] plant_building_names: e.g. ``['B001']``
    :param List[str] disconnected_building_names: e.g. ``['B002', 'B010', 'B004', 'B005', 'B009']``
    :param method: The algorithm to use for calculating the Steiner tree. Default is Kou.
    :param int connection_candidates: Number of nearest street connection points to consider per building.
        Default is 1 (greedy nearest). Values of 3-5 enable better optimization via Kou's metric closure.
        Only works with Kou algorithm - Mehlhorn will use greedy nearest regardless.
    :return: ``(mst_edges, mst_nodes)``
    """
    steiner_algorithm = SteinerAlgorithm(method)

    # Validate connection_candidates with Mehlhorn algorithm
    if connection_candidates > 1 and steiner_algorithm == SteinerAlgorithm.Mehlhorn:
        print("  ⚠ Warning: connection_candidates > 1 requires Kou algorithm for optimization.")
        print("             Mehlhorn does not compute metric closure. Using greedy nearest connection.")
        connection_candidates = 1

    # TODO: Ensure CRS is used properly throughout the function (currently not applied)
    # read building centroids shapefile into networkx format

    building_nodes_graph = gdf_to_nx(building_centroids_df.to_crs(crs_projected), name="name")

    if potential_network_graph is None or building_nodes_graph is None:
        raise ValueError('Could not read potential network or building centroids shapefiles. '
                         'Please check the files exist and are valid shapefiles.')

    # Extract original_junctions from graph metadata (if available)
    # This metadata is set by calc_connectivity_network_with_geometry
    original_junctions = potential_network_graph.graph.get('original_junctions', set())

    # transform to an undirected graph
    # Note: Graph corrections are now applied in calc_connectivity_network BEFORE
    # building terminals are connected, to ensure terminal nodes are not affected
    G = potential_network_graph.to_undirected()

    # get the building nodes and coordinates
    # Normalize coordinates to ensure consistent precision (prevents floating-point matching issues)
    iterator_nodes = building_nodes_graph.nodes
    terminal_nodes_coordinates = []
    terminal_nodes_names = []
    for coordinates, data in iterator_nodes.data():
        building_name = data['name']
        if building_name in disconnected_building_names:
            print("Building {} is considered to be disconnected and it is not included".format(building_name))
        else:
            terminal_nodes_coordinates.append(normalize_coords([coordinates])[0])
            terminal_nodes_names.append(data['name'])

    # Validate graph is ready for Steiner tree with terminal nodes
    is_ready, message = GraphCorrector.validate_steiner_tree_ready(G, terminal_nodes_coordinates)
    if not is_ready:
        raise ValueError(f'Graph validation failed before Steiner tree: {message}. '
                        f'This should not happen after corrections. Please report this issue.')

    # Handle single-building case (no optimization needed)
    if len(terminal_nodes_coordinates) == 1:
        print("  Single building network: Skipping Steiner tree optimization")
        mst_non_directed = nx.Graph()
        mst_non_directed.add_node(terminal_nodes_coordinates[0])
    else:
        # Calculate steiner spanning tree for multi-building network
        try:
            # Note: steiner_tree() already returns a tree (both Kou and Mehlhorn algorithms)
            # No need for additional MST computation
            mst_non_directed = steiner_tree(G, terminal_nodes_coordinates, method=steiner_algorithm)
        except Exception as e:
            raise ValueError('There was an error while creating the Steiner tree despite graph corrections. '
                            'This is an unexpected error. Please report this issue with your streets.shp file.') from e

    # Enforce constraints:
    # 1) Building terminals should be leaves (degree == 1)
    # 2) No direct building-to-building edges (must route through street network)
    def _enforce_terminal_leafs_and_no_b2b(full_graph: nx.Graph, steiner_graph: nx.Graph, terminals: set[tuple]) -> nx.Graph:
        sg = steiner_graph.copy()

        # Helper to add a path from full_graph into sg
        def _add_path_edges(path_nodes):
            for u, v in zip(path_nodes[:-1], path_nodes[1:]):
                if sg.has_edge(u, v):
                    continue
                data = full_graph.get_edge_data(u, v, default={})
                # Fallback weight if missing
                weight = data.get('weight', LineString([u, v]).length)
                geom = data.get('geometry', LineString([u, v]))
                sg.add_edge(u, v, weight=weight, geometry=geom)

        terminals_set = set(tuple(t) for t in terminals)

        # Pre-create a graph with all terminals removed for efficient shortest path queries
        # This avoids copying the full graph for every reroute operation (major performance optimization)
        G_no_terminals = full_graph.copy()
        for t in terminals_set:
            if G_no_terminals.has_node(t):
                G_no_terminals.remove_node(t)

        # 2) Remove direct building-to-building edges, replace with street path
        b2b_edges = [(u, v) for u, v in sg.edges() if u in terminals_set and v in terminals_set]
        for u, v in b2b_edges:
            # Compute shortest path between u and v in the street network (no terminals)
            # Add back only the source and target terminals for this query
            G2 = G_no_terminals.copy()
            # Re-add u and v terminals with their edges to streets
            for term in [u, v]:
                # Add the terminal node itself first
                if not G2.has_node(term):
                    # Copy node attributes from full_graph
                    if full_graph.has_node(term):
                        G2.add_node(term, **full_graph.nodes[term])
                    else:
                        G2.add_node(term)
                # Then add edges to street nodes
                for neighbor in full_graph.neighbors(term):
                    if neighbor not in terminals_set:  # Only connect to street nodes
                        edge_data = full_graph.get_edge_data(term, neighbor, default={})
                        G2.add_edge(term, neighbor, **edge_data)
            
            try:
                path = nx.shortest_path(G2, source=u, target=v, weight='weight')
            except nx.NetworkXNoPath:
                # If no alternate path, keep edge but warn (shouldn't happen with proper streets)
                print(f"  ⚠ Warning: No street path found to replace building-to-building edge {u}–{v}")
                continue
            # Replace edge with path along streets
            if sg.has_edge(u, v):
                sg.remove_edge(u, v)
            _add_path_edges(path)

        # 1) Enforce terminal nodes as leaves
        for t in list(terminals_set):
            if not sg.has_node(t):
                continue
            # While degree > 1, keep shortest incident edge and reroute others via streets
            while True:
                neighbours = list(sg.neighbors(t))
                if len(neighbours) <= 1:
                    break
                # Choose the neighbour connected by the smallest weight edge
                def edge_w(nbr):
                    data = sg.get_edge_data(t, nbr, default={})
                    return data.get('weight', LineString([t, nbr]).length)
                keep = min(neighbours, key=edge_w)
                to_reroute = [n for n in neighbours if n != keep]

                # Reroute each extra neighbour to 'keep' via streets without passing through building terminals
                # Build a query graph with only n and keep terminals added back (all other terminals excluded)
                for n in to_reroute:
                    G2 = G_no_terminals.copy()
                    # Re-add n and keep terminals with their edges to streets
                    for term in [n, keep]:
                        # Add the terminal node itself first
                        if not G2.has_node(term):
                            # Copy node attributes from full_graph
                            if full_graph.has_node(term):
                                G2.add_node(term, **full_graph.nodes[term])
                            else:
                                G2.add_node(term)
                        # Then add edges to street nodes
                        for neighbor in full_graph.neighbors(term):
                            if neighbor not in terminals_set:  # Only connect to street nodes
                                edge_data = full_graph.get_edge_data(term, neighbor, default={})
                                G2.add_edge(term, neighbor, **edge_data)
                    
                    try:
                        path = nx.shortest_path(G2, source=n, target=keep, weight='weight')
                        # Add reroute path
                        _add_path_edges(path)
                    except nx.NetworkXNoPath:
                        # If no path, we still need to remove the edge to avoid infinite loop
                        print(f"  ⚠ Warning: Unable to reroute extra terminal edge from {t} to {n}")
                    
                    # Always remove the direct terminal edge (whether rerouted successfully or not)
                    if sg.has_edge(t, n):
                        sg.remove_edge(t, n)

        # Finalize: return a minimum spanning tree to remove any cycles introduced by rerouting
        # Use weight attribute to keep distances consistent
        if sg.number_of_edges() > 0:
            sg = nx.minimum_spanning_tree(sg, weight='weight')
        return sg

    # Apply enforcement using the full potential graph (G) and terminal set
    terminals_set = set(terminal_nodes_coordinates)
    mst_non_directed = _enforce_terminal_leafs_and_no_b2b(G, mst_non_directed, terminals_set)

    # Post-Steiner cleanup: remove non-terminal leaf stubs, then contract street chains
    def _prune_nonterminal_leaves(steiner_graph: nx.Graph, terminals: set[tuple]) -> nx.Graph:
        sg = steiner_graph.copy()
        changed = True
        terminals = set(tuple(t) for t in terminals)
        while changed:
            changed = False
            leaves = []
            for n in list(sg.nodes()):
                if n in terminals:
                    continue
                if len(list(sg.neighbors(n))) == 1:
                    leaves.append(n)
            for n in leaves:
                sg.remove_node(n)
                changed = True
        return sg

    def _geometry_endpoints(line: LineString):
        coords = list(line.coords)
        return tuple(coords[0]), tuple(coords[-1])

    def _merge_two_edges(u, n, v, data_un, data_nv) -> tuple[LineString, float]:
        geom1: LineString = data_un.get('geometry', LineString([u, n]))
        geom2: LineString = data_nv.get('geometry', LineString([n, v]))

        # Orient so that geom1 ends at n and geom2 starts at n
        g1s, g1e = _geometry_endpoints(geom1)
        g2s, g2e = _geometry_endpoints(geom2)

        if g1e != n and g1s == n:
            # reverse geom1
            geom1 = LineString(list(geom1.coords)[::-1])
            g1s, g1e = g1e, g1s
        if g2s != n and g2e == n:
            # reverse geom2
            geom2 = LineString(list(geom2.coords)[::-1])
            g2s, g2e = g2e, g2s

        # Concatenate, avoiding duplicate n
        merged_coords = list(geom1.coords) + list(geom2.coords)[1:]
        merged = LineString(merged_coords)
        length = merged.length
        return merged, length

    def _contract_degree2_street_nodes(full_graph: nx.Graph, steiner_graph: nx.Graph, terminals: set[tuple], original_junctions: set[tuple] | None = None) -> nx.Graph:
        sg = steiner_graph.copy()
        terminals = set(tuple(t) for t in terminals)
        original_junctions = set(tuple(j) for j in (original_junctions or set()))

        # Helper to decide if an edge is a service stub (touches a terminal)
        def is_service_edge(a, b):
            return a in terminals or b in terminals

        changed = True
        while changed:
            changed = False
            # Work on a snapshot of nodes to avoid iteration issues
            for n in list(sg.nodes()):
                if n in terminals:
                    continue
                # Preserve original street junctions (degree >= 3 intersections)
                if n in original_junctions:
                    continue
                if n not in sg:
                    continue
                neigh = list(sg.neighbors(n))
                if len(neigh) != 2:
                    continue
                a, b = neigh[0], neigh[1]

                # Do not merge across terminal edges
                if is_service_edge(a, n) or is_service_edge(n, b):
                    continue

                # Fetch edge data
                data_an = sg.get_edge_data(a, n, default={})
                data_nb = sg.get_edge_data(n, b, default={})

                # Merge geometries and lengths
                merged_geom, merged_len = _merge_two_edges(a, n, b, data_an, data_nb)

                # Remove old and add merged
                if sg.has_edge(a, n):
                    sg.remove_edge(a, n)
                if sg.has_edge(n, b):
                    sg.remove_edge(n, b)

                if sg.has_node(n) and len(list(sg.neighbors(n))) == 0:
                    sg.remove_node(n)

                # Add merged edge with geometry and weight
                sg.add_edge(a, b, geometry=merged_geom, weight=merged_len)
                changed = True
        return sg

    # 1) prune dangling non-terminal leaves
    mst_non_directed = _prune_nonterminal_leaves(mst_non_directed, terminals_set)
    # 2) contract degree-2 street chains (while preserving original junctions)
    mst_non_directed = _contract_degree2_street_nodes(G, mst_non_directed, terminals_set, original_junctions)

    # Reporting helper: print network stats and total length
    def _report_network_stats(graph: nx.Graph, terminals: set[tuple], label: str = "Final"):
        terminals = set(tuple(t) for t in terminals)
        # Degrees
        deg = {n: len(list(graph.neighbors(n))) for n in graph.nodes()}
        non_terminal_leaves = [n for n, d in deg.items() if d == 1 and n not in terminals]
        terminals_bad_degree = [n for n in terminals if n in graph and deg.get(n, 0) != 1]
        # B2B edges (should be none)
        b2b = [(u, v) for u, v in graph.edges() if u in terminals and v in terminals]
        # Total length
        total_len = 0.0
        for u, v, data in graph.edges(data=True):
            if 'weight' in data and isinstance(data['weight'], (int, float)):
                total_len += float(data['weight'])
            else:
                try:
                    from shapely import LineString as _LS
                    total_len += _LS([u, v]).length
                except Exception:
                    # Fallback: ignore
                    pass
        print(f"\n{label} network stats:")
        print(f"  Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")
        print(f"  Terminals: {len(terminals)} | Non-terminal leaves: {len(non_terminal_leaves)}")
        if terminals_bad_degree:
            print(f"  ⚠ Terminals with degree !=1: {len(terminals_bad_degree)}")
        if b2b:
            print(f"  ⚠ Building-to-building edges: {len(b2b)}")
        print(f"  Total edge length: {total_len:.2f} m")

    _report_network_stats(mst_non_directed, terminals_set, label="Final")

    mst_nodes = gdf([{
        "geometry": Point(coords),
    } for coords in mst_non_directed.nodes()], crs=crs_projected)
    
    # since edges of graph is guranteed to be connected to nodes, we alter the edge geometries to snap to the nodes before writing to shapefile
    # This is to avoid small discrepancies due to rounding errors or slight misalignments when creating the graph from shapefiles (defensive programming)
    def replace_start_endpoints(line: LineString, u, v):
        from shapely.geometry import Point

        coords = list(line.coords)
        start_point = Point(coords[0])

        u_point = Point(u)
        v_point = Point(v)

        # Determine which node is closer to which endpoint
        dist_u_to_start = start_point.distance(u_point)
        dist_v_to_start = start_point.distance(v_point)

        if dist_u_to_start < dist_v_to_start:
            # u is closer to start, v is closer to end
            coords[0] = u
            coords[-1] = v
        else:
            # v is closer to start, u is closer to end
            coords[0] = v
            coords[-1] = u

        return LineString(coords)

    mst_edges = gdf({
        "geometry": [replace_start_endpoints(data['geometry'], u, v) 
                     for u, v, data in mst_non_directed.edges(data=True)]}, crs=crs_projected)

    # Handle single-building case (no edges)
    if len(mst_edges) == 0:
        # Create empty GeoDataFrame with proper schema
        mst_edges = gdf(
            columns=['geometry', 'type_mat', 'pipe_DN', 'name', 'weight'],
            geometry='geometry',
            crs=crs_projected
        )
        print("  Single-building network: No edges created")
    else:
        # Recalculate weights after snapping
        mst_edges['weight'] = mst_edges.geometry.length

    # POPULATE FIELDS IN NODES
    pointer_coordinates_building_names = dict(zip(terminal_nodes_coordinates, terminal_nodes_names))

    def populate_fields(coordinate):
        if coordinate in terminal_nodes_coordinates:
            return pointer_coordinates_building_names[coordinate]
        else:
            return "NONE"

    # Extract normalized coordinates to ensure consistent precision
    mst_nodes['coordinates'] = mst_nodes['geometry'].apply(
        lambda x: normalize_coords([x.coords[0]])[0]
    )
    mst_nodes['building'] = mst_nodes['coordinates'].apply(lambda x: populate_fields(x))
    mst_nodes['name'] = mst_nodes.index.map(lambda x: "NODE" + str(x))
    mst_nodes['type'] = mst_nodes['building'].apply(lambda x: 'CONSUMER' if x != "NONE" else "NONE")

    # Add junction type metadata to identify original street junctions
    original_junctions = original_junctions or set()
    def get_junction_type(coord):
        if coord in terminal_nodes_coordinates:
            return 'TERMINAL'
        elif coord in original_junctions:
            return 'ORIGINAL_JUNCTION'
        else:
            return 'NONE'

    mst_nodes['Type_node'] = mst_nodes['coordinates'].apply(get_junction_type)
    
    if set(terminal_nodes_names) != (set(mst_nodes['building'].unique()) - {'NONE'} ):
        raise ValueError('There was an error while populating the nodes fields. '
                         'One or more buildings could not be matched to nodes of the network. '
                         'Try changing the constant SNAP_TOLERANCE in cea/constants.py to try to fix this')

    # POPULATE FIELDS IN EDGES
    mst_edges.loc[:, 'type_mat'] = type_mat_default
    mst_edges.loc[:, 'pipe_DN'] = pipe_diameter_default
    mst_edges.loc[:, 'name'] = ["PIPE" + str(x) for x in mst_edges.index]

    if allow_looped_networks:
        # add loops to the network by connecting None nodes that exist in the potential network
        mst_edges, mst_nodes = add_loops_to_network(G,
                                                    mst_non_directed,
                                                    mst_nodes,
                                                    mst_edges,
                                                    type_mat_default,
                                                    pipe_diameter_default)
        # mst_edges.drop(['weight'], inplace=True, axis=1)

    elif os.path.exists(total_demand_location):
        # Check if we should skip plant creation (indicated by None)
        if plant_building_names is not None and len(plant_building_names) > 0:
            # Create a PLANT node for each specified plant building
            for plant_building_name in plant_building_names:
                building_anchor = mst_nodes[mst_nodes['building'] == plant_building_name]
                if not building_anchor.empty:
                    mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, mst_nodes, mst_edges,
                                                                     type_mat_default, pipe_diameter_default)
                else:
                    print(f"  ⚠ Warning: Plant building '{plant_building_name}' not found in network, skipping")
        elif plant_building_names is not None and type_network in ['DC', 'DH']:
            # Only create anchor-based plant for single network types (not DC+DH)
            # If plant_building_names is None, skip plant creation (caller will add plants)
            # If plant_building_names is [], create anchor-based plant
            building_anchor = calc_coord_anchor(total_demand_location, mst_nodes, type_network)
            mst_nodes, mst_edges = add_plant_close_to_anchor(building_anchor, mst_nodes, mst_edges,
                                                             type_mat_default, pipe_diameter_default)

    mst_edges.crs = crs_projected
    mst_nodes.crs = crs_projected
    mst_edges['length_m'] = mst_edges['weight']
    mst_edges[['geometry', 'length_m', 'type_mat', 'name', 'pipe_DN']].to_file(path_output_edges_shp,
                                                                               driver='ESRI Shapefile')
    mst_nodes[['geometry', 'building', 'name', 'type']].to_file(path_output_nodes_shp, driver='ESRI Shapefile')


def _get_missing_neighbours(node_coords, potential_graph: nx.Graph, steiner_graph: nx.Graph):
    """
    Find neighbours that exist in potential network but not in steiner network.

    :param node_coords: Coordinates of the node to check
    :param potential_graph: Full potential network graph
    :param steiner_graph: Current steiner tree graph
    :return: List of missing neighbour coordinates
    """
    potential_neighbours = set(potential_graph[node_coords].keys())
    steiner_neighbours = set(steiner_graph[node_coords].keys())
    return list(potential_neighbours - steiner_neighbours)


def _make_edge_key(coord1, coord2):
    """
    Create a unique edge key from two coordinates.
    Uses frozenset to make edges undirected (A->B == B->A).

    :param coord1: First coordinate tuple
    :param coord2: Second coordinate tuple
    :return: frozenset edge key
    """
    return frozenset([tuple(coord1), tuple(coord2)])


def _add_edge_to_network(mst_edges: gdf, start_coords, end_coords, pipe_dn, type_mat, existing_edges: set) -> gdf:
    """
    Add an edge to the network if it doesn't already exist.

    :param mst_edges: Current edges GeoDataFrame
    :param start_coords: Start point coordinates
    :param end_coords: End point coordinates
    :param pipe_dn: Pipe diameter
    :param type_mat: Pipe material type
    :param existing_edges: Set of existing edge keys (frozensets of coordinate tuples)
    :return: Updated edges GeoDataFrame
    """
    edge_key = _make_edge_key(start_coords, end_coords)

    if edge_key not in existing_edges:
        line = LineString((start_coords, end_coords))
        # Calculate weight from line length
        edge_weight = line.length
        # Get next pipe number from existing pipe names
        existing_pipe_numbers = [int(name.replace('PIPE', '')) for name in mst_edges['name'] if name.startswith('PIPE')]
        next_pipe_num = max(existing_pipe_numbers) + 1 if existing_pipe_numbers else 0
        new_edge = pd.DataFrame([{
            "geometry": line,
            "pipe_DN": pipe_dn,
            "type_mat": type_mat,
            "name": f"PIPE{next_pipe_num}",
            "weight": edge_weight
        }])
        mst_edges = gdf(
            pd.concat([mst_edges, new_edge], ignore_index=True),
            crs=mst_edges.crs
        )
        # Add to existing edges set
        existing_edges.add(edge_key)

    return mst_edges


def add_loops_to_network(G: nx.Graph, mst_non_directed: nx.Graph, new_mst_nodes: gdf, mst_edges: gdf, type_mat, pipe_dn) -> tuple[gdf, gdf]:
    added_a_loop = False

    # Initialize set of existing edges from current mst_edges
    existing_edges = set()
    for geom in mst_edges.geometry:
        coords = list(geom.coords)
        if len(coords) >= 2:
            edge_key = _make_edge_key(coords[0], coords[-1])
            existing_edges.add(edge_key)

    # Filter to only NONE type nodes
    none_nodes = new_mst_nodes[new_mst_nodes['type'] == 'NONE']
    none_coords = set(tuple(row.coordinates) for row in none_nodes.itertuples())

    # Identify all NONE type nodes in the steiner tree
    for row in none_nodes.itertuples():
        node_coords = row.coordinates

        # Find neighbours missing from steiner network
        missing_neighbours = _get_missing_neighbours(node_coords, G, mst_non_directed)

        # Check if the missing neighbour is also a NONE type node
        for new_neighbour in missing_neighbours:
            if tuple(new_neighbour) in none_coords:
                # Add edge between the two NONE nodes
                mst_edges = _add_edge_to_network(mst_edges, node_coords, new_neighbour, pipe_dn, type_mat, existing_edges)
                added_a_loop = True
    
    if not added_a_loop:
        print('No first degree loop added. Trying two nodes apart.')

        # Rebuild sets in case new_mst_nodes was modified in first loop
        none_nodes = new_mst_nodes[new_mst_nodes['type'] == 'NONE']
        none_coords = set(tuple(row.coordinates) for row in none_nodes.itertuples())

        # Create set of all node coordinates (for checking if intermediate node exists)
        all_coords = set(tuple(row.coordinates) for row in new_mst_nodes.itertuples())

        # Identify all NONE type nodes in the steiner tree
        for row in none_nodes.itertuples():
            node_coords = row.coordinates

            # Find neighbours missing from steiner network
            missing_neighbours = _get_missing_neighbours(node_coords, G, mst_non_directed)

            # Check if missing neighbour does NOT exist in steiner (need to go two hops)
            for new_neighbour in missing_neighbours:
                if tuple(new_neighbour) not in all_coords:
                    # Find neighbours of that intermediate node (two hops away)
                    second_degree_pot_neigh = list(G[new_neighbour].keys())
                    for potential_second_deg_neighbour in second_degree_pot_neigh:
                        if potential_second_deg_neighbour != node_coords:
                            if tuple(potential_second_deg_neighbour) in none_coords:
                                # Add first edge (to intermediate node)
                                mst_edges = _add_edge_to_network(mst_edges, node_coords, new_neighbour, pipe_dn, type_mat, existing_edges)

                                # Add new intermediate node from potential network to steiner tree
                                copy_of_new_mst_nodes = new_mst_nodes.copy()
                                x_distance = new_neighbour[0] - node_coords[0]
                                y_distance = new_neighbour[1] - node_coords[1]
                                copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(
                                    xoff=x_distance, yoff=y_distance)
                                selected_node = copy_of_new_mst_nodes[
                                    copy_of_new_mst_nodes["coordinates"] == node_coords]
                                selected_node["name"] = get_next_node_name(new_mst_nodes)
                                selected_node["type"] = "NONE"
                                geom = selected_node.geometry.values[0]
                                normalized_coords = (round(geom.coords[0][0], SHAPEFILE_TOLERANCE),
                                                     round(geom.coords[0][1], SHAPEFILE_TOLERANCE))
                                selected_node["coordinates"] = normalized_coords
                                if normalized_coords not in all_coords:
                                    new_mst_nodes = gdf(
                                        pd.concat([new_mst_nodes, selected_node], ignore_index=True),
                                        crs=new_mst_nodes.crs
                                    )
                                    # Update all_coords set
                                    all_coords.add(normalized_coords)

                                # Add second edge (from intermediate to second degree neighbour)
                                mst_edges = _add_edge_to_network(mst_edges, new_neighbour, potential_second_deg_neighbour, pipe_dn, type_mat, existing_edges)
                                added_a_loop = True
    if not added_a_loop:
        print('No loops added.')
    return mst_edges, new_mst_nodes


def calc_coord_anchor(total_demand_location, nodes_df, type_network):
    total_demand = pd.read_csv(total_demand_location)
    nodes_names_demand = nodes_df.merge(total_demand, left_on="building", right_on="name", how="inner")
    if type_network == "DH":
        field = "QH_sys_MWhyr"
    elif type_network == "DC":
        field = "QC_sys_MWhyr"
    else:
        raise ValueError("Invalid value for variable 'type_network': {type_network}".format(type_network=type_network))

    max_value = nodes_names_demand[field].max()
    building_series = nodes_names_demand[nodes_names_demand[field] == max_value]

    return building_series


def building_node_from_name(building_name, nodes_df):
    building_series = nodes_df[nodes_df['building'] == building_name]
    return building_series


def add_plant_close_to_anchor(building_anchor, new_mst_nodes: gdf, mst_edges: gdf, type_mat, pipe_dn):
    # find closest node
    copy_of_new_mst_nodes = new_mst_nodes.copy()
    building_coordinates = building_anchor.geometry.values[0].coords
    x1 = building_coordinates[0][0]
    y1 = building_coordinates[0][1]
    delta = 10E24  # big number
    node_id = None

    for node in copy_of_new_mst_nodes.iterrows():
        if node[1]['type'] == 'NONE':
            x2 = node[1].geometry.coords[0][0]
            y2 = node[1].geometry.coords[0][1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if 0 < distance < delta:
                delta = distance
                node_id = node[1]['name']

    if node_id is None:
        # Single building network - no NONE nodes available
        # Create plant node offset from the building node itself
        building_node = building_anchor.iloc[0]
        node_id = building_node['name']
        print("    Single-building network: Creating plant node offset from building node")

    # create copy of selected node and add to list of all nodes
    copy_of_new_mst_nodes.geometry = copy_of_new_mst_nodes.translate(xoff=1, yoff=1)
    selected_node = copy_of_new_mst_nodes[copy_of_new_mst_nodes["name"] == node_id].iloc[[0]]

    # Generate unique node name (prevents duplicates when nodes are removed during plant creation)
    selected_node["name"] = get_next_node_name(new_mst_nodes)

    selected_node["type"] = "PLANT"
    new_mst_nodes = gdf(
        pd.concat([new_mst_nodes, selected_node], ignore_index=True),
        crs=new_mst_nodes.crs
    )

    # create new edge
    point1 = (selected_node.iloc[0].geometry.x, selected_node.iloc[0].geometry.y)
    point2 = (new_mst_nodes[new_mst_nodes["name"] == node_id].iloc[0].geometry.x,
              new_mst_nodes[new_mst_nodes["name"] == node_id].iloc[0].geometry.y)
    line = LineString((point1, point2))
    edge_weight = line.length
    # Get next pipe number from existing pipe names
    existing_pipe_numbers = [int(name.replace('PIPE', '')) for name in mst_edges['name'] if name.startswith('PIPE')]
    next_pipe_num = max(existing_pipe_numbers) + 1 if existing_pipe_numbers else 0
    new_edge = gdf(
        pd.DataFrame([{"geometry": line, "pipe_DN": pipe_dn, "type_mat": type_mat,
                       "name": f"PIPE{next_pipe_num}", "weight": edge_weight}]),
        crs=mst_edges.crs
    )
    mst_edges = gdf(
        pd.concat( [mst_edges, new_edge], ignore_index=True),
        crs=mst_edges.crs
    )

    # Validation: Check for duplicate node names
    if new_mst_nodes['name'].duplicated().any():
        duplicates = new_mst_nodes[new_mst_nodes['name'].duplicated(keep=False)]['name'].unique().tolist()
        raise ValueError(f"Duplicate node names detected after adding plant node: {duplicates}")

    return new_mst_nodes, mst_edges
