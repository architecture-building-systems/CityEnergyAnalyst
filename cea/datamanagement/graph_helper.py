"""
Graph correction utilities for street network graphs.

This module provides centralized graph correction methods to fix common connectivity issues
in street network graphs obtained from OpenStreetMap. These corrections ensure that the
graphs are suitable for Steiner tree optimization and network layout calculations.

TYPICAL USAGE
=============

Basic usage - automatic corrections:
    from cea.datamanagement.graph_helper import GraphCorrector
    corrector = GraphCorrector(street_network_graph)
    corrected_graph = corrector.apply_corrections()
    print(corrector.get_corrections_log())

Manual usage - specific corrections:
    corrector = GraphCorrector(street_network_graph)
    corrector.merge_close_nodes()
    corrector.connect_intersecting_edges()
    corrected_graph = corrector.graph

Validate before Steiner tree:
    is_ready, message = GraphCorrector.validate_steiner_tree_ready(graph, terminal_nodes)
    if not is_ready:
        print(f"Graph validation failed: {message}")

CORRECTION PIPELINE
===================

The apply_corrections() method applies corrections in this order:
1. Remove self-loops - Eliminates invalid edges from nodes to themselves
2. Merge close nodes - Fixes coordinate precision issues (within SNAP_TOLERANCE = 0.1m)
3. Connect intersecting edges - Adds junction nodes where edges cross but don't connect
4. Connect disconnected components - Last resort: adds edges between nearest nodes

Each correction logs its actions for traceability.
"""

import math
import networkx as nx
from typing import Optional, Tuple, List, Set, Dict
from scipy.spatial import KDTree
import warnings

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Mathias Niffeler"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


class GraphCorrector:
    """
    Centralized graph correction utilities for street network graphs.

    This class provides methods to detect and fix common graph connectivity issues
    that prevent Steiner tree optimization from running successfully. It maintains
    a log of all corrections applied to the graph for traceability.

    The typical workflow is:
    1. Create a GraphCorrector instance with the problematic graph
    2. Call apply_corrections() to automatically fix common issues
    3. Retrieve the corrected graph and review the corrections log

    :param graph: NetworkX graph to be corrected
    :type graph: nx.Graph
    :param coord_precision: Number of decimal places for coordinate rounding (default: SHAPEFILE_TOLERANCE)
    :type coord_precision: int

    Example usage:
        from cea.datamanagement.graph_helper import GraphCorrector
        corrector = GraphCorrector(street_network_graph)
        corrected_graph = corrector.apply_corrections()
        print(f"Applied {len(corrector.get_corrections_log())} corrections")
        is_ready, msg = GraphCorrector.validate_steiner_tree_ready(corrected_graph, terminal_nodes)
    """

    def __init__(self, graph: nx.Graph, coord_precision: int = SHAPEFILE_TOLERANCE, protected_nodes: Optional[List] = None):
        """
        Initialize the GraphCorrector with a graph to be corrected.

        :param graph: NetworkX graph to be corrected
        :type graph: nx.Graph
        :param coord_precision: Number of decimal places for coordinate rounding
        :type coord_precision: int
        :param protected_nodes: List of nodes that should not be merged (e.g., building terminals)
        :type protected_nodes: Optional[List]
        """
        self.graph = graph.copy()  # Work on a copy to preserve original
        self.original_graph = graph
        self.coord_precision = coord_precision

        # Normalize protected node coordinates for comparison-time lookups
        self.protected_nodes = self._normalize_node_coords(protected_nodes) if protected_nodes else set()
        self.corrections_log = []

        # Double check if protected nodes exist in the graph
        if self.protected_nodes:
            # Normalize graph nodes to same precision as protected nodes for comparison
            protected_set = set(self.protected_nodes)
            normalized_result = set(self._normalize_node_coords(graph.nodes()))

            found_protected_nodes = protected_set & normalized_result
            if len(found_protected_nodes) < len(protected_set):
                missing = protected_set - found_protected_nodes
                warnings.warn(f"Some protected nodes were not found in the graph: {missing}", UserWarning)

    # ==================================================================================
    # MAIN CORRECTION PIPELINE
    # ==================================================================================

    def apply_corrections(self) -> nx.Graph:
        """
        Apply all graph corrections in the optimal order.

        This is the main method to call for automatic graph correction. It applies
        corrections in this order:
        1. Remove self-loops (clean up invalid edges)
        2. Merge close nodes (fix coordinate precision issues)
        3. Connect intersecting edges (add missing junction nodes)
        4. Connect disconnected components (last resort connections)

        :return: Corrected graph ready for Steiner tree optimization
        :rtype: nx.Graph
        """
        print("=" * 70)
        print("APPLYING GRAPH CORRECTIONS")
        print("=" * 70)

        # Step 1: Remove self-loops
        print("\n[1/4] Removing self-loops...")
        self.remove_self_loops()

        # Step 2: Merge close nodes
        print("\n[2/4] Merging close nodes...")
        self.merge_close_nodes()

        # Step 3: Connect intersecting edges
        print("\n[3/4] Connecting intersecting edges...")
        self.connect_intersecting_edges()

        # Step 4: Connect remaining disconnected components
        print("\n[4/4] Connecting remaining disconnected components...")
        self.connect_disconnected_components()

        # Final validation
        print("\n" + "=" * 70)
        is_valid, message = self.validate_connectivity()
        if is_valid:
            print(f"SUCCESS: {message}")
        else:
            print(f"WARNING: {message}")

        print(f"Applied {len(self.corrections_log)} correction(s)")
        print("=" * 70)

        return self.graph

    # ==================================================================================
    # VALIDATION METHODS
    # ==================================================================================

    def validate_connectivity(self) -> Tuple[bool, str]:
        """
        Check if the graph is connected and suitable for Steiner tree optimization.

        A graph is considered valid if:
        - It has at least one node
        - It is connected (single connected component)
        - It has no self-loops or parallel edges (for simple graphs)

        :return: Tuple of (is_valid, message) where is_valid is True if the graph passes
                 all validation checks, and message describes any issues found
        :rtype: Tuple[bool, str]
        """
        # Check if graph is empty
        if self.graph.number_of_nodes() == 0:
            return False, "Graph is empty (no nodes)"

        # Check if graph is connected
        if not nx.is_connected(self.graph):
            num_components = nx.number_connected_components(self.graph)
            return False, f"Graph is not connected: {num_components} disconnected components found"

        # Check for self-loops
        num_self_loops = nx.number_of_selfloops(self.graph)
        if num_self_loops > 0:
            return False, f"Graph contains {num_self_loops} self-loops"

        return True, "Graph is valid and connected"

    def identify_disconnected_components(self) -> List[Set]:
        """
        Identify all disconnected components in the graph.

        :return: List of sets, where each set contains the nodes in a connected component,
                 sorted by size (largest first)
        :rtype: List[Set]
        """
        components = list(nx.connected_components(self.graph))
        # Sort by size, largest first
        components_sorted = sorted(components, key=len, reverse=True)
        return components_sorted

    def identify_isolated_nodes(self) -> List:
        """
        Identify nodes with degree 0 (not connected to any other nodes).

        :return: List of isolated node identifiers
        :rtype: List
        """
        isolated = [node for node, degree in self.graph.degree() if degree == 0]
        return isolated

    # ==================================================================================
    # CORRECTION METHODS
    # ==================================================================================

    def connect_intersecting_edges(self, tolerance: float = SNAP_TOLERANCE) -> nx.Graph:
        """
        Find edges that geometrically intersect but don't share nodes, and add junction nodes.

        This fixes cases where OSM street segments cross but are missing a junction node,
        which is a common data quality issue. When edges from different components intersect,
        a new node is created at the intersection point and both edges are split there.

        Uses a batch processing approach: finds all intersections in a single O(n²) pass,
        then processes all splits together. This is much more efficient than iterative rebuilding.

        Note: This will connect some edges that shouldn't be connected (bridges/tunnels),
        but fixes the majority (likely ~90%) of legitimate missing junctions.

        :param tolerance: Snap new nodes to existing nodes within this distance (default: SNAP_TOLERANCE)
        :type tolerance: float
        :return: Graph with intersection nodes added
        :rtype: nx.Graph
        """
        if nx.is_connected(self.graph):
            print("Graph already connected, skipping intersection check")
            return self.graph

        components = self.identify_disconnected_components()
        print(f"Checking for intersecting edges across {len(components)} components...")

        # Build edge list with component membership
        edges_by_component = self._build_edge_list_by_component(components)

        # Find ALL intersections in a single pass
        all_intersections = self._find_all_intersections(edges_by_component, tolerance)

        if not all_intersections:
            print("No intersections found")
            return self.graph

        # Group intersections by edge and sort by parametric position
        edge_intersections = self._group_intersections_by_edge(all_intersections)

        # Process all splits
        total_nodes_added = self._process_all_intersections(edge_intersections)

        print(f"Found {len(all_intersections)} intersecting edge pairs")
        print(f"Added {total_nodes_added} junction nodes")

        self._log_correction('connect_intersecting_edges', {
            'intersections_found': len(all_intersections),
            'nodes_added': total_nodes_added,
            'tolerance': tolerance
        })

        return self.graph

    def _find_all_intersections(self, edges_by_component: List[Tuple],
                                 tolerance: float) -> List[Dict]:
        """
        Find all intersections between edges from different components in a single pass.

        Uses KDTree spatial indexing for efficient O(log N) nearest-node lookups instead of
        O(N) linear scans, significantly improving performance for large graphs.

        :param edges_by_component: List of tuples (edge, component_index)
        :type edges_by_component: List[Tuple]
        :param tolerance: Snap tolerance for finding nearby nodes
        :type tolerance: float
        :return: List of intersection dictionaries
        :rtype: List[Dict]
        """
        intersections = []

        # Build KDTree once for all nodes for efficient spatial queries
        nodes_list = list(self.graph.nodes())
        if nodes_list:
            node_coords = [(node[0], node[1]) for node in nodes_list]
            nodes_tree = KDTree(node_coords)
        else:
            nodes_tree = None

        for i, (edge1, comp1) in enumerate(edges_by_component):
            for edge2, comp2 in edges_by_component[i+1:]:
                if comp1 == comp2:
                    continue  # Same component, skip

                # Calculate intersection
                intersection_point = self._calculate_edge_intersection(edge1, edge2)

                if intersection_point is not None:
                    # Check if intersection is actually on both line segments
                    if self._point_on_segment(intersection_point, edge1) and \
                       self._point_on_segment(intersection_point, edge2):

                        # Calculate parametric positions along each edge
                        t1 = self._calculate_parametric_position(intersection_point, edge1)
                        t2 = self._calculate_parametric_position(intersection_point, edge2)

                        # Check if there's already a node very close to this intersection
                        # Use KDTree for efficient spatial lookup
                        existing_node = self._find_nearby_node_kdtree(
                            intersection_point, tolerance, nodes_list, nodes_tree
                        )

                        if existing_node:
                            junction_node = existing_node
                            is_new_node = False
                        else:
                            # Create new junction node coordinates using helper
                            junction_node = self._normalize_node_coords(intersection_point)
                            is_new_node = True

                        intersections.append({
                            'edge1': edge1,
                            'edge2': edge2,
                            't1': t1,
                            't2': t2,
                            'junction_node': junction_node,
                            'is_new_node': is_new_node
                        })

        return intersections

    def _calculate_parametric_position(self, point: tuple, edge: tuple) -> float:
        """
        Calculate the parametric position t of a point along an edge.

        :param point: Point coordinates (x, y)
        :type point: tuple
        :param edge: Edge as tuple of two nodes
        :type edge: tuple
        :return: Parametric position t in [0, 1]
        :rtype: float
        """
        (x1, y1), (x2, y2) = edge
        px, py = point

        # Use the dimension with larger variation for better numerical stability
        if abs(x2 - x1) > abs(y2 - y1):
            if abs(x2 - x1) > 1e-10:
                t = (px - x1) / (x2 - x1)
            else:
                t = 0.0
        else:
            if abs(y2 - y1) > 1e-10:
                t = (py - y1) / (y2 - y1)
            else:
                t = 0.0

        # Clamp to [0, 1] to handle floating point errors
        return max(0.0, min(1.0, t))

    def _group_intersections_by_edge(self, intersections: List[Dict]) -> Dict[tuple, List]:
        """
        Group intersections by edge and sort by parametric position.

        :param intersections: List of intersection dictionaries
        :type intersections: List[Dict]
        :return: Dictionary mapping edges to sorted lists of intersection data
        :rtype: Dict[tuple, List]
        """
        edge_intersections = {}

        for intersection in intersections:
            edge1 = intersection['edge1']
            edge2 = intersection['edge2']

            # Add to edge1's intersection list
            if edge1 not in edge_intersections:
                edge_intersections[edge1] = []
            edge_intersections[edge1].append({
                't': intersection['t1'],
                'junction_node': intersection['junction_node'],
                'is_new_node': intersection['is_new_node']
            })

            # Add to edge2's intersection list
            if edge2 not in edge_intersections:
                edge_intersections[edge2] = []
            edge_intersections[edge2].append({
                't': intersection['t2'],
                'junction_node': intersection['junction_node'],
                'is_new_node': intersection['is_new_node']
            })

        # Sort intersections along each edge by parametric position
        for edge in edge_intersections:
            edge_intersections[edge].sort(key=lambda x: x['t'])

        return edge_intersections

    def _process_all_intersections(self, edge_intersections: Dict[tuple, List]) -> int:
        """
        Process all intersections by splitting edges at their junction nodes.

        :param edge_intersections: Dictionary mapping edges to sorted intersection lists
        :type edge_intersections: Dict[tuple, List]
        :return: Number of new nodes added
        :rtype: int
        """
        nodes_added = 0
        added_nodes = set()  # Track which junction nodes we've already added

        # Process each edge that has intersections
        for edge, intersections in edge_intersections.items():
            # Add all new junction nodes first
            for intersection in intersections:
                junction_node = intersection['junction_node']
                if intersection['is_new_node'] and junction_node not in added_nodes:
                    self.graph.add_node(junction_node)
                    added_nodes.add(junction_node)
                    nodes_added += 1

            # Split the edge at all its intersection points
            self._split_edge_at_nodes(edge, [i['junction_node'] for i in intersections])

        return nodes_added

    def _split_edge_at_nodes(self, edge: tuple, junction_nodes: List[tuple]):
        """
        Split an edge at one or multiple junction nodes (assumed to be sorted along the edge).

        :param edge: Edge to split (tuple of two nodes)
        :type edge: tuple
        :param junction_nodes: List of junction nodes sorted along the edge
        :type junction_nodes: List[tuple]
        """
        if not self.graph.has_edge(*edge):
            # Edge may have already been processed as part of another split
            return

        node1, node2 = edge
        edge_data = self.graph.get_edge_data(node1, node2)
        original_weight = edge_data.get('weight', 0.0)

        # Remove the original edge
        self.graph.remove_edge(node1, node2)

        # Build the chain of nodes: start -> junction1 -> junction2 -> ... -> end
        node_chain = [node1] + junction_nodes + [node2]

        # Calculate total distance for weight proportioning
        total_dist = self._calculate_distance(node1, node2)

        # Create edges between consecutive nodes in the chain
        for i in range(len(node_chain) - 1):
            from_node = node_chain[i]
            to_node = node_chain[i + 1]

            # Skip if nodes are the same (shouldn't happen but be safe)
            if from_node == to_node:
                continue

            # Skip if edge already exists
            if self.graph.has_edge(from_node, to_node):
                continue

            # Calculate weight proportional to distance
            dist = self._calculate_distance(from_node, to_node)

            if total_dist > 0:
                # Use original weight if available and > 0, otherwise use Euclidean distance
                base_weight = original_weight if original_weight > 0 else total_dist
                weight = base_weight * (dist / total_dist)
            else:
                # Edge has zero length - use equal distribution
                weight = original_weight / len(node_chain) if original_weight > 0 else 0.0

            self.graph.add_edge(from_node, to_node, weight=weight)

    def _build_edge_list_by_component(self, components: List[Set]) -> List[Tuple]:
        """
        Build a list of edges with their component membership.

        :param components: List of component node sets
        :type components: List[Set]
        :return: List of tuples (edge, component_index)
        :rtype: List[Tuple]
        """
        edges_by_component = []
        for comp_idx, component in enumerate(components):
            edges_seen = set()
            for node in component:
                for neighbor in self.graph.neighbors(node):
                    if neighbor in component:  # Only internal edges
                        edge = tuple(sorted((node, neighbor)))
                        if edge not in edges_seen:
                            edges_seen.add(edge)
                            edges_by_component.append((edge, comp_idx))
        return edges_by_component

    def _calculate_edge_intersection(self, edge1: tuple, edge2: tuple) -> Optional[tuple]:
        """
        Calculate intersection point of two line segments using parametric line equations.

        :param edge1: Tuple of two nodes (x1, y1), (x2, y2)
        :param edge2: Tuple of two nodes (x3, y3), (x4, y4)
        :return: Intersection point (x, y) or None if lines are parallel
        :rtype: Optional[tuple]
        """
        (x1, y1), (x2, y2) = edge1
        (x3, y3), (x4, y4) = edge2

        # Calculate denominators for parametric equations
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if abs(denom) < 1e-10:  # Lines are parallel or coincident
            return None

        # Calculate intersection point using parametric form
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)

        return (x, y)

    def _point_on_segment(self, point: tuple, segment: tuple, epsilon: float = 1e-6) -> bool:
        """
        Check if a point lies on a line segment (not just the infinite line).

        :param point: Point to check (x, y)
        :param segment: Line segment as tuple of two nodes
        :param epsilon: Tolerance for floating point comparison
        :return: True if point is on segment
        :rtype: bool
        """
        px, py = point
        (x1, y1), (x2, y2) = segment

        # Check if point is within bounding box of segment
        if not (min(x1, x2) - epsilon <= px <= max(x1, x2) + epsilon and
                min(y1, y2) - epsilon <= py <= max(y1, y2) + epsilon):
            return False

        # Check if point is on the line (cross product should be ~0)
        cross = abs((py - y1) * (x2 - x1) - (px - x1) * (y2 - y1))

        return cross < epsilon * max(abs(x2 - x1), abs(y2 - y1), 1.0)

    def _find_nearby_node(self, point: tuple, tolerance: float) -> Optional[tuple]:
        """
        Find if there's an existing node within tolerance distance of point.

        Uses linear search O(N). For better performance when called multiple times,
        use _find_nearby_node_kdtree with a pre-built KDTree.

        :param point: Point to check (x, y)
        :param tolerance: Maximum distance to consider (inclusive)
        :return: Existing node if found, None otherwise
        :rtype: Optional[tuple]
        """
        for node in self.graph.nodes():
            if self._calculate_distance(point, node) <= tolerance:
                return node
        return None

    def _find_nearby_node_kdtree(self, point: tuple, tolerance: float,
                                  nodes_list: List[tuple], kdtree: Optional[KDTree]) -> Optional[tuple]:
        """
        Find if there's an existing node within tolerance distance of point using KDTree.

        This is O(log N) compared to O(N) for linear search, making it much faster
        for large graphs when called multiple times with a pre-built KDTree.

        :param point: Point to check (x, y)
        :param tolerance: Maximum distance to consider (inclusive)
        :param nodes_list: List of all nodes in the same order as KDTree was built
        :param kdtree: Pre-built KDTree for spatial queries, or None if no nodes
        :return: Existing node if found, None otherwise
        :rtype: Optional[tuple]
        """
        if not kdtree or not nodes_list:
            return None

        # Query KDTree for nearest neighbors within tolerance
        indices = kdtree.query_ball_point([point[0], point[1]], tolerance, p=2.0)

        # Return the first node within tolerance (if any)
        for idx in indices:
            node = nodes_list[idx]
            if self._calculate_distance(point, node) <= tolerance:
                return node

        return None

    def connect_disconnected_components(self) -> nx.Graph:
        """
        Connect disconnected components of the graph to create a single connected graph.

        Connects all components to the largest component by finding the nearest node pairs
        between each smaller component and the largest component, then adding edges between them.

        :return: Connected graph
        :rtype: nx.Graph
        """
        # Check if graph is already connected
        if nx.is_connected(self.graph):
            self._log_correction('connect_components', {
                'message': 'Graph already connected, no action needed'
            })
            return self.graph

        # Identify disconnected components
        components = self.identify_disconnected_components()
        num_components = len(components)

        print(f"Connecting {num_components} disconnected components...")

        edges_added = self._connect_via_nearest_neighbor(components)

        # Verify the graph is now connected
        if nx.is_connected(self.graph):
            print(f"Successfully connected graph. Was {num_components} components, now 1 component.")
            self._log_correction('connect_components', {
                'original_components': num_components,
                'final_components': 1,
                'edges_added': edges_added
            })
        else:
            print(f"Warning: Graph still has {nx.number_connected_components(self.graph)} components after correction")

        return self.graph

    def _connect_via_nearest_neighbor(self, components: List[Set]) -> int:
        """
        Connect all components to the largest component by finding nearest node pairs.

        Avoids creating direct edges between two protected nodes (e.g., building terminals)
        to maintain physical network constraints.

        TODO: Consider adding allow_protected_connections parameter for campus/institutional networks
              where building-to-building connections are physically realistic and cost-effective
              (universities, hospitals, industrial parks, 5GDHC prosumer networks).
              Alternative approach: use distance threshold (e.g., allow B-B if < 20-50m) to permit
              adjacent buildings in complexes while preventing unrealistic long-distance shortcuts.
              See: ASHRAE District Heating Guide, CIBSE CP1 Heat Networks Code of Practice.

        :param components: List of component node sets, sorted by size (largest first)
        :type components: List[Set]
        :return: Number of edges added
        :rtype: int
        """
        # Largest component is the anchor
        largest_component = components[0]
        edges_added = 0

        # Connect each smaller component to the largest
        for i, component in enumerate(components[1:], start=1):
            min_distance = float('inf')
            best_pair = None

            # Find nearest pair of nodes between this component and the largest
            # Avoid connecting two protected nodes directly (e.g., building-to-building)
            for node_comp in component:
                for node_large in largest_component:
                    # Skip if both nodes are protected (e.g., both are building terminals)
                    # This prevents direct building-to-building connections
                    if self._is_protected_node(node_comp) and self._is_protected_node(node_large):
                        continue

                    distance = self._calculate_distance(node_comp, node_large)
                    if distance < min_distance:
                        min_distance = distance
                        best_pair = (node_comp, node_large)

            if best_pair:
                # Add edge between nearest nodes
                self.graph.add_edge(best_pair[0], best_pair[1], weight=min_distance)
                edges_added += 1
                node1_type = "protected" if self._is_protected_node(best_pair[0]) else "street"
                node2_type = "protected" if self._is_protected_node(best_pair[1]) else "street"
                print(f"  Component {i}/{len(components)-1}: Connected {node1_type} to {node2_type} "
                      f"via edge of length {min_distance:.2f}m")

        print(f"Added {edges_added} edges to connect components")
        return edges_added

    def _is_protected_node(self, node: tuple) -> bool:
        """
        Check if a node is protected, using normalized coordinate comparison.

        :param node: Node to check
        :type node: tuple
        :return: True if node is in protected set (after normalization)
        :rtype: bool
        """
        normalized = self._normalize_node_coords(node)
        return normalized in self.protected_nodes

    def _normalize_node_coords(self, nodes) -> tuple | set:
        """
        Normalize node coordinates to the instance's coordinate precision.

        This ensures consistent coordinate precision across all operations,
        preventing lookup failures due to floating point precision differences.

        Supports both single node and collections of nodes (vectorized operation).

        :param nodes: Single node tuple (x, y) or iterable of node tuples
        :type nodes: tuple | List[tuple] | Set[tuple] | any iterable
        :return: Normalized node coordinates (single tuple) or set of normalized nodes
        :rtype: tuple | set

        Examples:
            >>> corrector._normalize_node_coords((123.456789, 456.789012))
            (123.456789, 456.789012)  # rounded to coord_precision

            >>> corrector._normalize_node_coords([(1.11111, 2.22222), (3.33333, 4.44444)])
            {(1.11111, 2.22222), (3.33333, 4.44444)}  # set of rounded coords
        """
        # Check if it's a single node (tuple with numeric elements)
        if isinstance(nodes, tuple) and len(nodes) == 2 and isinstance(nodes[0], (int, float)):
            return (round(nodes[0], self.coord_precision), round(nodes[1], self.coord_precision))

        # Otherwise treat as iterable of nodes
        return set(
            (round(node[0], self.coord_precision), round(node[1], self.coord_precision))
            for node in nodes
        )

    def _calculate_distance(self, node1, node2) -> float:
        """
        Calculate Euclidean distance between two nodes.

        :param node1: First node (tuple of coordinates)
        :param node2: Second node (tuple of coordinates)
        :return: Euclidean distance
        :rtype: float
        """
        return math.sqrt((node1[0] - node2[0])**2 + (node1[1] - node2[1])**2)

    def merge_close_nodes(self, distance_threshold: Optional[float] = None) -> nx.Graph:
        """
        Merge nodes that are closer than a specified distance threshold.

        This helps fix issues where multiple nodes exist at nearly the same location
        due to coordinate precision issues or data quality problems. When nodes are merged,
        all edges from the merged nodes are transferred to the kept node.

        Uses KDTree spatial indexing for efficient O(N log N) nearest neighbor search instead
        of O(N²) brute force, making it suitable for city-scale graphs with thousands of nodes.

        :param distance_threshold: Maximum distance for merging nodes (default: SNAP_TOLERANCE)
        :type distance_threshold: Optional[float]
        :return: Graph with close nodes merged
        :rtype: nx.Graph
        """
        if distance_threshold is None:
            distance_threshold = SNAP_TOLERANCE

        nodes = list(self.graph.nodes())
        num_nodes_before = len(nodes)
        nodes_to_merge = {}  # Maps nodes to be removed -> node to keep
        merged_count = 0

        print(f"Checking {num_nodes_before} nodes for merging (threshold: {distance_threshold}m)...")
        if self.protected_nodes:
            print(f"  Protecting {len(self.protected_nodes)} terminal nodes from merging")

        # Build KDTree once for efficient spatial queries (reuse helper method pattern)
        node_coords = [(node[0], node[1]) for node in nodes]
        tree = KDTree(node_coords)

        # Find pairs of nodes that are too close using KDTree
        for i, node1 in enumerate(nodes):
            if node1 in nodes_to_merge:  # Already marked for removal
                continue

            # Skip if this is a protected node (e.g., building terminal)
            if self._is_protected_node(node1):
                continue

            # Query KDTree for all neighbors within distance_threshold
            # Using query_ball_point for efficient radial search
            neighbor_indices = tree.query_ball_point(node_coords[i], distance_threshold, p=2.0)

            for j in neighbor_indices:
                if j <= i:  # Skip self and already processed pairs
                    continue

                node2 = nodes[j]
                if node2 in nodes_to_merge:  # Already marked for removal
                    continue

                # Skip if node2 is a protected node
                if self._is_protected_node(node2):
                    continue

                distance = self._calculate_distance(node1, node2)
                if distance < distance_threshold:
                    # Mark node2 for merging into node1
                    nodes_to_merge[node2] = node1
                    merged_count += 1
                    print(f"  Merging nodes {distance:.3f}m apart")

        if merged_count == 0:
            print("No nodes close enough to merge")
            return self.graph

        # Perform the merge: transfer all edges from nodes_to_merge to their target nodes
        for node_to_remove, node_to_keep in nodes_to_merge.items():
            # Get all edges connected to the node being removed
            for neighbor in list(self.graph.neighbors(node_to_remove)):
                if neighbor == node_to_keep:
                    continue  # Don't create self-loop

                if neighbor in nodes_to_merge and nodes_to_merge[neighbor] == node_to_keep:
                    continue  # Don't create self-loop if neighbor is also being merged to same node

                # Get edge data if it exists
                edge_data = self.graph.get_edge_data(node_to_remove, neighbor)

                # Calculate new weight based on actual distance if edge_data lacks weight or is invalid
                new_weight = edge_data.get('weight', None) if edge_data else None
                if new_weight is None or not isinstance(new_weight, (int, float)) or new_weight == float('inf'):
                    new_weight = self._calculate_distance(node_to_keep, neighbor)

                # Add edge from kept node to neighbor (if it doesn't exist, or update if new one is shorter)
                if self.graph.has_edge(node_to_keep, neighbor):
                    # Keep edge with minimum weight
                    existing_weight = self.graph[node_to_keep][neighbor].get('weight', float('inf'))
                    if new_weight < existing_weight:
                        self.graph[node_to_keep][neighbor]['weight'] = new_weight
                else:
                    # Create new edge attributes with updated weight
                    attrs = dict(edge_data) if edge_data else {}
                    attrs['weight'] = new_weight
                    self.graph.add_edge(node_to_keep, neighbor, **attrs)

            # Remove the merged node
            self.graph.remove_node(node_to_remove)

        num_nodes_after = self.graph.number_of_nodes()
        print(f"Merged {merged_count} nodes. Graph now has {num_nodes_after} nodes (was {num_nodes_before})")

        self._log_correction('merge_close_nodes', {
            'distance_threshold': distance_threshold,
            'nodes_merged': merged_count,
            'nodes_before': num_nodes_before,
            'nodes_after': num_nodes_after
        })

        return self.graph

    def remove_self_loops(self) -> nx.Graph:
        """
        Remove all self-loops (edges from a node to itself) from the graph.

        :return: Graph with self-loops removed
        :rtype: nx.Graph
        """
        num_self_loops_before = nx.number_of_selfloops(self.graph)

        if num_self_loops_before == 0:
            print("No self-loops found")
            return self.graph

        # Remove all self-loops
        self.graph.remove_edges_from(nx.selfloop_edges(self.graph))

        num_self_loops_after = nx.number_of_selfloops(self.graph)
        edges_removed = num_self_loops_before - num_self_loops_after

        print(f"Removed {edges_removed} self-loop(s)")

        self._log_correction('remove_self_loops', {
            'self_loops_removed': edges_removed,
            'edges_before': len(self.original_graph.edges()),
            'edges_after': len(self.graph.edges())
        })

        return self.graph

    # ==================================================================================
    # UTILITY METHODS
    # ==================================================================================

    def get_corrections_log(self) -> List[Dict]:
        """
        Get a log of all corrections that have been applied to the graph.

        :return: List of dictionaries describing each correction applied
        :rtype: List[Dict]
        """
        return self.corrections_log

    def _log_correction(self, correction_type: str, details: Dict):
        """
        Internal method to log a correction operation.

        :param correction_type: Type of correction applied
        :type correction_type: str
        :param details: Dictionary with details about the correction
        :type details: Dict
        """
        self.corrections_log.append({
            'type': correction_type,
            'details': details
        })

    # ==================================================================================
    # STATIC CONVENIENCE METHODS
    # ==================================================================================

    @staticmethod
    def validate_steiner_tree_ready(graph: nx.Graph, terminal_nodes: List) -> Tuple[bool, str]:
        """
        Check if a graph is ready for Steiner tree optimization.

        Validates that:
        - The graph is connected
        - All terminal nodes exist in the graph
        - The graph has sufficient structure for optimization

        :param graph: Graph to validate
        :type graph: nx.Graph
        :param terminal_nodes: List of terminal nodes that should be in the graph
        :type terminal_nodes: List
        :return: Tuple of (is_ready, message)
        :rtype: Tuple[bool, str]
        """
        # Check if graph is empty
        if graph.number_of_nodes() == 0:
            return False, "Graph is empty"

        # Check if graph is connected
        if not nx.is_connected(graph):
            num_components = nx.number_connected_components(graph)
            return False, f"Graph is not connected ({num_components} components). Steiner tree requires connected graph."

        # Check if terminal nodes list is valid
        if not terminal_nodes or len(terminal_nodes) < 2:
            return False, f"Need at least 2 terminal nodes for Steiner tree, got {len(terminal_nodes) if terminal_nodes else 0}"

        # Check if all terminal nodes exist in graph
        graph_nodes = set(graph.nodes())
        missing_terminals = [node for node in terminal_nodes if node not in graph_nodes]
        if missing_terminals:
            return False, f"{len(missing_terminals)} terminal nodes not found in graph"

        return True, f"Graph is ready for Steiner tree with {len(terminal_nodes)} terminals"


def main():
    """
    Example usage and testing of GraphCorrector.
    """
    print("GraphCorrector module - helper for graph correction operations")
    print("Import this module to use: from cea.datamanagement.graph_helper import GraphCorrector")


if __name__ == '__main__':
    main()
