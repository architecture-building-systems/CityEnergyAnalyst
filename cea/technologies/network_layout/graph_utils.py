"""
Graph Utilities for Network Layout

Helper functions for converting between GeoDataFrames and NetworkX graphs,
and other graph-related utilities for thermal network layout.
"""

import networkx as nx


def gdf_to_nx(network_gdf, coord_precision=3, preserve_geometry=False, **edge_attrs):
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
