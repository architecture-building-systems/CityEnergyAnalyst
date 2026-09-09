# LCA / Emissions Module

## Entry Points

- `main.py` → `main(config)` — what-if path: loops `config.emissions.what_if_name` → `calculate_emissions_for_whatif()`; legacy fallback: `emissions_detailed(config)`
- `main.py` → `emissions_simplified(locator)` — legacy path (embodied + operational, no timeline)
- `main.py` → `emissions_detailed(config)` — legacy path with timeline (`operational_hourly` + `total_yearly`)

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Script entry point, dispatches to what-if or legacy path |
| `emission_time_dependent.py` | What-if pipeline (`calculate_emissions_for_whatif`), legacy functions (`operational_hourly`, `total_yearly`), aggregation helpers (`sum_by_hour`, `sum_by_year`, `sum_by_building`) |
| `emission_timeline.py` | `BuildingEmissionTimeline` class — yearly lifecycle timeline per building (embodied + operational + solar + demolition) |
| `hourly_operational_emission.py` | `OperationalHourlyTimeline` class — 8760-row hourly emissions per building (legacy path), `_tech_name_mapping`, `_GRID_COMPONENTS` |
| `embodied.py` | `lca_embodied(year, locator)` — legacy embodied LCA (60-year payoff method) |
| `operation.py` | `lca_operation(locator)` — legacy operational LCA from demand results |

## Life-Cycle Module Coverage (EN 15978)

What CEA's emission phases mean in standard terms, and what is **not** covered. State this
boundary alongside any published result -- a declared scope is what makes an assessment
defensible, not full coverage.

| module | | CEA | source / note |
|---|---|---|---|
| A1-A3 | product (raw material, transport to plant, manufacture) | yes | reported as `production`; derived from `MATERIALS.csv` `GHG_emission_production` (KBOB *Herstellung*) |
| A4 | transport to site | **no** | not modelled |
| A5 | construction / installation | **no** | not modelled |
| B1 | in-use emissions (refrigerant leakage, off-gassing) | **no** | — |
| B2 | maintenance | **no** | — |
| B3 | repair | **no** | — |
| B4 | replacement | yes | envelope re-logged every `Service_Life_*`; PV uses its own `LT_yr`; the rest of the technical-system stack still uses the blanket `SERVICE_LIFE_OF_TECHNICAL_SYSTEMS` -- `component_lca.py` can resolve per component but is not wired in yet |
| B5 | refurbishment | partly | not a module, but district pathways model retrofits explicitly by year |
| B6 | operational energy | yes | hourly, per carrier |
| B7 | operational water | **no** | hot-water *energy* is B6; water supply impact is absent |
| C1 | deconstruction / demolition activity | **no** | the gap behind the `demolition` label -- see below |
| C2-C4 | transport to disposal, waste processing, disposal | yes | reported as `demolition`; derived from `MATERIALS.csv` `GHG_emission_disposal` (KBOB *Entsorgung*) |
| D | benefits beyond the boundary (reuse, recovery, recycling) | **no** | biogenic storage and the PV offset are reported separately, not as module D |

**The `demolition` phase is C2-C4, not C1.** The underlying data is KBOB *Entsorgung* --
transport to the disposal route plus incineration, landfill or recycling processing. The
on-site demolition activity (C1: machinery, site energy) is not included. The name is kept for
continuity with the output columns and plot categories; read it as "end of life".

**Biogenic carbon is not a module.** It is a separate reporting item (RICS PS on Whole Life
Carbon, section 4.11), stored negative throughout. KBOB applies carbon-neutral accounting, so
the stored carbon is not re-released in the C2-C4 figure.

### Technical systems (MEP) are counted, but not per device

**Replacement is per component; intensity is still blanket.**
`_log_technical_system_emissions` resolves each supply service's `primary_component_{hs,cs,dhw}`
(exposed by `BuildingSupplySystems`) to that component's own `LT_yr` via
`component_lca.service_life_for_component`, and logs one replacement cycle per component. A
20-year boiler and a 25-year chiller therefore renew independently. `log` is additive, so all
of them accumulate into the single reported `technical_systems` column -- the output shape is
unchanged.

The **embodied intensity** is still `EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS` (35 kgCO2e/m2 GFA),
shared equally between the services present, so the building total is unchanged from the
previous blanket treatment. Per-component carbon awaits capacities:
`component_lca.embodied_factor_for_component` reads the optional capacity-based
`GHG_embodied_kgCO2e_per_unit` (in the component's own `unit` -- W, VA, m2, m3, kWh, like the
cost curve), but installed capacities are not available in the timeline, and no family except
`PHOTOVOLTAIC_PANELS` carries data yet.

Two deliberate exclusions:

- **Electricity** has no component. `SUPPLY_ELECTRICITY` describes a grid connection, so
  `_SUPPLY_SERVICES` covers heating, cooling and hot water only.
- **A building with no components at all** (every service `NONE`, or a district connection
  whose plant is accounted for separately) keeps the old blanket cycle rather than dropping
  to zero.

An assumed service life is named in the timeline note, since it changes the replacement
count.

## Two Paths: What-If vs Legacy

### What-If Path (current, recommended)

`calculate_emissions_for_whatif(whatif_name, config)` — single function that:

1. Reads `configuration.json` → `building_configs`, `plant_configs`
2. Loads feedstock emission intensities (kgCO2/kWh per carrier, 8760 rows)
3. Optional: overrides GRID intensity from external CSV (`_load_grid_emission_intensity_override`)
4. Processes **buildings**: `_calc_operational_emissions_from_fe()` → hourly; `BuildingEmissionTimeline` → yearly
5. Processes **plants**: `_calc_plant_operational_emissions_from_fe()` → hourly; proportional yearly timeline
6. Aggregates to district: `sum_by_hour`, `sum_by_year`

**Input**: final-energy results (`B####.csv`, plant CSVs) + `configuration.json`
**Output**: see Output Files below

### Legacy Path

Two-step process (requires demand results, not final-energy):

1. `operational_hourly(config)` → `OperationalHourlyTimeline` per building → hourly emissions + PV offsetting
2. `total_yearly(config)` → `BuildingEmissionTimeline` per building → yearly lifecycle timeline

**Input**: demand results (`Total_demand.csv`, per-building CSVs)
**Output**: `outputs/lca/` folder

## Output Files

### What-If Path

```
outputs/data/analysis/{whatif_name}/emissions/
├── emissions_buildings.csv          # Summary per building/plant (one row each)
├── emissions_operational.csv        # District hourly operational (sum_by_hour)
├── emissions_timeline.csv           # District yearly lifecycle (sum_by_year)
├── operational/{building}.csv       # Per-building hourly operational
└── timeline/{building}.csv          # Per-building yearly lifecycle
```

### Legacy Path

```
outputs/lca/
├── operational/hourly/{building}.csv    # Per-building hourly
├── operational_total_building.csv       # Per-building annual summary
├── operational_total_hour.csv           # District hourly
├── timeline/{building}_timeline.csv     # Per-building yearly
├── total_emissions_building_{year}.csv  # Per-building lifecycle summary
└── total_emissions_timeline_{year}.csv  # District yearly timeline
```

## Zero-Emission Carriers

```python
_ZERO_EMISSION_CARRIERS = {'DH', 'DC', 'NONE'}
```

Buildings using DH/DC have **zero** operational emissions for those services at building level. The actual emissions are attributed to the **plant** via `operation_DH_kgCO2e` / `operation_DC_kgCO2e` in the district timeline.

## Timeline Column Structure

### Building Timeline (`BuildingEmissionTimeline`)

Indexed by `period` (`Y_XXXX`), columns:

**Embodied** (3 types × 10 components = 30 columns):
- `{emission}_{component}_kgCO2e` where emission ∈ {`production`, `biogenic`, `demolition`}
  - `biogenic` values are negative (stored carbon): the database column is already negative,
    so it is logged as-is. Do not negate it -- see `cea/databases/AGENTS.md`.
- Components: `wall_ag`, `wall_bg`, `wall_part`, `win_ag`, `roof`, `upperside`, `underside`, `floor`, `base`, `technical_systems`

**Operational** (6 columns):
- `operation_Qhs_sys_kgCO2e` — Space heating
- `operation_Qww_sys_kgCO2e` — DHW
- `operation_Qcs_sys_kgCO2e` — Space cooling
- `operation_E_sys_kgCO2e` — Electricity
- `operation_Qhs_booster_kgCO2e` — Space heating booster
- `operation_Qww_booster_kgCO2e` — DHW booster

**Solar offsets** (negative, optional):
- `PV_E_offset_kgCO2e`, `PVT_E_offset_kgCO2e`, `PVT_Q_offset_kgCO2e`, `SC_Q_offset_kgCO2e`

**Metadata**: `name` — building identifier

### Why solar offset rows are sometimes missing (FAQ)

A common confusion when reading the emission timeline: a scenario with
solar configured may show *no* negative-y offset bars. Three reasons,
in increasing subtlety:

1. **No solar configured.** If `configuration.{json,yml}` has every
   `solar.{roof, wall_*}` set to `None`, no `PV_*_kWh` / `PVT_*_kWh` /
   `SC_*_kWh` columns exist in `B####.csv`, so no offset row is written.
   Trivial case — check the per-building `solar` block first.

2. **SC is wired as the DHW primary** (the SC-DHW dispatch case). When
   `hot_water.type == 'SC'`, the SC thermal output is dispatched into
   `Qww_sys_SOLAR_kWh` (a zero-emission carrier — see
   `_ZERO_EMISSION_CARRIERS = {'DH','DC','NONE','SOLAR'}`). To prevent
   double-counting, `cea/analysis/final_energy/calculation.py` drops
   the per-facade `SC_*_kWh` columns from `B####.csv` for these buildings.
   The legacy `SC_Q_offset_kgCO2e` row therefore never gets generated.

   **The benefit is still in the chart**, it just shows up as a smaller
   *positive* operational-DHW layer (smaller `Qww_sys_GRID_kWh` /
   `Qww_sys_NATURALGAS_kWh` from the backup) instead of a visible
   negative offset. To compare against a no-SC baseline, run a sibling
   what-if without SC and diff the operational-DHW layer.

   PVT thermal is **not** affected — it's not allowed as a DHW primary
   (operating temperature too low for the DHW setpoint), so its `PVT_*_Q_kWh`
   columns survive and the legacy `PVT_Q_offset_kgCO2e` path still fires.

3. **PV / PVT electrical surfaces produce zero output**. If the
   per-surface generation is 0 (e.g. a heavily-shaded facade), the
   matching `PV_*_E_kWh` column may not be written, so the corresponding
   offset is absent. Inspect per-facade `PV_*` / `PVT_*_E_kWh` columns
   in `B####.csv` to verify.

If a user reports "missing solar offset," walk these in order. The
SC-DHW case (#2) is the one that surprises people most because the
panels *are* there and *are* doing useful work — the chart just
attributes the work to the SOLAR carrier (zero-emission, so it shrinks
the positive bar) rather than emitting it as a negative offset node.
See `cea/technologies/solar/AGENTS.md` § 3 for the data-flow detail.

### Plant Timeline (District Aggregate)

- `operation_DH_kgCO2e` — District heating plant emissions
- `operation_DC_kgCO2e` — District cooling plant emissions

## Plant Emission Proportional Allocation

Plant emissions are **not constant** across years. They are proportionally allocated based on building construction years and their DH/DC energy demand:

```
For each year Y:
    demand_Y = sum(building_DH_demand for buildings where construction_year <= Y)
    weight_Y = demand_Y / total_DH_demand
    operation_DH_kgCO2e[Y] = plant_annual_total × weight_Y
```

**Data sources**:
- `configuration.json` → which buildings use DH/DC (scale=DISTRICT)
- `B####.csv` (final-energy) → per-building annual DH/DC consumption (`*_DH_kWh`, `*_DC_kWh`)
- `building_properties.typology[name]['year']` → construction year

**Limitation**: The thermal network model does not track actual connection dates. Construction year is used as proxy for the earliest possible connection date.

## `_tech_name_mapping` (hourly_operational_emission.py)

```python
_tech_name_mapping = {
    "Qhs_sys": "hs",        "Qww_sys": "dhw",
    "Qcs_sys": "cs",         "E_sys": "el",
    "Qhs_booster": "hs_booster", "Qww_booster": "dhw_booster",
}
```

Drives `_COLUMN_MAPPING` and `_OPERATIONAL_COLS` in `BuildingEmissionTimeline`.

## Carrier Column Prefixes (emission_time_dependent.py)

```python
_CARRIER_COLUMN_PREFIXES = ('Qhs_sys_', 'Qww_sys_', 'Qcs_sys_', 'E_sys_',
                             'Qhs_booster_', 'Qww_booster_')
```

Used by `_calc_operational_emissions_from_fe()` to scan building final-energy CSV columns.

## `BuildingEmissionTimeline` API

```python
timeline = BuildingEmissionTimeline(building_properties, envelope_lookup, building_name, locator, end_year)
timeline.fill_embodied_emissions()                          # Envelope components
timeline.fill_solar_embodied_emissions(solar_config)        # What-if: solar from config
timeline.fill_pv_embodied_emissions(pv_codes)               # Legacy: PV from results
timeline.fill_operational_emissions(feedstock_policies, operational_df)  # Operational + decarbonisation
timeline.demolish(demolition_year)                          # Zero out future + log demolition
timeline.save_timeline()                                    # Legacy: save to outputs/lca/
timeline.timeline                                           # pd.DataFrame — the actual data
```

## `OperationalHourlyTimeline` API (Legacy)

```python
hourly = OperationalHourlyTimeline(locator, bpr)            # Reads demand CSV, creates 8760 timeline
hourly.calculate_operational_emission()                      # Multiply demand × emission intensity
hourly.apply_pv_offsetting(pv_codes)                         # Subtract PV generation offsets
hourly.save_results()                                        # Save to outputs/lca/operational/hourly/
hourly.operational_emission_timeline_extended                 # pd.DataFrame with all columns
```

## Grid Emission Intensity Override

`_load_grid_emission_intensity_override(config)` → `(bool, np.array|None)`
- Reads external CSV with 8760 (or 8784 → drops Feb 29) hourly grid carbon intensity values (g CO2/kWh)
- Configured via `config.emissions.grid_carbon_intensity_dataset_csv` + `csv_carbon_intensity_column_name`
- Overrides the GRID column in feedstock emission intensity

## Feedstock Decarbonisation Policies

```python
feedstock_policies = {"GRID": (reference_year, target_year, target_emission_factor)}
```

Applied per-year in `BuildingEmissionTimeline._apply_feedstock_policies()` — linearly interpolates emission factors between reference and target years, then applies to operational timeline.

Configured via: `config.emissions.grid_decarbonise_reference_year`, `grid_decarbonise_target_year`, `grid_decarbonise_target_emission_factor`

## Key Patterns

### DO: Add new operational column types
1. Add entry to `_tech_name_mapping` in `hourly_operational_emission.py`
2. Add carrier prefix to `_CARRIER_COLUMN_PREFIXES` in `emission_time_dependent.py`
3. Update plot categorisation in `cea/visualisation/special/emission_timeline.py`

### DON'T: Assume plant columns follow building naming
Plant hourly files use `plant_primary_{NT}_{CARRIER}_kgCO2e` — completely different from building `{service}_{CARRIER}_kgCO2e` prefixes. Plant columns are handled separately in `_calc_plant_operational_emissions_from_fe()`.

### DON'T: Modify `_ZERO_EMISSION_CARRIERS` without updating plant timeline
If DH/DC are removed from zero-emission carriers, plant emissions would be double-counted (once at building level, once at plant level).

## Related Files

- `cea/visualisation/special/emission_timeline.py` — Timeline plot (categories, colours, `_aggregate_into_9_categories`)
- `cea/visualisation/a_data_loader.py` — Loads emission data for bar/stacked plots
- `cea/visualisation/b_data_processor.py` — Processes emission data for plotting
- `cea/databases/feedstocks/` — Carrier emission factors
- `cea/demand/building_properties/` — `BuildingProperties`, typology (construction year)
- `cea/datamanagement/database/envelope_lookup.py` — `EnvelopeLookup` for embodied emissions
- `cea/datamanagement/database/components.py` — `Feedstocks` class
