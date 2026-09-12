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
{CEA Project}/{Current Scenario}/inputs/database/
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
- `indoor_comfort.csv` - Setpoint temperatures, acceptable ranges
- `hvac.csv` - HVAC system types
- `supply.csv` - Energy supply configuration

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
- Window-wall ratios (envelope.csv)
- HVAC system types (hvac.csv)
- Occupancy schedules (internal_loads.csv)
- Setpoint temperatures (indoor_comfort.csv)

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

## Archetype Lock

Only the **zone** table is authored by you. Five of the other input-editor tabs are *derived*
from it by the Archetypes Mapper, using each building's archetype:

| you author | CEA derives from the archetype |
|---|---|
| zone, surroundings, trees | envelope, HVAC, indoor comfort, internal loads, supply |

Building **schedules** are derived too, though they are not a tab.

Editing a derived table directly makes the construction type stop describing the building it
labels — the archetype says one thing, the tables another, and nothing records that. The
**Archetype Lock** toggle in the input editor decides who owns those tables.

### Locked

CEA owns the derived tables.

- The five derived tabs are **read-only** (bulk *Edit Selection* too).
- **The zone tab stays fully editable** — geometry, names, everything.
- Change a building's **archetype** in the zone tab and CEA regenerates its derived tables when
  you save. Add a building and it gets its derived rows the same way.

The archetype is more than `const_type`. These columns all select it:

```
const_type
use_type1, use_type1r, use_type2, use_type2r, use_type3, use_type3r
year
```

Changing `use_type1` matters as much as changing `const_type`: use type drives indoor comfort
and internal loads, construction type drives envelope, HVAC and supply.

Editing geometry — `height_ag`, `floors_ag`, the footprint — does **not** trigger a
regeneration, because it does not change which archetype applies.

### Unlocked

You own the derived tables and may edit them freely. Nothing on disk changes when you unlock.

Once your edits mean the derived tables no longer match the archetypes, CEA marks the
**archetype columns in the zone tab**, with a tooltip. The construction type shown there no
longer describes the building, and the mark is there so a reader knows not to trust it.

### Re-locking

Re-locking regenerates envelope, HVAC, indoor comfort, internal loads, supply **and the
building schedules** for every building, from their archetypes. **Any edits you made to those
tables are lost.** The confirmation names the tabs and the number of buildings affected.

### Defaults

| scenario | default |
|---|---|
| created by CEA | **locked** — it has just been mapped, so it is consistent |
| existing, from before this feature | **unlocked** |

Existing scenarios default to unlocked deliberately: they may already contain hand-edits, and
treating them as locked would licence CEA to overwrite work it knows nothing about. Lock one
when you are ready for CEA to regenerate its derived tables.

### The lock is enforced when you save, not just in the editor

Read-only tabs are the visible half. CEA also refuses to write the derived tables while locked,
whatever is sent to it — so a browser tab left open from before the lock cannot overwrite them.

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

4. Trees saved to `{scenario}/inputs/tree-geometry/trees.shp`

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

## Void Decks

A **void deck** is the open, unenclosed portion at the bottom of a building — the open ground
floors common in Singapore HDB blocks, or a building on stilts. It has no facade, contributes
no floor area, and leaves the underside exposed to outside air.

Record it in the zone geometry, in **metres**:

| Column | Meaning |
|---|---|
| `height_vd` | Height of the void deck above ground, in metres. Optional; `0` or absent means none. |
| `void_deck` | **Legacy.** The same void expressed as a whole number of floors. |

### How `floors_ag` is counted

This is the part to get right, because the two columns differ:

| | `height_ag` | `floors_ag` |
|---|---|---|
| with `height_vd` | void deck **+** enclosed building | **enclosed storeys only** |
| with `void_deck` (legacy) | void deck **+** enclosed building | **every storey**, void ones included |

So the same building can be written either way:

```
A 15 m block: 6 m open void deck, then 3 enclosed floors of 3 m

  legacy   void_deck = 2   floors_ag = 5   height_ag = 15
  metres   height_vd = 6   floors_ag = 3   height_ag = 15
```

Both give the same floor area, the same storey height, and the same 3D solid.

The storey height of the enclosed part is always

```
(height_ag − void deck height) ÷ enclosed floors
```

which is `(15 − 6) ÷ 3 = 3 m` either way. Note the denominator is the **enclosed** floor
count — that is `floors_ag` itself with `height_vd`, but `floors_ag − void_deck` with the
legacy column.

### Why metres matter: a void deck taller than a storey

A real void deck is often taller than the floors above it, and whole floors cannot express
that. An HDB-style block with a 4.5 m void deck under four 2.8 m residential floors:

```
  height_vd = 4.5    floors_ag = 4    height_ag = 15.7
  -> storey height (15.7 − 4.5) / 4 = 2.8 m, and 4 whole floors of area
```

Forcing that onto a single uniform storey grid would give a 3.14 m storey — neither the real
void deck nor the real floor — and understate the floor area by about 11%.

### Metres, not floors

`void_deck` could only express whole storeys, so a 4.5 m void in a building with 3 m floors had
to be rounded. `height_vd` records the height directly, so the void can sit anywhere.

**Every new scenario gets `height_vd`, set to 0.** Whether you generate the zone from
OpenStreetMap or upload your own, the column is created so you can edit it straight away
without adding a field in GIS. `0` means the building is enclosed to the ground.

**Existing scenarios keep working and are not modified.** Where `height_vd` is absent, CEA reads
`void_deck` and converts it at that building's own storey height (`height_ag / floors_ag`) —
the same conversion it always applied internally, so results do not change. Neither column is
required; a scenario with neither simply has no void decks.

Where both columns are present, CEA decides **per building, on the value**: a building whose
`height_vd` cell has a number uses it (and CEA warns that its `void_deck` is being ignored),
while a **blank** cell falls back to `void_deck`.

That matters when you open an older scenario in the input editor: the editor shows every column
in the schema, so you will see an empty `height_vd` column beside your populated `void_deck`.
**This is expected and harmless** — leaving it empty changes nothing. Entering a value switches
that building to metres; entering `0` removes its void deck.

You never have to migrate a CEA-4 scenario by hand. Add or edit `height_vd` only when you want a
void that is not a whole number of storeys.

### Upgrading from CEA-3

CEA-3 stored the void deck in `architecture.dbf`, in whole floors. The CEA-4 migration moves it
into the zone geometry **as `void_deck`, unchanged** — it is not converted to metres.

That is deliberate. Converting would mean redefining `floors_ag` to the enclosed count, and
`floors_ag` is read elsewhere as the total above-ground storey count (the database migration
rescales the occupied-area share `Ns` by `(floors_ag + floors_bg) / floors_ag`). Rewriting it
would quietly change occupied areas and demand for every migrated building. A migrated scenario
therefore keeps exactly the areas it had.

To move a building to metres yourself, convert both columns together: set
`height_vd = void_deck × (height_ag / floors_ag)`, reduce `floors_ag` by `void_deck`, and remove
`void_deck`. For the example above: `void_deck = 2, floors_ag = 5` becomes
`height_vd = 6, floors_ag = 3`.

### What it affects

- **Floor area** — the void contributes no GFA, so conditioned and occupied areas shrink with it
- **Embodied emissions** — void storeys have no partitions, no floor slab and no technical
  systems, so they are excluded from the embodied floor area as well
- **Facade area** — no walls or windows over the void height, which lowers embodied emissions
- **Heat loss** — the underside is exposed to outside air rather than sitting on the ground
- **Radiation** — the building solid starts at the top of the void deck
- **Radiation engine** — CRAX does not support void decks, so CEA falls back to DAYSIM when any
  building has one (see [Solar Radiation](02-solar-radiation.md))

### Rules

- Always measured **from ground level up**. CEA does not model an open storey part-way up a
  building.
- Must leave at least **2 m of height per enclosed floor**. CEA measures this on the enclosed
  part, not on `height_ag`, so a tall void deck cannot hide storeys squeezed into what is left.
- Cannot be negative.

---

## Database Editor: Material Layers

The Database Editor can now edit **material layers** for envelope assemblies, and derive the
thermal and carbon properties from them rather than requiring you to enter those numbers by
hand.

### The materials database

Materials live in `COMPONENTS/MATERIALS/MATERIALS.csv` and are referenced by name from the
envelope assemblies.

Only the **Swiss (CH)** database ships with a materials file. Open **COMPONENTS → MATERIALS**
in a scenario built from another region and the editor explains this and offers to import the
Swiss set, which is based on KBOB data.

> **Use at your own risk.** The imported values are specific to Switzerland and may not
> represent materials available in your region.

### Building up an envelope from layers

On the **ENVELOPE** tabs each assembly row carries up to three layers:

| Column | Meaning |
|---|---|
| `material_name_1` … `material_name_3` | Material, chosen from a dropdown of the materials database |
| `thickness_1_m` … `thickness_3_m` | Layer thickness in metres |

The material dropdowns only list names that exist in your materials file, so a row cannot
reference a material that is not there. These six columns appear only when a materials file
is present.

### Derived columns

Once a row has at least one material with a thickness greater than zero, CEA derives its
properties from the layers and **locks** the derived cells — they are computed, so editing
them by hand would be silently overwritten:

| Derived | Example column |
|---|---|
| U-value | `U_base` |
| Total embodied carbon | `GHG_floor_kgCO2m2` |
| Biogenic carbon | `GHG_biogenic_floor_kgCO2m2` |
| Production carbon (A1-A3) | `GHG_production_floor_kgCO2m2` |
| Disposal carbon (C2-C4) | `GHG_demolition_floor_kgCO2m2` |

Splitting embodied carbon into **production** and **demolition** is what lets the
[Emissions](06-2-emissions.md) feature report those EN 15978 modules separately.

### What you must still provide

Layers are optional — a database with no materials file keeps working exactly as before, with
U-values and carbon entered directly.

| Situation | Required |
|---|---|
| Row has at least one material with thickness > 0 | U-value and GHG columns may be left empty; they are derived |
| Row has no usable material layer | U-value and GHG columns must be filled in |
| Every row | Service life must be greater than zero |

Values are validated when you save, and errors name the row and column at fault. A genuine
zero is accepted — CEA distinguishes "zero" from "not filled in".

### Cross-check

Where a row has both derived values and values already in the file, CEA compares them and
warns if they differ by more than **1%**. Small differences are expected: published totals are
rounded, so production plus disposal rarely reproduces the stated total exactly.

### Tips

- Biogenic carbon is stored as a **negative** number throughout, representing carbon held in
  the material. Do not enter it as positive.
- After changing materials, re-run any analysis that reads envelope properties — the derived
  values change with them.

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

[← Back: Supply System Optimisation](07-supply-optimisation.md) | [Back to Index](index.md) | [Next: Utilities →](09-utilities.md)
