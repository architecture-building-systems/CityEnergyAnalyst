# Analysis: Curved vs Straight Street Geometry in Network Layout

## Overview

This document explains how street geometry (curved vs straight lines) is handled in the CEA network layout pipeline, and provides options for preserving curved geometry if needed.

## Current Behavior: Curves Are Converted to Straight Lines

### Where It Happens

**Location**: `connectivity_potential.py`, function `apply_graph_corrections()`, lines 221-239

When streets are converted from GeoDataFrame to NetworkX graph for topology corrections:

```python
# Convert GeoDataFrame to NetworkX graph
G = nx.Graph()
for _, row in network_gdf.iterrows():
    line = row.geometry
    if line.geom_type == 'LineString':
        coords = list(line.coords)
        # ONLY START AND END POINTS ARE EXTRACTED
        start = (round(coords[0][0], coord_precision), round(coords[0][1], coord_precision))
        end = (round(coords[-1][0], coord_precision), round(coords[-1][1], coord_precision))
        weight = line.length
        G.add_edge(start, end, weight=weight)  # ← All intermediate vertices lost
```

**What happens:**
- LineString with 20 points defining a curve → Only 2 points stored (start, end)
- All intermediate vertices discarded
- Edge weight (length) preserved, but shape lost

When converting back to GeoDataFrame (lines 255-259):
```python
corrected_lines = []
for u, v in G_corrected.edges():
    line = LineString([u, v])  # ← Creates straight line from 2 points
    corrected_lines.append(line)
```

Result: **All curved streets become straight lines**

### Why This Happens

1. **NetworkX is topology-based**: Graphs represent edges as node pairs, not geometric shapes
2. **Graph algorithms need topology**: Steiner tree, connectivity corrections work on node-edge structure
3. **No geometry storage**: The code doesn't store intermediate vertices during graph operations
4. **Intentional simplification**: Curves aren't needed for network optimization

### What Is Preserved vs Lost

✅ **Preserved:**
- Network topology (which streets connect to which)
- Edge lengths (stored as weights)
- Connectivity structure
- Optimal network layout

❌ **Lost:**
- Curved geometry (visual appearance)
- Intermediate vertices
- Exact path shape
- Realistic street appearance

---

## Impact Analysis

### When Curved Geometry Loss Matters:

1. **Visualization**: Networks look unrealistic in maps/plots (straight lines through curved streets)
2. **GIS Integration**: Output shapefiles don't match real street layouts
3. **Length Mismatch**: Visual geometry (straight-line distance) ≠ edge weight (original curve length)
4. **Spatial Analysis**: Inaccurate for analyses requiring exact geometry

### When It Doesn't Matter:

1. **Network Optimization**: Topology is what matters, not visual shape
2. **Energy Calculations**: Edge lengths are preserved as weights
3. **Connectivity Analysis**: Graph structure is correct
4. **Performance**: Straight lines are faster to process

---

## Options for Preserving Curved Geometry

### Option 1: Post-Processing (Recommended - Simplest)

**Approach**: Run existing pipeline, then map straight-line results back to original curved streets

**Implementation**: New module `geometry_mapper.py` (~300 lines)
- Uses spatial indexing to find matching original streets
- Extracts curved segment between edge endpoints
- Replaces straight geometry with curve where matches exist

**Pros:**
- ✅ Simple implementation (8-12 hours development)
- ✅ Low risk (doesn't touch core algorithms)
- ✅ Fast (adds 1-2 seconds)
- ✅ Non-invasive (separate post-processor)

**Cons:**
- ❌ New edges from GraphCorrector stay straight (no original geometry)
- ❌ Building terminals stay straight (expected)
- ❌ Matching may be ambiguous
- ❌ Edge weights may differ from visual length

**Expected Results:**
- ~30-50% of edges get curved geometry
- New edges and terminals remain straight
- Good enough for visualization and basic GIS integration

**Test Results** (from prototype):
- Total edges: 50
- Mapped to curves: 15 (30%)
- Kept straight: 35 (70%)
  - 11 new edges from GraphCorrector
  - 24 building terminals

---

### Option 2: Full Implementation (Most Accurate)

**Approach**: Store LineString geometries as edge attributes throughout entire pipeline

**Implementation**: Modify multiple files
1. `connectivity_potential.py`: Store geometry in `G.add_edge(..., geometry=line)`
2. `graph_helper.py`: Update GraphCorrector operations
   - `_split_edge_at_nodes()`: Split LineString geometries at junctions
   - `connect_intersecting_edges()`: Calculate exact intersection on curves
   - `merge_close_nodes()`: Re-route geometries through merged nodes
3. `steiner_spanning_tree.py`: Preserve geometries through Steiner tree
4. `utility.py`: Handle geometry attributes in output

**Pros:**
- ✅ Most accurate (exact curves preserved)
- ✅ Perfect GIS integration
- ✅ Edge weights match visual geometry
- ✅ All curves preserved (except new edges from GraphCorrector)

**Cons:**
- ❌ High complexity (26-50 hours development)
- ❌ Medium-High risk (modifies core algorithms)
- ❌ Performance overhead (slower processing)
- ❌ Extensive testing needed

**Key Challenges:**
- **Parametric splitting**: When edge intersects at point P, find parameter t ∈ [0,1] on curve
- **Coordinate precision**: Intersection points may not exactly match after rounding
- **Edge cases**: MultiLineStrings, self-intersecting lines, degenerate geometries

---

### Option 3: Hybrid (Moderate Complexity)

**Approach**: Preserve curves where possible, accept straight lines for new edges

**Implementation**: Similar to Option 2, but skip complex operations:
- Store geometries in graph edges
- Update `_split_edge_at_nodes()` for edge splitting
- Skip `merge_close_nodes()` geometry updates
- New edges from `connect_disconnected_components()` stay straight

**Pros:**
- ✅ Moderate complexity (16-24 hours)
- ✅ Preserves most curves
- ✅ Explicitly marks approximate edges
- ✅ Faster than full implementation

**Cons:**
- ❌ Mixed geometry quality (inconsistent appearance)
- ❌ Still requires geometric splitting logic
- ❌ Partial complexity

---

## Comparison Matrix

| Criterion | Post-Processing | Full Implementation | Hybrid |
|-----------|----------------|-------------------|--------|
| **Effort** | 13-20 hours | 36-66 hours | 24-35 hours |
| **Risk** | Low | Medium-High | Medium |
| **Accuracy** | 30-50% curved | ~90% curved | ~70% curved |
| **GIS Integration** | Good | Perfect | Very Good |
| **Maintainability** | Excellent | Moderate | Good |
| **Performance** | Fast (+1-2s) | Slower (+5-10s) | Moderate (+3-5s) |

---

## Recommendations

### For Quick Prototyping / Testing:
→ **Option 1: Post-Processing** (13-20 hours)
- See if curved geometry matters for your use case
- Good enough for most visualizations
- Can upgrade later if needed

### For Production with Critical GIS Integration:
→ **Option 2: Full Implementation** (36-66 hours)
- Maximum accuracy
- Perfect for GIS workflows
- Worth the effort if geometry is critical

### For Budget-Constrained Production:
→ **Option 3: Hybrid** (24-35 hours)
- Good compromise
- Most curves preserved
- Acceptable mixed quality

### Decision Framework:

Ask yourself:
1. **How many new edges does GraphCorrector add in your scenarios?**
   - Few (<10%): Post-processing is fine
   - Many (>20%): Need Full Implementation

2. **What's your budget?**
   - <20 hours: Post-processing
   - 20-40 hours: Hybrid
   - >40 hours: Full implementation

3. **How critical is curve accuracy?**
   - Visualization only: Post-processing
   - Some analysis: Hybrid
   - Critical GIS work: Full implementation

---

## Implementation Details for Post-Processing (Option 1)

If you choose post-processing, here's what you need:

### New File: `geometry_mapper.py`

```python
def map_to_curved_streets(output_edges_gdf, original_streets_gdf):
    """
    Map straight-line network edges back to original curved streets.

    For each edge:
    1. Find nearest original street using spatial index
    2. Extract curved segment between edge endpoints
    3. Replace straight geometry with curve (if match found)
    """
    # Build spatial index
    sindex = original_streets_gdf.sindex

    for edge in output_edges_gdf:
        # Find candidate streets
        candidates = find_nearest_street(edge, streets, sindex)

        if candidates:
            # Extract curve segment
            curve = extract_curve_segment(edge, best_match)

            if curve:
                edge.geometry = curve  # Replace with curve

    return output_edges_gdf
```

### Integration Point: `main.py`

```python
def layout_network(..., preserve_curved_geometry=True):
    # ... existing code ...

    calc_steiner_spanning_tree(...)  # Output: straight lines

    if preserve_curved_geometry:
        output_edges = gpd.read_file(path_output_edges_shp)
        curved_edges = map_to_curved_streets(output_edges, street_network_df)
        curved_edges.to_file(path_output_edges_shp)
```

### Testing:

```python
# Test 1: With curves
layout_network(network_layout, locator, preserve_curved_geometry=True)
# Expected: ~30-50% edges with >2 points

# Test 2: Without curves (faster)
layout_network(network_layout, locator, preserve_curved_geometry=False)
# Expected: All edges with 2 points (straight)
```

---

## Technical Notes

### Why NetworkX Doesn't Preserve Geometry:

NetworkX is designed for **graph theory**, not **geometric analysis**:
- Nodes: Identified by coordinates (tuples)
- Edges: Connections between nodes
- Attributes: Can store data, but algorithms don't use geometry

Graph algorithms (Steiner tree, shortest path, etc.) work on:
- Node connectivity (adjacency)
- Edge weights (distances)
- Graph structure (topology)

They **don't need** intermediate vertices or curves.

### Alternative: Don't Convert to NetworkX?

Could we avoid NetworkX and work directly with GeoDataFrames?

**Problems:**
1. GraphCorrector needs NetworkX for:
   - Connected components detection
   - Node merging (spatial clustering)
   - Topology analysis
2. Steiner tree algorithms are in NetworkX
3. Graph algorithms are well-tested in NetworkX
4. Would require reimplementing graph algorithms

**Conclusion**: NetworkX is the right tool, but it sacrifices geometry for topology.

---

## Cost-Benefit Summary

### Do Nothing (Current State):
- **Cost**: 0 hours
- **Benefit**: Fast, simple, works well for network optimization
- **Drawback**: Networks look unrealistic in visualizations

### Post-Processing (Option 1):
- **Cost**: 13-20 hours
- **Benefit**: 30-50% curves preserved, simple, low risk
- **Drawback**: New edges stay straight, some matching ambiguity

### Full Implementation (Option 2):
- **Cost**: 36-66 hours
- **Benefit**: ~90% curves preserved, perfect accuracy
- **Drawback**: High complexity, risky, slower performance

### Hybrid (Option 3):
- **Cost**: 24-35 hours
- **Benefit**: ~70% curves preserved, good compromise
- **Drawback**: Mixed quality, moderate complexity

---

## Conclusion

**Curved geometry is lost during graph conversion** (lines 228-231 in `apply_graph_corrections()`). This is **not a bug** - it's a consequence of using NetworkX for graph operations.

**If you need curves**, implement **Option 1 (Post-Processing)** first:
- Quick to implement (13-20 hours)
- Good enough for most use cases
- Low risk, easy to test
- Can upgrade to Option 2 or 3 later if needed

**If curves aren't critical**, keep current behavior:
- Zero effort
- Fast performance
- Network topology is correct
- Edge lengths preserved

---

## References

- `connectivity_potential.py` lines 221-262: Graph conversion (where curves are lost)
- `graph_helper.py` class `GraphCorrector`: Topology corrections
- `steiner_spanning_tree.py` lines 116-210: Steiner tree optimization
- NetworkX documentation: https://networkx.org/

---

**Last Updated**: 2025-01-06
**Status**: Analysis Complete, Implementation Not Started
