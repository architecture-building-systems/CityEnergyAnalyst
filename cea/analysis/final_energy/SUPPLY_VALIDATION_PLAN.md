# Supply Assembly Validation - Implementation Plan

**Status**: Planning phase - awaiting decision on assembly database structure
**Date**: 2026-02-05
**Context**: Restructuring supply parameters and creating validation module

---

## Current Status

### Completed:
- ✅ Simplified `DistrictSupplyTypeParameter` (single select, nullable)
- ✅ Simplified `SolarPanelChoiceParameter` (nullable, no "none" option)
- ✅ Updated `load_whatif_supply_configuration()` to use new parameter structure

### In Progress:
- 🔄 Parameter restructuring (merge hs+dhw for district systems)
- 🔄 Design validation module architecture
- ❌ **BLOCKED**: Database structure decision needed (see Issue #1 below)

---

## Issue #1: Assembly Database Structure Problem

### The Problem

**Current structure:**
- Space heating: `SUPPLY_HEATING.csv` → codes like `SUPPLY_HEATING_AS1`
- Hot water: `SUPPLY_HOTWATER.csv` → codes like `SUPPLY_HOTWATER_AS1`

**Requirement:**
- District heating plant serves BOTH hs and dhw with ONE assembly/fuel type
- Need to enforce consistency: hs assembly == dhw assembly

**Conflict:**
- Cannot enforce "same assembly code" because they're from different databases with different prefixes
- `SUPPLY_HEATING_AS3` ≠ `SUPPLY_HOTWATER_AS3` (different databases, different codes)

### Proposed Solutions

#### **Option 1: Use SUPPLY_HEATING for both services** (RECOMMENDED)

**Logic:**
- District heating plant = SUPPLY_HEATING assembly only
- For district-connected buildings:
  - `space_heating` → SUPPLY_HEATING assembly
  - `domestic_hot_water` → SUPPLY_HEATING assembly (NOT SUPPLY_HOTWATER)
- For standalone buildings:
  - `space_heating` → SUPPLY_HEATING assembly
  - `domestic_hot_water` → SUPPLY_HOTWATER assembly

**Parameters:**
```ini
# District heating (serves BOTH hs + dhw)
supply-type-heating-district = SUPPLY_HEATING_AS3

# Building-scale heating
supply-type-heating-building = SUPPLY_HEATING_AS1

# No separate dhw-district parameter needed
```

**Pros:**
- ✅ Matches physical reality (one plant, one fuel)
- ✅ Simple validation
- ✅ No database changes needed

**Cons:**
- ❌ SUPPLY_HOTWATER unused for district systems
- ❌ Need to decide: do we add `supply-type-dhw-building` parameter?

#### **Option 2: Validate same primary_component**

Allow different codes but validate underlying component matches:
```python
heating_assembly['primary_components'] == hotwater_assembly['primary_components']
```

**Pros:** Keeps separate databases
**Cons:** Complex validation, user confusion

#### **Option 3: Validate same carrier only**

Allow different assemblies if same fuel type (NATURALGAS, etc.)

**Pros:** Flexible
**Cons:** Allows different efficiencies (unrealistic for same plant)

### DECISION NEEDED:

**Question A**: Which option to use?
**Question B**: For standalone buildings, should we add `supply-type-dhw-building` parameter, or always read from supply.csv?

---

## Proposed Parameter Restructuring

### Remove (6 → 4 parameters):

```ini
# OLD - Remove
supply-type-hs-building
supply-type-hs-district
supply-type-dhw-building
supply-type-dhw-district
supply-type-cs-building
supply-type-cs-district
```

### Add (4 parameters):

```ini
# NEW - Heating (serves both hs + dhw for district)
supply-type-heating-building =
supply-type-heating-building.type = DistrictSupplyTypeParameter
supply-type-heating-building.supply-category = SUPPLY_HEATING
supply-type-heating-building.scale = BUILDING
supply-type-heating-building.nullable = true

supply-type-heating-district =
supply-type-heating-district.type = DistrictSupplyTypeParameter
supply-type-heating-district.supply-category = SUPPLY_HEATING
supply-type-heating-district.scale = DISTRICT
supply-type-heating-district.nullable = true

# NEW - Cooling
supply-type-cooling-building =
supply-type-cooling-building.type = DistrictSupplyTypeParameter
supply-type-cooling-building.supply-category = SUPPLY_COOLING
supply-type-cooling-building.scale = BUILDING
supply-type-cooling-building.nullable = true

supply-type-cooling-district =
supply-type-cooling-district.type = DistrictSupplyTypeParameter
supply-type-cooling-district.supply-category = SUPPLY_COOLING
supply-type-cooling-district.scale = DISTRICT
supply-type-cooling-district.nullable = true
```

### Keep (unchanged):

```ini
hs-booster-type
dhw-booster-type
```

---

## Validation Module Design

### New File: `cea/analysis/final_energy/supply_validation.py`

**Purpose:**
- Centralized validation logic for supply assemblies
- Fail fast (validate before processing buildings)
- Extensible for future criteria (temperature, efficiency, etc.)

### Key Components:

#### 1. Data Structures

```python
@dataclass
class NetworkConnectivity:
    """From network_connectivity.json"""
    network_name: str
    dh_buildings: Dict[str, List[str]]  # {building: [services]}
    dc_buildings: Dict[str, List[str]]

@dataclass
class SupplyConfiguration:
    """User selections from config"""
    heating_building: Optional[str]
    heating_district: Optional[str]
    cooling_building: Optional[str]
    cooling_district: Optional[str]

@dataclass
class SupplyFromCSV:
    """Current assemblies from supply.csv"""
    buildings: Dict[str, Dict[str, str]]
```

#### 2. Validator Class

```python
class AssemblyValidator:
    def validate_all(self) -> Dict[str, str]:
        """
        Run all validations, return final assembly selections

        Validations:
        1. District consistency (all DH buildings use same assembly)
        2. Heating plant unity (hs == dhw for district)
        3. Temperature compatibility (future)
        4. Efficiency thresholds (future)
        """

    def _validate_district_consistency(self):
        """All district buildings must use same assembly"""

    def _validate_heating_plant_unity(self):
        """DH plant: hs assembly == dhw assembly"""

    def _validate_temperature_compatibility(self):
        """Future: assembly temps match network design"""

    def _determine_final_assemblies(self):
        """
        Logic per service:
        1. If user parameter provided:
           - Connected → use district parameter
           - Standalone → use building parameter
        2. If user parameter None:
           - Connected → use supply.csv (validate consistency)
           - Standalone → use most common from supply.csv
        """
```

### Network Connectivity JSON Structure

**File**: `outputs/data/thermal-network/{network_name}/network_connectivity.json`

```json
{
  "network_name": "baseline",
  "networks": {
    "DH": {
      "per_building_services": {
        "B1001": ["space_heating", "domestic_hot_water"],
        "B1003": ["space_heating"]
      }
    },
    "DC": {
      "per_building_services": {
        "B1000": ["space_cooling"]
      }
    }
  }
}
```

**Service mapping:**
- `"space_heating"` = hs
- `"domestic_hot_water"` = dhw
- `"space_cooling"` = cs

---

## Validation Scenarios

### Pre-Processing (Fail Fast - Before Any Buildings)

**For DH network:**
1. Get all buildings with `"space_heating"` → validate same hs assembly
2. Get all buildings with `"domestic_hot_water"` → validate same dhw assembly
3. Validate district hs == district dhw (same plant)

**For DC network:**
1. Get all buildings with `"space_cooling"` → validate same cs assembly

**Errors:**
- ❌ network_connectivity.json not found → "Rerun thermal-network parts 1 & 2"
- ❌ Inconsistent district assemblies → "All district buildings must use same assembly"
- ❌ DH hs ≠ dhw → "District heating plant must use same assembly for hs and dhw"

### Per-Building Logic

#### Scenario 1: Parameter is None/empty + Building connected
- **Action**: Use existing district assembly from supply.csv
- **Error**: If building has no district assembly in supply.csv

#### Scenario 2: Parameter is None/empty + Building NOT connected
- **Action**: Use most common building-scale assembly from supply.csv (per service)
- **Error**: If no building-scale assembly exists

#### Scenario 3: Parameter provided + Building connected
- **Action**: Override supply.csv with district parameter
- **Note**: Consistency validated in pre-processing

#### Scenario 4: Parameter provided + Building NOT connected
- **Action**: Override supply.csv with building parameter

---

## Implementation Steps

### Step 1: Resolve Database Issue
- [ ] **DECISION**: Choose Option 1, 2, or 3 for assembly consistency
- [ ] **DECISION**: Add `supply-type-dhw-building` parameter or use supply.csv?

### Step 2: Update Parameters
- [ ] Modify `default.config` (remove 6, add 4)
- [ ] Update help text
- [ ] Regenerate `config.pyi`

### Step 3: Create Validation Module
- [ ] Create `supply_validation.py`
- [ ] Implement data structures
- [ ] Implement `AssemblyValidator` class
- [ ] Add helper functions

### Step 4: Add InputLocator Method
- [ ] Add `get_network_connectivity_file(network_name)` to `inputlocator.py`

### Step 5: Update Calculation Logic
- [ ] Refactor `load_whatif_supply_configuration()` to use validator
- [ ] Update `load_production_supply_configuration()` if needed
- [ ] Remove old validation code

### Step 6: Testing
- [ ] Test all 4 scenarios
- [ ] Test validation errors
- [ ] Test edge cases (ties, missing data)

### Step 7: Documentation
- [ ] Update `CLAUDE.md`
- [ ] Update docstrings
- [ ] Add examples

---

## Open Questions

1. **Database structure** (CRITICAL):
   - Which option for handling hs vs dhw assemblies?
   - Add `supply-type-dhw-building` parameter?

2. **InputLocator method name**:
   - `get_network_connectivity_file(network_name)`
   - `get_thermal_network_connectivity_file(network_name)`

3. **Most common assembly ties**:
   - Error out?
   - Pick alphabetically?
   - Pick first in database?

4. **Booster validation**:
   - Any special rules for which assemblies can be boosters?

5. **Error message style**:
   - Short technical errors?
   - Verbose with solutions?

---

## Future Extensibility

### Temperature Compatibility Validation

**Add to ASSEMBLIES database:**
```csv
code,...,supply_temp_C,return_temp_C
SUPPLY_HEATING_AS3,...,80,60
SUPPLY_HEATING_AS9,...,55,45
```

**Validator method:**
```python
def _validate_temperature_compatibility(self, user_config):
    assembly = self.supply_db.heating.loc[user_config.heating_district]
    network_temp = self._get_network_design_temp()

    if assembly['supply_temp_C'] < network_temp:
        raise ValueError(f"Assembly temp too low for network")
```

### Efficiency Threshold Validation

```python
def _validate_efficiency_thresholds(self, user_config):
    component = self._get_component_info(user_config.heating_district)

    if component['efficiency'] < 0.85:
        raise ValueError(f"District systems require efficiency >= 0.85")
```

---

## Related Files

- `cea/analysis/final_energy/calculation.py` - Main calculation logic
- `cea/analysis/final_energy/main.py` - Entry point
- `cea/config.py` - Parameter classes
- `cea/default.config` - Parameter definitions
- `cea/databases/CH/ASSEMBLIES/SUPPLY/` - Assembly databases

---

## Next Steps

**When returning to this:**
1. Make decisions on open questions (especially database structure)
2. Update parameters in `default.config`
3. Create `supply_validation.py`
4. Integrate with `calculation.py`

**Other questions to address**: [User will add other topics here]
