# Network Layout

## Purpose
Build thermal network connectivity graphs by connecting buildings to street networks while preserving curved geometries and maintaining coordinate precision.

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

### Examples

#### Example 1: Validate Mode (Default) - Strict Validation
```python
# User provides network with 3 buildings
user.shp: B1001, B1002, B1003

# But connected-buildings requires 5 buildings
connected-buildings: B1001, B1002, B1003, B1004, B1005

# network-layout-mode = validate (default)
# → ❌ ERROR raised immediately
# → Error message: "Network missing 2 buildings: B1004, B1005"
# → Suggests using augment or filter mode
# → Script stops (no output files created)
```

#### Example 2: Augment Mode
```python
# User provides network with 3 buildings
user.shp: B1001, B1002, B1003

# connected-buildings requires 5 buildings
connected-buildings: B1001, B1002, B1003, B1004, B1005

# network-layout-mode = augment
# auto-modify-network = true
# → CEA adds B1004, B1005 using Steiner tree optimisation
# → User's original edges/nodes for B1001-B1003 unchanged
# → New optimal paths added for B1004-B1005
# → Result: Network with all 5 buildings
```

#### Example 3: Filter Mode
```python
# User provides network with 5 buildings
user.shp: B1001, B1002, B1003, B1004, B1005

# But only want 3 buildings connected
connected-buildings: B1001, B1002, B1003

# network-layout-mode = filter
# auto-modify-network = true
# → CEA removes B1004, B1005 nodes and orphaned edges
# → Result: Network with only B1001-B1003
```

### Implementation Details

**Augmentation function:** `augment_user_network_with_buildings()` in `user_network_loader.py`

**Augmentation algorithm (3 steps):**
1. Create potential network: user edges + street network
2. Run Steiner tree optimisation (Kou algorithm) with **existing + new buildings as terminals**
   - Treats all existing user building nodes as terminals
   - Guarantees new buildings connect to existing network (not separate component)
   - Finds optimal entry point(s) to minimise added infrastructure
3. Merge augmented subnetwork with user's original network (additive-only)

**Filtering function:** `filter_network_to_buildings()` in `user_network_loader.py`

**Filtering algorithm (3 steps):**
1. Remove building nodes not in `buildings_to_keep` list
2. Convert to graph and find connected components containing kept buildings
3. Remove orphaned edges and junction nodes using graph cleanup

**Key properties:**
- **User's disk files never modified**: Only in-memory GeoDataFrames are changed
- Augmentation: New buildings connect at optimal entry points (existing nodes)
- Filtering: Uses graph-based cleanup to remove orphaned infrastructure
- Both use `connection_candidates` parameter (default: 3) for Steiner optimisation
- Coordinate precision: SHAPEFILE_TOLERANCE (6 decimal places)

### Input Format Support

Both input formats fully supported:
- **Shapefiles:** `edges-shp-path` + `nodes-shp-path`
- **GeoJSON:** `network-geojson-path` (Point + LineString features)

All modes work identically for both - `load_user_defined_network()` normalises to GeoDataFrames.

### Example Console Outputs

**Validate mode (missing buildings - ERROR):**
```
❌ Error: User-defined network is missing nodes for 2 building(s):

  B1004
  B1005

Resolution options:
  1. Add these building nodes to your network layout
  2. Use 'augment' mode to automatically add missing buildings
  3. Use 'filter' mode for exact match (add missing + remove extras)
  4. Update connected-buildings parameter to match your network
```

**Augment mode (adding buildings):**
```
  ⓘ Augment mode: Adding 2 missing building(s)...
  Augmenting user network with 2 missing building(s)...
    - Buildings to add: B1004, B1005
  Step 1/3: Creating potential network graph...
  Step 2/3: Optimising network layout using Steiner tree algorithm...
  Step 3/3: Merging augmented edges/nodes with user network...
  ✓ Augmentation complete:
    - Added 2 new node(s)
    - Added 5 new edge(s)
    - Total network: 15 nodes, 20 edges
```

**Filter mode (removing buildings):**
```
  ⚠️  WARNING: FILTER MODE - Network will be modified!
  Network has 2 extra building(s) that will be REMOVED: B1004, B1005

  Filtering network to 3 building(s)...
    ✓ Removed 2 node(s) and 5 edge(s)
    ✓ Final network: 10 nodes, 15 edges
```

**Augment mode without auto-modify:**
```
  ❌ Error: Augment mode requires auto-modify-network=true to add missing buildings.
    Missing buildings: B1004, B1005
  Resolution: Set auto-modify-network=true or use validate mode.
```

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

### Street Cleaning Notes
- `snap_endpoints_to_nearby_lines` now explodes `MultiLineString` geometries to individual `LineString`s at function entry to ensure safe access to `.coords` and consistent endpoint handling.
- All coordinates are coerced to `(float, float)` tuples before constructing `LineString` during snapping/splitting to avoid mixed sequence types.

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

## Configuration Parameters

### snap-tolerance
**Default:** `0.5m` (SNAP_TOLERANCE constant when left blank)
**Range:** `0.3-2.0m` typical
**Purpose:** Maximum distance to snap near-miss street endpoints and building connections

**Validation:** Warnings issued if:
- `snap_tolerance > 0.25 * median_segment_length` (may distort short segments)
- `snap_tolerance > 2.0 * typical_endpoint_gap` (may connect unrelated segments)

**Guidelines:**
- Dense urban networks (short segments): Use lower values (0.3-0.5m)
- Sparse suburban networks (long segments): Can use higher values (0.5-2.0m)
- Leave blank for default unless you observe topology issues
- Check warnings during street network cleaning phase

### connection-candidates
**Default:** `3` (balanced quality/speed)
**Range:** `1-5`
**Purpose:** Number of nearest street edges to consider per building

**Performance tradeoffs:**
- `k=1`: Fastest (greedy nearest), locally optimal, may miss better global solutions
- `k=3`: Balanced (default), ~3-5x slower than k=1, significantly better network quality
- `k=5`: Best quality, ~10-25x slower than k=1, diminishing returns beyond k=3

**Runtime scaling:** O(|B| × |S| × k) where B=buildings, S=streets
- 100 buildings × 500 streets: k=1 (~1s), k=3 (~3-5s), k=5 (~10-15s)
- 1000 buildings × 2000 streets: k=1 (~10s), k=3 (~30-50s), k=5 (~100-250s)

**Note:** Only works with Kou algorithm. Mehlhorn always uses k=1 (greedy).

## Alternative Steiner/MST Approaches

### Current Implementation: Kou's Metric Closure Algorithm
**How it works:**
1. Build complete graph on terminals (buildings) using shortest paths through street network
2. Compute MST on this metric closure graph
3. Expand MST edges back to shortest paths in original network
4. Remove cycles and redundant edges

**Pros:** Good quality, handles k-nearest candidates, O(|S||V|²) complexity
**Cons:** Slower for large networks, not exact optimal

### Alternative 1: Multi-Source Dijkstra (Approximation)
**Idea:** Start from all terminals simultaneously, grow shortest-path trees until they meet
**Pros:** Faster (O(|E|+|V|log|V|)), simpler implementation
**Cons:** Lower quality than metric closure, doesn't handle k-nearest candidates
**Use case:** Very large networks (>5000 buildings) where speed is critical

**Implementation sketch:**
```python
def multi_source_steiner(graph, terminals):
    import heapq
    
    # Priority queue: (distance, node, source_terminal)
    pq = [(0, t, t) for t in terminals]
    heapq.heapify(pq)
    
    visited = set()
    tree_edges = []
    
    while pq and len(visited) < len(graph.nodes()):
        dist, node, source = heapq.heappop(pq)
        
        if node in visited:
            continue
        
        visited.add(node)
        if node != source:
            tree_edges.append((source, node))
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                edge_weight = graph[node][neighbor]['weight']
                heapq.heappush(pq, (dist + edge_weight, neighbor, node))
    
    return tree_edges
```

### Alternative 2: Exact ILP Formulation (Small Networks)
**Idea:** Formulate as Integer Linear Program, solve with CPLEX/Gurobi
**Pros:** Provably optimal solution
**Cons:** NP-hard, only feasible for <100 terminals, requires commercial solver
**Use case:** Critical infrastructure where optimality is essential and network is small

**Formulation:**
- Binary variable `x_e` for each edge e (1 if in tree, 0 otherwise)
- Minimize: Σ(weight_e × x_e) over all edges
- Constraints:
  - Σ(x_e) = |V| - 1 (tree property)
  - For each terminal pair (s, t): flow(s→t) ≥ 1 (connectivity)
  - Subtour elimination constraints

### Alternative 3: MST with Terminal Preference Heuristic
**Idea:** Weight edges adjacent to terminals higher, then compute standard MST
**Pros:** Very fast (O(|E|log|V|)), simple, often good enough
**Cons:** Heuristic, no quality guarantees, ignores Steiner nodes

**Implementation sketch:**
```python
def terminal_weighted_mst(graph, terminals):
    # Penalize edges far from terminals
    for u, v, data in graph.edges(data=True):
        base_weight = data['weight']
        # Increase weight if both endpoints are non-terminals
        if u not in terminals and v not in terminals:
            data['mst_weight'] = base_weight * 1.5
        else:
            data['mst_weight'] = base_weight
    
    # Compute MST with adjusted weights
    mst = nx.minimum_spanning_tree(graph, weight='mst_weight')
    return mst
```

### Alternative 4: Iterative MST Refinement
**Idea:** Start with Kou's solution, iteratively remove high-cost Steiner nodes
**Pros:** Improves over Kou, still fast
**Cons:** May converge to local minimum

**Steps:**
1. Compute initial Steiner tree with Kou
2. For each Steiner node v with degree=2:
   - Check if removing v and connecting its neighbors directly reduces cost
   - If yes, apply change
3. Repeat until no improvements found

### When to Use Which Algorithm

| Network Size | Terminals | Quality Need | Recommended Algorithm | Expected Runtime |
|-------------|-----------|--------------|----------------------|------------------|
| <500 streets | <50 | Critical | Exact ILP | 1-60 seconds |
| <2000 streets | <500 | High | Kou k=3-5 | 10-120 seconds |
| <2000 streets | <500 | Medium | Kou k=1-3 | 1-30 seconds |
| >5000 streets | >1000 | Medium | Kou k=1 or Mehlhorn | 10-60 seconds |
| >10000 streets | >2000 | Fast | Multi-source Dijkstra | <30 seconds |

### Future Improvements

**Priority 1: Adaptive k selection**
- Auto-detect network density (buildings per street segment)
- Use k=5 for sparse networks, k=1 for dense networks
- Dynamically adjust based on runtime budget

**Priority 2: Spatial partitioning for large networks**
- Divide network into quadtree/grid cells
- Solve Steiner problem per cell independently
- Merge solutions at cell boundaries
- Enables parallelization and linear scaling

**Priority 3: Local search refinement**
- After Kou, apply 2-opt/3-opt moves on Steiner nodes
- Swap Steiner node positions to reduce total length
- Typically 5-15% improvement for marginal cost

**Priority 4: Machine learning guided search**
- Train model to predict good k values based on network features
- Learn network density patterns that benefit from higher k
- Avoid expensive exploration on networks where k=1 is near-optimal

## Constants
- `SHAPEFILE_TOLERANCE = 6` - Decimal places (1 micrometer precision)
- `SNAP_TOLERANCE = 0.5` - Meters for snapping near-miss connections (configurable via snap-tolerance parameter)

## Testing
Tests are in `cea/tests/test_network_layout_integration.py`

## Related Files
- `connectivity_potential.py` - Main network creation, `create_terminals()` for building connections
- `graph_utils.py` - Conversion utilities (gdf_to_nx, nx_to_gdf, normalize_*)
- `optimization_new/user_network_loader.py` - User network loading, validation, and augmentation
  - `augment_user_network_with_buildings()` - Main augmentation function
  - `validate_network_covers_district_buildings()` - Validation with strict/lenient modes
  - `load_user_defined_network()` - Handles shapefiles and GeoJSON
- `optimization_new/network.py` - Uses graph with building terminal metadata
- `main.py` - Orchestrates workflow, integrates augmentation logic
- `steiner_spanning_tree.py` - Contains `add_plant_close_to_anchor()` for plant creation, `calc_steiner_spanning_tree()` used by augmentation
