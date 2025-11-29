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

### Fallback Logic Summary

**When fallback applies** (Cases 1, 3, 5, 6 for standalone services):

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

**Key behavior**:
- Only checks services the building provides standalone
- Only applies if Building Properties/Supply has DISTRICT-scale code
- Only applies if config parameter has value (empty → no fallback)
- Modifies Building Properties/Supply temporarily before Domain reads it

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
- `cea/analysis/costs/baseline_costs.py` - Main implementation of 6-case logic
- `cea/analysis/costs/system_costs.py:107-135` - Cost calculation flow
- `cea/config.py:1269-1519` - DistrictSupplyTypeParameter (multi-select with scale labels)
- `cea/default.config:393-408` - Config help text for supply-type parameters
- `cea/databases/AGENTS.md` - Database structure
- `databases/{region}/ASSEMBLIES/SUPPLY/` - CAPEX, efficiency, lifetime
