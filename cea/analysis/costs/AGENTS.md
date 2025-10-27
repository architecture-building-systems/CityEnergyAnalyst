# CEA Cost Calculations Knowledge

This document explains how CAPEX and cost calculations work in CEA.

---

## CAPEX Usage in Cost Calculations

### Overview
**CAPEX_USD2015kW** from database files (e.g., `SUPPLY_ELECTRICITY.csv`) is used in cost calculations in `cea/analysis/costs/system_costs.py`.

### Calculation Flow

**Location**: `cea/analysis/costs/system_costs.py`

#### 1. Total CAPEX (line 107-109)
```python
result[service + '_capex_total_USD'] = (database[service + '0_kW'].values *
                                        database['efficiency'].values *
                                        database['CAPEX_USD2015kW'].values)
```

**Formula**: `Total CAPEX = Peak Power (kW) × Efficiency × Unit CAPEX (USD2015/kW)`

#### 2. Fixed OPEX (line 111)
Maintenance costs calculated from CAPEX:
```python
electricity_opex_fixed_USD = capex_total × O&M_% / 100
```

#### 3. Annualized CAPEX (line 119-121)
```python
electricity_capex_a_USD = calc_capex_annualized(capex_total, IR_%, LT_yr)
```

Amortizes infrastructure costs over the system lifetime.

#### 4. Total Annualized Cost - TAC (line 135)
```python
electricity_TAC_USD = opex_a_USD + capex_a_USD
```

Combines all annual costs.

---

## Cost Components Breakdown

### What CAPEX Represents
For grid electricity with CAPEX = 62.1 USD2015/kW (Singapore example):
- Electrical panels
- Transformers
- Grid connection infrastructure
- Distribution equipment within the building

**Unit**: USD2015 per kW of peak power demand

### Cost Flow Diagram
```
CAPEX_USD2015kW (from database)
    ↓
Total CAPEX = Peak_kW × efficiency × CAPEX_USD2015kW
    ↓
    ├─→ Fixed OPEX (O&M) = Total CAPEX × O&M_%
    └─→ Annualized CAPEX = f(Total CAPEX, IR_%, LT_yr)
         ↓
         Total Annualized Cost (TAC) = OPEX_a + CAPEX_a
```

---

## Key Parameters from Database

### From SUPPLY_*.csv files:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `CAPEX_USD2015kW` | Capital cost per kW | 62.1 USD/kW |
| `LT_yr` | Lifetime in years | 20 years |
| `O&M_%` | Annual O&M as % of CAPEX | 1.3% |
| `IR_%` | Interest rate for annualization | 1.3% |
| `efficiency` | System efficiency | 0.99 |

### Calculation Example

**Given**:
- Peak demand: 100 kW
- Efficiency: 0.99
- CAPEX: 62.1 USD2015/kW
- LT: 20 years
- O&M: 1.3%
- IR: 1.3%

**Calculations**:
1. Total CAPEX = 100 × 0.99 × 62.1 = **6,147.9 USD**
2. Annual O&M = 6,147.9 × 0.013 = **79.9 USD/year**
3. Annualized CAPEX = 6,147.9 × annuity_factor(1.3%, 20yr) = **~350 USD/year**
4. TAC = 79.9 + 350 + Variable_OPEX = **~430 USD/year** (excluding energy costs)

---

## Important Notes

### CAPEX vs OPEX
- **CAPEX** (Capital Expenditure): One-time infrastructure investment
- **Fixed OPEX**: Annual maintenance (% of CAPEX)
- **Variable OPEX**: Energy purchase costs (from GRID.csv's `Opex_var_buy_USD2015kWh`)

### Where Costs Are Used
- **LCA calculations**: `cea/analysis/lca/operation.py`
- **Cost calculations**: `cea/analysis/costs/system_costs.py`
- **Building supply systems**: `cea/demand/building_properties/building_supply_systems.py`

### Annualization Formula
The `calc_capex_annualized` function converts total CAPEX to annual cost using:
```python
annuity_factor = IR_% / (1 - (1 + IR_%)^(-LT_yr))
annualized_capex = total_capex × annuity_factor
```

---

## Quick Reference

**To find CAPEX values**: Check `databases/{region}/ASSEMBLIES/SUPPLY/SUPPLY_*.csv`

**To find OPEX values**: Check `databases/{region}/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/*.csv`

**To modify cost calculations**: See `cea/analysis/costs/system_costs.py`

---

**For more information, see**:
- CEA documentation: https://docs.cityenergyanalyst.com
- Cost calculation script: `cea/analysis/costs/system_costs.py`
- Database structure: `cea/databases/AGENTS.md`
