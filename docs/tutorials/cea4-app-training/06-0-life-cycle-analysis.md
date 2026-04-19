# Life Cycle Analysis

Life cycle analysis (LCA) features assess the environmental impacts and costs of building energy systems throughout their lifecycle. CEA-4 uses a **what-if analysis** framework: you define supply configurations for buildings and district plants, then analyse final energy, emissions, costs, and heat rejection for each scenario.

---

## What-If Analysis Concept

A **what-if scenario** represents one possible supply system configuration for your district. Each scenario defines:
- Which energy carrier each building uses for each service (heating, cooling, DHW, electricity)
- Which conversion technology each building uses (boiler, heat pump, chiller, etc.)
- Whether buildings connect to a district heating (DH) or district cooling (DC) network
- What plant technology serves the district network

You can create multiple what-if scenarios to compare alternatives (e.g. "all gas boilers" vs "heat pumps with DH").

### Dependency Chain

```
Energy Demand (Part 2)
  |
  v
Final Energy  (per what-if scenario)
  |
  +--> LCA Emissions  (lifecycle + operational)
  +--> System Costs    (CAPEX + OPEX)
  +--> Heat Rejection  (waste heat to environment)
```

**Final Energy** must run first for each what-if scenario. It produces `configuration.json` which stores the supply configuration, and per-building/plant hourly energy files. The other three features read from these outputs.

### Output Location

All what-if results are stored under:
```
{scenario}/outputs/data/analysis/{what-if-name}/
  ├── final-energy/
  ├── emissions/
  ├── costs/
  └── heat/
```

---

## Features

| Feature | Page | Description |
|---------|------|-------------|
| Final Energy | [06-1-final-energy.md](06-1-final-energy.md) | Energy carriers and quantities consumed by buildings and plants |
| Emissions | [06-2-emissions.md](06-2-emissions.md) | Lifecycle and operational greenhouse gas emissions |
| System Costs | [06-3-system-costs.md](06-3-system-costs.md) | CAPEX, OPEX, and total annualised costs |
| Heat Rejection | [06-4-heat-rejection.md](06-4-heat-rejection.md) | Waste heat rejected to the environment |

---

## Common Settings

### Include Plants/Buildings Filter

All four features and their plots share a filter to control whether **buildings**, **plants**, or both appear in results:
- **Buildings**: Individual building-scale systems
- **Plants**: District-scale plants (DH/DC network plants)

This is configured via the `plots-include-plants-buildings` parameter section.

### Building Filter

Standard building filters apply to all features:
- Filter by building name
- Filter by construction year range
- Filter by construction type
- Filter by use type

Plant entities are never filtered by the building name list.

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Prerequisite for all LCA features
- **[Thermal Network](05-thermal-network.md)** - Required for district-connected scenarios
- **[Renewable Energy Assessment](03-renewable-energy.md)** - Solar potential affects embodied emissions
- **[Visualisation](10-visualisation.md)** - Additional plotting tools
- **[Export Results to CSV](01-import-export.md#export-results-to-csv-summary--analytics)** - Batch export of what-if results

---

[← Back: Thermal Network](05-thermal-network.md) | [Back to Index](index.md) | [Next: Final Energy →](06-1-final-energy.md)
