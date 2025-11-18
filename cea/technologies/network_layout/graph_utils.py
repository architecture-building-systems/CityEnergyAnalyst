"""
Graph Utilities for Network Layout

Helper functions for converting between GeoDataFrames and NetworkX graphs,
and other graph-related utilities for thermal network layout.
"""

import networkx as nx
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
    Merge disconnected non-terminal components to nearest node in main component.
    
    This fixes isolated street fragments by connecting them to the main network.
    Merges components that:
    1. Are small (< 5 nodes)
    2. Have at least one non-terminal node within merge_threshold of main component
    
    Terminal nodes themselves are never used as bridge points (to preserve building connections),
    but components containing terminals CAN be merged via their street nodes.
    
    :param G: NetworkX graph
    :param terminal_nodes: Set of (x, y) coordinates that are building terminals
    :param merge_threshold: Maximum distance for merging (meters)
    :return: Graph with orphan components merged
    """
    from scipy.spatial import KDTree
    import numpy as np
    
    # Find connected components
    components = list(nx.connected_components(G))
    
    if len(components) <= 1:
        return G  # Already fully connected
    
    # Identify main component (largest)
    main_component = max(components, key=len)
    
    # Build KDTree from main component nodes for efficient nearest-neighbor search
    main_nodes = list(main_component)
    main_coords = np.array([(node[0], node[1]) for node in main_nodes])
    tree = KDTree(main_coords)
    
    components_merged = 0
    edges_added = 0
    
    # Process small disconnected components
    for component in components:
        if component == main_component:
            continue
            
        # Only process small isolated fragments (< 10 nodes)
        # Larger components likely indicate real network gaps that should be reported
        # Threshold of 10 accounts for slightly larger street fragments while still
        # protecting against merging entire disconnected neighborhoods
        if len(component) >= 10:
            continue
        
        # Find the node in this component closest to main component
        # BUT: Don't use terminal nodes as the bridge point (they should stay connected to buildings)
        best_orphan_node = None
        best_distance = float('inf')
        best_main_node = None
        
        for orphan_node in component:
            # Skip terminal nodes when choosing bridge point
            # (terminals must stay at their building connection points)
            if orphan_node in terminal_nodes:
                continue
                
            orphan_coords = [orphan_node[0], orphan_node[1]]
            dist, nearest_idx = tree.query(orphan_coords, k=1)
            
            if dist < best_distance:
                best_distance = dist
                best_orphan_node = orphan_node
                best_main_node = main_nodes[nearest_idx]
        
        # If we found a suitable bridge point within threshold, connect it
        if best_orphan_node is not None and best_distance <= merge_threshold:
            # Use average weight from orphan's existing edges, or distance as fallback
            orphan_edges = list(G.edges(best_orphan_node, data=True))
            if orphan_edges:
                avg_weight = np.mean([data.get('weight', best_distance) for _, _, data in orphan_edges])
            else:
                avg_weight = best_distance
            
            G.add_edge(best_orphan_node, best_main_node, weight=avg_weight)
            components_merged += 1
            edges_added += 1
    
    if components_merged > 0:
        print(f"Merged {components_merged} orphan component(s) to main network (added {edges_added} bridging edge(s))")
    
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
    return [(round(x, precision), round(y, precision)) for x, y in coords]


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
    edges_gdf = gdf(edges_data, crs=crs)

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
