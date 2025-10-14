# Life Cycle Analysis

Life cycle analysis features assess the environmental impacts and costs of building energy systems throughout their lifecycle, including embodied impacts from construction and operational impacts from energy use.

---

## Emissions

### Overview
Calculates aggregated embodied and operational greenhouse gas emissions for each building. The feature provides both total lifecycle emissions and detailed breakdowns by source, with options for hourly operational emissions and projected annual embodied emissions until a target year.

### What It Calculates

**Embodied Emissions** (kgCO₂-eq):
- Initial construction materials and processes
- Building envelope (walls, roof, floor, windows)
- Renovation and retrofit emissions
- Deconstruction and end-of-life
- Biogenic carbon storage (negative emissions from timber, etc.)
- PV panel manufacturing (if installed)

**Operational Emissions** (kgCO₂-eq):
- Energy supply system operation
- Heating, cooling, electricity, DHW
- Hourly timesteps available (8,760 hours)
- Grid emission factors or custom factors
- System-specific conversion efficiencies

### When to Use
- Assessing building or district carbon footprints
- Comparing design alternatives for climate impact
- Supporting net-zero carbon targets
- Regulatory compliance and certification
- Climate action planning

### Prerequisites
- **Energy Demand Part 2** - For operational emissions
- Solar radiation data - For PV-related embodied emissions
- Zone geometry and building properties

### Required Input Files
- Total demand summary
- Individual building demand files (for hourly operational)
- Building architecture (for embodied emissions)
- Building supply systems configuration
- Zone geometry
- Weather file
- Envelope databases (walls, roofs, windows, floors)
- Radiation data (for PV panels)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Target year for embodied emissions** | Future year for projection | 2050 |
| **Include hourly operational** | Generate 8,760 hourly emissions | Optional |
| **Embodied emission factors** | LCA database to use | KBOB / ICE / Custom |
| **Operational emission factors** | Grid carbon intensity | From database or custom |

### How to Use

1. **Complete prerequisites**:
   - ✅ Energy Demand Part 2
   - ✅ Solar Radiation (if PV installed)
   - ✅ Building properties assigned

2. **Run emissions analysis**:
   - Navigate to **Life Cycle Analysis**
   - Select **Emissions**
   - Set target year (e.g., 2050 for net-zero planning)
   - Optionally enable hourly operational emissions
   - Click **Run**

3. **Processing time**: 5-15 minutes for typical districts

### Output Files

**Annual emissions per building**: `{scenario}/outputs/data/emissions/Total_yearly_emissions_by_building.csv`
- Operational emissions by energy carrier (electricity, gas, etc.)
- Embodied emissions by component (envelope, systems, etc.)
- Total annual emissions (kgCO₂-eq/year)
- Emissions intensity (kgCO₂-eq/m²/year)

**Hourly operational emissions** (if enabled): `{scenario}/outputs/data/emissions/BXXX_hourly_operational.csv`
- 8,760 hourly emissions values
- Breakdown by energy service
- Useful for temporal analysis

**Projected annual embodied**: `{scenario}/outputs/data/emissions/projected_annual_embodied.csv`
- Annual embodied emissions until target year
- Accounts for renovations, PV installation, deconstruction
- Cumulative emissions over time

**Lifecycle summary**: `{scenario}/outputs/data/emissions/lifecycle_emissions_summary.csv`
- Total lifecycle emissions per building
- Embodied vs operational breakdown
- Net emissions (including biogenic sequestration)

### Understanding Results

#### Typical Emissions Breakdown

**Embodied Emissions** (varies significantly by building type):
- New construction: 300-800 kgCO₂-eq/m² GFA
- Timber buildings: Lower (200-500 kgCO₂-eq/m²) due to carbon storage
- Concrete/steel buildings: Higher (500-1,000 kgCO₂-eq/m²)
- Renovations add: 50-200 kgCO₂-eq/m²

**Operational Emissions** (annual):
- Low-energy buildings: 5-15 kgCO₂-eq/m²/year
- Standard buildings: 15-40 kgCO₂-eq/m²/year
- Old buildings: 40-80+ kgCO₂-eq/m²/year

#### Emission Sources

**Major embodied emission sources**:
1. Concrete and cement (30-50% of total)
2. Steel and metals (15-30%)
3. Insulation materials (5-15%)
4. Windows and glazing (5-10%)

**Major operational emission sources**:
1. Space heating (40-60% in cold climates)
2. Electricity (20-40%)
3. Domestic hot water (10-20%)
4. Space cooling (5-15% in warm climates)

### Interpreting Results

**Embodied vs Operational Ratio**:
- New low-energy buildings: ~60% embodied, ~40% operational (over 50 years)
- Existing buildings: ~20% embodied, ~80% operational
- Passive/net-zero buildings: Can be >70% embodied

**Time to "pay back" embodied emissions**:
- Deep energy retrofits: 10-30 years
- New construction vs existing: Often not paid back
- PV installation: 2-5 years typically

### Tips
- **Include biogenic carbon**: Timber structures can have negative net embodied emissions
- **Consider operational carbon first**: Usually the dominant source for existing buildings
- **Grid decarbonisation matters**: Operational emissions decrease as grid gets cleaner
- **Embodied matters for new/renovations**: New construction embodied emissions are significant

### Troubleshooting

**Issue**: Very high embodied emissions
- **Solution**: Check material quantities in architecture file are realistic
- **Solution**: Verify emission factors in database

**Issue**: Zero operational emissions
- **Solution**: Ensure energy demand calculation completed
- **Solution**: Check supply systems are defined

**Issue**: Missing biogenic carbon values
- **Solution**: Verify timber content is specified in architecture file
- **Solution**: Check LCA database includes biogenic factors

---

## Energy Supply System Costs

### Overview
Calculates the capital (CAPEX) and operational (OPEX) costs for building energy supply systems. This feature provides economic analysis of energy systems including equipment costs, installation, maintenance, and energy costs.

### What It Calculates

**Capital Costs (CAPEX)**:
- Equipment purchase (boilers, chillers, heat pumps, etc.)
- Installation and commissioning
- Connection fees (grid, district heating, etc.)
- PV system costs (if installed)
- Energy storage systems

**Operational Costs (OPEX)**:
- Annual energy costs (electricity, gas, district heating, etc.)
- Maintenance and servicing
- System replacement costs (amortised)
- Grid connection fees
- Carbon taxes (if applicable)

**Economic Metrics**:
- Total cost of ownership
- Levelised cost of energy (LCOE)
- Simple payback periods
- Net present value (NPV)

### When to Use
- Economic comparison of supply system alternatives
- Business case development
- Investment planning
- Comparing centralised vs decentralised systems
- Supporting supply system optimisation

### Prerequisites
- **Energy Demand Part 2** - For energy consumption
- Building supply systems defined

### Required Input Files
- Total demand summary
- Building supply systems configuration
- Cost databases (equipment, energy prices, etc.)

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Discount rate** | For NPV calculation | 3-6% |
| **Analysis period** | Years for lifecycle cost | 20-30 years |
| **Energy price escalation** | Annual increase in energy prices | 2-3% |
| **Carbon tax** | If applicable | Region-specific |

### How to Use

1. **Complete energy demand** calculation

2. **Verify supply systems** are defined in `supply_systems.xlsx`

3. **Run cost analysis**:
   - Navigate to **Life Cycle Analysis**
   - Select **Energy Supply System Costs**
   - Review/adjust economic parameters
   - Click **Run**

### Output Files

**System costs summary**: `{scenario}/outputs/data/costs/system_costs_summary.csv`
- CAPEX per building and system type
- Annual OPEX per building
- Total lifecycle costs
- Cost intensity (CHF/m² or $/m²)

**Detailed breakdown**: `{scenario}/outputs/data/costs/system_costs_detailed.csv`
- Cost breakdown by component
- Equipment sizing and costs
- Energy costs by carrier

### Understanding Results

#### Typical Cost Ranges

**CAPEX (per kW capacity)**:
- Gas boiler: 200-400 CHF/kW
- Heat pump: 800-1,500 CHF/kW
- PV system: 1,500-2,500 CHF/kWp
- District heating connection: 15,000-50,000 CHF/building

**OPEX (annual per m² GFA)**:
- Energy costs: 10-40 CHF/m²/year
- Maintenance: 2-5 CHF/m²/year
- Total: 15-50 CHF/m²/year

**Lifecycle Costs (20 years, per m² GFA)**:
- Standard heating: 300-600 CHF/m²
- Heat pump systems: 250-500 CHF/m²
- District heating: 300-550 CHF/m²

### Economic Analysis

**CAPEX vs OPEX Trade-off**:
- Efficient systems: Higher CAPEX, lower OPEX
- Simple systems: Lower CAPEX, higher OPEX
- Optimal choice depends on discount rate and time horizon

**Sensitivity Factors**:
- Energy price escalation (major impact on OPEX)
- Equipment lifetime assumptions
- Maintenance cost assumptions
- Discount rate (affects NPV significantly)

### Tips
- **Use realistic energy prices**: Include all fees, taxes, grid charges
- **Consider incentives**: Subtract subsidies from CAPEX
- **Account for replacement**: Major equipment has 15-25 year lifespan
- **Sensitivity analysis**: Test different energy price scenarios

### Troubleshooting

**Issue**: Costs seem too low or too high
- **Solution**: Check cost database is appropriate for your region
- **Solution**: Verify currency and units

**Issue**: Missing cost data for some systems
- **Solution**: Update cost database with local costs
- **Solution**: Provide custom cost factors

---

## Combined LCA Workflow

### Complete Environmental and Economic Assessment

1. **Run both features**:
   - Emissions (for carbon footprint)
   - Energy Supply System Costs (for economic analysis)

2. **Export results**: Use [Export Results to CSV](01-import-export.md#export-results-to-csv)

3. **Create comparison matrix**:
   - Scenario A vs B on emissions
   - Scenario A vs B on costs
   - Pareto frontier: cost vs carbon trade-offs

4. **Visualise**:
   - Use [Visualisation tools](10-visualisation.md) to plot results
   - Create cost-carbon plots
   - Show lifecycle timelines

### Decision Support

Combine emissions and cost data for multi-criteria decision making:
- **Low carbon, low cost**: Ideal solutions
- **Low carbon, high cost**: May need subsidies or carbon pricing
- **High carbon, low cost**: Economically attractive but environmentally poor
- **High carbon, high cost**: Should be avoided

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides operational energy (prerequisite)
- **[Renewable Energy Assessment](03-renewable-energy.md)** - PV affects both emissions and costs
- **[Supply System Optimisation](07-supply-optimisation.md)** - Uses LCA results for multi-objective optimisation
- **[Visualisation](10-visualisation.md)** - Plot emissions and cost results

---

[← Back: Thermal Network](05-thermal-network.md) | [Back to Index](index.md) | [Next: Supply System Optimisation →](07-supply-optimisation.md)
