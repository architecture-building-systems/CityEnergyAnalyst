# Thermal Network Design

Thermal network design features enable the planning and analysis of district heating and cooling systems. The process is divided into three parts:

1. **Part 1 — Layout**: generate or load a pipe trench layout and select which buildings are connected per service.
2. **Part 2 — Flow & Sizing**: simulate thermal-hydraulic performance and size pipes for a single network.
3. **Part 2b — Multi-Phase**: optimise pipe sizing across a sequence of networks that represent phased expansion or decommissioning over time.

CEA 4 supports **multiple network layouts** per scenario, lets you **chain a new layout off an existing one** (to add or remove buildings), and now lets you **decommission buildings between phases** under a sunk-infrastructure cost model.

---

## Thermal Network Part 1: Layout

### Overview
Generates a thermal network **pipe trench** (a single geometry that can carry both DH and DC pipes) and the service-specific node sets for district heating (DH) and/or district cooling (DC). There are three ways to produce a layout:

1. **Auto-generate** from street geometry using a Steiner spanning tree over the requested buildings.
2. **Upload** your own shapefile / GeoJSON network.
3. **Chain off an existing CEA-generated network** (`existing-network` parameter) and adjust its connected buildings — adding new ones, removing decommissioned ones, or both — without redrawing the trench from scratch.

The same tool handles all three paths; which one runs depends on which parameters you set.

**New in CEA 4**:
- Multiple network layouts per scenario with unique names (e.g. `sub1`, `sub2`, `baseline`, `optimised`).
- Universal pipe trench (`layout.shp`) shared by DH and DC, with separate per-service node files.
- `existing-network` + `network-layout-mode` lets you evolve a network across phases while keeping pipe names stable so downstream tools can match pipes across runs.
- **Plant nodes are protected infrastructure**: when filtering a network, plant nodes and their incident pipes are never pruned, even if the anchor building was removed.

### When to Use
- Designing a new district heating or cooling network
- Evolving an existing network across phases (adding new consumers, decommissioning old ones)
- Comparing alternative network designs side-by-side
- Loading a network designed externally in Rhino/Grasshopper/QGIS

### How It Works

**Auto-generation path**:
1. Read building footprints and street network
2. Pick the set of connected buildings (from `heating-/cooling-connected-buildings` config or from supply.csv)
3. Run a Kou or Mehlhorn Steiner spanning tree over those buildings along the street graph
4. Add plant nodes near the anchor building (highest demand or user-specified)
5. Write `layout.shp` (universal trench), `DH/layout/nodes.shp`, `DC/layout/nodes.shp`

**Existing-network path**:
1. Load the existing network's `layout.shp` + node files, merging DC and DH nodes into a single working graph
2. Apply the selected `network-layout-mode` to reconcile connected buildings with the `heating-/cooling-connected-buildings` parameters
3. Write the reconciled output under the new network name. **Original pipe names are preserved for shared geometries** so multi-phase tools (Part 2b) can match pipes across phases.

### Prerequisites
- **Energy Demand Part 2** — building loads must be available
- **Streets Helper** — street network must exist (only needed for auto-generation or for augment/filter modes that add new pipes)
- Zone geometry

### Required Input Files
- **Street network**: `streets.shp`
- **Total demand**: `Total_demand.csv`
- **Zone geometry**: building footprints
- **For `existing-network`**: the prior network's `layout.shp` + `{DH,DC}/layout/nodes.shp` under `outputs/data/thermal-network/{existing_name}/`

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **network-name** | Unique name for the layout being created | e.g. `sub1`, `baseline`, `optimised` |
| **network-type** | Services to generate: DH, DC, or both | `['DH']`, `['DC']`, `['DH', 'DC']` |
| **existing-network** | Name of a prior network to chain off. Leave blank for a fresh auto-generation. | blank, or `sub1` |
| **network-layout-mode** | How to reconcile connected buildings when loading an existing network or a user-provided one. See below. | `validate` / `augment` / `filter` |
| **auto-modify-network** | Whether `augment` / `filter` modes may actually modify the network. If `false`, they error instead of modifying. | `true` |
| **heating-connected-buildings** | DH consumers (overrides supply.csv when `overwrite-supply-settings=true`) | e.g. `['B1001','B1002',...]` |
| **cooling-connected-buildings** | DC consumers | e.g. `['B1001','B1003']` |
| **consider-only-buildings-with-demand** | Drop buildings with zero heating/cooling demand | `true` |
| **connection-candidates** | How many candidate trunk connection points per building (Kou only) | `3` |
| **snap-tolerance** | Max distance to snap near-miss endpoints (m) | `0.5` |
| **edges-shp-path** / **nodes-shp-path** | Paths to a user-provided shapefile layout | blank for auto |
| **network-geojson-path** | Path to a user-provided GeoJSON layout | blank |

### Network Layout Modes

When loading an existing network or a user-provided layout, the engine reconciles the loaded buildings against `heating-/cooling-connected-buildings` according to `network-layout-mode`:

| Mode | Missing buildings | Extra buildings | Use case |
|------|------------------|-----------------|----------|
| **validate** | ❌ Error | ❌ Error | Strict check — fail if the loaded network doesn't match the parameter exactly |
| **augment** | ➕ Add (Steiner tree off the street network) | ✓ Keep | Grow an existing network — add new connections, keep everything that was there |
| **filter** | ➕ Add | ➖ Remove (with plant preservation and stub pruning) | Shrink or refine an existing network — drop decommissioned buildings, keep the rest |

**Plant preservation invariant for filter**: plant nodes and the pipes connecting them to the trunk are never pruned, even if the building they were anchored to was removed. If a plant ends up in a component with no surviving consumers, the plant and its pipework are still kept and a warning is printed.

**Stub pruning**: after filter drops a building, any junction node with degree ≤ 1 that isn't a terminal or plant is iteratively removed along with its pipe, so the output doesn't contain dangling pipe stubs.

### How to Use

1. **Complete prerequisites**: Energy Demand + Streets Helper.

2. **Pick the flow** — one of:
   - **Fresh auto-generation**: leave `existing-network`, `edges-shp-path`, `nodes-shp-path`, `network-geojson-path` all blank.
   - **User-provided layout**: set `edges-shp-path` + `nodes-shp-path` (or `network-geojson-path`).
   - **Chain off an existing network**: set `existing-network` to the previous network's name.

3. **Run layout generation**:
   - Navigate to **Thermal Network Design → Part 1: Layout**
   - Give the new layout a **unique `network-name`**
   - Select `network-type` (`DH`, `DC`, or both)
   - If chaining or uploading, pick a `network-layout-mode`
   - Set `heating-connected-buildings` / `cooling-connected-buildings` if you want to override supply.csv
   - Click **Run**

4. **Processing time**: usually under a minute for typical districts.

### Output Files

All outputs go under `outputs/data/thermal-network/{network_name}/`:

- `layout.shp` — **universal pipe trench** (DC + DH edges deduplicated by geometry). This is the authoritative edge file.
- `DH/layout/nodes.shp` — DH-service nodes (consumers, plants, junctions)
- `DH/layout/edges.shp` — DH-service edges written by Part 2 downstream
- `DC/layout/nodes.shp` — DC-service nodes
- `DC/layout/edges.shp` — DC-service edges (Part 2)
- `connectivity.json` — per-building service metadata (which buildings connect to which service, with `overwrite_supply_settings` flag and timestamp)

**Edge-name stability**: when using `existing-network`, Part 1 preserves the original pipe names for any edge that existed in the source layout. Only genuine name collisions are renumbered. This is what makes multi-phase matching work — sub1's `PIPE1` stays `PIPE1` when you derive sub2 from sub1.

### Understanding Layout Results

Key metrics to review:
- **Total pipe length** (m or km)
- **Number of connected buildings**
- **Network density** (pipe length per connected building)
- **Building connection points**

Typical network characteristics:
- Tree networks: Pipe length = 0.8-1.5× linear distance between buildings
- Looped networks: Pipe length = 1.2-2.0× tree network length
- Urban density: 20-80 m pipe per building

### Visualising the Network
1. Use CEA-4 App 3D viewer to see network overlay
2. Export to Rhino/Grasshopper for detailed visualisation
3. Open shapefiles in QGIS or ArcGIS

### Tips
- **Accurate streets matter**: network follows streets, so street quality affects results
- **Check connectivity**: verify all desired buildings are connected to a plant
- **Consider future expansion**: leave capacity for additional connections
- **Manual editing**: you can manually edit the generated shapefiles if needed
- **Multiple scenarios**: create several network layouts (e.g. `baseline`, `low-temp`, `high-density`) to compare different design approaches
- **Network naming**: use descriptive names that help you remember the design strategy (e.g. `tree-80C`, `loop-60C`, `sub1`, `sub2`)
- **Chaining via `existing-network`**: for phased scenarios, derive each phase from the previous one using `existing-network` + `filter` or `augment`. This preserves pipe names across phases so Part 2b can match pipes correctly.
- **`filter` vs `augment`**: pick `filter` when the new phase should be an exact match to the listed connected buildings (drops decommissioned buildings, adds new ones). Pick `augment` when you only want to add buildings to an existing layout without removing anything.
- **Plant preservation**: when a filter run removes a building that was anchoring a plant, the plant node and its pipe stay put. You'll see a warning in the log if a plant ends up with no surviving consumers.

### Troubleshooting

**Issue**: Not all buildings connected
- Check that the street network covers the building areas
- Some buildings may be too far from streets — Part 1 snaps via `snap-tolerance`, but distances beyond that won't be bridged

**Issue**: Network layout doesn't follow streets well
- Improve street network quality with Streets Helper
- Manually add missing street segments

**Issue**: Missing output shapefiles
- Check for error messages in the log
- Verify `Total_demand.csv` exists and has valid data for every connected building

**Issue**: `Validation failed for DH (cooling)/...` when using `existing-network`
- The existing network's building set doesn't match `heating-/cooling-connected-buildings`
- **Fix**: switch `network-layout-mode` from `validate` to `augment` (to add missing buildings) or `filter` (to also remove extras), and make sure `auto-modify-network=true`

**Issue**: "Duplicated NODE IDs" when Part 2 reads the layout
- Usually caused by name collisions in the merged universal trench
- **Fix**: re-run Part 1 — the current version auto-resolves name collisions via `_resolve_duplicate_pipe_names` and merges DC + DH nodes with canonical ids to prevent this

---

## Thermal Network Part 2: Flow & Sizing

### Overview
Performs detailed thermal hydraulic simulation of the network created in Part 1. This feature calculates mass flow rates, pipe sizes, temperatures, pressure drops, and pump requirements for district heating or cooling systems.

### When to Use
- After generating network layout (Part 1)
- Sizing pipes for district energy systems
- Calculating pumping energy and pressure requirements
- Assessing thermal losses in distribution
- Verifying network hydraulic feasibility

### What It Calculates

**Hydraulic Analysis**:
- Mass flow rates in each pipe segment (kg/s)
- Required pipe diameters (mm)
- Pressure drops along network (Pa)
- Pump head and power requirements (kW)

**Thermal Analysis**:
- Supply and return temperatures at each node (°C)
- Heat losses from pipes (kW, kWh/year)
- Temperature drops along network
- Building substation heat exchangers

**Network Performance**:
- Total annual heat delivered (MWh/year)
- Total annual heat losses (MWh/year, %)
- Pumping energy consumption (MWh/year)
- Peak loads and flows (kW, kg/s)

### Prerequisites
- **Thermal Network Part 1** - Network layout must exist
- **Energy Demand Part 2** - Building hourly demands needed
- Weather file for ground temperature

### Required Input Files
- **Network layout**: Nodes and edges shapefiles (from Part 1)
- **Building demands**: Individual building demand files (`BXXX.csv`)
- **Component databases**: Pipe and system properties
- **Weather file**: For ground temperature calculation

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Network name** | Select which network layout to simulate | Choose from dropdown (created in Part 1) |
| **Network type** | DH or DC | Must match the network created in Part 1 |
| **Supply temperature** | Network supply temp | 80°C (DH) / 6°C (DC) |
| **Return temperature** | Network return temp | 50°C (DH) / 12°C (DC) |
| **Pipe insulation** | Insulation standard | Standard / High performance |
| **Ground temperature** | For heat loss calculation | From weather file |
| **Multiprocessing** | Parallel processing | Enabled |

**Note on temperature**: The network temperature regime is fully determined in Part 2 by the supply/return temperature parameters. The order of heating/cooling services configured in Part 1 does not affect the temperature regime.

### How to Use

1. **Complete network layout** (Part 1)

2. **Configure parameters**:
   - Navigate to **Thermal Network Design**
   - Select **Thermal Network Part 2: Flow & Sizing**
   - **Select network name** from dropdown (must be created in Part 1)
   - Select network type (must match the type used in Part 1)
   - Set supply/return temperatures:
     - **District heating**: 70-90°C supply, 40-50°C return
     - **Low-temperature district heating**: 50-70°C supply, 30-40°C return
     - **District cooling**: 5-8°C supply, 12-15°C return
   - Choose pipe insulation standard
   - Enable multiprocessing

3. **Run analysis**:
   - Click **Run**
   - Processing time: 10-60 minutes depending on network size and complexity

### Output Files

All Part 2 outputs are written under `outputs/data/thermal-network/{network_name}/{DH|DC}/`:

- **Edge sizing results** (`edges.csv` / `edge_list.csv`): pipe diameters, mass flow rates, pressure drops, heat losses per metre, temperature drops
- **Node results** (`nodes.csv`): node pressures, supply/return temperatures, building heat exchanger sizing
- **Plant thermal requirement** (`plant_thermal_load_kW.csv`): hourly heat duty at each plant
- **Plant pumping requirement** (`plant_pumping_load_kW.csv`): hourly pumping power
- **Network summary**: total pipe length and volume, annual heat losses, pumping energy
- **Substation files**: one CSV per connected building

**Note**: Results are organised by network name, so you can compare performance across different network designs without overwriting each other.

### Pipe Cost Database

Part 2 and Part 2b both read pipe costs from `{scenario}/inputs/technology/COMPONENTS/DISTRIBUTION/THERMAL_GRID.csv`. The following columns are **required** — any missing column will cause Part 2b (multi-phase sizing) to error out with a clear message pointing at the file:

| Column | Meaning | Example |
|--------|---------|---------|
| `pipe_DN` | Nominal diameter in mm | `20`, `50`, `100`, `200` |
| `Inv_USD2015perm` | Install cost in USD2015 per metre of pipe | `491.53` |

Other columns (`D_ext_m`, `D_int_m`, `D_ins_m`, `Vdot_min_m3s`, `Vdot_max_m3s`, `code`) are used by Part 2's hydraulic simulation. If your scenario inherits the default CH/DE/SG databases from CEA, all columns are already present.

If the required diameter produced by the simulation exceeds the largest DN in the database, the tool errors out rather than silently snapping to the largest available size — add a larger pipe row to the database, or check why the simulation is producing an oversized diameter.

### Understanding Results

#### Key Performance Indicators

**Heat Losses**:
- Well-designed DH: 10-20% annual losses
- Older DH networks: 20-35% losses
- Low-temperature DH: 5-15% losses

**Pumping Energy**:
- Typical: 1-3% of delivered heat energy
- Long networks or high ΔT: Up to 5%
- Affects system efficiency significantly

**Pipe Sizes**:
- Small buildings: DN25-DN50 (25-50 mm diameter)
- Medium buildings: DN50-DN100
- Main distribution: DN100-DN300
- Large district mains: DN300-DN600

#### Validation Checks

1. **Pressure feasibility**: All pressures should be positive (no cavitation)
2. **Temperature feasibility**: Return temp > supply temp at all points should never occur
3. **Reasonable losses**: Total losses typically 10-20% for new networks
4. **Flow velocities**: Typically 0.5-3 m/s (check derived from mass flow and diameter)

### Advanced Options

#### Network Temperature Regimes

**High-Temperature DH** (80-90°C):
- Traditional systems
- Higher heat losses
- Suitable for old buildings

**Low-Temperature DH** (50-70°C):
- Modern systems
- Lower heat losses
- Requires better building insulation
- Enables heat recovery sources

**Very Low-Temperature DH** (30-50°C):
- Ultra-modern systems
- Minimal heat losses
- Requires heat pumps at buildings
- Can also provide cooling

#### Pipe Insulation Standards

- **Standard**: Typical for urban DH (λ ≈ 0.023 W/mK)
- **High performance**: Better insulation for lower losses (λ ≈ 0.018 W/mK)
- **Twin pipes**: Pre-insulated pipe pairs (supply + return)

### Tips

1. **Temperature optimisation**: Lower supply temperatures reduce heat losses
2. **Pressure management**: Long networks may need intermediate pumping stations
3. **Insulation pays off**: Better insulation reduces operating costs
4. **Validate with reality**: Compare results with existing network data if available
5. **Consider future growth**: Size pipes with expansion margin (10-20%)

### Troubleshooting

**Issue**: Simulation fails or crashes
- **Solution**: Check network layout for disconnected segments
- **Solution**: Verify all buildings in network have valid demand data
- **Solution**: Try disabling multiprocessing for debugging

**Issue**: Unrealistic pressure drops (very high or negative)
- **Solution**: Check network connectivity and flow directions
- **Solution**: Verify pipe properties in database
- **Solution**: Review supply/return temperature settings

**Issue**: Very high heat losses (>30%)
- **Solution**: Check pipe insulation settings
- **Solution**: Verify ground temperature is reasonable
- **Solution**: Consider lower supply temperatures

**Issue**: No pump requirements calculated
- **Solution**: Check that network has defined plant location
- **Solution**: Verify pressure boundary conditions

---

## Thermal Network Part 2b: Multi-Phase Sizing

### Overview
Optimises pipe sizing across a **sequence of networks** that represent a phased rollout (and/or phased decommissioning) of a thermal network over time. Instead of sizing each phase independently, Part 2b sees the full timeline at once and decides when each pipe should be installed, replaced, kept, or left idle — minimising total capital + replacement cost under a **sunk infrastructure** cost model.

### When to Use
- Planning incremental network rollouts (e.g. connect district A now, district B in 2050, district C in 2075)
- Evaluating phased decommissioning (buildings drop off the network over time)
- Choosing between "oversize now vs replace later" strategies
- Comparing cost of different phasing plans

### Physical Model: Sunk Infrastructure

**Invariant**: once a pipe is installed in any phase, it stays in the trench forever. No salvage value, no removal cost, no physical downsize. Connected buildings, however, can change freely between phases — additions AND removals are allowed.

Consequences:

- Phase-N flow simulation uses only phase N's connected set. Decommissioned buildings contribute zero demand to phase N.
- A pipe whose downstream building was decommissioned is labelled **idle** in that phase: the pipe is preserved in the trench at its previously installed DN, but carries no flow and costs nothing that phase.
- A pipe that is reactivated later (its consumer comes back) keeps the originally-installed DN if demand fits, or triggers a replace if demand grew.
- Required DN can never exceed the largest DN in the cost database — the tool errors out rather than silently snapping.

### Per-Phase Action Vocabulary

Every edge × phase pair is labelled with one of:

| Action | Meaning | CAPEX |
|--------|---------|-------|
| `none` | Pipe has not been installed yet in any prior phase | 0 |
| `install` | Pipe is being installed for the first time this phase | full |
| `replace` | Required DN > installed DN; pipe is being upgraded | replace × `replacement-cost-multiplier` |
| `keep` | Pipe exists, required DN ≤ installed DN, still flowing | 0 |
| `idle` | Pipe installed in a prior phase, no flow this phase (decommissioned building) | 0 |

### Prerequisites
- **Thermal Network Part 1** run for each phase (e.g. `sub1`, `sub2`, `sub3`). The typical workflow is:
  1. Run Part 1 for `sub1` (the initial network)
  2. Run Part 1 for `sub2` using `existing-network=sub1` + adjusted `heating-/cooling-connected-buildings`
  3. Run Part 1 for `sub3` using `existing-network=sub2` + further adjustments
- **Pipe cost database** (`THERMAL_GRID.csv`) with `pipe_DN` and `Inv_USD2015perm` columns (see Part 2 above)
- Each phase's consumer buildings must have energy demand calculated

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **phasing-plan-name** | Identifier for this phasing plan | e.g. `plan8` |
| **network-name** (list) | Ordered list of per-phase networks from Part 1 | `['sub1', 'sub2', 'sub3']` |
| **phase-completion-year** (list) | Calendar years for each phase (same length as network-name) | `['2025', '2050', '2075']` |
| **network-type** | DH or DC (multi-phase runs one service at a time) | `['DH']` |
| **sizing-strategy** | How to trade off install vs replacement cost | `optimise` |
| **replacement-cost-multiplier** | Cost penalty for replacing a pipe in a later phase | `1.5` |

#### Sizing Strategies

| Strategy | Behaviour |
|----------|-----------|
| **optimise** | For each pipe, compare "size for each phase and replace as demand grows" vs "pre-size at final-phase DN" and pick the cheaper option |
| **size-per-phase** | Always size each pipe for the current phase's demand; replace when demand grows |
| **pre-size-all** | Install every pipe at its final-phase DN up front (never replaces) |

### How to Use

1. **Run Part 1 for each phase** in chronological order, using `existing-network` to chain them:
   ```
   Part 1 run 1: network-name = sub1, existing-network = (blank), heating-connected-buildings = [initial set]
   Part 1 run 2: network-name = sub2, existing-network = sub1, heating-connected-buildings = [phase-2 set], network-layout-mode = filter (or augment)
   Part 1 run 3: network-name = sub3, existing-network = sub2, heating-connected-buildings = [phase-3 set], network-layout-mode = filter
   ```
   Buildings can be added OR removed between phases — the filter mode handles both.

2. **Run Part 2 for each phase** individually (`thermal-network` tool) to generate per-phase simulation results. This populates the `edge_list.csv` metadata that Part 2b reads to get per-pipe flow requirements.

3. **Run Part 2b**:
   - Navigate to **Thermal Network Design → Part 2b: Multi-Phase**
   - Set `phasing-plan-name` (e.g. `plan8`)
   - Set `network-name` to your ordered phase list: `['sub1', 'sub2', 'sub3']`
   - Set `phase-completion-year` to matching years: `['2025', '2050', '2075']`
   - Pick `sizing-strategy` and `replacement-cost-multiplier`
   - Click **Run**

### Output Files

All Part 2b outputs go under `outputs/data/thermal-network/phasing-plans/{phasing-plan-name}/{DH|DC}/`:

- `phasing_summary.csv` — one row per phase: year, connected-building count, peak demand, install + replacement cost, plus a new `num_idle` column counting decommissioned-but-preserved pipes
- `pipe_sizing_decisions.csv` — one row per (edge, phase) with action (`install` / `replace` / `keep` / `idle` / `none`), DN, cost
- `edges_timeline.csv` — timeline of every installed pipe with its per-phase DN and action. **Idle phases are emitted with their installed DN preserved** so you can trace the full life of a pipe
- `nodes_timeline.csv` — one row per unique node with `phase_introduced` and `phase_last_seen` (the latter tells you when a consumer was decommissioned)
- `layout/edges.shp` + `layout/nodes.shp` — **timeline shapefile** covering the union of every pipe ever installed, with attributes: `ph_intro`, `yr_intro` (first install), `ph_last`, `yr_last` (last active phase), `idle_final` (1 if the pipe is idle in the final phase), `DN_final`, `num_repl`, `cost_USD`
- Per-phase subfolders (`sub1/layout/`, `sub2/layout/`, `sub3/layout/`) — each contains the full network layout visible at that phase, with every pipe labelled by its action for that phase

**Note on ESRI shapefile column widths**: attribute names are truncated to 10 characters, so the shapefile uses short names (`ph_intro`, `yr_intro`, `ph_last`, `yr_last`, `idle_final`, `num_repl`, `cost_USD`) rather than the longer names in the CSVs.

### Understanding Multi-Phase Results

**Reading the sizing decisions**:
- A pipe with phase 1 = `install`, phase 2 = `keep`, phase 3 = `keep` → installed once, cost only in phase 1, no upgrades needed
- Phase 1 = `install`, phase 2 = `replace`, phase 3 = `keep` → installed small, upgraded in phase 2 at 1.5× cost
- Phase 1 = `install`, phase 2 = `idle`, phase 3 = `idle` → installed in phase 1, building decommissioned in phase 2, pipe still in trench but carrying no flow
- Phase 1 = `none`, phase 2 = `install`, phase 3 = `keep` → new pipe added in phase 2 (served a building added in phase 2)

**Expected patterns**:
- Total CAPEX is heavily front-loaded if using `pre-size-all` or if all buildings connect in phase 1
- `num_idle` grows over time if you're modelling decommissioning
- With `optimise` strategy, you should see a mix of `install` and `replace` actions depending on each pipe's growth profile

### Troubleshooting

**Error**: `Phase N (subX) has consumer nodes that are not connected to any plant: ...`
- A phase dropped a trunk-middle building and left a downstream branch orphaned from the plant
- **Fix**: re-run Part 1 for that phase with the trunk building kept, or adjust the layout so the surviving consumers still have a path to a plant

**Error**: `THERMAL_GRID.csv is missing required column(s): ['Inv_USD2015perm']`
- Your pipe cost database is missing the canonical column
- **Fix**: use the default CH/DE/SG database, or add a column named `Inv_USD2015perm` (per-metre install cost in USD2015)

**Error**: `Pipe sizing needs DN N mm, but the largest DN in the cost database is M mm`
- The simulation produced a required diameter larger than anything in the database
- **Fix**: add a larger pipe row to `THERMAL_GRID.csv`, or check why the simulation is producing an oversized diameter

**Error**: `Thermal-network simulation failed for phase N (subX): ...`
- One of the per-phase single-phase simulations crashed
- **Fix**: run `thermal-network` directly on that phase to get the raw error, then troubleshoot normally (missing demand files, disconnected graph, etc.)

---

## Complete Thermal Network Workflow

### Standard Single-Network Workflow

1. **Data Preparation**:
   - Run [Energy Demand Part 2](04-demand-forecasting.md) for all buildings
   - Run [Streets Helper](08-data-management.md#streets-helper) to get street network

2. **Network Layout (Part 1)**:
   - Give your network a name (e.g. `baseline`)
   - Select service(s): DH, DC, or both
   - Leave `existing-network` blank for fresh auto-generation
   - Review the generated `layout.shp` and per-service node files

3. **Network Sizing (Part 2)**:
   - Select the network name created in Part 1
   - Set supply/return temperatures appropriate for the service
   - Review pipe sizes, heat losses, pumping energy

4. **Optimisation (optional)**:
   - Run [District Supply System Optimisation](07-supply-optimisation.md)
   - Iterate on network configuration if needed

5. **Analysis** (via what-if scenarios):
   - Run [Final Energy](06-1-final-energy.md), [Emissions](06-2-emissions.md), [System Costs](06-3-system-costs.md), [Heat Rejection](06-4-heat-rejection.md)
   - Use [Visualisation tools](10-visualisation.md) to present results

### Phased / Multi-Phase Workflow

Use this when you want to model a network that **evolves over time** — e.g. connect the city centre in 2025, expand to the northern district in 2050, decommission the steel mill in 2075.

1. **Data preparation**: same as single-network (demand + streets).

2. **Phase 1 layout**:
   - Run Part 1 with `network-name = sub1`, `existing-network = (blank)`, connected buildings = initial set.

3. **Phase 2 layout**:
   - Run Part 1 with `network-name = sub2`, `existing-network = sub1`, `network-layout-mode = filter` (or `augment`), connected buildings = phase-2 set.
   - Buildings can be added OR removed relative to phase 1.

4. **Phase 3 layout** (and so on):
   - Run Part 1 with `network-name = sub3`, `existing-network = sub2`, same pattern.

5. **Per-phase flow & sizing (Part 2)**:
   - Run Part 2 for each of `sub1`, `sub2`, `sub3` individually. This gives per-phase demand, mass flow, and an edge list that Part 2b will consume.

6. **Multi-phase optimisation (Part 2b)**:
   - Run Part 2b with `phasing-plan-name = plan8`, `network-name = ['sub1','sub2','sub3']`, `phase-completion-year = ['2025','2050','2075']`, `sizing-strategy = optimise`.
   - Review `phasing_summary.csv`, `pipe_sizing_decisions.csv`, and the timeline shapefile in the map viewer.

### District Cooling Workflow
Same structure as district heating, but:
- Choose DC (district cooling) in Part 1
- Set cooling temperatures in Part 2 (e.g. 6°C / 12°C)
- Use cooling demands from the demand calculation

---

## Network Design Best Practices

### Layout Design
- **Follow streets**: Easier permitting and construction
- **Minimize length**: Reduce capital cost and heat losses
- **Strategic branching**: Balance tree simplicity with reliability
- **Future-proof**: Consider expansion areas

### Operating Strategy
- **Temperature optimisation**: Lower temps = lower losses
- **Load management**: Balance peak loads across network
- **Seasonal adjustment**: Vary temperatures with season
- **Smart controls**: Use real-time monitoring and control

### Pipe Sizing Principles
- **Design for peak load**: Ensure adequate capacity for coldest day
- **Consider velocity limits**: 0.5-3 m/s typical range
- **Pressure constraints**: Maximum ~16 bar in most systems
- **Standard sizes**: Use common pipe diameters for cost efficiency

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides building loads (prerequisite)
- **[Data Management](08-data-management.md#streets-helper)** - Streets Helper for network path
- **[Supply System Optimisation](07-supply-optimisation.md)** - Network and plant optimisation
- **[Life Cycle Analysis](06-0-life-cycle-analysis.md)** - Emissions and costs for networks

---

## Further Reading
- District heating design handbook
- EN 13941: Design and installation of pre-insulated bonded pipe systems
- IEA DHC Annex documents
- 4th Generation District Heating (4GDH) concepts

---

[← Back: Energy Demand](04-demand-forecasting.md) | [Back to Index](index.md) | [Next: Life Cycle Analysis →](06-0-life-cycle-analysis.md)
