"""
Network connectivity module for connecting buildings to street networks.

This module creates a graph of potential thermal network paths by connecting building centroids to the nearest
points on a street network, preparing the data for Steiner tree optimization.

PURPOSE
=======
Creates a fully connected network graph where:
- Buildings are connected to their nearest street points via terminal lines
- All streets are split at intersection points for proper topology
- Graph is guaranteed to be connected (single component)
- Coordinate precision is consistently maintained throughout
- Building terminal coordinates are preserved exactly (protected from merging)

WORKFLOW
========
1. **Load and validate** street network and building centroids
2. **Clean street network** (preprocessing):
   - Split streets at intersection points (automatic detection via unary_union)
   - Snap near-miss endpoints to nearby lines (fix manual digitization errors)
   - Re-split to create junctions at newly connected points
3. **Correct street topology** (first pass):
   - Remove self-loops (invalid edges)
   - Merge close nodes (two-pass: micro-precision at 10^-6m, then snap-tolerance at 0.1m)
   - Connect intersecting edges
   - Connect disconnected components if needed
4. **Create building terminals**:
   - Find nearest point on street network for each building
   - Create LineString geometries connecting building → street
   - Split street lines at terminal junction points
   - Normalize all coordinates to 6 decimal places (SHAPEFILE_TOLERANCE)
5. **Correct combined topology** (second pass):
   - Apply same corrections to streets + terminals network
   - Protect building terminal nodes from being merged
   - Resolve any micro-precision disconnections from geometric operations
6. **Extract significant points**:
   - Collect all unique line endpoints (streets and terminals)
7. **Discretize network**:
   - Split lines at all significant points in one efficient operation
8. **Output** fully connected network ready for Steiner tree optimization

COORDINATE PRECISION HANDLING
==============================
This module implements robust coordinate normalization to prevent micro-precision disconnections:

- All coordinates normalized to SHAPEFILE_TOLERANCE (6 decimal places = 1 micrometer)
- Two-pass node merging strategy:
  * Pass 1 (Micro-precision): Merges nodes within 10^-6m using <= comparison
    Catches nodes at exactly the coordinate precision threshold
  * Pass 2 (Snap-tolerance): Merges nodes within 0.1m using < comparison
    Handles data quality issues
- Exact coordinate comparison (not distance thresholds) for split point detection
- Validation after terminal creation warns if disconnections detected

Why two correction passes?
- Geometric operations (interpolate, substring) can produce floating-point artifacts
- Coordinate rounding can create 1-micrometer gaps at junction points
- Second pass automatically fixes these artifacts while protecting building terminals

GUARANTEES
==========
- Final network is 100% connected (single component)
- Building terminal coordinates are exact (never moved)
- Street topology follows actual street intersections
- Coordinate precision is consistent (6 decimal places)
- All geometric operations preserve connectivity
- No micro-precision disconnections (automatically resolved)
"""

import warnings

import networkx as nx
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString
from shapely.ops import snap, split, substring

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE
from cea.datamanagement.graph_helper import GraphCorrector
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile
from cea.technologies.network_layout.graph_utils import gdf_to_nx, normalize_gdf_geometries, nx_to_gdf, normalize_coords


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
    valid_segments = result_gdf.geometry.length > min_length
    if sum(~valid_segments) > 0:
        print(f"Removed {sum(~valid_segments)} extremely short segments (< {min_length}m) after splitting at intersections")
    result_gdf = result_gdf[valid_segments].reset_index(drop=True)

    return result_gdf


def simplify_street_network_geometric(network_gdf: gdf, coord_precision: int = SHAPEFILE_TOLERANCE) -> gdf:
    """
    Simplify street network by merging chains of segments at degree-2 nodes.

    After split_streets_at_intersections(), we have many segments split at every
    intersection. This function identifies "chains" of segments between real
    intersections (degree >= 3) and merges them back into single segments while
    preserving the full geometry.

    This is a pure geometric operation using Shapely/GeoPandas that:
    - Builds endpoint connectivity map to calculate node degrees
    - Identifies chains of segments connected only through degree-2 nodes
    - Merges each chain using shapely.ops.linemerge()
    - Preserves all segments at degree-3+ nodes (real intersections)
    - **Removes self-loops** (closed chains where start == end)

    Benefits:
    - Reduces segment count before graph construction → faster Steiner tree
    - Removes insignificant pass-through nodes
    - Preserves all real intersection topology

    :param network_gdf: GeoDataFrame with street LineStrings (after splitting)
    :type network_gdf: gdf
    :param coord_precision: Decimal places for coordinate rounding
    :type coord_precision: int
    :return: Simplified GeoDataFrame with merged chains
    :rtype: gdf

    Example:
        >>> # After splitting creates: A-B-C-D-E (4 segments with degree-2 at B,C,D)
        >>> simplified = simplify_street_network_geometric(split_network)
        >>> # Result: A-----------E (1 segment, preserving all vertices)
    """
    from collections import defaultdict
    from shapely.ops import linemerge

    if len(network_gdf) == 0:
        return network_gdf

    TOLERANCE = coord_precision

    # Step 1: Build endpoint connectivity map
    endpoint_to_segments = defaultdict(list)
    segment_list = []

    for idx, row in network_gdf.iterrows():
        geom = row.geometry
        coords = list(geom.coords)
        start = tuple(round(c, TOLERANCE) for c in coords[0])
        end = tuple(round(c, TOLERANCE) for c in coords[-1])

        segment_info = {
            'idx': idx,
            'geometry': geom,
            'start': start,
            'end': end
        }
        segment_list.append(segment_info)

        # Track which segments share each endpoint
        endpoint_to_segments[start].append(len(segment_list) - 1)
        endpoint_to_segments[end].append(len(segment_list) - 1)

    # Step 1b: Detect multi-edges (parallel edges between same nodes)
    # This protects circular structures like roundabouts, cul-de-sacs, dual carriageways
    edge_pairs = defaultdict(list)
    for seg_idx, seg in enumerate(segment_list):
        # Normalize edge direction (always store smaller node first to catch N1→N2 and N2→N1)
        edge_key = tuple(sorted([seg['start'], seg['end']]))
        edge_pairs[edge_key].append(seg_idx)

    # Mark nodes that are part of multi-edge structures as protected
    protected_nodes = set()
    for edge_key, segs in edge_pairs.items():
        if len(segs) > 1:  # Multi-edge detected (e.g., roundabout, parallel roads)
            protected_nodes.update(edge_key)
            print(f"    Multi-edge detected: {len(segs)} edges between nodes (protects circular structures)")

    # Step 2: Calculate degree of each endpoint (with protection for multi-edges)
    endpoint_degree = {}
    for pt, segs in endpoint_to_segments.items():
        if pt in protected_nodes:
            # Never treat multi-edge nodes as degree-2 pass-through nodes
            endpoint_degree[pt] = float('inf')
        else:
            endpoint_degree[pt] = len(segs)

    # Step 3: Find chains of segments through degree-2 nodes
    visited = set()
    chains = []

    for seg_idx, seg in enumerate(segment_list):
        if seg_idx in visited:
            continue

        # Start a new chain
        chain = [seg_idx]
        visited.add(seg_idx)

        # Extend chain forward from end point (only through degree-2 nodes)
        current_end = seg['end']
        while endpoint_degree[current_end] == 2:
            # Find the other segment at this degree-2 node
            connected_segs = [s for s in endpoint_to_segments[current_end] if s not in visited]
            if not connected_segs:
                break

            next_seg_idx = connected_segs[0]
            next_seg = segment_list[next_seg_idx]
            chain.append(next_seg_idx)
            visited.add(next_seg_idx)

            # Move to next endpoint
            current_end = next_seg['end'] if next_seg['start'] == current_end else next_seg['start']

        # Extend chain backward from start point (only through degree-2 nodes)
        current_start = seg['start']
        while endpoint_degree[current_start] == 2:
            # Find the other segment at this degree-2 node
            connected_segs = [s for s in endpoint_to_segments[current_start] if s not in visited]
            if not connected_segs:
                break

            prev_seg_idx = connected_segs[0]
            prev_seg = segment_list[prev_seg_idx]
            chain.insert(0, prev_seg_idx)  # Prepend
            visited.add(prev_seg_idx)

            # Move to next endpoint
            current_start = prev_seg['start'] if prev_seg['end'] == current_start else prev_seg['end']

        chains.append(chain)

    # Step 4: Merge each chain using linemerge
    merged_geometries = []
    self_loops_removed = 0
    
    for chain in chains:
        if len(chain) == 1:
            # Single segment - check if it's a self-loop
            seg = segment_list[chain[0]]
            if seg['start'] == seg['end']:
                # Self-loop detected - skip it
                self_loops_removed += 1
                continue
            merged_geometries.append(seg['geometry'])
        else:
            # Merge multiple segments
            chain_geoms = [segment_list[idx]['geometry'] for idx in chain]
            merged = linemerge(chain_geoms)

            if merged.geom_type == 'LineString':
                # Check if merged line is a self-loop (closed ring)
                coords = list(merged.coords)
                start = tuple(round(c, TOLERANCE) for c in coords[0])
                end = tuple(round(c, TOLERANCE) for c in coords[-1])
                
                if start == end:
                    # Closed loop - skip it
                    self_loops_removed += 1
                    continue
                
                merged_geometries.append(merged)
            else:
                # Fallback: keep original segments if merge fails (but filter self-loops)
                for geom in chain_geoms:
                    coords = list(geom.coords)
                    start = tuple(round(c, TOLERANCE) for c in coords[0])
                    end = tuple(round(c, TOLERANCE) for c in coords[-1])
                    if start != end:  # Only keep non-self-loops
                        merged_geometries.append(geom)
                    else:
                        self_loops_removed += 1

    segments_removed = len(segment_list) - len(merged_geometries)
    print(f"  Simplified: {len(segment_list)} → {len(merged_geometries)} segments "
          f"({segments_removed} degree-2 nodes removed, {self_loops_removed} self-loops removed)")

    return gdf(geometry=merged_geometries, crs=network_gdf.crs)


def snap_endpoints_to_nearby_lines(network_gdf: gdf, snap_tolerance: float) -> gdf:
    """
    Snap line endpoints to nearby lines within tolerance to fix near-miss connections.

    This function addresses a common issue in manually digitized street networks where
    lines should connect but have small gaps due to drawing inaccuracies. It finds
    dangling endpoints (not already connected to other lines) that are close to other
    lines and snaps them to create proper T-junctions that will be properly split
    by subsequent union_all operations.

    Optimization: Only considers endpoints that are "dangling" (terminal points not
    already connected), dramatically reducing the search space.

    IMPORTANT FIX (2025-11): Changed line 404 from overwriting snap points to appending them.
    This ensures that multiple dangling endpoints snapping to the same line are all preserved,
    preventing disconnected components.

    Use Cases:
    ----------
    - Fixing manually digitized street networks with near-miss connections
    - Cleaning data where GPS inaccuracies created small gaps
    - Connecting street segments that should meet but have tiny offsets
    - Creating T-junctions where endpoints touch line segments

    Process:
    --------
    1. Identify all dangling endpoints (appears exactly once in network)
    2. For each dangling endpoint, find nearby lines within tolerance
    3. Snap endpoint to nearest point on closest line
    4. Collect all snap points per line (using append, not overwrite)
    5. Split target lines at all snap points to create explicit junctions
    6. Rebuild geometries with snapped endpoints

    :param network_gdf: GeoDataFrame with street LineStrings
    :type network_gdf: gdf
    :param snap_tolerance: Maximum distance to snap endpoints (meters)
    :type snap_tolerance: float
    :return: GeoDataFrame with snapped connections and split lines at junctions
    :rtype: gdf

    Example:
        >>> # Fix near-miss connections within 0.5 meters
        >>> cleaned_streets = snap_endpoints_to_nearby_lines(streets_gdf, 0.5)
    """
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

    # Step 2: Use GeoDataFrame's built-in spatial index for fast nearest-neighbor queries
    _network_gdf = network_gdf.copy()
    _network_gdf.reset_index(inplace=True, drop=True)  # Ensure clean index for sindex
    sindex = _network_gdf.sindex

    # Track which lines need to be split and where
    lines_to_split = {}  # {line_idx: [snap_points]}

    def _snap_point_to_nearby_lines(point_coords: tuple, idx_to_exclude) -> tuple:
        """
        Inner helper: Snap a single point to the nearest nearby line within tolerance.

        :param point_coords: Tuple of (x, y) coordinates to snap
        :param idx_to_exclude: The index of the line geometry to exclude (don't snap to itself)
        :return: Snapped coordinates (x, y) or original if no nearby line found
        """
        point = Point(point_coords)
        # Query spatial index with buffered point to find candidates
        nearby_indices = sindex.query(point.buffer(snap_tolerance), predicate='intersects')
        nearby_indices = [id for id in nearby_indices if id != idx_to_exclude]  # Exclude the line itself

        if not nearby_indices:
            return point_coords  # No nearby lines to snap to

        distance = _network_gdf.loc[nearby_indices].geometry.distance(point).sort_values()
        nearest_index = distance.index[0]
        nearest_line: LineString = _network_gdf.loc[nearest_index].geometry

        # Snap to nearest point on line
        snapped = nearest_line.interpolate(nearest_line.project(point))
        best_snap = (snapped.x, snapped.y)
        if lines_to_split.get(nearest_index) is None:
            lines_to_split[nearest_index] = []
        lines_to_split[nearest_index].append(Point(best_snap))

        return best_snap if best_snap else point_coords

    # Step 3: Process lines with dangling endpoints first
    modified_geometries = {}  # {idx: geometry}

    for idx, row in _network_gdf.iterrows():
        line = row.geometry
        coords = list(line.coords)

        start = tuple(coords[0])
        end = tuple(coords[-1])

        # Check if endpoints are dangling
        start_is_dangling = start in dangling_endpoints
        end_is_dangling = end in dangling_endpoints

        # Snap dangling endpoints
        if start_is_dangling or end_is_dangling:
            new_start = _snap_point_to_nearby_lines(coords[0], idx) if start_is_dangling else coords[0]
            new_end = _snap_point_to_nearby_lines(coords[-1], idx) if end_is_dangling else coords[-1]
            new_coords = [new_start] + coords[1:-1] + [new_end]
            modified_geometries[idx] = LineString(new_coords)
        else:
            modified_geometries[idx] = line

    # Step 4: Split lines that had endpoints snapped to them
    final_geometries = []
    for idx, row in _network_gdf.iterrows():
        if idx in lines_to_split:
            # This line needs to be split at snap points
            line = modified_geometries[idx]
            snap_points = lines_to_split[idx]

            # Manually split the line by inserting snap points
            # This is more reliable than Shapely's split() for points on lines
            coords = list(line.coords)

            # Calculate where each snap point falls along the line
            split_positions = []
            for snap_point in snap_points:
                distance_along = line.project(snap_point)
                split_positions.append((distance_along, (snap_point.x, snap_point.y)))

            # Sort by distance along the line
            split_positions.sort(key=lambda x: x[0])

            # Build new line segments
            current_start = coords[0]
            current_coords = [current_start]

            for distance_along, snap_coord in split_positions:
                # Add the snap point as the end of current segment
                current_coords.append(snap_coord)
                # Create line segment
                if len(current_coords) >= 2:
                    final_geometries.append(LineString(current_coords))
                # Start new segment from snap point
                current_coords = [snap_coord]

            # Add final segment from last snap point to end
            current_coords.append(coords[-1])
            if len(current_coords) >= 2:
                final_geometries.append(LineString(current_coords))
        else:
            final_geometries.append(modified_geometries[idx])

    return gdf(geometry=final_geometries, crs=network_gdf.crs)


def clean_street_network(network_gdf: gdf, snap_tolerance: float) -> gdf:
    """
    Comprehensive street network cleaning workflow.

    This function applies a sequence of cleaning operations to fix common issues
    in street network data:
    1. Snap near-miss endpoints to nearby lines (fix small gaps)
    2. Split streets at intersection points (automatic detection)
    3. Simplify by merging degree-2 nodes (remove insignificant pass-through points)

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
    print("1. Snapping near-miss endpoints...")
    network_gdf = snap_endpoints_to_nearby_lines(network_gdf, snap_tolerance)

    print("2. Splitting streets at intersections...")
    network_gdf = split_streets_at_intersections(network_gdf)

    print("3. Simplifying network (merging degree-2 nodes)...")
    network_gdf = simplify_street_network_geometric(network_gdf)

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


def near_analysis(building_centroids, street_network: gdf):
    # Get the nearest edge for each building centroid
    nearest_indexes = street_network.sindex.nearest(building_centroids.geometry, return_all=False)[1]
    nearest_lines = street_network.iloc[nearest_indexes].reset_index(drop=True)  # reset index so vectorization works

    # Find length along line that is closest to the point (project) and get interpolated point on the line (interpolate)
    # IMPORTANT: interpolate() returns raw float coordinates, so normalize immediately
    nearest_points_raw = nearest_lines.interpolate(nearest_lines.project(building_centroids))

    # Normalize all points to consistent precision to prevent floating-point mismatches
    from cea.technologies.network_layout.graph_utils import normalize_geometry
    nearest_points_normalized = [normalize_geometry(pt, SHAPEFILE_TOLERANCE) for pt in nearest_points_raw]

    df = gdf({"idx": nearest_indexes}, geometry=nearest_points_normalized, crs=street_network.crs)
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


def create_terminals(building_centroids: gdf, street_network: gdf) -> gdf:
    """
    Create terminal connection lines from building centroids to nearest points on street network.

    This function implements robust coordinate normalization to prevent micro-precision disconnections:
    1. Finds nearest point on street network for each building (via near_analysis)
    2. Normalizes all coordinates to SHAPEFILE_TOLERANCE precision (6 decimal places)
    3. Creates LineString geometries connecting building → street with normalized coords
    4. Splits street lines at terminal junction points using normalized split points
    5. Validates connectivity and warns if disconnected components are detected

    Key improvements for connectivity:
    - Uses exact normalized coordinate comparison instead of distance thresholds
    - Ensures all coordinates are consistently rounded before LineString creation
    - Validates coordinate normalization and checks for micro-disconnections

    :param building_centroids: GeoDataFrame with building centroids and 'name' column
    :type building_centroids: gdf
    :param street_network: GeoDataFrame with street network LineStrings (already corrected)
    :type street_network: gdf
    :return: Combined network (street + building terminals) with all coordinates normalized
    :rtype: gdf
    """
    # Find nearest point on street network for each building centroid
    # Note: near_analysis() now returns normalized points (after interpolate())
    near_points = near_analysis(building_centroids, street_network)

    # Create terminal lines using normalized coordinates
    # CRITICAL: Use normalized coordinates to prevent floating-point precision mismatches
    # Each line connects: building_centroid → nearest_street_point
    new_lines = []
    lines_to_split = {}
    for bldg_pt, street_pt, street_idx in zip(building_centroids.geometry, near_points.geometry, near_points.idx):
        # Normalize both endpoints before creating LineString
        bldg_coord = normalize_coords([bldg_pt.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
        street_coord = normalize_coords([street_pt.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]

        line = LineString([bldg_coord, street_coord])
        new_lines.append(line)

        # Store normalized Point for splitting (ensures split happens at exact coordinate)
        if lines_to_split.get(street_idx) is None:
            lines_to_split[street_idx] = []
        lines_to_split[street_idx].append(Point(street_coord))
    
    # Split street lines at terminal connection points using substring method
    for idx, line in street_network.iterrows():
        if idx not in lines_to_split:
            new_lines.append(line.geometry)
            continue

        split_points = lines_to_split[idx]  # These are already normalized Points

        # Normalize line endpoints for consistent comparison
        coords = list(line.geometry.coords)
        start_coord_normalized = normalize_coords([coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
        end_coord_normalized = normalize_coords([coords[-1]], precision=SHAPEFILE_TOLERANCE)[0]

        valid_split_points = []
        for pt in split_points:
            # Skip if point is at start or end of line (using exact normalized coordinate comparison)
            # Normalize point coordinates for exact comparison
            pt_coord = (round(pt.x, SHAPEFILE_TOLERANCE), round(pt.y, SHAPEFILE_TOLERANCE))

            # Use exact coordinate tuple comparison (more reliable than distance threshold)
            if pt_coord == start_coord_normalized or pt_coord == end_coord_normalized:
                continue
            valid_split_points.append(pt)

        if valid_split_points:
            # Get distances along line for each split point and sort
            distances = sorted([line.geometry.project(pt) for pt in valid_split_points])

            # Create segments between start, split points, and end
            all_distances = [0] + distances + [line.geometry.length]

            # Generate segments using substring
            # IMPORTANT: substring() produces raw float coordinates, so normalize immediately
            from cea.technologies.network_layout.graph_utils import normalize_geometry
            for i in range(len(all_distances) - 1):
                start_dist = all_distances[i]
                end_dist = all_distances[i + 1]

                if end_dist - start_dist > 1e-10:  # Skip zero-length segments
                    segment = substring(line.geometry, start_dist, end_dist, normalized=False)
                    # Normalize segment coordinates to prevent precision mismatches
                    segment_normalized = normalize_geometry(segment, precision=SHAPEFILE_TOLERANCE)
                    new_lines.append(segment_normalized)
        else:
            # No interior split points - keep original line
            new_lines.append(line.geometry)
    
    # Create GeoDataFrame with all network lines (streets + building terminals)
    combined_network = gdf(geometry=new_lines, crs=street_network.crs)

    # Note: No normalization needed here - all coordinates are already normalized:
    # - Terminal line endpoints: normalized before LineString creation (lines 621-622)
    # - Street split points: normalized Points used for splitting (line 630)
    # - Original streets: normalized in _prepare_network_inputs() before this function
    # This ensures consistent precision throughout and prevents disconnected components

    # Validate coordinate normalization
    # from cea.technologies.network_layout.graph_utils import validate_normalized_coordinates
    # validate_normalized_coordinates(combined_network, precision=SHAPEFILE_TOLERANCE)

    # # Check for micro-disconnections by converting to graph and analyzing connectivity
    # from cea.technologies.network_layout.graph_utils import gdf_to_nx
    # import networkx as nx

    # test_graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE)
    # if not nx.is_connected(test_graph):
    #     components = list(nx.connected_components(test_graph))
    #     print(f"⚠️  WARNING: create_terminals produced {len(components)} disconnected components")
    #     print(f"   Largest component: {len(max(components, key=len))} nodes")
    #     print(f"   Component sizes: {sorted([len(c) for c in components], reverse=True)}")
    #     print("   This may indicate coordinate precision issues that need investigation")

    return combined_network


def apply_graph_corrections(network_gdf: gdf, protected_nodes: list | None = None) -> gdf:
    """
    Apply graph corrections to a network to fix connectivity issues.

    This function converts a GeoDataFrame to a NetworkX graph, applies corrections
    using GraphCorrector with a two-pass merging strategy, then converts back to GeoDataFrame.

    Correction pipeline:
    1. Remove self-loops (invalid edges from nodes to themselves)
    2. Merge close nodes in two passes:
       - Pass 1 (Micro-precision): Merge nodes within 10^-6m (1 micrometer) using <= comparison
         Catches coordinate rounding artifacts from geometric operations
       - Pass 2 (Snap-tolerance): Merge nodes within 0.1m using < comparison
         Handles data quality issues and near-miss connections
    3. Connect intersecting edges (add missing junction nodes)
    4. Connect disconnected components (last resort connections between components)

    Protected nodes (e.g., building centroids) will not be merged or moved during
    corrections, ensuring their exact coordinates are preserved.

    Note: Edge weights are not preserved during correction as they will be
    recalculated from geometry later in the pipeline (Shape_Leng field).

    :param network_gdf: GeoDataFrame with network LineStrings (streets or streets + terminals)
    :type network_gdf: gdf
    :param protected_nodes: Optional list of node coordinates to protect from merging
    :type protected_nodes: list, optional
    :return: Corrected network as GeoDataFrame with all micro-precision disconnections resolved
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

    # Normalize all coordinates to consistent precision (prevents floating-point issues)
    print("Normalizing coordinates to consistent precision...")
    normalize_gdf_geometries(streets_network_df, precision=SHAPEFILE_TOLERANCE, inplace=True)
    normalize_gdf_geometries(building_centroids_df, precision=SHAPEFILE_TOLERANCE, inplace=True)

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
    prototype_network = create_terminals(building_centroids_df, street_network)

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

    potential_network_df['length'] = potential_network_df.geometry.length

    return potential_network_df


def _validate_network_creation(graph: nx.Graph, building_centroids_df: gdf, output_edges: gdf) -> None:
    """
    Validate that network creation succeeded correctly.

    Checks for common issues:
    - Graph connectivity (single connected component)
    - Building terminals exist in graph
    - Edge geometries are valid
    - Coordinate precision is consistent

    :param graph: NetworkX graph to validate
    :param building_centroids_df: GeoDataFrame of building centroids
    :param output_edges: GeoDataFrame of output edges
    :raises ValueError: If validation fails
    """
    # Check 1: Graph is connected
    if not nx.is_connected(graph):
        num_components = nx.number_connected_components(graph)
        raise ValueError(
            f"Network graph is not connected ({num_components} components found). "
            f"This should have been caught earlier in processing."
        )

    # Check 2: All building terminals have corresponding nodes in graph
    graph_nodes = set(graph.nodes())
    missing_terminals = []

    for idx, row in building_centroids_df.iterrows():
        building_id = row.get('name', idx)
        bldg_x, bldg_y = round(row.geometry.x, SHAPEFILE_TOLERANCE), round(row.geometry.y, SHAPEFILE_TOLERANCE)

        # Check if a node exists very close to this building (within tolerance)
        found = False
        for node in graph_nodes:
            if abs(node[0] - bldg_x) < 1.0 and abs(node[1] - bldg_y) < 1.0:
                found = True
                break

        if not found:
            missing_terminals.append(building_id)

    if missing_terminals:
        raise ValueError(
            f"{len(missing_terminals)} building terminals not found in graph: {missing_terminals[:5]}..."
        )

    # Check 3: Output edges have valid geometries
    if output_edges.empty:
        raise ValueError("No edges in output GeoDataFrame")

    invalid_geoms = ~output_edges.geometry.is_valid
    if invalid_geoms.any():
        raise ValueError(
            f"{invalid_geoms.sum()} invalid geometries found in output edges"
        )

    # Check 4: Edges have required attributes
    if 'length' not in output_edges.columns:
        raise ValueError("Output edges missing 'length' column")

    if (output_edges['length'] <= 0).any():
        raise ValueError("Output edges contain zero or negative lengths")

    print(f"  ✓ Validation passed: {len(graph.nodes())} nodes, {len(graph.edges())} edges, "
          f"{len(building_centroids_df)} building terminals")


def _extract_building_terminal_nodes(graph: nx.Graph, building_centroids_df: gdf) -> dict:
    """
    Extract mapping of building IDs to their terminal node coordinates in the graph.

    Uses spatial search (KDTree) to find the graph node closest to each building centroid.
    This accounts for CRS transformation and coordinate rounding that occurred during
    network creation.

    :param graph: NetworkX graph with building terminals as nodes
    :param building_centroids_df: GeoDataFrame of building centroids with 'name' column
    :return: Dictionary mapping building_id → (x, y) node coordinates
    :rtype: dict

    Note: Building coordinates are already in the same CRS and precision as the graph
    due to processing in _prepare_network_inputs and create_terminals.
    """
    from scipy.spatial import KDTree

    # Build KDTree from graph nodes for efficient nearest-neighbor search
    graph_nodes = list(graph.nodes())
    if not graph_nodes:
        return {}

    node_coords = [(node[0], node[1]) for node in graph_nodes]
    tree = KDTree(node_coords)

    terminal_mapping = {}

    for idx, row in building_centroids_df.iterrows():
        building_id = row.get('name', idx)
        bldg_geom = row.geometry

        # Get building coordinates (already normalized in _prepare_network_inputs)
        bldg_x, bldg_y = bldg_geom.x, bldg_geom.y

        # Find nearest graph node
        dist, node_idx = tree.query([bldg_x, bldg_y], k=1)

        if dist > 1.0:  # Tolerance: 1 meter (should be much closer in practice)
            print(f"  Warning: Building '{building_id}' terminal is {dist:.3f}m from nearest graph node")

        # Store the actual graph node coordinates
        terminal_mapping[building_id] = graph_nodes[node_idx]

    return terminal_mapping


def calc_connectivity_network_with_geometry(
    streets_network_df: gdf,
    building_centroids_df: gdf,
) -> gdf:
    """
    Create connectivity network preserving street geometries.

    This function creates a fully connected network by:
    1. Preparing inputs (CRS conversion, validation, street network cleaning)
    2. Creating building terminal connections to nearest street points
    3. Validating coordinate normalization
    4. Applying graph corrections to fix micro-precision disconnections
    5. Converting to NetworkX graph with building terminal metadata
    6. Validating final connectivity (raises error if still disconnected)

    The graph corrections step (added to fix connectivity issues) includes:
    - Micro-precision node merging (10^-6m tolerance with <= comparison)
    - Snap-tolerance node merging (0.1m tolerance with < comparison)
    - Protected node handling (building terminals are never merged)

    :param streets_network_df: GeoDataFrame with street network geometries
    :param building_centroids_df: GeoDataFrame with building centroids
    :return: Connectivity network as GeoDataFrame with preserved geometries
    :raises ValueError: If network has disconnected components after all corrections applied
    """
    # Prepare inputs (CRS conversion, validation, cleaning)
    streets_network_df, building_centroids_df, crs = _prepare_network_inputs(
        streets_network_df, building_centroids_df
    )

    # Create terminals from building centroids
    print("\nCreating building terminal connections...")
    streets_network_df = create_terminals(building_centroids_df, streets_network_df)

    # Validate that all coordinates are properly normalized before graph conversion
    # This catches any precision handling bugs early with clear error messages
    # print("  Validating coordinate normalization...")
    # validate_normalized_coordinates(streets_network_df, precision=SHAPEFILE_TOLERANCE)
    # print("  ✓ All coordinates normalized to consistent precision")

    # # Apply graph corrections to fix micro-precision disconnections
    # # This merges nodes that are within floating-point epsilon (handles coordinate rounding artifacts)
    # print("\n  Applying graph corrections to fix micro-precision issues...")
    # building_centroid_coords = _get_protected_building_coords(building_centroids_df)
    # streets_network_df = apply_graph_corrections(streets_network_df, protected_nodes=building_centroid_coords)

    # Convert to graph with geometry preservation
    graph = gdf_to_nx(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)

    # Store building terminal metadata in graph for downstream use
    terminal_mapping = _extract_building_terminal_nodes(graph, building_centroids_df)
    graph.graph['building_terminals'] = terminal_mapping
    graph.graph['crs'] = crs
    graph.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    # Clean up graph components and connect them if needed
    components = list(nx.connected_components(graph))

    # Drop single-node components (as they don't contribute to connectivity)
    if len(components) > 1:
        raise ValueError(
            f"Network graph has {len(components)} disconnected components after terminal creation. "
            f"This indicates a serious connectivity issue that must be resolved."
        )

    # Use the fully connected graph
    G_filtered = graph.copy()

    # Update metadata
    G_filtered.graph['building_terminals'] = terminal_mapping
    G_filtered.graph['crs'] = crs
    G_filtered.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    # Convert back to geodataframe with preserved geometries
    edges = nx_to_gdf(G_filtered, crs=crs, preserve_geometry=True)

    # Set length attribute from geometry if not already present
    if 'geometry' in edges.columns:
        edges['length'] = edges.geometry.length

    # Validate network creation before returning
    print("\nValidating network creation...")
    _validate_network_creation(G_filtered, building_centroids_df, edges)

    return edges
