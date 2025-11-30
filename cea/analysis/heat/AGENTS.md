# Anthropogenic Heat Assessment

## Main API

**`anthropogenic_heat_main(locator, config) → None`** - Calculate heat rejection from energy systems

**`calculate_standalone_heat_rejection(locator, config, network_types) → dict`** - Building-level heat

**`calculate_network_heat_rejection(locator, config, network_type, network_name, standalone_results) → dict`** - District plant heat

## Key Concepts

**Anthropogenic Heat** = Heat_Rejection + Electricity_for_Heat_Rejection

- **Heat Rejection**: Waste heat from condenser, flue gas, etc. (kWh)
- **Electricity for Heat Rejection**: Cooling tower fans, pumps (kWh)
- **Total**: Both components added together

**Formula (from `cooling_tower.py:22-39`)**:
```python
# Chiller condenser heat
q_condenser_kW = q_cooling_kW * (1 + 1/COP)

# Cooling tower auxiliary power (fans, pumps)
p_fan_kW = q_condenser_kW * aux_power_fraction  # ~2-5% typically

# Total anthropogenic heat
q_anthropogenic_kW = q_condenser_kW + p_fan_kW
```

## Data Flow

```
Building Demand (8760 hours)
    ↓
Domain.buildings[i].stand_alone_supply_system
    ↓
SupplySystem.heat_rejection → Dict[str, pd.Series]
    ↓ (energy carrier → time series)
    │
    ├→ 'T_AIR_20C': [h1, h2, ..., h8760]  # Air-based rejection
    ├→ 'T_AIR_ODB': [h1, h2, ..., h8760]  # Outdoor air rejection
    └→ Total = sum(all carriers)
         ↓
    Annual_MWh = sum(8760 hours) / 1000
    Peak_kW = max(8760 hours)
```

## Key Patterns

### Building-Level Heat Rejection

```python
# Extract from Domain (already calculated by optimization-new)
domain = Domain(config, locator)
for building in domain.buildings:
    heat_rejection = building.stand_alone_supply_system.heat_rejection
    # Dict[energy_carrier_code, pd.Series of 8760 hours]

    annual_total = sum([series.sum() for series in heat_rejection.values()])
    combined_hourly = pd.concat(list(heat_rejection.values()), axis=1).sum(axis=1)
    peak_kw = combined_hourly.max()
```

### District Network Heat Rejection

```python
# Create network supply system
supply_system = create_network_supply_system(locator, config, network_type, ...)
total_heat_rejection = supply_system.heat_rejection

# Multiple plants - split equally
num_plants = len(plant_nodes)
plant_heat_annual = total_annual / num_plants
plant_heat_hourly = total_hourly / num_plants
```

### Spatial Output (Coordinates)

```python
# Building coordinates from Domain
building.geometry.centroid → (x, y)

# Plant coordinates from network layout
nodes_gdf = gpd.read_file(locator.get_network_layout_nodes_shapefile(...))
plant_nodes = nodes_gdf[nodes_gdf['Type'].str.contains('PLANT')]
x, y = plant_node.geometry.x, plant_node.geometry.y
```

## Output Files

### 1. `heat_rejection_buildings.csv` (Summary)
```csv
name, type, GFA_m2, x_coord, y_coord,
heat_rejection_annual_MWh, peak_heat_rejection_kW, peak_datetime, scale
```

**Rows**:
- Buildings: One row per building with `type='building'`
- Plants: One row per plant node with `type='plant'`

**Key columns**:
- `type`: 'building' or 'plant'
- `scale`: 'BUILDING' or 'DISTRICT'
- `x_coord, y_coord`: Spatial location for heatmaps

### 2. `heat_rejection_hourly_spatial.csv` (For Heatmaps)
```csv
name, type, x_coord, y_coord, DATE, Heat_rejection_kW
```

**Size**: 8760 rows × number of buildings/plants

**Usage**:
- Load into QGIS with temporal controller
- Animate hourly heat rejection
- Filter by `type` for buildings-only or plants-only views

### 3. `heat_rejection_components.csv` (Detailed - Future)
```csv
name, network_type, service, component_code, energy_carrier,
heat_rejection_annual_MWh, peak_heat_rejection_kW, scale
```

Currently placeholder - will extract from `heat_rejection_by_carrier`

## 6-Case Building Connectivity Logic

**Same as system-costs**:

| Case | Network Status | Heat Rejection Calculated |
|------|----------------|--------------------------|
| 1 | Standalone (no network) | All services (building-scale) |
| 2 | In network | From network (no building heat) |
| 3 | Not in network | All services (fallback to standalone) |
| 4 | Both DC & DH | None (all from networks) |
| 5 | DC only | Heating & DHW (building-scale) |
| 6 | DH only | Cooling (building-scale) |

**Implementation**: Uses same `filter_supply_code_by_scale()` logic as system-costs

## ✅ DO

```python
# Extract heat rejection from existing optimization-new objects
heat_rejection = supply_system.heat_rejection  # Dict already populated

# Combine all energy carriers for totals
total_annual = sum([series.sum() for series in heat_rejection.values()])
combined_hourly = pd.concat(list(heat_rejection.values()), axis=1).sum(axis=1)

# Split multiple plants equally
plant_heat = total_heat / len(plant_nodes)

# Get coordinates from geometry
x, y = geometry.centroid.x, geometry.centroid.y
```

## ❌ DON'T

```python
# Don't recalculate heat rejection - it's already in supply_system
# Don't allocate plant heat to buildings - keep at plant location
# Don't create new equations - reuse optimization-new calculations
# Don't forget to divide by 1000 to convert kWh → MWh for output
```

## Multiple Plants Handling

When a network has multiple PLANT nodes:

1. **Detect plants**: Read `nodes.shp` and filter `Type == 'PLANT'`
2. **Calculate total**: One supply system for entire network
3. **Split equally**: `plant_heat = total_heat / num_plants`
4. **Assign coordinates**: Each plant gets its own (x, y) from nodes.shp

**Output example**:
```csv
validation_DC_plant_001, plant, 103.860, 1.295, 925.2, 310.2, DISTRICT
validation_DC_plant_002, plant, 103.865, 1.298, 925.2, 310.2, DISTRICT
```

## Energy Carrier Classification

**Releasable environmental carriers** (from `supplySystemStructure.py:282-297`):
- Air-based thermal carriers: `T_AIR_20C`, `T_AIR_ODB`, etc.
- These represent heat rejected to outdoor air
- Automatically tracked by `SupplySystem._add_to_heat_rejection()`

**Not included** (by design):
- Grid exports: Electrical energy exported, not heat rejection
- Infinite carriers: Fuel supplies, not environmental outputs

## Related Files

- `cea/optimization_new/supplySystem.py:58,398-409` - Heat rejection tracking
- `cea/technologies/cooling_tower.py:22-39` - Anthropogenic heat calculation
- `cea/analysis/costs/supply_costs.py` - Similar structure (costs vs. heat)
- `cea/technologies/network_layout/` - Plant node operations
