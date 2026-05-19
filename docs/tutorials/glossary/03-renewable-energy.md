# Renewable Energy Potential Assessment

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **15**

---

## Files

- [`get_geothermal_potential`](#get_geothermal_potential)
- [`get_sewage_heat_potential`](#get_sewage_heat_potential)
- [`get_water_body_potential`](#get_water_body_potential)
- [`PV_metadata_results`](#pv_metadata_results)
- [`PV_results`](#pv_results)
- [`PV_total_buildings`](#pv_total_buildings)
- [`PV_totals`](#pv_totals)
- [`PVT_metadata_results`](#pvt_metadata_results)
- [`PVT_results`](#pvt_results)
- [`PVT_total_buildings`](#pvt_total_buildings)
- [`PVT_totals`](#pvt_totals)
- [`SC_metadata_results`](#sc_metadata_results)
- [`SC_results`](#sc_results)
- [`SC_total_buildings`](#sc_total_buildings)
- [`SC_totals`](#sc_totals)

---

### `get_geothermal_potential`

- **Path**: `outputs/data/potentials/Shallow_geothermal_potential.csv`
- **File type**: `csv`
- **Created by**: `shallow_geothermal_potential`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_avail_m2` | areas available to install ground source heat pumps | float | `[m2]` | {0.0...n} |
| `QGHP_kW` | geothermal heat potential | float | `[kW]` | {0.0...n} |
| `Ts_C` | ground temperature | float | `[C]` | {0.0...n} |

---

### `get_sewage_heat_potential`

- **Path**: `outputs/data/potentials/Sewage_heat_potential.csv`
- **File type**: `csv`
- **Created by**: `sewage_potential`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `mww_zone_kWperC` | heat capacity of total sewage in a zone | float | `[kW/C]` | {0.0...n} |
| `Qsw_kW` | heat extracted from sewage flows | float | `[kWh]` | {0.0...n} |
| `T_in_HP_C` | Inlet temperature of the sweage heapump | float | `[C]` | {0.0...n} |
| `T_in_sw_C` | Inlet temperature of sewage flows | float | `[C]` | {0.0...n} |
| `T_out_HP_C` | Outlet temperature of the sewage heatpump | float | `[C]` | {0.0...n} |
| `T_out_sw_C` | Outlet temperature of sewage flows | float | `[C]` | {0.0...n} |
| `Ts_C` | Average temperature of sewage flows | float | `[C]` | {0.0...n} |

---

### `get_water_body_potential`

- **Path**: `outputs/data/potentials/Water_body_potential.csv`
- **File type**: `csv`
- **Created by**: `water_body_potential`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `QLake_kW` | thermal potential from water body | float | `[kWh]` | {0.0...n} |
| `Ts_C` | average temperature of the water body | float | `[C]` | {0.0...n} |

---

### `PV_metadata_results`

- **Path**: `outputs/data/potentials/solar/B001_PV_sensors.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `area_installed_module_m2` | The area of the building surface covered by one solar panel | float | `[m2]` | {0.0...n} |
| `AREA_m2` | Surface area. | float | `[m2]` | {0.0...n} |
| `array_spacing_m` | Spacing between solar arrays. | float | `[m]` | {0.0...n} |
| `B_deg` | Tilt angle of the installed solar panels | float | `[deg]` | {0.0...n} |
| `BUILDING` | Unique building ID. It must start with a letter. | string | `[-]` | alphanumeric |
| `CATB` | Category according to the tilt angle of the panel | int | `[-]` | {0...n} |
| `CATGB` | Category according to the annual radiation on the panel surface | int | `[-]` | {0...n} |
| `CATteta_z` | Category according to the surface azimuth of the panel | int | `[-]` | {0...n} |
| `intersection` | flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected) | int | `[-]` | {0, 1} |
| `orientation` | Orientation of the surface (north/east/south/west/top) | string | `[-]` | {north, south, west, east, top} |
| `SURFACE` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface_azimuth_deg` | Azimuth angle of the panel surface e.g. south facing = 180 deg | float | `[deg]` | {0.0...n} |
| `tilt_deg` | Tilt angle of roof or walls | float | `[deg]` | {0.0...n} |
| `total_rad_Whm2` | Total radiatiative potential of a given surfaces area. | float | `[Wh/m2]` | {0.0...n} |
| `TYPE` | Surface typology. | string | `[-]` | {walls, roofs} |
| `type_orientation` | Concatenated surface type and orientation. | string | `[-]` | {walls_east, walls_south, walls_north, walls_west, roofs_top} |
| `Xcoor` | Describes the position of the x vector. | float | `[-]` | {0.0...n} |
| `Xdir` | Directional scalar of the x vector. | float | `[-]` | {-1.0...1.0} |
| `Ycoor` | Describes the position of the y vector. | float | `[-]` | {0.0...n} |
| `Ydir` | Directional scalar of the y vector. | float | `[-]` | {-1.0...1.0} |
| `Zcoor` | Describes the position of the z vector. | float | `[-]` | {0.0...n} |
| `Zdir` | Directional scalar of the z vector. | float | `[-]` | {-1.0...1.0} |

---

### `PV_results`

- **Path**: `outputs/data/potentials/solar/B001_PV.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PV_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `NA` | YYYY-MM-DD |
| `E_PV_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `PV_roofs_top_E_kWh` | Electricity production from photovoltaic panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PV_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PV_walls_east_E_kWh` | Electricity production from photovoltaic panels on east facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_north_E_kWh` | Electricity production from photovoltaic panels on north facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_south_E_kWh` | Electricity production from photovoltaic panels on south facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_west_E_kWh` | Electricity production from photovoltaic panels on west facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |

---

### `PV_total_buildings`

- **Path**: `outputs/data/potentials/solar/PV_total_buildings.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PV_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `E_PV_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `[-]` | alphanumeric |
| `PV_roofs_top_E_kWh` | Electricity production from photovoltaic panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PV_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PV_walls_east_E_kWh` | Electricity production from photovoltaic panels on east facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_north_E_kWh` | Electricity production from photovoltaic panels on north facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_south_E_kWh` | Electricity production from photovoltaic panels on south facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_west_E_kWh` | Electricity production from photovoltaic panels on west facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |

---

### `PV_totals`

- **Path**: `outputs/data/potentials/solar/PV_total.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PV_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `NA` | YYYY-MM-DD |
| `E_PV_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `PV_roofs_top_E_kWh` | Electricity production from photovoltaic panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PV_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PV_walls_east_E_kWh` | Electricity production from photovoltaic panels on east facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_north_E_kWh` | Electricity production from photovoltaic panels on north facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_south_E_kWh` | Electricity production from photovoltaic panels on south facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PV_walls_west_E_kWh` | Electricity production from photovoltaic panels on west facades | float | `[kWh]` | {0.0...n} |
| `PV_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |

---

### `PVT_metadata_results`

- **Path**: `outputs/data/potentials/solar/B001_PVT_sensors.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic_thermal`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `area_installed_module_m2` | The area of the building surface covered by one solar panel | float | `[m2]` | {0.0...n} |
| `AREA_m2` | Surface area. | float | `[m2]` | {0.0...n} |
| `array_spacing_m` | Spacing between solar arrays. | float | `[m]` | {0.0...n} |
| `B_deg` | Tilt angle of the installed solar panels | float | `[deg]` | {0.0...n} |
| `BUILDING` | Unique building ID. It must start with a letter. | string | `[-]` | alphanumeric |
| `CATB` | Category according to the tilt angle of the panel | int | `[-]` | {0...n} |
| `CATGB` | Category according to the annual radiation on the panel surface | int | `[-]` | {0...n} |
| `CATteta_z` | Category according to the surface azimuth of the panel | int | `[-]` | {0...n} |
| `intersection` | flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected) | int | `[-]` | {0, 1} |
| `orientation` | Orientation of the surface (north/east/south/west/top) | string | `[-]` | {north, south, west, east, top} |
| `SURFACE` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface_azimuth_deg` | Azimuth angle of the panel surface e.g. south facing = 180 deg | float | `[deg]` | {0.0...n} |
| `tilt_deg` | Tilt angle of roof or walls | float | `[deg]` | {0.0...n} |
| `total_rad_Whm2` | Total radiatiative potential of a given surfaces area. | float | `[Wh/m2]` | {0.0...n} |
| `TYPE` | Surface typology. | string | `[-]` | {walls, roofs} |
| `type_orientation` | Concatenated surface type and orientation. | string | `[-]` | {walls_east, walls_south, walls_north, walls_west, roofs_top} |
| `Xcoor` | Describes the position of the x vector. | float | `[-]` | {0.0...n} |
| `Xdir` | Directional scalar of the x vector. | float | `[-]` | {-1.0...1.0} |
| `Ycoor` | Describes the position of the y vector. | float | `[-]` | {0.0...n} |
| `Ydir` | Directional scalar of the y vector. | float | `[-]` | {-1.0...1.0} |
| `Zcoor` | Describes the position of the z vector. | float | `[-]` | {0.0...n} |
| `Zdir` | Directional scalar of the z vector. | float | `[-]` | {-1.0...1.0} |

---

### `PVT_results`

- **Path**: `outputs/data/potentials/solar/B001_PVT.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic_thermal`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PVT_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `[datetime]` | YYYY-MM-DD |
| `E_PVT_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Eaux_PVT_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `mcp_PVT_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector. | float | `[kW/C]` | {0.0...n} |
| `PVT_roofs_top_E_kWh` | Electricity production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PVT_roofs_top_Q_kWh` | Heat production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_E_kWh` | Electricity production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_east_Q_kWh` | Heat production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_E_kWh` | Electricity production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_north_Q_kWh` | Heat production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_E_kWh` | Electricity production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_south_Q_kWh` | Heat production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_E_kWh` | Electricity production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `PVT_walls_west_Q_kWh` | Heat production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `Q_PVT_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_PVT_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |
| `T_PVT_re_C` | Collector hot water return temperature. | float | `[C]` | {0.0...n} |
| `T_PVT_sup_C` | Collector heating supply temperature. | float | `[C]` | {0.0...n} |

---

### `PVT_total_buildings`

- **Path**: `outputs/data/potentials/solar/PVT_total_buildings.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic_thermal`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PVT_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `E_PVT_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Eaux_PVT_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `name` | Unique building ID. | string | `[-]` | alphanumeric |
| `PVT_roofs_top_E_kWh` | Electricity production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PVT_roofs_top_Q_kWh` | Heat production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_E_kWh` | Electricity production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_east_Q_kWh` | Heat production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_E_kWh` | Electricity production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_north_Q_kWh` | Heat production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_E_kWh` | Electricity production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_south_Q_kWh` | Heat production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_E_kWh` | Electricity production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `PVT_walls_west_Q_kWh` | Heat production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `Q_PVT_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_PVT_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |

---

### `PVT_totals`

- **Path**: `outputs/data/potentials/solar/PVT_total.csv`
- **File type**: `csv`
- **Created by**: `photovoltaic_thermal`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_PVT_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `NA` | YYYY-MM-DD |
| `E_PVT_gen_kWh` | Total electricity generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Eaux_PVT_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `mcp_PVT_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector. | float | `[kW/C]` | {0.0...n} |
| `PVT_roofs_top_E_kWh` | Electricity production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `PVT_roofs_top_Q_kWh` | Heat production from photovoltaic-thermal panels on roof tops | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_E_kWh` | Electricity production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_east_Q_kWh` | Heat production from photovoltaic-thermal panels on east facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_E_kWh` | Electricity production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_north_Q_kWh` | Heat production from photovoltaic-thermal panels on north facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_E_kWh` | Electricity production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `PVT_walls_south_Q_kWh` | Heat production from photovoltaic-thermal panels on south facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_E_kWh` | Electricity production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `PVT_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `PVT_walls_west_Q_kWh` | Heat production from photovoltaic-thermal panels on west facades | float | `[kWh]` | {0.0...n} |
| `Q_PVT_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_PVT_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |
| `T_PVT_re_C` | Collector heating supply temperature. | float | `[C]` | {0.0...n} |
| `T_PVT_sup_C` | Collector heating supply temperature. | float | `[C]` | {0.0...n} |

---

### `SC_metadata_results`

- **Path**: `outputs/data/potentials/solar/B001_SC_ET_sensors.csv`
- **File type**: `csv`
- **Created by**: `solar_collector`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `area_installed_module_m2` | The area of the building surface covered by one solar panel | float | `[m2]` | {0.0...n} |
| `AREA_m2` | Surface area. | float | `[m2]` | {0.0...n} |
| `array_spacing_m` | Spacing between solar arrays. | float | `[m]` | {0.0...n} |
| `B_deg` | Tilt angle of the installed solar panels | float | `[deg]` | {0.0...n} |
| `BUILDING` | Unique building ID. It must start with a letter. | string | `[-]` | alphanumeric |
| `CATB` | Category according to the tilt angle of the panel | int | `[-]` | {0...n} |
| `CATGB` | Category according to the annual radiation on the panel surface | int | `[-]` | {0...n} |
| `CATteta_z` | Category according to the surface azimuth of the panel | int | `[-]` | {0...n} |
| `intersection` | flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected) | int | `[-]` | {0, 1} |
| `orientation` | Orientation of the surface (north/east/south/west/top) | string | `[-]` | {north, south, west, east, top} |
| `SURFACE` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface` | Unique surface ID for each building exterior surface. | string | `[-]` | alphanumeric |
| `surface_azimuth_deg` | Azimuth angle of the panel surface e.g. south facing = 180 deg | float | `[deg]` | {0.0...n} |
| `tilt_deg` | Tilt angle of roof or walls | float | `[deg]` | {0.0...n} |
| `total_rad_Whm2` | Total radiatiative potential of a given surfaces area. | float | `[Wh/m2]` | {0.0...n} |
| `TYPE` | Surface typology. | string | `[-]` | {walls, roofs} |
| `type_orientation` | Concatenated surface type and orientation. | string | `[-]` | {walls_east, walls_south, walls_north, walls_west, roofs_top} |
| `Xcoor` | Describes the position of the x vector. | float | `[-]` | {0.0...n} |
| `Xdir` | Directional scalar of the x vector. | float | `[-]` | {-1.0...1.0} |
| `Ycoor` | Describes the position of the y vector. | float | `[-]` | {0.0...n} |
| `Ydir` | Directional scalar of the y vector. | float | `[-]` | {-1.0...1.0} |
| `Zcoor` | Describes the position of the z vector. | float | `[-]` | {0.0...n} |
| `Zdir` | Directional scalar of the z vector. | float | `[-]` | {-1.0...1.0} |

---

### `SC_results`

- **Path**: `outputs/data/potentials/solar/B001_SC_ET.csv`
- **File type**: `csv`
- **Created by**: `solar_collector`
- **Used by**: `decentralized`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_SC_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `NA` | YYYY-MM-DD |
| `Eaux_SC_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `mcp_SC_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector. | float | `[kW/C]` | {0.0...n} |
| `Q_SC_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_SC_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |
| `SC_ET_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `SC_ET_roofs_top_Q_kWh` | Heat production from solar collectors on roof tops | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_east_Q_kWh` | Heat production from solar collectors on east facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_north_Q_kWh` | Heat production from solar collectors on north facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_south_Q_kWh` | Heat production from solar collectors on south facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_west_m2` | Collector surface area on west facades. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_west_Q_kWh` | Heat production from solar collectors on west facades | float | `[kWh]` | {0.0...n} |
| `T_SC_re_C` | Collector hot water return temperature. | float | `[C]` | {0.0...n} |
| `T_SC_sup_C` | Collector hot water supply temperature. | float | `[C]` | {0.0...n} |

---

### `SC_total_buildings`

- **Path**: `outputs/data/potentials/solar/SC_ET_total_buildings.csv`
- **File type**: `csv`
- **Created by**: `solar_collector`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_SC_m2` | Total area of investigated collector. | float | `[m2]` | {0.0...n} |
| `Eaux_SC_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `name` | Unique building ID. | string | `[-]` | alphanumeric |
| `Q_SC_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_SC_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |
| `SC_ET_roofs_top_m2` | Roof top collector surface area. | float | `[m2]` | {0.0...n} |
| `SC_ET_roofs_top_Q_kWh` | Heat production from solar collectors on roof tops | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_east_m2` | East facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_east_Q_kWh` | Heat production from solar collectors on east facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_north_m2` | North facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_north_Q_kWh` | Heat production from solar collectors on west facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_south_m2` | South facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_south_Q_kWh` | Heat production from solar collectors on south facades | float | `[kWh]` | {0.0...n} |
| `SC_ET_walls_west_m2` | West facing wall collector surface area. | float | `[m2]` | {0.0...n} |
| `SC_ET_walls_west_Q_kWh` | Heat production from solar collectors on west facades | float | `[kWh]` | {0.0...n} |

---

### `SC_totals`

- **Path**: `outputs/data/potentials/solar/SC_FP_total.csv`
- **File type**: `csv`
- **Created by**: `solar_collector`
- **Used by**: `optimization`

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Area_SC_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `Date` | Date and time in hourly steps. | date | `NA` | YYYY-MM-DD |
| `Eaux_SC_kWh` | Auxiliary electricity consumed by the collector. | float | `[kWh]` | {0.0...n} |
| `mcp_SC_kWperC` | Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector. | float | `[kW/C]` | {0.0...n} |
| `Q_SC_gen_kWh` | Total heat generated by the collector. | float | `[kWh]` | {0.0...n} |
| `Q_SC_l_kWh` | Collector heat loss. | float | `[kWh]` | {0.0...n} |
| `radiation_kWh` | Total radiatiative potential. | float | `[kWh]` | {0.0...n} |
| `SC_FP_roofs_top_m2` | Collector surface area on roof tops. | float | `[m2]` | {0.0...n} |
| `SC_FP_roofs_top_Q_kWh` | Heat production from solar collectors on roof tops | float | `[kWh]` | {0.0...n} |
| `SC_FP_walls_east_m2` | Collector surface area on east facades. | float | `[m2]` | {0.0...n} |
| `SC_FP_walls_east_Q_kWh` | Heat production from solar collectors on east facades | float | `[kWh]` | {0.0...n} |
| `SC_FP_walls_north_m2` | Collector surface area on north facades. | float | `[m2]` | {0.0...n} |
| `SC_FP_walls_north_Q_kWh` | Heat production from solar collectors on north facades | float | `[kWh]` | {0.0...n} |
| `SC_FP_walls_south_m2` | Collector surface area on south facades. | float | `[m2]` | {0.0...n} |
| `SC_FP_walls_south_Q_kWh` | Heat production from solar collectors on south facades | float | `[kWh]` | {0.0...n} |
| `SC_FP_walls_west_m2` | Collector surface area on west facades. | float | `[m2]` | {0.0...n} |
| `SC_FP_walls_west_Q_kWh` | Heat production from solar collectors on west facades | float | `[kWh]` | {0.0...n} |
| `T_SC_re_C` | Collector hot water return temperature. | float | `[C]` | {0.0...n} |
| `T_SC_sup_C` | Collector hot water supply temperature. | float | `[C]` | {0.0...n} |

---

[← Solar Radiation Analysis](02-solar-radiation.md) | [Glossary index](index.md) | [Energy Demand Forecasting →](04-demand-forecasting.md)
