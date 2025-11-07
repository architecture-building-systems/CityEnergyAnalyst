"""
Graph Utilities for Network Layout

Helper functions for converting between GeoDataFrames and NetworkX graphs,
and other graph-related utilities for thermal network layout.
"""

import networkx as nx
from shapely.geometry import Point, LineString, MultiLineString
from geopandas import GeoDataFrame as gdf

from cea.constants import SHAPEFILE_TOLERANCE


def gdf_to_nx(network_gdf, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True, **edge_attrs):
    """
    Convert GeoDataFrame to NetworkX Graph.

    This is a consolidated helper function for converting GeoDataFrame geometries
    to NetworkX graphs with consistent handling of LineString and MultiLineString
    geometries.

    :param network_gdf: GeoDataFrame with LineString/MultiLineString geometries
    :type network_gdf: geopandas.GeoDataFrame
    :param coord_precision: Decimal places for coordinate rounding (default: 3)
    :type coord_precision: int
    :param preserve_geometry: If True, store full LineString geometry as edge attribute (default: False)
    :type preserve_geometry: bool
    :param edge_attrs: Additional edge attributes to extract from GeoDataFrame columns
    :type edge_attrs: dict
    :return: NetworkX Graph with edges representing network connections
    :rtype: networkx.Graph

    Example:
        >>> # Simple conversion
        >>> G = gdf_to_nx(streets_gdf, coord_precision=3)
        >>>
        >>> # Preserve full geometries for curved streets
        >>> G = gdf_to_nx(streets_gdf, preserve_geometry=True)
        >>>
        >>> # Extract specific columns as edge attributes
        >>> G = gdf_to_nx(streets_gdf, type_mat='type_mat', pipe_DN='pipe_DN')

    Notes:
        - Coordinates are rounded to avoid floating-point precision issues
        - Both LineString and MultiLineString geometries are supported
        - Edge weight is set to geometry length by default
        - If preserve_geometry=True, 'geometry' edge attribute contains full LineString
    """
    G = nx.Graph()

    for idx, row in network_gdf.iterrows():
        geom = row.geometry

        # Process LineString or MultiLineString
        if geom.geom_type == 'LineString':
            _add_linestring_to_graph(G, geom, row, idx, coord_precision, preserve_geometry, **edge_attrs)
        elif geom.geom_type == 'MultiLineString':
            for sub_line in geom.geoms:
                _add_linestring_to_graph(G, sub_line, row, idx, coord_precision, preserve_geometry, **edge_attrs)

    return G


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
    edge_data = {'weight': line.length}

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
