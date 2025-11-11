# CEA Demand Calculations - Detailed Guide

This document provides detailed explanations about demand calculations for human readers.

## Shading Systems: How They Work

### Automatic Shading Control

Shading systems (rollo, venetian blinds) automatically activate based on solar radiation levels to reduce cooling loads.

### Database Structure
**File**: `databases/{region}/ASSEMBLIES/ENVELOPE/ENVELOPE_SHADING.csv`

```csv
description,code,rf_sh
none,SHADING_AS0,1.0
rollo,SHADING_AS1,0.08
venetian blinds,SHADING_AS2,0.15
```

### Understanding rf_sh (Shading Reduction Factor)

The `rf_sh` parameter represents the fraction of solar radiation that passes through when blinds are activated:

- `rf_sh = 1.0` (no shading): 100% of solar radiation passes through
- `rf_sh = 0.08` (rollo): Only 8% passes through (blocks 92%)
- `rf_sh = 0.15` (venetian blinds): Only 15% passes through (blocks 85%)

### Activation Logic Details

**Location**: `cea/technologies/blinds.py`
**Applied in**: `cea/demand/building_solar.py:117-123`

The activation threshold of 300 W/m² comes from ISO 13790 standard for building energy calculations.

```python
def calc_blinds_activation(radiation, g_gl, Rf_sh):
    """
    Activate blinds when radiation > 300 W/m2 (ISO 13790 standard)

    Parameters:
    - radiation: Solar radiation [W/m2]
    - g_gl: Window g-value (solar factor, typically 0.4-0.7)
    - Rf_sh: Shading factor (from ENVELOPE_SHADING.csv)

    Returns:
    - Effective g-value accounting for shading
    """
    if radiation > 300:  # Threshold: 300 W/m2
        return g_gl * Rf_sh  # Blinds ACTIVATED - reduce solar gain
    else:
        return g_gl  # Blinds NOT ACTIVATED - full solar gain
```

### Example Scenario: Building with Venetian Blinds

Consider a building with venetian blinds (rf_sh = 0.15) and windows with g-value = 0.6:

| Time | Radiation (W/m²) | Blinds Status | Calculation | Effective G-value | Solar Gain |
|------|------------------|---------------|-------------|-------------------|------------|
| 8 AM | 150 | OFF | 0.6 | 0.6 | 60% passes |
| 12 PM | 600 | ON | 0.6 × 0.15 | 0.09 | 9% passes |
| 4 PM | 400 | ON | 0.6 × 0.15 | 0.09 | 9% passes |
| 6 PM | 200 | OFF | 0.6 | 0.6 | 60% passes |

### Key Points
- **Automatic activation**: No manual control modeled; purely based on radiation threshold
- **Hourly variation**: Blinds can activate/deactivate throughout the day
- **Impact on cooling**: Significantly reduces solar heat gain and thus cooling demand
- **Rollo vs. Venetian**: Rollo (0.08) is more effective than venetian blinds (0.15)
- **Standard compliance**: 300 W/m² threshold follows ISO 13790

## HVAC vs SUPPLY: Understanding the Separation

### Design Philosophy

CEA separates **distribution/emission** (HVAC) from **generation** (SUPPLY) to allow flexible system configurations and accurate cost modeling.

### HVAC Assemblies = Distribution/Emission Systems

**Location**: `ASSEMBLIES/HVAC/`

**What they define**:
- How energy is distributed within the building (ducts, pipes, pumps)
- How energy is emitted to spaces (radiators, diffusers, floor heating)
- Temperature setpoints and supply air temperatures
- System capacities (W/m²)
- Control strategies (constant volume, variable volume, etc.)

**Example - HVAC_COOLING.csv**:
```csv
description,code,Qcsmax_Wm2,dTcs_C,Tscs0_ahu_C,dTcs0_ahu_C
mini-split AC,HVAC_COOLING_AS2,150,0.7,6.5,9.0
central AC,HVAC_COOLING_AS3,500,0.5,6.5,9.0
```

**NO CAPEX/LT_yr columns!** These are included in SUPPLY costs.

**Used in**: `cea/demand/building_hvac.py`
**Purpose**: Determine thermal comfort and energy demand

### SUPPLY Assemblies = Generation Systems

**Location**: `ASSEMBLIES/SUPPLY/`

**What they define**:
- Where/how energy is generated (boiler room, chiller plant, etc.)
- Costs (CAPEX, O&M)
- Lifespans (LT_yr)
- Efficiency and performance
- Energy feedstock (electricity, natural gas, etc.)

**Example - SUPPLY_COOLING.csv**:
```csv
description,code,efficiency,CAPEX_USD2015kW,LT_yr,feedstock
Chiller+Tower,SUPPLY_COOLING_AS1,2.7,710,20,GRID
```

**HAS CAPEX/LT_yr columns!**

**Used in**: `cea/analysis/costs/system_costs.py`, `cea/analysis/lca/operation.py`
**Purpose**: Determine costs and emissions

### System Component Breakdown

**Cooling System Example**:
- **Chiller** (generates cold water): SUPPLY_COOLING ✅ (has costs)
- **Cooling tower** (heat rejection): SUPPLY_COOLING ✅ (included in chiller costs)
- **Chilled water pumps**: SUPPLY_COOLING ✅ (included in system costs)
- **Air Handling Unit** (distributes cold air): HVAC_COOLING ✅ (affects demand)
- **Ductwork**: HVAC_COOLING ✅ (affects distribution losses)
- **Ceiling diffusers** (emit cold air): HVAC_COOLING ✅ (affects emission losses)

**Heating System Example**:
- **Boiler** (generates hot water): SUPPLY_HEATING ✅ (has costs)
- **Hot water pumps**: SUPPLY_HEATING ✅ (included in system costs)
- **Radiators** (emit heat): HVAC_HEATING ✅ (affects demand)
- **Floor heating** (emit heat): HVAC_HEATING ✅ (affects demand)
- **Piping**: HVAC_HEATING ✅ (affects distribution losses)

### Data Flow Through the System

```
1. Building Properties + HVAC Assemblies
   ↓
   Determine: temperatures, flow rates, capacities

2. Demand Calculation
   ↓
   Calculate: energy needs (kWh) including all HVAC losses

3. SUPPLY Assemblies
   ↓
   Apply: costs, efficiencies, emissions to energy consumption

4. Cost Calculation
   ↓
   Compute: CAPEX + OPEX based on SUPPLY assemblies only
```

### Important Design Decision

**HVAC devices are NOT counted separately for lifespan and cost** in CEA.

**Why this design?**
1. **Simplification**: HVAC costs are typically included in SUPPLY CAPEX values
2. **Focus**: HVAC primarily affects energy demand, not cost structure
3. **Building-level**: Appropriate for building-level analysis (not component-level)
4. **Data availability**: SUPPLY CAPEX data is more readily available than detailed HVAC component costs

**Assumption**: SUPPLY CAPEX values are comprehensive and include associated distribution equipment costs.

## End Use vs Final Energy: Understanding Energy Flow

### The Two Types of Energy Columns

Demand output files contain two fundamentally different types of energy columns that serve different analytical purposes.

### End Use Demand (Q*_sys columns)

**Definition**: Useful energy needed at the point of use, including all HVAC system losses.

**Heating Example**:
```
Qhs_sys_kWh = End-use space heating demand
            = Qhs_sen_sys (sensible heat needed for space)
            + Qhs_em_ls (emission losses from radiators/diffusers)
            + Qhs_dis_ls (distribution losses from pipes/ducts)
```

**Cooling Example**:
```
Qcs_sys_kWh = End-use space cooling demand
            = Qcs_sen_sys (sensible cooling)
            + Qcs_lat_sys (latent cooling for dehumidification)
            + Qcs_em_ls (emission losses)
            + Qcs_dis_ls (distribution losses)
```

**What it means**: This is the energy the HVAC system needs to deliver to maintain thermal comfort.

### Final Energy Demand (GRID_*, NG_*, etc. columns)

**Definition**: Primary energy consumed from supply source, accounting for system efficiency.

**Formula**:
```python
Final Energy = End Use Demand / System Efficiency

# Example for heating:
GRID_hs = Qhs_sys / eff_hs  # If electric heating (e.g., heat pump)
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

**End Use Columns** (building needs):
```python
Qhs_sys_kWh          # End-use space heating
Qcs_sys_kWh          # End-use space cooling
Qww_sys_kWh          # End-use hot water (domestic hot water)
Qcdata_sys_kWh       # End-use data center cooling
Qcre_sys_kWh         # End-use refrigeration cooling
Qhpro_sys_kWh        # End-use process heating
Qcpro_sys_kWh        # End-use process cooling

# Aggregates
QH_sys_kWh = Qww_sys + Qhs_sys + Qhpro_sys  # Total heating
QC_sys_kWh = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys  # Total cooling
E_sys_kWh  # Total electricity end-use
```

**Final Energy Columns** (source consumption):
```python
# Electricity from grid
GRID_hs_kWh, GRID_cs_kWh, GRID_ww_kWh  # HVAC
GRID_l_kWh, GRID_a_kWh, GRID_v_kWh     # Lighting, appliances, ventilation
GRID_aux_kWh                            # Auxiliary equipment

# Natural gas
NG_hs_kWh, NG_ww_kWh

# District heating/cooling
DH_hs_kWh, DH_ww_kWh, DC_cs_kWh

# Other fuels
OIL_hs_kWh, COAL_hs_kWh, WOOD_hs_kWh
```

### Detailed Calculation Examples

**Scenario 1: Electric heat pump (COP = 3.0)**

| Step | Variable | Value | Formula | Explanation |
|------|----------|-------|---------|-------------|
| End-use demand | `Qhs_sys` | 10,000 kWh | Sensible + emission + distribution losses | Energy needed at building |
| System efficiency | `eff_hs` | 3.0 (COP) | From SUPPLY_HEATING.csv | Heat pump coefficient of performance |
| Final energy | `GRID_hs` | **3,333 kWh** | 10,000 / 3.0 | Electricity consumed from grid |

**Interpretation**: For every 1 kWh of electricity consumed, the heat pump delivers 3 kWh of heat.

**Scenario 2: Gas boiler (efficiency = 0.8)**

| Step | Variable | Value | Formula | Explanation |
|------|----------|-------|---------|-------------|
| End-use demand | `Qhs_sys` | 10,000 kWh | *Same as above* | Energy needed at building |
| System efficiency | `eff_hs` | 0.8 | From SUPPLY_HEATING.csv | Boiler combustion efficiency |
| Final energy | `NG_hs` | **12,500 kWh** | 10,000 / 0.8 | Natural gas consumed |

**Interpretation**: For every 1 kWh of natural gas consumed, the boiler delivers 0.8 kWh of heat (20% loss).

### Practical Example from Output File

```csv
name,Qhs_sys_kWh,GRID_hs_kWh,NG_hs_kWh,Qcs_sys_kWh,GRID_cs_kWh
B001,15000,5000,0,8000,2900
```

**Complete Interpretation**:

**Heating**:
- Building needs 15,000 kWh of heating delivered to spaces (`Qhs_sys`)
- System uses electricity from grid: 5,000 kWh (`GRID_hs`)
- Implied COP = 15,000 / 5,000 = **3.0** (likely a heat pump)
- No natural gas used (`NG_hs = 0`)

**Cooling**:
- Building needs 8,000 kWh of cooling delivered to spaces (`Qcs_sys`)
- Chiller consumes electricity: 2,900 kWh (`GRID_cs`)
- Implied COP = 8,000 / 2,900 = **2.76** (typical chiller efficiency)

**Energy Bills**:
- Total electricity consumption: 5,000 + 2,900 = 7,900 kWh
- At $0.15/kWh: $1,185 for heating + cooling

### Key Differences Table

| Aspect | End Use (Q*_sys) | Final Energy (GRID_*, NG_*) |
|--------|------------------|----------------------------|
| **Physical meaning** | Useful energy at building | Primary energy from source |
| **Includes** | HVAC losses (emission, distribution) | HVAC + generation efficiency losses |
| **Independent of** | Supply technology choice | — |
| **Affected by** | Building design, HVAC design | Supply system efficiency |
| **Example** | Qhs_sys = 1000 kWh | GRID_hs = 333 kWh (if COP=3) |
| **Used for** | HVAC system sizing | Energy bills, emissions, costs |
| **Constant across** | Different supply technologies | — |

### When to Use Each Column

**Use End-Use Columns (Q*_sys) for**:
- HVAC system sizing and design
- Thermal comfort analysis
- Building envelope performance comparison
- HVAC distribution system evaluation

**Use Final Energy Columns (GRID_*, NG_*) for**:
- Energy bill calculations
- Emissions calculations (multiply by emission factors)
- Cost analysis
- Primary energy consumption reporting
- Energy source comparison

### Common Mistakes to Avoid

❌ **Wrong**: Using end-use for energy bills
```python
# This ignores system efficiency!
energy_cost = df['Qhs_sys_kWh'] * electricity_price
```

✅ **Correct**: Using final energy for energy bills
```python
energy_cost = df['GRID_hs_kWh'] * electricity_price
```

❌ **Wrong**: Using final energy for system sizing
```python
# This already includes efficiency division!
boiler_capacity = df['GRID_hs_kWh'].max()
```

✅ **Correct**: Using end-use for system sizing
```python
boiler_capacity = df['Qhs_sys_kWh'].max()
```

## For More Information

- CEA documentation: https://docs.cityenergyanalyst.com
- Demand calculation scripts: `cea/demand/`
- Thermal loads calculation: `cea/demand/thermal_loads.py`
- Building HVAC: `cea/demand/building_hvac.py`
- Database structure: `cea/databases/AGENTS.md`
