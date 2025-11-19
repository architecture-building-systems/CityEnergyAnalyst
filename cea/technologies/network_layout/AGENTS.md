# Network Layout

## Purpose
Build thermal network connectivity graphs by connecting buildings to street networks while preserving curved geometries and maintaining coordinate precision.

## Main API

### `calc_connectivity_network_with_geometry(streets_gdf, buildings_gdf, connection_candidates=1) → nx.Graph`
**Returns:** NetworkX graph with preserved geometries and metadata
- **Nodes:** `(x, y)` tuples normalized to 6 decimal places
- **Edges:** `geometry` (curved LineStrings), `weight` (length)
- **Metadata:** `graph.graph['building_terminals']` (dict: building_id → node coords), `graph.graph['crs']`, `graph.graph['coord_precision']`
- **connection_candidates:** Number of nearest street edges to connect each building to (default 1)
  - `1` = greedy nearest (fastest, locally optimal)
  - `3-5` = k-nearest optimization with Kou's metric closure (better quality, 3-25x slower)
  - Only works with Kou algorithm - Mehlhorn uses greedy regardless

**Convert to GeoDataFrame:**
```python
edges_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)
```

### `calc_steiner_spanning_tree(..., method='kou', connection_candidates=1)`
Calculate optimal network connecting buildings through street network
- **method:** `'kou'` (higher quality) or `'mehlhorn'` (faster)
- **connection_candidates:** Number of connection options per building (1-5)
  - With Kou + k>1: Each building tries k nearest streets, Kou's metric closure picks optimal combination
  - With Mehlhorn: Always uses greedy nearest (k>1 ignored with warning)

## Critical Pattern: Coordinate Normalization

**Problem:** Geometric operations produce raw floats → micro-precision gaps → disconnected networks

**Solution:** Normalize immediately after ANY operation that produces coordinates

### Operations That Need Normalization
```python
# After interpolate()
point_raw = line.interpolate(line.project(building))
point = normalize_geometry(point_raw, SHAPEFILE_TOLERANCE)

# After substring()
segment_raw = substring(line, start, end)
segment = normalize_geometry(segment_raw, SHAPEFILE_TOLERANCE)

# Before creating geometries
coords_normalized = normalize_coords(coords, SHAPEFILE_TOLERANCE)
line = LineString(coords_normalized)

# CRITICAL: After combining street + terminal networks
# substring() on curved streets introduces drift at intermediate vertices
# Final pass ensures ALL coordinates are consistent before graph conversion
combined_network = create_terminals(buildings, streets, k)
normalize_gdf_geometries(combined_network, SHAPEFILE_TOLERANCE, inplace=True)
```

## Critical Pattern: Orphan Node Merging

**Problem:** Isolated street fragments (e.g., disconnected road segments) cause building disconnections

**Solution:** Use `_merge_orphan_nodes_to_nearest()` as explicit cleaning step after `gdf_to_nx()`

### When Orphan Merging Occurs
- Component has < 10 nodes (small isolated fragment)
- Component has at least one non-terminal node within `merge_threshold` (default 50m)
- Terminal nodes are never used as bridge points (preserves building connections)
- **Key**: Components with terminals CAN be merged via their street nodes

### Example
```python
# 1. Extract building terminal coordinates for protection
terminal_nodes = set()
terminal_mapping = {}  # building_id -> (x, y)
for idx, row in buildings.iterrows():
    building_id = row.get('name', idx)
    coord = normalize_coords([row.geometry.coords[0]], SHAPEFILE_TOLERANCE)[0]
    terminal_nodes.add(coord)
    terminal_mapping[building_id] = coord

# 2. Create terminals and convert to graph
combined_network = create_terminals(buildings, streets, connection_candidates=k)
graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)

# 3. Apply orphan merging as explicit cleaning step
from cea.technologies.network_layout.graph_utils import _merge_orphan_nodes_to_nearest
graph = _merge_orphan_nodes_to_nearest(
    graph,
    terminal_nodes=terminal_nodes,  # Protect terminal nodes from being bridge points
    merge_threshold=50.0  # Max distance to bridge gaps
)
# Output: "Merged 2 orphan component(s) to main network (added 2 bridging edge(s))"

# 4. Store terminal mapping in graph metadata
graph.graph['building_terminals'] = terminal_mapping
```

### Real-World Example: B1014 Case
- Building B1014 connects to isolated street fragment 25.87m from main network
- Without merging: ERROR "Network has 2 disconnected components"
- With merging: Street node (non-terminal) used as bridge → fully connected ✅

## Key Helper Functions

### `gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True, **attrs)`
Convert GeoDataFrame → NetworkX graph
- Handles Point (lone nodes), LineString, MultiLineString
- Set `preserve_geometry=True` to store full geometries in edge attributes
- Returns graph with normalized node coordinates
- **Note**: This is a pure conversion function - for orphan merging, use `_merge_orphan_nodes_to_nearest()` after conversion

### `_merge_orphan_nodes_to_nearest(graph, terminal_nodes, merge_threshold=50.0)`
**Cleaning function** - Merge small disconnected components to main network
- `terminal_nodes`: Set of (x, y) building terminal coordinates to protect from merging
- Returns graph with normalized node coordinates

### `nx_to_gdf(graph, crs, preserve_geometry=True)`
Convert NetworkX graph → GeoDataFrame
- Restores GeoDataFrame from graph edges
- Set `preserve_geometry=True` to use stored geometries (preserves curves)

### `normalize_coords(coords, precision=6)`
Round coordinate tuples to precision decimal places

### `normalize_geometry(geom, precision=6)`
Round Point/LineString/MultiLineString coordinates

### `normalize_gdf_geometries(gdf, precision=6, inplace=True)`
Normalize all geometries in a GeoDataFrame

## Workflow

1. **`_prepare_network_inputs()`** - CRS transformation, validation, cleaning (snap endpoints, split at intersections, simplify)
2. **`create_terminals(connection_candidates=k)`** - Connect each building to k-nearest street points with normalized coordinates
3. **`calc_connectivity_network_with_geometry()`** - Build final graph with metadata
4. **`calc_steiner_spanning_tree(method, connection_candidates)`** - Optimize network layout
   - If `connection_candidates > 1` and `method='kou'`: Kou's metric closure automatically selects best connections
   - If `method='mehlhorn'`: Uses greedy nearest regardless of k

## Key Helper Functions

### `get_next_node_name(nodes_gdf)`
Generate unique node names by finding max existing node number
- Returns `NODE{n}` where n = max existing number + 1
- Prevents duplicates when nodes are removed during network construction
- **Always use this** instead of `len(nodes_gdf)` or `.name.count()` for node naming

## Common Patterns

### ✅ DO: Use helper function for node naming
```python
# Good - handles node removal correctly
from cea.technologies.network_layout.steiner_spanning_tree import get_next_node_name
node_name = get_next_node_name(nodes_gdf)
new_node = gpd.GeoDataFrame([{'name': node_name, ...}])
```

### ❌ DON'T: Use len() or count() for node naming
```python
# Bad - creates duplicates if nodes are removed
node_name = f'NODE{len(nodes_gdf)}'  # WRONG
node_name = f'NODE{nodes_gdf.name.count()}'  # WRONG
```

### ✅ DO: Normalize after geometric operations
```python
# Good
point_raw = line.interpolate(distance)
point = normalize_geometry(point_raw, SHAPEFILE_TOLERANCE)
```

### ❌ DON'T: Use raw coordinates from geometric operations
```python
# Bad - floating-point drift will cause disconnections
point = line.interpolate(distance)  # RAW FLOATS
line = LineString([point1.coords[0], point2.coords[0]])  # RAW COORDS
```

### ✅ DO: Use building terminal metadata
```python
# Good - guaranteed to work
graph = calc_connectivity_network_with_geometry(streets, buildings)
terminal_coord = graph.graph['building_terminals'][building_id]
```

### ❌ DON'T: Search for terminals manually
```python
# Bad - floating-point errors, CRS mismatches
for node in graph.nodes():
    if distance(node, building_coord) < threshold:  # Will fail
        ...
```

## Plant Node Architecture

**Critical:** Plant nodes are **separate infrastructure nodes**, NOT building nodes with changed type.

### Node Types in Network Layout
- **CONSUMER nodes:** Building connection points (demand-side)
- **PLANT nodes:** Thermal plant infrastructure (supply-side)
- **NONE nodes:** Junction points in network (no building, no plant)

### ✅ DO: Create separate plant node near anchor building
```python
# Good - building node remains CONSUMER, plant is separate node
building_anchor = nodes[nodes['building'] == anchor_building]
nodes, edges = add_plant_close_to_anchor(
    building_anchor, nodes, edges, 'T1', 150
)
# Result:
#   - Building node: type=CONSUMER, building=anchor_building
#   - Plant node: type=PLANT, building=NONE (separate node)
```

### ❌ DON'T: Convert building node to plant
```python
# Bad - building loses its consumer status
anchor_node_idx = nodes[nodes['building'] == anchor_building].index[0]
nodes.loc[anchor_node_idx, 'type'] = 'PLANT'  # WRONG - building is now plant
# Result: Building no longer acts as consumer (breaks demand calculations)
```

### Why Separate Nodes Matter
- Building nodes represent **demand** (consumer connection points)
- Plant nodes represent **supply** (production infrastructure)
- A building can be near a plant but remains a consumer
- Thermal network simulation expects plant nodes to be distinct from building nodes

## Constants
- `SHAPEFILE_TOLERANCE = 6` - Decimal places (1 micrometer precision)
- `SNAP_TOLERANCE = 0.1` - Meters for snapping near-miss connections

## Testing
Tests are in `cea/tests/test_network_layout_integration.py`

## Related Files
- `connectivity_potential.py` - Main network creation
- `graph_utils.py` - Conversion utilities (gdf_to_nx, nx_to_gdf, normalize_*)
- `optimization_new/network.py` - Uses graph with building terminal metadata
- `main.py` - Converts graph to GeoDataFrame for Steiner tree
- `steiner_spanning_tree.py` - Contains `add_plant_close_to_anchor()` for plant creation
