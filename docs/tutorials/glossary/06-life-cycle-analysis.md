# Life Cycle Analysis (BETA)

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **24**

---

## Files

- [`get_analysis_configuration_file`](#get_analysis_configuration_file)
- [`get_baseline_costs`](#get_baseline_costs)
- [`get_baseline_costs_detailed`](#get_baseline_costs_detailed)
- [`get_costs_whatif_buildings_file`](#get_costs_whatif_buildings_file)
- [`get_costs_whatif_components_file`](#get_costs_whatif_components_file)
- [`get_emissions_whatif_buildings_file`](#get_emissions_whatif_buildings_file)
- [`get_emissions_whatif_operational_file`](#get_emissions_whatif_operational_file)
- [`get_emissions_whatif_timeline_file`](#get_emissions_whatif_timeline_file)
- [`get_final_energy_building_file`](#get_final_energy_building_file)
- [`get_final_energy_buildings_file`](#get_final_energy_buildings_file)
- [`get_final_energy_file`](#get_final_energy_file)
- [`get_final_energy_plant_file`](#get_final_energy_plant_file)
- [`get_heat_rejection_buildings`](#get_heat_rejection_buildings)
- [`get_heat_rejection_components`](#get_heat_rejection_components)
- [`get_heat_rejection_hourly_building`](#get_heat_rejection_hourly_building)
- [`get_heat_rejection_hourly_spatial`](#get_heat_rejection_hourly_spatial)
- [`get_heat_rejection_whatif_building_file`](#get_heat_rejection_whatif_building_file)
- [`get_heat_rejection_whatif_buildings_file`](#get_heat_rejection_whatif_buildings_file)
- [`get_heat_rejection_whatif_components_file`](#get_heat_rejection_whatif_components_file)
- [`get_lca_embodied`](#get_lca_embodied)
- [`get_lca_mobility`](#get_lca_mobility)
- [`get_lca_operation`](#get_lca_operation)
- [`get_lca_operational_hourly_building`](#get_lca_operational_hourly_building)
- [`get_total_yearly_operational_building`](#get_total_yearly_operational_building)

---

### `get_analysis_configuration_file`

- **Path**: `outputs/data/analysis/{whatif_name}/configuration.json`
- **File type**: `json`
- **Created by**: `final_energy`
- **Used by**: _(none)_

---

### `get_baseline_costs`

- **Path**: `outputs/data/costs/baseline_costs.csv`
- **File type**: `csv`
- **Created by**: `system_costs`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_building_scale_USD` | Annualised capital expenditure for building-scale systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Capex_a_district_scale_USD` | Annualised capital expenditure for district-scale systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Capex_a_USD` | Annualised capital expenditure for all supply systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Capex_total_building_scale_USD` | Total capital expenditure for building-scale systems | float | `[$USD(2015)]` | {0.0...n} |
| `Capex_total_district_scale_USD` | Total capital expenditure for district-scale systems (networks + piping) | float | `[$USD(2015)]` | {0.0...n} |
| `Capex_total_USD` | Total capital expenditure for all supply systems and components | float | `[$USD(2015)]` | {0.0...n} |
| `GFA_m2` | Gross floor area (sum of all buildings for networks) | float | `[m2]` | {0.0...n} |
| `name` | Building or network name | string | `NA` | alphanumeric |
| `Opex_a_building_scale_USD` | Annual operational expenditure for building-scale systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Opex_a_district_scale_USD` | Annual operational expenditure for district-scale systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Opex_a_USD` | Total annual operational expenditure (fixed + variable) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Opex_fixed_a_USD` | Annual fixed operational expenditure (O&M) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `Opex_var_a_USD` | Annual variable operational expenditure (energy costs) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `TAC_USD` | Total annualised cost (CAPEX_a + OPEX_a) | float | `[$USD(2015)/yr]` | {0.0...n} |

---

### `get_baseline_costs_detailed`

- **Path**: `outputs/data/costs/baseline_costs_detailed.csv`
- **File type**: `csv`
- **Created by**: `system_costs`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `capacity_kW` | Component capacity in kilowatts (0 for energy carriers and piping) | float | `[kW]` | {0.0...n} |
| `capex_a_USD` | Annualised capital expenditure for component | float | `[$USD(2015)/yr]` | {0.0...n} |
| `capex_total_USD` | Total capital expenditure for component | float | `[$USD(2015)]` | {0.0...n} |
| `code` | Component code (e.g., CH1 for chiller type 1, CT1 for cooling tower type 1, PIPES for distribution piping) or energy carrier code (e.g., E230AC for electricity, NATURALGAS for natural gas) | string | `NA` | alphanumeric |
| `name` | Building or network name | string | `NA` | alphanumeric |
| `network_type` | Network type (DC for district cooling, DH for district heating) or empty for standalone buildings | string | `NA` | alphanumeric |
| `opex_fixed_a_USD` | Annual fixed operational expenditure (operations and maintenance) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `opex_var_a_USD` | Annual variable operational expenditure (energy costs from fuel or electricity purchases) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `placement` | Component placement in system (primary for heat/cooling generation, secondary for intermediate conversion, tertiary for heat rejection, distribution for piping, energy_carrier for fuel/electricity costs) | string | `NA` | alphanumeric |
| `scale` | System scale (BUILDING for individual building systems, DISTRICT for district network systems) | string | `NA` | alphanumeric |
| `service` | Energy service (e.g., GRID_cs for grid cooling, DC_network for district cooling network, NONE for buildings with no systems) | string | `NA` | alphanumeric |

---

### `get_costs_whatif_buildings_file`

- **Path**: `outputs/data/analysis/{whatif_name}/costs/costs_buildings.csv`
- **File type**: `csv`
- **Created by**: `system_costs`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `capex_a_USD` | Annualised capital expenditure for all supply systems | float | `[$USD(2015)/yr]` | {0.0...n} |
| `capex_total_USD` | Total capital expenditure for all supply systems | float | `[$USD(2015)]` | {0.0...n} |
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `name` | Building or plant name | string | `NA` | alphanumeric |
| `opex_fixed_a_USD` | Annual fixed operational expenditure (O&M) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `opex_var_a_USD` | Annual variable operational expenditure (energy costs) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `scale` | Supply system scale (BUILDING or DISTRICT) | string | `NA` | alphanumeric |
| `TAC_USD` | Total annualised cost (capex_a + opex_fixed_a + opex_var_a) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `type` | Row type (building or plant) | string | `NA` | alphanumeric |
| `whatif_name` | What-if scenario name | string | `NA` | alphanumeric |
| `x_coord` | Building centroid x coordinate | float | `[m]` | {n...n} |
| `y_coord` | Building centroid y coordinate | float | `[m]` | {n...n} |

---

### `get_costs_whatif_components_file`

- **Path**: `outputs/data/analysis/{whatif_name}/costs/costs_components.csv`
- **File type**: `csv`
- **Created by**: `system_costs`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `assembly_code` | Supply assembly code (e.g., SUPPLY_HEATING_AS3) | string | `NA` | alphanumeric |
| `capacity_kW` | Component capacity in kilowatts (peak / efficiency) | float | `[kW]` | {0.0...n} |
| `capex_a_USD` | Annualised capital expenditure for this component | float | `[$USD(2015)/yr]` | {0.0...n} |
| `capex_total_USD` | Total capital expenditure for this component | float | `[$USD(2015)]` | {0.0...n} |
| `carrier` | Energy carrier (NATURALGAS, GRID, OIL, etc.) | string | `NA` | alphanumeric |
| `component_code` | Component code (e.g., BO1, HP1, CH1, PU1) | string | `NA` | alphanumeric |
| `name` | Building or plant name | string | `NA` | alphanumeric |
| `opex_fixed_a_USD` | Annual fixed operational expenditure (O&M) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `opex_var_a_USD` | Annual variable operational expenditure (energy costs) | float | `[$USD(2015)/yr]` | {0.0...n} |
| `peak_service_kW` | Peak service demand in kilowatts | float | `[kW]` | {0.0...n} |
| `scale` | Supply system scale (BUILDING or DISTRICT) | string | `NA` | alphanumeric |
| `service` | Energy service (hs, ww, cs, E, hs_booster, ww_booster, hs_pumping, hs_piping, cs_pumping, cs_piping, PV_*, SC_*, PVT_*) | string | `NA` | alphanumeric |
| `TAC_USD` | Total annualised cost (capex_a + opex_fixed_a + opex_var_a) | float | `[$USD(2015)/yr]` | {0.0...n} |

---

### `get_emissions_whatif_buildings_file`

- **Path**: `outputs/data/analysis/{whatif_name}/emissions/emissions_buildings.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `biogenic_kgCO2e` | Total lifecycle biogenic carbon storage across all years (negative = sequestration) | float | `[kgCO2e]` | {n...n} |
| `case` | Connectivity case number from final-energy | float | `NA` | {n...n} |
| `case_description` | Human-readable description of connectivity case | string | `NA` | alphanumeric |
| `demolition_kgCO2e` | Total lifecycle demolition GHG emissions across all years | float | `[kgCO2e]` | {n...n} |
| `GFA_m2` | Gross floor area (null for plants) | float | `[m2]` | {0.0...n} |
| `name` | Building name or plant identifier (e.g. B1001, NODE16) | string | `NA` | alphanumeric |
| `operation_kgCO2e` | Total annual operational GHG emissions | float | `[kgCO2e/yr]` | {n...n} |
| `production_kgCO2e` | Total lifecycle production (embodied) GHG emissions across all years | float | `[kgCO2e]` | {n...n} |
| `scale` | System scale (BUILDING for standalone, DISTRICT for networked) | string | `NA` | alphanumeric |
| `type` | Entity type (building or plant) | string | `NA` | {building, plant} |
| `whatif_name` | What-if scenario name | string | `NA` | alphanumeric |
| `x_coord` | X coordinate of building centroid or plant node location | float | `[m]` | {n...n} |
| `y_coord` | Y coordinate of building centroid or plant node location | float | `[m]` | {n...n} |

---

### `get_emissions_whatif_operational_file`

- **Path**: `outputs/data/analysis/{whatif_name}/emissions/emissions_operational.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Hourly timestamp | string | `NA` | alphanumeric |

---

### `get_emissions_whatif_timeline_file`

- **Path**: `outputs/data/analysis/{whatif_name}/emissions/emissions_timeline.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `period` | Year label (e.g. Y_2025) | string | `NA` | alphanumeric |

---

### `get_final_energy_building_file`

- **Path**: `outputs/data/analysis/{whatif_name}/final-energy/{building}.csv`
- **File type**: `csv`
- **Created by**: `final_energy`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `case` | Connectivity case: 1=Standalone, 2=DH+DC, 3=DH only, 4=DC only, 4.01/4.02/4.03=DC with boosters | float | `NA` | {n...n} |
| `case_description` | Human-readable description of connectivity case | string | `NA` | alphanumeric |
| `date` | Timestamp for each hour (8760 rows per year) | date | `NA` | YYYY-MM-DD |
| `E_sys_GRID_kWh` | Hourly grid electricity consumption for appliances/lighting/ventilation | float | `[kWh]` | {0.0...n} |
| `E_sys_kWh` | Hourly electricity system demand (appliances, lighting, ventilation) | float | `[kWh]` | {0.0...n} |
| `PV_roof_kWh` | Hourly solar electrical generation from roof panels | float | `[kWh]` | {0.0...n} |
| `PV_total_kWh` | Hourly total solar electrical generation (sum of all facades) | float | `[kWh]` | {0.0...n} |
| `PV_wall_east_kWh` | Hourly solar electrical generation from east wall panels | float | `[kWh]` | {0.0...n} |
| `PV_wall_north_kWh` | Hourly solar electrical generation from north wall panels | float | `[kWh]` | {0.0...n} |
| `PV_wall_south_kWh` | Hourly solar electrical generation from south wall panels | float | `[kWh]` | {0.0...n} |
| `PV_wall_west_kWh` | Hourly solar electrical generation from west wall panels | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_DC_kWh` | Hourly district cooling consumption | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_GRID_kWh` | Hourly grid electricity consumption for space cooling | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_kWh` | Hourly space cooling system demand | float | `[kWh]` | {0.0...n} |
| `Qhs_booster_NATURALGAS_kWh` | Hourly natural gas consumption for space heating booster | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_DH_kWh` | Hourly district heating consumption for space heating | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_GRID_kWh` | Hourly grid electricity consumption for space heating (heat pumps) | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_kWh` | Hourly space heating system demand | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_NATURALGAS_kWh` | Hourly natural gas consumption for space heating | float | `[kWh]` | {0.0...n} |
| `Qww_booster_NATURALGAS_kWh` | Hourly natural gas consumption for hot water booster | float | `[kWh]` | {0.0...n} |
| `Qww_sys_DH_kWh` | Hourly district heating consumption for hot water | float | `[kWh]` | {0.0...n} |
| `Qww_sys_kWh` | Hourly domestic hot water system demand | float | `[kWh]` | {0.0...n} |
| `Qww_sys_NATURALGAS_kWh` | Hourly natural gas consumption for hot water | float | `[kWh]` | {0.0...n} |
| `scale` | System scale (BUILDING for standalone, DISTRICT for networked) | string | `NA` | alphanumeric |
| `SOLAR_roof_kWh` | Hourly solar thermal generation from roof collectors | float | `[kWh]` | {0.0...n} |
| `SOLAR_total_kWh` | Hourly total solar thermal generation (sum of all facades) | float | `[kWh]` | {0.0...n} |
| `SOLAR_wall_east_kWh` | Hourly solar thermal generation from east wall collectors | float | `[kWh]` | {0.0...n} |
| `SOLAR_wall_north_kWh` | Hourly solar thermal generation from north wall collectors | float | `[kWh]` | {0.0...n} |
| `SOLAR_wall_south_kWh` | Hourly solar thermal generation from south wall collectors | float | `[kWh]` | {0.0...n} |
| `SOLAR_wall_west_kWh` | Hourly solar thermal generation from west wall collectors | float | `[kWh]` | {0.0...n} |

---

### `get_final_energy_buildings_file`

- **Path**: `outputs/data/analysis/{whatif_name}/final-energy/final_energy_buildings.csv`
- **File type**: `csv`
- **Created by**: `final_energy`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `case` | Connectivity case: 1=Standalone, 2=DH+DC, 3=DH only, 4=DC only, 4.01/4.02/4.03=DC with boosters, 5=District plant | float | `NA` | {n...n} |
| `case_description` | Human-readable description of connectivity case | string | `NA` | alphanumeric |
| `COAL_MWh` | Annual coal consumption | float | `[MWh/yr]` | {0.0...n} |
| `DC_MWh` | Annual district cooling consumption | float | `[MWh/yr]` | {0.0...n} |
| `DH_MWh` | Annual district heating consumption | float | `[MWh/yr]` | {0.0...n} |
| `E_sys_MWh` | Annual electricity system demand (appliances, lighting, ventilation) | float | `[MWh/yr]` | {0.0...n} |
| `GFA_m2` | Gross floor area (0 for plants) | float | `[m2]` | {0.0...n} |
| `GRID_MWh` | Annual grid electricity consumption | float | `[MWh/yr]` | {0.0...n} |
| `name` | Building name or plant name (e.g., B1001, NODE16) | string | `NA` | alphanumeric |
| `NATURALGAS_MWh` | Annual natural gas consumption | float | `[MWh/yr]` | {0.0...n} |
| `OIL_MWh` | Annual oil consumption | float | `[MWh/yr]` | {0.0...n} |
| `peak_datetime` | Timestamp when peak demand occurs | string | `NA` | alphanumeric |
| `peak_demand_kW` | Peak total demand (thermal + electrical) | float | `[kW]` | {0.0...n} |
| `PV_MWh` | Annual solar electrical generation (from PV and PVT panels) | float | `[MWh/yr]` | {0.0...n} |
| `Qcs_sys_MWh` | Annual space cooling system demand | float | `[MWh/yr]` | {0.0...n} |
| `Qhs_sys_MWh` | Annual space heating system demand | float | `[MWh/yr]` | {0.0...n} |
| `Qww_sys_MWh` | Annual domestic hot water system demand | float | `[MWh/yr]` | {0.0...n} |
| `scale` | System scale (BUILDING for standalone, DISTRICT for networked) | string | `NA` | {BUILDING, DISTRICT} |
| `SOLAR_MWh` | Annual solar thermal generation (from SC and PVT panels) | float | `[MWh/yr]` | {0.0...n} |
| `TOTAL_MWh` | Total annual final energy consumption (sum of all carriers) | float | `[MWh/yr]` | {0.0...n} |
| `type` | Entity type (building or plant) | string | `NA` | {building, plant} |
| `WOOD_MWh` | Annual wood/biomass consumption | float | `[MWh/yr]` | {0.0...n} |
| `x_coord` | X coordinate of building centroid or plant node location | float | `[m]` | {n...n} |
| `y_coord` | Y coordinate of building centroid or plant node location | float | `[m]` | {n...n} |

---

### `get_final_energy_file`

- **Path**: `outputs/data/analysis/{whatif_name}/final-energy/final_energy.csv`
- **File type**: `csv`
- **Created by**: `final_energy`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `COAL_kWh` | Hourly coal consumption (buildings + plants) | float | `[kWh]` | {0.0...n} |
| `date` | Timestamp for each hour (8760 rows per year) | date | `NA` | YYYY-MM-DD |
| `DC_kWh` | Hourly district cooling consumption | float | `[kWh]` | {0.0...n} |
| `DH_kWh` | Hourly district heating consumption | float | `[kWh]` | {0.0...n} |
| `E_sys_kWh` | Hourly electricity system demand (all buildings aggregated) | float | `[kWh]` | {0.0...n} |
| `GRID_kWh` | Hourly grid electricity consumption (buildings + plants) | float | `[kWh]` | {0.0...n} |
| `NATURALGAS_kWh` | Hourly natural gas consumption (buildings + plants) | float | `[kWh]` | {0.0...n} |
| `OIL_kWh` | Hourly oil consumption (buildings + plants) | float | `[kWh]` | {0.0...n} |
| `PV_kWh` | Hourly solar electrical generation (from PV and PVT panels) | float | `[kWh]` | {0.0...n} |
| `Qcs_sys_kWh` | Hourly space cooling system demand (all buildings aggregated) | float | `[kWh]` | {0.0...n} |
| `Qhs_sys_kWh` | Hourly space heating system demand (all buildings aggregated) | float | `[kWh]` | {0.0...n} |
| `Qww_sys_kWh` | Hourly domestic hot water system demand (all buildings aggregated) | float | `[kWh]` | {0.0...n} |
| `SOLAR_kWh` | Hourly solar thermal generation (from SC and PVT panels) | float | `[kWh]` | {0.0...n} |
| `TOTAL_kWh` | Hourly total final energy consumption (sum of all carriers) | float | `[kWh]` | {0.0...n} |
| `WOOD_kWh` | Hourly wood/biomass consumption (buildings + plants) | float | `[kWh]` | {0.0...n} |

---

### `get_final_energy_plant_file`

- **Path**: `outputs/data/analysis/{whatif_name}/final-energy/{plant_name}.csv`
- **File type**: `csv`
- **Created by**: `final_energy`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Timestamp for each hour (8760 rows per year) | date | `NA` | YYYY-MM-DD |
| `network_name` | Network layout name | string | `NA` | alphanumeric |
| `network_type` | Network type (DH for district heating, DC for district cooling) | string | `NA` | {DH, DC} |
| `plant_name` | Plant node name from network shapefile (e.g., NODE16, PLANT_A) | string | `NA` | alphanumeric |
| `plant_primary_DC_GRID_kWh` | Hourly grid electricity consumption for DC plant primary component (chiller) | float | `[kWh]` | {0.0...n} |
| `plant_primary_DH_GRID_kWh` | Hourly grid electricity consumption for DH plant primary component (heat pump) | float | `[kWh]` | {0.0...n} |
| `plant_primary_DH_NATURALGAS_kWh` | Hourly natural gas consumption for DH plant primary component (boiler) | float | `[kWh]` | {0.0...n} |
| `plant_primary_DH_OIL_kWh` | Hourly oil consumption for DH plant primary component (boiler) | float | `[kWh]` | {0.0...n} |
| `plant_primary_DH_WOOD_kWh` | Hourly wood/biomass consumption for DH plant primary component (boiler) | float | `[kWh]` | {0.0...n} |
| `plant_pumping_DC_GRID_kWh` | Hourly grid electricity consumption for DC network pumping | float | `[kWh]` | {0.0...n} |
| `plant_pumping_DH_GRID_kWh` | Hourly grid electricity consumption for DH network pumping | float | `[kWh]` | {0.0...n} |
| `plant_tertiary_DC_GRID_kWh` | Hourly grid electricity consumption for DC plant tertiary component (cooling tower fan) | float | `[kWh]` | {0.0...n} |
| `pumping_load_kWh` | Hourly pumping energy consumption for distribution network | float | `[kWh]` | {0.0...n} |
| `scale` | System scale (always DISTRICT for plants) | string | `NA` | {DISTRICT} |
| `thermal_load_kWh` | Hourly thermal load served by the plant (heating or cooling) | float | `[kWh]` | {0.0...n} |

---

### `get_heat_rejection_buildings`

- **Path**: `outputs/data/heat/heat_rejection_buildings.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `GFA_m2` | Gross floor area (0 for plant nodes) | float | `[m2]` | {0.0...n} |
| `heat_rejection_annual_MWh` | Total annual heat rejection to environment (sum of all energy carriers) | float | `[MWh]` | {0.0...n} |
| `name` | Building or network plant name | string | `NA` | alphanumeric |
| `peak_datetime` | Date and time of peak heat rejection | string | `NA` | alphanumeric |
| `peak_heat_rejection_kW` | Peak hourly heat rejection rate | float | `[kW]` | {0.0...n} |
| `scale` | System scale (BUILDING for individual building systems, DISTRICT for district network plants) | string | `NA` | alphanumeric |
| `type` | Type of heat source (building for individual buildings, plant for district energy plants) | string | `NA` | alphanumeric |
| `x_coord` | X coordinate for spatial location (longitude or projected coordinate) | float | `[m]` | {n...n} |
| `y_coord` | Y coordinate for spatial location (latitude or projected coordinate) | float | `[m]` | {n...n} |

---

### `get_heat_rejection_components`

- **Path**: `outputs/data/heat/heat_rejection_components.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `component_code` | Component code (e.g., CH1 for chiller type 1, CT1 for cooling tower type 1) | string | `NA` | alphanumeric |
| `energy_carrier` | Energy carrier code for heat rejection medium (e.g., T_AIR_20C for air at 20C, T_AIR_ODB for outdoor air) | string | `NA` | alphanumeric |
| `heat_rejection_annual_MWh` | Annual heat rejection for this component and energy carrier | float | `[MWh]` | {0.0...n} |
| `name` | Building or network plant name | string | `NA` | alphanumeric |
| `network_type` | Network type (DC for district cooling, DH for district heating) or empty for standalone buildings | string | `NA` | alphanumeric |
| `peak_heat_rejection_kW` | Peak hourly heat rejection rate for this component | float | `[kW]` | {0.0...n} |
| `scale` | System scale (BUILDING for individual building systems, DISTRICT for district network plants) | string | `NA` | alphanumeric |
| `service` | Energy service (e.g., GRID_cs for grid cooling, DC_plant for district cooling plant) | string | `NA` | alphanumeric |

---

### `get_heat_rejection_hourly_building`

- **Path**: `outputs/data/heat/{building}.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `DATE` | Timestamp for this hour (8760 hours total, no leap day) | string | `NA` | alphanumeric |
| `heat_rejection_kW` | Heat rejection rate at this hour (sum of all energy carriers) | float | `[kW]` | {0.0...n} |

---

### `get_heat_rejection_hourly_spatial`

- **Path**: `outputs/data/heat/heat_rejection_hourly_spatial.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Timestamp for this hour (8760 hours per location) | string | `NA` | alphanumeric |
| `heat_rejection_kW` | Heat rejection rate at this hour (sum of all energy carriers) | float | `[kW]` | {0.0...n} |
| `name` | Building or network plant name | string | `NA` | alphanumeric |
| `type` | Type of heat source (building for individual buildings, plant for district energy plants) | string | `NA` | alphanumeric |

---

### `get_heat_rejection_whatif_building_file`

- **Path**: `outputs/data/analysis/{whatif_name}/heat/{name}.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `date` | Timestamp for each hour (8760 rows per year) | date | `NA` | YYYY-MM-DD |
| `heat_rejection_kW` | Heat rejection rate at this hour (sum of all energy carriers) | float | `[kW]` | {0.0...n} |

---

### `get_heat_rejection_whatif_buildings_file`

- **Path**: `outputs/data/analysis/{whatif_name}/heat/heat_rejection_buildings.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `case` | Connectivity case number from final-energy | float | `NA` | {n...n} |
| `case_description` | Human-readable description of connectivity case | string | `NA` | alphanumeric |
| `GFA_m2` | Gross floor area (0 for plants) | float | `[m2]` | {0.0...n} |
| `heat_rejection_annual_MWh` | Total annual heat rejection to the environment | float | `[MWh/yr]` | {0.0...n} |
| `name` | Building name or plant identifier (e.g. B1001, NODE16) | string | `NA` | alphanumeric |
| `peak_heat_rejection_kW` | Peak hourly heat rejection rate | float | `[kW]` | {0.0...n} |
| `scale` | System scale (BUILDING for standalone, DISTRICT for networked) | string | `NA` | alphanumeric |
| `type` | Entity type (building or plant) | string | `NA` | {building, plant} |
| `whatif_name` | What-if scenario name | string | `NA` | alphanumeric |
| `x_coord` | X coordinate of building centroid or plant node location | float | `[m]` | {n...n} |
| `y_coord` | Y coordinate of building centroid or plant node location | float | `[m]` | {n...n} |

---

### `get_heat_rejection_whatif_components_file`

- **Path**: `outputs/data/analysis/{whatif_name}/heat/heat_rejection_components.csv`
- **File type**: `csv`
- **Created by**: `anthropogenic_heat`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `assembly_code` | Supply assembly code from database | string | `NA` | alphanumeric |
| `carrier` | Energy carrier (NATURALGAS, GRID, DH, DC, etc.) | string | `NA` | alphanumeric |
| `component_code` | Primary component code (e.g. BO1, CH1) | string | `NA` | alphanumeric |
| `heat_rejection_annual_MWh` | Annual heat rejection for this service | float | `[MWh/yr]` | {0.0...n} |
| `name` | Building name or plant identifier | string | `NA` | alphanumeric |
| `peak_heat_rejection_kW` | Peak hourly heat rejection for this service | float | `[kW]` | {0.0...n} |
| `scale` | System scale (BUILDING or DISTRICT) | string | `NA` | {BUILDING, DISTRICT} |
| `service` | Energy service (hs, ww, cs, hs_booster, ww_booster) | string | `NA` | alphanumeric |

---

### `get_lca_embodied`

- **Path**: `outputs/data/emissions/Total_LCA_embodied.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `GHG_base_tonCO2` | Embodied emissions of basement floor due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_floor_tonCO2` | Embodied emissions of floors due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_part_tonCO2` | Embodied emissions of indoor partition due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_roof_tonCO2` | Embodied emissions of roof due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_embodied_kgCO2m2yr` | Embodied emissions per conditioned floor area due to building or retrofit construction and decommissioning | float | `[kg CO2-eq/m2.yr]` | {0.0...n} |
| `GHG_sys_embodied_tonCO2yr` | Embodied emissions due to building construction and decommissioning or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_uptake_kgCO2m2yr` | Embodied emissions per conditioned floor area due to building or retrofit construction and decommissioning | float | `[kg CO2-eq/m2.yr]` | {n...0.0} |
| `GHG_sys_uptake_tonCO2yr` | Carbon storage with in building materials due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `GHG_technical_system_tonCO2` | Embodied emissions of building technical systems due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_wall_tonCO2` | Embodied emissions of external walls due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_window_tonCO2` | Embodied emissions of windows due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `uptake_base_tonCO2` | Carbon storage with in the basement floor due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `uptake_floor_tonCO2` | Carbon storage with in the floors due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `uptake_part_tonCO2` | Carbon storage with in the indoor partition due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `uptake_roof_tonCO2` | Carbon storage with in the roof due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `uptake_wall_tonCO2` | Carbon storage with in the external walls due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |
| `uptake_window_tonCO2` | Carbon storage with in the windows due to building construction or retrofit | float | `[ton CO2-eq/yr]` | {n...0.0} |

---

### `get_lca_mobility`

- **Path**: `outputs/data/emissions/Total_LCA_mobility.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `GHG_sys_mobility_kgCO2m2` | Operational emissions per unit of conditioned floor area due to mobility | float | `[kg CO2-eq/m2.yr]` | {0.0...n} |
| `GHG_sys_mobility_tonCO2` | Operational emissions due to mobility | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |

---

### `get_lca_operation`

- **Path**: `outputs/data/emissions/Total_LCA_operation.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `COAL_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the coal powererd heating system | float | `[kg/m2yr]` | {0.0...n} |
| `COAL_hs_ghg_ton` | Operational emissions of the coal powered heating system | float | `[ton/yr]` | {0.0...n} |
| `COAL_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for coal powered heating system | float | `[GJ/yr]` | {0.0...n} |
| `COAL_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `COAL_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the coal powered domestic hot water system | float | `[kg/m2 -yr]` | {0.0...n} |
| `COAL_ww_ghg_ton` | Operational emissions of the coal powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `COAL_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for coal powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `COAL_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |
| `DC_cdata_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the district cooling for the data center | float | `[kg/m2 -yr]` | {0.0...n} |
| `DC_cdata_ghg_ton` | Operational emissions of the district cooling for the data center | float | `[ton/yr]` | {0.0...n} |
| `DC_cdata_nre_pen_GJ` | Operational primary energy demand (non-renewable) for district cooling system for cool room refrigeration | float | `[GJ/yr]` | {0.0...n} |
| `DC_cdata_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) for district cooling for cool room refrigeration | float | `[MJ/m2-yr]` | {0.0...n} |
| `DC_cre_ghg_kgm2` | Operational emissions per unit of conditioned floor area for district cooling system for cool room refrigeration | float | `[kg/m2yr]` | {0.0...n} |
| `DC_cre_ghg_ton` | Operational emissions for district cooling system for cool room refrigeration | float | `[ton/yr]` | {0.0...n} |
| `DC_cre_nre_pen_GJ` | Operational primary energy demand (non-renewable) for district cooling system for cool room refrigeration | float | `[GJ/yr]` | {0.0...n} |
| `DC_cre_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable)  for cool room refrigeration | float | `[MJ/m2-yr]` | {0.0...n} |
| `DC_cs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the district cooling | float | `[kg/m2yr]` | {0.0...n} |
| `DC_cs_ghg_ton` | Operational emissions of the district cooling | float | `[ton/yr]` | {0.0...n} |
| `DC_cs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for district cooling system | float | `[GJ/yr]` | {0.0...n} |
| `DC_cs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district cooling | float | `[MJ/m2-yr]` | {0.0...n} |
| `DH_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the district heating system | float | `[kg/m2yr]` | {0.0...n} |
| `DH_hs_ghg_ton` | Operational emissions of the district heating system | float | `[ton/yr]` | {0.0...n} |
| `DH_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for district heating system | float | `[GJ/yr]` | {0.0...n} |
| `DH_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `DH_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the district heating domestic hot water system | float | `[kg/m2yr]` | {0.0...n} |
| `DH_ww_ghg_ton` | Operational emissions of the district heating powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `DH_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for district heating powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `DH_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |
| `GFA_m2` | Gross floor area | float | `[m2]` | {0.0...n} |
| `GHG_sys_kgCO2m2` | Total operational emissions per unit of conditioned floor area | float | `[kg CO2-eq/m2.yr]` | {0.0...n} |
| `GHG_sys_tonCO2` | Total operational emissions | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GRID_ghg_kgm2` | Operational emissions per unit of conditioned floor area from grid electricity | float | `[kg/m2yr]` | {0.0...n} |
| `GRID_ghg_ton` | Operational emissions of the electrictiy from the grid | float | `[ton/yr]` | {0.0...n} |
| `GRID_nre_pen_GJ` | Operational primary energy demand (non-renewable) from the grid | float | `[GJ/yr]` | {0.0...n} |
| `GRID_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) from grid electricity | float | `[MJ/m2-yr]` | {0.0...n} |
| `name` | Unique building ID. It must start with a letter. | string | `NA` | alphanumeric |
| `NG_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the natural gas powered heating system | float | `[kg/m2yr]` | {0.0...n} |
| `NG_hs_ghg_ton` | Operational emissions of the natural gas powered heating system | float | `[ton/yr]` | {0.0...n} |
| `NG_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for natural gas powered heating system | float | `[GJ/yr]` | {0.0...n} |
| `NG_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `NG_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the gas powered domestic hot water system | float | `[kg/m2yr]` | {0.0...n} |
| `NG_ww_ghg_ton` | Operational emissions of the solar powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `NG_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for natural gas powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `NG_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |
| `OIL_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the oil powered heating system | float | `[kg/m2yr]` | {0.0...n} |
| `OIL_hs_ghg_ton` | Operational emissions of the oil powered heating system | float | `[ton/yr]` | {0.0...n} |
| `OIL_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for oil powered heating system | float | `[GJ/yr]` | {0.0...n} |
| `OIL_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `OIL_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the oil powered domestic hot water system | float | `[kg/m2yr]` | {0.0...n} |
| `OIL_ww_ghg_ton` | Operational emissions of the oil powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `OIL_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for oil powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `OIL_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |
| `PV_ghg_kgm2` | Operational emissions per unit of conditioned floor area for PV-System | float | `[kg/m2yr]` | {0.0...n} |
| `PV_ghg_ton` | Operational emissions of the PV-System | float | `[ton/yr]` | {0.0...n} |
| `PV_nre_pen_GJ` | Operational primary energy demand (non-renewable) for PV-System | float | `[GJ/yr]` | {0.0...n} |
| `PV_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) for PV System | float | `[MJ/m2-yr]` | {0.0...n} |
| `SOLAR_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the solar powered heating system | float | `[kg/m2yr]` | {0.0...n} |
| `SOLAR_hs_ghg_ton` | Operational emissions of the solar powered heating system | float | `[ton/yr]` | {0.0...n} |
| `SOLAR_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) of the solar powered heating system | float | `[GJ/yr]` | {0.0...n} |
| `SOLAR_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar powered heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `SOLAR_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the solar powered domestic hot water system | float | `[kg/m2yr]` | {0.0...n} |
| `SOLAR_ww_ghg_ton` | Operational emissions of the solar powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `SOLAR_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for solar powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `SOLAR_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar poweed domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |
| `WOOD_hs_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the wood powered heating system | float | `[kg/m2yr]` | {0.0...n} |
| `WOOD_hs_ghg_ton` | Operational emissions of the wood powered heating system | float | `[ton/yr]` | {0.0...n} |
| `WOOD_hs_nre_pen_GJ` | Operational primary energy demand (non-renewable) for wood powered heating system | float | `[GJ/yr]` | {0.0...n} |
| `WOOD_hs_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered heating system | float | `[MJ/m2-yr]` | {0.0...n} |
| `WOOD_ww_ghg_kgm2` | Operational emissions per unit of conditioned floor area of the wood powered domestic hot water system | float | `[kg/m2yr]` | {0.0...n} |
| `WOOD_ww_ghg_ton` | Operational emissions of the wood powered domestic hot water system | float | `[ton/yr]` | {0.0...n} |
| `WOOD_ww_nre_pen_GJ` | Operational primary energy demand (non-renewable) for wood powered domestic hot water system | float | `[GJ/yr]` | {0.0...n} |
| `WOOD_ww_nre_pen_MJm2` | Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered domestic hot water system | float | `[MJ/m2-yr]` | {0.0...n} |

---

### `get_lca_operational_hourly_building`

- **Path**: `outputs/data/emissions/timeline/{building}_operational_hourly.csv`
- **File type**: `csv`
- **Created by**: `emission_time_dependent`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `E_sys_kgCO2` | hourly operational emission caused by satisfying electrical appliances demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `hour` | hour of the year. | int | `[h]` | {0...n} |
| `Qcs_sys_kgCO2` | hourly operational emission caused by satisfying cooling demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `Qhs_sys_kgCO2` | hourly operational emission caused by satisfying space heating demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `Qww_sys_kgCO2` | hourly operational emission caused by satisfying hot water demand. | float | `[kg CO2-eq]` | {0.0...n} |

---

### `get_total_yearly_operational_building`

- **Path**: `outputs/data/emissions/timeline/Total_yearly_operational_building.csv`
- **File type**: `csv`
- **Created by**: `emissions`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `E_sys_kgCO2` | total hourly operational emission of all buildings caused by satisfying electrical appliances demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `hour` | Hour of the year. | int | `[h]` | {0...8759} |
| `Qcs_sys_kgCO2` | total hourly operational emission of all buildings caused by satisfying cooling demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `Qhs_sys_kgCO2` | total hourly operational emission of all buildings caused by satisfying space heating demand. | float | `[kg CO2-eq]` | {0.0...n} |
| `Qww_sys_kgCO2` | total hourly operational emission of all buildings caused by satisfying hot water demand. | float | `[kg CO2-eq]` | {0.0...n} |

---

[← Thermal Network Design](05-thermal-network.md) | [Glossary index](index.md) | [Energy Supply System Optimisation →](07-supply-optimisation.md)
