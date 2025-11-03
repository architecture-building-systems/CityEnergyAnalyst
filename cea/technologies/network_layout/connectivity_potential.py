"""
Network connectivity module for connecting buildings to street networks.

This module creates a graph of potential thermal network paths by connecting building centroids to the nearest
points on a street network, preparing the data for Steiner tree optimization.

WORKFLOW:
=========
1. Load and validate street network
2. Apply GraphCorrector to street network (fixes connectivity, intersections, merges close nodes)
3. Create building terminal connection lines (geometries from building → nearest street point)
4. Topologically merge and connect geometries:
   - one_linestring_per_intersection: Merge touching lines, split at intersections
   - snappy_endings: Snap isolated endpoints to nearby vertices
   - snap_points: Split lines at significant points
5. Discretize network for graph representation
6. Output for Steiner tree optimization

ARCHITECTURE:
=============
- GraphCorrector (graph_helper.py): Topology fixes on street network only
- create_terminals: Spatial operation to find nearest street points for buildings
- Geometric merging/snapping: Ensures building connections are topologically integrated
- Discretization: Converts continuous geometries into graph-ready segments

This separation ensures:
- Street network is corrected BEFORE building terminals are added
- Terminal nodes are protected from graph correction operations
- Building connections are properly merged with street network geometries
- Final network is suitable for NetworkX graph conversion
"""

import os
import warnings

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString, MultiPoint, box
from shapely.ops import split, linemerge, snap

import cea.config
import cea.inputlocator
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


def compute_intersections(lines, crs):
    import itertools
    inters = []
    for line1, line2 in itertools.combinations(lines, 2):
        if line1.intersects(line2):
            inter = line1.intersection(line2)
            if "Point" == inter.geom_type:
                inters.append(inter)
            elif "MultiPoint" == inter.geom_type:
                inters.extend([pt for pt in inter.geoms])
            elif "MultiLineString" == inter.geom_type:
                multiLine = [line for line in inter]
                first_coords = multiLine[0].coords[0]
                last_coords = multiLine[len(multiLine) - 1].coords[1]
                inters.append(Point(first_coords[0], first_coords[1]))
                inters.append(Point(last_coords[0], last_coords[1]))
            elif "GeometryCollection" == inter.geom_type:
                for geom in inter:
                    if "Point" == geom.geom_type:
                        inters.append(geom)
                    elif "MultiPoint" == geom.geom_type:
                        inters.extend([pt for pt in geom.geoms])
                    elif "MultiLineString" == geom.geom_type:
                        multiLine = [line for line in geom.geoms]
                        first_coords = multiLine[0].coords[0]
                        last_coords = multiLine[len(multiLine) - 1].coords[1]
                        inters.append(Point(first_coords[0], first_coords[1]))
                        inters.append(Point(last_coords[0], last_coords[1]))

    geometry = inters
    df = gdf(geometry=geometry, crs=crs)
    return df


def computer_end_points(lines, crs):
    all_points = []
    for line in lines:
        for i in [0, -1]:  # start and end point
            all_points.append(line.coords[i])

    unique_points = set(all_points)
    endpts = [Point(p) for p in unique_points]
    df = gdf(geometry=endpts, crs=crs)

    return df


def nearest_neighbor_within(others, point, max_distance):
    """Find nearest point among others up to a maximum distance.

    Args:
        others: a list of Points or a MultiPoint
        point: a Point
        max_distance: maximum distance to search for the nearest neighbor

    Returns:
        A shapely Point if one is within max_distance, None otherwise
    """
    search_region = point.buffer(max_distance)
    interesting_points = search_region.intersection(MultiPoint(others))

    if not interesting_points:
        closest_point = None
    elif isinstance(interesting_points, Point):
        closest_point = interesting_points
    else:
        distances = [point.distance(ip) for ip in interesting_points.geoms
                     if point.distance(ip) > 0]
        closest_point = interesting_points.geoms[distances.index(min(distances))]

    return closest_point


def find_isolated_endpoints(lines):
    """Find endpoints of lines that don't touch another line.

    Args:
        lines: a list of LineStrings or a MultiLineString

    Returns:
        A list of line end Points that don't touch any other line of lines
    """

    isolated_endpoints = []
    for i, line in enumerate(lines):
        other_lines = lines[:i] + lines[i + 1:]
        for q in [0, -1]:
            endpoint = Point(line.coords[q])
            if any(endpoint.touches(another_line)
                   for another_line in other_lines):
                continue
            else:
                isolated_endpoints.append(endpoint)
    return isolated_endpoints


def bend_towards(line, where, to):
    """Move the point where along a line to the point at location to.

    Args:
        line: a LineString
        where: a point ON the line (not necessarily a vertex)
        to: a point NOT on the line where the nearest vertex will be moved to

    Returns:
        the modified (bent) line
    """

    if not line.contains(where) and not line.touches(where):
        raise ValueError('line does not contain the point where.')

    coords = line.coords[:]
    # easy case: where is (within numeric precision) a vertex of line
    for k, vertex in enumerate(coords):
        if where.equals_exact(Point(vertex), tolerance=1e-6):
            # move coordinates of the vertex to destination
            coords[k] = to.coords[0]
            return LineString(coords)

    # hard case: where lies between vertices of line, so
    # find nearest vertex and move that one to point to
    _, min_k = min((where.distance(Point(vertex)), k)
                   for k, vertex in enumerate(coords))
    coords[min_k] = to.coords[0]
    return LineString(coords)


def vertices_from_lines(lines):
    """Return list of unique vertices from list of LineStrings."""

    vertices = []
    for line in lines:
        vertices.extend(list(line.coords))
    return [Point(p) for p in set(vertices)]


def snappy_endings(lines, max_distance, crs):
    """Snap endpoints of lines together if they are at most max_length apart.

    Args:
        lines: a list of LineStrings or a MultiLineString
        max_distance: maximum distance two endpoints may be joined together
    """

    # initialize snapped lines with list of original lines
    # snapping points is a MultiPoint object of all vertices
    snapped_lines = [line for line in lines]
    snapping_points = vertices_from_lines(snapped_lines)

    # isolated endpoints are going to snap to the closest vertex
    isolated_endpoints = find_isolated_endpoints(snapped_lines)

    # only move isolated endpoints, one by one
    for endpoint in isolated_endpoints:
        # find all vertices within a radius of max_distance as possible
        target = nearest_neighbor_within(snapping_points, endpoint,
                                         max_distance)

        # do nothing if no target point to snap to is found
        if not target:
            continue

            # find the LineString to modify within snapped_lines and update it
        for i, snapped_line in enumerate(snapped_lines):
            if endpoint.touches(snapped_line):
                snapped_lines[i] = bend_towards(snapped_line, where=endpoint,
                                                to=target)
                break

        # also update the corresponding snapping_points
        for i, snapping_point in enumerate(snapping_points):
            if endpoint.equals(snapping_point):
                snapping_points[i] = target
                break

    # post-processing: remove any resulting lines of length 0
    snapped_lines = [s for s in snapped_lines if s.length > 0]

    df = gdf(geometry=snapped_lines, crs=crs)
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


def snap_points(points, lines, tolerance):
    length = lines.shape[0]
    for i in range(length):
        for point in points.geometry:
            line = lines.loc[i, "geometry"]
            point_inline_projection = line.interpolate(line.project(point))
            distance_to_line = point.distance(point_inline_projection)
            if (point.x, point.y) not in line.coords:
                if distance_to_line < tolerance:
                    buff = point.buffer(0.1)
                    ### Split the line on the buffer
                    geometry = split(line, buff)
                    line_1_points = [tuple(xy) for xy in geometry.geoms[0].coords[:-1]]
                    line_1_points.append((point.x, point.y))
                    line_2_points = []
                    line_2_points.append((point.x, point.y))
                    line_2_points.extend([x for x in geometry.geoms[-1].coords[1:]])
                    ### Stitch together the first segment, the interpolated point, and the last segment
                    new_line = linemerge((LineString(line_1_points), LineString(line_2_points)))
                    lines.loc[i, "geometry"] = new_line

    G = points["geometry"].apply(lambda geom: geom.wkb)
    points = points.loc[G.drop_duplicates().index]

    G = lines["geometry"].apply(lambda geom: geom.wkb)
    lines = lines.loc[G.drop_duplicates().index]

    return points, lines


def one_linestring_per_intersection(lines, crs):
    """ Move line endpoints to intersections of line segments.

    Given a list of touching or possibly intersecting LineStrings, return a
    list LineStrings that have their endpoints at all crossings and
    intersecting points and ONLY there.

    Args:
        a list of LineStrings or a MultiLineString

    Returns:
        a list of LineStrings
    """
    lines_merged = linemerge(lines)

    # intersecting multiline with its bounding box somehow triggers a first intersection
    try:
        bounding_box = box(*lines_merged.bounds)
        lines_merged = lines_merged.intersection(bounding_box)
    except Exception:
        # if the bounding_box fails, then revert to lines merge.
        print('bounding box method did not work, falling to a more simple method, no need to worry')

    # merge the result
    lines_merged = linemerge(lines_merged)

    lines = [line for line in lines_merged.geoms]
    df = gdf(geometry=lines, crs=crs)
    return df


def calculate_end_points_intersections(prototype_network, crs):
    # compute endpoints of the new prototype network
    gdf_points = computer_end_points(prototype_network.geometry, crs)
    # compute intersections
    gdf_intersections = compute_intersections(prototype_network.geometry, crs)
    gdf_points_snapped = pd.concat([gdf_points, gdf_intersections], ignore_index=True)
    G = gdf_points_snapped["geometry"].apply(lambda geom: geom.wkb)
    gdf_points_snapped = gdf_points_snapped.loc[G.drop_duplicates().index]
    return gdf_points_snapped


def create_terminals(building_centroids, crs, street_network):
    # get list of nearest points
    near_points = near_analysis(building_centroids, street_network, crs)
    # extend to the building centroids
    all_points = pd.concat([near_points.to_crs(crs), building_centroids.to_crs(crs)])
    all_points.crs = crs
    # Aggregate these points with the GroupBy
    lines_to_buildings = all_points.groupby(['name'])['geometry'].apply(lambda x: LineString(x.tolist()))
    lines_to_buildings = gdf(lines_to_buildings, geometry='geometry', crs=crs)

    lines_to_buildings = pd.concat([lines_to_buildings, street_network]).reset_index(drop=True)
    lines_to_buildings.crs = crs
    return lines_to_buildings


def simplify_liness_accurracy(lines, decimals, crs):
    new_lines = []
    for line in lines:
        points_of_line = []
        for point in line.coords:
            x = round(point[0], decimals)
            y = round(point[1], decimals)
            points_of_line.append((x, y))
        new_lines.append(LineString(points_of_line))
    df = gdf(geometry=new_lines, crs=crs)
    return df


def apply_graph_corrections_to_street_network(street_network_gdf, crs):
    """
    Apply graph corrections to the street network to fix connectivity issues.

    This function converts the street network GeoDataFrame to a NetworkX graph,
    applies corrections using GraphCorrector, then converts back to GeoDataFrame.
    This should be done BEFORE connecting building terminals to ensure terminal
    nodes are not affected by corrections.

    Note: Edge weights are not preserved during correction as they will be
    recalculated from geometry later in the pipeline (Shape_Leng field).

    :param street_network_gdf: GeoDataFrame with street network LineStrings
    :type street_network_gdf: gdf
    :param crs: Coordinate reference system
    :type crs: str
    :return: Corrected street network as GeoDataFrame
    :rtype: gdf
    """
    # Convert GeoDataFrame to NetworkX graph
    G = nx.Graph()
    for idx, row in street_network_gdf.iterrows():
        line = row.geometry
        # Handle both LineString and MultiLineString geometries
        if line.geom_type == 'LineString':
            coords = list(line.coords)
            start = (round(coords[0][0], SHAPEFILE_TOLERANCE), round(coords[0][1], SHAPEFILE_TOLERANCE))
            end = (round(coords[-1][0], SHAPEFILE_TOLERANCE), round(coords[-1][1], SHAPEFILE_TOLERANCE))
            weight = line.length
            G.add_edge(start, end, weight=weight)
        elif line.geom_type == 'MultiLineString':
            # Handle MultiLineString by adding each component line
            for sub_line in line.geoms:
                coords = list(sub_line.coords)
                start = (round(coords[0][0], SHAPEFILE_TOLERANCE), round(coords[0][1], SHAPEFILE_TOLERANCE))
                end = (round(coords[-1][0], SHAPEFILE_TOLERANCE), round(coords[-1][1], SHAPEFILE_TOLERANCE))
                weight = sub_line.length
                G.add_edge(start, end, weight=weight)

    # Apply graph corrections
    print("\nApplying graph corrections to street network (before connecting buildings)...")
    corrector = GraphCorrector(G, coord_precision=SHAPEFILE_TOLERANCE)
    G_corrected = corrector.apply_corrections()

    # Validate that the corrected graph is connected
    if not nx.is_connected(G_corrected):
        num_components = nx.number_connected_components(G_corrected)
        warnings.warn(f"Street network still has {num_components} disconnected components after corrections. "
                     f"This may cause issues with Steiner tree optimization.")

    # Convert corrected graph back to GeoDataFrame
    # Weights will be recalculated from geometry later in the pipeline
    corrected_lines = []
    for u, v, data in G_corrected.edges(data=True):
        line = LineString([u, v])
        corrected_lines.append(line)

    corrected_gdf = gdf(geometry=corrected_lines, crs=crs)
    return corrected_gdf


def calc_connectivity_network(path_streets_shp, building_centroids_df, optimisation_flag=False, path_potential_network=None):
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

    :param path_streets_shp: Path to street network shapefile
    :type path_streets_shp: str
    :param building_centroids_df: GeoDataFrame with building centroids (must have 'name' column)
    :type building_centroids_df: gdf
    :param optimisation_flag: If True, return GeoDataFrame; if False, write to file
    :type optimisation_flag: bool
    :param path_potential_network: Output path for potential network shapefile (required if optimisation_flag=False)
    :type path_potential_network: str
    :return: CRS if optimisation_flag=False, else potential network GeoDataFrame
    :rtype: str or gdf
    """
    # first get the street network
    street_network = gdf.from_file(path_streets_shp)

    # check coordinate system
    lat, lon = get_lat_lon_projected_shapefile(street_network)
    street_network = street_network.to_crs(get_projected_coordinate_system(lat, lon))
    crs = street_network.crs

    valid_geometries = street_network[street_network.geometry.is_valid].geometry

    if valid_geometries.empty:
        raise ValueError("No valid geometries found in the shapefile.")
    elif len(street_network) != len(valid_geometries):
        warnings.warn("Invalid geometries found in the shapefile. Discarding all invalid geometries.")

    street_network = simplify_liness_accurracy(valid_geometries, SHAPEFILE_TOLERANCE, crs)

    # Apply graph corrections to street network BEFORE connecting buildings
    # This ensures terminal nodes are not affected by corrections
    # GraphCorrector already handles: intersections, close nodes, disconnected components
    street_network = apply_graph_corrections_to_street_network(street_network, crs)

    # create terminals/branches form street to buildings
    # This creates individual line segments from each building centroid to nearest street point
    prototype_network = create_terminals(building_centroids_df, crs, street_network)
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # Merge touching lines and split at intersections
    # This ensures building connections are topologically merged with the street network
    prototype_network = one_linestring_per_intersection(prototype_network.geometry.tolist(), crs)

    # Snap isolated endpoints to nearby vertices
    # This ensures all connections are properly joined within tolerance
    prototype_network = snappy_endings(prototype_network.geometry.values, SNAP_TOLERANCE, crs)

    # Calculate all significant points (endpoints and intersections) for final discretization
    gdf_points_snapped = calculate_end_points_intersections(prototype_network, crs)

    # Snap points to lines and split lines at those points
    # This ensures all junction points become explicit vertices
    gdf_points_snapped, prototype_network = snap_points(gdf_points_snapped, prototype_network, SNAP_TOLERANCE)

    # save for verification purposes
    prototype_network.to_file(locator.get_temporary_file("prototype_network.shp"), driver='ESRI Shapefile')

    # Final discretization: split the combined network at all significant points
    # This creates proper graph structure where each junction/endpoint is explicit
    potential_network_df = split_line_by_nearest_points(prototype_network, gdf_points_snapped, SNAP_TOLERANCE, crs)

    # calculate Shape_len field
    potential_network_df["Shape_Leng"] = potential_network_df["geometry"].apply(lambda x: x.length)

    if optimisation_flag is True:
        return potential_network_df
    else:
        potential_network_df.to_file(path_potential_network, driver='ESRI Shapefile')
        return crs
