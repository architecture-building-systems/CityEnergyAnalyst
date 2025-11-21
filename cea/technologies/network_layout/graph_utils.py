"""
Graph Utilities for Network Layout

Helper functions for converting between GeoDataFrames and NetworkX graphs,
and other graph-related utilities for thermal network layout.
"""

import networkx as nx
from scipy.spatial import KDTree
from shapely.geometry import Point, LineString, MultiLineString
from geopandas import GeoDataFrame as gdf

from cea.constants import SHAPEFILE_TOLERANCE


def gdf_to_nx(network_gdf: gdf, coord_precision: int = SHAPEFILE_TOLERANCE, preserve_geometry=True, **attrs):
    """
    Convert GeoDataFrame to NetworkX Graph.

    This is a consolidated helper function for converting GeoDataFrame geometries
    to NetworkX graphs with consistent handling of Point, LineString and MultiLineString
    geometries.

    :param network_gdf: GeoDataFrame with Point/LineString/MultiLineString geometries
    :type network_gdf: geopandas.GeoDataFrame
    :param coord_precision: Decimal places for coordinate rounding (default: SHAPEFILE_TOLERANCE)
    :type coord_precision: int
    :param preserve_geometry: If True, store full LineString geometry as edge attribute (default: True)
    :type preserve_geometry: bool
    :param attrs: Additional attributes to extract from GeoDataFrame columns
    :type attrs: dict
    :return: NetworkX Graph with edges representing network connections and nodes for Points
    :rtype: networkx.Graph

    Example:
        >>> # Simple conversion
        >>> G = gdf_to_nx(streets_gdf, coord_precision=6)
        >>>
        >>> # Preserve full geometries for curved streets
        >>> G = gdf_to_nx(streets_gdf, preserve_geometry=True)
        >>>
        >>> # Extract specific columns as edge attributes
        >>> G = gdf_to_nx(streets_gdf, type_mat='type_mat', pipe_DN='pipe_DN')
        >>>
        >>> # Mixed geometries - Points become lone nodes, LineStrings become edges
        >>> mixed_gdf = gpd.GeoDataFrame({
        ...     'geometry': [Point(0, 0), LineString([(1, 1), (2, 2)])]
        ... })
        >>> G = gdf_to_nx(mixed_gdf)
        >>> list(G.nodes())  # [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
        >>> list(G.edges())  # [((1.0, 1.0), (2.0, 2.0))]

    Notes:
        - Coordinates are rounded to avoid floating-point precision issues
        - Point geometries are added as lone nodes (nodes without edges)
        - LineString and MultiLineString geometries become edges
        - Edge weight is set to geometry length by default
        - If preserve_geometry=True, 'geometry' edge attribute contains full LineString
    """
    G = nx.Graph()

    for idx, row in network_gdf.iterrows():
        geom = row.geometry
        
        if geom is None or geom.is_empty:
            continue

        # Process different geometry types
        if geom.geom_type == 'Point':
            # Add Point as a lone node
            _add_point_to_graph(G, geom, row, coord_precision, **attrs)
        elif geom.geom_type == 'LineString':
            _add_linestring_to_graph(G, geom, row, idx, coord_precision, preserve_geometry, **attrs)
        elif geom.geom_type == 'MultiLineString':
            for sub_line in geom.geoms:
                _add_linestring_to_graph(G, sub_line, row, idx, coord_precision, preserve_geometry, **attrs)

    return G


def _merge_orphan_nodes_to_nearest(G, terminal_nodes, merge_threshold):
    """
    Merge ALL disconnected components to form a fully connected network.
    
    Strategy:
    1. Discard tiny orphan components (< 3 nodes) with no terminals
    2. Find the two closest components and merge them (iteratively)
    3. Prefer non-terminal nodes as bridge points
    4. Use progressive thresholds: 50m → 100m → 200m → 500m until connected
    
    :param G: NetworkX graph
    :param terminal_nodes: Set of (x, y) coordinates that are building terminals
    :param merge_threshold: Initial maximum distance for merging (meters)
    :return: Graph with all components merged into one connected network
    """
    import numpy as np
    import math
    
    components_merged_total = 0
    edges_added_total = 0
    components_discarded = 0
    
    # Progressive thresholds to ensure connectivity
    thresholds = [merge_threshold, merge_threshold * 2, merge_threshold * 4, merge_threshold * 10]
    
    for threshold_idx, threshold in enumerate(thresholds):
        MAX_ITERATIONS = 200  # Safety limit per threshold
        iteration = 0
        merges_at_this_threshold = 0
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            
            # Find connected components
            components = list(nx.connected_components(G))
            
            if len(components) <= 1:
                break  # Fully connected!
            
            # First pass: Discard tiny orphans with no terminals
            components = list(nx.connected_components(G))  # Get initial components
            for component in list(components):  # Make a copy to iterate safely
                component_terminals = [n for n in component if n in terminal_nodes]
                if len(component) < 3 and len(component_terminals) == 0:
                    for node in component:
                        G.remove_node(node)
                    components_discarded += 1
                    
            # Recompute components after discarding
            components = list(nx.connected_components(G))
            if len(components) <= 1:
                break
            
            if iteration == 1 and threshold_idx == 0:
                print(f"  DEBUG: After discarding, {len(components)} components remain, sizes: {sorted([len(c) for c in components], reverse=True)[:10]}")
            
            # Find the two closest components to merge
            best_node_A = None
            best_node_B = None
            best_distance = float('inf')
            
            # Check all pairs of components
            for i, comp_A in enumerate(components):
                # Build KDTree for comp_A nodes
                comp_A_nodes = list(comp_A)
                comp_A_coords = np.array([(n[0], n[1]) for n in comp_A_nodes])
                tree_A = KDTree(comp_A_coords)
                
                for j, comp_B in enumerate(components[i+1:], start=i+1):
                    # For each node in comp_B, find closest in comp_A
                    for node_B in comp_B:
                        # Prefer non-terminal nodes
                        if node_B in terminal_nodes:
                            continue
                            
                        coords_B = [node_B[0], node_B[1]]
                        dist, nearest_idx = tree_A.query(coords_B, k=1)
                        node_A = comp_A_nodes[nearest_idx]
                        
                        # Check if node_A is also non-terminal (preferred)
                        if dist < best_distance and node_A not in terminal_nodes:
                            best_distance = dist
                            best_node_A = node_A
                            best_node_B = node_B
            
            # If no non-terminal pairs found, allow terminal nodes
            if best_node_A is None:
                for i, comp_A in enumerate(components):
                    comp_A_nodes = list(comp_A)
                    comp_A_coords = np.array([(n[0], n[1]) for n in comp_A_nodes])
                    tree_A = KDTree(comp_A_coords)
                    
                    for j, comp_B in enumerate(components[i+1:], start=i+1):
                        for node_B in comp_B:
                            coords_B = [node_B[0], node_B[1]]
                            dist, nearest_idx = tree_A.query(coords_B, k=1)
                            node_A = comp_A_nodes[nearest_idx]
                            
                            if dist < best_distance:
                                best_distance = dist
                                best_node_A = node_A
                                best_node_B = node_B
            
            # Merge if within threshold
            if best_distance <= threshold and best_node_A is not None:
                # Snap best_node_B to best_node_A by reconnecting all edges
                orphan_edges = list(G.edges(best_node_B, data=True))
                
                for u, v, data in orphan_edges:
                    other_node = v if u == best_node_B else u
                    
                    if 'geometry' in data:
                        old_geom = data['geometry']
                        coords = list(old_geom.coords)
                        
                        # Replace the orphan endpoint
                        if coords[0] == best_node_B or coords[0] == u:
                            coords[0] = best_node_A
                        else:
                            coords[-1] = best_node_A
                        
                        new_geom = LineString(coords)
                        data['geometry'] = new_geom
                        data['weight'] = new_geom.length
                    else:
                        data['weight'] = math.sqrt(
                            (best_node_A[0] - other_node[0])**2 + 
                            (best_node_A[1] - other_node[1])**2
                        )
                    
                    if not G.has_edge(other_node, best_node_A):
                        G.add_edge(other_node, best_node_A, **data)
                        edges_added_total += 1
                
                G.remove_node(best_node_B)
                components_merged_total += 1
                merges_at_this_threshold += 1
            else:
                # No more components can be merged at this threshold
                if threshold_idx == 0 and iteration == 1:
                    print(f"  DEBUG: First attempt - best_distance={best_distance:.1f}m, threshold={threshold:.1f}m, best_node_A={best_node_A is not None}")
                break
        
        # Check if fully connected now
        if nx.number_connected_components(G) == 1:
            if merges_at_this_threshold > 0:
                print(f"  - Achieved full connectivity at threshold {threshold:.1f}m ({merges_at_this_threshold} merges)")
            break
        elif merges_at_this_threshold > 0:
            print(f"  - Merged {merges_at_this_threshold} components at threshold {threshold:.1f}m, {nx.number_connected_components(G)} remain")
    
    # Final check
    remaining_components = list(nx.connected_components(G))
    if len(remaining_components) > 1:
        component_sizes = sorted([len(c) for c in remaining_components], reverse=True)
        print(f"  WARNING: Unable to fully connect network - {len(remaining_components)} components remain")
        print(f"      Component sizes: {component_sizes}")
        print(f"      Max threshold tried: {thresholds[-1]:.1f}m")
    
    if components_merged_total > 0:
        print(f"Merged {components_merged_total} orphan component(s) to main network (snapped {edges_added_total} edge endpoint(s))")
    if components_discarded > 0:
        print(f"Safely discarded {components_discarded} orphan component(s) with 2 street node(s) (no building terminals attached)")
    
    return G


def _add_point_to_graph(G, point, row, coord_precision, **node_attrs):
    """
    Helper to add a single Point as a lone node to the graph.

    :param G: NetworkX graph to add node to
    :param point: Point geometry
    :param row: GeoDataFrame row containing node attributes
    :param coord_precision: Decimal places for coordinate rounding
    """
    coords = tuple(round(c, coord_precision) for c in [point.x, point.y])

    node_data = {}

    # Add requested attributes from row
    for attr_name, col_name in node_attrs.items():
        if col_name in row.index:
            node_data[attr_name] = row[col_name]

    G.add_node(coords, **node_data)


def _add_linestring_to_graph(G, line, row, idx, coord_precision, preserve_geometry, **edge_attrs):
    """
    Helper to add a single LineString as an edge to the graph.

    :param G: NetworkX graph to add edge to
    :param line: LineString geometry
    :param row: GeoDataFrame row containing edge attributes
    :param idx: Row index from original GeoDataFrame
    :param coord_precision: Decimal places for coordinate rounding
    :param preserve_geometry: Whether to store full geometry
    :param edge_attrs: Column names to extract as edge attributes
    """
    coords = list(line.coords)
    start = tuple(round(c, coord_precision) for c in coords[0])
    end = tuple(round(c, coord_precision) for c in coords[-1])

    # Build edge data dictionary
    # Prefer existing length column if available (more accurate for processed networks)
    # Check for common length column names: 'length', 'length_m', 'weight'
    weight = None
    for length_col in ['length', 'length_m', 'weight']:
        if length_col in row.index and row[length_col] is not None:
            weight = row[length_col]
            break

    # Fall back to calculating from geometry if no length column found
    if weight is None:
        weight = line.length

    edge_data = {'weight': weight}

    if preserve_geometry:
        edge_data['geometry'] = line

    # Add requested attributes from row
    for attr_name, col_name in edge_attrs.items():
        if col_name in row.index:
            edge_data[attr_name] = row[col_name]

    G.add_edge(start, end, **edge_data)


def normalize_coords(coords, precision=SHAPEFILE_TOLERANCE):
    """
    Normalize coordinate sequence to consistent precision.

    Rounds all coordinates to the specified precision to prevent floating-point
    precision issues when comparing coordinates or using them as dictionary keys.

    :param coords: Sequence of (x, y) coordinate tuples
    :type coords: list of tuples
    :param precision: Number of decimal places for rounding (default: SHAPEFILE_TOLERANCE)
    :type precision: int
    :return: List of rounded (x, y) coordinate tuples
    :rtype: list of tuples

    Example:
        >>> coords = [(1.123456789, 2.987654321), (3.111111111, 4.999999999)]
        >>> normalize_coords(coords, precision=6)
        [(1.123457, 2.987654), (3.111111, 5.0)]
    """
    rounded = []
    for c in coords:
        # Accept (x, y) or (x, y, z/other); ignore extra dimensions
        # Also tolerate sequences like numpy arrays
        if isinstance(c, (list, tuple)) and len(c) >= 2:
            x = float(c[0])
            y = float(c[1])
        else:
            # Fallback: attempt attribute access (e.g., shapely Point)
            try:
                x = float(c[0])  # type: ignore[index]
                y = float(c[1])  # type: ignore[index]
            except Exception as e:
                raise ValueError(f"Invalid coordinate element for normalization: {c!r}") from e
        rounded.append((round(x, precision), round(y, precision)))
    return rounded


def normalize_geometry(geom, precision=SHAPEFILE_TOLERANCE):
    """
    Normalize Point/LineString/MultiLineString geometry coordinates to consistent precision.

    Creates a new geometry object with all coordinates rounded to the specified precision.
    This prevents floating-point precision issues and ensures consistent coordinate
    representation across geometric operations.

    :param geom: Shapely geometry (Point, LineString, or MultiLineString)
    :type geom: shapely.geometry
    :param precision: Number of decimal places for rounding (default: SHAPEFILE_TOLERANCE)
    :type precision: int
    :return: New geometry with normalized coordinates
    :rtype: shapely.geometry

    Example:
        >>> from shapely.geometry import LineString
        >>> line = LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
        >>> normalized = normalize_geometry(line, precision=6)
        >>> list(normalized.coords)
        [(0.123457, 1.987654), (2.111111, 4.0)]
    """
    if geom.geom_type == 'Point':
        rounded_coords = (round(geom.x, precision), round(geom.y, precision))
        return Point(rounded_coords)
    elif geom.geom_type == 'LineString':
        rounded_coords = normalize_coords(list(geom.coords), precision)
        return LineString(rounded_coords)
    elif geom.geom_type == 'MultiLineString':
        rounded_lines = [normalize_geometry(line, precision) for line in geom.geoms]
        return MultiLineString(rounded_lines)
    else:
        raise ValueError(f"Unsupported geometry type: {geom.geom_type}")


def normalize_gdf_geometries(network_gdf, precision=SHAPEFILE_TOLERANCE, inplace=True):
    """
    Normalize all geometries in a GeoDataFrame to consistent precision.

    Applies coordinate normalization to all geometry objects in the GeoDataFrame,
    ensuring consistent precision across all features. This is critical for
    preventing floating-point precision issues in graph operations.

    :param network_gdf: GeoDataFrame with Point/LineString/MultiLineString geometries
    :type network_gdf: geopandas.GeoDataFrame
    :param precision: Number of decimal places for rounding (default: SHAPEFILE_TOLERANCE)
    :type precision: int
    :param inplace: If True, modify GeoDataFrame in place; if False, return copy (default: True)
    :type inplace: bool
    :return: GeoDataFrame with normalized geometries (or None if inplace=True)
    :rtype: geopandas.GeoDataFrame or None

    Example:
        >>> import geopandas as gpd
        >>> from shapely.geometry import LineString
        >>> gdf = gpd.GeoDataFrame(geometry=[LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])])
        >>> normalize_gdf_geometries(gdf, precision=6)
        >>> list(gdf.geometry[0].coords)
        [(0.123457, 1.987654), (2.111111, 4.0)]
    """
    if inplace:
        network_gdf.geometry = network_gdf.geometry.apply(lambda geom: normalize_geometry(geom, precision))
        return None
    else:
        result = network_gdf.copy()
        result.geometry = result.geometry.apply(lambda geom: normalize_geometry(geom, precision))
        return result


def nx_to_gdf(graph, crs, preserve_geometry=True):
    """
    Convert NetworkX graph back to GeoDataFrame.

    Inverse of gdf_to_nx() - creates a GeoDataFrame of edges from a NetworkX graph.
    This ensures round-trip conversion (GeoDataFrame → graph → GeoDataFrame) is reliable.

    :param graph: NetworkX graph with edge attributes
    :type graph: networkx.Graph
    :param crs: Coordinate reference system for output GeoDataFrame
    :type crs: str or pyproj.CRS
    :param preserve_geometry: If True, use 'geometry' edge attribute for curved lines;
                             if False, create straight LineStrings from node coordinates
    :type preserve_geometry: bool
    :return: GeoDataFrame with edges and their attributes
    :rtype: geopandas.GeoDataFrame

    Example:
        >>> # Create graph from GeoDataFrame
        >>> graph = gdf_to_nx(streets_gdf, preserve_geometry=True)
        >>>
        >>> # Convert back to GeoDataFrame
        >>> streets_restored = nx_to_gdf(graph, crs=streets_gdf.crs, preserve_geometry=True)
        >>>
        >>> # Geometries are preserved
        >>> assert len(streets_restored) == len(streets_gdf)

    Notes:
        - If preserve_geometry=True, edges must have 'geometry' attribute with LineString
        - If preserve_geometry=False, creates straight lines between node coordinates
        - All edge attributes (except 'geometry' and 'weight') are preserved in output
        - Output edges maintain same coordinate precision as graph nodes
    """
    edges_data = []

    for u, v, data in graph.edges(data=True):
        edge_dict = {}

        # Determine geometry
        if preserve_geometry and 'geometry' in data:
            # Use preserved curved geometry
            edge_dict['geometry'] = data['geometry']
        else:
            # Create straight line from node coordinates
            edge_dict['geometry'] = LineString([u, v])

        # Copy all other edge attributes
        for key, value in data.items():
            if key != 'geometry':  # Don't duplicate geometry
                edge_dict[key] = value

        edges_data.append(edge_dict)

    # Create GeoDataFrame
    if edges_data:
        edges_gdf = gdf(edges_data, crs=crs)
    else:
        # Handle empty graph (no edges)
        edges_gdf = gdf(
            columns=['geometry'],
            geometry='geometry',
            crs=crs
        )

    return edges_gdf


def validate_normalized_coordinates(network_gdf: gdf, precision: int = SHAPEFILE_TOLERANCE) -> None:
    """
    Validate that all coordinates in a GeoDataFrame are normalized to the specified precision.

    This is critical for preventing floating-point precision mismatches that can cause
    disconnected components in the graph.

    :param network_gdf: GeoDataFrame to validate
    :param precision: Number of decimal places expected (default: SHAPEFILE_TOLERANCE)
    :raises ValueError: If any coordinate is not properly normalized
    """
    for idx, geom in enumerate(network_gdf.geometry):
        if geom.is_empty:
            continue

        # Handle different geometry types
        if geom.geom_type == 'Point':
            # Point has x, y attributes instead of coords
            coord_lists = [[(geom.x, geom.y)]]
        elif geom.geom_type == 'MultiLineString':
            coord_lists = [list(line.coords) for line in geom.geoms]
        elif geom.geom_type == 'LineString':
            coord_lists = [list(geom.coords)]
        else:
            # Skip unsupported geometry types
            continue

        for coords in coord_lists:
            for coord_idx, coord in enumerate(coords):
                x_rounded = round(coord[0], precision)
                y_rounded = round(coord[1], precision)

                # Check if coordinate matches rounded value
                if coord[0] != x_rounded or coord[1] != y_rounded:
                    raise ValueError(
                        f"Geometry {idx} ({geom.geom_type}) coordinate {coord_idx} has unnormalized values: "
                        f"({coord[0]}, {coord[1]}) != ({x_rounded}, {y_rounded}). "
                        f"This indicates a precision handling bug that will cause disconnected components. "
                        f"All coordinates must be normalized to {precision} decimal places."
                    )
