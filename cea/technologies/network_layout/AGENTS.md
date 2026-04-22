# Network Layout

## Purpose
Build thermal network connectivity graphs by connecting buildings to street networks while preserving curved geometries and maintaining coordinate precision.

## Connected Buildings Configuration

### Separate Parameters for Heating and Cooling

**Network Part 1** (this script) uses separate parameters for district heating and cooling services:
- `heating-connected-buildings`: Buildings to connect to district heating network
- `cooling-connected-buildings`: Buildings to connect to district cooling network

**Key Concept**: User-provided networks represent a **universal pipe trench** (physical infrastructure corridor) that can contain both heating and cooling pipes.

### Workflow: Universal Layout → Service-Specific Nodes

**Step 1: Create Universal Layout (Pipe Trench)**
- Covers **union** of heating + cooling buildings
- Represents physical infrastructure corridor
- Output: `thermal-network/{network_name}/layout.shp`

**Step 2: Generate Service-Specific Nodes (Part 1)**
- Extract heating buildings → `thermal-network/{network_name}/dh/layout/nodes.shp`
- Extract cooling buildings → `thermal-network/{network_name}/dc/layout/nodes.shp`
- Nodes files store which buildings connect to which service

**Step 3: Generate Service-Specific Edges (Part 2)**
- Part 2 script reads universal layout + service-specific nodes
- Generates `dc/layout/edges.shp` and `dh/layout/edges.shp`

### Example Usage

```python
# Different buildings for heating vs cooling
heating-connected-buildings: B1001, B1002, B1003
cooling-connected-buildings: B1003, B1004, B1005

# Result:
# - Universal layout.shp covers: B1001, B1002, B1003, B1004, B1005 (union of 5 buildings)
# - dh/layout/nodes.shp contains: B1001, B1002, B1003 (3 heating nodes)
# - dc/layout/nodes.shp contains: B1003, B1004, B1005 (3 cooling nodes)
# - Part 2 generates separate edges for each service
```

### Parameter Behavior

**When blank (empty list):**
- `heating-connected-buildings = ` → All buildings with heating demand
- `cooling-connected-buildings = ` → All buildings with cooling demand

**When explicitly set:**
- Only specified buildings are connected to that service
- Universal layout still covers the union of both lists

**With `consider-only-buildings-with-demand = true`:**
- Filters each service's buildings by demand type
- DC buildings filtered by cooling demand
- DH buildings filtered by heating demand
- Universal layout covers filtered union
- In `process_user_defined_network()`, this filtering must be applied before
  augment/filter validation too, not only in auto-layout mode
- For DH, demand filtering must follow `itemised-dh-services`:
  `space_heating -> Qhs_sys_MWhyr`, `domestic_hot_water -> Qww_sys_MWhyr`
  rather than the broader aggregate `QH_sys_MWhyr`
- Service-to-column mapping lives in ``_DH_DEMAND_COLUMN`` in ``main.py``.
  Both the upstream filter (``get_buildings_with_demand``) and the
  downstream trimmer (``filter_dh_services_by_demand``) read from it,
  so a new DH sub-service is a one-line dict edit.

### Loading Existing Networks

**When using `existing-network`**, `main()` resolves the edges + nodes shapefiles for that network and then passes them through the same `process_user_defined_network()` pipeline as any other user-defined input. The `network-layout-mode` parameter is applied to the loaded graph exactly as it would be for a user-provided shapefile — see the User-Defined Network Layout Modes section below.

If the existing network has both DC and DH node files, they are merged into a temporary shapefile (deduplicated on `(building, geometry)`) so DH-only buildings are preserved. The helper is `_load_existing_network_node_paths()` in `main.py`.

## User-Defined Network Layout Modes

### Overview
When users provide their own network layout (via `edges-shp-path`/`nodes-shp-path` or `network-geojson-path`), CEA offers three modes for handling mismatches between the network and the `connected-buildings` parameter.

### Configuration Parameters

**`network-layout-mode`** (default: `validate`)
- **`validate`**: Strict validation - error if network doesn't match parameter exactly
- **`augment`**: Add missing buildings to network (union/additive)
- **`filter`**: Add missing AND remove extra buildings (exact match)

**`auto-modify-network`** (default: `true`)
- Enables network modifications for `augment`/`filter` modes
- When `false`: augment/filter modes will error if modifications are needed
- Ignored in `validate` mode (always non-destructive)
- User's original network files on disk are **never changed**

### Mode Behaviors

| Mode | Missing Buildings | Extra Buildings | Use Case |
|------|------------------|----------------|----------|
| **validate** | ❌ Error | ❌ Error | Strict validation - ensure network matches parameter exactly |
| **augment** | ➕ Add (if auto-modify=true) | ✓ Keep | Bottom-up expansion - start with core, grow to full district |
| **filter** | ➕ Add (if auto-modify=true) | ➖ Remove (if auto-modify=true) | Top-down/selective - prune network to specific buildings |

### Implementation Details

**Augmentation function:** `augment_user_network_with_buildings()` in `user_network_loader.py`

**Augmentation** (`augment_user_network_with_buildings()`): creates potential network (user edges + streets), runs Kou Steiner with existing + new buildings as terminals, merges result additively. User disk files never modified.

**Filtering** (`filter_network_to_buildings()`): removes nodes not in keep list, drops incident edges, keeps connected components anchored by a surviving terminal or plant, then iteratively prunes dangling junction stubs via `_prune_dangling_stubs()`.

**Plant preservation invariant (filter):** plant nodes and the pipes connecting them to the trunk are protected infrastructure — they are never pruned, even if the building they were anchored to was removed. If a plant ends up in a component with no surviving consumers, the plant and its pipework are still kept and a warning is printed.

**Stub pruning (`_prune_dangling_stubs()`):** iterative helper used by filter. Drops any degree-≤1 node that isn't in the protected-coord set (terminals + plants) and drops its incident edge, repeating until stable. This is what removes leftover junction-only stubs after building removal.

### Input Format Support

Both input formats fully supported:
- **Shapefiles:** `edges-shp-path` + `nodes-shp-path`
- **GeoJSON:** `network-geojson-path` (Point + LineString features)

All modes work identically for both - `load_user_defined_network()` normalises to GeoDataFrames.

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

Terminal nodes (building connection points) are never used as bridge points — only non-terminal street nodes bridge gaps. Real-world case: building connecting to an isolated street fragment 25m from main network would fail without merging.

## Key Helper Functions (`graph_utils.py`)

- `gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True)` — GeoDataFrame → NetworkX. Pure conversion; call `_merge_orphan_nodes_to_nearest()` separately after.
- `_merge_orphan_nodes_to_nearest(graph, terminal_nodes, merge_threshold=50.0)` — merge small disconnected components; pass terminal coords to protect them.
- `nx_to_gdf(graph, crs, preserve_geometry=True)` — NetworkX → GeoDataFrame; use `preserve_geometry=True` to keep curves.
- `normalize_coords(coords, precision=6)` / `normalize_geometry(geom, precision=6)` / `normalize_gdf_geometries(gdf, precision=6, inplace=True)` — round coordinates to avoid float drift.

## Workflow

1. **`_prepare_network_inputs()`** - CRS transformation, validation, cleaning (snap endpoints, split at intersections, simplify)
2. **`create_terminals(connection_candidates=k)`** - Connect each building to k-nearest street points with normalized coordinates
3. **`calc_connectivity_network_with_geometry()`** - Build final graph with metadata
4. **`calc_steiner_spanning_tree(method, connection_candidates)`** - Optimize network layout
   - If `connection_candidates > 1` and `method='kou'`: Kou's metric closure automatically selects best connections
   - If `method='mehlhorn'`: Uses greedy nearest regardless of k

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

## Configuration Parameters

### snap-tolerance
**Default:** `0.5m` (SNAP_TOLERANCE constant when left blank)
**Range:** `0.3-2.0m` typical
**Purpose:** Maximum distance to snap near-miss street endpoints and building connections

Leave blank for default. Use lower values (0.3-0.5m) for dense urban, higher (0.5-2.0m) for sparse suburban. Warnings issued if value may distort geometry.

### connection-candidates
**Default:** `3` (balanced quality/speed)
**Range:** `1-5`
**Purpose:** Number of nearest street edges to consider per building

**Performance tradeoffs:** k=1 fastest/locally optimal, k=3 default (3-5x slower, better quality), k=5 best quality (10-25x slower). Only works with Kou; Mehlhorn always uses k=1.

## Constants
- `SHAPEFILE_TOLERANCE = 6` - Decimal places (1 micrometer precision)
- `SNAP_TOLERANCE = 0.5` - Meters for snapping near-miss connections (configurable via snap-tolerance parameter)

## Testing
Tests are in `cea/tests/test_network_layout_integration.py`

## Related Files
- `steiner_algorithm_alternatives.md` - Dev reference: alternative algorithms and future improvements
- `connectivity_potential.py` - Main network creation, `create_terminals()`
- `graph_utils.py` - `gdf_to_nx`, `nx_to_gdf`, `normalize_*`
- `optimization_new/user_network_loader.py` - User network loading, validation, augmentation, filtering
- `optimization_new/network.py` - Uses graph with building terminal metadata
- `main.py` - Orchestrates workflow
- `steiner_spanning_tree.py` - `add_plant_close_to_anchor()`, `calc_steiner_spanning_tree()`
