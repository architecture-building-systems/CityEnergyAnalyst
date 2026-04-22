# Final Energy Calculation Module

Calculate final energy consumption (energy by carrier) for buildings and district plants.

## Overview

This module converts building energy demand to final energy consumption by carrier type (electricity, natural gas, district heating, etc.), accounting for supply system conversion efficiencies.

**Key Features:**
- Constant efficiency approach using COMPONENTS database
- Assembly → Component → Feedstock workflow
- Building-scale and district-scale system support
- Booster system handling for temperature supplementation
- Dual mode operation (production vs what-if)

## Quick Start

### Production Mode (Baseline)
Uses supply system configuration from `supply.csv`:

```bash
cea final-energy --scenario /path/to/scenario
```

Output location: `outputs/data/final-energy/baseline/`

### What-If Mode
Override supply systems with config parameters:

```bash
cea final-energy \
  --scenario /path/to/scenario \
  --overwrite-supply-settings \
  --what-if-name my-scenario \
  --supply-type-hs "SUPPLY_HEATING_AS3 (building)" \
  --supply-type-dhw "SUPPLY_HOTWATER_AS3 (building)" \
  --supply-type-cs "SUPPLY_COOLING_AS1 (building)"
```

Output location: `outputs/data/final-energy/my-scenario/`

## Prerequisites

1. **Energy demand results** - Run `cea demand` first
2. **Supply system configuration** - Either:
   - `inputs/building-properties/supply.csv` (production mode)
   - Config parameters (what-if mode)
3. **Thermal network results** (if using district systems) - Run `cea thermal-network` first

## Output Files

### Individual Building Files (`B####.csv`)
Hourly timeseries (8760 rows) with final energy by carrier:
- Demand columns: `Qhs_sys_kWh`, `Qww_sys_kWh`, `Qcs_sys_kWh`, `E_sys_kWh`
- Carrier columns: `Qhs_sys_{CARRIER}_kWh`, `Qww_sys_{CARRIER}_kWh`, etc.
- Metadata: `scale`, `case`, `case_description`

### Buildings Summary (`final_energy_buildings.csv`)
Annual totals and peaks per building:
- One row per building
- Annual energy by carrier (MWh)
- Total final energy and peak demand
- Building metadata (GFA, coordinates, case)

### Detailed Breakdown (`final_energy.csv`)
Service-level breakdown with component details:
- Multiple rows per building (one per service-carrier combination)
- Assembly and component information
- Efficiency values
- Demand column references for traceability

### Supply Configuration (`supply_configuration.json`)
Complete supply system configuration used:
- Metadata (mode, timestamp, network name)
- Per-building configurations
- Assembly codes, component codes, efficiencies
- Booster system information

## Energy Carriers

Supported carrier types:
- **NATURALGAS** - Natural gas from grid
- **OIL** - Heating oil
- **COAL** - Coal fuel
- **WOOD** - Wood biomass
- **GRID** - Electricity from grid
- **DH** - District heating
- **DC** - District cooling
- **SOLAR** - Solar thermal (future)

## Case Classification

Buildings are classified by supply system configuration:
- **Case 1:** Standalone (all services building-scale)
- **Case 2:** DH + DC (centralized heating + cooling)
- **Case 3:** DH only (district heating + standalone cooling)
- **Case 4:** DC only (standalone heating + district cooling)
- **Case 4.01:** DC + booster for space heating
- **Case 4.02:** DC + booster for hot water
- **Case 4.03:** DC + booster for both

## Calculation Method

### Building-Scale Systems
```python
final_energy = demand / component_efficiency
```

Example: Natural gas boiler (efficiency 0.82)
- Demand: 50 MWh/year
- Final energy: 50 / 0.82 = 60.98 MWh/year natural gas

### District-Scale Systems
Reads actual consumption from thermal-network substation results:
```python
final_energy = thermal_network_consumption
```

No efficiency applied (already accounted for at plant level).

### Booster Systems
For buildings with district supply where network temperature is insufficient:
```python
booster_final_energy = booster_demand / booster_efficiency
```

Booster demand comes from thermal-network booster substation files.

## Configuration Parameters

### Core Parameters
- `overwrite-supply-settings` (bool) - Enable what-if mode
- `what-if-name` (str) - Scenario name for output folder
- `network-name` (str) - District network layout name

### Supply Type Parameters (What-If Mode)
- `supply-type-hs` (list) - Space heating assemblies
- `supply-type-dhw` (list) - Hot water assemblies
- `supply-type-cs` (list) - Space cooling assemblies

### Booster Parameters (What-If Mode)
- `hs-booster-type` (list) - Space heating booster assemblies
- `dhw-booster-type` (list) - Hot water booster assemblies

## Error Handling

Common errors and solutions:

**"Demand file not found"**
→ Run `cea demand` first

**"District heating substation file not found"**
→ Building has district system (AS9) but no thermal-network results
→ Run `cea thermal-network` or change to building-scale system

**"Assembly not found in database"**
→ Check assembly code spelling in supply.csv or config parameters
→ Verify database files exist in `inputs/database/`

**"Component not found"**
→ Component code referenced by assembly doesn't exist
→ Check ASSEMBLIES/SUPPLY files for correct component references

## Examples

### Example 1: Production Mode
Calculate final energy using existing supply.csv:

```bash
cea final-energy --scenario /path/to/scenario
```

### Example 2: What-If with Natural Gas
Test scenario with natural gas heating and cooling:

```bash
cea final-energy \
  --scenario /path/to/scenario \
  --overwrite-supply-settings \
  --what-if-name gas-only \
  --supply-type-hs "SUPPLY_HEATING_AS3 (building)" \
  --supply-type-dhw "SUPPLY_HOTWATER_AS3 (building)" \
  --supply-type-cs "SUPPLY_COOLING_AS1 (building)"
```

### Example 3: District Heating + Cooling
Test centralized energy scenario:

```bash
cea final-energy \
  --scenario /path/to/scenario \
  --overwrite-supply-settings \
  --what-if-name district \
  --network-name my-network \
  --supply-type-hs "SUPPLY_HEATING_AS9 (district)" \
  --supply-type-dhw "SUPPLY_HOTWATER_AS9 (district)" \
  --supply-type-cs "SUPPLY_COOLING_AS3 (district)"
```

## Technical Details

### Database Structure
- **ASSEMBLIES/SUPPLY** - Simplified system packages with primary_components
- **COMPONENTS/CONVERSION** - Detailed equipment with efficiency and fuel_code
- Component types: Boilers (BO*), Heat Pumps (HP*), Chillers (CH*)

### Efficiency Values
- Boilers: `min_eff_rating` (e.g., 0.82 for natural gas boiler)
- Heat Pumps: `min_eff_rating_seasonal` (COP, e.g., 3.1)
- Chillers: `min_eff_rating` (COP, e.g., 4.7)

### File Locations
Input files:
- `inputs/building-properties/supply.csv` - Supply system assignments
- `inputs/database/ASSEMBLIES/SUPPLY/*.csv` - Supply assemblies
- `inputs/database/COMPONENTS/CONVERSION/*.csv` - Component specifications
- `outputs/data/thermal-network/{network}/DH/substation/*.csv` - DH consumption
- `outputs/data/thermal-network/{network}/DC/substation/*.csv` - DC consumption

Output files:
- `outputs/data/final-energy/{whatif-name}/` - All final energy results

## Related Scripts

- `cea demand` - Calculate building energy demand (prerequisite)
- `cea thermal-network` - Simulate district heating/cooling networks (for district systems)
- `cea emissions` - Calculate GHG emissions from final energy
- `cea system-costs` - Calculate supply system costs

## References

- IMPLEMENTATION_PLAN.md - Design decisions and calculation approach
- BACKEND_PLAN.md - File organization and CSV schemas
- cea/databases/AGENTS.md - Database structure documentation
