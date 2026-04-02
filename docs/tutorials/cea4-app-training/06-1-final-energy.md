# Final Energy

## Overview

Calculates the final energy consumed by each building and district plant under a specific supply configuration (what-if scenario). Final energy is what the energy system actually consumes from carriers (grid electricity, natural gas, oil, coal, wood) to meet the building's energy demand.

## What It Calculates

For each **building**:
- Energy carrier consumption per service (heating, cooling, DHW, electricity)
- Conversion losses based on technology efficiency
- Booster energy for district-connected buildings

For each **district plant** (DH/DC):
- Primary and tertiary conversion energy
- Network pumping electricity

## Prerequisites

- **Energy Demand Part 2** completed
- **Solar Radiation** completed (if PV/PVT/SC are configured)
- **Thermal Network Part 1 + Part 2** completed (if district network scenarios are used)
- Building supply settings configured (Building Properties > Supply tab)

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| **What-if name** | Name for this supply configuration scenario |
| **Network name** | Which thermal network layout to use (if applicable) |
| **Supply type (heating/cooling/DHW)** | Assembly codes for building and/or district scale |
| **Overwrite supply settings** | True to use what-if mode instead of production mode |
| **Connected buildings** | Override which buildings connect to the network |

## How to Use

1. **Configure supply systems** in Building Properties > Supply tab:
   - Set scale (BUILDING or DISTRICT) per service per building
   - Assign conversion technologies and carriers

2. **Run Final Energy**:
   - Navigate to **Life Cycle Analysis**
   - Select **Final Energy**
   - Enter a what-if scenario name
   - Select network layout (if buildings use district services)
   - Click **Run**

3. **Processing time**: 1-5 minutes for typical districts

## Output Files

All outputs are stored under `{scenario}/outputs/data/analysis/{what-if-name}/final-energy/`:

| File | Description |
|------|-------------|
| `configuration.json` | Full supply configuration (buildings + plants). Used by all downstream features. |
| `final_energy_buildings.csv` | Annual summary per entity (buildings + plants) |
| `{building_name}.csv` | 8,760-row hourly energy by carrier per building |
| `{plant_name}.csv` | 8,760-row hourly energy by carrier per plant |

## Understanding Results

- **Building-scale systems**: Final energy = demand / efficiency
- **District-connected buildings**: Show DH/DC as their carrier; actual fuel consumption is at the plant level
- **Plants**: Appear as separate rows with `type=plant`; their carrier consumption covers all connected buildings plus network losses and pumping
- **`configuration.json`**: Stores the complete supply configuration and is the sole source of truth for emissions, costs, and heat rejection

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Multiple district heating assembly types detected" | All district buildings must use the same assembly. Provide only one district assembly per service. |
| "District substation file not found" | Run thermal-network Part 2 before final-energy for scenarios with district connections. |
| "Component not found" | Check that ASSEMBLIES references valid COMPONENTS codes in the database. |

---

## Plot - Final Energy

### Overview
Creates bar charts of final energy consumption by carrier for buildings and plants.

### What It Shows
- Stacked bars per building showing carrier breakdown (Grid, Natural Gas, Oil, Coal, Wood)
- Plant entities shown with `-DH` or `-DC` suffix
- Multiple what-if scenarios can be compared side by side

### Key Parameters

| Parameter | Description | Options |
|-----------|-------------|---------|
| **What-if name** | Which scenario(s) to plot | Multi-select from available |
| **Y metric** | Which carrier(s) to show | Grid electricity, Natural gas, Oil, Coal, Wood |
| **Y unit** | Energy unit | MWh, kWh, Wh |
| **Normalise by** | Normalisation | None, Gross floor area, Conditioned floor area |
| **X axis** | View type | By building, by month, by season, district hourly, etc. |
| **Include** | Entity filter | Buildings, Plants, or both |

### Chart Interpretation

- **Tall bars** = high energy consumers
- **Colour distribution** shows fuel mix
- **Plant bars** are typically much larger than individual buildings (they serve many buildings)
- **Normalised view** (per m2) enables fair comparison across building sizes

---

## Related Features
- **[Emissions](06-2-emissions.md)** - Uses final energy to calculate operational emissions
- **[System Costs](06-3-system-costs.md)** - Uses final energy to calculate operational costs
- **[Heat Rejection](06-4-heat-rejection.md)** - Uses final energy to calculate waste heat

---

[<- Back: Life Cycle Analysis](06-0-life-cycle-analysis.md) | [Back to Index](index.md) | [Next: Emissions ->](06-2-emissions.md)
