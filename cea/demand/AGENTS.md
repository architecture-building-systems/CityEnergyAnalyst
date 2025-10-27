# CEA Demand Calculations Knowledge

This document explains demand calculations, HVAC systems, shading, and energy output columns in CEA.

---

## Shading Systems: Rollo and Venetian Blinds

### Overview
Shading systems automatically activate based on solar radiation to reduce cooling loads.

### Database Structure
**File**: `databases/{region}/ASSEMBLIES/ENVELOPE/ENVELOPE_SHADING.csv`

```csv
description,code,rf_sh
none,SHADING_AS0,1.0
rollo,SHADING_AS1,0.08
venetian blinds,SHADING_AS2,0.15
```

**rf_sh** = Shading reduction factor:
- `1.0` = No shading (100% of solar radiation passes through)
- `0.08` = Rollo blocks 92% of solar radiation
- `0.15` = Venetian blinds block 85% of solar radiation

### Activation Logic

**Location**: `cea/technologies/blinds.py`

```python
def calc_blinds_activation(radiation, g_gl, Rf_sh):
    """
    Activate blinds when radiation > 300 W/m2 (ISO 13790 standard)

    Parameters:
    - radiation: Solar radiation [W/m2]
    - g_gl: Window g-value (solar factor)
    - Rf_sh: Shading factor (from ENVELOPE_SHADING.csv)
    """
    if radiation > 300:  # Threshold: 300 W/m2
        return g_gl * Rf_sh  # Blinds ACTIVATED - reduce solar gain
    else:
        return g_gl  # Blinds NOT ACTIVATED - full solar gain
```

**Applied in**: `cea/demand/building_solar.py:117-123`

### Example: Building with Venetian Blinds (rf_sh = 0.15)

| Time | Radiation (W/m²) | Blinds Status | Effective G-value | Solar Gain |
|------|------------------|---------------|-------------------|------------|
| Morning | 150 | OFF | g_gl = 0.6 | 60% passes |
| Noon | 600 | ON | g_gl × 0.15 = 0.09 | 9% passes |
| Evening | 200 | OFF | g_gl = 0.6 | 60% passes |

### Key Points
- Automatic activation (no manual control)
- Threshold-based: 300 W/m² triggers blinds (ISO 13790)
- Hourly variation throughout the day
- Reduces solar heat gain and cooling demand
- Rollo (0.08) more effective than venetian blinds (0.15)

---

## HVAC vs SUPPLY Assemblies

### Critical Design Distinction
CEA separates **distribution/emission** (HVAC) from **generation** (SUPPLY).

### HVAC Assemblies = Distribution/Emission Systems

**Location**: `ASSEMBLIES/HVAC/`

**What they define**:
- How energy is distributed and emitted within the building
- Temperature setpoints and supply air temperatures
- System capacities (W/m²)
- Control strategies

**Example - HVAC_COOLING.csv**:
```csv
description,code,Qcsmax_Wm2,dTcs_C,Tscs0_ahu_C,dTcs0_ahu_C
mini-split AC,HVAC_COOLING_AS2,150,0.7,6.5,9.0
central AC,HVAC_COOLING_AS3,500,0.5,6.5,9.0
```

**NO CAPEX/LT_yr columns!**

**Used in**: `cea/demand/building_hvac.py`
**Purpose**: Determine thermal comfort and energy demand

### SUPPLY Assemblies = Generation Systems

**Location**: `ASSEMBLIES/SUPPLY/`

**What they define**:
- Where/how energy is generated
- Costs (CAPEX, O&M)
- Lifespans (LT_yr)
- Efficiency
- Feedstock

**Example - SUPPLY_COOLING.csv**:
```csv
description,code,efficiency,CAPEX_USD2015kW,LT_yr,feedstock
Chiller+Tower,SUPPLY_COOLING_AS1,2.7,710,20,GRID
```

**HAS CAPEX/LT_yr columns!**

**Used in**: `cea/analysis/costs/system_costs.py`, `cea/analysis/lca/operation.py`
**Purpose**: Determine costs and emissions

### System Component Mapping

**Cooling System**:
| Component | HVAC | SUPPLY |
|-----------|------|--------|
| Chiller (generates cold water) | ❌ | ✅ SUPPLY_COOLING |
| Air Handling Unit (distributes) | ✅ HVAC_COOLING | ❌ |
| Ceiling diffusers (emits) | ✅ HVAC_COOLING | ❌ |

**Heating System**:
| Component | HVAC | SUPPLY |
|-----------|------|--------|
| Boiler (generates hot water) | ❌ | ✅ SUPPLY_HEATING |
| Radiators (emit heat) | ✅ HVAC_HEATING | ❌ |
| Floor heating (emit heat) | ✅ HVAC_HEATING | ❌ |

### Data Flow
```
Building Properties
     ↓
1. HVAC assemblies → Determine temperatures & capacities
     ↓
2. Demand calculation → Calculate energy needs (kWh)
     ↓
3. SUPPLY assemblies → Apply costs to energy consumption
     ↓
4. Cost calculation → CAPEX + OPEX based on SUPPLY only
```

### Important
**HVAC devices are NOT counted for lifespan and cost** in CEA.

**Why?**
1. HVAC costs typically included in SUPPLY costs
2. HVAC primarily affects energy demand, not cost
3. Simplification for building-level analysis

**Assumption**: SUPPLY CAPEX values are comprehensive and include associated distribution equipment.

---

## End Use vs Final Energy Demand

### Overview
Demand output files contain two types of energy columns that serve different purposes.

### Column Naming Pattern

| Type | Prefix | Example | Description |
|------|--------|---------|-------------|
| **End Use** | `Q*_sys` | `Qhs_sys_kWh` | Energy needed **at the building** |
| **Final Energy** | `GRID_*`, `NG_*`, `OIL_*` | `GRID_hs_kWh` | Energy consumed **from source** |

### End Use Demand (Q*_sys columns)

Represents **useful energy** needed at point of use, **including all losses**.

**Heating Example**:
```
Qhs_sys_kWh = End-use space heating demand
            = Qhs_sen_sys (sensible heat)
            + Qhs_em_ls (emission losses)
            + Qhs_dis_ls (distribution losses)
```

**Cooling Example**:
```
Qcs_sys_kWh = End-use space cooling demand
            = Qcs_sen_sys (sensible cooling)
            + Qcs_lat_sys (latent cooling)
            + Qcs_em_ls (emission losses)
            + Qcs_dis_ls (distribution losses)
```

**What it means**: Energy the HVAC system needs to deliver.

### Final Energy Demand (GRID_*, NG_*, etc. columns)

Represents **primary energy** consumed from supply source, accounting for **system efficiency**.

**Formula**:
```python
Final Energy = End Use Demand / System Efficiency

# Example for heating:
GRID_hs = Qhs_sys / eff_hs  # If electric heating
NG_hs = Qhs_sys / eff_hs    # If natural gas boiler
```

**From code** (`cea/demand/thermal_loads.py`):
```python
if energy_source == "GRID":
    E_hs = Qhs_sys / efficiency_average_year
elif energy_source == "NATURALGAS":
    NG_hs = Qhs_sys / efficiency_average_year
```

### Complete Column Categories

**End Use Columns**:
```python
Qhs_sys_kWh          # End-use space heating
Qcs_sys_kWh          # End-use space cooling
Qww_sys_kWh          # End-use hot water
Qcdata_sys_kWh       # End-use data center cooling
Qcre_sys_kWh         # End-use refrigeration cooling
Qhpro_sys_kWh        # End-use process heating
Qcpro_sys_kWh        # End-use process cooling

# Aggregates
QH_sys_kWh = Qww_sys + Qhs_sys + Qhpro_sys
QC_sys_kWh = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys
E_sys_kWh  # Total electricity end-use
```

**Final Energy Columns**:
```python
# Electricity from grid
GRID_hs_kWh, GRID_cs_kWh, GRID_ww_kWh
GRID_l_kWh, GRID_a_kWh, GRID_v_kWh, GRID_aux_kWh

# Natural gas
NG_hs_kWh, NG_ww_kWh

# District heating/cooling
DH_hs_kWh, DH_ww_kWh, DC_cs_kWh

# Other fuels
OIL_hs_kWh, COAL_hs_kWh, WOOD_hs_kWh
```

### Example Calculation

**Scenario 1: Electric heat pump (COP = 3.0)**
| Step | Variable | Value | Formula |
|------|----------|-------|---------|
| End-use demand | `Qhs_sys` | 10,000 kWh | Sensible + losses |
| System efficiency | `eff_hs` | 3.0 (COP) | From SUPPLY database |
| Final energy | `GRID_hs` | **3,333 kWh** | Qhs_sys / eff_hs |

**Scenario 2: Gas boiler (efficiency = 0.8)**
| Step | Variable | Value | Formula |
|------|----------|-------|---------|
| End-use demand | `Qhs_sys` | 10,000 kWh | *Same* |
| System efficiency | `eff_hs` | 0.8 | From SUPPLY database |
| Final energy | `NG_hs` | **12,500 kWh** | Qhs_sys / eff_hs |

### Practical Example from Output File

```csv
name,Qhs_sys_kWh,GRID_hs_kWh,NG_hs_kWh,Qcs_sys_kWh,GRID_cs_kWh
B001,15000,5000,0,8000,2900
```

**Interpretation**:
- Building needs 15,000 kWh of heating (`Qhs_sys`)
- Electric system uses 5,000 kWh from grid (`GRID_hs`)
  - Implies COP = 15000/5000 = **3.0**
- No natural gas used (`NG_hs = 0`)
- Building needs 8,000 kWh of cooling (`Qcs_sys`)
- Chiller uses 2,900 kWh from grid (`GRID_cs`)
  - Implies COP = 8000/2900 = **2.76**

### Key Differences Summary

| Aspect | End Use (Q*_sys) | Final Energy (GRID_*, NG_*) |
|--------|------------------|----------------------------|
| **Represents** | Useful energy at building | Primary energy from source |
| **Includes** | All HVAC losses | System efficiency losses too |
| **Independent of** | Supply technology | — |
| **Example** | Qhs_sys = 1000 kWh | GRID_hs = 333 kWh (COP=3) |
| **Used for** | Sizing HVAC systems | Energy bills & costs |

### When to Use Each

**Energy bills** → Use final energy columns
**System sizing** → Use end-use demand columns
**Emissions** → Use final energy columns × emission factors

---

## Quick Reference

**Shading activation**: 300 W/m² threshold (ISO 13790)
**HVAC vs SUPPLY**: HVAC = distribution, SUPPLY = generation (with costs)
**End Use vs Final**: Q*_sys = building needs, GRID_*/NG_* = energy purchased

---

**For more information, see**:
- CEA documentation: https://docs.cityenergyanalyst.com
- Demand calculation scripts: `cea/demand/`
- Database structure: `cea/databases/AGENTS.md`
