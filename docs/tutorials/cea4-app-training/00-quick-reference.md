# Quick Reference Guide

This page provides a complete overview of all 39 features available in the CEA-4 App dashboard.

---

## Import & Export

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Export to Rhino/Grasshopper** | Export CEA files to Rhino/Grasshopper-ready format | Share geometry and results with Rhino/GH workflows |
| **Import from Rhino/Grasshopper** | Import Rhino/Grasshopper-generated files into CEA | Bring externally designed geometry into CEA |
| **Export Results to CSV** | Generate CSV files with CEA results summary and analytics | Create custom reports and perform external analysis |

---

## Solar Radiation Analysis

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Building Solar Radiation using DAYSIM** | Perform solar radiation analysis using DAYSIM | Accurate solar radiation for renewable energy assessment |
| **Building Solar Radiation using CRAX** [BETA] | Perform solar radiation analysis using CRAX model | Faster solar analysis for dense urban environments (experimental) |

---

## Renewable Energy Potential Assessment

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Photovoltaic (PV) Panels** | Calculate PV electricity yields from solar panels | Assess rooftop and facade solar electricity potential |
| **Photovoltaic-Thermal (PVT) Panels** | Calculate PVT electricity and heat yields from hybrid panels | Evaluate combined electricity and heat generation |
| **Solar Collectors (SC)** | Calculate heat yields from solar collectors | Assess solar thermal heating potential |
| **Shallow Geothermal Potential** | Calculate heat extracted from shallow geothermal probes | Evaluate ground-source heat pump potential (up to 50m depth) |
| **Water Body Potential** | Calculate heat extracted from water bodies | Assess lake/reservoir heat extraction potential |
| **Sewage Heat Potential** | Calculate heat extracted from sewage heat exchangers | Evaluate wastewater heat recovery potential |

---

## Energy Demand Forecasting

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Energy Demand Part 1: Building Occupancy** | Estimate building occupancy profiles using CEA models | Generate hourly occupancy patterns for demand calculation |
| **Energy Demand Part 2: Load Modelling** | Forecast energy demand of buildings using CEA models | Calculate hourly heating, cooling, electricity, and DHW demand |

---

## Thermal Network Design

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Thermal Network Part 1: Layout** | Create thermal network piping layout using minimum spanning tree | Generate district heating/cooling network layout |
| **Thermal Network Part 2: Flow & Sizing** | Solve thermal hydraulic network flow and sizing | Size pipes and calculate pressure drops for networks |

---

## Life Cycle Analysis

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Emissions** | Calculate embodied and operational emissions of buildings | Assess lifecycle carbon footprint (construction + operation) |
| **Energy Supply System Costs** | Calculate costs for energy supply systems | Estimate capital and operational costs of energy systems |

---

## Energy Supply System Optimisation

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Supply System Optimisation: Building-Scale** | Optimise decentralised energy supply systems | Find optimal building-level energy system configurations |
| **Supply System Optimisation: District-Scale** | Optimise centralised energy supply systems | Find optimal district-level energy system configurations |

---

## Data Management

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Database Helper** | Load CEA Database into current scenario | Import standard databases for building properties and systems |
| **Archetypes Mapper** | Populate building properties using archetypal database | Automatically assign building properties based on archetypes |
| **Weather Helper** | Fetch weather data from third-party sources or morph to future climate scenarios | Download .epw weather files or create future climate scenarios |
| **Surroundings Helper** | Query surrounding building geometry from OpenStreetMap | Automatically fetch surrounding buildings for shading analysis |
| **Terrain Helper** | Fetch topography data from third-party sources | Download .tif terrain elevation data |
| **Streets Helper** | Query streets geometry from OpenStreetMap | Automatically fetch street networks for district analysis |
| **Trees Helper** | Import tree geometries into scenario | Add trees for shading and microclimate analysis |

---

## Utilities

| Feature | Description | Key Use |
|---------|-------------|---------|
| **CEA-4 Format Helper** | Verify and migrate inputs to CEA-4 format | Check data format compatibility and migrate from CEA-3 |
| **Generate Samples for Sensitivity Analysis** | Generate samples for sensitivity analysis using Sobol method | Create parameter samples for uncertainty analysis |
| **Batch Process Workflow** | Batch process scenarios using configured workflow | Run multiple scenarios with the same workflow automatically |
| **DBF to CSV to DBF** | Convert files between DBF and CSV formats | Edit .dbf files in Excel/CSV format |
| **SHP to CSV to SHP** | Convert files between shapefile and CSV formats | Edit shapefile attributes in Excel/CSV format |
| **Rename Building** | Facilitate renaming buildings in scenario | Change building IDs across all scenario files |

---

## Visualisation

| Feature | Description | Key Use |
|---------|-------------|---------|
| **Plot - Building Energy Demand** | Plot bar chart of building energy demand results | Visualise heating, cooling, electricity demand by building |
| **Plot - Lifecycle Emissions** | Plot bar chart of building lifecycle emissions | Visualise total embodied and operational emissions |
| **Plot - Emission Timeline** | Visualise how emissions evolve over time | Track cumulative emissions across different sources over time |
| **Plot - Operational Emissions** | Plot bar chart of building operational emissions | Visualise emissions from energy system operation |
| **Plot - Solar Technology** | Plot bar chart of solar energy technologies' yields | Visualise PV, PVT, and solar collector potential |
| **Plot - Building Comfort Chart** | Plot comfort and discomfort hours for buildings | Visualise thermal comfort analysis results |
| **Plot - Pareto Front** | Plot Pareto front for optimisation results | Visualise trade-offs between cost, emissions, and energy |

---

## Common Workflows

### Basic Building Energy Analysis

**Initial Setup** (Steps 1-5 are typically automated by the Create New Scenario Wizard in CEA-4 App):
1. **Create New Scenario** using CEA-4 App wizard (automatically runs steps 2-5)
2. **Weather Helper** → Fetch weather data (automatic)
3. **Surroundings Helper** → Fetch surrounding buildings (automatic)
4. **Terrain Helper** → Fetch terrain data (automatic)
5. **Database Helper** → Load CEA database (automatic)
6. **Archetypes Mapper** → Assign building properties (automatic on first run)

**Analysis Workflow** (Manual steps):
7. **Building Solar Radiation** → Calculate solar radiation
8. **Energy Demand Part 1** → Calculate occupancy
9. **Energy Demand Part 2** → Calculate energy demand
10. **Plot - Building Energy Demand** → Visualise results

⚠️ **Important**: Remember to re-run **Archetypes Mapper** every time you manually edit input files (zone.shp, building properties, etc.)

### Renewable Energy Assessment
1. Complete Basic Building Energy Analysis (steps 1-10 above)
2. **Photovoltaic Panels** → Calculate PV potential
3. **Solar Collectors** → Calculate solar thermal potential
4. **Shallow Geothermal Potential** → Calculate geothermal potential
5. **Plot - Solar Technology** → Visualise renewable potential

### District Energy System Design
1. Complete Basic Building Energy Analysis (use Create New Scenario Wizard, then run steps 7-10)
2. **Streets Helper** → Fetch street network (may be automatic in wizard)
3. **Thermal Network Part 1** → Generate network layout
4. **Thermal Network Part 2** → Size network pipes
5. **Supply System Optimisation: District-Scale** → Optimise system
6. **Emissions** → Calculate lifecycle emissions
7. **Energy Supply System Costs** → Calculate system costs
8. **Plot - Pareto Front** → Visualise optimisation results

### Climate Impact Assessment
1. Complete Basic Building Energy Analysis (use Create New Scenario Wizard, then run steps 7-10)
2. **Emissions** → Calculate lifecycle emissions
3. **Plot - Lifecycle Emissions** → Visualise total emissions
4. **Plot - Operational Emissions** → Visualise operational emissions
5. **Plot - Emission Timeline** → Track emissions over time

---

## Feature Dependencies

Most CEA-4 features have dependencies on other features. Here are the key dependency chains:

1. **Solar-dependent features** require:
   - Building Solar Radiation (DAYSIM or CRAX)

2. **Demand-dependent features** require:
   - Energy Demand Part 1 (Occupancy)
   - Energy Demand Part 2 (Load Modelling)

3. **Optimisation features** require:
   - Energy Demand Part 2 (Load Modelling)

4. **Network features** require:
   - Energy Demand Part 2 (Load Modelling)
   - Streets Helper (for network layout)

5. **LCA features** require:
   - Energy Demand Part 2 (Load Modelling)

---

## Data Preparation Checklist

Before running any analysis, ensure you have:

- [ ] **Zone geometry** - Building footprints with height information
- [ ] **Weather file** - .epw weather data (use Weather Helper if needed)
- [ ] **Surroundings** - Surrounding buildings for shading (use Surroundings Helper)
- [ ] **Terrain** - Elevation data .tif file (use Terrain Helper)
- [ ] **Building properties** - Use Archetypes Mapper or manual entry
- [ ] **Database files** - Use Database Helper to load standard databases
- [ ] **CEA-4 format verification** - Use CEA-4 Format Helper to verify/migrate data

---

## Getting Started Tips

1. **Use Create New Scenario Wizard**: The CEA-4 App wizard automates initial data setup (weather, surroundings, terrain, databases, archetypes)
2. **Re-run Archetypes Mapper after edits**: Always run Archetypes Mapper again if you manually edit input files
3. **Start small**: Test workflows on a single building before scaling to entire districts
4. **Follow the sequence**: Respect feature dependencies (e.g., run solar before PV)
5. **Check inputs first**: Use CEA-4 Format Helper to verify data quality
6. **Visualise often**: Use plotting features to verify results at each step
7. **Save scenarios**: Create separate scenarios for different design alternatives

---

## Where to Find More Information

For detailed information about each feature, refer to the category-specific guides:

- [Import & Export](01-import-export.md)
- [Solar Radiation Analysis](02-solar-radiation.md)
- [Renewable Energy Potential Assessment](03-renewable-energy.md)
- [Energy Demand Forecasting](04-demand-forecasting.md)
- [Thermal Network Design](05-thermal-network.md)
- [Life Cycle Analysis](06-life-cycle-analysis.md)
- [Energy Supply System Optimisation](07-supply-optimization.md)
- [Data Management](08-data-management.md)
- [Utilities](09-utilities.md)
- [Visualisation](10-visualisation.md)

---

[← Back to Index](index.md)