# Network Layout

## Purpose
Build thermal network connectivity graphs by connecting buildings to street networks while preserving curved geometries and maintaining coordinate precision.

## Main API

### `calc_connectivity_network_with_geometry(streets_gdf, buildings_gdf) → nx.Graph`
**Returns:** NetworkX graph with preserved geometries and metadata
- **Nodes:** `(x, y)` tuples normalized to 6 decimal places
- **Edges:** `geometry` (curved LineStrings), `weight` (length)
- **Metadata:** `graph.graph['building_terminals']` (dict: building_id → node coords), `graph.graph['crs']`, `graph.graph['coord_precision']`

**Convert to GeoDataFrame:**
```python
edges_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)
```

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
```

## Key Helper Functions

### `gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True)`
Convert GeoDataFrame → NetworkX graph
- Handles Point (lone nodes), LineString, MultiLineString
- Set `preserve_geometry=True` to store full geometries in edge attributes
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
2. **`create_terminals()`** - Connect each building to nearest street point with normalized coordinates
3. **`calc_connectivity_network_with_geometry()`** - Build final graph with metadata

## Common Patterns

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
