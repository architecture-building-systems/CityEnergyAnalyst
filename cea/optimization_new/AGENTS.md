# Optimization New - Component Selection & Energy Carriers

## Energy Carrier Compatibility

### Key Concept: Medium and Temperature

Energy carriers have two critical properties:
1. **Medium** (subtype): water, air, or brine
2. **Temperature** (mean_qual): thermal level in °C

**Rule**: Different mediums CANNOT be converted passively (no heat exchanger can convert water ↔ air).

### Compatibility Matrix

#### For Heating Systems (DH networks, primary components)

| Supply → Demand | T30W (water, 30°C) | T60W (water, 60°C) | T100W (water, 100°C) |
|-----------------|--------------------|--------------------|----------------------|
| **T25A** (air, 25°C) | ❌ Medium mismatch | ❌ Medium mismatch | ❌ Medium mismatch |
| **T30W** (water, 30°C) | ✅ Exact match | ❌ Too cold | ❌ Too cold |
| **T60W** (water, 60°C) | ✅ HX cools down | ✅ Exact match | ❌ Too cold |
| **T100W** (water, 100°C) | ✅ HX cools down | ✅ HX cools down | ✅ Exact match |

**Key**:
- ✅ **Compatible**: Can satisfy demand (directly or with heat exchanger)
- ❌ **Incompatible**: Cannot satisfy demand

**Rules**:
- **Hotter water → Cooler water**: ✅ Works (heat exchanger cools it down)
- **Cooler water → Hotter water**: ❌ Fails (cannot heat up passively)
- **Water ↔ Air**: ❌ Fails (different mediums)

### Component Output by Type

| Component | Code | Input Medium | Output Medium | Output Temp | Output Carrier | Use For |
|-----------|------|--------------|---------------|-------------|----------------|---------|
| **Boilers** |
| Natural gas boiler | BO1 | - | water | 82°C | T60W* | DH networks ✅ |
| Electric boiler | BO5 | - | water | ~90°C | T60W* | DH networks, DHW ✅ |
| **Heat Pumps** |
| Geothermal (brine-air) | HP1 | brine | **air** | 27°C | T25A | Building air systems ❌ DH |
| Water-source (water-air) | HP2 | water | **air** | 27°C | T25A | Building air systems ❌ DH |
| Air-water | HP3 | air | **water** | 35°C | T30W* | DH networks ✅ |

*Actual mapping depends on `energyCarrier.py` logic and available temperature carriers.

### Common Errors & Solutions

#### Error 1: Medium Mismatch (Water ↔ Air)

**Symptom**:
```
Issue: MEDIUM MISMATCH
  Components output air, but demand requires water.
  Different mediums (water/air/brine) cannot be converted with passive components.
```

**Example**: Using HP1 or HP2 (output air) for district heating (requires water)

**Solution**:
1. **For DH networks**: Use water-output components
   - Boilers: BO1, BO2, BO5 (all output water)
   - Heat pumps: HP3 (air-water, outputs water)
   - Avoid: HP1, HP2 (output air)

2. **Change SUPPLY assembly**:
   ```csv
   # databases/CH/ASSEMBLIES/SUPPLY/SUPPLY_HEATING.csv
   # Current (WRONG for DH):
   SUPPLY_HEATING_AS10,HP1,...  # HP1 outputs air ❌

   # Fixed:
   SUPPLY_HEATING_AS10,HP3,...  # HP3 outputs water ✅
   ```

#### Error 2: Temperature Too Low

**Symptom**:
```
Issue: TEMPERATURE TOO LOW
  Components output 27°C (T25A), but demand requires ≥60°C (T60W).
  Cannot heat up passively - need active heating component.
```

**Example**: Using HP3 (35°C output) to provide DHW (requires 60°C)

**Solution**:
1. Use higher-temperature components:
   - For 30°C demand: HP3 (35°C) ✅
   - For 60°C demand: BO1, BO5 (80-90°C) ✅
   - For 100°C demand: High-temp boilers ✅

2. Check if demand temperature is correct:
   - **Space heating**: Typically T30W (30°C for low-temp radiant systems)
   - **DHW**: Requires T60W (60°C for hot water taps)
   - **District networks**: May aggregate both → need ≥60°C

#### Error 3: Temperature Too High (Less Common)

**Note**: This usually works via heat exchanger. If you see this error, it indicates another issue (capacity, availability).

**Solution**: Check component capacity and database configuration.

## District Heating (DH) Network Requirements

### Hardcoded Assumptions in building.py

**Line 102, 119**: DH networks use **WATER** carriers (T30W, T60W, T100W)

```python
if energy_system_type == 'DC':
    self.demand_flow = EnergyFlow('primary', 'consumer', 'T10W', ...)  # Water
elif energy_system_type == 'DH':
    energy_carrier_code = 'T30W' or 'T60W'  # Water
    self.demand_flow = EnergyFlow('primary', 'consumer', energy_carrier_code, ...)
```

**Why**: District heating networks distribute hot water through pipes, not air. Building-level systems may use air internally, but the **network interface is always water-based**.

### Demand Temperature Logic

**Space heating dominant** (Qhs > 0):
- Assigns: **T30W** (30°C water)
- Rationale: Low-temperature heating systems (radiators, floor heating)

**DHW-only** (Qhs = 0, Qww > 0):
- Assigns: **T60W** (60°C water)
- Rationale: Domestic hot water requires 60°C

**Both** (Qhs > 0 and Qww > 0):
- Assigns: **T30W** (space heating takes priority)
- Note: District supply may need ≥60°C to serve DHW via heat exchangers

### Correct SUPPLY Assemblies for DH

| Assembly Code | Component | Output | Status |
|---------------|-----------|--------|--------|
| SUPPLY_HEATING_AS9 | BO1 (gas boiler) | water, 82°C → T60W | ✅ Works |
| SUPPLY_HEATING_AS10 | HP1 (brine-air) | air, 27°C → T25A | ❌ Fails (medium mismatch) |
| SUPPLY_HEATING_AS11 | HP2 (water-air) | air, 27°C → T25A | ❌ Fails (medium mismatch) |
| **Recommended Fix** | HP3 (air-water) | water, 35°C → T30W | ✅ Works for T30W demand |

## Creating Compatible Assemblies

### Option 1: Fix Existing Assemblies (Recommended)

Edit `databases/CH/ASSEMBLIES/SUPPLY/SUPPLY_HEATING.csv`:

```csv
# Change AS10 and AS11 to use HP3 instead of HP1/HP2
description,code,primary_components,...
district heating - heatpump - air/water,SUPPLY_HEATING_AS10,HP3,...
district heating - heat pump - air/water,SUPPLY_HEATING_AS11,HP3,...
```

### Option 2: Create New Assembly

Add new row to `SUPPLY_HEATING.csv`:

```csv
district heating - air-water heat pump,SUPPLY_HEATING_AS12,HP3,-,-,GRID,DISTRICT,3.0,150,25,1,5,custom
```

### Option 3: Fix Component Database (Advanced)

If you want HP1/HP2 to output water, edit `databases/CH/COMPONENTS/CONVERSION/HEAT_PUMPS.csv`:

```csv
# Change medium_cond_side from "air" to "water"
description,code,...,medium_cond_side,...
geothermal heat pump,HP1,...,water,...  # Changed from "air"
```

**Warning**: This changes the component specification globally.

## Code References

**Energy carrier compatibility**:
- `energyCarrier.py:265-290` - `get_hotter_thermal_ecs()` (heating can use hotter sources)
- `energyCarrier.py:293-318` - `get_colder_thermal_ecs()` (cooling can use colder sources)
- `energyCarrier.py:321-377` - `temp_to_thermal_ec()` (maps component temp → carrier code)

**Compatibility checking**:
- `supplySystemStructure.py:835-852` - `_find_convertible_energy_carriers()` (checks if passive conversion possible)
- `supplySystemStructure.py:697-891` - `_generate_energy_carrier_mismatch_error()` (diagnostic error messages)

**Demand assignment**:
- `building.py:94-123` - `load_demand_profile()` (assigns T30W or T60W for DH)
- `building.py:248-288` - `check_demand_energy_carrier()` (validates demand matches supply)

## Related Documentation

- `cea/databases/CLAUDE.md` - Database structure (ASSEMBLIES vs COMPONENTS)
- `cea/demand/CLAUDE.md` - Demand calculation (HVAC vs SUPPLY, QH_sys vs Qhs/Qww)
- `cea/analysis/costs/CLAUDE.md` - Cost calculations (district vs building-level)
