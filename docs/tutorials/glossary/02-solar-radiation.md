# Solar Radiation Analysis

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **4**

---

## Files

- [`get_radiation_building`](#get_radiation_building)
- [`get_radiation_building_sensors`](#get_radiation_building_sensors)
- [`get_radiation_materials`](#get_radiation_materials)
- [`get_radiation_metadata`](#get_radiation_metadata)

---

### `get_radiation_building`

- **Path**: `outputs/data/solar-radiation/{building}_radiation.csv`
- **File type**: `csv`
- **Created by**: `radiation`
- **Used by**: `demand`, `photovoltaic`, `photovoltaic_thermal`, `solar_collector`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Date` | Date and time in hourly steps | date | `NA` | YYYY-MM-DD |
| `roofs_top_kW` | solar incident on the roof tops | float | `[kWh]` | {0.0...n} |
| `roofs_top_m2` | roof top area | float | `[m2]` | {0.0...n} |
| `walls_east_kW` | solar incident on the east facing facades excluding windows | float | `[kWh]` | {0.0...n} |
| `walls_east_m2` | area of the east facing facades excluding windows | float | `[m2]` | {0.0...n} |
| `walls_north_kW` | solar incident on the north facing facades excluding windows | float | `[kWh]` | {0.0...n} |
| `walls_north_m2` | area of the north facing facades excluding windows | float | `[m2]` | {0.0...n} |
| `walls_south_kW` | solar incident on the south facing facades excluding windows | float | `[kWh]` | {0.0...n} |
| `walls_south_m2` | area of the south facing facades excluding windows | float | `[m2]` | {0.0...n} |
| `walls_west_kW` | solar incident on the west facing facades excluding windows | float | `[kWh]` | {0.0...n} |
| `walls_west_m2` | area of the south facing facades excluding windows | float | `[m2]` | {0.0...n} |
| `windows_east_kW` | solar incident on windows on the south facing facades | float | `[kWh]` | {0.0...n} |
| `windows_east_m2` | window area on the east facing facades | float | `[m2]` | {0.0...n} |
| `windows_north_kW` | solar incident on windows on the south facing facades | float | `[kWh]` | {0.0...n} |
| `windows_north_m2` | window area on the north facing facades | float | `[m2]` | {0.0...n} |
| `windows_south_kW` | solar incident on windows on the south facing facades | float | `[kWh]` | {0.0...n} |
| `windows_south_m2` | window area on the south facing facades | float | `[m2]` | {0.0...n} |
| `windows_west_kW` | solar incident on windows on the west facing facades | float | `[kWh]` | {0.0...n} |
| `windows_west_m2` | window area on the west facing facades | float | `[m2]` | {0.0...n} |

---

### `get_radiation_building_sensors`

- **Path**: `outputs/data/solar-radiation/B001_insolation_Whm2.json`
- **File type**: `json`
- **Created by**: `radiation`
- **Used by**: `demand`, `photovoltaic`, `photovoltaic_thermal`, `solar_collector`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `srf0` | TODO | float | `TODO` | {n...n} |

---

### `get_radiation_materials`

- **Path**: `outputs/data/solar-radiation/buidling_materials.csv`
- **File type**: `csv`
- **Created by**: `radiation`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `G_win` | Solar heat gain coefficient. Defined according to ISO 13790. | float | `[-]` | {0.0...1.0} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `r_roof` | Reflectance in the Red spectrum. Defined according Radiance. (long-wave) | float | `[-]` | {0.0...n} |
| `r_wall` | Reflectance in the Red spectrum. Defined according Radiance. (long-wave) | float | `[-]` | {0.0...n} |
| `type_base` | Basement floor construction assembly (relates to "code" in ENVELOPE assemblies) | string | `NA` | alphanumeric |
| `type_floor` | Internal floor construction assembly (relates to "code" in ENVELOPE assemblies) | string | `NA` | alphanumeric |
| `type_roof` | Roof construction assembly (relates to "code" in ENVELOPE assemblies) | string | `NA` | alphanumeric |
| `type_wall` | External wall construction assembly (relates to "code" in ENVELOPE assemblies) | string | `NA` | alphanumeric |
| `type_win` | Window assembly (relates to "code" in ENVELOPE assemblies) | string | `NA` | alphanumeric |

---

### `get_radiation_metadata`

- **Path**: `outputs/data/solar-radiation/B001_geometry.csv`
- **File type**: `csv`
- **Created by**: `radiation`
- **Used by**: `demand`, `photovoltaic`, `photovoltaic_thermal`, `solar_collector`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `AREA_m2` | Surface area. | float | `[m2]` | {0.0...n} |
| `BUILDING` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `intersection` | flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected) | float | `[-]` | {0, 1} |
| `orientation` | Orientation of the surface (north/east/south/west/top) | string | `NA` | {north, east, west, south, top} |
| `SURFACE` | Unique surface ID for each building exterior surface. | string | `NA` | alphanumeric |
| `TYPE` | Surface typology. | string | `NA` | {walls, windows, roofs} |
| `Xcoor` | Describes the position of the x vector. | float | `[-]` | {0.0...n} |
| `Xdir` | Directional scalar of the x vector. | float | `[-]` | {-1.0...1.0} |
| `Ycoor` | Describes the position of the y vector. | float | `[-]` | {0.0...n} |
| `Ydir` | Directional scalar of the y vector. | float | `[-]` | {-1.0...1.0} |
| `Zcoor` | Describes the position of the z vector. | float | `[-]` | {0.0...n} |
| `Zdir` | Directional scalar of the z vector. | float | `[-]` | {-1.0...1.0} |

---

[← User Inputs](00-user-inputs.md) | [Glossary index](index.md) | [Renewable Energy Potential Assessment →](03-renewable-energy.md)
