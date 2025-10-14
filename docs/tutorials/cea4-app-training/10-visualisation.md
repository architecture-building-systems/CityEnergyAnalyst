# Visualisation

Visualisation features create charts and plots to present CEA results. These tools generate publication-quality graphics for energy demand, emissions, solar potential, comfort analysis, and optimisation results.

---

## Plot - Building Energy Demand

### Overview
Creates bar charts of building energy demand results, showing heating, cooling, electricity, and hot water demand for selected buildings. This is the primary visualisation for energy demand forecasting results.

### When to Use
- After completing [Energy Demand Part 2](04-demand-forecasting.md)
- Presenting building energy performance
- Comparing energy demand across buildings
- Supporting energy reports and presentations

### What It Plots

**Energy Services**:
- Space heating (Qhs)
- Space cooling (Qcs)
- Electricity (E) - appliances, lighting, auxiliaries
- Domestic hot water (Qww)

**Chart Types Available**:
1. **Annual demand** - Total MWh/year per building (stacked bar)
2. **Energy intensity** - kWh/m²/year per building (normalised)
3. **Peak loads** - Maximum kW per building
4. **Time series** - Hourly demand profiles (line charts)
5. **Monthly aggregation** - Seasonal patterns

### Prerequisites
- **Energy Demand Part 2** completed
- Total demand file exists

### Key Parameters

| Parameter | Description | Options |
|-----------|-------------|---------|
| **Chart type** | Type of visualisation | Annual / Intensity / Peaks / Time series / Monthly |
| **Building filter** | Which buildings to include | All / Selected / By type |
| **Energy services** | Which services to show | All / Heating / Cooling / Electricity |
| **Stacked vs grouped** | Bar chart style | Stacked (default) / Grouped |

### How to Use

1. **Complete Energy Demand Part 2**

2. **Run plot generation**:
   - Navigate to **Visualisation**
   - Select **Plot - Building Energy Demand**
   - Choose chart type (start with "Annual demand")
   - Select buildings (or use "All")
   - Choose whether to stack or group energy services
   - Click **Run**

3. **View results**:
   - Charts saved to `{scenario}/outputs/plots/demand/`
   - Interactive HTML plots (open in browser)
   - Static PNG/PDF (for presentations)

### Chart Interpretation

**Annual Demand Bar Chart**:
- Height = total energy (MWh/year)
- Colors = energy services (heating, cooling, electricity, DHW)
- Taller bars = higher energy consumers
- Color distribution shows energy mix

**Energy Intensity**:
- Normalises by floor area (kWh/m²/year)
- Allows comparison regardless of building size
- Typical ranges:
  - Low-energy buildings: 50-100 kWh/m²/year total
  - Standard buildings: 100-200 kWh/m²/year
  - Old/inefficient: >200 kWh/m²/year

**Time Series**:
- Shows hourly variation over year
- Identify peak demand periods
- Assess load diversity
- Support system sizing

### Customisation Options

- **Colors**: Customise color scheme for energy services
- **Sorting**: Sort buildings by total demand, name, or type
- **Labels**: Show/hide data labels on bars
- **Legend**: Position and format
- **Export format**: HTML (interactive), PNG, PDF, SVG

### Tips
- **Start with annual demand**: Best overview of results
- **Use intensity for comparisons**: Fairer comparison across building sizes
- **Filter by type**: Group similar buildings for clearer insights
- **Time series for validation**: Check if patterns make sense

### Troubleshooting

**Issue**: No plots generated
- **Solution**: Ensure Energy Demand Part 2 completed successfully
- **Solution**: Check Total_demand.csv exists

**Issue**: Charts show unexpected values
- **Solution**: Validate demand calculation results first
- **Solution**: Check units (MWh vs kWh)

---

## Plot - Lifecycle Emissions

### Overview
Creates bar charts showing total lifecycle emissions (embodied + operational) for buildings. Visualises both construction impacts and energy use emissions.

### When to Use
- After running [Emissions analysis](06-life-cycle-analysis.md#emissions)
- Presenting carbon footprint assessments
- Comparing building environmental performance
- Supporting net-zero carbon strategies

### What It Plots

**Emission Sources**:
- Embodied emissions (construction, materials, end-of-life)
- Operational emissions (heating, cooling, electricity, DHW)
- Biogenic carbon (negative emissions from timber storage)
- PV production emissions (if applicable)

**Chart Types**:
1. **Annual total emissions** - kgCO₂-eq/year
2. **Emissions intensity** - kgCO₂-eq/m²/year
3. **Lifecycle cumulative** - Total over analysis period
4. **Emissions breakdown** - By source (embodied vs operational)

### Prerequisites
- [Emissions analysis](06-life-cycle-analysis.md#emissions) completed

### How to Use

1. **Complete Emissions calculation**

2. **Generate plots**:
   - Navigate to **Visualisation**
   - Select **Plot - Lifecycle Emissions**
   - Choose chart type
   - Select buildings
   - Click **Run**

3. **Outputs**: `{scenario}/outputs/plots/emissions/lifecycle/`

### Chart Interpretation

**Embodied vs Operational**:
- Stacked bars show split between construction and operation
- New buildings: Often 30-50% embodied over 50 years
- Retrofits: Lower embodied fraction
- Passive/net-zero: Can be >60% embodied

**Negative Emissions**:
- Timber buildings may show negative embodied emissions
- Biogenic carbon storage exceeds manufacturing emissions
- Consider temporary storage (released at end-of-life)

### Tips
- **Present both totals and intensity**: Different audiences prefer different metrics
- **Show time horizon**: Lifecycle depends on analysis period
- **Highlight trade-offs**: Low operational may mean high embodied

---

## Plot - Emission Timeline

### Overview
Visualises how emissions evolve over time, tracking cumulative lifecycle emissions across different sources. Shows trajectory toward net-zero targets.

### When to Use
- Climate action planning
- Demonstrating path to net-zero
- Understanding emission timing and sources
- Supporting climate policy compliance

### What It Plots

**Emission Sources Over Time**:
- Operational emissions (annual)
- Embodied emissions (construction years)
- Renovation emissions (retrofit years)
- PV embodied (installation year)
- Biogenic sequestration (throughout building life)
- Demolition emissions (end-of-life)

**Visualisation Modes**:
1. **Line plot** - Itemised emission trends by source
2. **Net emissions line** - Overall net emissions with target year
3. **Stacked area** - Total emissions, contribution by source
4. **Percentage stacked** - Relative composition shifts

### Prerequisites
- Emissions analysis with target year projection

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Target year** | Net-zero target | 2050 |
| **Visualisation mode** | Chart style | Line / Area / Percentage |
| **Show cumulative** | Running total vs annual | Cumulative (default) |

### How to Use

1. **Run Emissions with target year** (e.g., 2050)

2. **Generate timeline plot**:
   - Navigate to **Visualisation**
   - Select **Plot - Emission Timeline**
   - Set target year
   - Choose visualisation mode
   - Click **Run**

3. **Outputs**: `{scenario}/outputs/plots/emissions/timeline/`

### Chart Interpretation

**Cumulative Emissions**:
- Shows total accumulated carbon over time
- Initial spike = embodied emissions from construction
- Steady rise = ongoing operational emissions
- Step changes = renovations or system replacements

**Path to Net-Zero**:
- Target line shows required trajectory
- Gap between actual and target = additional action needed
- Identify when net-zero is achieved (if at all)

**Emission Composition**:
- Stacked area shows how sources change over time
- Early: Dominated by embodied
- Long-term: Dominated by operational
- Grid decarbonization = operational decreases over time

### Use Cases

- **Policy compliance**: Demonstrate meeting targets
- **Investment decisions**: Show long-term climate impact
- **Renovation planning**: Timing and impact of interventions

### Tips
- **Include grid decarbonisation**: Model future grid becoming cleaner
- **Show mitigation scenarios**: Compare with/without interventions
- **Use for communication**: Effective stakeholder engagement tool

For detailed examples, see: [IDAida.ch Course](https://platform.idaida.ch/course/view.php?id=41)

---

## Plot - Operational Emissions

### Overview
Plots bar charts of annual operational emissions from energy system operation (heating, cooling, electricity, DHW).

### When to Use
- Focusing on operational carbon (excluding embodied)
- Comparing energy system alternatives
- Supporting system selection decisions

### What It Plots

**Operational Emission Sources**:
- Heating system emissions
- Cooling system emissions
- Electricity emissions
- DHW system emissions

Breakdown by:
- Energy carrier (gas, electricity, district heating, etc.)
- Building
- Time period (annual, monthly, hourly if available)

### Prerequisites
- Emissions analysis completed

### How to Use

1. Complete Emissions calculation
2. Navigate to **Visualisation** → **Plot - Operational Emissions**
3. Select chart type and buildings
4. Run

### Chart Types

- **Annual operational emissions** (kgCO₂-eq/year)
- **Emissions by energy carrier**
- **Monthly operational emissions**

### Tips
- **Compare to embodied**: Use with Lifecycle Emissions plot
- **Assess system changes**: Show impact of fuel switching
- **Monthly patterns**: Identify seasonal effects

---

## Plot - Solar Technology

### Overview
Creates bar charts of solar energy technology potential (PV, PVT, solar collectors), showing electricity and heat generation capacity for buildings.

### When to Use
- After running [renewable energy assessments](03-renewable-energy.md)
- Presenting solar potential results
- Supporting solar investment decisions
- Comparing solar technologies

### What It Plots

**Solar Technologies**:
- PV: Electricity generation (MWh/year, kWp capacity)
- PVT: Electricity + heat generation
- Solar collectors: Heat generation (MWh/year)

**Chart Types**:
1. **Annual generation** - Total MWh/year by technology
2. **Installed capacity** - kWp (PV/PVT) or m² (SC)
3. **Technology comparison** - PV vs PVT vs SC side-by-side
4. **Specific yield** - kWh/kWp/year or kWh/m²/year

### Prerequisites
- At least one solar technology assessment completed:
  - [Photovoltaic Panels](03-renewable-energy.md#photovoltaic-pv-panels)
  - [PVT Panels](03-renewable-energy.md#photovoltaic-thermal-pvt-panels)
  - [Solar Collectors](03-renewable-energy.md#solar-collectors-sc)

### How to Use

1. **Complete solar assessments** (PV, PVT, and/or SC)

2. **Generate plots**:
   - Navigate to **Visualisation**
   - Select **Plot - Solar Technology**
   - Choose technologies to include
   - Select chart type
   - Click **Run**

3. **Outputs**: `{scenario}/outputs/plots/solar/`

### Chart Interpretation

**Annual Generation**:
- Compares total output by technology
- PV: Electricity only
- PVT: Electricity + heat (show both)
- SC: Heat only

**Comparison Across Buildings**:
- Identifies buildings with best solar potential
- Accounts for shading, orientation, available area

**Technology Trade-offs**:
- PV: Maximum electricity, no heat
- PVT: Balanced electricity + heat, lower electrical efficiency
- SC: Maximum heat, no electricity

### Tips
- **Normalise by area**: Use kWh/m² for fair comparison
- **Show both capacity and yield**: Capacity = size, yield = performance
- **Highlight best performers**: Identify buildings for priority installation

---

## Plot - Building Comfort Chart

### Overview
Plots comfort and discomfort hours for buildings based on thermal comfort analysis from energy demand calculations. Shows when indoor conditions meet or fail to meet comfort criteria.

### When to Use
- After Energy Demand calculation
- Assessing indoor environmental quality
- Evaluating HVAC system performance
- Supporting comfort-based design decisions

### What It Plots

**Comfort Metrics**:
- Total comfort hours (hours/year within setpoint ranges)
- Discomfort hours (hours/year outside ranges)
  - Too hot
  - Too cold
- By building and by zone (if multi-zone)

**Comfort Standards**:
- Based on setpoints in `comfort.xlsx`
- Typically ASHRAE 55 or EN 15251 criteria
- Adaptive comfort models (if configured)

### Prerequisites
- Energy Demand Part 2 completed
- Comfort setpoints defined in `comfort.xlsx`

### How to Use

1. Complete Energy Demand calculation

2. Generate comfort plots:
   - Navigate to **Visualisation**
   - Select **Plot - Building Comfort Chart**
   - Select buildings
   - Click **Run**

3. **Outputs**: `{scenario}/outputs/plots/comfort/`

### Chart Types

**Annual Comfort Hours**:
- Stacked bar showing comfort/discomfort split
- Goal: Minimise discomfort hours

**Discomfort Breakdown**:
- Too hot vs too cold
- Seasonal patterns

**Comfort vs Outdoor Temperature**:
- Scatter plots showing indoor-outdoor relationship

### Interpretation

**Acceptable Discomfort**:
- Category I (best): <10% discomfort (< 876 hours)
- Category II (standard): 10-20% discomfort (876-1,752 hours)
- Category III (acceptable): 20-30% discomfort (1,752-2,628 hours)
- >30% discomfort: Unacceptable

**Typical Patterns**:
- Free-running buildings: More discomfort but acceptable
- Fully conditioned: Minimal discomfort, high energy use
- Balance: Moderate comfort, moderate energy

### Tips
- **Compare comfort vs energy**: High comfort often means high energy
- **Seasonal analysis**: Identify summer overheating or winter underheating
- **Validate HVAC sizing**: Excessive discomfort suggests undersized systems

---

## Plot - Pareto Front

### Overview
Plots Pareto frontiers from optimisation results, visualising trade-offs between competing objectives (cost, emissions, energy).

### When to Use
- After running [Supply System Optimisation](07-supply-optimisation.md)
- Presenting optimisation results
- Supporting multi-objective decision-making
- Showing cost-carbon trade-offs

### What It Plots

**Optimisation Objectives**:
- Typically 2D or 3D scatter plots
- X-axis: Total annualised cost (CHF/year or $/year)
- Y-axis: Total GHG emissions (kgCO₂-eq/year)
- Optionally Z-axis: Primary energy (MWh/year)

**Points on Chart**:
- **Pareto optimal solutions**: Non-dominated solutions (on frontier)
- **Dominated solutions**: Worse on all objectives (not shown or greyed)
- **Reference solutions**: Baseline, current state

### Prerequisites
- Building-scale or District-scale optimisation completed

### Key Parameters

| Parameter | Description | Options |
|-----------|-------------|---------|
| **Objectives to plot** | Which objectives on axes | Cost vs Emissions (default) / Cost vs Energy / 3D |
| **Highlight solutions** | Mark specific solutions | Min cost / Min emissions / Compromise |
| **Reference point** | Show baseline | Current system / No optimisation |

### How to Use

1. **Complete optimisation** (building or district scale)

2. **Generate Pareto plot**:
   - Navigate to **Visualisation**
   - Select **Plot - Pareto Front**
   - Choose objectives for axes
   - Optionally highlight key solutions
   - Click **Run**

3. **Outputs**: `{scenario}/outputs/plots/optimization/pareto_front/`

### Chart Interpretation

**Pareto Frontier**:
- Lower-left corner: Best solutions (low cost, low emissions)
- Horizontal movement: Cost changes with minimal emission change
- Vertical movement: Emission changes with minimal cost change
- No solution dominates another on frontier

**Key Points on Frontier**:
1. **Min cost solution**: Cheapest option (often high emissions)
2. **Min emissions solution**: Cleanest option (often expensive)
3. **Knee point**: Best compromise (balanced cost and emissions)

**Decision Making**:
- Choose solution based on priorities (budget, climate goals)
- Trade-off rate: EUR per ton CO₂ saved
- Carbon price implications

### Customisation

- **Color by technology**: Show which technologies appear in solutions
- **Size by objective**: Third objective as marker size
- **Annotate**: Label key solutions

### Tips
- **Show current state**: Add reference point for context
- **Calculate trade-off rate**: Cost increase per ton CO₂ reduction
- **Interactive plots**: HTML allows hovering to see solution details
- **Multiple scenarios**: Overlay Pareto fronts to compare

---

## Common Visualisation Workflow

### Standard Visualisation Sequence

After completing CEA analyses:

1. **Energy Demand Plots**:
   - Plot - Building Energy Demand (annual and intensity)
   - Validate results before proceeding

2. **Emissions Plots**:
   - Plot - Lifecycle Emissions (understand carbon footprint)
   - Plot - Emission Timeline (show path to net-zero)
   - Plot - Operational Emissions (focus on system performance)

3. **Renewable Energy Plots**:
   - Plot - Solar Technology (if solar assessments done)

4. **Comfort Plots** (optional):
   - Plot - Building Comfort Chart (verify thermal comfort)

5. **Optimisation Plots** (if optimisation done):
   - Plot - Pareto Front (show trade-offs and optimal solutions)

### Creating Presentation Packages

**For Reports**:
- Export as PNG or PDF (300 dpi)
- Use consistent color schemes
- Include data tables with charts

**For Presentations**:
- Export as SVG for scaling
- Use interactive HTML for workshops
- Highlight key findings with annotations

**For Publications**:
- Export vector formats (SVG, PDF)
- Follow journal style guidelines
- Provide source data

---

## Visualisation Best Practices

### Chart Design
- **Clear titles**: Describe what is shown
- **Axis labels**: Include units
- **Legend**: Essential for multi-series charts
- **Colors**: Use colorblind-friendly palettes
- **Annotations**: Highlight key findings

### Data Presentation
- **Normalise when comparing**: Use intensity (per m² or per capita)
- **Sort logically**: By value, name, or type
- **Filter for clarity**: Don't show too many buildings (>20 becomes cluttered)
- **Aggregate when needed**: Group by building type if many buildings

### Storytelling with Charts
1. **Start with overview**: Total demand, total emissions
2. **Break down by component**: Which services dominate?
3. **Compare across buildings**: Identify outliers and patterns
4. **Show time dimension**: How do patterns vary over time?
5. **Present solutions**: If optimisation done, show improvements

---

## Customising Plots

### Configuration Files
Advanced users can customise plot appearance via configuration files:
- Color schemes
- Chart dimensions
- Font sizes
- Export formats

See CEA documentation for details on plot configuration.

### Post-Processing
For publication-quality figures:
1. Export as SVG
2. Edit in Inkscape or Adobe Illustrator
3. Adjust fonts, colors, labels as needed
4. Export to required format

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides demand data
- **[Life Cycle Analysis](06-life-cycle-analysis.md)** - Provides emissions data
- **[Renewable Energy](03-renewable-energy.md)** - Provides solar generation data
- **[Supply System Optimisation](07-supply-optimisation.md)** - Provides Pareto frontier data
- **[Export Results to CSV](01-import-export.md#export-results-to-csv)** - Export data for custom plots

---

[← Back: Utilities](09-utilities.md) | [Back to Index](index.md)
