# Solar Radiation Analysis

Solar radiation analysis calculates the amount of solar energy incident on building surfaces, which is essential for renewable energy potential assessment and energy demand calculations (especially cooling loads from solar gains).

---

## Building Solar Radiation using DAYSIM

### Overview
Uses the DAYSIM engine to perform detailed solar radiation analysis on all building surfaces (roofs and facades). DAYSIM is a validated, physics-based radiance engine that accurately simulates direct, diffuse, and reflected solar radiation.

### When to Use
- **Always required** before running renewable energy assessments (PV, PVT, SC)
- **Always required** before running energy demand forecasting
- When you need accurate solar radiation data accounting for:
  - Building self-shading
  - Shading from surrounding buildings
  - Terrain effects
  - Atmospheric conditions from weather file

### Required Inputs
- **Building architecture**: Building construction properties
- **Surroundings geometry**: Nearby buildings for shading analysis
- **Zone geometry**: Building footprints with height data
- **Terrain**: Elevation data (.tif file)
- **Weather file**: .epw format with solar radiation data

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Roof grid** | Grid resolution for roof surfaces (m) | 2 (default, recommended) |
| **Walls grid** | Grid resolution for wall surfaces (m) | 2 (default, recommended) |

- **Advanced Parameters** (generally leave as default)
- **Level of Details' roof-grid** and **walls-grid**: Control the resolution of solar radiation calculations. Smaller values = more detail but much longer computation. Default value of 2 m provides good balance. Not recommended to change unless you have specific requirements.

### How to Use

1. **Prepare inputs** (one-time setup):
   - Use [Weather Helper](08-data-management.md#weather-helper) to fetch weather data
   - Use [Surroundings Helper](08-data-management.md#surroundings-helper) to fetch nearby buildings
   - Use [Terrain Helper](08-data-management.md#terrain-helper) to fetch elevation data

2. **Run solar radiation**:
   - Navigate to **Solar Radiation Analysis**
   - Select **Building Solar Radiation using DAYSIM**
   - Configure multiprocessing (recommended: enabled)
   - Click **Run**

3. **Wait for completion**:
   - Processing time depends on:
     - Number of buildings
     - Geometric complexity
     - Density of surroundings
     - Number of CPUs available

### Output Files
For each building `BXXX`, the feature generates:

**Radiation building file**: `{scenario}/outputs/data/solar-radiation/BXXX_radiation.csv`
- Hourly solar radiation values (W/m²) for every surface point
- 8,760 hours × surface points matrix

**Radiation metadata file**: `{scenario}/outputs/data/solar-radiation/BXXX_radiation_metadata.csv`
- Surface properties (area, orientation, tilt)
- Annual cumulative radiation per surface
- Surface coordinates

### Understanding Results

The radiation results show:
- **Total radiation** = Direct + Diffuse + Reflected components
- **Surface orientation**: North, South, East, West, Top (roof)
- **Annual radiation**: kWh/m²/year on each surface

### Next Steps
After running solar radiation:
1. **Renewable energy assessment**: Run [PV, PVT, or Solar Collectors](03-renewable-energy.md)
2. **Energy demand forecasting**: Run [Demand calculations](04-demand-forecasting.md)
3. **Visualisation**: View results in the 3D viewer or export to Rhino/Grasshopper

### Tips
- **Run once, use many times**: Solar radiation results are reused by multiple features
- **Enable multiprocessing**: Significantly reduces computation time
- **Include all surroundings**: Missing context buildings lead to overestimated radiation
- **Check terrain data**: Accurate elevations improve radiation calculations in hilly areas
- **Leave grid resolution at default (2 m)**: Roof and walls grid parameters should generally not be changed. Smaller values drastically increase computation time with minimal accuracy improvement

### Troubleshooting

**Issue**: Very slow computation (>1 hour per building)
- **Solution**: Verify roof and walls grid parameters are set to default (2 m). Smaller values drastically increase computation time
- **Solution**: Check surrounding buildings count. If >500 buildings, consider reducing search radius
- **Solution**: Simplify building geometries if they have excessive detail

**Issue**: "Missing surroundings geometry" warning
- **Solution**: Run Surroundings Helper or provide manual surroundings shapefile

**Issue**: Unrealistic radiation values (too high)
- **Solution**: Verify weather file contains valid solar radiation data
- **Solution**: Ensure surroundings geometry is included

**Issue**: Missing terrain file
- **Solution**: Run Terrain Helper or set flat terrain assumption

---

## Building Solar Radiation using CRAX [BETA]

### Overview
Uses Tongji University's CRAX (CityRadiation Accelerator) model for fast solar radiation analysis in dense urban environments. CRAX employs advanced computational geometry methods (Polygon Clipping Shadow) to achieve 10-100× speedup compared to DAYSIM while maintaining good accuracy.

⚠️ **BETA Status**: This feature is actively under development and may not work as expected. **Use DAYSIM for buildings with void decks** (e.g., Singapore HDB buildings with open ground floors).

### When to Use
- Dense urban environments with many buildings (>100)
- Need for faster results at slight accuracy trade-off
- Preliminary studies before detailed DAYSIM analysis
- **NOT for buildings with void decks or complex geometries**

### Advantages vs DAYSIM
- **Speed**: 10-100× faster for dense urban areas
- **Scalability**: Better performance with many surrounding buildings
- **Memory**: Lower memory requirements

### Limitations
- **BETA status**: May have bugs or unexpected behaviour
- **Void decks**: Does not support buildings with open ground floors
- **Complexity**: Less accurate for highly complex geometries
- **Validation**: Not as extensively validated as DAYSIM

### Required Inputs
Same as DAYSIM:
- Building architecture
- Surroundings geometry
- Zone geometry
- Terrain
- Weather file

### Key Parameters

Same as DAYSIM:

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Multiprocessing** | Enable parallel processing | Enabled |
| **Number of CPUs to keep free** | CPUs reserved | 1-2 |
| **Debug mode** | Detailed logging | Disabled |
| **Roof grid** | Grid resolution for roofs (m) | 2 (default, recommended) |
| **Walls grid** | Grid resolution for walls (m) | 2 (default, recommended) |

**Advanced Parameters** (generally leave as default):
- **Roof grid** and **Walls grid**: Same as DAYSIM - control calculation resolution. Keep at default value of 2 m.

### How to Use

1. **Verify compatibility**:
   - Check that buildings do **NOT** have void decks
   - Verify geometries are relatively simple

2. **Run CRAX**:
   - Navigate to **Solar Radiation Analysis**
   - Select **Building Solar Radiation using CRAX [BETA]**
   - Configure multiprocessing (recommended: enabled)
   - Click **Run**

3. **Validate results**:
   - Compare against DAYSIM for a subset of buildings
   - Check that radiation values are reasonable
   - Report any issues to CEA development team

### Output Files
Identical format to DAYSIM:
- Radiation building files
- Radiation metadata files

### When to Prefer DAYSIM
Use DAYSIM instead of CRAX when:
- Buildings have void decks or complex geometries
- Highest accuracy is required
- Working with fewer than 50 buildings
- CRAX results seem unrealistic
- Production/publication-quality work

### Tips
- **Leave grid resolution at default (2 m)**: Same as DAYSIM - do not change roof/walls grid unless absolutely necessary
- **Report issues**: Help improve CRAX by reporting bugs on GitHub
- **Stay updated**: Check CEA releases for CRAX improvements

### Troubleshooting

**Issue**: CRAX crashes or produces errors
- **Solution**: Switch to DAYSIM for this scenario

**Issue**: Results differ significantly from DAYSIM
- **Solution**: Use DAYSIM for accurate results; report discrepancy if CRAX shows systematic errors

**Issue**: Void deck buildings fail
- **Solution**: CRAX does not support void decks; use DAYSIM instead

---

## Comparison: DAYSIM vs CRAX

| Aspect | DAYSIM                 | CRAX [BETA] |
|--------|------------------------|-------------|
| **Accuracy** | Highest (validated)    | Good (faster methods) |
| **Speed** | Baseline               | 10-100× faster |
| **Complexity** | Handles all geometries | Simplified geometries only |
| **Void decks** | Supported              | Not supported |
| **Surroundings** | Handles any density    | Optimised for dense areas |
| **Status** | Production             | Beta (experimental) |

---

## Common Workflow

### Standard Solar Radiation Workflow
1. **Prepare data** (Data Management):
   - Weather Helper → Fetch .epw file
   - Surroundings Helper → Fetch context buildings
   - Terrain Helper → Fetch elevation data

2. **Run solar radiation**:
   - Choose DAYSIM (recommended) or CRAX (experimental)
   - Enable multiprocessing
   - Run analysis

3. **Use results**:
   - Proceed to [Renewable Energy Assessment](03-renewable-energy.md)
   - Proceed to [Energy Demand Forecasting](04-demand-forecasting.md)

---

## Best Practices

1. **Always include surroundings**: Missing context leads to overestimated solar potential
2. **Use appropriate weather file**: Ensure weather file matches geographic location
3. **Run before demand**: Solar radiation must complete before energy demand calculation
4. **Archive results**: Solar radiation results are large; back up completed analyses

---

## Related Features
- **[Data Management](08-data-management.md)** - Weather, Surroundings, Terrain Helpers
- **[Renewable Energy](03-renewable-energy.md)** - PV, PVT, Solar Collectors (require radiation)
- **[Energy Demand](04-demand-forecasting.md)** - Demand calculation (requires radiation)

---

## Further Reading
- CRAX reference: [https://doi.org/10.1016/j.buildenv.2022.109937](https://doi.org/10.1016/j.buildenv.2022.109937)

---

[← Back: Import & Export](01-import-export.md) | [Back to Index](index.md) | [Next: Renewable Energy →](03-renewable-energy.md)
