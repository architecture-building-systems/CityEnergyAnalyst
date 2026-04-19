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

## Plot - Final Energy

See [Final Energy > Plot - Final Energy](06-1-final-energy.md#plot---final-energy) for full documentation.

Bar charts of final energy consumption by carrier (grid, gas, oil, coal, wood) for buildings and plants under a what-if scenario.

---

## Plot - Lifecycle Emissions

See [Emissions > Plot - Lifecycle Emissions](06-2-emissions.md#plot---lifecycle-emissions) for full documentation.

Stacked bar charts showing total lifecycle emissions per building (embodied + operational + biogenic + solar offsets). Title includes the lifecycle year range.

---

## Plot - Emission Timeline

See [Emissions > Plot - Emission Timeline](06-2-emissions.md#plot---emission-timeline) for full documentation.

Cumulative stacked area chart showing how district emissions evolve from construction through demolition.

---

## Plot - Operational Emissions

See [Emissions > Plot - Operational Emissions](06-2-emissions.md#plot---operational-emissions) for full documentation.

Bar charts of operational emissions by service or energy carrier, with solar offset as negative bars.

---

## Plot - Cost Sankey

See [System Costs > Plot - Cost Sankey](06-3-system-costs.md#plot---cost-sankey) for full documentation.

Sankey diagram showing cost flows from components through services to total costs, with annualised or total CAPEX views.

---

## Plot - Heat Rejection

See [Heat Rejection > Plot - Heat Rejection](06-4-heat-rejection.md#plot---heat-rejection) for full documentation.

Bar charts of waste heat rejected to the environment by buildings and district plants.

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
- Y-axis: Total GHG emissions (kgCO₂e/year)
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

3. **Outputs**: `{scenario}/outputs/plots/optimisation/pareto_front/`

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

2. **Life Cycle Analysis Plots** (per what-if scenario):
   - [Plot - Final Energy](06-1-final-energy.md#plot---final-energy) (carrier breakdown)
   - [Plot - Lifecycle Emissions](06-2-emissions.md#plot---lifecycle-emissions) (full lifecycle carbon)
   - [Plot - Emission Timeline](06-2-emissions.md#plot---emission-timeline) (cumulative trajectory)
   - [Plot - Operational Emissions](06-2-emissions.md#plot---operational-emissions) (operational carbon)
   - [Plot - Cost Sankey](06-3-system-costs.md#plot---cost-sankey) (cost flow diagram)
   - [Plot - Heat Rejection](06-4-heat-rejection.md#plot---heat-rejection) (waste heat)

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
- **[Life Cycle Analysis](06-0-life-cycle-analysis.md)** - Provides emissions data
- **[Renewable Energy](03-renewable-energy.md)** - Provides solar generation data
- **[Supply System Optimisation](07-supply-optimisation.md)** - Provides Pareto frontier data
- **[Export Results to CSV](01-import-export.md#export-results-to-csv)** - Export data for custom plots

---

[← Back: Utilities](09-utilities.md) | [Back to Index](index.md)
