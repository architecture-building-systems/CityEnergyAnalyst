# Demand Calculations

## Key Concepts

**HVAC vs SUPPLY**: CEA separates distribution/emission (HVAC) from generation (SUPPLY)
- **HVAC**: How energy is distributed/emitted (no costs)
- **SUPPLY**: Where energy is generated (CAPEX, OPEX, emissions)

**End Use vs Final Energy**:
- **End Use** (`Q*_sys`): Energy needed at building (includes HVAC losses)
- **Final Energy** (`GRID_*`, `NG_*`): Energy consumed from source (includes efficiency)

## Main Patterns

### Shading Activation (`blinds.py`)

```python
def calc_blinds_activation(radiation, g_gl, Rf_sh):
    """Activate when radiation > 300 W/m² (ISO 13790)"""
    if radiation > 300:
        return g_gl * Rf_sh  # Blinds ON - reduce solar gain
    else:
        return g_gl          # Blinds OFF - full solar gain
```

**Database**: `ASSEMBLIES/ENVELOPE/ENVELOPE_SHADING.csv`

| Code | Description | rf_sh | Effect |
|------|-------------|-------|--------|
| SHADING_AS0 | None | 1.0 | 0% blocked |
| SHADING_AS1 | Rollo | 0.08 | 92% blocked |
| SHADING_AS2 | Venetian | 0.15 | 85% blocked |

**Applied**: `building_solar.py:117-123`

### HVAC vs SUPPLY System Mapping

| Component | Type | Database | Has Costs? |
|-----------|------|----------|-----------|
| Chiller | Generation | SUPPLY_COOLING | ✅ |
| Boiler | Generation | SUPPLY_HEATING | ✅ |
| AHU | Distribution | HVAC_COOLING | ❌ |
| Radiators | Emission | HVAC_HEATING | ❌ |

**Data Flow**:
```
HVAC (temperatures, capacities) → Demand (kWh) → SUPPLY (costs, emissions)
```

**Key**: HVAC affects energy demand only; SUPPLY holds all costs/emissions

### Output Columns: End Use vs Final Energy

| Type | Prefix | Includes | Formula | Use For |
|------|--------|----------|---------|---------|
| **End Use** | `Q*_sys` | HVAC losses | Sensible + emission + distribution losses | System sizing |
| **Final Energy** | `GRID_*`, `NG_*` | Efficiency losses | `Q*_sys / efficiency` | Bills, emissions |

**Key columns**:
```python
# End Use (building needs) - System sizing
Qhs_sys_kWh    # Space heating demand (radiators, AHU heating coils)
Qww_sys_kWh    # Domestic hot water demand (DHW, taps, showers)
Qhpro_sys_kWh  # Process heating demand (industrial processes)
QH_sys_kWh     # TOTAL heating = Qhs_sys_kWh + Qww_sys_kWh + Qhpro_sys_kWh

Qcs_sys_kWh    # Space cooling demand (chillers, AHU cooling coils)
Qcre_sys_kWh   # Refrigeration cooling demand
Qcdata_sys_kWh # Data centre cooling demand
Qcpro_sys_kWh  # Process cooling demand (industrial processes)
QC_sys_kWh     # TOTAL cooling = Qcs_sys_kWh + Qcre_sys_kWh + Qcdata_sys_kWh + Qcpro_sys_kWh

# Final Energy (source consumption) - Bills, emissions
GRID_hs_kWh, NG_hs_kWh, DH_hs_kWh  # Space heating sources
GRID_ww_kWh, NG_ww_kWh, DH_ww_kWh  # DHW sources
GRID_cs_kWh, DC_cs_kWh             # Cooling sources
```

**IMPORTANT**:
- `QH_sys_kWh` = total heating (space + DHW + process)
- `QC_sys_kWh` = total cooling (space + refrigeration + data + process)
- DH networks serve ALL heating services (use `QH_sys_kWh`)
- DC networks serve ALL cooling services (use `QC_sys_kWh`)

**Calculation** (`thermal_loads.py`):
```python
if energy_source == "GRID":
    GRID_hs = Qhs_sys / efficiency_average_year
elif energy_source == "NATURALGAS":
    NG_hs = Qhs_sys / efficiency_average_year
```

## Example

**Output file**:
```csv
name,Qhs_sys_kWh,GRID_hs_kWh,Qcs_sys_kWh,GRID_cs_kWh
B001,15000,5000,8000,2900
```

**Interpretation**:
- Building needs 15,000 kWh heating → uses 5,000 kWh grid (COP = 3.0)
- Building needs 8,000 kWh cooling → uses 2,900 kWh grid (COP = 2.76)

## ✅ DO

```python
# Use end-use for HVAC sizing
hvac_capacity = df['Qhs_sys_kWh'].max()

# Use final energy for costs/emissions
energy_cost = df['GRID_hs_kWh'] * electricity_price
emissions = df['GRID_hs_kWh'] * emission_factor
```

## ❌ DON'T

```python
# Don't use end-use for energy bills (ignores efficiency)
cost = df['Qhs_sys_kWh'] * price  # WRONG

# Don't use final energy for system sizing (already divided by efficiency)
capacity = df['GRID_hs_kWh'].max()  # WRONG
```

## Related Files
- `cea/demand/thermal_loads.py` - End use → final energy conversion
- `cea/demand/building_hvac.py` - HVAC assemblies (temperatures, capacities)
- `cea/technologies/blinds.py` - Shading activation logic
- `cea/demand/building_solar.py:117-123` - Shading application
- `cea/databases/AGENTS.md` - HVAC vs SUPPLY distinction
