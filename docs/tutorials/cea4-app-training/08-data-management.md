# Data Management

Data management features help prepare and validate input data for CEA analysis. These "helper" tools automate data acquisition from external sources and ensure data quality and format compliance.

---

## Database Helper

### Overview
Loads standard CEA databases into your current scenario. These databases contain archetypal properties for building envelopes, HVAC systems, internal loads, and more, providing default values based on building standards and research.

### When to Use
- Starting a new CEA project
- Ensuring you have latest standard databases
- Resetting databases to defaults
- After updating CEA to newer version

### What It Loads

**Envelope Databases**:
- Wall assemblies (construction types, U-values, materials)
- Roof assemblies
- Floor assemblies
- Window types (glazing, frames, U-values, g-values)
- Shading systems

**HVAC Databases**:
- Heating system types and efficiencies
- Cooling system types and COPs
- Hot water systems
- Ventilation controllers
- Distribution systems

**Use Type Databases**:
- Internal loads by building use (occupancy, appliances, lighting)
- Schedules (hourly profiles for different uses)
- Comfort requirements (temperature, humidity setpoints)

**Technology Databases**:
- Conversion technologies (boilers, heat pumps, CHPs, etc.)
- Renewable energy systems (PV panels, solar collectors)
- Storage systems (thermal, battery)
- Cost and performance data

### How to Use

1. Navigate to **Data Management**
2. Select **Database Helper**
3. Choose database source:
   - CEA Default (recommended for most users)
   - Custom database path (for advanced users)
4. Click **Run**

The feature will copy all database files to:
```
{CEA Project}/{Current Scenario}/inputs/technology/
```

### Database Versions

CEA databases are versioned and updated with new releases:
- **Check version**: Each database has a version identifier
- **Update regularly**: Run Database Helper after CEA updates
- **Custom modifications**: Make copies before editing

### Tips
- **Run once per scenario** typically sufficient
- **Backup custom changes** before running (it overwrites existing databases)
- **Regional differences**: Default databases are European-focused; customise for your region

### Troubleshooting

**Issue**: Custom database modifications overwritten
- **Solution**: Back up custom databases before running Database Helper
- **Solution**: Store custom databases in separate folder and copy manually

---

## Archetypes Mapper

### Overview
Automatically populates building properties (envelope, systems, internal loads) based on archetypal building classifications. This feature uses the building's age, use type, and construction standard to assign appropriate property values from the CEA databases.

### When to Use
- **Essential step in every CEA project** before running demand or other analyses
- Assigning properties to new buildings
- Bulk-assigning properties to many buildings
- Creating baseline scenarios

### How It Works
The feature maps buildings to archetypes based on:
1. **Building age** (construction year or renovation year)
2. **Building use type** (residential, office, retail, etc.)
3. **Construction standard** (national building codes, energy standards)
4. **Climate zone** (for location-specific requirements)

### Prerequisites
- Zone geometry with buildings
- Building use types and ages defined in `zone.shp` attributes

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Archetype system** | Regional standard (ASHRAE, SIA, etc.) | Region-specific |
| **Overwrite existing** | Replace existing properties | Yes (first time) / No (to preserve manual edits) |

### How to Use

1. **Ensure building attributes exist**:
   - Open `zone.shp` in QGIS or use CEA inputs editor
   - Verify each building has:
     - `Name` (building ID)
     - `YEAR` (construction year)
     - `1ST_USE` (primary use type, e.g., "MULTI_RES", "OFFICE")
     - Optionally: `2ND_USE`, `3RD_USE` for mixed-use buildings

2. **Run Archetypes Mapper**:
   - Navigate to **Data Management**
   - Select **Archetypes Mapper**
   - Choose archetype system (default: automatic based on location)
   - Configure overwrite option
   - Click **Run**

3. **Processing time**: < 1 minute for typical projects

### Output Files
The feature populates all building property files:
- `envelope.csv` - Envelope properties, window-wall ratios, floor heights
- `internal_loads.csv` - Occupancy densities, appliances, lighting
- `comfort.csv` - Setpoint temperatures, acceptable ranges
- `air_conditioning.csv` - HVAC system types
- `supply_systems.csv` - Energy supply configuration

### Understanding Archetype Mapping

**Example**: Office building built in 2005 in Switzerland
- Archetype: SIA 2024 "OFFICE" + SIA 380/1:2009 standard
- Properties assigned:
  - Wall U-value: ~0.25 W/m²K (well-insulated)
  - Window U-value: ~1.3 W/m²K (double-glazed)
  - Occupancy: 0.111 people/m² (during office hours)
  - Lighting: 14 W/m²
  - HVAC: Air-conditioning with heat recovery

### Customisation After Mapping

After running Archetypes Mapper, you can manually adjust properties:
1. Open property files in Excel
2. Modify specific buildings or properties
3. Save files
4. Proceed with CEA analysis

Common adjustments:
- Window-wall ratios (architecture.csv)
- HVAC system types (air_conditioning.csv)
- Occupancy schedules (internal_loads.csv)
- Setpoint temperatures (comfort.csv)

### Tips
- **Run before first demand calculation**: Mandatory step
- **Check mapped properties**: Review a few buildings to ensure reasonable values
- **Use overwrite carefully**: Preserves manual edits if set to "No"
- **Mixed-use buildings**: Use 1ST_USE, 2ND_USE, 3RD_USE fields with percentages

### Troubleshooting

**Issue**: Missing properties after mapping
- **Solution**: Check that building use types in `zone.shp` are valid
- **Solution**: Verify Database Helper was run first

**Issue**: Unrealistic property values
- **Solution**: Check building year is reasonable (not 0 or future date)
- **Solution**: Verify use type matches actual building
- **Solution**: Manually adjust properties after mapping

---

## Weather Helper

### Overview
Fetches EPW (EnergyPlus Weather) files from third-party sources or morphs existing EPW files to future climate scenarios. This feature automates weather data acquisition and climate change projection.

### When to Use
- **Essential for every CEA project**: Weather data required for all analyses
- Starting new projects without weather files
- Studying future climate scenarios
- Comparing different climate projections

### Features

**1. Fetch Weather Data**:
- Downloads EPW files from [Climate.OneBuilding](https://climate.onebuilding.org)
- Automatic location detection from zone geometry
- Nearest weather station selection
- Multiple years available (typical meteorological year)

**2. Morph to Future Climate**:
- Uses `pyepwmorph` library
- Access global climate models (GCMs)
- Generate future climate scenarios (2030, 2050, 2080, etc.)
- Multiple RCP/SSP scenarios (climate forcing scenarios)

### Prerequisites
- Zone geometry (for location detection)
- Internet connection (for downloading weather data)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Mode** | Fetch or Morph | Fetch |
| **Target year** (morph) | Future year | 2050 |
| **Climate scenario** (morph) | RCP/SSP | RCP 4.5 or RCP 8.5 |
| **GCM model** (morph) | Climate model | Ensemble mean |

### How to Use

#### Fetching Weather Data

1. Navigate to **Data Management**
2. Select **Weather Helper**
3. Choose mode: **Fetch weather data**
4. Click **Run**
5. The feature will:
   - Detect location from zone geometry coordinates
   - Find nearest available weather station
   - Download EPW file
   - Save to `{scenario}/inputs/weather/`

#### Morphing to Future Climate

1. **Ensure current EPW file exists** in scenario
2. Navigate to **Weather Helper**
3. Choose mode: **Morph to future climate**
4. Set target year (e.g., 2050)
5. Select climate scenario:
   - **RCP 2.6**: Strong mitigation (low warming)
   - **RCP 4.5**: Moderate mitigation (medium warming)
   - **RCP 8.5**: High emissions (high warming)
6. Click **Run**
7. Morphed EPW file saved as `{scenario}/inputs/weather/weather_morphed_YEAR_SCENARIO.epw`

### Understanding Weather Files

EPW files contain hourly data for full year (8,760 hours):
- Dry-bulb temperature (°C)
- Relative humidity (%)
- Solar radiation (direct, diffuse)
- Wind speed and direction
- Atmospheric pressure
- Sky conditions

### Climate Morphing Details

Morphing adjusts EPW parameters based on climate model projections:
- **Temperature**: +1.5°C to +4°C (depending on scenario and year)
- **Humidity**: Changes based on temperature and precipitation projections
- **Solar radiation**: Adjusted for cloud cover changes
- **Wind**: Modified based on circulation pattern changes

Reference: [McCarty & Shareef (2023)](https://doi.org/10.1088/1742-6596/2600/8/082005)

### Tips
- **Use TMY files**: Typical Meteorological Year represents average conditions
- **Check location**: Verify downloaded weather matches your site location
- **Multiple scenarios**: Run analyses with both current and future climate
- **Validate morphed files**: Check that future temperatures are realistic

### Troubleshooting

**Issue**: No weather data found for location
- **Solution**: Zone geometry may be in remote area; manually download EPW from other sources
- **Solution**: Try nearby cities on Climate.OneBuilding.org

**Issue**: Morphing fails
- **Solution**: Ensure base EPW file exists and is valid
- **Solution**: Check internet connection (pyepwmorph may need to download climate data)

**Issue**: Unrealistic future temperatures
- **Solution**: Verify climate scenario and target year are correctly selected
- **Solution**: Check base EPW file is reasonable

---

## Surroundings Helper

### Overview
Automatically queries and downloads surrounding building geometries from OpenStreetMap. Surrounding buildings are essential for accurate solar radiation analysis, as they provide shading context.

### When to Use
- **Required before solar radiation analysis**: Surroundings affect shading
- Starting new projects without context buildings
- Updating surroundings for changed urban context

### How It Works
1. Detects location from zone geometry
2. Queries OpenStreetMap for buildings within radius
3. Estimates building heights (from OSM data or rules of thumb)
4. Creates `surroundings.shp` shapefile

### Prerequisites
- Zone geometry with valid coordinates
- Internet connection

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|-------------|
| **Search radius** | Distance to fetch buildings (m) | 50-100 m |
| **Height estimation** | Method for missing heights | OSM data or # of floors × 3m |

### How to Use

1. Navigate to **Data Management**
2. Select **Surroundings Helper**
3. Set search radius:
   - **Urban core**: 50-100 m (many nearby tall buildings)
   - **Suburban**: 30-50 m (fewer, lower buildings)
   - **Rural**: 20-30 m (sparse buildings)
4. Click **Run**
5. Surroundings saved to `{scenario}/inputs/building-geometry/surroundings.shp`

### Output File

**Surroundings shapefile**: `surroundings.shp`
- Building footprints (polygons)
- Estimated heights (m)
- Building IDs from OSM

### Understanding Surroundings

**Why surroundings matter**:
- Buildings cast shadows on each other
- Affects solar radiation calculations
- Impacts PV and solar thermal potential
- Influences cooling loads (solar gains through windows)

### Tips
- **Larger radius for tall buildings**: Tall buildings cast longer shadows
- **Check heights**: OSM height data is often incomplete; verify for key buildings
- **Manual editing**: You can manually edit `surroundings.shp` to correct heights
- **Exclude distant buildings**: Buildings >1 km usually negligible for shading

### Troubleshooting

**Issue**: No surroundings found
- **Solution**: Check zone geometry has valid coordinates
- **Solution**: Rural area may have sparse OSM data; this is OK

**Issue**: Buildings with zero height
- **Solution**: OSM data incomplete; heights estimated as 3m × floors or default 10m
- **Solution**: Manually edit surroundings.shp to add heights

**Issue**: Too many surrounding buildings (slow radiation calculation)
- **Solution**: Reduce search radius
- **Solution**: Manually filter distant or irrelevant buildings

---

## Terrain Helper

### Overview
Fetches topography data (.tif elevation raster) from third-party sources. Terrain elevation data is used for solar radiation calculations (horizon effects) and ground temperature estimation.

### When to Use
- **Recommended before solar radiation analysis**: Terrain affects solar exposure
- Sites with significant topography (hills, mountains, valleys)
- Improving accuracy of solar and demand calculations

### How It Works
1. Detects location and extent from zone + surroundings geometry
2. Queries elevation data sources (SRTM, ASTER GDEM, etc.)
3. Downloads and crops digital elevation model (DEM)
4. Saves as GeoTIFF raster file

### Prerequisites
- Zone geometry
- Surroundings geometry (recommended, to set extent)
- Internet connection

### How to Use

1. **Run Surroundings Helper first** (to establish extent)
2. Navigate to **Data Management**
3. Select **Terrain Helper**
4. Click **Run**
5. Terrain saved to `{scenario}/inputs/topography/terrain.tif`

### Output File

**Terrain raster**: `terrain.tif`
- GeoTIFF format
- Elevation values in meters
- Covers zone + surroundings extent
- Typical resolution: 30m × 30m (SRTM) or better

### Understanding Terrain Effects

**Terrain impacts on CEA**:
- **Solar radiation**: Hills block low-angle sun, valleys receive less
- **Ground temperature**: Elevation affects air and ground temperature
- **Shading**: Terrain horizon limits solar access

**When terrain matters most**:
- Mountainous regions
- Hillsides and valleys
- Coastal cliffs
- Sites with >50m elevation change within 1 km

**When terrain is less important**:
- Flat regions (elevation change <10m within 1 km)
- Dense urban areas (building shading dominates)

### Tips
- **Flat sites**: You can skip this feature; CEA assumes flat terrain
- **Check elevation range**: Verify terrain.tif has reasonable values
- **Resolution**: 30m resolution is sufficient for most applications

### Troubleshooting

**Issue**: Terrain download fails
- **Solution**: Check internet connection
- **Solution**: Remote areas may lack coverage; use flat terrain assumption

**Issue**: Extreme or incorrect elevation values
- **Solution**: Verify coordinate system of zone geometry is correct
- **Solution**: Check for data corruption; re-run Terrain Helper

---

## Streets Helper

### Overview
Queries streets geometry from OpenStreetMap for use in thermal network layout generation. Street networks define the routing paths for district heating and cooling pipe networks.

### When to Use
- **Required before Thermal Network Part 1**: Streets guide network layout
- Planning district energy systems
- Ensuring realistic pipe routing

### How It Works
1. Detects location from zone geometry
2. Queries OpenStreetMap for street network
3. Filters relevant road types
4. Creates `streets.shp` shapefile (polylines)

### Prerequisites
- Zone geometry
- Internet connection

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Road types** | Which roads to include | Primary, secondary, residential |
| **Search radius** | Distance to fetch streets | Match zone extent + buffer |

### How to Use

1. Navigate to **Data Management**
2. Select **Streets Helper**
3. Configure road types (default: all paved roads)
4. Click **Run**
5. Streets saved to `{scenario}/inputs/networks/streets.shp`

### Output File

**Streets shapefile**: `streets.shp`
- Polylines representing street centerlines
- Street names and types
- Network topology (connections)

### Street Network Quality

**Good quality**:
- Complete coverage of site area
- Proper connections at intersections
- Reaches all buildings

**Poor quality (requires manual editing)**:
- Missing streets
- Disconnected segments
- Private roads not in OSM

### Tips
- **Check coverage**: Verify streets reach all buildings
- **Manual editing**: You can add missing streets in QGIS
- **Private roads**: Often missing from OSM; add manually if needed for networks

### Troubleshooting

**Issue**: Missing streets
- **Solution**: Manually digitise missing streets in QGIS
- **Solution**: Check OSM for your area; contribute missing data to OSM

**Issue**: Disconnected network
- **Solution**: Add connecting segments manually
- **Solution**: Simplify network to connect major nodes

---

## Trees Helper

### Overview
Imports tree geometries into the scenario for shading and microclimate analysis. Trees can significantly affect solar radiation on buildings and outdoor thermal comfort.

### When to Use
- Sites with significant tree coverage
- Improving solar radiation accuracy
- Microclimate and comfort studies
- Parks, campuses, residential areas with mature trees

### How It Works
Requires manual input data:
- Tree locations (points)
- Tree heights
- Crown diameters
- Optionally: species, leaf area index (LAI)

See CEA Learning Camp Lesson cea-a-02 for detailed instructions.

### Input Data

Users must provide tree data as:
- CSV file with tree attributes
- Shapefile (points) with tree properties
- Or manual database entry

Required attributes:
- X, Y coordinates
- Height (m)
- Crown diameter (m)

### How to Use

1. **Prepare tree data** (external data collection required):
   - Survey trees on site
   - Use aerial imagery to identify locations
   - Estimate or measure heights and crown sizes

2. **Format data** according to CEA schema

3. **Run Trees Helper**:
   - Navigate to **Data Management**
   - Select **Trees Helper**
   - Provide tree data file
   - Click **Run**

4. Trees saved to `{scenario}/inputs/building-geometry/trees.shp`

### Tree Shading Effects

**Deciduous trees**:
- Summer: Provide shading (reduce cooling load, reduce PV)
- Winter: Less shading (leafless)
- Seasonal leaf area index adjustment

**Evergreen trees**:
- Year-round shading
- Constant impact on solar access

**Typical impact**:
- Large trees near south facade: 10-30% reduction in solar gains
- Tree-lined street: 5-15% reduction in PV potential
- Park setting: Variable, site-specific

### Tips
- **Worth the effort for tree-heavy sites**: Skip if minimal tree coverage
- **Estimate if needed**: Use aerial imagery and typical dimensions
- **Seasonal variation**: Deciduous trees modeled with seasonal LAI

### Troubleshooting

**Issue**: Trees not affecting solar radiation results
- **Solution**: Verify trees.shp is in correct location and format
- **Solution**: Check tree heights are reasonable (>2m typically)

---

## Data Management Workflow

### Recommended Sequence

For new CEA projects:

1. **Create zone geometry** (buildings) - external GIS or Rhino/Grasshopper
2. **Database Helper** - Load CEA databases
3. **Weather Helper** - Fetch weather data
4. **Surroundings Helper** - Get context buildings
5. **Terrain Helper** - Get elevation data
6. **Streets Helper** - Get street network (if planning district systems)
7. **Trees Helper** - Import trees (if significant tree coverage)
8. **Archetypes Mapper** - Assign building properties

Then proceed to analysis:
- Solar Radiation Analysis
- Energy Demand Forecasting
- Renewable Energy Assessment
- Life Cycle Analysis
- Supply System Optimisation

---

## Related Features
- **[CEA-4 Format Helper](09-utilities.md#cea-4-format-helper)** - Verify data format
- **[Solar Radiation Analysis](02-solar-radiation.md)** - Uses surroundings, terrain, weather
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Uses weather, building properties
- **[Thermal Network Design](05-thermal-network.md)** - Uses streets

---

[← Back: Supply System Optimisation](07-supply-optimization.md) | [Back to Index](index.md) | [Next: Utilities →](09-utilities.md)
