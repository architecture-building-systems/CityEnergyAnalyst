# CEA Database Structure

## File Hierarchy

```
databases/{region}/
├── ASSEMBLIES/           # Simplified system packages for building-level analysis
│   ├── SUPPLY/          # Generation systems (CAPEX, efficiency, lifespan)
│   ├── HVAC/            # Distribution/emission (temperatures, capacities)
│   └── ENVELOPE/        # Building envelope (U-values, windows, shading)
└── COMPONENTS/          # Detailed equipment for optimization
    ├── CONVERSION/      # Boilers, chillers, heat pumps (cost curves)
    └── FEEDSTOCKS/      # Grid electricity, fuels (hourly OPEX, emissions)
```

## Key Patterns

### COMPONENTS vs ASSEMBLIES

**COMPONENTS** - Detailed equipment specs for optimization:
- Location: `COMPONENTS/CONVERSION/*.csv`
- Use: District energy optimization, capacity-dependent costs
- Example: `BO5` electrical boiler - eff: 0.99, cost curve: a+bx+cx²

**ASSEMBLIES** - Simplified packages for building demand:
- Location: `ASSEMBLIES/SUPPLY/*.csv`
- Use: Building-level demand calculations, baseline costs
- Example: `SUPPLY_HOTWATER_AS1` - eff: 0.9, cost: 200 USD/kW

| Aspect | COMPONENTS | ASSEMBLIES |
|--------|-----------|------------|
| Efficiency | 0.99 (detailed) | 0.9 (conservative) |
| Cost | Complex curve | Single value |
| Use Case | Optimization | Demand calculation |

### Grid Electricity: Two Complementary Files

**SUPPLY_ELECTRICITY.csv** (Infrastructure):
```python
# Location: ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv
CAPEX_USD2015kW    # One-time infrastructure (panels, transformers)
efficiency, LT_yr  # System performance, lifetime
```

**GRID.csv** (Energy costs):
```python
# Location: COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/GRID.csv
# 24 hourly rows
GHG_kgCO2MJ              # Emissions factor
Opex_var_buy_USD2015kWh  # Hourly purchase cost
```

**Merge pattern**:
```python
factors_electricity = pd.read_csv('SUPPLY_ELECTRICITY.csv')
factors_resources = pd.read_csv('GRID.csv')
costs = factors_electricity.merge(factors_resources, left_on='feedstock', right_on='code')
```

## ✅ DO

```python
# Use ASSEMBLIES for building demand
supply = pd.read_csv('ASSEMBLIES/SUPPLY/SUPPLY_HEATING.csv')

# Use COMPONENTS for optimization
equipment = pd.read_csv('COMPONENTS/CONVERSION/BOILERS.csv')

# Check references when modifying COMPONENTS
assemblies = pd.read_csv('ASSEMBLIES/SUPPLY/SUPPLY_HEATING.csv')
refs = assemblies['primary_components']  # e.g., "BO5"
```

## ❌ DON'T

```python
# Don't use COMPONENTS for simple demand calculations
# Don't modify COMPONENTS without checking ASSEMBLY references
# Don't treat SUPPLY_ELECTRICITY.csv and GRID.csv as duplicates
```

## Related Files
- `cea/schemas.yml` - Database schema definitions
- `cea/demand/building_properties/building_supply_systems.py` - ASSEMBLIES usage
- `cea/optimization_new/` - COMPONENTS usage
- `cea/analysis/costs/system_costs.py` - SUPPLY_ELECTRICITY + GRID merge
