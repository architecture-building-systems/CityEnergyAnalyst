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
name,type,x_coord,y_coord,heat_rejection_annual_MWh,peak_heat_rejection_kW,peak_datetime,scale
B1001,building,374252.82,146016.62,0.47,0.14,2013-01-02 06:00:00,BUILDING
crycry_DC_plant_001,plant,374305.97,146155.99,11537.03,2333.37,2011-05-08 16:00:00,DISTRICT
```

**Rows**:
- Buildings: One row per building with `type='building'`, `scale='BUILDING'`
- Plants: One row per plant node with `type='plant'`, `scale='DISTRICT'`

**Key columns**:
- `type`: 'building' or 'plant'
- `scale`: 'BUILDING' or 'DISTRICT'
- `x_coord, y_coord`: Spatial location for map layers
- **No GFA column** - GFA calculated from zone geometry when needed

### 2. Individual Hourly Files: `{name}.csv`
One file per building/plant in `/outputs/data/heat/`:
```csv
DATE,heat_rejection_kW
2020-01-01 00:00:00,1115.34
2020-01-01 01:00:00,1082.71
...
```

**Size**: 8760 rows per file (leap day removed)

**Usage**:
- Time series plotting (district-level)
- Map layer temporal animation
- Building-specific analysis

### 3. `heat_rejection_components.csv` (Component Breakdown)
```csv
name,type,component_code,component_type,placement,capacity_kW,heat_rejection_annual_MWh,peak_heat_rejection_kW,scale
B1014,building,CH2,VapourCompressionChiller,primary,650.398,,,BUILDING
B1014,building,CT2,CoolingTower,tertiary,773.11,,,BUILDING
B1014,building,T25A,energy_carrier,heat_rejection,0.0,3509.29,797.47,BUILDING
```

**Rows per building**:
- Component rows: Equipment capacity (component_type = equipment class)
- Energy carrier rows: Heat rejection by carrier (component_type = 'energy_carrier')

**Energy carrier codes**:
- `T25A`: Cooling heat rejection (from chillers/cooling towers)
- `T100A`: DHW heat rejection (from boilers/high-temp systems)

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

## Visualisation Integration

### Plot Configuration: `[plots-heat-rejection]`

**Single metric only**: `heat_rejection`
```ini
y-metric-to-plot = heat_rejection
y-metric-to-plot.type = ChoiceParameter  # Single choice
y-metric-to-plot.choices = heat_rejection

y-normalised-by = no_normalisation
y-normalised-by.type = ChoiceParameter
y-normalised-by.choices = no_normalisation, gross_floor_area, conditioned_floor_area
```

### Normalisation Logic

**For buildings**:
```python
# GFA from zone geometry
gfa_m2 = zone.loc[building_name].geometry.area * zone.loc[building_name].floors_ag
normalised = heat_rejection_MWh / gfa_m2 * 1000  # kWh/m²
```

**For plants (district-scale)**:
```python
# Get all buildings connected to this network
connected_buildings = network.get_consumer_buildings()
total_gfa = sum(zone.loc[bid].geometry.area * zone.loc[bid].floors_ag for bid in connected_buildings)

# Divide by number of plants
plant_gfa = total_gfa / num_plants
normalised = heat_rejection_MWh / plant_gfa * 1000  # kWh/m²
```

✅ **DO**: Treat plants as "buildings" with serviced GFA for normalisation
❌ **DON'T**: Use plant footprint area - meaningless for district systems

### Data Loader Integration

Add to `cea/visualisation/a_data_loader.py`:
```python
dict_plot_metrics_cea_feature = {
    'demand': demand_metrics,
    'heat-rejection': ['heat_rejection'],  # Single metric
    # ...
}

dict_plot_analytics_cea_feature = {
    'demand': demand_analytics,
    'heat-rejection': [],  # No analytics metrics
    # ...
}
```

### Map Layer Integration

When user selects "Anthropogenic Heat Rejection" from map dropdown:
1. Load `heat_rejection_buildings.csv`
2. Display points colored by `heat_rejection_annual_MWh`
3. Distinguish buildings (circles) from plants (stars/squares)
4. Set plot context: `{"feature": "heat-rejection"}`
5. Plot form automatically updates with heat rejection config options

## Related Files

- `cea/optimization_new/supplySystem.py:58,398-409` - Heat rejection tracking
- `cea/technologies/cooling_tower.py:22-39` - Anthropogenic heat calculation
- `cea/analysis/costs/supply_costs.py` - Similar structure (costs vs. heat)
- `cea/technologies/network_layout/` - Plant node operations
- `cea/visualisation/a_data_loader.py` - Plot metrics registration
- `cea/visualisation/plot_main.py` - Plot orchestration
- `cea/default.config` - Plot configuration parameters
