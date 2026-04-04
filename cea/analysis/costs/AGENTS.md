# Cost Calculations

## Main API

**`calc_capex_annualized(capex_total, IR_%, LT_yr) → float`** - Convert total CAPEX to annual cost

## Cost Flow

```
Database Parameters (SUPPLY_*.csv)
    ↓
Total CAPEX = Peak_kW × efficiency × CAPEX_USD2015kW
    ↓
    ├─→ Fixed OPEX = CAPEX × O&M_%
    └─→ Annualized CAPEX = CAPEX × IR% / (1 - (1 + IR%)^-LT)
         ↓
         TAC = OPEX_a + CAPEX_a + Variable_OPEX
```

## Key Patterns

### Cost Calculation in `system_costs.py`

```python
# 1. Total CAPEX (line 107-109)
capex_total = peak_kW * efficiency * CAPEX_USD2015kW

# 2. Fixed OPEX (O&M) (line 111)
opex_fixed = capex_total * (O&M_% / 100)

# 3. Annualized CAPEX (line 119-121)
capex_a = calc_capex_annualized(capex_total, IR_%, LT_yr)

# 4. Total Annualized Cost (line 135)
TAC = opex_a + capex_a
```

### Database Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `CAPEX_USD2015kW` | Infrastructure cost per kW | 62.1 |
| `LT_yr` | Lifetime | 20 |
| `O&M_%` | Annual O&M as % of CAPEX | 1.3 |
| `IR_%` | Interest rate | 1.3 |
| `efficiency` | System efficiency | 0.99 |

**Source**: `databases/{region}/ASSEMBLIES/SUPPLY/SUPPLY_*.csv`

## Example Calculation

**Input**: 100 kW peak, eff=0.99, CAPEX=62.1, LT=20yr, O&M=1.3%, IR=1.3%

```python
capex_total = 100 × 0.99 × 62.1 = 6,148 USD
opex_fixed = 6,148 × 0.013 = 80 USD/yr
capex_a = 6,148 × 0.0655 = 350 USD/yr  # annuity factor ≈ 0.0655
TAC = 80 + 350 + variable_opex = 430 USD/yr (+ energy costs)
```

## ✅ DO

```python
# Read CAPEX from SUPPLY assemblies
supply = pd.read_csv('ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv')
capex = supply['CAPEX_USD2015kW']

# Read variable OPEX from feedstocks
grid = pd.read_csv('COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/GRID.csv')
opex_var = grid['Opex_var_buy_USD2015kWh']

# Merge for complete cost picture
costs = supply.merge(grid, left_on='feedstock', right_on='code')
```

## ❌ DON'T

```python
# Don't confuse CAPEX (infrastructure) with variable OPEX (energy purchase)
# Don't use COMPONENTS for building-level cost estimates
# Don't forget to annualize CAPEX before comparing with annual OPEX
```

## Related Files
- `cea/analysis/costs/system_costs.py:107-135` - Cost calculation flow
- `cea/analysis/lca/operation.py` - Uses same database parameters
- `cea/databases/AGENTS.md` - Database structure
- `databases/{region}/ASSEMBLIES/SUPPLY/` - CAPEX, efficiency, lifetime
- `databases/{region}/COMPONENTS/FEEDSTOCKS/` - Variable OPEX, emissions
