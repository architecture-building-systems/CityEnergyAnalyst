"""
Network connectivity module for connecting buildings to street networks.

This module creates a graph of potential thermal network paths by connecting building centroids to the nearest
points on a street network, preparing the data for Steiner tree optimization.

WORKFLOW (Single-Pass with Preprocessing):
==========================================
1. Load and validate street network
2. **CLEAN**: Preprocess raw street network
   - Split streets at intersection points (automatic detection via unary_union)
   - Snap near-miss endpoints to nearby lines (fix manual digitization errors)
   - Re-split to create junctions at newly connected points
3. **CORRECT**: Apply graph corrections to cleaned network
   - Fixes remaining topology issues: self-loops, close nodes, disconnected components
   - Uses GraphCorrector with coordinate precision matching
4. Create building terminal connection lines (geometries from building → nearest street point)
5. **PASS 2 ELIMINATED**: No second correction pass needed!
   - Junction additions maintain connectivity (split edges but don't disconnect)
   - Terminal additions maintain connectivity (add connected edges)
   - Geometry restoration snaps endpoints to rounded coordinates (preserves connectivity)
6. Extract all significant points (line endpoints, including terminal connection points)
7. Discretize network: split lines at all significant points in one efficient operation
8. Output fully connected network for Steiner tree optimization

RATIONALE FOR PREPROCESSING + SINGLE PASS:
===========================================
**Why preprocessing?** Cleaning the raw street network first:
- Automatically detects and fixes intersection topology issues
- Handles common data quality problems (near-miss connections, gaps)
- Reduces burden on GraphCorrector (fewer edge cases to handle)
- Results in higher quality network topology

**Why single correction pass is sufficient?**
- Preprocessing creates proper junctions at natural intersections
- Endpoint snapping in geometry restoration prevents round-trip disconnections
- Building terminal additions explicitly maintain connectivity
- Second pass was defensive programming for issues now prevented upstream

ARCHITECTURE:
=============
- apply_graph_corrections: Unified function for all graph corrections (with optional protected nodes)
  * Converts GeoDataFrame → NetworkX graph → applies GraphCorrector → converts back to GeoDataFrame
  * GraphCorrector (graph_helper.py): Topology fixes with optional protected nodes
  * Merges close nodes within SNAP_TOLERANCE (except protected nodes)
  * Connects intersecting edges from different components
  * Connects disconnected components (avoids direct building-to-building connections when protected nodes given)
- create_terminals: Creates LineStrings from buildings to nearest street points
- calculate_significant_points: Extracts unique line endpoints (includes terminal connection points)
- split_streets_at_intersections: Automatically splits streets at intersection points using unary_union
- snap_endpoints_to_nearby_lines: Fixes near-miss connections by snapping close endpoints
- split_network_at_points: Discretizes network by snapping to specified points and splitting

This approach ensures:
- Street network topology is clean before adding buildings
- Building centroids (protected nodes) are NOT moved from their exact locations
- Final network is fully connected and suitable for Steiner tree optimization
- Better network quality by following street topology for component connections
"""

import warnings

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString
from shapely.ops import split, snap

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE
from cea.datamanagement.graph_helper import GraphCorrector
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile
from cea.technologies.network_layout.geometry_graph import GeometryPreservingGraph
from cea.technologies.network_layout.graph_utils import gdf_to_nx

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Malcolm Kesson", "Mattijn"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def compute_end_points(lines, crs):
    all_points = []
    for line in lines:
        for i in [0, -1]:  # start and end point
            all_points.append(line.coords[i])

    unique_points = set(all_points)
    endpts = [Point(p) for p in unique_points]
    df = gdf(geometry=endpts, crs=crs)

    return df


def split_streets_at_intersections(network_gdf: gdf) -> gdf:
    """
    Split street LineStrings at intersection points using unary_union.

    This function uses Shapely's unary_union to automatically detect where lines
    intersect and split them at those points, creating proper junctions. This is
    cleaner than manually finding intersection points.

    The unary_union operation:
    1. Merges all overlapping/touching lines
    2. Splits lines at intersection points
    3. Returns a MultiLineString with properly segmented lines

    :param network_gdf: GeoDataFrame with street LineStrings
    :type network_gdf: gdf
    :return: GeoDataFrame with streets split at all intersections
    :rtype: gdf

    Example:
        Before: Two crossing streets as continuous lines
        After: Four line segments meeting at intersection point
    """
    # Union all geometries - this automatically splits at intersections
    merged = network_gdf.geometry.union_all()

    # Extract individual line segments into a GeoDataFrame using explode()
    # explode() is vectorized and handles MultiLineString -> individual LineStrings efficiently
    result_gdf = gdf(geometry=[merged], crs=network_gdf.crs).explode(index_parts=False).reset_index(drop=True)

    # Vectorized filtering: remove extremely short segments (numerical artifacts)
    # This uses vectorized length calculation instead of list comprehension
    min_length = 10 ** (-SHAPEFILE_TOLERANCE)
    result_gdf = result_gdf[result_gdf.geometry.length > min_length].reset_index(drop=True)

    return result_gdf


def snap_endpoints_to_nearby_lines(network_gdf: gdf, snap_tolerance: float) -> gdf:
    """
    Snap line endpoints to nearby lines within tolerance to fix near-miss connections.

    This function addresses a common issue in manually digitized street networks where
    lines should connect but have small gaps due to drawing inaccuracies. It finds
    dangling endpoints (not already connected to other lines) that are close to other
    lines and snaps them to create proper connections.

    Optimization: Only considers endpoints that are "dangling" (terminal points not
    already connected), dramatically reducing the search space.

    Use Cases:
    ----------
    - Fixing manually digitized street networks with near-miss connections
    - Cleaning data where GPS inaccuracies created small gaps
    - Connecting street segments that should meet but have tiny offsets

    Process:
    --------
    1. Identify all dangling endpoints (appears exactly once in network)
    2. For each dangling endpoint, find nearby lines within tolerance
    3. Snap endpoint to nearest point on closest line
    4. Rebuild geometries with snapped endpoints

    :param network_gdf: GeoDataFrame with street LineStrings
    :type network_gdf: gdf
    :param snap_tolerance: Maximum distance to snap endpoints (meters)
    :type snap_tolerance: float
    :return: GeoDataFrame with snapped connections
    :rtype: gdf

    Example:
        >>> # Fix near-miss connections within 0.5 meters
        >>> cleaned_streets = snap_endpoints_to_nearby_lines(streets_gdf, 0.5)
    """
    from shapely.strtree import STRtree
    from collections import Counter

    # Step 1: Find dangling endpoints (terminal points not connected)
    # Count how many times each endpoint appears across all lines
    endpoint_counts = Counter()
    for geom in network_gdf.geometry:
        coords = list(geom.coords)
        start = tuple(coords[0])
        end = tuple(coords[-1])
        endpoint_counts[start] += 1
        endpoint_counts[end] += 1

    # Dangling endpoints appear exactly once (not shared with other lines)
    dangling_endpoints = {pt for pt, count in endpoint_counts.items() if count == 1}

    if not dangling_endpoints:
        # No dangling endpoints, nothing to snap
        return network_gdf

    # Step 2: Create spatial index for fast nearest-neighbor queries
    line_index = STRtree(network_gdf.geometry)

    # Step 3: Process only lines that have dangling endpoints
    modified_geometries = []

    for idx, row in network_gdf.iterrows():
        line = row.geometry
        coords = list(line.coords)

        start = tuple(coords[0])
        end = tuple(coords[-1])

        # Check if endpoints are dangling
        start_is_dangling = start in dangling_endpoints
        end_is_dangling = end in dangling_endpoints

        # Skip if no dangling endpoints
        if not start_is_dangling and not end_is_dangling:
            modified_geometries.append(line)
            continue

        new_start = coords[0]
        new_end = coords[-1]

        # Snap start point if it's dangling
        if start_is_dangling:
            start_point = Point(coords[0])
            nearby_indices = line_index.query(start_point.buffer(snap_tolerance))

            for nearby_idx in nearby_indices:
                nearby_line = network_gdf.iloc[nearby_idx].geometry
                # Don't snap to itself
                if nearby_line == line:
                    continue

                # Check if point is close enough
                distance = nearby_line.distance(start_point)
                if 0 < distance < snap_tolerance:
                    # Snap to nearest point on line
                    snapped = nearby_line.interpolate(nearby_line.project(start_point))
                    new_start = (snapped.x, snapped.y)
                    break

        # Snap end point if it's dangling
        if end_is_dangling:
            end_point = Point(coords[-1])
            nearby_indices = line_index.query(end_point.buffer(snap_tolerance))

            for nearby_idx in nearby_indices:
                nearby_line = network_gdf.iloc[nearby_idx].geometry
                # Don't snap to itself
                if nearby_line == line:
                    continue

                # Check if point is close enough
                distance = nearby_line.distance(end_point)
                if 0 < distance < snap_tolerance:
                    # Snap to nearest point on line
                    snapped = nearby_line.interpolate(nearby_line.project(end_point))
                    new_end = (snapped.x, snapped.y)
                    break

        # Rebuild geometry with potentially snapped endpoints
        new_coords = [new_start] + coords[1:-1] + [new_end]
        modified_geometries.append(LineString(new_coords))

    return gdf(geometry=modified_geometries, crs=network_gdf.crs)


def clean_street_network(network_gdf: gdf, snap_tolerance: float) -> gdf:
    """
    Comprehensive street network cleaning workflow.

    This function applies a sequence of cleaning operations to fix common issues
    in street network data:
    1. Split streets at intersection points (automatic detection)
    2. Snap near-miss endpoints to nearby lines (fix small gaps)
    3. Split again at new intersections created by snapping

    This is the recommended preprocessing step before applying graph corrections.

    :param network_gdf: GeoDataFrame with raw street LineStrings
    :type network_gdf: gdf
    :param snap_tolerance: Maximum distance to snap endpoints (meters)
    :type snap_tolerance: float
    :return: Cleaned GeoDataFrame with proper topology
    :rtype: gdf

    Example:
        >>> # Clean raw street network before processing
        >>> cleaned = clean_street_network(raw_streets_gdf, SNAP_TOLERANCE)
        >>> # Now apply graph corrections
        >>> corrected = apply_graph_corrections(cleaned)
    """
    print("  1. Splitting streets at intersections...")
    network_gdf = split_streets_at_intersections(network_gdf)

    print("  2. Snapping near-miss endpoints...")
    network_gdf = snap_endpoints_to_nearby_lines(network_gdf, snap_tolerance)

    print("  3. Re-splitting after snapping (creates new intersections)...")
    network_gdf = split_streets_at_intersections(network_gdf)

    return network_gdf

def split_network_at_points(gdf_line: gdf, gdf_points: gdf, snap_tolerance: float, crs: str):
    """
    Split network lines at specified point locations with snapping tolerance.

    Unlike split_streets_at_intersections() which automatically finds intersections,
    this function splits lines at explicitly provided points (e.g., building connection
    points, manually specified junction locations). Points are snapped to the nearest
    position on lines within the tolerance before splitting.

    Use Cases:
    ----------
    - Adding building terminal connection points to a street network
    - Splitting at manually specified junction locations
    - Adding custom split points that aren't natural line intersections

    Comparison:
    -----------
    - split_streets_at_intersections(): Automatic intersection detection via unary_union
    - split_network_at_points(): Manual point specification with snapping tolerance

    :param gdf_line: GeoDataFrame with network line segments (streets + building connections)
    :type gdf_line: gdf
    :param gdf_points: GeoDataFrame with point geometries where splits should occur
    :type gdf_points: gdf
    :param snap_tolerance: Distance tolerance for snapping points to lines (meters)
    :type snap_tolerance: float
    :param crs: Coordinate reference system
    :type crs: str
    :return: Discretized network as individual segments
    :rtype: gdf

    Example:
        >>> # Split streets at building connection points
        >>> building_points = gdf(geometry=[Point(100, 200), Point(150, 250)])
        >>> split_network = split_network_at_points(streets_gdf, building_points,
        ...                                          SNAP_TOLERANCE, crs)

    Reference: https://github.com/ojdo/python-tools/blob/master/shapelytools.py#L144
    """
    # Union all geometries into single objects for splitting operation
    line = gdf_line.geometry.union_all()
    snap_points = gdf_points.geometry.union_all()

    # Snap points to lines within tolerance, then split lines at those points
    # This ensures all significant points become explicit vertices in the network
    split_line = split(line, snap(snap_points, line, snap_tolerance))

    # Vectorized extraction: use explode() to handle MultiLineString -> individual LineStrings
    result_gdf = gdf(geometry=[split_line], crs=crs).explode(index_parts=False).reset_index(drop=True)

    # Vectorized filtering: remove numerical artifacts (extremely short segments)
    # Use threshold based on coordinate precision: 10^-6 meters (1 micrometer) with SHAPEFILE_TOLERANCE=6
    min_length = 10 ** (-SHAPEFILE_TOLERANCE)
    result_gdf = result_gdf[result_gdf.geometry.length > min_length].reset_index(drop=True)

    return result_gdf


def near_analysis(building_centroids, street_network, crs):
    # Get the nearest edge for each building centroid
    nearest_indexes = street_network.sindex.nearest(building_centroids.geometry, return_all=False)[1]
    nearest_lines = street_network.iloc[nearest_indexes].reset_index(drop=True)  # reset index so vectorization works

    # Find length along line that is closest to the point (project) and get interpolated point on the line (interpolate)
    nearest_points = nearest_lines.interpolate(nearest_lines.project(building_centroids))

    df = gdf({"name": building_centroids["name"]}, geometry=nearest_points, crs=crs)
    return df


def calculate_significant_points(prototype_network, crs):
    """
    Extract all significant points (line endpoints) from the network for discretization.

    After GraphCorrector has processed street intersections and terminals have been added,
    only line endpoints are needed. Terminal connection points are automatically included
    as endpoints of terminal lines. The split_network_at_points function will handle
    snapping and splitting lines at these points.

    :param prototype_network: Combined network GeoDataFrame (streets + terminals)
    :type prototype_network: gdf
    :param crs: Coordinate reference system
    :type crs: str
    :return: GeoDataFrame of unique significant points
    :rtype: gdf
    """
    # Extract all line endpoints (includes both street vertices and terminal connection points)
    gdf_points = compute_end_points(prototype_network.geometry, crs)

    # Remove duplicate points efficiently using drop_duplicates on geometry
    gdf_points = gdf_points.drop_duplicates(subset=['geometry']).reset_index(drop=True)

    return gdf_points


def create_terminals(building_centroids: gdf, street_network: gdf, crs: str) -> gdf:
    """
    Create terminal connection lines from building centroids to nearest points on street network.
    
    This function:
    1. Finds nearest point on street network for each building
    2. Creates LineString geometries connecting building → street
    3. Combines terminal lines with street network
    
    :param building_centroids: GeoDataFrame with building centroids and 'name' column
    :type building_centroids: gdf
    :param street_network: GeoDataFrame with street network LineStrings (already corrected)
    :type street_network: gdf
    :param crs: Coordinate reference system
    :type crs: str
    :return: Combined network (street + building terminals)
    :rtype: gdf
    """
    # Find nearest point on street network for each building centroid
    near_points = near_analysis(building_centroids, street_network, crs)
    
    # Create terminal lines using vectorized LineString construction
    # Each line connects: nearest_street_point → building_centroid
    lines_to_buildings = gdf(
        geometry=[
            LineString([street_pt.coords[0], bldg_pt.coords[0]])
            for street_pt, bldg_pt in zip(near_points.geometry, building_centroids.geometry)
        ],
        crs=crs
    )
    
    # Combine building terminals with street network
    combined_network = gdf(pd.concat([lines_to_buildings, street_network], ignore_index=True), crs=crs)
    
    return combined_network


def apply_graph_corrections(network_gdf: gdf, protected_nodes: list | None = None) -> gdf:
    """
    Apply graph corrections to a network to fix connectivity issues.

    This function converts a GeoDataFrame to a NetworkX graph, applies corrections
    using GraphCorrector (merging close nodes, connecting intersecting edges,
    connecting disconnected components), then converts back to GeoDataFrame.

    Protected nodes (e.g., building centroids) will not be merged or moved during
    corrections, ensuring their exact coordinates are preserved.

    Note: Edge weights are not preserved during correction as they will be
    recalculated from geometry later in the pipeline (Shape_Leng field).

    :param network_gdf: GeoDataFrame with network LineStrings (streets or streets + terminals)
    :type network_gdf: gdf
    :param protected_nodes: Optional list of node coordinates to protect from merging
    :type protected_nodes: list, optional
    :return: Corrected network as GeoDataFrame
    :rtype: gdf
    """
    coord_precision = SHAPEFILE_TOLERANCE

    # Convert GeoDataFrame to NetworkX graph using consolidated helper
    G = gdf_to_nx(network_gdf, coord_precision=coord_precision)

    # Apply graph corrections with optional protected nodes
    corrector = GraphCorrector(G, coord_precision=coord_precision, protected_nodes=protected_nodes)
    G_corrected = corrector.apply_corrections()

    # Validate connectivity
    if not nx.is_connected(G_corrected):
        num_components = nx.number_connected_components(G_corrected)
        if protected_nodes:
            raise ValueError(f"Network still has {num_components} disconnected components after corrections. "
                           f"This indicates a serious connectivity issue that could not be automatically resolved.")
        else:
            warnings.warn(f"Network still has {num_components} disconnected components after corrections. "
                        f"This may cause issues with Steiner tree optimization.")

    # Convert corrected graph back to GeoDataFrame (straight lines)
    corrected_lines = []
    for u, v in G_corrected.edges():
        line = LineString([u, v])
        corrected_lines.append(line)

    corrected_gdf = gdf(geometry=corrected_lines, crs=network_gdf.crs)
    return corrected_gdf


def _prepare_network_inputs(streets_network_df: gdf, building_centroids_df: gdf) -> tuple[gdf, gdf, str]:
    """
    Preprocessing for connectivity network functions.

    This function:
    1. Converts to projected CRS for accurate distance calculations
    2. Validates geometries
    3. Cleans street network (splits at intersections, snaps near-miss endpoints)

    :return: Tuple of (streets_gdf, buildings_gdf, crs)
    """
    # Convert both streets and buildings to projected CRS for accurate distance calculations
    lat, lon = get_lat_lon_projected_shapefile(building_centroids_df)
    crs = get_projected_coordinate_system(lat, lon)
    streets_network_df = streets_network_df.to_crs(crs)
    building_centroids_df = building_centroids_df.to_crs(crs)

    # Validate geometries
    valid_geometries = streets_network_df.geometry.is_valid
    if not valid_geometries.any():
        raise ValueError("No valid geometries found in the shapefile.")
    elif len(streets_network_df) != valid_geometries.sum():
        warnings.warn("Invalid geometries found in the shapefile. Discarding all invalid geometries.")
        streets_network_df = streets_network_df[streets_network_df.geometry.is_valid]

    # Clean street network: split at intersections and snap near-miss endpoints
    print("Cleaning street network...")
    streets_network_df = clean_street_network(streets_network_df, SNAP_TOLERANCE)

    return streets_network_df, building_centroids_df, crs


def _get_protected_building_coords(building_centroids_df: gdf) -> list:
    """Get rounded building centroid coordinates for use as protected nodes."""
    return [
        (round(pt.coords[0][0], SHAPEFILE_TOLERANCE), round(pt.coords[0][1], SHAPEFILE_TOLERANCE))
        for pt in building_centroids_df.geometry
    ]


def calc_connectivity_network(streets_network_df: gdf, building_centroids_df: gdf) -> gdf:
    """
    Create a graph of potential thermal network connections by connecting building centroids to the nearest street
    network.

    This function prepares a network suitable for Steiner tree optimization by:
    1. Loading and validating the street network
    2. Applying graph corrections to streets only (connect components, fix intersections, merge close nodes)
    3. Creating building terminal connection lines (building → nearest street point)
    4. Topologically merging and connecting all geometries (merge lines, snap endpoints, split at junctions)
    5. Discretizing the network into graph-ready segments

    The street network is assumed to be a good path for district heating or cooling networks.

    Pipeline:
    ---------
    Streets → Graph Corrections → Add Building Lines → Merge/Snap Geometries → Discretize → Output

    :param streets_network_df: GeoDataFrame with street network geometries
    :type streets_network_df: gdf
    :param building_centroids_df: GeoDataFrame with building centroids (must have 'name' column)
    :type building_centroids_df: gdf
    :return: Potential connectivity network as GeoDataFrame in projected CRS
    :rtype: gdf
    """
    # Prepare inputs (CRS conversion and validation)
    streets_network_df, building_centroids_df, crs = _prepare_network_inputs(
        streets_network_df, building_centroids_df
    )

    # PASS 1: Apply graph corrections to street network first (without terminals)
    print("\nApplying graph corrections to street network (before connecting buildings)...")
    street_network = apply_graph_corrections(streets_network_df)

    # Create terminals from corrected street network to buildings
    prototype_network = create_terminals(building_centroids_df, street_network, crs)

    # PASS 2: Apply graph corrections to the combined network (streets + terminals)
    print("\nApplying graph corrections to combined network (streets + building terminals)...")
    building_centroid_coords = _get_protected_building_coords(building_centroids_df)
    prototype_network = apply_graph_corrections(
        prototype_network, protected_nodes=building_centroid_coords
    )

    # Calculate all significant points (line endpoints) for discretization
    # Terminal connection points are included as endpoints of terminal lines
    gdf_points = calculate_significant_points(prototype_network, crs)

    # Final discretization: split the combined network at all significant points
    # This snaps points to lines and splits lines at those points in one operation
    # Creates proper graph structure where each junction/endpoint is explicit
    potential_network_df = split_network_at_points(prototype_network, gdf_points, SNAP_TOLERANCE, crs)

    return potential_network_df


def calc_connectivity_network_with_geometry(
    streets_network_df: gdf,
    building_centroids_df: gdf,
) -> tuple[gdf, GeometryPreservingGraph]:
    """
    Create connectivity network preserving curved street geometries.

    This function creates a graph-based network while preserving the original
    curved geometries of streets. It adds junctions where buildings connect
    to streets, maintaining aesthetic quality of the network.

    Pipeline:
    ---------
    1. Apply graph corrections to street network (fix topology issues)
    2. Restore curved geometries (with endpoint snapping for connectivity)
    3. Build GeometryPreservingGraph from corrected curved streets
    4. Add building terminal junctions (splits edges, maintains connectivity)
    5. Export and discretize network for Steiner tree optimization

    Key Feature:
    ------------
    Geometry restoration snaps endpoints to rounded coordinates, ensuring that
    the round-trip conversion (Graph → GeoDataFrame → Graph) maintains full
    connectivity without needing additional correction passes.

    :param streets_network_df: GeoDataFrame with street network geometries
    :type streets_network_df: gdf
    :param building_centroids_df: GeoDataFrame with building centroids (must have 'name' column)
    :type building_centroids_df: gdf
    :return: Tuple of (potential_network_gdf, geometry_graph)
    :rtype: tuple[gdf, GeometryPreservingGraph]
    """
    # Prepare inputs (CRS conversion and validation)
    streets_network_df, building_centroids_df, crs = _prepare_network_inputs(
        streets_network_df, building_centroids_df
    )

    # Apply graph corrections to street network and restore curved geometries
    # Endpoints are snapped to rounded coordinates to ensure connectivity is preserved
    print("\nApplying graph corrections to street network...")
    geometry_map = GeometryPreservingGraph.build_geometry_map(streets_network_df, SHAPEFILE_TOLERANCE)
    street_network = apply_graph_corrections(streets_network_df)
    street_network = GeometryPreservingGraph.restore_geometries(street_network, geometry_map, SHAPEFILE_TOLERANCE)

    street_network.to_file("corrected_streets.shp")

    # Build geometry-preserving graph from corrected streets
    print("\nBuilding geometry-preserving graph...")
    gp_graph = GeometryPreservingGraph(street_network, coord_precision=SHAPEFILE_TOLERANCE)

    # Add building terminals by creating junctions on nearest edges
    print("\nAdding building terminal junctions...")
    building_nodes = []
    for idx, building in building_centroids_df.iterrows():
        building_point: Point = building.geometry

        # Find nearest edge in the geometry graph
        nearest_edge, nearest_point_on_edge, _ = gp_graph.find_nearest_edge(building_point)

        if nearest_edge is None or nearest_point_on_edge is None:
            warnings.warn(f"Could not find nearest edge for building {building.get('name', idx)}")
            continue

        # Add junction on the nearest edge
        point_coords = (nearest_point_on_edge.coords[0][0], nearest_point_on_edge.coords[0][-1]) # linting fix, ensure 2 coords
        junction_node = gp_graph.add_junction(nearest_edge, point_coords)

        # Add edge from junction to building
        building_coords = (building_point.coords[0][0], building_point.coords[0][-1])  # linting fix, ensure 2 coords
        building_node = gp_graph._round_coords(building_coords)
        terminal_line = LineString([junction_node, building_node])
        gp_graph.G.add_edge(
            junction_node,
            building_node,
            weight=terminal_line.length,
            geometry=terminal_line,
            original_id=None,
            edge_id=gp_graph._edge_id_counter
        )
        gp_graph._edge_id_counter += 1
        building_nodes.append(building_node)

    # Export final network for discretization
    # No need for PASS 2 corrections since:
    # - Junction additions maintain connectivity (split edges but don't disconnect)
    # - Terminal additions maintain connectivity (add connected edges)
    # - Geometry restoration now snaps endpoints to rounded coordinates, preserving connectivity
    combined_gdf = gp_graph.to_geodataframe(crs)
    # gdf_points = calculate_significant_points(combined_gdf, crs)
    # potential_network_df = split_network_at_points(combined_gdf, gdf_points, SNAP_TOLERANCE, crs)

    return combined_gdf, gp_graph
