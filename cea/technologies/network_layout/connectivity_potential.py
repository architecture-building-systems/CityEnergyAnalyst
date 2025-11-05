"""
Network connectivity module for connecting buildings to street networks.

This module creates a graph of potential thermal network paths by connecting building centroids to the nearest
points on a street network, preparing the data for Steiner tree optimization.

WORKFLOW (Two-Pass Correction):
================================
1. Load and validate street network
2. **PASS 1**: Apply graph corrections to street network
   - Fixes base network topology: self-loops, close nodes, intersecting edges, disconnected components
   - Ensures clean street network before adding building connections
3. Create building terminal connection lines (geometries from building → nearest corrected street point)
4. **PASS 2**: Apply graph corrections to combined network (streets + terminals)
   - Fixes any disconnections introduced when connecting building terminals
   - Building centroids marked as protected nodes (stay at exact locations)
   - Connects remaining isolated components (e.g., buildings connecting to isolated street segments)
5. Extract all significant points (line endpoints, including terminal connection points)
6. Discretize network: split lines at all significant points in one efficient operation
7. Output fully connected network for Steiner tree optimization

RATIONALE FOR TWO-PASS APPROACH:
=================================
**Why not single pass?** Adding terminals to an uncorrected street network can create many disconnected
components (one per isolated street segment that buildings connect to). The GraphCorrector then has to
connect all these components, often creating suboptimal shortcuts that don't follow the street topology.

**Why two passes?** Correcting the street network first:
- Reduces number of disconnected components after terminal connection (fewer problems to fix)
- Ensures component connections follow street topology (better network quality)
- Less work in second pass (only fix terminal-induced disconnections)
- More robust to street network data quality issues

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
- split_line_by_nearest_points: Discretizes network by snapping and splitting in one operation

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


def split_line_by_nearest_points(gdf_line: gdf, gdf_points: gdf, snap_tolerance: float, crs: str):
    """
    Discretize network by splitting lines at all significant points (junctions, endpoints, intersections).
    This converts continuous LineStrings into graph-ready segments where each topologically
    significant point becomes an explicit node in the network structure.

    :param gdf_line: GeoDataFrame with network line segments (streets + building connections)
    :type gdf_line: gdf
    :param gdf_points: GeoDataFrame with all significant points (endpoints, intersections)
    :type gdf_points: gdf
    :param snap_tolerance: Distance tolerance for snapping points to lines (meters)
    :type snap_tolerance: float
    :param crs: Coordinate reference system
    :type crs: str
    :return: Discretized network as individual segments
    :rtype: gdf

    Reference: https://github.com/ojdo/python-tools/blob/master/shapelytools.py#L144
    """
    # Union all geometries into single objects for splitting operation
    line = gdf_line.geometry.union_all()
    snap_points = gdf_points.geometry.union_all()

    # Snap points to lines within tolerance, then split lines at those points
    # This ensures all significant points become explicit vertices in the network
    split_line = split(line, snap(snap_points, line, snap_tolerance))

    # Filter out numerical artifacts (extremely short segments from floating-point precision)
    # Use threshold based on coordinate precision: 10^-6 meters (1 micrometer) with SHAPEFILE_TOLERANCE=6
    min_length = 10 ** (-SHAPEFILE_TOLERANCE)
    segments = [feature for feature in split_line.geoms if feature.length > min_length]

    gdf_segments = gdf(geometry=segments, crs=crs)
    return gdf_segments


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
    as endpoints of terminal lines. The split_line_by_nearest_points function will handle
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

    # Convert GeoDataFrame to NetworkX graph
    G = nx.Graph()
    for _, row in network_gdf.iterrows():
        line = row.geometry
        # Handle both LineString and MultiLineString geometries
        if line.geom_type == 'LineString':
            coords = list(line.coords)
            start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
            end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
            weight = line.length
            G.add_edge(start, end, weight=weight)
        elif line.geom_type == 'MultiLineString':
            # Handle MultiLineString by adding each component line
            for sub_line in line.geoms:
                coords = list(sub_line.coords)
                start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
                end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
                weight = sub_line.length
                G.add_edge(start, end, weight=weight)

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

    # Convert corrected graph back to GeoDataFrame
    corrected_lines = []
    for u, v in G_corrected.edges():
        line = LineString([u, v])
        corrected_lines.append(line)

    corrected_gdf = gdf(geometry=corrected_lines, crs=network_gdf.crs)
    return corrected_gdf


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

    # convert both streets and buildings to projected CRS for accurate distance calculations
    lat, lon = get_lat_lon_projected_shapefile(building_centroids_df)
    crs = get_projected_coordinate_system(lat, lon)
    streets_network_df = streets_network_df.to_crs(crs)
    building_centroids_df = building_centroids_df.to_crs(crs)

    valid_geometries = streets_network_df.geometry.is_valid

    if not valid_geometries.any():
        raise ValueError("No valid geometries found in the shapefile.")
    elif len(streets_network_df) != valid_geometries.sum():
        warnings.warn("Invalid geometries found in the shapefile. Discarding all invalid geometries.")
        streets_network_df = streets_network_df[streets_network_df.geometry.is_valid]

    # PASS 1: Apply graph corrections to street network first (without terminals)
    # This fixes the base network topology before adding building connections
    # Benefits: fewer components to connect, better edge placement following streets
    print("\nApplying graph corrections to street network (before connecting buildings)...")
    street_network = apply_graph_corrections(streets_network_df)

    # Create terminals/branches from corrected street network to buildings
    # This creates individual line segments from each building centroid to nearest street point
    prototype_network = create_terminals(building_centroids_df, street_network, crs)

    # PASS 2: Apply graph corrections to the combined network (streets + terminals)
    # This fixes any disconnections introduced when connecting building terminals
    # Building centroids are marked as protected nodes to preserve their exact locations
    building_centroid_coords = [
        (round(pt.coords[0][0], SHAPEFILE_TOLERANCE), round(pt.coords[0][1], SHAPEFILE_TOLERANCE))
        for pt in building_centroids_df.geometry
    ]
    print("\nApplying graph corrections to combined network (streets + building terminals)...")
    prototype_network = apply_graph_corrections(
        prototype_network, protected_nodes=building_centroid_coords
    )

    # Calculate all significant points (line endpoints) for discretization
    # Terminal connection points are included as endpoints of terminal lines
    gdf_points = calculate_significant_points(prototype_network, crs)

    # Final discretization: split the combined network at all significant points
    # This snaps points to lines and splits lines at those points in one operation
    # Creates proper graph structure where each junction/endpoint is explicit
    potential_network_df = split_line_by_nearest_points(prototype_network, gdf_points, SNAP_TOLERANCE, crs)

    # calculate Shape_len field
    potential_network_df["Shape_Leng"] = potential_network_df.geometry.length

    return potential_network_df