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

**Views Available** (via X to plot, Y normalised by and Plot type):
1. **Per building** - Totals per building, stacked or grouped by service
2. **Energy intensity** - Normalised by gross or conditioned floor area
3. **Faceted** - By months, seasons, construction type, or main use type
4. **District time series** - Hourly, daily, monthly, seasonal, or annual totals

### Prerequisites
- **Energy Demand Part 2** completed
- Total demand file exists

### Key Parameters

| Parameter | Description | Options |
|-----------|-------------|---------|
| **Y metric to plot** | End-use services to show | electricity / space_heating / space_cooling / domestic_hot_water |
| **Y metric unit** | Unit | MWh / kWh (default) / Wh |
| **Y normalised by** | Normalisation | no_normalisation / gross_floor_area (default) / conditioned_floor_area |
| **X to plot** | X-axis grouping | building (default), faceted by months, seasons, construction type, etc. |
| **Plot type** | Bar chart style | bar_plot_stack (default) / bar_plot_group / bar_plot_stack_percentage |
| **Buildings** and building filters | Which buildings to include | All, or filter by year, construction type, use type |

### How to Use

1. **Complete Energy Demand Part 2**

2. **Run plot generation**:
   - Navigate to **Visualisation**
   - Select **Plot - Building Energy Demand**
   - Choose services (Y metric to plot), unit and normalisation
   - Choose the X-axis grouping (start with `building`)
   - Select buildings (or leave blank for all)
   - Choose plot type (stacked, grouped, or stacked percentage)
   - Click **Run**

3. **View results**:
   - The interactive chart is shown in the app (not saved to the scenario folder)
   - Hover for values; zoom, pan, or download a PNG from the chart toolbar

### Chart Interpretation

**Annual Demand Bar Chart**:
- Height = total energy (MWh/year)
- Colours = energy services (heating, cooling, electricity, DHW)
- Taller bars = higher energy consumers
- Colour distribution shows energy mix

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

- **Colours**: Customise colour scheme for energy services
- **Sorting**: Sort buildings by total demand, name, or type
- **Labels**: Show/hide data labels on bars
- **Legend**: Position and format
- **Export**: Plots are interactive HTML in the app; download a PNG from the chart toolbar. HTML files are only written when you export a canvas archive

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

## Plot - Energy by Carrier

See [Final Energy > Plot - Energy by Carrier](06-1-final-energy.md#plot---energy-by-carrier) for full documentation.

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

## Plot - System Cost Sankey

See [System Costs > Plot - System Cost Sankey](06-3-system-costs.md#plot---system-cost-sankey) for full documentation.

Sankey diagram showing cost flows from components through services to total costs, with annualised or total CAPEX views.

---

## Plot - Anthropogenic Heat Rejection

See [Heat Rejection > Plot - Anthropogenic Heat Rejection](06-4-heat-rejection.md#plot---anthropogenic-heat-rejection) for full documentation.

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

**Views**:
1. **By surface** - Roofs and north/east/south/west walls (Y metric to plot)
2. **Normalised** - Per gross floor area or per installed panel area of each surface
3. **Per building or district time series** - Via X to plot

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
   - Choose surfaces (Y metric to plot), unit and normalisation
   - Choose the X-axis grouping
   - Click **Run**

3. **Output**: The interactive chart is shown in the app (not saved to the scenario folder). See [Saving and Sharing Plots](#saving-and-sharing-plots).

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
- Based on setpoints in `indoor_comfort.csv`
- Typically ASHRAE 55 or EN 15251 criteria
- Adaptive comfort models (if configured)

### Prerequisites
- Energy Demand Part 2 completed
- Comfort setpoints defined in `indoor_comfort.csv`

### How to Use

1. Complete Energy Demand calculation

2. Generate comfort plots:
   - Navigate to **Visualisation**
   - Select **Plot - Building Comfort Chart**
   - Select buildings
   - Click **Run**

3. **Output**: The interactive chart is shown in the app (not saved to the scenario folder). See [Saving and Sharing Plots](#saving-and-sharing-plots).

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
- The objective functions selected when the optimisation was run (`cost`, `GHG_emissions`, `system_energy_demand`, `anthropogenic_heat`)
- One 2D scatter plot per pair of objectives
- An additional 3D plot when three objectives were optimised

**Points on Chart**:
- **Pareto optimal solutions**: Non-dominated solutions (on frontier)
- **Dominated solutions**: Worse on all objectives (not shown or greyed)
- **Reference solutions**: Baseline, current state

### Prerequisites
- District Supply System Optimisation completed

### Key Parameters

None besides the scenario. The axes follow the objective functions of the optimisation run.

### How to Use

1. **Complete District Supply System Optimisation**

2. **Generate Pareto plot**:
   - Navigate to **Visualisation**
   - Select **Plot - Pareto Front**
   - Click **Run**

3. **Output**: The interactive chart is shown in the app (not saved to the scenario folder). See [Saving and Sharing Plots](#saving-and-sharing-plots).

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

- **Colour by technology**: Show which technologies appear in solutions
- **Size by objective**: Third objective as marker size
- **Annotate**: Label key solutions

### Tips
- **Show current state**: Add reference point for context
- **Calculate trade-off rate**: Cost increase per ton CO₂ reduction
- **Interactive plots**: Hover over the plot to see solution details
- **Multiple scenarios**: Overlay Pareto fronts to compare

---

## Plot - Pathway Emission Timeline

Cumulative lifecycle emissions for one **district pathway**, across its state years, broken
down by source. The pathway equivalent of Plot - Emission Timeline.

Requires a pathway with simulated states — see
[District Evolution Pathways](11-district-pathways.md).

---

## Plot - Cost Breakdown

Cost breakdown for energy supply systems. Supports both **baseline costs** and **what-if
scenario costs**, so it can be used before or after a what-if has been defined.

See [LCA Part 2b: Costs](06-3-system-costs.md) for the underlying results.

---

## Plot - Energy Flow Sankey

Annual energy flows for a what-if scenario as a Sankey diagram, running from energy carrier
through conversion to end use. Use it to see where carriers enter the district and what they
ultimately serve.

See [LCA Part 1: Energy by Carrier](06-1-final-energy.md) for the underlying results.

---

## Plot - Load Duration Curve by Component

One load duration curve per selected supply component — annual hourly loads sorted from
highest to lowest. Reading the curve tells you how a component is actually used: a steep,
short curve indicates peaking duty, a long flat one indicates base load.

Useful for sanity-checking sizing before reading cost results.

See [LCA Part 1: Energy by Carrier](06-1-final-energy.md) for the underlying results.

---

## Plot - Supply System

Plots the components of energy supply systems, showing what the optimisation selected.

See [Energy Supply System Optimisation](07-supply-optimisation.md).

---

## Common Visualisation Workflow

### Standard Visualisation Sequence

After completing CEA analyses:

1. **Energy Demand Plots**:
   - Plot - Building Energy Demand (annual and intensity)
   - Validate results before proceeding

2. **Life Cycle Analysis Plots** (per what-if scenario):
   - [Plot - Energy by Carrier](06-1-final-energy.md#plot---energy-by-carrier) (carrier breakdown)
   - [Plot - Lifecycle Emissions](06-2-emissions.md#plot---lifecycle-emissions) (full lifecycle carbon)
   - [Plot - Emission Timeline](06-2-emissions.md#plot---emission-timeline) (cumulative trajectory)
   - [Plot - Operational Emissions](06-2-emissions.md#plot---operational-emissions) (operational carbon)
   - [Plot - System Cost Sankey](06-3-system-costs.md#plot---system-cost-sankey) (cost flow diagram)
   - [Plot - Anthropogenic Heat Rejection](06-4-heat-rejection.md#plot---anthropogenic-heat-rejection) (waste heat)

3. **Renewable Energy Plots**:
   - Plot - Solar Technology (if solar assessments done)

4. **Comfort Plots** (optional):
   - Plot - Building Comfort Chart (verify thermal comfort)

5. **Optimisation Plots** (if optimisation done):
   - Plot - Pareto Front (show trade-offs and optimal solutions)

### Saving and Sharing Plots

Plots are generated on demand and shown in the app; CEA does not write plot files to the scenario folder. HTML plot files are only produced inside exported canvas archives (`data/<cardId>/plot_<i>.html`).

- **Image**: Hover over a chart and use the camera icon in the chart toolbar to download a PNG
- **Side-by-side views**: Arrange plots and maps in the [Canvas Builder](12-canvas-builder.md)
- **Underlying data**: Use [Export Results to .csv (Summary & Analytics)](01-import-export.md#export-results-to-csv-summary--analytics) to get the numbers behind a chart
- **Publication figures**: CEA has no SVG or PDF export; rebuild the chart from the exported .csv in your own plotting tool

---

## Visualisation Best Practices

### Chart Design
- **Clear titles**: Describe what is shown
- **Axis labels**: Include units
- **Legend**: Essential for multi-series charts
- **Colours**: Use colour-blind-friendly palettes
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

### Plot Parameters
Most bar-chart plot tools expose their appearance settings as parameters: plot title, axis labels, Y-axis range and step, plot type (stacked, grouped, or stacked percentage), X-axis grouping and sorting, and faceting.

### Post-Processing
For publication-quality figures:
1. Export the data with Export Results to .csv (Summary & Analytics)
2. Recreate the chart in your own plotting tool
3. Adjust fonts, colours, and labels as needed

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides demand data
- **[Life Cycle Analysis](06-0-life-cycle-analysis.md)** - Provides emissions data
- **[Renewable Energy](03-renewable-energy.md)** - Provides solar generation data
- **[Supply System Optimisation](07-supply-optimisation.md)** - Provides Pareto frontier data
- **[Export Results to .csv (Summary & Analytics)](01-import-export.md#export-results-to-csv-summary--analytics)** - Export data for custom plots

---

[← Back: Utilities](09-utilities.md) | [Back to Index](index.md) | [Next: District Evolution Pathways →](11-district-pathways.md)
