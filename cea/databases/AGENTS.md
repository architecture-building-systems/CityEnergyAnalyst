# CEA Database Structure Knowledge

This document explains the CEA database structure, relationships between files, and how different database components work together.

---

## Grid Electricity: Two Sources of Truth

### Overview
Two CSV files define grid electricity properties that work together hierarchically:

### SUPPLY_ELECTRICITY.csv (Assembly Level)
**Location**: `databases/{region}/ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv`

**Purpose**: Defines electricity supply assemblies (system configurations)

**Key Fields**:
- `CAPEX_USD2015kW`: Capital expenditure for infrastructure (panels, transformers, grid connection)
- `efficiency`: System efficiency
- `LT_yr`, `O&M_%`, `IR_%`: Lifetime, maintenance costs, interest rate

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

**How They Work Together**:
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
- They **complement** each other rather than duplicate information

---

## Components vs Assemblies Relationship

### Key Concept
These are **NOT two sources of truth** - they have **different purposes** and work at different abstraction levels.

### COMPONENTS = Building Blocks
**Location**: `COMPONENTS/CONVERSION/*.csv` (e.g., BOILERS.csv)

**Purpose**: Detailed technical specifications for individual equipment

**Example: BO5 (Electrical Boiler)**:
- Efficiency: 0.99 (detailed)
- Cost Model: Complex curve (a+bx+cx²...)
- Capacity range: 1 W to 10,000,000,000 W

**Used for**:
- Detailed optimization
- District energy system design
- Capacity-dependent cost curves

### ASSEMBLIES = Simplified System Packages
**Location**: `ASSEMBLIES/SUPPLY/*.csv` (e.g., SUPPLY_HOTWATER.csv)

**Purpose**: Simplified system configurations for building-level analysis

**Example: SUPPLY_HOTWATER_AS1 (Electrical boiler)**:
- Efficiency: 0.9 (conservative/simplified)
- Cost Model: Single value (200 USD/kW)
- Aggregated/average capacity

**Used for**:
- Building demand calculations
- Baseline cost estimates

### Key Differences

| Aspect | COMPONENTS | ASSEMBLIES |
|--------|-----------|------------|
| **Purpose** | Detailed equipment specs | Simplified system package |
| **Cost Model** | Complex curve | Single value |
| **Efficiency** | Detailed (0.99) | Conservative (0.9) |
| **Used By** | Optimization, district systems | Building demand calculations |
| **Capacity** | Size-dependent | Aggregated/average |

### Relationship
- ASSEMBLIES *can reference* COMPONENTS via `primary_components` field
- Example: `SUPPLY_HEATING_AS4` → `BO5` → Detailed BO5 specs

### When to Use Each

**Use ASSEMBLIES when**:
- Quick building-level assessments
- "What type of system does this building have?"

**Use COMPONENTS when**:
- Detailed system optimization
- "What specific boiler model and size should we install?"

---

## File Structure Quick Reference

```
databases/{region}/
├── ASSEMBLIES/
│   ├── SUPPLY/
│   │   ├── SUPPLY_ELECTRICITY.csv  (CAPEX, system efficiency)
│   │   ├── SUPPLY_HEATING.csv
│   │   ├── SUPPLY_COOLING.csv
│   │   └── SUPPLY_HOTWATER.csv
│   └── HVAC/
│       ├── HVAC_HEATING.csv
│       └── HVAC_COOLING.csv
└── COMPONENTS/
    ├── CONVERSION/
    │   ├── BOILERS.csv             (Detailed equipment specs)
    │   └── CHILLERS.csv
    └── FEEDSTOCKS/
        └── FEEDSTOCKS_LIBRARY/
            └── GRID.csv            (Hourly OPEX and emissions)
```

---

## Common Questions

**Q: Are SUPPLY_ELECTRICITY.csv and GRID.csv duplicates?**
A: No, they complement each other. SUPPLY_ELECTRICITY has CAPEX (infrastructure), GRID.csv has OPEX (energy costs).

**Q: Why do we have both COMPONENTS and ASSEMBLIES?**
A: Different detail levels for different purposes. ASSEMBLIES for quick building analysis, COMPONENTS for detailed optimization.

**Q: Can I modify just one file?**
A: Be careful - ensure consistency. If you change a COMPONENT, check if any ASSEMBLY references it.

---

**For more information, see**:
- CEA documentation: https://docs.cityenergyanalyst.com
- CEA schemas: `cea/schemas.yml`
- Database documentation: `cea/databases/{region}/documentation.md`
