# Thermal-Network vs System-Costs: Architectural Analysis

**Date**: 2025-12-06
**Issue**: SUPPLY_COOLING_AS3 works in thermal-network but fails in system-costs
**Root Cause**: Different architectural approaches to component handling

---

## Executive Summary

Thermal-network (Part 2) and system-costs are **parallel calculations** with minimal coupling. Thermal-network performs pure hydraulic-thermal physics without referencing SUPPLY assemblies or component codes, while system-costs attempts to instantiate and validate components from assemblies. This creates situations where the same configuration succeeds in one module but fails in the other.

**Key Finding**: For baseline cost calculations with SUPPLY assemblies that already contain complete cost data (CAPEX, efficiency, lifetime), the current component instantiation approach adds unnecessary complexity and potential failure points.

---

## Question 1: Why Does Thermal-Network Succeed Where System-Costs Fails?

### Case Study: SUPPLY_COOLING_AS3

**Assembly Configuration**:
```csv
description: district cooling - Lakewater/water
code: SUPPLY_COOLING_AS3
primary_components: CH2
tertiary_components: CT1  # or HEX1 in some databases
efficiency: 3.2
CAPEX_USD2015kW: 200
```

### Thermal-Network Behaviour

**What it does**:
1. Reads building cooling demands (QC_sys_kWh)
2. Calculates network pipe sizes based on peak flows
3. Runs EPANET hydraulic solver
4. Determines substation heat exchanger specifications independently
5. Outputs: pipe diameters, lengths, flows, temperatures

**What it does NOT do**:
- Never reads SUPPLY assembly files
- Never accesses component codes (CH2, CT1, HEX1)
- Never instantiates Component objects
- Never validates energy carriers

**Code Location**: `/Users/zshi/Documents/GitHub/CityEnergyAnalyst/cea/technologies/thermal_network/`
- `thermal_network.py` (lines 3423-3515): Main network calculations
- `simplified_thermal_network.py` (lines 402-467): Substation design
- **Zero references** to SUPPLY assemblies or component codes (verified via grep)

**Result**: SUPPLY_COOLING_AS3 with HEX1 causes **no issues** because HEX1 is never referenced.

---

### System-Costs Behaviour

**What it does**:
1. Reads SUPPLY assembly to extract component codes
2. Attempts to instantiate each component:
   ```python
   component = ComponentClass(code, placement, capacity)
   ```
3. Validates energy carrier compatibility
4. Calculates costs from component specifications

**What causes failures**:
- **HeatExchanger (HEX)** requires special initialization:
  ```python
  HeatExchanger(code, placement, capacity, temp_before, temp_after)
  # Standard: Component(code, placement, capacity)  # ← Fails for HEX
  ```
- **TypeError** when using standard initialization → cost calculation aborts

**Code Location**: `/Users/zshi/Documents/GitHub/CityEnergyAnalyst/cea/analysis/costs/`
- `supply_costs.py:25-71`: `get_components_from_supply_assembly()`
- `supply_costs.py:1143`: Reads SUPPLY assembly codes
- `supply_costs.py:1278`: Creates `SupplySystemStructure` with component codes
- `supply_costs.py:1284`: Calls `system_structure.build()` → instantiates components

**Result**: SUPPLY_COOLING_AS3 with HEX1 **fails** with TypeError.

---

### Dependency Analysis

**How much does system-costs depend on thermal-network results?**

**Minimal** - only these values:
1. **Pipe lengths/diameters**: For piping infrastructure costs
2. **Building connectivity**: Which buildings are actually connected to network
3. **Network existence check**: Validates thermal-network was executed

**Does NOT depend on**:
- Component selection or technology choices from thermal-network
- How thermal-network calculated substation specifications
- Heat exchanger sizing from thermal-network

**Independence**: System-costs performs its own **independent** component analysis using the SUPPLY assembly specified in config, completely separate from thermal-network's physics-based calculations.

---

### Architectural Comparison

```
┌─────────────────────────────────────────────────────────────┐
│ THERMAL-NETWORK (Part 2)                                    │
│                                                              │
│  Building demands → Pipe sizing → EPANET → Outputs          │
│                                                              │
│  Inputs:  QC_sys_kWh (from demand simulation)              │
│  Process: Hydraulic network solver                          │
│  Outputs: Pipe diameters, flows, temperatures              │
│                                                              │
│  ✗ Never touches SUPPLY assemblies                          │
│  ✗ Never instantiates components                            │
│  ✓ Pure physics-based calculation                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SYSTEM-COSTS                                                 │
│                                                              │
│  SUPPLY assembly → Extract codes → Instantiate → Costs      │
│                                                              │
│  Inputs:  SUPPLY_COOLING_AS3, thermal-network results      │
│  Process: Component validation + cost calculation           │
│  Outputs: CAPEX, OPEX, TAC by component                    │
│                                                              │
│  ✓ Reads SUPPLY assemblies                                  │
│  ✓ Must instantiate components                              │
│  ✗ Can fail on component instantiation errors               │
└─────────────────────────────────────────────────────────────┘

         │ Coupling: Pipe lengths/diameters only │
         ↓                                        ↓
    Parallel calculations with minimal dependency
```

---

## Question 2: Why Not Use Peak Demand Directly for Costs?

### Current Approach (Complex)

**What happens now**:
```python
# Step 1: Read assembly
assembly = pd.read_csv('SUPPLY_COOLING.csv')
# Result: {'code': 'AS3', 'primary_components': 'CH2',
#          'tertiary_components': 'CT1', 'CAPEX_USD2015kW': 200}

# Step 2: Extract component codes
component_codes = ['CH2', 'CT1']

# Step 3: Instantiate each component
for code in component_codes:
    comp_class = ActiveComponent.code_to_class_mapping[code]
    component = comp_class(code, placement, capacity)
    # Requires COMPONENTS/CONVERSION/CHILLERS.csv for CH2
    # Requires COMPONENTS/CONVERSION/COOLING_TOWERS.csv for CT1
    # FAILS if component has special initialization (e.g., HEX)

# Step 4: Validate energy carriers
validate_energy_carrier_compatibility()

# Step 5: Calculate costs
capex_total = peak_kW * component_specs['CAPEX_per_kW']
# Result: Same as assembly['CAPEX_USD2015kW'] × peak_kW
```

**Complexity**: 5 steps, requires COMPONENTS database, can fail on instantiation

---

### Alternative Simple Approach

**What COULD work for assemblies with complete cost data**:
```python
# Step 1: Read assembly
assembly = pd.read_csv('SUPPLY_COOLING.csv')

# Step 2: Calculate costs directly
peak_kW = thermal_network_results['peak_demand']
capex_total = peak_kW * assembly['CAPEX_USD2015kW']
opex_fixed = capex_total * (assembly['O&M_%'] / 100)
capex_annualized = calc_capex_annualized(capex_total, assembly['IR_%'], assembly['LT_yr'])
# Done!
```

**Complexity**: 2 steps, no component instantiation, no failure points

**Result**: Identical cost calculation, but simpler and more robust

---

### Why the Complex Approach Exists

The component instantiation serves these purposes:

1. **Energy carrier validation**: Ensures components can provide required energy (water vs air, correct temperature)
2. **Efficiency calculations**: Components have different efficiencies affecting operational costs
3. **Fuel type selection**: Different components use different fuels (electricity, gas, etc.)
4. **Multi-component systems**: Primary + secondary + tertiary with different capacities and activation order

**These features are essential for**:
- **Optimization module**: Mix-and-match components, find optimal configurations
- **Custom systems**: User-defined component combinations without assemblies

**These features are NOT essential for**:
- **Baseline costs**: Fixed assemblies with predefined CAPEX/efficiency
- **Simple cost estimation**: Single technology, known costs

---

### The Data Redundancy

**SUPPLY assembly already contains all cost parameters**:

```csv
description,code,primary_components,tertiary_components,efficiency,CAPEX_USD2015kW,LT_yr,O&M_%,IR_%
district cooling,AS3,CH2,CT1,3.2,200,20,1,5
```

**Component codes (CH2, CT1) are only needed for**:
- Optimization (component-level mix-and-match)
- Energy carrier validation (verify water/air compatibility)

**For baseline costs**:
- `efficiency = 3.2` → Already in assembly
- `CAPEX_USD2015kW = 200` → Already in assembly
- `LT_yr, O&M_%, IR_%` → Already in assembly

**The `primary_components` column creates a false dependency** that isn't needed for simple cost calculations.

---

## The Design Issue

### Problem: Assembly-Level vs Component-Level Data

**Assemblies (SUPPLY_COOLING.csv)** contain:
- High-level system specifications
- Aggregated efficiency (system-level COP)
- Single CAPEX value ($/kW for entire system)
- Intended for: Simplified baseline analysis

**Components (COMPONENTS/CONVERSION/*.csv)** contain:
- Detailed equipment specifications
- Component-level efficiency
- Cost curves (a + b×capacity + c×capacity²)
- Intended for: Detailed optimization

**Current system mixes both**:
- Uses assembly for cost parameters (CAPEX, efficiency)
- BUT requires component instantiation for validation
- Creates unnecessary coupling and failure points

---

## Potential Solutions

### Option 1: Two-Mode Cost Calculation (Recommended)

**Mode 1: Assembly-Based (Simple)**
```python
if assembly_has_complete_cost_data(assembly):
    # Use CAPEX_USD2015kW directly from assembly
    # Skip component instantiation
    capex = peak_kW * assembly['CAPEX_USD2015kW']
    efficiency = assembly['efficiency']
    # No component validation needed
```

**Mode 2: Component-Based (Complex - Current Behaviour)**
```python
else:
    # For optimization or custom systems
    # Instantiate components from codes
    components = instantiate_from_codes(assembly['primary_components'])
    capex = calculate_from_components(components)
    efficiency = calculate_system_efficiency(components)
```

**Benefits**:
- ✅ Baseline scenarios work without component database
- ✅ Assemblies with HEX or other special components work
- ✅ Optimization still has full component-level detail
- ✅ Backwards compatible

**Implementation**:
- Check if assembly has `CAPEX_USD2015kW`, `efficiency`, `LT_yr`, `O&M_%`, `IR_%`
- If yes → Use assembly data directly (Mode 1)
- If no → Fall back to component instantiation (Mode 2)

---

### Option 2: Remove Component Codes from Assemblies

**Change SUPPLY assembly structure**:
```csv
# Old (has component codes):
description,code,primary_components,tertiary_components,efficiency,CAPEX_USD2015kW
district cooling,AS3,CH2,CT1,3.2,200

# New (no component codes):
description,code,system_type,efficiency,CAPEX_USD2015kW
district cooling,AS3,VAPOR_COMPRESSION,3.2,200
```

**Benefits**:
- ✅ Removes false dependency on component database
- ✅ Assemblies are truly standalone
- ✅ Clear separation: assemblies for baseline, components for optimization

**Drawbacks**:
- ❌ Breaking change to database structure
- ❌ Requires migration of existing scenarios
- ❌ Loses component-level detail for assemblies

---

### Option 3: Make Component Codes Optional

**Keep current structure but make codes optional**:
```python
# In get_components_from_supply_assembly():
if 'primary_components' in row and pd.notna(row['primary_components']):
    # Use component-based approach
    component_codes = parse_components(row['primary_components'])
else:
    # Use assembly-based approach (no instantiation)
    component_codes = []
```

**Benefits**:
- ✅ Backwards compatible
- ✅ Allows assemblies without component codes
- ✅ Gradual migration path

**Drawbacks**:
- ⚠ Two code paths to maintain
- ⚠ Unclear when to use which approach

---

## Recommendations

### Immediate Fix (Current Error)

**For the HEX1 issue**:
1. Change SUPPLY_COOLING_AS3 from `tertiary_components: HEX1` to `tertiary_components: CT1`
2. Or use component categories instead: `heat-rejection-components = COOLING_TOWERS`

**Why this works**:
- Thermal-network: Unaffected (doesn't read assembly)
- System-costs: Can instantiate CT1 without special parameters

---

### Long-Term Design Improvement

**Implement Option 1: Two-Mode Cost Calculation**

**Phase 1** (Quick win):
- Add Mode 1 (assembly-based) for assemblies with complete cost data
- Keep Mode 2 (component-based) as fallback
- No breaking changes

**Phase 2** (Future):
- Consider separating baseline assemblies from optimization components
- Document which approach to use for which scenarios
- Add validation to prevent mixing modes inappropriately

**Benefits**:
- Resolves HEX/special component issues
- Maintains optimization capabilities
- Simplifies baseline cost calculations
- More robust (fewer failure points)

---

## Technical Details

### Component Instantiation Failure Points

**Current system can fail when**:

1. **Component not in COMPONENTS database**:
   ```
   KeyError: 'HEX1' not found in HEAT_EXCHANGERS.csv
   ```

2. **Component has non-standard initialization**:
   ```python
   TypeError: HeatExchanger.__init__() missing 3 required positional arguments:
   'capacity', 'temperature_before', and 'temperature_after'
   ```

3. **Energy carrier mismatch**:
   ```
   ValueError: HP1 outputs air (T25A) but demand requires water (T30W)
   ```

**All three are avoided** with assembly-based approach (Mode 1).

---

### Code Locations Reference

**Thermal-Network**:
- Main: `cea/technologies/thermal_network/thermal_network.py`
- Substation design: `cea/technologies/thermal_network/simplified_thermal_network.py:402-467`
- **No SUPPLY assembly references** (verified)

**System-Costs**:
- Assembly reading: `cea/analysis/costs/supply_costs.py:25-71`
- Component instantiation: `cea/analysis/costs/supply_costs.py:1278-1284`
- Component validation: `cea/optimization_new/containerclasses/supplySystemStructure.py:347`

**Component Classes**:
- Base class: `cea/optimization_new/component.py:85-110`
- HeatExchanger: `cea/optimization_new/component.py:899`

**Error Diagnostics**:
- New diagnostic system: `cea/optimization_new/error_diagnostics.py`
- Detects: medium mismatch, temperature incompatibility, unsupported component types

---

## Questions for Team Discussion

1. **Is the component instantiation necessary for baseline costs?**
   - Do we need energy carrier validation for fixed assemblies?
   - Could we trust assembly data is already validated?

2. **Should assemblies be self-contained?**
   - Should CAPEX/efficiency in assembly be sufficient?
   - Or do we always need component-level detail?

3. **What's the intended use case split?**
   - Assemblies for: Baseline only? Or also optimization?
   - Components for: Optimization only? Or also baseline?

4. **Migration strategy?**
   - Implement two-mode calculation (Option 1)?
   - Or redesign assembly structure (Option 2)?
   - Timeline and effort required?

5. **User experience**:
   - Should users need to understand component database for baseline scenarios?
   - Or should assemblies "just work" without component dependencies?

---

## Appendix: Error Message Improvements

**New diagnostic system** (implemented in `error_diagnostics.py`):

### Example 1: Medium Mismatch
```
Issue: MEDIUM MISMATCH
  Components output air, but demand requires water.
  Different mediums (water/air/brine) cannot be converted with passive components.

Solutions:
  1. Use components that output water:
     - BO1, BO5 (boilers) - output water at 60-100°C
     - HP3 (air-water heat pump) - outputs water at 35°C
  2. Change SUPPLY assembly to use water-output components
```

### Example 2: Unsupported Component Type
```
Issue: UNSUPPORTED COMPONENT TYPE
  Component(s) HEX1 cannot be used in this context.
  These components require special initialisation parameters that are not available
  during automatic system generation.

Explanation:
  - HeatExchanger (HEX) requires source and sink temperature specifications
  - These passive components need active components to drive them

Solutions:
  1. Replace unsupported components in SUPPLY assembly:
     - Use COOLING_TOWERS (CT1, CT2, CT3) instead of HEAT_EXCHANGERS
  2. Edit SUPPLY assembly:
     - Change tertiary_components from HEX1 to CT1
  3. Alternative: Use component categories instead of SUPPLY assemblies
```

**These clear messages** help users understand and fix configuration issues without deep system knowledge.
