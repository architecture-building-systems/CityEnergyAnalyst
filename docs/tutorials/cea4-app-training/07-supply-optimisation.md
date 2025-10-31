# Energy Supply System Optimisation

Supply system optimisation features use multi-objective optimisation algorithms to find optimal energy system configurations that balance cost, emissions, and energy consumption. The optimisation can be performed at building scale (decentralised) or district scale (centralised).

---

## Supply System Optimisation: Building-Scale

### Overview
Optimises decentralised energy supply systems for individual buildings. The feature explores combinations of conversion technologies (boilers, heat pumps, chillers, etc.) and renewable energy sources (PV, solar thermal, geothermal) to find cost-effective and low-carbon solutions for each building independently.

### When to Use
- Designing building-level energy systems
- Comparing retrofit options for existing buildings
- Finding optimal technology combinations
- Supporting building-level investment decisions
- When district systems are not feasible

### What It Optimises

**Decision Variables**:
- Heating system type and capacity (boiler, heat pump, etc.)
- Cooling system type and capacity (chiller, heat pump, etc.)
- DHW system configuration
- PV system size and placement
- Solar thermal system size
- Battery storage size (optional)
- Thermal storage size (optional)

**Objectives**:
1. **Minimize total annualised cost** (CAPEX + OPEX)
2. **Minimize GHG emissions** (operational)
3. **Minimize primary energy consumption**

### Prerequisites
- **Energy Demand Part 2** - Building energy loads required
- **Renewable energy assessments** (optional but recommended):
  - PV potential
  - Solar thermal potential
  - Geothermal potential

### Required Input Files
- Total demand summary (building loads)
- Cost and emission databases
- Technology databases
- Renewable energy potential files (if available)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Optimisation algorithm** | NSGA-II or other | NSGA-II |
| **Population size** | Number of solutions per generation | 100-200 |
| **Number of generations** | Iterations | 50-100 |
| **Allow heat pumps** | Include HP in technology options | Yes |
| **Allow boilers** | Include boilers | Yes |
| **Allow solar** | Include solar technologies | Yes |
| **Allow storage** | Include thermal/battery storage | Optional |
| **Multiprocessing** | Parallel evaluation | Enabled |

### How to Use

1. **Complete prerequisites**:
   - ✅ Energy Demand Part 2
   - ✅ (Optional) Renewable energy assessments

2. **Configure optimisation**:
   - Navigate to **Energy Supply System Optimisation**
   - Select **Supply System Optimisation: Building-Scale**
   - Enable desired technology options
   - Set population size and generations
   - Enable multiprocessing (strongly recommended)

3. **Run optimisation**:
   - Click **Run**
   - **Processing time**: 30 minutes to 4 hours depending on:
     - Number of buildings
     - Population size × generations
     - Technology options enabled
     - CPU cores available

### Output Files

**Pareto optimal solutions**: `{scenario}/outputs/data/optimization/decentralized/pareto_solutions.csv`
- Non-dominated solutions (cost-emission trade-offs)
- Technology configurations for each solution
- Costs, emissions, and energy metrics
- System capacities

**Individual building results**: `{scenario}/outputs/data/optimization/decentralized/BXXX_optimal_systems.csv`
- Optimal system configuration for each building
- Equipment sizing (kW)
- Annual costs and emissions
- Energy generation/consumption

**Summary statistics**: `{scenario}/outputs/data/optimization/decentralized/optimization_summary.csv`
- Best solutions by objective
- Min cost solution
- Min emissions solution
- Compromise solutions

### Understanding Results

#### Pareto Frontier
The Pareto frontier shows trade-offs between objectives:
- **Lower-left**: Best solutions (low cost, low emissions)
- **Extreme points**: Single-objective optima (pure cost or pure emissions focus)
- **Middle**: Balanced compromise solutions

Typical findings:
- **Min cost**: Often gas boiler + some PV
- **Min emissions**: Heat pump + large PV + storage
- **Compromise**: Heat pump + moderate PV

#### Technology Selection Patterns

**Cost-optimal systems** typically include:
- Gas/oil boilers (if gas is cheap)
- Air-source heat pumps (moderate climates)
- Minimal renewable energy
- Small or no storage

**Emissions-optimal systems** typically include:
- Heat pumps (all-electric)
- Maximum feasible PV
- Thermal and/or battery storage
- Solar thermal for DHW

### Tips
- **Start with smaller population/generations** for testing (e.g., 50×25)
- **Increase for final results** (e.g., 200×100 for publication)
- **Enable multiprocessing**: Reduces time from days to hours
- **Constrain technologies** if some are not feasible at your site
- **Review multiple Pareto solutions**: Understand trade-off space

### Troubleshooting

**Issue**: Optimisation runs very slowly
- **Solution**: Reduce population size or generations for testing
- **Solution**: Enable multiprocessing
- **Solution**: Reduce number of technology options

**Issue**: No feasible solutions found
- **Solution**: Relax constraints (e.g., allow more technology types)
- **Solution**: Check demand data is valid
- **Solution**: Verify cost/performance databases

**Issue**: All solutions look similar
- **Solution**: Increase population diversity (larger population)
- **Solution**: Run for more generations
- **Solution**: Expand technology options

---

## Supply System Optimisation: District-Scale

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
1. **Minimize total system cost** (CAPEX + OPEX + network)
2. **Minimize total GHG emissions**
3. **Minimize primary energy consumption**

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
| **Optimisation algorithm** | Evolutionary algorithm | NSGA-II or similar |
| **Population size** | Solutions per generation | 100-300 |
| **Number of generations** | Optimization iterations | 50-150 |
| **Allow district heating** | Include DH network option | Optional |
| **Allow district cooling** | Include DC network option | Optional |
| **Allow CHP** | Include combined heat & power | Optional |
| **Allow thermal storage** | Include storage at plant | Yes |
| **Network layout** | Use existing or optimise | From Part 1 or optimise |
| **Multiprocessing** | Parallel evaluation | Enabled |

### How to Use

1. **Complete prerequisites**:
   - ✅ Energy Demand Part 2 for all buildings
   - ✅ Streets network
   - ✅ (Optional) Thermal Network Part 1

2. **Configure optimisation**:
   - Navigate to **Energy Supply System Optimisation**
   - Select **Supply System Optimisation: District-Scale**
   - Enable desired system options (DH, DC, CHP, storage, etc.)
   - Set population and generation parameters
   - Configure multiprocessing

3. **Run optimisation**:
   - Click **Run**
   - **Processing time**: 2-24+ hours depending on:
     - District size (number of buildings)
     - Complexity (network + technologies)
     - Population × generations
     - Available CPU cores
   - Consider running overnight or on high-performance computer

### Output Files

**Pareto frontier**: `{scenario}/outputs/data/optimization-new/pareto_optimal_solutions.csv`
- Non-dominated system configurations
- Cost, emissions, and energy for each solution
- Network configurations
- Plant capacities and locations

**Optimal system configurations**: `{scenario}/outputs/data/optimization-new/optimal_supply_systems_summary.csv`
- Detailed technology mix for each Pareto solution
- Equipment types and capacities
- Network characteristics
- Annual performance metrics

**Building connections**: `{scenario}/outputs/data/optimization-new/building_connections.csv`
- Which buildings connect to district systems (per solution)
- Substation sizing
- Connection costs

**Hourly operation** (for selected solutions): `{scenario}/outputs/data/optimization-new/hourly_operation/`
- Plant dispatch schedules
- Storage operation
- Network flows
- Import/export profiles

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

### Parameter Selection
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
- **[Life Cycle Analysis](06-life-cycle-analysis.md)** - Detailed cost and emission calculations
- **[Visualisation](10-visualisation.md)** - Plot Pareto frontiers

---

[← Back: Life Cycle Analysis](06-life-cycle-analysis.md) | [Back to Index](index.md) | [Next: Data Management →](08-data-management.md)
