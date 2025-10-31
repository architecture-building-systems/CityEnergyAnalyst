# Energy Demand Forecasting

Energy demand forecasting is the core functionality of CEA, calculating hourly energy demand for heating, cooling, electricity, domestic hot water, and other services. The process is divided into two parts: building occupancy estimation and energy load modelling.

---

## Energy Demand Part 1: Building Occupancy

### Overview
Estimates building occupancy profiles using CEA models and input schedules. This feature generates realistic hourly occupancy patterns that drive internal heat gains, ventilation requirements, and appliance/lighting loads in the subsequent demand calculation.

### When to Use
- **Always before Energy Demand Part 2** - This is a mandatory preprocessing step
- When you want to generate occupancy profiles automatically
- For buildings without measured occupancy data
- To ensure consistency between schedules and building types

### Why Is This Separate from Part 2?
Occupancy calculation can be computationally intensive and is often reused across different demand scenarios. Separating it allows:
- Faster iteration on building properties without recalculating occupancy
- Reuse of occupancy data for multiple demand calculations
- Better control over occupancy assumptions

### Prerequisites
- Zone geometry with building footprints
- Building properties assigned (use [Archetypes Mapper](08-data-management.md#archetypes-mapper))
- Weather file

### Required Input Files
- **Building internal loads** (`internal_loads.xlsx`) - Occupancy densities, appliances, lighting
- **Building comfort** (`comfort.xlsx`) - Comfort setpoints and schedules
- **Building architecture** (`architecture.xlsx`) - Floor areas and heights
- **Zone geometry** - Building footprints
- **Weather file** - Climate data

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Multiprocessing** | Enable parallel processing | Enabled |
| **Number of CPUs to keep free** | CPUs reserved | 1-2 |
| **Debug mode** | Detailed logging | Disabled |

### How to Use

1. **Verify input data**:
   - Check that building properties are assigned
   - Review internal loads schedules
   - Verify comfort schedules

2. **Run occupancy calculation**:
   - Navigate to **Energy Demand Forecasting**
   - Select **Energy Demand Part 1: Building Occupancy**
   - Enable multiprocessing (recommended)
   - Click **Run**

3. **Wait for completion**:
   - Processing time: ~1-5 minutes per building
   - Faster with multiprocessing enabled

### Output Files
For each building `BXXX`:

**Occupancy model**: `{scenario}/inputs/building-properties/occupancy/BXXX.csv`
- 8,760 hourly rows (one year)
- Occupancy levels (people)
- Internal heat gains from people (W)
- Appliance loads (W)
- Lighting loads (W)
- Ventilation requirements (m³/s)

### Understanding Occupancy Results

Key patterns to check:
- **Weekly cycles**: Lower occupancy on weekends (for offices)
- **Daily cycles**: Peak occupancy during working/living hours
- **Seasonal variation**: Some building types have seasonal patterns
- **Internal gains**: Should correlate with occupancy density

Typical occupancy densities:
- **Residential**: 0.02-0.04 people/m² GFA (average over 24 hours)
- **Office**: 0.05-0.15 people/m² GFA (during working hours)
- **Retail**: 0.10-0.30 people/m² GFA (during opening hours)
- **School**: 0.30-0.50 people/m² GFA (during school hours)

### Tips
- **Check schedules**: Review `internal_loads.xlsx` schedules before running
- **Validate outputs**: Spot-check a few buildings' occupancy profiles for realism
- **Reuse results**: Once calculated, occupancy can be reused unless building types change
- **Custom occupancy**: For buildings with known occupancy, you can manually provide occupancy files

### Troubleshooting

**Issue**: Unrealistic occupancy patterns
- **Solution**: Review and correct schedules in `internal_loads.xlsx`
- **Solution**: Verify building use types are assigned correctly

**Issue**: Missing occupancy files after completion
- **Solution**: Check for error messages in the log
- **Solution**: Verify building properties files exist and are valid

**Issue**: Very long computation time
- **Solution**: Enable multiprocessing
- **Solution**: Check if debug mode is accidentally enabled

---

## Energy Demand Part 2: Load Modelling

### Overview
This is the core CEA feature that calculates detailed hourly energy demand for all energy services using physics-based building energy models. It accounts for envelope heat transfer, thermal mass, HVAC systems, solar gains, internal gains, and occupant behaviour.

### When to Use
- **Central to most CEA workflows** - Required for nearly all downstream analyses
- Forecasting building or district energy demand
- Comparing energy performance of different building designs
- Supporting energy system sizing and optimisation
- Compliance with energy standards and regulations

### What It Calculates

The feature calculates hourly demand for:

**Heating Services**:
- Space heating (Qhs)
- Domestic hot water (Qww)
- Snow melting (Qsn, if applicable)

**Cooling Services**:
- Space cooling (Qcs)
- Data centre cooling (Qcdata, if applicable)
- Process cooling (Qcre, if applicable)

**Electricity**:
- Appliances (Eal)
- Lighting (Eal)
- Appliances and lighting (E)
- Auxiliary energy for HVAC (Ea)
- Process electricity (Epro)

**Additional Outputs**:
- Indoor temperatures and comfort metrics
- HVAC system loads and capacities
- Ventilation and infiltration rates
- Solar gains through windows
- Internal heat gains

### Prerequisites
- **Energy Demand Part 1** (Building Occupancy) - Must be completed first
- **Solar Radiation Analysis** - Must be completed first
- Zone geometry and all building properties assigned
- Weather file

### Required Input Files

**Geometry**:
- Zone geometry shapefile

**Building Properties** (typically from Archetypes Mapper):
- `architecture.xlsx` - Envelope, floors, windows
- `internal_loads.xlsx` - Occupancy, appliances, lighting
- `comfort.xlsx` - Setpoints and schedules
- `air_conditioning.xlsx` - HVAC system types
- `supply_systems.xlsx` - Energy supply configuration

**Databases**:
- Envelope databases (walls, roofs, windows, floors)
- HVAC databases (heating, cooling, hot water, controllers)
- Tightness and mass databases

**Occupancy**:
- Occupancy model files (from Part 1)

**Solar Radiation**:
- Radiation metadata and building files

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Multiprocessing** | Enable parallel processing | Enabled |
| **Number of CPUs to keep free** | CPUs reserved | 1-2 |
| **Use dynamic infiltration** | Weather-dependent infiltration | Enabled |
| **Resolution output** | Hourly detail level | 1 hour |
| **Debug mode** | Instant visualisation + detailed outputs | Disabled |
| **Buildings** | Specific buildings or all | All |

### How to Use

1. **Complete prerequisites**:
   - ✅ Building Occupancy (Part 1)
   - ✅ Solar Radiation Analysis
   - ✅ Building properties assigned

2. **Run demand calculation**:
   - Navigate to **Energy Demand Forecasting**
   - Select **Energy Demand Part 2: Load Modelling**
   - Enable multiprocessing (strongly recommended)
   - Enable dynamic infiltration (recommended)
   - Keep debug mode disabled (unless troubleshooting)
   - Click **Run**

3. **Wait for completion**:
   - Processing time: ~5-30 minutes per building
   - District-scale (50-100 buildings): 1-4 hours with multiprocessing
   - Progress is reported in the log

### Output Files

**Individual Building Demands**: `{scenario}/outputs/data/demand/BXXX.csv`
- 8,760 hourly rows
- Columns for all energy services (Qhs, Qcs, E, Qww, etc.)
- Indoor temperatures and comfort
- HVAC system loads
- ~50-100 columns per building

**Total Demand**: `{scenario}/outputs/data/demand/Total_demand.csv`
- Annual demand per building (one row per building)
- Aggregated metrics (MWh/year)
- Peak loads (kW)
- Energy intensity (kWh/m²/year)

**Demand Totals**: `{scenario}/outputs/data/demand/demand_totals.csv`
- Hourly district-wide totals
- Aggregated across all buildings
- Used for district system sizing

### Understanding Demand Results

#### Key Metrics to Review

**Annual Demand** (from `Total_demand.csv`):
- **Qhs_MWhyr**: Annual space heating demand
- **Qcs_MWhyr**: Annual space cooling demand
- **E_MWhyr**: Annual electricity demand (appliances + lighting + aux)
- **Qww_MWhyr**: Annual domestic hot water demand

**Energy Intensity** (normalize by floor area):
- **Qhs**: 30-150 kWh/m²/yr (climate-dependent)
- **Qcs**: 10-80 kWh/m²/yr (climate and cooling system-dependent)
- **E**: 20-100 kWh/m²/yr (building type-dependent)
- **Qww**: 10-30 kWh/m²/yr (occupancy-dependent)

**Peak Loads** (from `Total_demand.csv`):
- Used for sizing heating/cooling systems
- Typically occur during winter (heating) and summer (cooling)

#### Validation Checks

1. **Energy intensity** should match building type benchmarks
2. **Peak loads** should be reasonable for building size
3. **Seasonal patterns** should match climate expectations
4. **Heating vs cooling** balance should match climate zone

### Advanced Options

#### Dynamic Infiltration
When enabled (recommended):
- Infiltration varies with wind speed and temperature difference
- More realistic energy demand
- Slightly longer computation time

#### Debug Mode
When enabled (not for production):
- Creates detailed hourly output files for every building
- Generates instant visualisations of results
- Significantly increases file sizes and computation time
- Use only for troubleshooting specific buildings

#### Resolution Output
- Default: 1 hour (8,760 timesteps/year)
- Can be increased for sub-hourly analysis (experimental)

### Tips

1. **Run in stages**: Test on 2-3 buildings first before full district
2. **Enable multiprocessing**: Reduces total time dramatically
3. **Check prerequisites**: Missing radiation or occupancy causes failures
4. **Validate incrementally**: Review results for a few buildings before proceeding
5. **Archive results**: Demand results are large; compress or archive when done

### Common Issues and Solutions

**Issue**: "Missing radiation data" error
- **Solution**: Run Solar Radiation Analysis (DAYSIM or CRAX) first
- **Solution**: Verify radiation files exist for all buildings

**Issue**: "Missing occupancy data" error
- **Solution**: Run Energy Demand Part 1 (Building Occupancy) first
- **Solution**: Check that occupancy files exist in `inputs/building-properties/occupancy/`

**Issue**: Very high or very low demand values
- **Solution**: Verify building properties are correctly assigned
- **Solution**: Check envelope U-values and HVAC system types
- **Solution**: Review occupancy schedules

**Issue**: Demand calculation crashes or hangs
- **Solution**: Try running with debug mode disabled
- **Solution**: Check for invalid building geometry
- **Solution**: Verify all required input files exist and are valid

**Issue**: Long computation time (>1 hour per building)
- **Solution**: Disable debug mode
- **Solution**: Enable multiprocessing
- **Solution**: Check if building geometry is overly complex

**Issue**: Unrealistic seasonal patterns
- **Solution**: Verify weather file is correct for location
- **Solution**: Check HVAC system and setpoint schedules

### Troubleshooting Specific Buildings

If one building fails or has unrealistic results:

1. **Run in debug mode** for that building only:
   - Select specific building in "Buildings" parameter
   - Enable debug mode
   - Review detailed outputs and visualisations

2. **Check input data**:
   - Verify geometry is valid
   - Check radiation files exist
   - Review occupancy profiles
   - Validate building properties

3. **Simplify and isolate**:
   - Try running with default properties
   - Check if specific envelope or system types cause issues

---

## Complete Demand Forecasting Workflow

### Standard Workflow

1. **Data Preparation** ([Data Management](08-data-management.md)):
   - Weather Helper → Fetch weather data
   - Surroundings Helper → Fetch context buildings
   - Terrain Helper → Fetch elevation
   - Archetypes Mapper → Assign building properties

2. **Solar Radiation** ([Solar Radiation Analysis](02-solar-radiation.md)):
   - Run DAYSIM solar radiation analysis

3. **Occupancy Calculation**:
   - Run Energy Demand Part 1: Building Occupancy

4. **Demand Calculation**:
   - Run Energy Demand Part 2: Load Modelling

5. **Review Results**:
   - Check `Total_demand.csv` for annual metrics
   - Validate against benchmarks
   - Use [Visualisation tools](10-visualisation.md) to plot results

6. **Next Steps**:
   - Run [Life Cycle Analysis](06-life-cycle-analysis.md) for emissions
   - Run [Renewable Energy Assessment](03-renewable-energy.md) for supply
   - Run [Supply System Optimisation](07-supply-optimisation.md) for system design

---

## Related Features
- **[Solar Radiation Analysis](02-solar-radiation.md)** - Required prerequisite
- **[Data Management](08-data-management.md)** - Input data preparation
- **[Life Cycle Analysis](06-life-cycle-analysis.md)** - Uses demand results
- **[Supply System Optimisation](07-supply-optimisation.md)** - Uses demand results
- **[Visualisation](10-visualisation.md)** - Plot demand results

---

## Further Reading
- CEA demand model documentation: [https://city-energy-analyst.readthedocs.io/](https://city-energy-analyst.readthedocs.io/)
- Building energy modelling principles
- ISO 13790 and ISO 52016 (calculation standards)

---

[← Back: Renewable Energy](03-renewable-energy.md) | [Back to Index](index.md) | [Next: Thermal Network Design →](05-thermal-network.md)
