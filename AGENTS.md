# CEA Database and Calculation Knowledge Base

This document contains frequently asked questions and detailed explanations about the City Energy Analyst (CEA) database structure, calculations, and relationships between different data files.

---

## Table of Contents

1. [Grid Electricity: Two Sources of Truth](#1-grid-electricity-two-sources-of-truth)
2. [CAPEX Usage in Cost Calculations](#2-capex-usage-in-cost-calculations)
3. [Shading Systems: Rollo and Venetian Blinds](#3-shading-systems-rollo-and-venetian-blinds)
4. [Components vs Assemblies Relationship](#4-components-vs-assemblies-relationship)
5. [HVAC vs SUPPLY Assemblies](#5-hvac-vs-supply-assemblies)
6. [End Use vs Final Energy Demand](#6-end-use-vs-final-energy-demand)

---

## 1. Grid Electricity: Two Sources of Truth

### Question
In `databases/sg/assemblies/supply/supply_electricity.csv`'s CAPEX_USD2015kW and in `components/feedstocks/feedstocks_library/grid.csv`'s opex_var_buy_usd2015kWh and opex_var_sell_usd2015kwh. I believe the two .csv files are two sources of truth for grid electricity. Can you check how are these two files being used?

### Answer

These are **two sources of truth** working together in a hierarchical manner:

#### **SUPPLY_ELECTRICITY.csv** (Assembly Level)
**Location**: `databases/{region}/ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv`

**Purpose**: Defines electricity supply **assemblies** (system configurations)

**Contains**:
```csv
code,feedstock,efficiency,CAPEX_USD2015kW,LT_yr,O&M_%,IR_%
SUPPLY_ELECTRICITY_AS1,GRID,0.99,62.1,20,1.3,1.3
```

**Fields**:
- `code`: Assembly identifier
- `feedstock`: References the energy source (e.g., "GRID")
- `efficiency`: System efficiency
- `CAPEX_USD2015kW`: **Capital expenditure** for infrastructure (electrical panels, transformers, grid connection)
- `LT_yr`, `O&M_%`, `IR_%`: Lifetime, maintenance costs, interest rate

**Used by**:
- LCA calculations (`cea/analysis/lca/operation.py:56`)
- Cost calculations (`cea/analysis/costs/system_costs.py:181`)
- Building supply systems (`cea/demand/building_properties/building_supply_systems.py:54`)

#### **GRID.csv** (Feedstock Level)
**Location**: `databases/{region}/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/GRID.csv`

**Purpose**: Defines the grid electricity **feedstock** properties (hourly data)

**Contains** (24 hourly rows):
```csv
hour,GHG_kgCO2MJ,Opex_var_buy_USD2015kWh,Opex_var_sell_USD2015kWh
0,0.136,0.17808,0.17808
1,0.136,0.17808,0.17808
...
```

**Fields**:
- `hour`: Hour of day (0-23)
- `GHG_kgCO2MJ`: **Emissions factor** for grid electricity
- `Opex_var_buy_USD2015kWh`: **Variable operating cost** to buy electricity
- `Opex_var_sell_USD2015kWh`: **Variable operating cost** to sell electricity

**Used by**:
- LCA calculations (loads all feedstocks including GRID)
- Cost calculations (loads all feedstocks including GRID)

#### **How They Work Together**:

```python
# Step 1: Load supply assemblies (including CAPEX)
factors_electricity = pd.read_csv('SUPPLY_ELECTRICITY.csv')
# Result: code=SUPPLY_ELECTRICITY_AS1, feedstock=GRID, CAPEX_USD2015kW=62.1

# Step 2: Load feedstocks (including OPEX and emissions)
factors_resources['GRID'] = pd.read_csv('GRID.csv')
# Result: Opex_var_buy_USD2015kWh=0.17808, GHG_kgCO2MJ=0.136

# Step 3: Merge them together
electricity_costs = factors_electricity.merge(factors_resources,
                                             left_on='feedstock', right_on='code')
# Result: Combined data with both CAPEX and OPEX
```

**Summary**:
- **SUPPLY_ELECTRICITY.csv's CAPEX** = Infrastructure costs (one-time investment)
- **GRID.csv's Opex_var_buy** = Energy purchase costs (ongoing operational)
- They **complement** each other rather than duplicate information

---

## 2. CAPEX Usage in Cost Calculations

### Question
Where is the CAPEX being used?

### Answer

**CAPEX_USD2015kW** from `SUPPLY_ELECTRICITY.csv` is used in **cost calculations** in `/cea/analysis/costs/system_costs.py`.

#### **Calculation Location** (line 107-109):

```python
result[service + '_capex_total_USD'] = (database[service + '0_kW'].values *
                                        database['efficiency'].values *
                                        database['CAPEX_USD2015kW'].values)
```

#### **What This Calculates**:
- **Total Capital Expenditure** for the electricity supply system
- Formula: `Peak Power (kW) × Efficiency × Unit CAPEX (USD2015/kW)`

#### **The CAPEX Flows Through These Calculations**:

1. **Total CAPEX** (line 107-109):
   ```python
   electricity_capex_total_USD = Peak_kW × efficiency × CAPEX_USD2015kW
   ```

2. **Fixed OPEX** (line 111) - Maintenance costs:
   ```python
   electricity_opex_fixed_USD = capex_total × O&M_% / 100
   ```

3. **Annualized CAPEX** (line 119-121):
   ```python
   electricity_capex_a_USD = calc_capex_annualized(capex_total, IR_%, LT_yr)
   ```

4. **Total Annualized Cost (TAC)** (line 135):
   ```python
   electricity_TAC_USD = opex_a_USD + capex_a_USD
   ```

#### **Summary**:
- **CAPEX_USD2015kW** = Infrastructure/connection costs per kW
- Used to calculate:
  - Initial infrastructure investment
  - Annual maintenance costs (O&M)
  - Annualized infrastructure costs (amortized over lifetime)
- For grid electricity with CAPEX = 62.1 USD2015/kW (Singapore), this represents the cost of electrical infrastructure per kW of peak power demand

---

## 3. Shading Systems: Rollo and Venetian Blinds

### Question
How is the rollo and venetian blinds inside envelope_shading.csv being used? How is shading calculated/activated?

### Answer

#### **File Structure**:
`ENVELOPE_SHADING.csv` contains:
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

#### **Blind Activation Logic** (`cea/technologies/blinds.py`):

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

#### **Applied to Solar Calculations** (`building_solar.py:117-123`):

```python
# Calculate total solar radiation on windows
I_sol_win = (windows_east + windows_west + windows_north + windows_south) * 1000  # in W

# Calculate shading factor for each hour
Fsh_win = calc_blinds_activation(I_sol_win, G_win, rf_sh)

# Apply shading to solar radiation
I_sol_win = I_sol_win * Fsh_win * (1 - F_F)
```

#### **Example: Building with Venetian Blinds (rf_sh = 0.15)**

| Time | Radiation (W/m²) | Blinds Status | Effective G-value | Solar Gain |
|------|------------------|---------------|-------------------|------------|
| Morning (low sun) | 150 | **OFF** | g_gl = 0.6 | 60% passes |
| Noon (high sun) | 600 | **ON** | g_gl × 0.15 = 0.09 | Only 9% passes |
| Evening (low sun) | 200 | **OFF** | g_gl = 0.6 | 60% passes |

#### **Key Points**:
- ✓ **Automatic activation** - No manual control needed
- ✓ **Threshold-based** - 300 W/m² triggers blinds (ISO 13790 standard)
- ✓ **Hourly variation** - Blinds open/close throughout the day
- ✓ **Affects cooling** - Reduces solar heat gain when activated
- ✓ **Rollo is more effective** (0.08) than venetian blinds (0.15) at blocking solar radiation

---

## 4. Components vs Assemblies Relationship

### Question
My understanding is .csv files in components/conversion make up the csv files in assemblies/supply. However, I saw Supply_hotwater.csv has electrical boiler while BOILERS.csv does have BO5. Aren't these two sources of truth? Or am I understanding it wrongly?

### Answer

These are **NOT two sources of truth** - they have **different purposes** and work together:

#### **1. COMPONENTS (e.g., BOILERS.csv) = Building Blocks**
**Location**: `COMPONENTS/CONVERSION/BOILERS.csv`

**Purpose**: Detailed technical specifications for individual equipment

**Example: BO5 (Electrical Boiler)**:
```csv
code: BO5
type: elec
fuel_code: E230AC
efficiency: 0.99
cap_min: 1 W
cap_max: 10,000,000,000 W
Detailed cost function: a=36931, b=254, c=0.91, d=-7740, e=0
LT_yr: 20
O&M_%: 5
```

**Used for**:
- Detailed optimization
- District energy system design
- Capacity-dependent cost curves

#### **2. ASSEMBLIES (e.g., SUPPLY_HOTWATER.csv) = Simplified System Packages**
**Location**: `ASSEMBLIES/SUPPLY/SUPPLY_HOTWATER.csv`

**Purpose**: Simplified system configurations for building-level analysis

**Example: SUPPLY_HOTWATER_AS1 (Electrical boiler)**:
```csv
description: Electrical boiler
code: SUPPLY_HOTWATER_AS1
feedstock: GRID
efficiency: 0.9
CAPEX_USD2015kW: 200 (simplified aggregate value)
LT_yr: 20
O&M_%: 5
```

**Used for**:
- Building demand calculations
- Baseline cost estimates

#### **Key Differences**:

| Aspect | COMPONENTS (BO5) | ASSEMBLIES (SUPPLY_HOTWATER_AS1) |
|--------|------------------|----------------------------------|
| **Purpose** | Detailed equipment specs | Simplified system package |
| **Cost Model** | Complex curve (a+bx+cx²...) | Single value (200 USD/kW) |
| **Efficiency** | 0.99 (detailed) | 0.9 (conservative/simplified) |
| **Used By** | Optimization, district systems | Building demand calculations |
| **Capacity** | Size-dependent | Aggregated/average |
| **Reference** | Component code (BO5) | May reference component |

#### **Why Both Exist**:

1. **Different Use Cases**:
   - **ASSEMBLIES**: Quick building-level assessments
   - **COMPONENTS**: Detailed system optimization

2. **Different Detail Levels**:
   - **ASSEMBLIES**: "What type of system does this building have?"
   - **COMPONENTS**: "What specific boiler model and size should we install?"

3. **Relationship**:
   - ASSEMBLIES *can reference* COMPONENTS via `primary_components` field
   - Example: `SUPPLY_HEATING_AS4` → `BO5` → Detailed BO5 specs

#### **For the Electrical Boiler Example**:

**SUPPLY_HOTWATER.csv (SG)**:
- Simplified: "electrical boiler, 90% efficient, costs 200 USD/kW"
- Used for building demand/cost when you just need aggregate values

**BOILERS.csv (SG)**:
- Detailed: Exact cost formula changes with boiler size
- Used when optimizing which size boiler to install

#### **Conclusion**:
❌ **NOT two sources of truth** (not duplicates)
✅ **Two levels of abstraction** working together:
- **ASSEMBLIES** = High-level building descriptions
- **COMPONENTS** = Low-level equipment specifications

---

## 5. HVAC vs SUPPLY Assemblies

### Question
What is the difference between HVAC and SUPPLY? So the devices in HVAC is not counted for life span and cost?

### Answer

You've identified a **critical design choice** in CEA!

#### **1. HVAC Assemblies = Distribution/Emission Systems (Inside Building)**

**Location**: `ASSEMBLIES/HVAC/`

**What they define**:
- **How** energy is distributed and emitted **within the building**
- Temperature setpoints and supply air temperatures
- System capacities (W/m²)
- Control strategies

**Example - HVAC_COOLING.csv**:
```csv
description,code,Qcsmax_Wm2,dTcs_C,Tscs0_ahu_C,dTcs0_ahu_C
mini-split AC,HVAC_COOLING_AS2,150,0.7,6.5,9.0
central AC,HVAC_COOLING_AS3,500,0.5,6.5,9.0
```

**❌ No CAPEX/LT_yr columns!**

#### **2. SUPPLY Assemblies = Generation Systems (Energy Production)**

**Location**: `ASSEMBLIES/SUPPLY/`

**What they define**:
- **Where/how** energy is generated
- Costs (CAPEX, O&M)
- Lifespans (LT_yr)
- Efficiency
- Feedstock

**Example - SUPPLY_COOLING.csv**:
```csv
description,code,efficiency,CAPEX_USD2015kW,LT_yr,feedstock
Chiller+Tower,SUPPLY_COOLING_AS1,2.7,710,20,GRID
```

**✅ Has CAPEX/LT_yr columns!**

#### **Analogy**:

Think of a building's cooling system:

| Component | HVAC | SUPPLY |
|-----------|------|--------|
| **Chiller** (generates cold water) | ❌ Not here | ✅ SUPPLY_COOLING |
| **Air Handling Unit** (distributes cold air) | ✅ HVAC_COOLING | ❌ Not here |
| **Ceiling diffusers** (emits cold air) | ✅ HVAC_COOLING | ❌ Not here |

Or for heating:

| Component | HVAC | SUPPLY |
|-----------|------|--------|
| **Boiler** (generates hot water) | ❌ Not here | ✅ SUPPLY_HEATING |
| **Radiators** (emit heat) | ✅ HVAC_HEATING | ❌ Not here |
| **Floor heating** (emit heat) | ✅ HVAC_HEATING | ❌ Not here |

#### **How Each is Used**:

**HVAC (Emission/Distribution)**:
- **Used in**: Demand calculations (`building_hvac.py`)
- **Purpose**: Determine **thermal comfort** and **energy demand**
  - What temperature water/air is needed?
  - How much capacity is needed per m²?
  - What control strategy?
- **NOT used for**: Cost calculations ❌
- **NOT tracked**: Lifespan, CAPEX, OPEX ❌

**SUPPLY (Generation)**:
- **Used in**: Cost calculations (`system_costs.py`), LCA (`operation.py`)
- **Purpose**: Determine **costs** and **emissions**
  - How much does the system cost?
  - How long does it last?
  - What's the efficiency?
  - What fuel/energy source?
- **Used for**: CAPEX, OPEX, TAC calculations ✅

#### **The Data Flow**:

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

#### **Answer to Your Question**:

> **"Are HVAC devices not counted for lifespan and cost?"**

**✅ CORRECT!** HVAC assemblies are **NOT included** in cost/lifespan calculations.

**Why this design choice?**

1. **HVAC costs are typically included in SUPPLY costs**
   - When you buy a "chiller system," the price includes air handlers, ductwork, etc.
   - SUPPLY_COOLING CAPEX is an **aggregate** that includes generation + distribution

2. **HVAC primarily affects energy demand, not cost**
   - Ceiling cooling vs floor heating affects **how much energy** you need
   - But the **boiler cost** is tracked separately in SUPPLY

3. **Simplification for building-level analysis**
   - Detailed HVAC component costing is complex
   - CEA focuses on **supply system costs** as the main capital investment

#### **Conclusion**:

**HVAC devices are NOT counted for lifespan and cost** in the current CEA implementation. This is a deliberate design choice where:
- **HVAC** = Technical parameters for demand simulation
- **SUPPLY** = Financial parameters for cost/LCA analysis

The assumption is that SUPPLY CAPEX values are **comprehensive** and include associated distribution equipment.

---

## 6. End Use vs Final Energy Demand

### Question
How is end use demand and final use demand differentiated in the demand output file's columns?

### Answer

#### **Column Naming Pattern**:

| Type | Prefix | Example | Unit | Description |
|------|--------|---------|------|-------------|
| **End Use** | `Q*_sys` | `Qhs_sys_kWh` | kWh | Energy needed **at the building** |
| **Final Energy** | `GRID_*`, `NG_*`, `OIL_*`, etc. | `GRID_hs_kWh`, `NG_hs_kWh` | kWh | Energy consumed **from source** |

#### **A. End Use Demand (Q*_sys columns)**:

These represent **useful energy** needed at the point of use, **including all losses**:

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

**Key Point**: `Q*_sys` = What the **HVAC system** needs to deliver

#### **B. Final Energy Demand (GRID_*, NG_*, etc. columns)**:

These represent **primary energy** consumed from the **supply source**, accounting for **system efficiency**:

**Formula**:
```python
Final Energy = End Use Demand / System Efficiency

# Example for heating:
GRID_hs = Qhs_sys / eff_hs  # If electric heating
NG_hs = Qhs_sys / eff_hs    # If natural gas boiler
```

**From the code** (`thermal_loads.py`):
```python
if energy_source == "GRID":
    E_hs = Qhs_sys / efficiency_average_year
elif energy_source == "NATURALGAS":
    NG_hs = Qhs_sys / efficiency_average_year
```

#### **Complete Column Categories in Demand Output**:

**End Use Columns (Q*_sys)**:
```
Qhs_sys_kWh          # End-use space heating
Qcs_sys_kWh          # End-use space cooling
Qww_sys_kWh          # End-use hot water
Qcdata_sys_kWh       # End-use data center cooling
Qcre_sys_kWh         # End-use refrigeration cooling
Qhpro_sys_kWh        # End-use process heating
Qcpro_sys_kWh        # End-use process cooling

# Aggregates
QH_sys_kWh = Qww_sys + Qhs_sys + Qhpro_sys  # Total heating end-use
QC_sys_kWh = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys  # Total cooling end-use
E_sys_kWh  # Total electricity end-use
```

**Final Energy Columns (by fuel/source)**:
```
# Electricity from grid
GRID_hs_kWh          # Grid electricity for space heating
GRID_cs_kWh          # Grid electricity for space cooling
GRID_ww_kWh          # Grid electricity for hot water
GRID_l_kWh           # Grid electricity for lighting
GRID_a_kWh           # Grid electricity for appliances
GRID_v_kWh           # Grid electricity for ventilation
GRID_aux_kWh         # Grid electricity for auxiliary

# Natural gas
NG_hs_kWh            # Natural gas for space heating
NG_ww_kWh            # Natural gas for hot water

# District heating/cooling
DH_hs_kWh            # District heating for space heating
DH_ww_kWh            # District heating for hot water
DC_cs_kWh            # District cooling for space cooling

# Other fuels
OIL_hs_kWh           # Oil for space heating
COAL_hs_kWh          # Coal for space heating
WOOD_hs_kWh          # Wood for space heating
```

#### **The Relationship - Example Calculation**:

**Scenario 1**: Building with electric heat pump for space heating

| Step | Variable | Value | Formula |
|------|----------|-------|---------|
| 1. End-use demand | `Qhs_sys` | 10,000 kWh | Sensible + losses |
| 2. System efficiency | `eff_hs` | 3.0 (COP) | From SUPPLY database |
| 3. Final energy | `GRID_hs` | **3,333 kWh** | Qhs_sys / eff_hs |

**Scenario 2**: Same building with gas boiler

| Step | Variable | Value | Formula |
|------|----------|-------|---------|
| 1. End-use demand | `Qhs_sys` | 10,000 kWh | *Same* |
| 2. System efficiency | `eff_hs` | 0.8 | From SUPPLY database |
| 3. Final energy | `NG_hs` | **12,500 kWh** | Qhs_sys / eff_hs |

#### **Key Differences Summary**:

| Aspect | End Use (Q*_sys) | Final Energy (GRID_*, NG_*) |
|--------|------------------|----------------------------|
| **Represents** | Useful energy at building | Primary energy from source |
| **Includes** | All HVAC losses | System efficiency losses too |
| **Units** | kWh (thermal or electric) | kWh (always primary energy) |
| **Independent of** | Supply technology | — |
| **Dependent on** | Building & HVAC | **Supply system efficiency** |
| **Example (heating)** | Qhs_sys = 1000 kWh | GRID_hs = 333 kWh (if COP=3) |
| **Used for** | Sizing HVAC systems | Energy bills & costs |

#### **Practical Example from Output File**:

```csv
name,Qhs_sys_kWh,GRID_hs_kWh,NG_hs_kWh,Qcs_sys_kWh,GRID_cs_kWh
B001,15000,5000,0,8000,2900
```

**Interpretation**:
- Building needs **15,000 kWh** of heating (`Qhs_sys`)
- Supplied by electric system using **5,000 kWh** from grid (`GRID_hs`)
  - Implies efficiency = 15000/5000 = **3.0 COP**
- No natural gas used (`NG_hs = 0`)
- Building needs **8,000 kWh** of cooling (`Qcs_sys`)
- Supplied by chiller using **2,900 kWh** from grid (`GRID_cs`)
  - Implies efficiency = 8000/2900 = **2.76 COP**

#### **Column Naming Rule**:
- ✅ **`Q*_sys_*`** = End-use demand (what building needs)
- ✅ **`GRID_*`, `NG_*`, `OIL_*`, etc.** = Final energy (what you pay for)

#### **Relationship**:
```
Final Energy = End Use Demand / System Efficiency
```

This distinction is crucial for:
- **Energy bills** → Use final energy columns
- **System sizing** → Use end-use demand columns
- **Emissions** → Use final energy columns × emission factors

---

## Document Metadata

- **Created**: 2025-01-08
- **Purpose**: Knowledge base for CEA database structure and calculations
- **Intended Use**: Static Q&A reference or LLM agent training
- **Source**: Interactive Q&A session covering database relationships and calculation methodologies
- **CEA Version**: Compatible with CEA 4.x architecture

---

## Usage Notes

This document can be used to:
1. Train LLM agents for CEA-specific questions
2. Create a static FAQ/documentation page
3. Onboard new developers to understand CEA's database architecture
4. Reference when troubleshooting database-related issues
5. Understand the relationship between different CSV files in the CEA database structure

For questions not covered here, refer to:
- CEA documentation: https://docs.cityenergyanalyst.com
- CEA schemas: `cea/schemas.yml`
- Database documentation: `cea/databases/{region}/documentation.md`
