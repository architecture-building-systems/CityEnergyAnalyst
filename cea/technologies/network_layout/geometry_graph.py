"""
Geometry-preserving graph implementation for network layout.

This module provides a NetworkX graph wrapper that preserves full LineString geometries
(including curves) as edge attributes, allowing for:
- Dynamic edge splitting at junction points
- Geometry-aware edge operations
- Collapsing edges back to original curved geometries
- Clean visualization output

TYPICAL USAGE
=============

Basic usage - build from GeoDataFrame:
    from cea.technologies.network_layout.geometry_graph import GeometryPreservingGraph
    gp_graph = GeometryPreservingGraph(streets_gdf)
    gp_graph.add_junction((node_u, node_v), junction_point)
    result_gdf = gp_graph.to_geodataframe(crs)

Advanced usage - collapse edges after optimization:
    # After Steiner tree optimization
    steiner_edges = [(n1, n2), (n2, n3), (n3, n4)]
    gp_graph.collapse_edge_chain([n1, n2, n3, n4])
    final_gdf = gp_graph.to_geodataframe(crs)

WORKFLOW INTEGRATION
====================

This class enables a hybrid workflow:
1. Build graph preserving curved geometries
2. Add junctions only where needed (building connections, intersections)
3. Run Steiner tree optimization on the graph structure
4. Collapse edges back to original curves for export

This combines computational efficiency (fewer nodes) with aesthetic quality (curved output).
"""

import networkx as nx
from geopandas import GeoDataFrame as gdf
from shapely.geometry import Point, LineString
from shapely.ops import linemerge
from shapely.strtree import STRtree
import warnings
from typing import Optional, Tuple, List

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class GeometryPreservingGraph:
    """
    NetworkX graph wrapper that preserves LineString geometries when edges are split or merged.

    This class maintains the visual quality of curved streets while allowing dynamic
    topology changes (adding junctions, splitting edges, merging edges).

    Edge attributes:
        - weight: Edge length in meters (for shortest path algorithms)
        - geometry: Full LineString geometry (may have multiple vertices)
        - original_id: Reference to original input edge (if available)

    Example:
        >>> gp_graph = GeometryPreservingGraph(streets_gdf)
        >>> # Add junction where building connects mid-street
        >>> gp_graph.add_junction(('node_a', 'node_b'), (50.0, 25.0))
        >>> # Export with preserved geometries
        >>> output_gdf = gp_graph.to_geodataframe(crs='EPSG:2056')
    """

    def __init__(self, network_gdf: Optional[gdf] = None, coord_precision: int = SHAPEFILE_TOLERANCE):
        """
        Initialize geometry-preserving graph.

        :param network_gdf: GeoDataFrame with LineString geometries (optional)
        :type network_gdf: gdf, optional
        :param coord_precision: Decimal places for coordinate rounding
        :type coord_precision: int
        """
        self.G = nx.Graph()
        self.coord_precision = coord_precision
        self._edge_id_counter = 0  # For tracking edges

        # R-tree spatial index for fast nearest edge queries
        self._spatial_index = None
        self._edge_geometries: list[LineString] | None = None
        self._edge_lookup: dict[int, tuple[int, int]] | None = None

        if network_gdf is not None:
            self._build_from_gdf(network_gdf)

    def _build_from_gdf(self, network_gdf: gdf):
        """
        Build graph from GeoDataFrame, preserving full geometries.

        :param network_gdf: GeoDataFrame with LineString geometries
        :type network_gdf: gdf
        """
        # Use consolidated helper for conversion, then enhance with geometry preservation
        from cea.technologies.network_layout.graph_utils import gdf_to_nx
        temp_graph = gdf_to_nx(network_gdf, coord_precision=self.coord_precision, preserve_geometry=True)

        # Copy edges to our graph with additional metadata
        for u, v, data in temp_graph.edges(data=True):
            edge_id = self._edge_id_counter
            self._edge_id_counter += 1

            self.G.add_edge(u, v,
                           weight=data['weight'],
                           geometry=data['geometry'],
                           original_id=None,  # Could be passed via edge_attrs if needed
                           edge_id=edge_id)

    def _add_edge_from_linestring(self, line: LineString, original_id=None):
        """
        Add an edge from a LineString geometry.

        :param line: LineString geometry
        :type line: LineString
        :param original_id: Original edge ID from input data
        :type original_id: any, optional
        """
        coords = list(line.coords)
        start = self._round_coords(coords[0])
        end = self._round_coords(coords[-1])

        edge_id = self._edge_id_counter
        self._edge_id_counter += 1

        self.G.add_edge(start, end,
                       weight=line.length,
                       geometry=line,
                       original_id=original_id,
                       edge_id=edge_id)

        # Invalidate spatial index since topology changed
        self._invalidate_spatial_index()

    def add_junction(self, edge: Tuple, junction_point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Add a junction point to an existing edge, splitting it into two edges.

        This preserves the original curved geometry by splitting the LineString
        at the junction point. The two resulting edges maintain their curve shape.

        :param edge: Tuple (node_u, node_v) representing the edge to split
        :type edge: Tuple
        :param junction_point: Coordinates (x, y) of the new junction node
        :type junction_point: Tuple
        :return: Rounded junction node coordinates
        :rtype: Tuple

        Example:
            >>> gp_graph.add_junction(('node_a', 'node_b'), (50.0, 25.0))
            >>> # Edge (node_a, node_b) is now split into:
            >>> # - (node_a, junction)
            >>> # - (junction, node_b)
        """
        node_u, node_v = edge

        if not self.G.has_edge(node_u, node_v):
            raise ValueError(f"Edge {edge} does not exist in graph")

        # Get original edge data
        edge_data = self.G.edges[node_u, node_v]
        original_geom = edge_data['geometry']
        original_id = edge_data.get('original_id')

        # Find nearest point on the line for the junction
        junction_on_line = self._find_nearest_point_on_line(junction_point, original_geom)

        # Split the LineString geometry at the junction point
        geom1, geom2 = self._split_geometry_at_point(original_geom, junction_on_line)

        # Round junction coordinates for graph node
        junction_node = self._round_coords(junction_on_line.coords[0])

        # If junction is extremely close to an endpoint, don't split
        if self._calculate_distance(junction_node, node_u) < SNAP_TOLERANCE:
            return node_u
        if self._calculate_distance(junction_node, node_v) < SNAP_TOLERANCE:
            return node_v

        # Remove original edge
        self.G.remove_edge(node_u, node_v)

        # Add two new edges with split geometries
        edge_id_1 = self._edge_id_counter
        self._edge_id_counter += 1
        edge_id_2 = self._edge_id_counter
        self._edge_id_counter += 1

        self.G.add_edge(node_u, junction_node,
                       weight=geom1.length,
                       geometry=geom1,
                       original_id=original_id,
                       edge_id=edge_id_1)

        self.G.add_edge(junction_node, node_v,
                       weight=geom2.length,
                       geometry=geom2,
                       original_id=original_id,
                       edge_id=edge_id_2)

        # Invalidate spatial index since topology changed
        self._invalidate_spatial_index()

        return junction_node

    def _split_geometry_at_point(self, line: LineString, point: Point) -> Tuple[LineString, LineString]:
        """
        Split a LineString at a point, preserving curve geometry.

        :param line: LineString to split
        :type line: LineString
        :param point: Point where to split the line
        :type point: Point
        :return: Tuple of (LineString before point, LineString after point)
        :rtype: Tuple[LineString, LineString]
        """
        # Project point onto line to get distance along the line
        distance_along = line.project(point)

        # Get all coordinates
        coords = list(line.coords)

        # Find which segment the point falls on
        accumulated_dist = 0
        split_idx = None

        for i in range(len(coords) - 1):
            segment = LineString([coords[i], coords[i+1]])
            seg_length = segment.length

            if accumulated_dist + seg_length >= distance_along - 1e-9:  # Small epsilon for float comparison
                split_idx = i
                break
            accumulated_dist += seg_length

        if split_idx is None:
            split_idx = len(coords) - 2

        # Create interpolated point on the line
        split_point = line.interpolate(distance_along)
        split_coords = (split_point.x, split_point.y)

        # Build two new LineStrings
        # Segment 1: from start to split point (including intermediate curve vertices)
        coords1 = coords[:split_idx+1] + [split_coords]
        # Segment 2: from split point to end (including intermediate curve vertices)
        coords2 = [split_coords] + coords[split_idx+1:]

        return LineString(coords1), LineString(coords2)

    def collapse_edge_chain(self, nodes: List[Tuple]) -> None:
        """
        Collapse a chain of edges into a single edge with merged geometry.

        Useful for simplifying networks after Steiner tree optimization,
        merging sequential edges back into smooth curves.

        :param nodes: List of nodes forming a chain [n1, n2, n3, ..., nk]
        :type nodes: List[Tuple]

        Example:
            >>> # Collapse three edges into one
            >>> gp_graph.collapse_edge_chain([node_a, node_b, node_c, node_d])
            >>> # Edges (a,b), (b,c), (c,d) become single edge (a,d)
        """
        if len(nodes) < 3:
            return  # Need at least 3 nodes to collapse

        # Collect all geometries in the chain
        geometries = []
        total_weight = 0
        original_id = None

        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i+1]
            if not self.G.has_edge(u, v):
                raise ValueError(f"Edge {u}↔{v} does not exist in chain")

            edge_data = self.G.edges[u, v]
            geometries.append(edge_data['geometry'])
            total_weight += edge_data['weight']

            # Preserve original_id if available
            if original_id is None:
                original_id = edge_data.get('original_id')

        # Merge geometries into a single LineString
        try:
            # Try using linemerge for smooth merging
            merged_geometry = linemerge(geometries)
            if merged_geometry.geom_type != 'LineString':
                # Fallback: manual coordinate concatenation
                merged_geometry = self._merge_linestrings_manual(geometries)
        except Exception:
            # Fallback: manual coordinate concatenation
            merged_geometry = self._merge_linestrings_manual(geometries)

        # Remove all intermediate edges
        for i in range(len(nodes) - 1):
            self.G.remove_edge(nodes[i], nodes[i+1])

        # Remove intermediate nodes (if degree 0)
        for node in nodes[1:-1]:
            if self.G.degree(node) == 0:
                self.G.remove_node(node)

        # Add collapsed edge
        edge_id = self._edge_id_counter
        self._edge_id_counter += 1

        self.G.add_edge(nodes[0], nodes[-1],
                       weight=total_weight,
                       geometry=merged_geometry,
                       original_id=original_id,
                       edge_id=edge_id,
                       collapsed=True)

        # Invalidate spatial index since topology changed
        self._invalidate_spatial_index()

    def _merge_linestrings_manual(self, geometries: List[LineString]) -> LineString:
        """
        Manually merge LineStrings by concatenating coordinates.

        :param geometries: List of LineStrings to merge
        :type geometries: List[LineString]
        :return: Merged LineString
        :rtype: LineString
        """
        all_coords = []
        for geom in geometries:
            coords = list(geom.coords)
            if all_coords and self._coords_equal(coords[0], all_coords[-1]):
                # Skip duplicate point at junction
                all_coords.extend(coords[1:])
            else:
                all_coords.extend(coords)

        return LineString(all_coords)

    def collapse_degree_2_nodes(self) -> int:
        """
        Collapse all degree-2 nodes (nodes with exactly 2 neighbors).

        This simplifies the network by merging sequential edges that pass
        through junction points with no branches.

        :return: Number of nodes collapsed
        :rtype: int

        Example:
            >>> # After Steiner tree, you may have: A→B→C→D
            >>> # Where B and C are just pass-through points
            >>> gp_graph.collapse_degree_2_nodes()
            >>> # Result: A→D (with merged curved geometry)
        """
        collapsed_count = 0

        # Find all degree-2 nodes
        degree_2_nodes = [node for node in self.G.nodes() if self.G.degree(node) == 2]

        for node in degree_2_nodes:
            if not self.G.has_node(node):  # May have been removed already
                continue

            neighbors = list(self.G.neighbors(node))
            if len(neighbors) != 2:  # Degree may have changed
                continue

            # Collapse the chain: neighbor1 → node → neighbor2
            chain = [neighbors[0], node, neighbors[1]]
            try:
                self.collapse_edge_chain(chain)
                collapsed_count += 1
            except Exception as e:
                warnings.warn(f"Could not collapse node {node}: {e}")

        return collapsed_count

    def to_geodataframe(self, crs: str) -> gdf:
        """
        Convert graph back to GeoDataFrame with full geometries preserved.

        :param crs: Coordinate reference system for the output
        :type crs: str
        :return: GeoDataFrame with LineString geometries
        :rtype: gdf
        """
        edges = []
        for u, v, data in self.G.edges(data=True):
            edges.append({
                'geometry': data['geometry'],
                'weight': data['weight'],
                'u': u,
                'v': v,
                'original_id': data.get('original_id'),
                'edge_id': data.get('edge_id'),
                'collapsed': data.get('collapsed', False)
            })

        return gdf(edges, crs=crs)

    def _build_spatial_index(self):
        """
        Build R-tree spatial index for fast nearest edge queries.

        This is called lazily on first use of find_nearest_edge(). The index
        provides O(log n) nearest-neighbor search instead of O(n) brute force.

        The index must be rebuilt after graph topology changes (add_junction,
        collapse_edge_chain, etc.) by calling _invalidate_spatial_index().
        """
        if self._spatial_index is not None:
            return  # Already built

        if self.G.number_of_edges() == 0:
            return  # Empty graph

        # Collect all edge geometries with their corresponding edge tuples
        self._edge_geometries = []
        self._edge_lookup = {}

        for u, v, data in self.G.edges(data=True):
            geom = data['geometry']
            self._edge_geometries.append(geom)
            # Map geometry id to edge tuple (u, v)
            self._edge_lookup[id(geom)] = (u, v)

        # Build STRtree (bulk-loading R-tree)
        self._spatial_index = STRtree(self._edge_geometries)

    def _invalidate_spatial_index(self):
        """
        Invalidate the spatial index after graph topology changes.

        Called internally after operations that modify edges (add_junction,
        collapse_edge_chain, etc.) to ensure the index stays synchronized.
        """
        self._spatial_index = None
        self._edge_geometries = None
        self._edge_lookup = None

    def find_nearest_edge(self, point: Point) -> Tuple[Optional[Tuple], Optional[Point], Optional[float]]:
        """
        Find the nearest edge to a given point using R-tree spatial indexing.

        Uses Shapely's STRtree for O(log n) nearest-neighbor search instead of
        O(n) brute-force iteration. The spatial index is built lazily on first
        use and automatically invalidated when the graph topology changes.

        :param point: Point to search from
        :type point: Point
        :return: Tuple of (edge, nearest_point_on_edge, distance)
        :rtype: Tuple[Optional[Tuple], Optional[Point], Optional[float]]

        Example:
            >>> edge, nearest_pt, dist = gp_graph.find_nearest_edge(Point(50, 25))
            >>> print(f"Nearest edge: {edge}, distance: {dist:.2f}m")
        """
        # Lazy build spatial index on first use
        self._build_spatial_index()

        if self._spatial_index is None or not self._edge_geometries or not self._edge_lookup:
            return None, None, None

        # Query nearest geometry using R-tree (returns index into geometry list)
        nearest_idx = self._spatial_index.nearest(point)
        nearest_geom = self._edge_geometries[int(nearest_idx)]

        # Calculate projected point and distance
        projected_point = nearest_geom.interpolate(nearest_geom.project(point))
        distance = point.distance(projected_point)

        # Look up the edge tuple (u, v)
        edge = self._edge_lookup[id(nearest_geom)]

        return edge, projected_point, distance

    def _find_nearest_point_on_line(self, point: Tuple, line: LineString) -> Point:
        """
        Find nearest point on line to given coordinates.

        :param point: Point coordinates (x, y)
        :type point: Tuple
        :param line: LineString to project onto
        :type line: LineString
        :return: Nearest point on line
        :rtype: Point
        """
        pt = Point(point)
        return line.interpolate(line.project(pt))

    def _round_coords(self, coords: Tuple[float, float]) -> Tuple[float, float]:
        """
        Round coordinates to instance's coordinate precision.

        :param coords: Coordinates (x, y)
        :type coords: Tuple
        :return: Rounded coordinates
        :rtype: Tuple
        """
        return (round(coords[0], self.coord_precision),
                round(coords[1], self.coord_precision))

    def _coords_equal(self, coord1: Tuple[float, float], coord2: Tuple[float, float], tolerance: float = 1e-9) -> bool:
        """
        Check if two coordinates are equal within tolerance.

        :param coord1: First coordinate (x, y)
        :type coord1: Tuple
        :param coord2: Second coordinate (x, y)
        :type coord2: Tuple
        :param tolerance: Distance tolerance
        :type tolerance: float
        :return: True if coordinates are equal within tolerance
        :rtype: bool
        """
        return abs(coord1[0] - coord2[0]) < tolerance and abs(coord1[1] - coord2[1]) < tolerance

    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two coordinates.

        :param coord1: First coordinate (x, y)
        :type coord1: Tuple
        :param coord2: Second coordinate (x, y)
        :type coord2: Tuple
        :return: Distance
        :rtype: float
        """
        return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5

    @staticmethod
    def build_geometry_map(network_gdf: gdf, coord_precision: int) -> dict:
        """
        Build a lookup table mapping edge keys to original curved geometries.

        Used to preserve street curves during graph corrections.

        :param network_gdf: GeoDataFrame with network LineStrings
        :type network_gdf: gdf
        :param coord_precision: Number of decimal places for coordinate rounding
        :type coord_precision: int
        :return: Dict mapping (node1, node2) tuples to LineString geometries
        :rtype: dict

        Example:
            >>> geometry_map = GeometryPreservingGraph.build_geometry_map(streets_gdf, SHAPEFILE_TOLERANCE)
            >>> # Apply corrections...
            >>> restored = GeometryPreservingGraph.restore_geometries(corrected_gdf, geometry_map, SHAPEFILE_TOLERANCE)
        """
        geometry_map = {}
        for _, row in network_gdf.iterrows():
            line = row.geometry
            if line.geom_type == 'LineString':
                coords = list(line.coords)
                start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
                end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
                edge_key = tuple(sorted([start, end]))
                # Store original geometry (prefer longer/more detailed if duplicate)
                if edge_key not in geometry_map or len(coords) > len(list(geometry_map[edge_key].coords)):
                    geometry_map[edge_key] = line
            elif line.geom_type == 'MultiLineString':
                for sub_line in line.geoms:
                    coords = list(sub_line.coords)
                    start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
                    end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
                    edge_key = tuple(sorted([start, end]))
                    if edge_key not in geometry_map or len(coords) > len(list(geometry_map[edge_key].coords)):
                        geometry_map[edge_key] = sub_line
        return geometry_map

    @staticmethod
    def restore_geometries(corrected_gdf: gdf, geometry_map: dict, coord_precision: int) -> gdf:
        """
        Restore original curved geometries to a corrected network GeoDataFrame.

        After graph corrections, edges may have been added/removed. This function
        replaces straight-line edges with original curved geometries where available.

        :param corrected_gdf: GeoDataFrame after corrections (with straight lines)
        :type corrected_gdf: gdf
        :param geometry_map: Dict mapping edge keys to original LineString geometries
        :type geometry_map: dict
        :param coord_precision: Number of decimal places for coordinate rounding
        :type coord_precision: int
        :return: GeoDataFrame with restored curved geometries
        :rtype: gdf

        Example:
            >>> geometry_map = GeometryPreservingGraph.build_geometry_map(streets_gdf, SHAPEFILE_TOLERANCE)
            >>> corrected = apply_graph_corrections(streets_gdf)
            >>> restored = GeometryPreservingGraph.restore_geometries(corrected, geometry_map, SHAPEFILE_TOLERANCE)
        """
        restored_lines = []
        for _, row in corrected_gdf.iterrows():
            line = row.geometry
            coords = list(line.coords)
            start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
            end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
            edge_key = tuple(sorted([start, end]))

            if edge_key in geometry_map:
                # Use original curved geometry
                restored_lines.append(geometry_map[edge_key])
            else:
                # Keep straight line (new edge from corrections)
                restored_lines.append(line)

        return gdf(geometry=restored_lines, crs=corrected_gdf.crs)

    @property
    def graph(self) -> nx.Graph:
        """Get the underlying NetworkX graph."""
        return self.G

    def __repr__(self) -> str:
        """String representation of the graph."""
        return f"GeometryPreservingGraph(nodes={self.G.number_of_nodes()}, edges={self.G.number_of_edges()})"
