"""
Create thermal network connectivity graphs by connecting buildings to street networks.

This module builds a NetworkX graph suitable for Steiner tree optimisation by:
1. Cleaning street networks (snap near-miss endpoints, split at intersections, simplify)
2. Creating building terminal connections to nearest street points
3. Normalising coordinates to 6 decimal places to prevent floating-point errors
4. Preserving curved street geometries and building terminal metadata

Main Function
=============
calc_connectivity_network_with_geometry(streets_gdf, buildings_gdf) → NetworkX graph
    Returns a graph with:
    - Nodes: (x, y) tuples with consistent coordinate precision
    - Edges: With 'geometry' (curved LineStrings) and 'weight' (length) attributes
    - Metadata: graph.graph['building_terminals'], graph.graph['crs'], graph.graph['coord_precision']

Coordinate Precision
====================
All coordinates are normalized to SHAPEFILE_TOLERANCE (6 decimal places = 1 micrometer precision).
This prevents floating-point errors from geometric operations like interpolate() and substring()
that can create micro-gaps at junction points.

Key guarantees:
- Network is fully connected (single component)
- Building coordinates are preserved exactly
- Street geometries are preserved (including curves)
- No floating-point precision issues
"""

import warnings
from collections import defaultdict, Counter

import networkx as nx
import numpy as np
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString
from shapely.ops import substring, linemerge

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile
from cea.technologies.network_layout.graph_utils import gdf_to_nx, normalize_gdf_geometries, normalize_coords, normalize_geometry, _merge_orphan_nodes_to_nearest


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

    Example:
        Before: Two crossing streets as continuous lines
        After: Four line segments meeting at intersection point

    :param network_gdf: GeoDataFrame with street LineStrings
    :type network_gdf: gdf
    :return: Cleaned GeoDataFrame with endpoints snapped to nearby lines
    :rtype: gdf
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

    After splitting at intersections, we have many segments. This function identifies
    chains of segments between real intersections (degree >= 3) and merges them into
    single segments while preserving full geometry. This reduces the number of nodes
    for the Steiner tree algorithm to process.

    Key features:
    - Merges chains of segments connected only through degree-2 nodes
    - Preserves all segments at degree-3+ nodes (real intersections)
    - Protects circular structures (roundabouts, cul-de-sacs)
    - Removes self-loops ONLY when they're truly isolated loops

    :param network_gdf: GeoDataFrame with street LineStrings (after splitting)
    :param coord_precision: Decimal places for coordinate rounding
    :return: Simplified GeoDataFrame with merged chains

    Example:
        >>> # After splitting: A-B-C-D-E (4 segments with degree-2 at B,C,D)
        >>> simplified = simplify_street_network_geometric(split_network)
        >>> # Result: A-----------E (1 segment, preserving all vertices)
    """
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

    for chain in chains:
        if len(chain) == 1:
            # Single segment - keep it even if it's a self-loop (could be a roundabout)
            seg = segment_list[chain[0]]
            merged_geometries.append(seg['geometry'])
        else:
            # Merge multiple segments
            chain_geoms = [segment_list[idx]['geometry'] for idx in chain]
            merged = linemerge(chain_geoms)

            if merged.geom_type == 'LineString':
                # Keep merged line even if closed - it could be a valid circular street
                merged_geometries.append(merged)
            else:
                # Fallback: keep original segments if merge fails
                for geom in chain_geoms:
                    merged_geometries.append(geom)

    segments_removed = len(segment_list) - len(merged_geometries)
    if segments_removed > 0:
        print(f"  Simplified: {len(segment_list)} → {len(merged_geometries)} segments "
              f"({segments_removed} degree-2 nodes removed)")

    return gdf(geometry=merged_geometries, crs=network_gdf.crs)


def snap_endpoints_to_nearby_lines(network_gdf: gdf, snap_tolerance: float, split_lines: bool = False) -> gdf:
    """
    Fix near-miss connections by snapping dangling endpoints to nearby lines.

    Common issue: Street networks often have small gaps where lines should connect but
    don't quite touch. This function finds "dangling" endpoints (that appear only once)
    and snaps them to nearby lines within tolerance to create proper connections.

    :param network_gdf: GeoDataFrame with street LineStrings
    :param snap_tolerance: Maximum distance to snap endpoints (meters)
    :param split_lines: If True, split lines at snap points to create junctions; if False, only snap endpoints
    :return: GeoDataFrame with snapped connections (and optionally split lines at junctions)

    Process:
    1. Find dangling endpoints (endpoints that appear only once in the network)
    2. For each dangling endpoint, find nearby lines within snap_tolerance
    3. Snap endpoint to nearest point on closest line
    4. Optionally split target lines at snap points to create explicit T-junctions

    Example:
        >>> # Fix near-miss connections within 0.5 meters
        >>> cleaned = snap_endpoints_to_nearby_lines(streets_gdf, snap_tolerance=0.5)
        >>> # Just snap without splitting
        >>> snapped = snap_endpoints_to_nearby_lines(streets_gdf, snap_tolerance=0.5, split_lines=False)
    """
    # Ensure all geometries are LineStrings (explode MultiLineStrings first)
    # This avoids errors when accessing `.coords` on MultiLineString geometries
    if not all(network_gdf.geometry.geom_type == 'LineString'):
        network_gdf = network_gdf.explode(index_parts=False).reset_index(drop=True)

    # Step 1: Find dangling endpoints (terminal points not connected)
    # Count how many times each endpoint appears across all lines
    endpoint_counts = Counter()
    for geom in network_gdf.geometry:
        # Convert to plain (float, float) tuples to avoid inhomogeneous types
        coords = [(float(c[0]), float(c[1])) for c in geom.coords]
        start = coords[0]
        end = coords[-1]
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

    def _snap_point_to_nearby_lines(point_coords: tuple, idx_to_exclude) -> tuple[float, float]:
        """
        Inner helper: Snap a single point to the nearest nearby line within tolerance.

        :param point_coords: Tuple of (x, y) coordinates to snap
        :param idx_to_exclude: The index of the line geometry to exclude (don't snap to itself)
        :return: Snapped coordinates (x, y) or original if no nearby line found
        """
        # Ensure point_coords is a plain tuple (not numpy array or other sequence)
        point_coords = tuple(point_coords)
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
        # Build normalized coordinate tuple directly to avoid geometry-type ambiguity
        best_snap = (
            round(float(snapped.x), SHAPEFILE_TOLERANCE),
            round(float(snapped.y), SHAPEFILE_TOLERANCE)
        )
        if lines_to_split.get(nearest_index) is None:
            lines_to_split[nearest_index] = []
        lines_to_split[nearest_index].append(Point(best_snap))

        return best_snap

    # Step 3: Process lines with dangling endpoints first
    modified_geometries = {}  # {idx: geometry}

    for idx, row in _network_gdf.iterrows():
        line = row.geometry
        # Use homogeneous (float, float) tuples for all vertices
        coords = [(float(c[0]), float(c[1])) for c in line.coords]

        start = coords[0]
        end = coords[-1]

        # Check if endpoints are dangling
        start_is_dangling = start in dangling_endpoints
        end_is_dangling = end in dangling_endpoints

        # Snap dangling endpoints
        if start_is_dangling or end_is_dangling:
            new_start = _snap_point_to_nearby_lines(coords[0], idx) if start_is_dangling else coords[0]
            new_end = _snap_point_to_nearby_lines(coords[-1], idx) if end_is_dangling else coords[-1]
            # Ensure all middle coordinates are (float, float) tuples
            new_coords = [new_start] + [(float(c[0]), float(c[1])) for c in coords[1:-1]] + [new_end]
            modified_geometries[idx] = LineString(new_coords)
        else:
            modified_geometries[idx] = line

    # Just snap and not split
    final_geometries = []
    # Step 4a: If no splitting needed, return snapped geometries directly
    if not split_lines:
        for idx, row in _network_gdf.iterrows():
            final_geometries.append(modified_geometries[idx])
        return gdf(geometry=final_geometries, crs=network_gdf.crs)

    # Step 4b: Split lines that had endpoints snapped to them
    for idx, row in _network_gdf.iterrows():
        if idx in lines_to_split:
            # This line needs to be split at snap points
            line = modified_geometries[idx]
            snap_points = lines_to_split[idx]

            # Manually split the line by inserting snap points
            # This is more reliable than Shapely's split() for points on lines
            # Use homogeneous (float, float) tuples for splitting operations
            coords = [(float(c[0]), float(c[1])) for c in line.coords]

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
    3. Simplify by merging degree-2 nodes (reduces nodes for Steiner tree algorithm)

    :param network_gdf: GeoDataFrame with raw street LineStrings
    :param snap_tolerance: Maximum distance to snap endpoints (meters)
    :return: Cleaned GeoDataFrame with proper topology

    Example:
        >>> # Clean raw street network before processing
        >>> cleaned = clean_street_network(raw_streets_gdf, SNAP_TOLERANCE)
    """
    print("1. Snapping near-miss endpoints...")
    network_gdf = snap_endpoints_to_nearby_lines(network_gdf, snap_tolerance)

    print("2. Splitting streets at intersections...")
    network_gdf = split_streets_at_intersections(network_gdf)

    print("3. Simplifying network (merging degree-2 nodes)...")
    network_gdf = simplify_street_network_geometric(network_gdf)

    return network_gdf


def near_analysis(building_centroids, street_network: gdf, k: int = 1):
    """
    Find k-nearest street edges for each building centroid.

    Optimized implementation using vectorized operations and spatial indexing
    for efficient k-nearest neighbor search.

    :param building_centroids: GeoDataFrame of building centroids
    :param street_network: GeoDataFrame of street network edges
    :param k: Number of nearest edges to find per building (default 1)
    :return: GeoDataFrame with building_idx, street_idx, and connection point geometry
    """
    if k < 1:
        k = 1

    if len(street_network) == 0 or len(building_centroids) == 0:
        return gdf({"building_idx": [], "idx": []}, geometry=[], crs=street_network.crs)

    results = []
    k_nearest_count = min(k, len(street_network))

    # Pre-compute all distances in a vectorized manner
    # For each building, calculate distances to all streets (vectorized)
    # Then select k smallest per building
    for bldg_idx, bldg_row in building_centroids.iterrows():
        bldg_geom = bldg_row.geometry

        # Compute distances to all streets (vectorized)
        distances = street_network.geometry.distance(bldg_geom)
        if distances.isna().all():
            continue

        # Get k-nearest street indices
        k_nearest_indices = distances.nsmallest(k_nearest_count).index.tolist()

        # Batch process the k-nearest streets for this building
        for street_idx in k_nearest_indices:
            street_line = street_network.loc[street_idx].geometry
            # Project building point onto street line and interpolate
            projected_distance = street_line.project(bldg_geom)
            connection_point_raw = street_line.interpolate(projected_distance)
            connection_point_normalized = normalize_geometry(connection_point_raw, SHAPEFILE_TOLERANCE)

            results.append({
                "building_idx": bldg_idx,
                "idx": street_idx,
                "geometry": connection_point_normalized
            })

    if not results:
        # No candidates found at all; return empty GDF with expected columns
        return gdf({"building_idx": [], "idx": []}, geometry=[], crs=street_network.crs)

    return gdf(results, crs=street_network.crs)


def create_terminals(building_centroids: gdf, street_network: gdf, connection_candidates: int = 1) -> gdf:
    """
    Create terminal connection lines from building centroids to nearest points on street network.

    This function implements robust coordinate normalization to prevent micro-precision disconnections:
    1. Finds k-nearest points on street network for each building (via near_analysis)
    2. Normalizes all coordinates to SHAPEFILE_TOLERANCE precision (6 decimal places)
    3. Creates LineString geometries connecting building → street with normalized coords
    4. Splits street lines at terminal junction points using normalized split points
    5. Validates connectivity and warns if disconnected components are detected

    Key improvements for connectivity:
    - Uses exact normalized coordinate comparison instead of distance thresholds
    - Ensures all coordinates are consistently rounded before LineString creation
    - Validates coordinate normalization and checks for micro-disconnections
    - Supports k-nearest connections for better network optimization (when k > 1)

    :param building_centroids: GeoDataFrame with building centroids and 'name' column
    :type building_centroids: gdf
    :param street_network: GeoDataFrame with street network LineStrings (already corrected)
    :type street_network: gdf
    :param connection_candidates: Number of nearest street edges to connect each building to (default 1)
    :type connection_candidates: int
    :return: Combined network (street + building terminals) with all coordinates normalized
    :rtype: gdf
    """
    # Find k-nearest points on street network for each building centroid
    # Note: near_analysis() now returns normalized points (after interpolate())
    near_points = near_analysis(building_centroids, street_network, k=connection_candidates)

    # Create terminal lines using normalized coordinates
    # CRITICAL: Use normalized coordinates to prevent floating-point precision mismatches
    # Each line connects: building_centroid → k-nearest_street_points
    # When k > 1, creates multiple connection options per building for Steiner tree optimization
    new_lines = []
    lines_to_split = {}
    
    # Iterate through all near_points (which may include k candidates per building)
    for idx, row in near_points.iterrows():
        bldg_idx = row['building_idx']
        street_idx = row['idx']
        street_pt = row.geometry
        bldg_pt = building_centroids.loc[bldg_idx].geometry
        
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

    # CRITICAL FIX: Re-normalize all geometries after substring operations
    # 
    # substring() performs geometric interpolation which can introduce floating-point drift,
    # especially at intermediate vertices of curved streets. Even though we normalize the
    # result with normalize_geometry(), the preserved geometry in edge attributes may still
    # contain unnormalized intermediate vertices. When gdf_to_nx() later extracts start/end
    # coordinates and re-normalizes them, any terminal connection at an intermediate vertex
    # will have a normalized coordinate that doesn't match the drifted vertex coordinate.
    # This causes terminal edges and street segments to become disconnected nodes in the graph.
    #
    # Solution: Apply one final normalization pass to ALL geometries (including all vertices)
    # to ensure absolute coordinate consistency across the entire combined network.
    normalize_gdf_geometries(combined_network, precision=SHAPEFILE_TOLERANCE, inplace=True)

    # Important: Do NOT run global snap/union here.
    # Running topology operations (snap/intersection split) on the combined set of
    # street + terminal lines can unintentionally merge terminal lines with street
    # segments across multiple buildings, producing long segments with building-to-
    # building endpoints. Those become direct building-to-building edges in the graph.
    #
    # Street network was already cleaned in _prepare_network_inputs(...) and each
    # street line was explicitly split at terminal junctions above. Keeping the
    # terminal lines separate here preserves the intended topology:
    #  - Buildings connect to streets via leaf terminal edges only
    #  - No direct building-to-building edges are created by global merges
    # If further cleaning is needed, it must be applied to the street network
    # BEFORE adding terminals (already done upstream), not after combining.

    return combined_network


def _validate_snap_tolerance(streets_network_df: gdf, snap_tolerance: float):
    """
    Validate snap_tolerance parameter and warn if value is too large relative to street geometry.
    
    Large tolerance values can cause unintended connections and distorted network topology.
    This function calculates street segment statistics and warns if tolerance exceeds
    reasonable thresholds based on the actual street network geometry.
    
    :param streets_network_df: GeoDataFrame with street network geometries
    :param snap_tolerance: Configured snap tolerance value (meters)
    """
    # Calculate street segment lengths
    segment_lengths = streets_network_df.geometry.length
    
    if len(segment_lengths) == 0:
        return  # Empty network, skip validation
    
    median_length = segment_lengths.median()
    percentile_95_length = segment_lengths.quantile(0.95)
    
    # Calculate endpoint proximity statistics (estimate typical gaps between near-miss endpoints)
    # Use a sample if network is large (>1000 segments)
    sample_size = min(1000, len(streets_network_df))
    sample_df = streets_network_df.sample(n=sample_size, random_state=42) if len(streets_network_df) > sample_size else streets_network_df
    
    # Build spatial index for efficient proximity queries
    sindex = streets_network_df.sindex
    
    # For each line endpoint, find distance to nearest other line
    endpoint_gaps = []
    for idx, row in sample_df.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue
        coords = list(geom.coords)
        if len(coords) < 2:
            continue
        
        # Check both endpoints
        for endpoint_coord in [coords[0], coords[-1]]:
            endpoint = Point(endpoint_coord)
            
            # Find nearby line segments (within 2 * snap_tolerance search radius)
            search_radius = max(2.0 * snap_tolerance, 1.0)  # At least 1m search radius
            nearby_indices = sindex.query(endpoint.buffer(search_radius), predicate='intersects')
            
            min_gap = float('inf')
            for nearby_idx in nearby_indices:
                if nearby_idx == idx:
                    continue  # Skip self
                nearby_geom = streets_network_df.iloc[nearby_idx].geometry
                gap = endpoint.distance(nearby_geom)
                if gap > 0:  # Exclude touching lines
                    min_gap = min(min_gap, gap)
            
            if min_gap < float('inf'):
                endpoint_gaps.append(min_gap)
    
    # Calculate gap statistics
    if endpoint_gaps:
        typical_gap = np.median(endpoint_gaps)
        gap_95th = np.percentile(endpoint_gaps, 95)
    else:
        typical_gap = None
        gap_95th = None
    
    # Warning thresholds
    # 1. Tolerance should be < 25% of median segment length (prevents distorting short segments)
    # 2. Tolerance should be < 2x typical endpoint gap (prevents over-snapping)
    warning_triggered = False
    
    if snap_tolerance > 0.25 * median_length:
        warning_triggered = True
        print(f"  ⚠ WARNING: snap_tolerance ({snap_tolerance:.2f}m) is large relative to street segments")
        print(f"      - Current tolerance: {snap_tolerance:.2f}m")
        print(f"      - Median street segment length: {median_length:.2f}m")
        print(f"      - Recommended maximum: {0.25 * median_length:.2f}m (25% of median segment)")
        print(f"      → Large tolerance may distort short street segments")
    
    if typical_gap is not None and snap_tolerance > 2.0 * typical_gap:
        warning_triggered = True
        print(f"  ⚠ WARNING: snap_tolerance ({snap_tolerance:.2f}m) exceeds typical endpoint gaps")
        print(f"      - Current tolerance: {snap_tolerance:.2f}m")
        print(f"      - Typical endpoint gap: {typical_gap:.2f}m (median)")
        print(f"      - 95th percentile gap: {gap_95th:.2f}m")
        print(f"      - Recommended maximum: {2.0 * typical_gap:.2f}m (2x typical gap)")
        print(f"      → Large tolerance may connect unrelated street segments")
    
    if warning_triggered:
        print(f"  ℹ Advisory: Typical snap_tolerance range is 0.3-2.0m")
        print(f"             Leave snap-tolerance blank in config to use default ({SNAP_TOLERANCE}m)")
        print()


def _prepare_network_inputs(streets_network_df: gdf, building_centroids_df: gdf, snap_tolerance: float = SNAP_TOLERANCE) -> tuple[gdf, gdf, str]:
    """
    Preprocessing for connectivity network functions.

    This function:
    1. Converts to projected CRS for accurate distance calculations
    2. Validates geometries
    3. Cleans street network (splits at intersections, snaps near-miss endpoints)

    :param snap_tolerance: Maximum distance to snap near-miss endpoints (meters), defaults to SNAP_TOLERANCE
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
    
    # Validate snap_tolerance before cleaning
    _validate_snap_tolerance(streets_network_df, snap_tolerance)
    
    streets_network_df = clean_street_network(streets_network_df, snap_tolerance)

    # Normalise all coordinates to consistent precision (prevents floating-point issues)
    print(f"\nNormalising coordinates to consistent precision ({SHAPEFILE_TOLERANCE} decimal places)...")
    normalize_gdf_geometries(streets_network_df, precision=SHAPEFILE_TOLERANCE, inplace=True)
    normalize_gdf_geometries(building_centroids_df, precision=SHAPEFILE_TOLERANCE, inplace=True)

    return streets_network_df, building_centroids_df, crs


def _identify_original_junctions(graph: nx.Graph, terminal_nodes: set[tuple], coord_precision: int = SHAPEFILE_TOLERANCE) -> set[tuple]:
    """
    Identify original street junctions (degree >= 3 nodes) from a graph, excluding terminal nodes.

    Original junctions are nodes where 3 or more edges meet, representing real street
    intersections from the input street network. Building terminals are excluded even
    if they have high degree, as they represent connection points rather than junctions.

    :param graph: NetworkX graph representing the street network
    :param terminal_nodes: Set of (x, y) coordinates of building terminal nodes to exclude
    :param coord_precision: Decimal places for coordinate normalization
    :return: Set of (x, y) coordinates representing original street junctions
    """
    original_junctions = set()

    for node in graph.nodes():
        # Skip terminal nodes (building connections)
        node_coord = tuple(round(c, coord_precision) for c in node) if not isinstance(node, tuple) else node
        if node_coord in terminal_nodes:
            continue

        # Check degree (number of neighbors)
        degree = len(list(graph.neighbors(node)))
        if degree >= 3:
            original_junctions.add(node_coord)

    print(f"  Identified {len(original_junctions)} original street junctions (degree >= 3) in graph")
    return original_junctions


def _validate_and_fix_connectivity(
    graph: nx.Graph,
    terminal_mapping: dict,
    building_centroids_df: gdf,
    streets_clean_df: gdf,
    connection_candidates: int,
    crs: str,
) -> nx.Graph:
    """
    Validate graph connectivity, fix issues, and update graph metadata.

    This function validates terminal mapping integrity, removes orphan components,
    and updates graph.graph metadata with terminal_mapping, crs, and coord_precision.

    :param graph: NetworkX graph to validate
    :param terminal_mapping: Dict mapping building_id → (x, y) node coordinates
    :param building_centroids_df: GeoDataFrame of building centroids
    :param streets_clean_df: GeoDataFrame of cleaned street network (without terminals)
    :param connection_candidates: Number of connection candidates used
    :param crs: Coordinate reference system
    :return: Validated and fixed graph with updated metadata
    :raises ValueError: If network remains disconnected with building terminals on separate components
    """
    # Validate terminal mapping integrity
    graph_nodes = set(graph.nodes())
    building_terminal_nodes = set(terminal_mapping.values())
    
    # Check 1: All expected buildings have terminal mappings
    expected_buildings = set(building_centroids_df['name']) if 'name' in building_centroids_df.columns else set(building_centroids_df.index)
    mapped_buildings = set(terminal_mapping.keys())
    missing_mappings = expected_buildings - mapped_buildings
    if missing_mappings:
        print(f"Warning: {len(missing_mappings)} building(s) missing from terminal_mapping: {list(missing_mappings)[:5]}")
    
    # Check 2: All terminal nodes exist in the graph
    missing_nodes = building_terminal_nodes - graph_nodes
    if missing_nodes:
        print(f"Warning: {len(missing_nodes)} terminal node(s) not found in graph: {list(missing_nodes)[:5]}")
        # Clean up terminal_mapping to remove invalid entries
        terminal_mapping = {bid: node for bid, node in terminal_mapping.items() if node in graph_nodes}
        building_terminal_nodes = set(terminal_mapping.values())
    
    # Check 3: Verify terminal nodes actually have edges (degree >= 1)
    # Note: graph.degree is a DegreeView, not callable - iterate to check degrees
    orphan_terminals = []
    for node in building_terminal_nodes:
        if node in graph and len(list(graph.neighbors(node))) == 0:
            orphan_terminals.append(node)
    if orphan_terminals:
        print(f"Warning: {len(orphan_terminals)} terminal node(s) have no edges (isolated): {orphan_terminals[:5]}")
    
    components = list(nx.connected_components(graph))

    if len(components) > 1:
        # Safely discard orphan components that contain NO building terminals
        # Components with building terminals indicate real connectivity issues that need to be reported
        orphan_components_removed = 0
        orphan_nodes_removed = 0
        
        for component in list(components):  # Use list() to avoid modification during iteration
            # Check if this component has any building terminals
            has_building = any(node in building_terminal_nodes for node in component)
            
            if not has_building:
                # Safe to discard: this component contains only street nodes with no building connections
                # This can happen from isolated street fragments, data artifacts, or network cleaning residue
                for node in component:
                    graph.remove_node(node)
                    orphan_nodes_removed += 1
                orphan_components_removed += 1
        
        if orphan_components_removed > 0:
            print(f"Safely discarded {orphan_components_removed} orphan component(s) with {orphan_nodes_removed} street node(s) (no building terminals attached)")
        
        # Raise error if still disconnected
        if len(list(nx.connected_components(graph))) > 1:
            # Identify buildings in disconnected components and collect diagnostics
            print("\nDisconnected components detected in network graph:")
            all_components = list(nx.connected_components(graph))
            for i, component in enumerate(all_components):
                print(f"  Component {i+1}: {len(component)} nodes")

            # Assume component 0 is the main one
            main_component = all_components[0]
            disconnected_buildings = []
            diagnostics = []

            for building_id, node_coords in terminal_mapping.items():
                if node_coords not in main_component:
                    disconnected_buildings.append(building_id)
                    # Best-effort: get building geometry
                    b_geom = None
                    if 'name' in building_centroids_df.columns:
                        _candidate = building_centroids_df[building_centroids_df['name'] == building_id]
                        if len(_candidate) > 0:
                            b_geom = _candidate.iloc[0].geometry
                    if b_geom is None:
                        # Fallback to index-based lookup if possible
                        try:
                            b_geom = building_centroids_df.loc[building_id].geometry  # type: ignore[index]
                        except Exception:
                            b_geom = None

                    coord_str = "unknown"
                    nearest_str = "n/a"
                    if b_geom is not None:
                        coord_str = f"({round(b_geom.x, 3)}, {round(b_geom.y, 3)})"
                        try:
                            # Use distances to the cleaned street network only (exclude terminal edges)
                            dists = streets_clean_df.geometry.distance(b_geom)
                            topk = dists.nsmallest(min(3, len(dists)))
                            nearest_str = ", ".join([f"idx {idx}: {round(float(dist), 2)} m" for idx, dist in topk.items()])
                        except Exception:
                            nearest_str = "failed to compute"

                    diagnostics.append(f"  - {building_id} at {coord_str}; nearest streets: {nearest_str}")

            hint = (
                f"The network is disconnected with connection_candidates={connection_candidates}. "
                "This indicates the street network near the listed buildings is isolated from the main component. "
                "Try increasing connection_candidates (e.g., to 3) to allow buildings to consider alternative street connections, "
                "or inspect the street geometry around these buildings for missing connections, micro-gaps, or orphan street segments."
            )

            diag_text = "\n".join(diagnostics) if diagnostics else "  (no diagnostics available)"
            
            raise ValueError(
                "\n".join([
                    f"Network graph has {len(all_components)} disconnected components after terminal creation.",
                    "This indicates connectivity issues with the provided street network or terminal placement.",
                    f"Disconnected buildings: {', '.join(disconnected_buildings) if disconnected_buildings else 'unknown'}",
                    "Diagnostics:",
                    diag_text,
                    hint,
                ])
            )

    # Update graph metadata with validated terminal mapping
    graph.graph['building_terminals'] = terminal_mapping
    graph.graph['crs'] = crs
    graph.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    return graph


def calc_connectivity_network_with_geometry(
    streets_network_df: gdf,
    building_centroids_df: gdf,
    connection_candidates: int = 1,
    snap_tolerance: float = SNAP_TOLERANCE,
):
    """
    Create connectivity network graph preserving street geometries and building terminal metadata.

    This function creates a fully connected NetworkX graph by:
    1. Preparing inputs (CRS conversion, validation, street network cleaning)
    2. Creating building terminal connections to nearest street points
    3. Converting to NetworkX graph with preserved geometries
    4. Storing building terminal metadata in graph attributes

    The returned graph includes important metadata:
    - graph.graph['building_terminals']: Dict mapping building_id → (x, y) node coordinates
    - graph.graph['original_junctions']: Set of (x, y) coordinates of original street junctions (calculated on-demand)
    - graph.graph['crs']: Coordinate reference system
    - graph.graph['coord_precision']: Precision used (SHAPEFILE_TOLERANCE)
    - Edge attributes: 'geometry' (curved LineStrings), 'weight' (length)

    To get a GeoDataFrame from the graph:
        edges_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)

    :param streets_network_df: GeoDataFrame with street network geometries
    :param building_centroids_df: GeoDataFrame with building centroids
    :param connection_candidates: Number of nearest street edges to connect each building to.
        Default is 1 (greedy nearest). Values > 1 enable k-nearest optimization with Kou algorithm.
    :param snap_tolerance: Maximum distance to snap near-miss endpoints (meters), defaults to SNAP_TOLERANCE
    :return: NetworkX graph with preserved geometries and building terminal metadata
    :raises ValueError: If network has disconnected components after all corrections applied
    """
    graph = gdf_to_nx(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE)
    print(f"Initial network graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges, number of components: {nx.number_connected_components(graph)}")

    # Prepare inputs (CRS conversion, validation, cleaning)
    streets_network_df, building_centroids_df, crs = _prepare_network_inputs(
        streets_network_df, building_centroids_df, snap_tolerance
    )

    # Preserve a copy of the cleaned street network (without terminals) for diagnostics and retries
    streets_clean_df = streets_network_df.copy()

    # Extract terminal node coordinates (building centroids, normalized)
    # These will be used for:
    # 1. Protecting terminal nodes during orphan merging
    # 2. Building terminal mapping for graph metadata
    terminal_nodes = set()
    terminal_mapping = {}  # building_id -> (x, y) normalized coords
    for idx, row in building_centroids_df.iterrows():
        building_id = row.get('name', idx)
        bldg_coord = normalize_coords([row.geometry.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
        terminal_nodes.add(bldg_coord)
        terminal_mapping[building_id] = bldg_coord

    # Create terminals from building centroids
    if connection_candidates > 1:
        print(f"\nCreating building terminal connections (k={connection_candidates} nearest per building)...")
    else:
        print("\nCreating building terminal connections...")
    combined_network_df = create_terminals(building_centroids_df, streets_network_df, connection_candidates=connection_candidates)

    # Convert to graph with geometry preservation
    graph = gdf_to_nx(
        combined_network_df,
        coord_precision=SHAPEFILE_TOLERANCE,
        preserve_geometry=True
    )

    # Clean orphan nodes: merge small isolated street fragments to main network
    # This fixes disconnections from isolated street segments while protecting building terminals
    graph = _merge_orphan_nodes_to_nearest(
        graph,
        terminal_nodes=terminal_nodes,
        merge_threshold=50.0  # Max 50m to connect isolated street fragments
    )
    graph.graph['building_terminals'] = terminal_mapping
    graph.graph['crs'] = crs
    graph.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    # Identify and store original street junctions (degree >= 3 nodes) from STREETS-ONLY network
    # IMPORTANT: Must use streets_clean_df (before adding building terminals) to avoid inflating junction count
    # If we use the combined graph, any street node connected to a building becomes degree >= 3 (junction),
    # which prevents legitimate degree-2 nodes from being contracted in the Steiner tree
    streets_only_graph = gdf_to_nx(streets_clean_df, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=False)
    original_junctions = _identify_original_junctions(streets_only_graph, set(), SHAPEFILE_TOLERANCE)  # Empty terminal set for streets-only
    graph.graph['original_junctions'] = original_junctions

    # Validate connectivity and fix issues
    graph = _validate_and_fix_connectivity(
        graph=graph,
        terminal_mapping=terminal_mapping,
        building_centroids_df=building_centroids_df,
        streets_clean_df=streets_clean_df,
        connection_candidates=connection_candidates,
        crs=crs,
    )

    return graph
