# Solar Technologies Guide

This guide explains how CEA calculates solar energy potential for buildings, including photovoltaic (PV) panels, photovoltaic-thermal (PVT) systems, and solar thermal collectors (SC).

## Overview

CEA provides three main solar technology assessment tools:

1. **Photovoltaic (PV)** - Electricity generation from solar panels
2. **Photovoltaic-Thermal (PVT)** - Combined electricity and heat generation
3. **Solar Collectors (SC)** - Heat generation only

All three technologies require **solar radiation data** as input, which must be calculated first using either DAYSIM or CRAX.

---

## Workflow

### Step 1: Calculate Solar Radiation

Before assessing solar technologies, you must calculate how much solar radiation hits each building surface:

**Option A: DAYSIM (Recommended)**
- More accurate for complex urban geometries
- Uses Radiance ray-tracing engine
- Slower but more detailed
- **Script**: `radiation-daysim`

**Option B: CRAX (Beta - Faster)**
- Faster for large scenarios
- Good for dense urban environments
- Less detailed than DAYSIM
- **Script**: `radiation-crax`

**Output**: Creates radiation files for each building surface (roof and walls).

### Step 2: Assess Solar Technology Potential

Choose one or more solar technologies to assess:

**Photovoltaic (PV)**
- **Script**: `photovoltaic`
- **Output**: Electricity generation potential (kWh/year)
- **Use case**: Buildings with high electricity demand

**Photovoltaic-Thermal (PVT)**
- **Script**: `photovoltaic-thermal`
- **Output**: Electricity + heat generation potential
- **Use case**: Buildings needing both electricity and low-temperature heat

**Solar Collectors (SC)**
- **Script**: `solar-collector`
- **Output**: Heat generation potential (kWh/year)
- **Use case**: Buildings with high hot water demand

---

## Key Concepts

### Panel Placement

Solar panels can be installed on:
- **Roofs**: Typically higher radiation exposure, configurable tilt angle
- **Walls**: Lower radiation but larger available area in dense cities

Configuration:
- `panel-on-roof`: Enable/disable roof installations (default: True)
- `panel-on-wall`: Enable/disable wall installations (default: True)
- `max-roof-coverage`: Maximum fraction of roof area for panels (default: 0.9)

### Panel Types

**PV Panel Types** (`type-pvpanel`):
- Different efficiency ratings (e.g., monocrystalline, polycrystalline)
- Defined in database: `CONVERSION/PHOTOVOLTAIC_PANELS`
- Affects electricity output

**SC Panel Types** (`type-scpanel`):
- Different thermal efficiency curves
- Defined in database: `CONVERSION/SOLAR_COLLECTORS`
- Affects heat output

### Radiation Threshold

**`annual-radiation-threshold`** (default: 800 kWh/m²/year):
- Minimum annual radiation required for panel installation
- Surfaces below this threshold are excluded
- Lower values = more panels but lower efficiency
- Higher values = fewer panels but better performance

### Tilt Angle

**For Roof Panels**:
- `custom-tilt-angle`: Use fixed angle (True) or follow roof slope (False)
- `panel-tilt-angle`: Fixed angle in degrees (if custom enabled)
- Optimal angle varies by latitude (~30° for tropics, ~45° for temperate)

**For Wall Panels**:
- Always vertical (90° tilt)
- Orientation follows wall direction

### Solar Window

**`solar-window-solstice`**:
- Determines which days to simulate for radiation analysis
- Simulates solstice days and interpolates for full year
- Balances accuracy vs. computation time

---

## Output Files

### Photovoltaic (PV)

**Location**: `outputs/data/potentials/solar/`

**Main outputs**:
- `PV_total_buildings.csv` - Summary by building
  - `E_PV_gen_kWh`: Annual electricity generation
  - `Area_PV_m2`: Total panel area installed
  - `radiation_kWh`: Total solar radiation received

- `PV_results/` - Detailed hourly profiles per building
  - Hourly electricity generation
  - Breakdown by surface (roof/wall)

### Photovoltaic-Thermal (PVT)

**Location**: `outputs/data/potentials/solar/`

**Main outputs**:
- `PVT_total_buildings.csv` - Summary by building
  - `E_PVT_gen_kWh`: Annual electricity generation
  - `Q_PVT_gen_kWh`: Annual heat generation
  - `Area_PVT_m2`: Total panel area
  - `mcp_PVT_kWperC`: Heat capacity flow rate

- `PVT_results/` - Detailed hourly profiles
  - Both electricity and heat output
  - Operating temperatures

**Input Temperature** (`t-in-pvt`):
- Temperature of fluid entering PVT panels (°C)
- Affects thermal efficiency
- Typically 40-60°C for domestic hot water

### Solar Collectors (SC)

**Location**: `outputs/data/potentials/solar/`

**Main outputs**:
- `SC_total_buildings.csv` - Summary by building
  - `Q_SC_gen_kWh`: Annual heat generation
  - `Area_SC_m2`: Total collector area
  - `mcp_SC_kWperC`: Heat capacity flow rate

- `SC_results/` - Detailed hourly profiles
  - Heat generation by hour
  - Operating temperatures

**Input Temperature** (`t-in-sc`):
- Temperature of fluid entering collectors (°C)
- Affects thermal efficiency
- Typically 40-70°C depending on application

---

## Configuration Parameters

### Common Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `panel-on-roof` | Install panels on roofs | True | True/False |
| `panel-on-wall` | Install panels on walls | True | True/False |
| `annual-radiation-threshold` | Min radiation for installation | 800 | 0-2000 kWh/m²/yr |
| `solar-window-solstice` | Days to simulate | True | True/False |
| `max-roof-coverage` | Max roof fraction for panels | 0.9 | 0.0-1.0 |
| `custom-tilt-angle` | Use fixed tilt angle | False | True/False |
| `panel-tilt-angle` | Fixed tilt angle if custom | 30 | 0-90° |
| `buildings` | List of buildings to assess | [] | Building names |

### PV-Specific Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `type-pvpanel` | PV panel type from database | PV1 |

### PVT-Specific Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `type-pvpanel` | PV panel type | PV1 |
| `type-scpanel` | Solar collector type | SC1 |
| `t-in-pvt` | Inlet fluid temperature | 60°C |

### SC-Specific Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `type-scpanel` | Solar collector type | SC1 |
| `t-in-sc` | Inlet fluid temperature | 60°C |

---

## Typical Workflow Examples

### Example 1: PV Assessment for All Buildings

```bash
# Step 1: Calculate radiation (prerequisite)
cea radiation-daysim --scenario /path/to/scenario

# Step 2: Assess PV potential
cea photovoltaic --scenario /path/to/scenario \
    --type-pvpanel PV1 \
    --panel-on-roof True \
    --panel-on-wall False \
    --annual-radiation-threshold 1000
```

**Result**: Electricity generation potential for rooftop PV only, minimum 1000 kWh/m²/year radiation.

### Example 2: Combined PVT and SC for Hot Water

```bash
# Step 1: Radiation (if not already done)
cea radiation-daysim --scenario /path/to/scenario

# Step 2: Assess PVT (electricity + heat)
cea photovoltaic-thermal --scenario /path/to/scenario \
    --type-pvpanel PV1 \
    --type-scpanel SC1 \
    --t-in-pvt 50 \
    --max-roof-coverage 0.5

# Step 3: Assess SC for additional heat
cea solar-collector --scenario /path/to/scenario \
    --type-scpanel SC2 \
    --t-in-sc 60 \
    --panel-on-roof True \
    --max-roof-coverage 0.9
```

**Result**: Combined assessment - PVT covers 50% of roof for both electricity and heat, remaining 40% available for pure thermal collectors.

### Example 3: High-Density Urban Scenario with Walls

```bash
# Use CRAX for faster radiation calculation
cea radiation-crax --scenario /path/to/scenario

# Assess PV on both roofs and walls (important in dense cities)
cea photovoltaic --scenario /path/to/scenario \
    --panel-on-roof True \
    --panel-on-wall True \
    --annual-radiation-threshold 600 \
    --buildings B1,B2,B3
```

**Result**: PV potential for selected buildings including wall-mounted panels, lower threshold for dense urban context.

---

## Technology Selection Guide

### When to Use PV

**Best for:**
- Buildings with high electricity demand
- Grid-connected systems
- Maximising self-consumption

**Considerations:**
- Higher efficiency than PVT for electricity
- No heat output
- Good for commercial buildings with daytime loads

### When to Use PVT

**Best for:**
- Buildings needing both electricity and heat
- Simultaneous electric and thermal loads
- Space-constrained roofs (dual output)

**Considerations:**
- Lower electrical efficiency than pure PV
- Requires heat demand to be cost-effective
- More complex installation (plumbing + electrical)
- Good for residential with DHW demand

### When to Use SC

**Best for:**
- Buildings with high hot water demand
- Process heat requirements
- Swimming pools, laundries

**Considerations:**
- Heat only (no electricity)
- Higher thermal efficiency than PVT
- Simpler system than PVT
- Good for hotels, hospitals, sports centres

---

## Database Configuration

Solar panel specifications are defined in:

**PV Panels**: `databases/{region}/COMPONENTS/CONVERSION/PHOTOVOLTAIC_PANELS.csv`

Columns:
- `code`: Panel identifier (e.g., PV1, PV2)
- `Description`: Panel name/model
- `efficiency`: Electrical efficiency (0-1)
- `module_area_m2`: Area per panel
- Additional performance parameters

**Solar Collectors**: `databases/{region}/COMPONENTS/CONVERSION/SOLAR_COLLECTORS.csv`

Columns:
- `code`: Collector identifier (e.g., SC1, SC2)
- `Description`: Collector name/type
- `n_a0`: Optical efficiency
- `n_a1`, `n_a2`: Heat loss coefficients
- Performance curve parameters

**To add new panel types:**
1. Add row to appropriate CSV file
2. Assign unique code
3. Specify efficiency and performance parameters
4. Reference code in configuration

---

## Common Issues and Solutions

### Issue: No solar potential results

**Possible causes:**
1. Radiation analysis not run → Run `radiation-daysim` or `radiation-crax` first
2. Radiation below threshold → Lower `annual-radiation-threshold`
3. No roof/wall area available → Check `zone-geometry` input

### Issue: Very low generation values

**Possible causes:**
1. Threshold too high → Adjust `annual-radiation-threshold`
2. Wrong panel type → Check database for appropriate `type-pvpanel` or `type-scpanel`
3. Limited coverage → Increase `max-roof-coverage`
4. Shading from surroundings → Review radiation analysis results

### Issue: PVT heat output too low

**Possible causes:**
1. Inlet temperature too high → Lower `t-in-pvt` (try 40-50°C)
2. Wrong collector type → Use higher efficiency `type-scpanel`
3. Environmental conditions → Check weather file temperatures

### Issue: Computation takes too long

**Solutions:**
1. Use CRAX instead of DAYSIM for radiation
2. Enable `solar-window-solstice` (simulate only solstice days)
3. Limit assessment to specific buildings with `buildings` parameter
4. Increase `annual-radiation-threshold` to exclude low-potential surfaces
5. Enable multiprocessing with `multiprocessing=True` and set `number-of-cpus-to-keep-free`

---

## Integration with Other CEA Tools

### With Demand Calculation
- Solar electricity can offset building electricity demand
- Solar heat can contribute to DHW and space heating

### With Optimisation
- Solar potentials can be used as renewable energy sources
- PV electricity fed to optimisation as supply option
- Solar thermal can reduce conventional heating

### With Baseline Costs
- Solar panel costs calculated using `solar_costs.py`
- Includes CAPEX, OPEX, and annualised costs
- Integrated into building cost summaries

### With Life Cycle Assessment
- Solar panels have environmental impacts from manufacturing
- Renewable electricity reduces operational emissions
- Net carbon benefit over panel lifetime

---

## Performance Tips

1. **Multiprocessing**: Enable for large scenarios with many buildings
2. **Radiation Caching**: Radiation results are reused, only recalculate if geometry changes
3. **Building Selection**: Use `buildings` parameter to test subset first
4. **Threshold Tuning**: Start with higher thresholds to identify viable areas quickly
5. **Panel Coverage**: Start with conservative `max-roof-coverage` (0.5-0.7) for realistic scenarios

---

## References

**Key modules:**
- `cea/technologies/solar/photovoltaic.py` - PV calculations
- `cea/technologies/solar/photovoltaic_thermal.py` - PVT calculations
- `cea/technologies/solar/solar_collector.py` - SC calculations
- `cea/utilities/solar_equations.py` - Shared solar physics equations
- `cea/analysis/costs/solar_costs.py` - Cost calculations

**Related guides:**
- Radiation analysis: See DAYSIM/CRAX documentation
- Database configuration: `cea/databases/DATABASE_GUIDE.md`
- Cost calculations: `cea/analysis/costs/CLAUDE.md`

**External references:**
- DAYSIM: http://daysim.ning.com/
- Radiance: https://www.radiance-online.org/
- Solar angles and equations: Duffie & Beckman, "Solar Engineering of Thermal Processes"
