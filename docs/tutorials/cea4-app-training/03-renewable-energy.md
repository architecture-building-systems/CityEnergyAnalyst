# Renewable Energy Potential Assessment

This category evaluates the potential for renewable energy generation from various sources including solar (PV, PVT, solar thermal), geothermal, water bodies, and sewage heat recovery.

**💡 Customising Technology Databases**: All renewable energy technologies reference CEA databases for performance characteristics. You can customise these databases to test specific manufacturers' products or future technologies. Look for database files in `{scenario}/inputs/technology/components/CONVERSION/` and edit the relevant CSV files.

---

## Photovoltaic (PV) Panels

### Overview
Calculates electricity generation potential from photovoltaic solar panels installed on building roofs and facades. The feature accounts for panel efficiency, temperature effects, shading, and orientation to estimate realistic PV yields.

### When to Use
- Assessing rooftop solar PV potential for buildings
- Evaluating facade-mounted PV systems
- Comparing different PV panel technologies
- Determining optimal PV panel placement
- Supporting net-zero energy building design

### Prerequisites
- **Solar radiation analysis** must be completed first (DAYSIM or CRAX)
- Zone geometry with valid building footprints
- Weather file

### Required Inputs
- Radiation metadata (from solar radiation analysis)
- Radiation building data (from solar radiation analysis)
- Zone geometry
- PV panel database (CEA default or custom)
- Weather file

### Key Parameters

| Parameter | Description | Typical Value            |
|-----------|-------------|--------------------------|
| **Type of PV panel** | Panel technology from database | PV1 (monocrystalline Si) |
| **Panel on roof** | Install panels on roofs | Yes                      |
| **Panel on wall** | Install panels on facades | Optional                 |
| **Annual radiation threshold** | Minimum annual radiation (kWh/m²/yr) | 200-1000                 |
| **Max roof coverage** | Maximum fraction of roof area for panels | 0.5-0.9                  |
| **Custom tilt angle** | Use custom tilt instead of roof angle | Optional                 |
| **Panel tilt angle** | Fixed tilt angle if custom enabled | Optional                 |
| **Buildings** | Select specific buildings or all | All                      |

### How to Use

1. **Complete solar radiation analysis** (prerequisite)

2. **Configure PV parameters**:
   - Navigate to **Renewable Energy Potential Assessment**
   - Select **Photovoltaic (PV) Panels**
   - Choose PV panel type (default: PV1)
   - Enable roof panels (recommended)
   - Optionally enable wall panels
   - Set radiation threshold (e.g., 800 kWh/m²/yr)
   - Set maximum roof coverage (e.g., 0.7 = 70%)

3. **Run analysis**:
   - Enable multiprocessing for faster computation
   - Click **Run**

4. **Review results** in output files

### Output Files
For each building `BXXX`:

**PV results**: `{scenario}/outputs/data/potentials/solar/BXXX_PV.csv`
- Hourly electricity generation (kWh)
- 8,760 hours of generation data
- Total annual generation

**PV metadata**: `{scenario}/outputs/data/potentials/solar/BXXX_PV_sensors.csv`
- Panel locations and orientations
- Installed capacity per surface (kWp)
- Annual radiation per panel array
- Surface areas and tilt angles

### Understanding Results

Key metrics to examine:
- **Annual electricity generation** (MWh/yr or kWh/yr)
- **Installed capacity** (kWp) - total rated capacity
- **Capacity factor** = Annual generation / (Installed capacity × 8760 hours)
- **Specific yield** = Annual generation / Installed capacity (kWh/kWp/yr)

Typical values (Central Europe):
- Capacity factor: 10-15%
- Specific yield: 900-1,200 kWh/kWp/yr
- Rooftop coverage: 50-70% of available area

### Panel Types in CEA Database

The CEA database includes various PV panel technologies with different efficiencies and performance characteristics. To see available panel types and their properties:
1. Navigate to `{scenario}/inputs/technology/components/CONVERSION/PHOTOVOLTAIC_PANELS.csv`
2. Review panel specifications (efficiency, temperature coefficients, etc.)

**Customising the Database**:
- You can add custom PV panel types by editing `PHOTOVOLTAIC_PANELS.csv`
- Add new rows with your panel specifications (e.g., in CEA-4 App, Excel or text editor)
- Reference the new panel code in the "Type of PV panel" parameter
- Useful for testing specific manufacturers' panels or future technologies

Common PV technology categories in the database:
- **Monocrystalline silicon**: Highest efficiency (~18-22%)
- **Polycrystalline silicon**: Moderate efficiency (~15-18%)
- **Thin film**: Lower efficiency (~10-13%), better performance in diffuse light and high temperatures

### Tips
- **Start with roofs only**: Facade PV typically has lower yields
- **Use radiation threshold**: Exclude poorly-oriented surfaces (< 800 kWh/m²/yr)
- **Check roof coverage**: Leave space for maintenance access and other equipment
- **Compare panel types**: Run analysis with different panel technologies
- **Consider shading**: Results automatically account for shading from solar radiation analysis

### Troubleshooting

**Issue**: No PV potential calculated
- **Solution**: Ensure solar radiation analysis completed successfully
- **Solution**: Check radiation threshold isn't too high

**Issue**: Very low PV yields
- **Solution**: Verify solar radiation results are reasonable
- **Solution**: Check if buildings are heavily shaded

**Issue**: Missing output files
- **Solution**: Check that building names match between geometry and radiation files

---

## Photovoltaic-Thermal (PVT) Panels

### Overview
Calculates combined electricity and heat generation from hybrid photovoltaic-thermal panels. PVT panels generate electricity like standard PV while simultaneously capturing waste heat for domestic hot water or space heating.

### When to Use
- Assessing combined electricity and heat generation
- Maximising energy yield per roof area
- Buildings with both electricity and heat demand
- Comparing PVT vs separate PV + solar thermal systems

### Prerequisites
Same as PV: solar radiation analysis must be completed

### Key Differences from PV
- **Dual output**: Electricity (kWh_el) + Heat (kWh_th)
- **Temperature effects**: More complex thermal modelling
- **Inlet temperature**: Heat generation depends on fluid inlet temperature
- **Panel database**: Uses PVT-specific panel properties

**PVT Panel Database**:
- Navigate to `{scenario}/inputs/technology/components/CONVERSION/PHOTOVOLTAIC_THERMAL_PANELS.csv`
- You can customise by adding new PVT panel types with specific electrical and thermal performance characteristics
- Reference custom panels in the "Type of PV panel" and "Type of SC panel" parameters

### Key Parameters
Similar to PV, plus:

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Type of PV panel** | PV component technology | PV1 |
| **Type of SC panel** | Solar thermal component | SC1 (flat plate) |
| **Inlet temperature (PVT)** | Fluid inlet temp for heat extraction | 35-60°C |

### How to Use

1. Complete solar radiation analysis

2. **Configure PVT parameters**:
   - Navigate to **Renewable Energy Potential Assessment**
   - Select **Photovoltaic-Thermal (PVT) Panels**
   - Choose PV and SC panel types
   - Set inlet temperature (e.g., 50°C for DHW)
   - Configure coverage and threshold parameters

3. Run analysis

### Output Files
For each building `BXXX`:

**PVT results**: `{scenario}/outputs/data/potentials/solar/BXXX_PVT.csv`
- Hourly electricity generation (kWh_el)
- Hourly heat generation (kWh_th)
- Panel temperatures
- Efficiency values

**PVT metadata**: Similar to PV metadata with additional thermal properties

### Understanding PVT Results

Key metrics:
- **Electrical efficiency**: Slightly lower than standalone PV (due to higher operating temperatures)
- **Thermal efficiency**: 30-50% of incident radiation
- **Combined efficiency**: Can exceed 60-70%
- **Heat output**: Depends strongly on inlet temperature (lower temp = higher output)

Typical annual yields (Central Europe, per kWp installed):
- Electricity: 800-1,000 kWh/kWp/yr
- Heat: 400-600 kWh/kWp/yr (at 50°C inlet)

### Tips
- **Set realistic inlet temperature**: Match to system design (35°C for heat pumps, 60°C for DHW)
- **Compare to separate systems**: Run separate PV and SC analyses to compare
- **Consider integration**: PVT requires careful system integration for heat utilisation

---

## Solar Collectors (SC)

### Overview
Calculates heat generation potential from solar thermal collectors (flat plate or evacuated tube). Solar collectors provide heat for domestic hot water, space heating, or industrial processes.

### When to Use
- Assessing solar thermal heating potential
- Designing solar DHW systems
- Evaluating district heating solar support
- Comparing solar thermal vs heat pump systems

### Prerequisites
Solar radiation analysis must be completed

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Type of SC panel** | Collector technology | SC1 (flat plate) or SC2 (evacuated tube) |
| **Inlet temperature (SC)** | Fluid inlet temperature | 40-70°C |
| **Panel on roof** | Install on roofs | Yes |
| **Panel on wall** | Install on facades | Rarely |
| **Radiation threshold** | Minimum radiation | 800 kWh/m²/yr |
| **Max roof coverage** | Maximum coverage | 0.3-0.5 (leave room for PV) |

### Collector Types

The CEA database includes various solar thermal collector technologies. To see available collector types:
1. Navigate to `{scenario}/inputs/technology/components/CONVERSION/SOLAR_COLLECTORS.csv`
2. Review collector specifications (efficiency curves, optical properties, etc.)

**Customising the Database**:
- You can add custom solar collector types by editing `SOLAR_COLLECTORS.csv`
- Add new rows with your collector specifications (e.g., in Excel or text editor)
- Reference the new collector code in the "Type of SC panel" parameter
- Useful for testing specific manufacturers' collectors

Common solar collector categories in the database:

**Flat Plate Collectors**:
- Lower cost
- Good for low-to-medium temperatures (40-80°C)
- Better for DHW applications
- Efficiency: 50-70% at optimal conditions

**Evacuated Tube Collectors**:
- Higher cost
- Better for high temperatures (60-100°C)
- Lower heat losses
- Better performance in cold/cloudy conditions
- Efficiency: 60-80% at optimal conditions

### How to Use

1. Complete solar radiation analysis

2. **Configure SC parameters**:
   - Navigate to **Renewable Energy Potential Assessment**
   - Select **Solar Collectors (SC)**
   - Choose collector type (SC1 or SC2)
   - Set inlet temperature based on application:
     - DHW systems: 40-50°C
     - Space heating: 30-40°C
     - High-temp applications: 60-80°C
   - Set coverage (recommend 30-50% to leave room for PV)

3. Run analysis

### Output Files
For each building `BXXX`:

**SC results**: `{scenario}/outputs/data/potentials/solar/BXXX_SC.csv`
- Hourly heat generation (kWh_th)
- Collector temperatures
- Efficiency values

**SC metadata**: Panel locations, installed area, annual yields

### Understanding SC Results

Performance factors:
- **Higher inlet temperature** = Lower efficiency = Lower heat output
- **Evacuated tubes** perform better at high temperatures and low irradiation
- **Flat plates** are more cost-effective for DHW in sunny climates

Typical specific yields (kWh/m²/yr of collector area):
- Flat plate (40°C inlet): 400-600 kWh/m²/yr
- Flat plate (60°C inlet): 300-450 kWh/m²/yr
- Evacuated tube (60°C inlet): 400-550 kWh/m²/yr

### Tips
- **Match inlet temp to application**: Lower temps give higher yields
- **Leave room for PV**: Solar collectors need ~30-50% of roof
- **Consider seasonality**: SC output peaks in summer when heating demand is low
- **Size for summer loads**: Often sized for DHW, not space heating

---

## Shallow Geothermal Potential

### Overview
Calculates heat extraction potential from shallow geothermal probes (borehole heat exchangers up to 50 m deep) for ground-source heat pump systems.

### When to Use
- Assessing ground-source heat pump feasibility
- Determining required borehole field size
- Comparing geothermal vs other heating sources
- Planning district-scale ground-source systems

### How It Works
The feature estimates:
- Available ground area for boreholes
- Soil thermal properties (from terrain data)
- Sustainable heat extraction rates
- Number and depth of required boreholes

### Prerequisites
- Zone geometry
- Scenario-level configuration (no building-specific inputs needed)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Borehole depth** | Maximum depth of probes | 50 m (shallow) |
| **Borehole spacing** | Minimum distance between probes | 5-6 m |
| **Soil thermal conductivity** | Ground thermal properties | Auto (from terrain) or manual |

### How to Use

1. Navigate to **Renewable Energy Potential Assessment**
2. Select **Shallow Geothermal Potential**
3. Review default parameters (usually suitable)
4. Click **Run**

### Output Files

**Geothermal potential**: `{scenario}/outputs/data/potentials/geothermal_potential.csv`
- Available ground area per building
- Number of possible boreholes
- Heat extraction capacity (kW)
- Annual extractable heat (MWh/yr)

### Understanding Results

Key metrics:
- **Heat extraction rate**: Typically 30-60 W/m of borehole
- **Total capacity**: Number of boreholes × depth × extraction rate
- **Seasonal limitation**: Sustainable annual extraction ~1,800-2,200 hours equivalent

Typical values:
- Single-family home: 1-2 boreholes (5-10 kW capacity)
- Apartment building: 5-15 boreholes (25-75 kW capacity)
- District system: 50-200 boreholes (250-1,000 kW capacity)

### Tips
- **Check site constraints**: Results assume available ground area; verify site-specific limitations
- **Consider ground properties**: Clay, sand, and rock have different thermal properties
- **Account for recharge**: Ground needs summer recharge (passive cooling or regeneration)
- **Use with heat pumps**: Geothermal provides low-temp heat source; pair with heat pumps

### Troubleshooting

**Issue**: Very low geothermal potential
- **Solution**: Check if sufficient ground area is available around buildings
- **Solution**: High-density areas may have limited ground access

---

## Water Body Potential

### Overview
Calculates heat extraction potential from nearby water bodies (lakes, reservoirs, rivers) for heat pump systems. Water bodies provide stable heat sources/sinks for large-scale heat pump applications.

### When to Use
- Sites near lakes, rivers, or reservoirs
- District heating/cooling systems
- Large-scale heat pump applications
- Comparing water-source vs ground-source heat pumps

### How It Works
Estimates sustainable heat extraction based on:
- Water body volume and temperature
- Flow rates (for rivers)
- Environmental constraints
- Distance from buildings

### Prerequisites
- Zone geometry
- Water body definition (manual input or GIS data)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Water body type** | Lake, river, or reservoir | User-defined |
| **Distance to site** | Piping distance | Site-specific |
| **Minimum water temp** | Environmental constraint | 4°C (to prevent freezing) |

### How to Use

1. **Define water body**:
   - Provide water body polygon or coordinates
   - Specify water body properties

2. **Run analysis**:
   - Navigate to **Renewable Energy Potential Assessment**
   - Select **Water Body Potential**
   - Configure parameters
   - Click **Run**

### Output Files

**Water body potential**: `{scenario}/outputs/data/potentials/water_body_potential.csv`
- Available heat extraction capacity (kW)
- Seasonal variation
- Distance penalties
- Environmental constraints

### Understanding Results

Factors affecting potential:
- **Water volume**: Larger bodies = greater capacity
- **Flow rate**: Rivers with high flow = nearly unlimited capacity
- **Temperature**: Warmer water = better heat pump efficiency
- **Distance**: Long piping distances reduce economic viability

Typical applications:
- Lake-source: 50-500 kW extraction per hectare of lake surface
- River-source: Limited by environmental regulations, not capacity
- Deep lakes: Can provide year-round heating and cooling

### Tips
- **Check regulations**: Water heat extraction usually requires permits
- **Consider ecology**: Must not harm aquatic ecosystems
- **Account for piping**: Long distances increase costs and losses
- **Seasonal variation**: Some water bodies freeze in winter

---

## Sewage Heat Potential

### Overview
Calculates heat recovery potential from wastewater (sewage) using heat exchangers. Sewage provides a consistent, year-round heat source for heat pumps, with temperatures typically 10-20°C.

### When to Use
- Buildings with significant wastewater flows
- District systems with sewage access
- Evaluating wastewater heat recovery systems
- Circular economy and resource efficiency studies

### How It Works
Estimates heat recovery based on:
- Building water demand (from demand calculations)
- Wastewater temperatures
- Heat exchanger efficiency
- Flow rates and timing

### Prerequisites
- **Energy demand analysis** must be completed (to determine water usage)
- Zone geometry

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Heat exchanger efficiency** | Recovery efficiency | 40-60% |
| **Minimum sewage temp** | After heat extraction | 10°C |
| **Building water demand** | From demand calculation | Auto |

### How to Use

1. **Complete energy demand analysis** (prerequisite for water demand data)

2. **Run sewage potential**:
   - Navigate to **Renewable Energy Potential Assessment**
   - Select **Sewage Heat Potential**
   - Review parameters (defaults usually suitable)
   - Click **Run**

### Output Files

**Sewage potential**: `{scenario}/outputs/data/potentials/sewage_potential.csv`
- Recoverable heat per building (kWh/yr)
- Peak recovery capacity (kW)
- Monthly variation
- Water flow rates

### Understanding Results

Typical sewage heat potential:
- **Residential buildings**: 0.5-1.5 kWh thermal per m³ wastewater
- **Hotels/hospitals**: Higher potential due to consistent hot water use
- **Office buildings**: Lower potential (limited showers/kitchens)

Factors affecting recovery:
- **Flow rates**: Higher flows = more heat available
- **Usage patterns**: Continuous flows better than intermittent
- **Temperature**: Hot water use increases sewage temperature

Annual recoverable heat (rule of thumb):
- ~20-30% of domestic hot water energy consumption
- ~5-10% of total building heating demand

### Tips
- **Building type matters**: Residential and hotels have best potential
- **Combine with heat pumps**: Sewage provides 10-20°C source for heat pumps
- **Consider centralized systems**: District-scale sewage heat recovery often more viable
- **Check access**: Need physical access to sewage pipes

### Troubleshooting

**Issue**: Zero sewage potential
- **Solution**: Ensure energy demand analysis completed successfully
- **Solution**: Check that buildings have water demand (DHW)

**Issue**: Very low potential
- **Solution**: Office/industrial buildings may have limited water use
- **Solution**: Verify water demand calculations are reasonable

---

## Comparing Renewable Energy Options

### Decision Matrix

| Technology | Best For | Pros | Cons | Typical Cost |
|------------|----------|------|------|--------------|
| **PV** | All buildings with roof access | Mature technology, low maintenance | Intermittent, no heating | Medium |
| **PVT** | Buildings needing both heat & power | High combined efficiency | Complex integration | High |
| **Solar Collectors** | Buildings with DHW demand | Simple, reliable | Seasonal mismatch, space | Low-Medium |
| **Geothermal** | Buildings with ground access | Stable, year-round | High upfront cost, drilling | High |
| **Water Body** | Sites near large water bodies | High capacity, low running costs | Distance limitations, permits | Medium-High |
| **Sewage** | High water-use buildings | Consistent availability | Limited capacity, access needed | Medium |

### Typical Workflow for Renewable Energy Assessment

1. **Run solar radiation** (DAYSIM)
2. **Assess all relevant renewable sources**:
   - PV (always)
   - Solar collectors (if heating demand)
   - PVT (if both heat and power needed)
   - Geothermal (if ground access)
   - Water body (if nearby)
   - Sewage (if high water use)
3. **Compare results** using [Export Results to CSV](01-import-export.md#export-results-to-csv)
4. **Visualise** using [Plot - Solar Technology](10-visualisation.md#plot-solar-technology)
5. **Integrate into supply system optimisation**

---

## Related Features
- **[Solar Radiation Analysis](02-solar-radiation.md)** - Required prerequisite
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Required for sewage potential
- **[Supply System Optimisation](07-supply-optimisation.md)** - Integrate renewable energy results
- **[Visualisation](10-visualisation.md)** - Plot renewable energy potential

---

[← Back: Solar Radiation](02-solar-radiation.md) | [Back to Index](index.md) | [Next: Energy Demand Forecasting →](04-demand-forecasting.md)
