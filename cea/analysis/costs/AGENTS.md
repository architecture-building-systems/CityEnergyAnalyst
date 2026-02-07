# Cost Calculations

## Main API

**`calc_capex_annualized(capex_total, IR_%, LT_yr) → float`** - Convert total CAPEX to annual cost

**`get_component_codes_from_categories(locator, component_categories, network_type) → list[str]`** - Convert category names to component codes from database

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

## District Network Component Selection

### ✅ DO: Build explicit component selection based on network type

```python
# For DC networks: only cooling + heat rejection
if network_type == 'DC':
    cooling_cats = ['VAPOR_COMPRESSION_CHILLERS']  # Exclude absorption chillers for baseline
    heat_rejection_cats = ['COOLING_TOWERS']

    # Convert categories to actual codes from database
    # Filter by peak demand to only include codes that can handle the required capacity
    cooling_codes = get_component_codes_from_categories(locator, cooling_cats, network_type, peak_demand_kw)
    heat_rejection_codes = get_component_codes_from_categories(locator, heat_rejection_cats, network_type, peak_demand_kw)

    # For baseline costs, use only FIRST viable component per category (simple system)
    cooling_primary = cooling_codes[:1]  # e.g., ['CH1'] only
    heat_rejection_tertiary = heat_rejection_codes[:1]  # e.g., ['CT1'] only

    # Build explicit selection dict
    user_component_selection = {
        'primary': cooling_primary,
        'secondary': [],
        'tertiary': heat_rejection_tertiary
    }

# For DH networks: only heating
elif network_type == 'DH':
    heating_cats = ['BOILERS', 'HEAT_PUMPS']
    heating_codes = get_component_codes_from_categories(locator, heating_cats, network_type, peak_demand_kw)

    # For baseline costs, use only FIRST viable component
    heating_primary = heating_codes[:1]  # e.g., ['BO1'] only

    user_component_selection = {
        'primary': heating_primary,
        'secondary': [],
        'tertiary': []
    }
```

**Key principles for baseline costs:**
1. **Exclude absorption chillers** - They require heat sources (T100W) in secondary category, adding complexity
2. **Filter by peak demand** - Only include components with capacity >= peak demand
3. **Select first component only** - Baseline is a simple system, not an optimized mix (CH1 only, not CH1+CH2)

### ❌ DON'T: Pass None to SupplySystemStructure for district networks

```python
# ❌ This includes ALL components from database regardless of network type
system_structure = SupplySystemStructure(
    user_component_selection=None,  # BAD: DC network gets heating components too!
    target_building_or_network=network_id
)
```

**Why**: When `user_component_selection=None`, SupplySystemStructure loads all available components from the database, causing DC networks to include heating components (boilers, furnaces) which leads to validation errors in CapacityIndicatorVector.

## ❌ DON'T

```python
# Don't confuse CAPEX (infrastructure) with variable OPEX (energy purchase)
# Don't use COMPONENTS for building-level cost estimates
# Don't forget to annualize CAPEX before comparing with annual OPEX
# Don't filter CapacityIndicatorVector after creation - this breaks dependency chains
```

## Baseline Costs: 6-Case Building Connectivity Logic

The `baseline_costs.py` module implements a 6-case logic system to determine how buildings receive energy services and which supply assemblies to use.

### Case 1: Standalone-only mode (network-name = "(none)")
- **Triggers when**: User selects "(none)" or leaves network-name empty
- **Building connectivity**: ALL buildings treated as standalone
- **Service provision**:
  - Cooling: Building-scale (standalone)
  - Heating: Building-scale (standalone)
  - DHW: Building-scale (standalone)
- **Supply system selection**:
  1. Check Building Properties/Supply for each service
  2. If DISTRICT-scale code found:
     - Config parameter has value → Use BUILDING-scale from config (fallback)
     - Config parameter empty → Keep DISTRICT code (⚠️ may cause error)
  3. If BUILDING-scale code → Use it directly
- **Cost output**: All building-scale costs, zero district-scale costs
- **Use case**: Initial baseline without networks, all-standalone comparison scenarios

### Case 2: Building IN selected network
- **Note**: Case 2 is embedded in Cases 4, 5, 6 for the services that come from networks
- Services from district network have no standalone calculation
- No fallback needed (building doesn't provide those services)

### Case 3: Building NOT in network
- **Triggers when**: Building not found in network layout nodes.shp
- **Service provision**: Same as Case 1 (all standalone)
- **Supply system selection**: Same fallback logic as Case 1
- **Use case**: Buildings outside network coverage, future expansion areas

### Case 4: Building in BOTH DC and DH networks
- **Building connectivity**: Found in both DC/nodes.shp and DH/nodes.shp
- **Service provision**:
  - Cooling: District-scale (from DC network)
  - Heating: District-scale (from DH network)
  - DHW: District-scale (from DH network)
- **Supply system selection**:
  - Cooling: `filter_supply_code_by_scale(config.supply_type_cs, is_standalone=False)` → DISTRICT
  - Heating: `filter_supply_code_by_scale(config.supply_type_hs, is_standalone=False)` → DISTRICT
  - DHW: `filter_supply_code_by_scale(config.supply_type_dhw, is_standalone=False)` → DISTRICT
- **Fallback**: None needed (no standalone services)
- **Cost output**: All district-scale costs, zero building-scale costs
- **Use case**: Dense urban areas with full district energy coverage

### Case 5: Building in DC network only
- **Building connectivity**: In DC/nodes.shp, NOT in DH/nodes.shp
- **Service provision**:
  - Cooling: District-scale (from DC network)
  - Heating: Building-scale (standalone)
  - DHW: Building-scale (standalone)
- **Supply system selection**:
  - Cooling: Config filtered to DISTRICT-scale
  - Heating: Check Building Properties/Supply with fallback logic (Case 1)
  - DHW: Check Building Properties/Supply with fallback logic (Case 1)
- **Cost output**: Mixed - district cooling costs + building heating/DHW costs
- **Use case**: Cooling-dominant climates (Singapore, Middle East), phased deployment

### Case 6: Building in DH network only
- **Building connectivity**: In DH/nodes.shp, NOT in DC/nodes.shp
- **Service provision**:
  - Cooling: Building-scale (standalone)
  - Heating: District-scale (from DH network)
  - DHW: District-scale (from DH network)
- **Supply system selection**:
  - Cooling: Check Building Properties/Supply with fallback logic (Case 1)
  - Heating: Config filtered to DISTRICT-scale
  - DHW: Config filtered to DISTRICT-scale
- **Cost output**: Mixed - building cooling costs + district heating/DHW costs
- **Use case**: Heating-dominant climates (Northern Europe, North America)

### Config Parameter Filtering

**`filter_supply_code_by_scale(locator, supply_codes, category, is_standalone)`**

Behavior depends on input:

1. **supply_codes is empty list `[]`**:
   - Returns `None`
   - No fallback applied
   - Uses Building Properties/Supply as-is (⚠️ risk if wrong scale)

2. **supply_codes has 1 item** (e.g., `["AS1 (building)"]`):
   - Returns that item (stripped of label)
   - Used regardless of scale match

3. **supply_codes has 2 items** (e.g., `["AS1 (building)", "AS4 (district)"]`):
   - Filters by target scale:
     - `is_standalone=True` → Look for BUILDING-scale → Return AS1
     - `is_standalone=False` → Look for DISTRICT-scale → Return AS4
   - If no scale match → Return first item

4. **supply_codes is "Custom"**:
   - Not handled by filter function
   - Uses component parameters instead

### Decision Tree

```
START: Calculate costs for building X

├─ network-name = "(none)" or empty?
│  └─ YES → CASE 1 (all buildings standalone)
│
└─ NO → Check building connectivity:
   ├─ In DC/nodes.shp? → in_dc_network = True/False
   └─ In DH/nodes.shp? → in_dh_network = True/False

   Determine case:
   ├─ in_dc_network=True AND in_dh_network=True → CASE 4
   ├─ in_dc_network=True AND in_dh_network=False → CASE 5
   ├─ in_dc_network=False AND in_dh_network=True → CASE 6
   └─ in_dc_network=False AND in_dh_network=False → CASE 3
```

## Config Parameter Auto-Selection (Bidirectional)

**Location**:
- `config.py:1370-1445` (`DistrictSupplyTypeParameter._get_auto_default`)
- `config.py:1513-1563` (`DistrictSupplyTypeParameter.get`)

The system automatically ensures BOTH building-scale and district-scale assemblies are available, using a bidirectional auto-selection strategy:

**Auto-selection strategy (when config is empty)**:
1. Find most common **BUILDING-scale** assembly in `supply.csv`
2. Find most common **DISTRICT-scale** assembly in `supply.csv`
3. **If no BUILDING-scale found in supply.csv** → Auto-select first from database (alphabetically)
4. **If no DISTRICT-scale found in supply.csv** → Auto-select first from database (alphabetically)

**Auto-add strategy (when config has value)**:
1. Check which scales are present in configured values
2. **If only BUILDING-scale configured** → Auto-add first DISTRICT-scale from database
3. **If only DISTRICT-scale configured** → Auto-add first BUILDING-scale from database

**Example 1 - Building-only in supply.csv**:
```python
# supply.csv contains: SUPPLY_COOLING_AS1 (building scale only)
# Database contains: AS1, AS2, AS5 (building), AS3, AS4 (district)
# Config not set → Auto-default returns:
['SUPPLY_COOLING_AS1 (building)', 'SUPPLY_COOLING_AS3 (district)']
# AS3 auto-added from database
```

**Example 2 - District-only configured by user**:
```python
# User sets: supply-type-cs = SUPPLY_COOLING_AS4 (district scale only)
# Database contains: AS1, AS2, AS5 (building), AS3, AS4 (district)
# Config.get() returns:
['SUPPLY_COOLING_AS4 (district)', 'SUPPLY_COOLING_AS1 (building)']
# AS1 auto-added from database
```

**Example 3 - Building-only configured by user**:
```python
# User sets: supply-type-cs = SUPPLY_COOLING_AS1 (building scale only)
# Database contains: AS1, AS2, AS5 (building), AS3, AS4 (district)
# Config.get() returns:
['SUPPLY_COOLING_AS1 (building)', 'SUPPLY_COOLING_AS3 (district)']
# AS3 auto-added from database
```

**Why**:
- District networks require **DISTRICT-scale** assemblies
- Standalone buildings require **BUILDING-scale** assemblies
- Ensures both use cases work regardless of what's in supply.csv or user config

**When applied**:
- When loading config via `parameter.get()` (`config.py:1513-1563`)
- Works for both auto-default (empty config) and user-configured values

## Multi-Level Fallback Logic

The system has **3 levels** of fallbacks when determining supply systems for buildings and district networks. These fallbacks cascade from config-level to assembly-level to component-level, with strict scale matching enforcement.

### 4-Case Usage Scenarios

The fallback system handles 4 distinct scenarios based on configuration completeness:

#### Case 1: Complete Configuration (Both Scales Available)
**Scenario**: Config/supply.csv has both BUILDING-scale AND DISTRICT-scale assemblies

**Example**:
```python
config.supply_type_cs = ['SUPPLY_COOLING_AS1 (building)', 'SUPPLY_COOLING_AS3 (district)']
```

**Behavior**:
- Standalone buildings → Use AS1 (building scale) ✅
- District network → Use AS3 (district scale) ✅
- **No fallback needed** - Direct scale matching works

**Use case**: Production systems with properly configured databases

---

#### Case 2: Building-Scale Only (District Auto-Added)
**Scenario**: Config/supply.csv has only BUILDING-scale assemblies

**Example**:
```python
# User config or supply.csv:
supply_type_cs = SUPPLY_COOLING_AS1  # Building scale only

# System returns (auto-adds AS3):
['SUPPLY_COOLING_AS1 (building)', 'SUPPLY_COOLING_AS3 (district)']
```

**Behavior**:
- Standalone buildings → Use AS1 (building scale) ✅
- District network → Use AS3 (auto-added district scale) ✅
- **Fallback triggered**: Bidirectional auto-selection adds first district-scale from database

**Use case**: Scenarios designed for standalone buildings, user wants to explore district networks

---

#### Case 3: District-Scale Only (Building Auto-Added)
**Scenario**: Config/supply.csv has only DISTRICT-scale assemblies

**Example**:
```python
# User config:
supply_type_cs = SUPPLY_COOLING_AS4  # District scale only

# System returns (auto-adds AS1):
['SUPPLY_COOLING_AS4 (district)', 'SUPPLY_COOLING_AS1 (building)']
```

**Behavior**:
- Standalone buildings → Use AS1 (auto-added building scale) ✅
- District network → Use AS4 (district scale) ✅
- **Fallback triggered**: Bidirectional auto-selection adds first building-scale from database

**Use case**: District-focused studies, user wants to compare with standalone buildings

---

#### Case 4: Wrong Scale or Empty Config (Component-Based Fallback)
**Scenario**: Config has wrong scale OR no assemblies configured, AND no components configured

**Example A - Wrong scale not auto-corrected**:
```python
# Config has only building-scale, but bidirectional auto-add is disabled/failed
config.supply_type_cs = ['SUPPLY_COOLING_AS1 (building)']  # No district available

# For district network:
# Level 2 returns None (scale mismatch)
# Level 3 checks component categories
```

**Example B - Empty config**:
```python
config.supply_type_cs = []
config.cooling_components = []
```

**Behavior**:
- **Level 2 returns None** (no scale match or empty)
- **Level 3A checks**: Are component categories configured?
  - YES → Use component-based system ✅
  - NO → **ERROR** ❌

**Error message**:
```
No DISTRICT-scale cooling assembly or component configuration found for DC network 'validation'.
Please either:
  1. Create a DISTRICT-scale SUPPLY_COOLING assembly in your database, OR
  2. Configure 'cooling-components' and 'heat-rejection-components' parameters
```

**Use case**:
- Database migration scenarios
- Custom component-based systems
- Configuration errors (guides user to fix)

---

### Overview: 3-Level Fallback System

```
Level 1: Config Fallback (Scale Mismatch in supply.csv)
   ↓ (Standalone buildings only)
Level 2: Multi-Select Scale Filtering & Verification
   ↓ (Returns code if scale matches, None if mismatch)
Level 3A: Component Category Fallback (District Networks)
   OR
Level 3B: DHW Component Fallback (Buildings - DHW only)
```

**Key Principle**: Scale matching is **strictly enforced**. If config has wrong scale, system proceeds to component-based fallback rather than using mismatched assembly.

**When each level applies**:
- **Level 1**: Only for standalone buildings with DISTRICT-scale code in supply.csv
- **Level 2**: Always applied - filters config by scale, returns None if no match
- **Level 3A**: District networks when Level 2 returns None
- **Level 3B**: Buildings DHW service when assembly has no components

### Level 1: Config Fallback (Scale Mismatch)

**Location**: `supply_costs.py:443-520` (`apply_supply_code_fallback_for_standalone`)

**Trigger**: Building's `supply.csv` has **DISTRICT-scale** code but building is **standalone** for that service

**When applies**: Cases 1, 3, 5, 6 for standalone services only

**Process**:
```python
def apply_supply_code_fallback_for_standalone(building, is_in_dc, is_in_dh):
    fallbacks = {}

    # Check services building provides standalone
    if not is_in_dc:  # Cooling is standalone
        csv_code = building_supply['supply_type_cs']
        if get_scale(csv_code) == 'DISTRICT':
            fallback = filter_supply_code_by_scale(
                config.supply_type_cs, 'SUPPLY_COOLING', is_standalone=True
            )
            if fallback:  # Only if config has value
                fallbacks['supply_type_cs'] = fallback

    if not is_in_dh:  # Heating/DHW are standalone
        # Same logic for supply_type_hs and supply_type_dhw

    return fallbacks  # Applied to Building Properties/Supply before calculation
```

**Example**:
```python
# supply.csv has: supply_type_cs = "AS4" (DISTRICT scale)
# But building NOT in DC network (Case 6)
# Config has: supply_type_cs = ["AS1 (building)", "AS4 (district)"]
# Result: Use "AS1" (building-scale) from config
```

**Key behaviour**:
- Only checks services the building provides standalone
- Only applies if Building Properties/Supply has DISTRICT-scale code
- Only applies if config parameter has value (empty → no fallback)
- Modifies `supply.csv` temporarily before Domain reads it (`supply_costs.py:689-714`)

### Level 2: Multi-Select Scale Filtering

**Location**: `supply_costs.py:73-181` (`filter_supply_code_by_scale`, `_verify_scale_match`)

**Trigger**: Config parameter has supply codes (single or multi-select)

**Process**:
1. **Empty list** → Return `None` (proceed to Level 3)
2. **1 code** → Verify scale match:
   - Scale matches target → Return code
   - Scale mismatch → Return `None` (proceed to Level 3)
3. **2 codes** → Filter by target scale:
   - `is_standalone=True` → Select BUILDING-scale code if exists
   - `is_standalone=False` → Select DISTRICT-scale code if exists
   - No scale match → Return `None` (proceed to Level 3)

**Example**:
```python
supply_codes = ["AS1 (building)", "AS4 (district)"]

# District network (is_standalone=False)
filter_supply_code_by_scale(supply_codes, 'SUPPLY_COOLING', is_standalone=False)
# → Returns "AS4" (DISTRICT scale matches)

# District network with only building-scale code
supply_codes = ["AS1 (building)"]
filter_supply_code_by_scale(supply_codes, 'SUPPLY_COOLING', is_standalone=False)
# → Returns None (scale mismatch, triggers Level 3)
```

**Used in**:
- District network cost calculation (`supply_costs.py:1132, 1174-1175`)
- Config fallback for standalone buildings (`supply_costs.py:514-516`)

### Level 3A: District Network Component Fallback

**Location**: `supply_costs.py:1145-1168` (DC networks), `supply_costs.py:1188-1209` (DH networks)

**Trigger**: Level 2 returns `None` (no matching scale assembly found) for district network

**Process**:
1. Check if component categories configured (`cooling-components`, `heating-components`, etc.)
2. If components configured → Use component-based system (fallback succeeds)
3. If NO components configured → **Raise error** asking user to create assembly

**Example - DC network**:
```python
# Level 2 returned None (no DISTRICT-scale assembly)
# Check component configuration
cooling_components = config.system_costs.cooling_components  # ['VAPOR_COMPRESSION_CHILLERS']
heat_rejection_components = config.system_costs.heat_rejection_components  # ['COOLING_TOWERS']

if cooling_components:
    # SUCCESS: Use component-based system
    print("Using component settings: cooling=['VAPOR_COMPRESSION_CHILLERS']")
else:
    # ERROR: No assembly, no components
    raise ValueError("No DISTRICT-scale cooling assembly or component configuration found...")
```

**When triggered**: District network cost calculation when no suitable assembly found (`supply_costs.py:1145-1168`, `1188-1209`)

**Error message format**:
```
No DISTRICT-scale cooling assembly or component configuration found for DC network 'validation'.
Please either:
  1. Create a DISTRICT-scale SUPPLY_COOLING assembly in your database, OR
  2. Configure 'cooling-components' and 'heat-rejection-components' parameters
```

### Level 3B: DHW Component Fallback

**Location**: `supply_costs.py:183-384` (`apply_dhw_component_fallback`)

**Trigger**: `SUPPLY_HOTWATER` assembly has **no components** specified (empty primary/secondary/tertiary columns)

**Process**:
1. Read building's DHW supply code from `supply.csv`
2. Read `SUPPLY_HOTWATER.csv` to get feedstock (e.g., "GRID", "NATURALGAS")
3. Map feedstock to boiler component code from `BOILERS.csv`:
   - `GRID` → `BO5` (electric boiler)
   - `NATURALGAS`/`Cgas` → `BO1` (gas boiler)
   - `OIL`/`Coil` → `BO2` (oil boiler)
   - `COAL`/`Ccoa` → `BO4`, `WOOD`/`Cwod` → `BO6`
4. Create synthetic DHW supply system with that component
5. Calculate and return DHW costs (service suffix changed from `_hs` to `_ww`)

**Example**:
```python
# SUPPLY_HOTWATER_AS1 assembly has no components
# But assembly specifies feedstock = "GRID"
# Fallback: Use BO5 (electric boiler) sized to DHW demand
# Output: Service name "GRID_ww" instead of "GRID_hs"
```

**Feedstock mapping** (`supply_costs.py:199-209`):
```python
feedstock_to_fuel = {
    'GRID': 'E230AC',      # BO5 - Electric boiler
    'NATURALGAS': 'Cgas',  # BO1 - Natural gas boiler
    'OIL': 'Coil',         # BO2 - Oil boiler
    'COAL': 'Ccoa',        # BO4 - Coal boiler
    'WOOD': 'Cwod',        # BO6 - Wood boiler
}
```

**When triggered**: During building cost calculation when DHW demand exists but no components found (`supply_costs.py:1281-1287`)

**DHW energy carrier**: Uses `T60W` (60°C water) for medium-temperature DHW demand (`supply_costs.py:321-327`)

## Fallback Priority Chain

### Complete 3-Level Fallback Flow

```
START: Determine supply system for building or district network
│
├─── STANDALONE BUILDING (Cases 1, 3, 5, 6) ─────────────────────────┐
│                                                                     │
│    Step 1: Check supply.csv for this building                      │
│    ├─ Has DISTRICT-scale code? (e.g., AS4)                         │
│    │  ├─ YES → LEVEL 1: Config Fallback                            │
│    │  │         └─ Config has BUILDING-scale? → Replace with it    │
│    │  │         └─ Config empty? → Keep DISTRICT (may error)       │
│    │  └─ NO → Continue to Level 2                                  │
│    │                                                                │
│    Step 2: LEVEL 2 - Scale Filtering                               │
│    ├─ Filter config by scale (is_standalone=True)                  │
│    ├─ Found BUILDING-scale match? → USE IT ✅                       │
│    ├─ No match? → Return None, proceed to Level 3B                 │
│    │                                                                │
│    Step 3: LEVEL 3B - DHW Component Fallback (DHW service only)    │
│    ├─ Assembly has components? → Use assembly ✅                    │
│    └─ No components? → Map feedstock to boiler (BO1, BO5, etc.) ✅  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

├─── DISTRICT NETWORK (DC or DH) ────────────────────────────────────┐
│                                                                     │
│    Step 1: LEVEL 2 - Scale Filtering                               │
│    ├─ Filter config by scale (is_standalone=False)                 │
│    ├─ Found DISTRICT-scale match? → USE IT ✅                       │
│    ├─ No match or empty? → Return None, proceed to Level 3A        │
│    │                                                                │
│    Step 2: LEVEL 3A - Component Category Fallback                  │
│    ├─ Component categories configured?                             │
│    │  ├─ DC: cooling-components + heat-rejection-components        │
│    │  └─ DH: heating-components                                    │
│    ├─ YES → Use component-based system ✅                           │
│    └─ NO → ERROR ❌                                                 │
│              └─ "Create DISTRICT-scale assembly OR configure       │
│                  component parameters"                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Decision Points

**When does each level activate?**

| Level | Trigger Condition | Applies To | Outcome |
|-------|------------------|------------|---------|
| **Level 1** | supply.csv has DISTRICT-scale code | Standalone buildings only | Replaces with BUILDING-scale from config |
| **Level 2** | Config has value (any scale) | Both buildings & networks | Returns code if scale matches, else `None` |
| **Level 3A** | Level 2 returned `None` | District networks only | Uses components or raises error |
| **Level 3B** | Assembly missing components | Building DHW service only | Maps feedstock to boiler |

### Decision Flow Summary

```
Network layout (truth - from nodes.shp)
  ↓
Config parameters (bidirectional auto-selection adds missing scale)
  ↓
┌─────────────────────┬─────────────────────┐
│ STANDALONE BUILDING │ DISTRICT NETWORK    │
├─────────────────────┼─────────────────────┤
│ Level 1: supply.csv │ (skip Level 1)      │
│   Scale mismatch?   │                     │
│   → Config fallback │                     │
├─────────────────────┼─────────────────────┤
│ Level 2: Config     │ Level 2: Config     │
│   Filter to BUILDING│   Filter to DISTRICT│
│   Match? ✅         │   Match? ✅         │
│   No? → Level 3B    │   No? → Level 3A    │
├─────────────────────┼─────────────────────┤
│ Level 3B: DHW only  │ Level 3A: Components│
│   No components?    │   Configured? ✅    │
│   → Feedstock map   │   No? → ERROR ❌    │
└─────────────────────┴─────────────────────┘
```

### Example Scenarios

#### Scenario A: Complete Config (No Fallback)
```python
config.supply_type_cs = ['AS1 (building)', 'AS3 (district)']
supply.csv: AS1 for all buildings
network: DC with 10 buildings

# Standalone buildings (8 buildings)
Level 2: Filter to BUILDING → Returns AS1 ✅

# District network
Level 2: Filter to DISTRICT → Returns AS3 ✅

# Result: No fallback needed
```

#### Scenario B: Building-Only Config (Auto-Add Triggers)
```python
config.supply_type_cs = ['AS1 (building)']  # Only building
supply.csv: AS1 for all buildings
network: DC with 10 buildings

# Bidirectional auto-selection adds AS3 first
config.supply_type_cs → ['AS1 (building)', 'AS3 (district)']

# Standalone buildings
Level 2: Filter to BUILDING → Returns AS1 ✅

# District network
Level 2: Filter to DISTRICT → Returns AS3 ✅

# Result: Auto-add fallback succeeded
```

#### Scenario C: Wrong Scale (Component Fallback)
```python
# Hypothetical case where auto-add failed
config.supply_type_cs = ['AS1 (building)']  # Only building, no AS3 in database
config.cooling_components = ['VAPOR_COMPRESSION_CHILLERS']
supply.csv: AS1 for all buildings
network: DC with 10 buildings

# District network
Level 2: Filter to DISTRICT → Returns None (no match)
Level 3A: Check components → Found, use CH1+CT1 ✅

# Result: Component-based fallback succeeded
```

#### Scenario D: Missing Everything (Error)
```python
config.supply_type_cs = []  # Empty
config.cooling_components = []  # Empty
network: DC with 10 buildings

# District network
Level 2: Empty config → Returns None
Level 3A: Check components → None configured → ERROR ❌

Error: "No DISTRICT-scale cooling assembly or component configuration found..."

# Result: User must configure assemblies or components
```

### Output Files

**costs_buildings.csv**:
```csv
name, GFA_m2, Capex_total_USD, TAC_USD,
Capex_total_building_scale_USD,  # From standalone services
Capex_total_district_scale_USD,  # Allocated from networks
Capex_a_building_scale_USD,
Capex_a_district_scale_USD,
...
```

**costs_components.csv**:
```csv
name, network_type, service, code, capacity_kW, scale,
capex_total_USD, capex_a_USD, opex_fixed_a_USD, opex_var_a_USD
```
- `network_type`: "DH", "DC", or NaN (standalone)
- `scale`: "BUILDING" or "DISTRICT"
- `service`: e.g., "GRID_cs" (cooling from grid), "NG_hs" (heating from natural gas)

## Related Files

**Main module**:
- `main.py:82-297` - Entry point, orchestration, case handling, validation
- `supply_costs.py` - Core cost calculation logic

**6-case logic implementation**:
- `main.py:109-135` - Case 1: Standalone-only mode
- `main.py:137-297` - Cases 3-6: Network + standalone mode
- `supply_costs.py:523-757` - `calculate_standalone_building_costs()` - Cases 3, 5, 6
- `supply_costs.py:1166-1376` - `calculate_costs_for_network_type()` - Cases 4, 5, 6

**Multi-level fallback**:
- `supply_costs.py:443-520` - Level 1: Config fallback (`apply_supply_code_fallback_for_standalone`)
- `supply_costs.py:73-140` - Level 2: Multi-select filtering (`filter_supply_code_by_scale`)
- `supply_costs.py:183-384` - Level 3: DHW fallback (`apply_dhw_component_fallback`)

**Network calculations**:
- `supply_costs.py:760-1055` - `calculate_district_network_costs()` - Central plant sizing
- `supply_costs.py:142-180` - `get_component_codes_from_categories()` - Component selection
- `supply_costs.py:1010-1043` - Piping cost calculation from thermal-network outputs

**Config and database**:
- `cea/config.py:1269-1519` - DistrictSupplyTypeParameter (multi-select with scale labels)
- `cea/default.config:393-408` - Config help text for supply-type parameters
- `cea/databases/AGENTS.md` - Database structure
- `databases/{region}/ASSEMBLIES/SUPPLY/` - CAPEX, efficiency, lifetime
