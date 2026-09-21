# Energy Supply System Optimisation

Supply system features evaluate energy system configurations against cost, emissions, and energy consumption. Building scale (decentralised) compares a fixed set of configurations per building; district scale (centralised) uses a multi-objective genetic algorithm.

---

## Supply System Optimisation: Building-Scale

⚠️ **Note**: This feature is only available via **Command Line Interface (CLI)**. It is not accessible through the CEA-4 App dashboard.

### Overview
Evaluates decentralised energy supply systems for individual buildings. There is no search algorithm: for each building, CEA simulates a fixed set of heating and cooling supply configurations, compares them one-to-one, and flags the best one. Each building is treated independently, as if it were disconnected from any district network.

### When to Use
- Designing building-level energy systems
- Comparing retrofit options for existing buildings
- Supporting building-level investment decisions
- When district systems are not feasible

### What It Evaluates

**Heating** (13 configurations per building):
- Natural gas boiler
- Biogas boiler
- Fuel cell
- Ground-source heat pump with natural gas backup boiler, at ten heat pump / boiler capacity splits. Configurations whose heat pump exceeds what the building's footprint area allows for boreholes are disqualified

**Cooling** (6 configurations per building):
- Direct expansion / mini-split (not fully built yet)
- Vapour compression chiller with cooling tower
- Flat-plate or evacuated-tube solar collectors with a single-effect absorption chiller, boiler and cooling tower
- Combinations that supply the sensible cooling load separately from the air-handling / recirculation load

**How the best configuration is chosen**: configurations are ranked separately by total annualised cost (TAC) and by GHG emissions. The configuration with the best combined rank is flagged as `Best configuration`. If the rank is tied, the configuration with the lowest compounded relative cost and emissions is chosen (a random pick only if those are identical too).

### Prerequisites
- **Energy Demand Part 2** - `Total_demand.csv` and building loads
- **Solar collector potential (SC1 flat plate and SC2 evacuated tube)** for every building with a cooling load - the cooling calculation reads both
- Building supply properties, zone geometry and a weather file (used for the ground-source heat pump)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Multiprocessing** | Parallel evaluation | Enabled |
| **Number of CPUs to keep free** | CPUs left free for other work | 1 |

No other parameters: technology data come from the scenario's supply-system databases.

### How to Use

**Note**: This feature must be run from the command line. See [CLI Documentation](https://city-energy-analyst.readthedocs.io/) for detailed parameter configuration.

1. **Complete prerequisites**:
   - ✅ Energy Demand Part 2
   - ✅ Solar collector potential (SC1 and SC2)

2. **Run via CLI**:
   ```bash
   cea decentralized --scenario /path/to/scenario
   ```

3. **Configure parameters** (optional):
   - Only `--multiprocessing` and `--number-of-cpus-to-keep-free`
   - Enable multiprocessing (strongly recommended)

4. **Processing time**: Depends mainly on the number of buildings and available CPU cores. Each building is simulated independently, so multiprocessing helps directly.

### Output Files

> **Note the folder spelling.** Results are written to `outputs/data/optimization/decentralized/` with a
> **z**, even though the feature is named with an "s" elsewhere in the app.

All files are in `{scenario}/outputs/data/optimization/decentralized/`, one set per building:

| File | Content |
|------|---------|
| `BXXX_AHU_ARU_SCU_result_cooling.csv` | One row per cooling configuration: capacities, CAPEX, OPEX, GHG emissions, TAC, and a `Best configuration` flag |
| `BXXX_AHU_ARU_SCU_cooling_activation.csv` | Hourly activation of the best cooling configuration |
| `DiscOp_BXXX_result_heating.csv` | One row per heating configuration: capacities, CAPEX, OPEX, GHG emissions, TAC, and a `Best configuration` flag |
| `DiscOp_BXXX_result_heating_activation.csv` | Hourly activation of the best heating configuration |

### Understanding Results

- Compare configurations within one building using the `TAC_USD` and `GHG_tonCO2` columns; the flagged best configuration is a compromise between the two rankings, not a Pareto front.
- Building-scale results are not Pareto optimisation results, so they are not used by **Plot - Pareto Front**.

### Tips
- **Enable multiprocessing**: Buildings are simulated independently, so runs scale with available CPU cores
- **Keep a few CPUs free** so your machine stays responsive during long runs
- **Compare all rows**, not just the flagged best, if you care about a specific trade-off between cost and emissions

### Troubleshooting

**Issue**: Run fails with a missing file (e.g. solar collector results)
- **Solution**: Run the solar collector potential for both SC1 and SC2 first, and Energy Demand Part 2

**Issue**: Optimisation runs very slowly
- **Solution**: Enable multiprocessing
- **Solution**: Test on a scenario with fewer buildings first

**Issue**: A heat pump configuration is missing or marked as not best
- **Solution**: Heat pump sizes are limited by the building's footprint area (borehole space); larger heat pump shares are disqualified for small footprints

---

## District Supply System Optimisation

### Overview
Optimises centralised energy supply systems for entire districts. This feature finds optimal configurations for central plants, distribution networks, and building substations, considering both individual building requirements and district-level synergies.

### When to Use
- Designing district heating/cooling systems
- Planning energy hubs or neighbourhood systems
- Comparing centralised vs decentralised approaches
- Optimising plant locations and capacities
- Supporting district-level energy master planning

### What It Optimises

**Decision Variables**:
- Central plant technology types and capacities
- Network configuration (buildings to connect)
- Plant location
- Thermal storage size and operation
- Renewable energy integration (solar fields, geothermal, etc.)
- Peak vs base load equipment sizing
- Energy import/export strategies

**Objectives**:
Any combination selected under **Objective functions**:
1. **Minimise cost** (`cost`)
2. **Minimise GHG emissions** (`GHG_emissions`)
3. **Minimise system energy demand** (`system_energy_demand`)
4. **Minimise anthropogenic heat** (`anthropogenic_heat`)

### Additional Complexity vs Building-Scale

District optimisation must account for:
- **Network costs and losses** (pipe lengths, diameters, heat losses)
- **Load diversity** (coincidence of peaks across buildings)
- **Economy of scale** (larger central equipment often more efficient)
- **Technology synergies** (CHP, waste heat recovery, etc.)
- **Spatial constraints** (plant locations, network routing)

### Prerequisites
- **Energy Demand Part 2** - All building loads
- **Streets network** - For network routing (if thermal network)
- **Thermal Network Part 1** (optional but recommended) - Network layout

### Required Input Files
- Total demand summary
- Street network (for district heating/cooling)
- Cost, emission, and technology databases
- Renewable energy potential data (if available)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Network name** | Existing network layout for the base case, or (none) to auto-generate one from Input Editor > supply | From Thermal Network Part 1 |
| **Network type** | District heating or district cooling | DH / DC |
| **Buildings** | Buildings to include. Leave blank for all | All |
| **Cooling / heating / heat rejection components** | Technology categories to consider, in priority order (e.g. BOILERS, COGENERATION_PLANTS, HEAT_PUMPS) | Defaults |
| **Maximum number of networks** | Maximum thermal networks generated across the district | 2 |
| **Objective functions** | `cost`, `GHG_emissions`, `system_energy_demand`, `anthropogenic_heat` | Two or three objectives |
| **Available energy sources / potentials** | Unlimited carriers (grid, fossil, bio fuels) and local potentials (PV, PVT, SC, geothermal, water bodies, sewage) | Defaults |
| **Systems / networks algorithm** | Genetic algorithm used for supply systems and networks | NSGAIII |
| **GA population size** | Individuals per generation. Leave blank for the NSGA-III suggestion (92) | Blank |
| **GA number of generations** | Optimisation iterations | 3 (test) / more for real studies |
| **Generate detailed outputs** | Write hourly supply-system profiles | false |
| **Retain run results** | Keep this run instead of overwriting it next time | false |

### How to Use

1. **Complete prerequisites**:
   - ✅ Energy Demand Part 2 for all buildings
   - ✅ Streets network
   - ✅ (Optional) Thermal Network Part 1

2. **Configure optimisation**:
   - Navigate to **Energy Supply System Optimisation**
   - Select **District Supply System Optimisation**
   - Select the network layout and network type (DH or DC)
   - Choose the heating, cooling and heat rejection components, energy sources and potentials
   - Choose the objective functions
   - Set GA population size and number of generations

3. **Run optimisation**:
   - Click **Run**
   - **Processing time**: 2-24+ hours depending on:
     - District size (number of buildings)
     - Complexity (network + technologies)
     - Population × generations
     - Available CPU cores
   - Consider running overnight or on high-performance computer

### Output Files

All district results live under
`{scenario}/outputs/data/optimization/centralized/{DES_id}/`, where `{DES_id}` identifies one
near-Pareto-optimal district energy system (`current_DES` for the base case). Each candidate
system gets its own folder, so the Pareto set is a set of *folders* rather than one file.

> **Note the folder spelling**: `optimization` with a **z**.

**Supply systems summary**: `.../{DES_id}/Supply_systems/Supply_systems_summary.csv`
- Technology mix, equipment types and capacities for that district energy system
- Annual performance metrics

**Individual supply system structure**: `.../{DES_id}/Supply_systems/{system_id}_supply_system_structure.csv`
- One file per network (`N0000`) or standalone building (`B0000`)

**Network layout**: `.../{DES_id}/networks/{network_id}_layout.geojson`
- The optimised network geometry

**Network performance**: `.../{DES_id}/Supply_system_operation_details/network_performance.csv`
- Detailed thermal and hydraulic performance of the networks

**Hourly operation**: `.../{DES_id}/Supply_system_operation_details/{system_id}_operation.csv`
- Plant dispatch and storage operation, hour by hour

**Annual breakdown**: `.../{DES_id}/Supply_system_operation_details/{system_id}_annual_breakdown.csv`
- Annual energy demand, generation and losses per system

### Understanding Results

#### District vs Decentralised Trade-offs

**District systems advantages**:
- Economy of scale (lower cost per kW)
- Load diversity (lower peak capacity needed)
- Enable waste heat recovery
- Centralised maintenance
- Higher efficiency central equipment

**District systems disadvantages**:
- Network capital cost and losses (10-20%)
- Requires suitable density
- Less flexibility for individual buildings

**Decision threshold**:
- High-density areas (>0.5 MW/hectare): District often optimal
- Low-density areas (<0.2 MW/hectare): Decentralised often better
- Medium density: Depends on specifics

#### Typical Results

**Min cost solutions** might include:
- Gas CHP for baseload
- Gas boiler for peaks
- Moderate thermal storage
- Connect ~60-80% of buildings

**Min emission solutions** might include:
- Heat pumps with renewable electricity
- Large thermal storage
- Maximum building connections
- Solar thermal fields

### Tips
- **Very computationally intensive**: Plan for long run times
- **Use high-performance computing** if available
- **Start with coarse optimisation** (smaller population/generations) to understand solution space
- **Consider running overnight** or over weekend
- **Review network assumptions**: Network costs heavily influence results
- **Compare to decentralised**: Run building-scale optimisation too for comparison

### Troubleshooting

**Issue**: Extremely long computation time (>24 hours)
- **Solution**: Reduce population size and generations significantly
- **Solution**: Simplify technology options
- **Solution**: Consider smaller sub-district
- **Solution**: Use high-performance computing cluster

**Issue**: Network costs dominate results
- **Solution**: Verify network layout is reasonable (use Thermal Network Part 1)
- **Solution**: Check pipe cost database values
- **Solution**: Consider if district system is appropriate for this density

**Issue**: No centralised solutions in Pareto frontier
- **Solution**: This may indicate decentralised is truly better for this case
- **Solution**: Check that district options are enabled
- **Solution**: Verify building density is sufficient

---

## Comparing Building-Scale vs District-Scale

### When to Use Each

Use **Building-Scale Optimisation** when:
- Low building density
- Buildings have very different profiles
- No existing district infrastructure
- Individual building owners want autonomy
- Testing building-level options quickly

Use **District-Scale Optimisation** when:
- High building density
- Master planning for new developments
- Existing or planned district infrastructure
- Centralised ownership/management
- Access to waste heat or renewable sources

### Running Both for Comparison

Best practice workflow:
1. Run **building-scale** optimisation first (faster)
2. Review building-level optimal solutions
3. Run **district-scale** optimisation
4. Compare costs and emissions:
   - Sum of building-scale solutions = fully decentralised
   - District-scale results = centralised options
   - Choose based on cost/emission/practical considerations

---

## Optimisation Best Practices

### Parameter Selection (district-scale)
- **Testing**: 50 population × 25 generations (~1,000 evaluations)
- **Production**: 200 population × 100 generations (~20,000 evaluations)
- **Publication**: 300 population × 150 generations (~45,000 evaluations)

### Validation
- Check solutions are technically feasible
- Verify capacities are reasonable
- Compare to rule-of-thumb sizing
- Test sensitivity to key assumptions

### Interpretation
- **No single "best" solution**: Pareto frontier shows trade-offs
- Select solution based on priorities (cost, emissions, energy)
- Consider practical constraints (space, permits, expertise)
- Account for uncertainties (future energy prices, regulations)

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides loads (prerequisite)
- **[Renewable Energy Assessment](03-renewable-energy.md)** - Provides renewable potential
- **[Thermal Network Design](05-thermal-network.md)** - Network layout for district systems
- **[Life Cycle Analysis](06-0-life-cycle-analysis.md)** - Detailed cost and emission calculations
- **[Visualisation](10-visualisation.md)** - Plot Pareto frontiers

---

[← Back: Life Cycle Analysis](06-0-life-cycle-analysis.md) | [Back to Index](index.md) | [Next: Data Management →](08-data-management.md)
