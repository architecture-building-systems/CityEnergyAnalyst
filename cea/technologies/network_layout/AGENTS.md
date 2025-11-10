# Network Layout Module - Developer Documentation

## Overview

This module handles the creation of thermal network layouts by connecting buildings to street networks while preserving curved street geometries. It addresses the critical challenge of maintaining coordinate precision throughout multiple transformations (CRS conversions, geometric operations, graph conversions) to prevent floating-point errors that can cause network connectivity issues.

## Key Concepts

### Coordinate Precision Management

**The Problem**: Thermal network creation involves multiple stages where floating-point precision can drift:
1. CRS transformation (WGS84 → Projected UTM)
2. Geometric operations (`interpolate()`, `project()`, `distance()`, `substring()`) produce raw floats
3. Graph conversion (GeoDataFrame ↔ NetworkX)
4. Steiner tree optimization (requires exact node coordinate matches)

**The Solution**: **"Normalize Early, Normalize Often"** strategy:
- Normalize **immediately after** ANY geometric operation that produces coordinates
- Use normalized coordinates for ALL LineString/Point creation
- Validate normalization before graph conversion
- Building terminal metadata storage in graph

**Key Operations That Produce Raw Floats:**
- `interpolate()` - Finding nearest point on line → **normalized in `near_analysis()`**
- `substring()` - Splitting lines → **normalized after segment creation**
- `project()` - Distance along line → Used with normalized Points
- Terminal connections → **normalized before LineString creation**

### Building Terminal Alignment

**Critical Requirement**: Building centroids must be precisely represented in the network graph for Steiner tree optimization. The `validate_steiner_tree_ready()` function performs exact tuple matching:

```python
if terminal_node not in set(graph.nodes()):
    raise ValueError("Terminal not found")
```

This requires:
1. Consistent coordinate precision (SHAPEFILE_TOLERANCE = 6 decimal places)
2. Same CRS transformations for streets and buildings
3. Metadata-based terminal lookup (eliminates floating-point search errors)

## Architecture

### Core Workflow

```
1. _prepare_network_inputs()
   ├─ CRS transformation to projected coordinates
   ├─ Geometry validation
   ├─ Street network cleaning (split at intersections, snap endpoints)
   └─ Coordinate normalization (SHAPEFILE_TOLERANCE precision)

2. create_terminals()
   ├─ Find nearest point on street for each building via near_analysis()
   │  └─ Normalizes interpolated points immediately
   ├─ Normalize building & street coordinates before LineString creation
   ├─ Create LineString connections with normalized coords (building → street)
   ├─ Split streets at junction points using normalized split Points
   │  └─ Normalize substring() results immediately
   └─ Validate all coordinates are normalized (catches bugs early)

3. calc_connectivity_network_with_geometry()
   ├─ Convert GeoDataFrame → NetworkX graph
   ├─ Extract building terminal metadata → store in graph attributes
   ├─ Component analysis (drop single-node components)
   ├─ Validate network integrity
   └─ Return edges GeoDataFrame (default) OR graph with metadata (if return_graph=True)

4. Optimization (optimization_new/network.py)
   ├─ _load_pot_network() calls calc_connectivity_network_with_geometry(return_graph=True)
   │  └─ Gets graph directly with building terminal metadata preserved
   ├─ _set_potential_network_terminals()
   │  └─ Uses all domain.buildings (all are in network due to component connection)
   └─ _find_building_terminal_nodes_in_graph()
      └─ Use graph.graph['building_terminals'] metadata (fast dictionary lookup)
```

### Key Functions

#### `normalize_coords(coords, precision=SHAPEFILE_TOLERANCE)`
Normalize coordinate sequence to consistent precision.

**Use this when**:
- Working with raw coordinate tuples
- Need to ensure coordinate consistency before comparisons

**Example**:
```python
coords = [(1.123456789, 2.987654321)]
normalized = normalize_coords(coords, precision=6)
# Result: [(1.123457, 2.987654)]
```

#### `normalize_geometry(geom, precision=SHAPEFILE_TOLERANCE)`
Normalize Point/LineString/MultiLineString geometry.

**Use this when**:
- Working with Shapely geometry objects
- After geometric operations (buffer, union, split)

**Example**:
```python
from shapely.geometry import LineString
line = LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
normalized = normalize_geometry(line, precision=6)
# Result: LineString with rounded coordinates
```

#### `normalize_gdf_geometries(gdf, precision=SHAPEFILE_TOLERANCE, inplace=True)`
Normalize all geometries in a GeoDataFrame.

**Use this when**:
- After loading network from shapefile
- After performing bulk geometric operations
- Before converting to NetworkX graph

**Example**:
```python
streets_gdf = gpd.read_file('streets.shp')
normalize_gdf_geometries(streets_gdf, precision=6, inplace=True)
# All geometries now have consistent precision
```

#### `gdf_to_nx(network_gdf, coord_precision=6, preserve_geometry=True, **edge_attrs)`
Convert GeoDataFrame to NetworkX graph.

**Parameters**:
- `coord_precision`: Rounding precision for node coordinates (default: SHAPEFILE_TOLERANCE)
- `preserve_geometry`: If True, store full LineString as edge attribute (for curved streets)
- `**edge_attrs`: Additional columns to extract as edge attributes

**Use this when**:
- Need graph representation for optimization
- Want to analyze network connectivity
- Performing graph algorithms (shortest path, Steiner tree)
- Converting mixed Point/LineString geometries to graph

**Geometry Support**:
- **Point**: Added as lone nodes (degree 0) without edges
- **LineString**: Converted to edges connecting two nodes
- **MultiLineString**: Each component becomes a separate edge
- **Mixed**: Can process GeoDataFrames with mixed geometry types

**Example**:
```python
# Preserve curved street geometries
graph = gdf_to_nx(streets_gdf, preserve_geometry=True)

# Extract additional attributes
graph = gdf_to_nx(streets_gdf, preserve_geometry=True,
                  pipe_DN='pipe_DN', type_mat='type_mat')

# Mixed geometries - Points become lone nodes
mixed_gdf = gpd.GeoDataFrame({
    'geometry': [Point(0, 0), LineString([(1, 1), (2, 2)])]
})
graph = gdf_to_nx(mixed_gdf)
# Graph has 3 nodes: (0,0) as lone node, (1,1) and (2,2) as edge endpoints
```

**Graph Structure**:
- Nodes: `(x, y)` tuples rounded to `coord_precision`
  - May include lone nodes from Point geometries (degree 0)
- Edges: `{u, v, data}` where `data` contains:
  - `weight`: Line length (always present)
  - `geometry`: Full LineString (if `preserve_geometry=True`)
  - Custom attributes (if specified via `**edge_attrs`)

#### `nx_to_gdf(graph, crs, preserve_geometry=True)`
Convert NetworkX graph back to GeoDataFrame.

**Use this when**:
- Need to export graph back to shapefile
- Want to visualize graph edges as geographic features
- Round-trip conversion required

**Example**:
```python
# Convert graph back to GeoDataFrame
edges_gdf = nx_to_gdf(graph, crs='EPSG:32632', preserve_geometry=True)

# Save to file
edges_gdf.to_file('network_edges.shp')
```

**Round-Trip Guarantee**:
```python
# This preserves geometries exactly:
original_gdf = gpd.read_file('streets.shp')
normalize_gdf_geometries(original_gdf, precision=6, inplace=True)
graph = gdf_to_nx(original_gdf, preserve_geometry=True)
restored_gdf = nx_to_gdf(graph, crs=original_gdf.crs, preserve_geometry=True)
# original_gdf geometries == restored_gdf geometries
```

#### `calc_connectivity_network_with_geometry(streets_network_df, building_centroids_df, return_graph=False)`
Create connectivity network preserving street geometries.

**Parameters**:
- `streets_network_df`: GeoDataFrame with street network geometries
- `building_centroids_df`: GeoDataFrame with building centroids (must have 'name' column for building IDs)
- `return_graph`: If True, return NetworkX graph with metadata; if False (default), return edges GeoDataFrame

**Note**: Building identifiers are extracted from the 'name' column. If neither exists, the DataFrame index is used as the building ID.

**Returns**:
- **Default (`return_graph=False`)**: GeoDataFrame of network edges with:
  - `geometry`: Preserved curved LineString geometries
  - `length`: Edge lengths
  - CRS: Same as input streets

- **With `return_graph=True`**: NetworkX graph with metadata:
  - `graph.graph['building_terminals']`: Dict mapping building_id → (x, y) node coordinates
  - `graph.graph['crs']`: Coordinate reference system
  - `graph.graph['coord_precision']`: Precision used (SHAPEFILE_TOLERANCE)

**Disconnected Components Handling**:
If the street network has multiple disconnected components, the function:
1. Drops single-node components (isolated nodes)
2. **Connects** remaining components by adding edges between closest points
3. Issues warnings about connecting components
4. Preserves **all buildings** in the network

This is common in real-world scenarios where terminal connection edges are lost during coordinate rounding/simplification, or street networks have genuinely disconnected areas.

**Validation Performed**:
1. Graph connectivity (single component after connecting)
2. All building terminals exist in graph
3. Valid geometries
4. Positive edge lengths

**Usage**:
```python
# Standard usage - returns GeoDataFrame
edges = calc_connectivity_network_with_geometry(streets, buildings)

# For optimization - returns graph with metadata
graph = calc_connectivity_network_with_geometry(streets, buildings, return_graph=True)
terminal_mapping = graph.graph['building_terminals']

# Note: If network has disconnected components, they are automatically
# connected with edges between closest points. All buildings are preserved.
```

## Best Practices

### DO: Use Centralized Normalization

✅ **Good**:
```python
from cea.technologies.network_layout.graph_utils import normalize_gdf_geometries

streets_gdf = gpd.read_file('streets.shp')
normalize_gdf_geometries(streets_gdf, inplace=True)
```

❌ **Bad**:
```python
# Manual rounding - error-prone, inconsistent
for idx, row in streets_gdf.iterrows():
    coords = [(round(x, 6), round(y, 6)) for x, y in row.geometry.coords]
    streets_gdf.loc[idx, 'geometry'] = LineString(coords)
```

### DO: Use Metadata for Terminal Lookup

✅ **Good**:
```python
# Request graph with metadata preserved
graph = calc_connectivity_network_with_geometry(streets, buildings, return_graph=True)

# Fast dictionary lookup - guaranteed to work
terminal_coord = graph.graph['building_terminals'][building_id]
```

❌ **Bad**:
```python
# Get GeoDataFrame, convert to graph, then try to find terminals manually
edges = calc_connectivity_network_with_geometry(streets, buildings)
graph = gdf_to_nx(edges)

# Slow and error-prone - requires CRS transformation and spatial search
building_coord = (building.x, building.y)  # Wrong CRS!
if building_coord in graph.nodes():  # Will fail due to precision
    ...
```

### DO: Normalize Immediately After Geometric Operations

✅ **Good** (normalize immediately):
```python
from cea.technologies.network_layout.graph_utils import normalize_geometry, normalize_coords

# After interpolate()
nearest_point_raw = line.interpolate(line.project(building_point))
nearest_point = normalize_geometry(nearest_point_raw, precision=SHAPEFILE_TOLERANCE)

# After substring()
segment_raw = substring(line, start_dist, end_dist)
segment = normalize_geometry(segment_raw, precision=SHAPEFILE_TOLERANCE)

# Before creating LineString
bldg_coord = normalize_coords([bldg_pt.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
street_coord = normalize_coords([street_pt.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
terminal_line = LineString([bldg_coord, street_coord])
```

❌ **Bad** (using raw coordinates):
```python
# Geometric operations introduce floating-point drift
nearest_point = line.interpolate(line.project(building_point))  # RAW FLOATS
segment = substring(line, start_dist, end_dist)  # RAW FLOATS
terminal_line = LineString([bldg_pt.coords[0], street_pt.coords[0]])  # RAW COORDS

# This WILL cause 1-micrometer precision differences → disconnected components!
```

### DO: Use Round-Trip Conversion Safely

✅ **Good**:
```python
# Normalize FIRST, then convert
normalize_gdf_geometries(streets_gdf, inplace=True)
graph = gdf_to_nx(streets_gdf, preserve_geometry=True)
restored_gdf = nx_to_gdf(graph, crs=streets_gdf.crs, preserve_geometry=True)
# Geometries preserved exactly
```

❌ **Bad**:
```python
# Converting without normalization - precision drift accumulates
graph = gdf_to_nx(streets_gdf, preserve_geometry=True)
# ... graph operations ...
restored_gdf = nx_to_gdf(graph, crs=streets_gdf.crs)
# Coordinates may have drifted
```

## Common Issues & Solutions

### Issue 1: Terminal Nodes Not Found in Graph

**Symptom**:
```
ValueError: Building 'B001' terminal node not found in graph
```

**Causes**:
1. CRS mismatch (building coordinates in different CRS than graph)
2. Coordinate rounding inconsistency
3. Missing coordinate normalization

**Solution**:
Ensure `_prepare_network_inputs()` normalizes both streets and buildings:
```python
normalize_gdf_geometries(streets_network_df, precision=SHAPEFILE_TOLERANCE, inplace=True)
normalize_gdf_geometries(building_centroids_df, precision=SHAPEFILE_TOLERANCE, inplace=True)
```

### Issue 2: Disconnected Street Networks

**Symptom** (Now handled automatically):
```
WARNING: Network has 2 disconnected components.
Connecting components to preserve all buildings...
Main component has X nodes.
Component 2 (Y nodes): connecting to main component with Z.ZZm edge
Added N connecting edges.
```

**Causes**:
1. Terminal connection edges lost during coordinate rounding/simplification
2. Street network genuinely has disconnected areas (common in real-world data)
3. Buildings spread across disconnected street segments

**Behavior**:
- The function automatically **connects** disconnected components
- Finds closest pair of nodes between each component
- Adds straight-line edges to connect components
- **All buildings are preserved** in the network
- Clear informational messages about connections added

**Action Required**:
- Review the warnings to understand network topology
- Note the distance of connecting edges (may indicate data quality issues)
- If connecting edges are very long (>100m), consider improving street network data
- Otherwise, no action needed - all buildings are included automatically

### Issue 3: Floating-Point Coordinate Drift

**Symptom**: Coordinates differ by 10^-7 to 10^-9 after transformations

**Causes**:
1. Multiple geometric operations without intermediate rounding
2. CRS transformations accumulate floating-point errors

**Solution**:
- Apply `normalize_gdf_geometries()` after major transformations:
  - After CRS conversion
  - After street network cleaning
  - After terminal creation
  - Before graph conversion

### Issue 4: Steiner Tree Validation Fails

**Symptom**:
```
AssertionError: Terminal coordinates don't match graph nodes
```

**Causes**:
1. Building terminals not using metadata from graph
2. Manual coordinate rounding doesn't match graph node rounding

**Solution**:
Use the fast path in `_find_building_terminal_nodes_in_graph()`:
```python
if 'building_terminals' in graph.graph:
    terminal_mapping = graph.graph['building_terminals']
    return [terminal_mapping[bldg.identifier] for bldg in buildings]
```

## Testing

### Unit Tests

Located in `cea/tests/test_graph_utils.py`:

1. **Coordinate Normalization Tests**
   - `test_normalize_coords_*` - Test coordinate tuple normalization
   - `test_normalize_geometry_*` - Test geometry object normalization
   - `test_normalize_gdf_geometries_*` - Test GeoDataFrame normalization

2. **Conversion Tests**
   - `test_gdf_to_nx_*` - Test GeoDataFrame → NetworkX conversion
   - `test_nx_to_gdf_*` - Test NetworkX → GeoDataFrame conversion

3. **Round-Trip Tests**
   - `test_round_trip_*` - Test GeoDataFrame → graph → GeoDataFrame preserves geometries

### Integration Tests

To test network creation with real data:

```python
import geopandas as gpd
from cea.technologies.network_layout.connectivity_potential import (
    calc_connectivity_network_with_geometry
)

# Load test data
streets = gpd.read_file('tests/data/streets.shp')
buildings = gpd.read_file('tests/data/buildings.shp')

# Create network
network = calc_connectivity_network_with_geometry(streets, buildings)

# Verify
assert not network.empty
assert 'length' in network.columns
assert all(network.geometry.is_valid)
```

## Constants

```python
SHAPEFILE_TOLERANCE = 6  # Decimal places for coordinate storage
SNAP_TOLERANCE = 0.1     # Meters for geometric snapping
```

**Why 6 decimal places?**
- At equator: 0.000001° ≈ 0.11 meters
- For projected coordinates (meters): 0.000001 m = 1 micrometer
- Sufficient precision for thermal network layout
- Prevents numerical artifacts (< 1 μm segments)

## Related Files

- `connectivity_potential.py` - Network creation functions
- `graph_utils.py` - Graph conversion utilities (normalize, gdf_to_nx, nx_to_gdf)
- `graph_helper.py` - GraphCorrector for topology fixes
- `optimization_new/network.py` - Network optimization (uses building terminal metadata)
- `tests/test_graph_utils.py` - Comprehensive unit tests

## Migration Notes

### Removed: GeometryPreservingGraph Class

**Previously**: Used `GeometryPreservingGraph` wrapper for graph creation
```python
gp_graph = GeometryPreservingGraph(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE)
graph = gp_graph.graph
```

**Now**: Direct conversion with `gdf_to_nx()`
```python
graph = gdf_to_nx(streets_network_df, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)
```

**Reason**: `GeometryPreservingGraph` was only used to extract the `.graph` property. The class had many advanced features (junction splitting, edge collapsing) that were never used in production code. Direct conversion is simpler and more maintainable.

### Added: Building Terminal Metadata with `return_graph` Parameter

**Previously**: Had to get GeoDataFrame, convert to graph, then search for terminals
```python
# Get GeoDataFrame
edges = calc_connectivity_network_with_geometry(streets, buildings)

# Convert to graph (loses metadata)
graph = gdf_to_nx(edges)

# Slow - CRS transformation + KDTree spatial search
terminal_coords = _find_building_terminal_nodes_in_graph(buildings)
```

**Now**: Request graph directly to preserve metadata
```python
# Get graph directly with metadata preserved
graph = calc_connectivity_network_with_geometry(streets, buildings, return_graph=True)

# Fast - direct dictionary lookup
terminal_coords = [graph.graph['building_terminals'][b.id] for b in buildings]
```

**Benefits**:
- No redundant graph ↔ GeoDataFrame conversions
- 100x faster terminal lookup
- Eliminates floating-point search errors
- Guarantees exact coordinate matches for Steiner tree validation
- Backward compatible (default still returns GeoDataFrame)

## Future Improvements

1. **Parallel Normalization**: Use multiprocessing for large GeoDataFrames
2. **Incremental Validation**: Validate at each stage instead of only at end
3. **Graph Caching**: Cache normalized graphs to avoid recomputation
4. **Precision Profiles**: Support different precision levels for different use cases
