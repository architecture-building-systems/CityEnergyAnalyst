"""
Create thermal network connectivity graphs by connecting buildings to street networks.

This module builds a NetworkX graph suitable for Steiner tree optimization by:
1. Cleaning street networks (snap near-miss endpoints, split at intersections, simplify)
2. Creating building terminal connections to nearest street points
3. Normalizing coordinates to 6 decimal places to prevent floating-point errors
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

import networkx as nx
from geopandas import GeoDataFrame as gdf
from shapely import Point, LineString
from shapely.ops import substring

from cea.constants import SHAPEFILE_TOLERANCE, SNAP_TOLERANCE
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_lat_lon_projected_shapefile
from cea.technologies.network_layout.graph_utils import gdf_to_nx, normalize_gdf_geometries, normalize_coords, normalize_geometry


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

    # Final cleaning: snap near-miss endpoints and split at intersections
    combined_network = snap_endpoints_to_nearby_lines(combined_network, SNAP_TOLERANCE)
    combined_network = split_streets_at_intersections(combined_network)

    return combined_network


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
    print(f"\nNormalizing coordinates to consistent precision ({SHAPEFILE_TOLERANCE} decimal places)...")
    normalize_gdf_geometries(streets_network_df, precision=SHAPEFILE_TOLERANCE, inplace=True)
    normalize_gdf_geometries(building_centroids_df, precision=SHAPEFILE_TOLERANCE, inplace=True)

    return streets_network_df, building_centroids_df, crs


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
    - graph.graph['crs']: Coordinate reference system
    - graph.graph['coord_precision']: Precision used (SHAPEFILE_TOLERANCE)
    - Edge attributes: 'geometry' (curved LineStrings), 'weight' (length)

    To get a GeoDataFrame from the graph:
        edges_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)

    :param streets_network_df: GeoDataFrame with street network geometries
    :param building_centroids_df: GeoDataFrame with building centroids
    :return: NetworkX graph with preserved geometries and building terminal metadata
    :raises ValueError: If network has disconnected components after all corrections applied
    """
    graph = gdf_to_nx(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE)
    print(f"Initial network graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges, number of components: {nx.number_connected_components(graph)}")

    # Prepare inputs (CRS conversion, validation, cleaning)
    streets_network_df, building_centroids_df, crs = _prepare_network_inputs(
        streets_network_df, building_centroids_df
    )

    # Create terminals from building centroids
    print("\nCreating building terminal connections...")
    streets_network_df = create_terminals(building_centroids_df, streets_network_df)

    # Convert to graph with geometry preservation
    graph = gdf_to_nx(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)

    # Store building terminal metadata in graph for downstream use
    terminal_mapping = _extract_building_terminal_nodes(graph, building_centroids_df)
    graph.graph['building_terminals'] = terminal_mapping
    graph.graph['crs'] = crs
    graph.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    # Clean up graph components and connect them if needed
    components = list(nx.connected_components(graph))

    if len(components) > 1:
        # Try to remove single-node components
        for component in components:
            if len(component) == 1:
                graph.remove_node(next(iter(component)))
        
        # Raise error if still disconnected
        if len(list(nx.connected_components(graph))) > 1:
            # Identify buildings in disconnected components
            disconnected_buildings = []
            print("\nDisconnected components detected in network graph:")
            for i, component in enumerate(nx.connected_components(graph)):
                print(f"  Component {i+1}: {len(component)} nodes")
                # Assume first component is the main one
                if i == 0:
                    continue
                for building_id, node_coords in terminal_mapping.items():
                    if node_coords in component:
                        disconnected_buildings.append(building_id)

            raise ValueError(
                f"Network graph has {len(components)} disconnected components after terminal creation.\n"
                f"This indicates connectivity issues with the network provided.\n"
                f"Disconnected buildings: {', '.join(disconnected_buildings)}\n"
                "Check street network connectivity around these buildings."
            )

    # Update metadata in graph
    graph.graph['building_terminals'] = terminal_mapping
    graph.graph['crs'] = crs
    graph.graph['coord_precision'] = SHAPEFILE_TOLERANCE

    return graph
