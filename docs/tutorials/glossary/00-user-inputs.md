# User Inputs

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **6**

---

## Files

- [`get_site_polygon`](#get_site_polygon)
- [`get_street_network`](#get_street_network)
- [`get_surroundings_geometry`](#get_surroundings_geometry)
- [`get_terrain`](#get_terrain)
- [`get_weather`](#get_weather)
- [`get_zone_geometry`](#get_zone_geometry)

---

### `get_site_polygon`

- **Path**: `inputs/building-geometry/site.shp`
- **File type**: `shp`
- **Created by**: _user input_
- **Used by**: `zone_helper`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `FID` | Shapefile ID | int | `[-]` | {0...n} |
| `geometry` | Shapefile POLYGON | Polygon | `NA` |  |

---

### `get_street_network`

- **Path**: `inputs/networks/streets.shp`
- **File type**: `shp`
- **Created by**: _user input_
- **Used by**: `network_layout`, `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `geometry` | Geometry | LineString | `NA` |  |
| `Id` | Unique street ID. It must start with a letter. | string | `NA` | alphanumeric |

---

### `get_surroundings_geometry`

- **Path**: `inputs/building-geometry/surroundings.shp`
- **File type**: `shp`
- **Created by**: _user input_
- **Used by**: `radiation`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `floors_ag` | Number of floors above ground (incl. ground floor, Minimum one floor is needed) | int | `[-]` | {1...n} |
| `geometry` | Shapefile POLYGON | Polygon | `NA` |  |
| `height_ag` | Height above ground (incl. ground floor, Minimum one floor is needed) | float | `[m]` | {2.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `REFERENCE` | Reference to data (if any) | string | `NA` | alphanumeric |

---

### `get_terrain`

- **Path**: `inputs/topography/terrain.tif`
- **File type**: `tif`
- **Created by**: _user input_
- **Used by**: `radiation`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `raster_value` | TODO | TODO | `TODO` |  |

---

### `get_weather`

- **Path**: `databases/weather/Zug-inducity_1990_2010_TMY.epw`
- **File type**: `epw`
- **Created by**: _user input_
- **Used by**: `weather_helper`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `aerosol_opt_thousandths (index = 29)` | TODO | TYPE | `TODO` |  |
| `Albedo (index = 32)` | Albedo | TYPE | `TODO` |  |
| `atmos_Pa (index = 9)` | Atmospheric pressure | TYPE | `TODO` |  |
| `ceiling_hgt_m (index = 25)` | TODO | TYPE | `TODO` |  |
| `datasource (index = 5)` | Source of data | TYPE | `TODO` |  |
| `day (index = 2)` | TODO | TYPE | `TODO` |  |
| `days_last_snow (index = 31)` | Days since last snow | TYPE | `TODO` |  |
| `dewpoint_C (index = 7)` | TODO | TYPE | `TODO` |  |
| `difhorillum_lux (index = 18)` | TODO | TYPE | `TODO` |  |
| `difhorrad_Whm2 (index = 15)` | TODO | TYPE | `TODO` |  |
| `dirnorillum_lux (index = 17)` | TODO | TYPE | `TODO` |  |
| `dirnorrad_Whm2 (index = 14)` | TODO | TYPE | `TODO` |  |
| `drybulb_C (index = 6)` | TODO | TYPE | `TODO` |  |
| `extdirrad_Whm2 (index = 11)` | TODO | TYPE | `TODO` |  |
| `exthorrad_Whm2 (index = 10)` | TODO | TYPE | `TODO` |  |
| `glohorillum_lux (index = 16)` | TODO | TYPE | `TODO` |  |
| `glohorrad_Whm2 (index = 13)` | TODO | TYPE | `TODO` |  |
| `horirsky_Whm2 (index = 12)` | TODO | TYPE | `TODO` |  |
| `hour (index = 3)` | TODO | TYPE | `TODO` |  |
| `liq_precip_depth_mm (index = 33)` | TODO | TYPE | `TODO` |  |
| `liq_precip_rate_Hour (index = 34)` | TODO | TYPE | `TODO` |  |
| `minute (index = 4)` | TODO | TYPE | `TODO` |  |
| `month (index = 1)` | TODO | TYPE | `TODO` |  |
| `opaqskycvr_tenths (index = 23)` | TODO | TYPE | `TODO` |  |
| `precip_wtr_mm (index = 28)` | TODO | TYPE | `TODO` |  |
| `presweathcodes (index = 27)` | TODO | TYPE | `TODO` |  |
| `presweathobs (index = 26)` | TODO | TYPE | `TODO` |  |
| `relhum_percent (index = 8)` | TODO | TYPE | `TODO` |  |
| `snowdepth_cm (index = 30)` | TODO | TYPE | `TODO` |  |
| `totskycvr_tenths (index = 22)` | TODO | TYPE | `TODO` |  |
| `visibility_km (index = 24)` | TODO | TYPE | `TODO` |  |
| `winddir_deg (index = 20)` | TODO | TYPE | `TODO` |  |
| `windspd_ms (index = 21)` | TODO | TYPE | `TODO` |  |
| `year (index = 0)` | TODO | TYPE | `TODO` |  |
| `zenlum_lux (index = 19)` | TODO | TYPE | `TODO` |  |

---

### `get_zone_geometry`

- **Path**: `inputs/building-geometry/zone.shp`
- **File type**: `shp`
- **Created by**: _user input_
- **Used by**: `archetypes_mapper`, `decentralized`, `demand`, `emissions`, `network_layout`, `optimization`, `photovoltaic`, `photovoltaic_thermal`, `radiation`, `occupancy`, `sewage_potential`, `shallow_geothermal_potential`, `solar_collector`, `thermal_network`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `const_type` | Construction Archetypes | string | `[-]` | alphanumeric |
| `floors_ag` | Number of floors above ground (incl. ground floor, minimum one floor is needed) | int | `[-]` | {1...n} |
| `floors_bg` | Number of floors below ground (basement) | int | `[-]` | {0...n} |
| `geometry` | Shapefile POLYGON | Polygon | `NA` |  |
| `height_ag` | Height above ground (incl. ground floor, minimum one floor is needed) | float | `[m]` | {2.0...n} |
| `height_bg` | Height below ground (basement) | float | `[m]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `reference` | Reference to data (if any) | string | `NA` | alphanumeric |
| `use_type1` | First (Main) Use type of the building | string | `[-]` | alphanumeric |
| `use_type1r` | Fraction of gross floor area for first Use Type | float | `[m2/m2]` | {0.0...1.0} |
| `use_type2` | Second Use type of the building | string | `[-]` | alphanumeric |
| `use_type2r` | Fraction of gross floor area for second Use Type | float | `[m2/m2]` | {0.0...1.0} |
| `use_type3` | Third Use type of the building | string | `[-]` | alphanumeric |
| `use_type3r` | Fraction of gross floor area for third Use Type | float | `[m2/m2]` | {0.0...1.0} |
| `void_deck` | Number of floors (from the ground up) with an open envelope (default = 0, should be lower than floors_ag.) | int | `[-]` | {0...n} |
| `year` | Construction year | int | `[-]` | {0...n} |

---

[Glossary index](index.md) | [Solar Radiation Analysis →](02-solar-radiation.md)
