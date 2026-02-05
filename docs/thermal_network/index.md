# CEA Thermal Network Documentation Index

This directory contains comprehensive documentation of the CEA thermal network implementation, created to support a major refactoring to separate DHW and space heating services.

## Documentation Files

### 1. exploration_summary.md (10 KB)
**Purpose**: High-level overview of the entire exploration

**Contents**:
- Executive summary of key findings
- Two-phase architecture explanation
- Building selection mechanism
- Supply.csv integration status (what's working, what's missing)
- Service configuration method (PLANT node type encoding)
- Booster logic overview
- 10 key insights
- Recommended next steps

**Best for**: Getting oriented, understanding the big picture

---

### 2. refactoring_guide.md (28 KB, 799 lines)
**Purpose**: Comprehensive technical reference for architects and developers

**Contents** (14 parts):
1. Main entry points and call flow
2. All configuration parameters with defaults
3. Building selection logic with decision trees
4. Network layout generation workflows (auto and user-defined)
5. Supply.csv integration and schema
6. Service configuration (DHW vs. space heating)
7. Complete building selection example scenarios
8. Plant node creation and anchor building selection
9. Network layout output file structure
10. Service temperature implications
11. Data dependencies (what files are needed)
12. Critical data flow points (the three major flows)
13. Refactoring considerations and limitations
14. Key files reference with line numbers

**Best for**: Deep understanding, implementation planning, code navigation

---

### 3. quick_reference.txt (14 KB)
**Purpose**: Developer cheat sheet for quick lookup during implementation

**Contents** (text format for terminal viewing):
- ASCII architecture diagrams
- Building selection decision tree (visual)
- Configuration parameters organized by category
- Supply.csv integration status (visual)
- Service configuration and plant types
- Critical data flows
- Plant node placement algorithm
- Refactoring opportunities (4 phases)
- Key files with line numbers
- Example scenarios (3 real-world cases)
- Testing checklist

**Best for**: Implementation work, quick lookup, in-terminal reference

---

## How to Use These Documents

### For Understanding the System
1. Start with **exploration_summary.md** (10 min read)
2. Read **refactoring_guide.md** Part 1-3 (30 min)
3. Review **quick_reference.txt** architecture diagram (5 min) - if available

### For Implementing Phase 1 (Supply.csv Enhancement)
1. Review refactoring_guide.md Part 3 (Building selection)
2. Review refactoring_guide.md Part 5 (Supply.csv integration)
3. Use quick_reference.txt REFACTORING_OPPORTUNITIES section - if available
4. Reference key files: main.py lines 149-174, 636-727

### For Implementing Phase 2 (Separate DHW/SH Networks)
1. Study refactoring_guide.md Part 6 (Service configuration)
2. Study refactoring_guide.md Part 8-9 (Plant nodes and file structure)
3. Reference key files: plant_node_operations.py
4. Reference building_heating_booster.py for booster logic

### For Code Navigation
1. Use quick_reference.txt KEY FILES section for file locations - if available
2. Use refactoring_guide.md Part 14 for detailed file reference with line numbers
3. Use exploration_summary.md CODE LOCATIONS SUMMARY for specific functions

### For New Developers
1. Read exploration_summary.md completely (20 min)
2. Read quick_reference.txt (print for desk reference) (15 min) - if available
3. Keep refactoring_guide.md open while exploring code (reference)

---

## Key Findings at a Glance

### Current Architecture
- **Two phases**: Layout generation (building selection) and thermal simulation
- **Service encoding**: Uses PLANT node types (PLANT_hs_ww, PLANT_ww_hs, etc.)
- **Configuration**: Global `itemised-dh-services` applies to all buildings
- **Supply.csv**: Partially implemented (building list only, not service config)

### What's Working
- Basic building selection via supply.csv or connected-buildings parameter
- Demand-based filtering
- Service configuration encoding/decoding
- Booster logic for both space heating and DHW

### What's Missing
- Per-building service specification from supply.csv
- Separate networks per service (DHW vs. space heating)
- Plant-aware network optimization
- Building-level service configuration in output

### Refactoring Phases
1. **Phase 1**: Enhance supply.csv to specify services per building
2. **Phase 2**: Generate separate networks for DHW and space heating
3. **Phase 3**: Include plant placement in Steiner tree optimization
4. **Phase 4**: Store building-level service config in nodes.shp

---

## Configuration Parameters by Category

### Building Selection Parameters
- `overwrite-supply-settings` (bool, default: true)
- `connected-buildings` (list, default: blank)
- `consider-only-buildings-with-demand` (bool, default: true)

### Service Configuration Parameters
- `itemised-dh-services` (multi-choice, default: [space_heating, domestic_hot_water])

### Plant Placement Parameters
- `heating-plant-building` (string, comma-separated)
- `cooling-plant-building` (string, comma-separated)

### Network Layout Parameters
- `network-name` (required)
- `include-services` (list: DH, DC)
- `connection-candidates` (int, default: 3)
- `snap-tolerance` (default: 0.5m)
- `number-of-components` (optional, for validation)

### Thermal Simulation Parameters
- `network-name` (must match layout)
- `network-type` (list: DH, DC, or both)
- `network-model` (simplified or detailed)
- `temperature-control` (VT or CT)
- `plant-supply-temperature` (for CT mode)

---

## Critical Code Locations

### Main Entry Points
- Layout generation: `/cea/technologies/network_layout/main.py::main()`
- Thermal simulation: `/cea/technologies/thermal_network/thermal_network.py::main()`

### Building Selection
- Main logic: `/cea/technologies/network_layout/main.py::auto_layout_network()` lines 628-1020
- Supply.csv reading: `/cea/technologies/network_layout/main.py::get_buildings_from_supply_csv()` lines 149-174
- Demand filtering: `/cea/technologies/network_layout/main.py::get_buildings_with_demand()` lines 177-218

### Service Configuration
- Encode: `/cea/technologies/network_layout/plant_node_operations.py::get_plant_type_from_services()`
- Decode: `/cea/technologies/network_layout/plant_node_operations.py::get_services_from_plant_type()`
- Plant creation: `/cea/technologies/network_layout/plant_node_operations.py::add_plant_close_to_anchor()`

### Booster Logic
- Implementation: `/cea/technologies/building_heating_booster.py::calc_dh_heating_with_booster_tracking()`

### Thermal Simulation Service Reading
- Main: `/cea/technologies/thermal_network/thermal_network.py::get_thermal_network_from_shapefile()` lines 241-262
- Min temp calc: `/cea/technologies/thermal_network/simplified_thermal_network.py::calculate_minimum_network_temperature()` lines 402-510

### Configuration Files
- Parameters: `/cea/default.config` lines 1614-1682
- File paths: `/cea/inputlocator.py` line 905

---

## Example Scenarios

### Standard Mode (supply.csv-based)
```
overwrite-supply-settings = False
consider-only-buildings-with-demand = True
itemised-dh-services = [space_heating, domestic_hot_water]
```
Result: DH network has buildings where supply_type_hs maps to DISTRICT and have heating demand

### What-if Scenario (user-specified buildings)
```
overwrite-supply-settings = True
connected-buildings = [B001, B003, B005]
consider-only-buildings-with-demand = True
```
Result: DH network has [B001, B003, B005] that have heating demand

### DHW Priority Network
```
overwrite-supply-settings = True
connected-buildings = (all zone buildings)
consider-only-buildings-with-demand = True
itemised-dh-services = [domestic_hot_water, space_heating]
```
Result: DH network at 60°C for DHW, space heating gets direct supply (no booster)

---

## Testing Checklist

From THERMAL_NETWORK_quick_reference.txt:

- [ ] Test building selection with various config combinations
- [ ] Test supply.csv with missing columns
- [ ] Test with buildings that have zero demand
- [ ] Test plant placement with user-specified buildings
- [ ] Test service configuration encoding/decoding
- [ ] Test booster activation logic
- [ ] Test backward compatibility (legacy PLANT types)
- [ ] Test with user-defined networks
- [ ] Test node naming (no duplicates after plant creation)
- [ ] Test coordinate precision (6 decimals)

---

## Document Statistics

| Document | Size | Lines | Purpose |
|----------|------|-------|---------|
| exploration_summary.md | 10 KB | ~300 | Overview |
| refactoring_guide.md | 28 KB | 799 | Deep reference |
| quick_reference.txt | 14 KB | 283 | Developer cheat sheet |

Total: 52 KB of comprehensive documentation

---

## Navigation Tips

### I want to understand the overall architecture
→ Read exploration_summary.md then quick_reference.txt ASCII diagrams (if available)

### I need to implement Phase 1 (supply.csv enhancement)
→ Read refactoring_guide.md Part 3 and Part 5, then navigate to code using KEY FILES section

### I need to implement Phase 2 (separate networks)
→ Read refactoring_guide.md Part 6 and Part 8, study booster logic in building_heating_booster.py

### I'm debugging a building selection issue
→ Use quick_reference.txt BUILDING SELECTION DECISION TREE (if available) and navigate to specific code

### I need to add a new configuration parameter
→ Read refactoring_guide.md Part 2, check default.config, follow AGENTS.md patterns in cea/technologies/thermal_network/

### I need to understand plant node placement
→ Read refactoring_guide.md Part 8, read quick_reference.txt PLANT NODE PLACEMENT section (if available)

---

## Related Documentation

See also:
- `/CLAUDE.md` (project root) - General LLM guidelines for CEA
- `/cea/technologies/network_layout/AGENTS.md` - Network layout architectural patterns
- `/cea/technologies/thermal_network/AGENTS.md` - Thermal network architectural patterns
- `/cea/default.config` - All configuration parameters with help text

---

## Contact & Updates

This documentation was created: 2025-12-19

During refactoring implementation:
1. Keep these documents updated as architecture changes
2. Add code examples as patterns emerge
3. Update testing checklist as tests are created
4. Document new configuration parameters following CLAUDE.md patterns

---

**Last Updated**: 2025-12-19  
**Thoroughness Level**: Very Thorough (comprehensive coverage of all major components)
