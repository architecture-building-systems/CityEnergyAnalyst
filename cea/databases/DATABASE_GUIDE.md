# CEA Database Structure - Detailed Guide

This document provides detailed explanations about the CEA database structure for human readers.

## Grid Electricity: Two Complementary Files

### SUPPLY_ELECTRICITY.csv (Assembly Level)
**Location**: `databases/{region}/ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv`

**Purpose**: Defines electricity supply assemblies (system configurations)

**Key Fields**:
- `CAPEX_USD2015kW`: Capital expenditure for infrastructure (panels, transformers, grid connection)
- `efficiency`: System efficiency
- `LT_yr`: Lifetime in years
- `O&M_%`: Annual operations & maintenance as percentage of CAPEX
- `IR_%`: Interest rate for annualization

**Used by**:
- `cea/analysis/lca/operation.py:56`
- `cea/analysis/costs/system_costs.py:181`
- `cea/demand/building_properties/building_supply_systems.py:54`

### GRID.csv (Feedstock Level)
**Location**: `databases/{region}/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/GRID.csv`

**Purpose**: Defines hourly grid electricity properties (24 rows for each hour)

**Key Fields**:
- `GHG_kgCO2MJ`: Emissions factor for grid electricity
- `Opex_var_buy_USD2015kWh`: Variable operating cost to buy electricity
- `Opex_var_sell_USD2015kWh`: Variable operating cost to sell electricity

### How They Work Together

These two files complement each other rather than duplicate information:

```python
# Step 1: Load supply assemblies (CAPEX)
factors_electricity = pd.read_csv('SUPPLY_ELECTRICITY.csv')

# Step 2: Load feedstocks (OPEX and emissions)
factors_resources['GRID'] = pd.read_csv('GRID.csv')

# Step 3: Merge together
electricity_costs = factors_electricity.merge(factors_resources,
                                             left_on='feedstock', right_on='code')
```

**Summary**:
- **SUPPLY_ELECTRICITY.csv's CAPEX** = Infrastructure costs (one-time investment)
- **GRID.csv's Opex_var_buy** = Energy purchase costs (ongoing operational)

## Components vs Assemblies: Different Abstraction Levels

### COMPONENTS = Detailed Equipment Specifications

**Location**: `COMPONENTS/CONVERSION/*.csv` (e.g., BOILERS.csv)

**Purpose**: Detailed technical specifications for individual equipment used in optimization

**Example: BO5 (Electrical Boiler)**:
- Efficiency: 0.99 (detailed, manufacturer-specific)
- Cost Model: Complex curve (a + b×capacity + c×capacity²...)
- Capacity range: 1 W to 10,000,000,000 W
- Size-dependent performance curves

**Used for**:
- Detailed optimization studies
- District energy system design
- Capacity-dependent cost calculations
- Technology comparison

### ASSEMBLIES = Simplified System Packages

**Location**: `ASSEMBLIES/SUPPLY/*.csv` (e.g., SUPPLY_HOTWATER.csv)

**Purpose**: Simplified system configurations for building-level analysis

**Example: SUPPLY_HOTWATER_AS1 (Electrical boiler)**:
- Efficiency: 0.9 (conservative/simplified for general use)
- Cost Model: Single value (200 USD/kW)
- Aggregated/average capacity
- Simplified performance assumptions

**Used for**:
- Quick building-level demand calculations
- Baseline cost estimates
- Scenario comparisons
- Initial feasibility studies

### When to Use Each

**Use ASSEMBLIES when**:
- Performing quick building-level assessments
- Answering "What type of system does this building have?"
- Baseline energy demand calculations
- Comparing different building scenarios

**Use COMPONENTS when**:
- Optimizing detailed system configurations
- Answering "What specific boiler model and size should we install?"
- District energy system design
- Detailed technology selection

### Relationship Between COMPONENTS and ASSEMBLIES

ASSEMBLIES can reference COMPONENTS via the `primary_components` field:
- Example: `SUPPLY_HEATING_AS4` → references `BO5` → links to detailed BO5 specs in BOILERS.csv

### Common Questions

**Q: Are SUPPLY_ELECTRICITY.csv and GRID.csv duplicates?**
A: No, they complement each other. SUPPLY_ELECTRICITY has CAPEX (infrastructure), GRID.csv has OPEX (energy costs). Think of SUPPLY_ELECTRICITY as the "hardware costs" and GRID.csv as the "energy costs".

**Q: Why do we have both COMPONENTS and ASSEMBLIES?**
A: Different detail levels for different purposes. ASSEMBLIES are like "pre-configured packages" for quick analysis, while COMPONENTS are "detailed specifications" for optimization. It's similar to choosing between a pre-configured laptop vs. building a custom PC.

**Q: Can I modify just one file?**
A: Be careful - ensure consistency. If you change a COMPONENT that's referenced by an ASSEMBLY, you should check if the ASSEMBLY needs updating too.

**Q: Why are ASSEMBLY efficiencies lower than COMPONENT efficiencies?**
A: ASSEMBLIES use conservative values to account for real-world conditions, installation quality variations, and aging. COMPONENTS use manufacturer-specified values for optimization studies.

## File Structure Reference

```
databases/{region}/
├── ARCHETYPES/
│   ├── CONSTRUCTION_TYPES.csv    # Links buildings to envelope/HVAC systems
│   └── USE_TYPES.csv             # Defines occupancy, setpoints, schedules
│
├── ASSEMBLIES/                   # Simplified packages for building-level analysis
│   ├── SUPPLY/
│   │   ├── SUPPLY_ELECTRICITY.csv  # CAPEX, system efficiency, lifetime
│   │   ├── SUPPLY_HEATING.csv
│   │   ├── SUPPLY_COOLING.csv
│   │   └── SUPPLY_HOTWATER.csv
│   ├── HVAC/
│   │   ├── HVAC_HEATING.csv      # Distribution/emission systems
│   │   └── HVAC_COOLING.csv
│   └── ENVELOPE/
│       ├── ENVELOPE_WALL.csv     # U-values, thermal properties
│       ├── ENVELOPE_ROOF.csv
│       ├── ENVELOPE_WINDOW.csv
│       └── ENVELOPE_SHADING.csv
│
└── COMPONENTS/                   # Detailed equipment for optimization
    ├── CONVERSION/
    │   ├── BOILERS.csv           # Detailed equipment specs, cost curves
    │   ├── CHILLERS.csv
    │   ├── HEAT_PUMPS.csv
    │   └── ...
    └── FEEDSTOCKS/
        └── FEEDSTOCKS_LIBRARY/
            ├── GRID.csv          # Hourly OPEX and emissions
            ├── NATURALGAS.csv
            └── ...
```

## Modifying Databases Safely

1. **Backup first**: Always keep a copy of the original database files
2. **Check references**: Use grep/search to find where database entries are used
3. **Validate structure**: Ensure CSV structure matches schema in `cea/schemas.yml`
4. **Test thoroughly**: Run test scenarios after modifications
5. **Document changes**: Keep notes on what you changed and why

## For More Information

- CEA documentation: https://docs.cityenergyanalyst.com
- CEA schemas: `cea/schemas.yml`
- Database-specific documentation: `cea/databases/{region}/documentation.md`
