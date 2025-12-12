# CEA Frequently Asked Questions & Troubleshooting Guide

**Last Updated**: December 2025
**Compiled from**: 3 months of user support emails (Sept-Dec 2025)

---

## Table of Contents

1. [Common Errors](#common-errors)
2. [Data Input & Database Issues](#data-input--database-issues)
3. [Energy Demand Simulation](#energy-demand-simulation)
4. [Thermal Networks](#thermal-networks)
5. [Supply System Optimisation](#supply-system-optimisation)
6. [Emission Timeline & LCA](#emission-timeline--lca)
7. [Cloud Platform Issues](#cloud-platform-issues)
8. [Workflow Best Practices](#workflow-best-practices)

---

## Common Errors

### Error: "KeyError: 'name'" in Energy Demand Part 2

**Symptom**:
```
KeyError: 'name'
File ".../building_hvac.py", line 222, in verify_hvac_system_combination
building_name = result.loc[idx, 'name']
```

**Root Cause**: Database definition mismatch or missing building properties mapping.

**Solution**:
1. Check your HVAC system definitions in `inputs/database/ASSEMBLIES/HVAC/`
2. Verify all buildings have properly mapped archetypes
3. Re-run archetype mapper after geometry changes
4. Check for missing columns in input CSV files

**Reference**: Issue reported by Huang Siran, 15 Oct 2025

---

### Error: "Invalid temperature configuration detected" in Cooling Coil

**Symptom**:
```
ValueError: Invalid temperature configuration detected!
Hot end (thi - tco): -1.50
Cold end (tho - tci): 6.50
```

**Root Cause**: Incorrect HVAC system temperature settings in ASSEMBLIES database.

**Solution**:
1. Check `ASSEMBLIES > HVAC > COOLING` definitions
2. Ensure you've provided:
   - `Tcs0_aru_C`: Nominal supply temperature (water side, air-recirculation units)
   - `DTcs0_aru_C`: Nominal temperature increase (water side, air-recirculation units)
3. Refer to Zurich database for correct HVAC system examples
4. See documentation: [How to add a heating/cooling system in CEA](https://city-energy-analyst.readthedocs.io/)

**Reference**: Issue reported by Ana Perez, 22 Oct 2025; Resolved by Bernad, 23 Oct 2025

---

### Error: "The truth value of a Series is ambiguous"

**Symptom**:
```
ValueError: The truth value of a Series is ambiguous.
Use a.empty, a.bool(), a.item(), a.any() or a.all().
```

**Root Cause**: Duplicate building names in zone.shp file.

**Solution**:
1. Open zone.shp and check for duplicate building names (e.g., multiple "L2124", "L2125")
2. Building names must be unique identifiers in CEA
3. Rename duplicates (e.g., L2124_1, L2124_2, etc.)
4. Re-upload shapefile to CEA

**Reference**: Issue reported by Matteo & Gino, 22 Oct 2025

---

### Error: "check potential error in input database of LCA infrastructure / ELECTRICITY"

**Symptom**:
```
Exception: check potential error in input database of LCA infrastructure / ELECTRICITY
```

**Root Cause**: Invalid definitions in supply system database (likely SUPPLY_ELECTRICITY).

**Solution**:
1. Check `inputs/database/ASSEMBLIES/SUPPLY/SUPPLY_ELECTRICITY.csv`
2. Verify all referenced components exist in `COMPONENTS/CONVERSION/` databases
3. Run CEA-4 Format Helper to identify database errors
4. Compare your definitions with the default Zurich database

**Reference**: Issue reported by Léonie Guers, 26 Nov 2025

---

### Error: No Space Heating Demand (Qhs_sys = 0)

**Symptom**: Buildings show DHW demand but zero heating demand.

**Root Causes**:
1. Heating schedules turned OFF in use-type schedules
2. Invalid HVAC heating system temperature parameters
3. Incorrect heating supply system definition

**Solution**:
1. **Check schedules**: Navigate to `inputs/database/ARCHETYPES/USE/SCHEDULES/SCHEDULES_LIBRARY/`
   - Open relevant use-type schedule (e.g., MULTI_RES, OFFICE)
   - Ensure heating is not set to "OFF" (0) for all hours
   - Set appropriate setpoints (e.g., 20°C) and setbacks (e.g., 16°C)

2. **Verify HVAC system**:
   - Check `ASSEMBLIES > HVAC > HEATING` for your assigned system
   - Ensure supply/return temperatures are properly defined
   - Verify heating system is activated in `inputs/building-properties/air_conditioning.dbf`

3. **Check supply system**:
   - Open `inputs/building-properties/supply_systems.dbf`
   - Verify heating system type is assigned (not blank)
   - Ensure SUPPLY_HEATING assembly exists in database

4. **Validate formula**: In `outputs/demand/total_demand.csv`, check:
   ```
   QH_sys_kWh = Qhs_sys_kWh + Qww_sys_kWh + Qhpro_sys_kWh
   ```

**Reference**: Issues reported by:
- Gino Sandi, 22-23 Oct 2025
- Chia-Wei Lee, 5-10 Nov 2025
- Ioannis Galetakis, 27 Oct 2025

---

## Data Input & Database Issues

### Issue: Database Edits Not Saving in CEA Cloud

**Symptom**: Changes made in CEA Cloud input editor don't persist or appear correctly.

**Root Cause**: Cloud synchronisation issues or browser caching.

**Workaround**:
1. Download scenario as ZIP
2. Edit input files locally (Excel/LibreOffice)
3. Re-upload entire scenario to CEA Cloud
4. Avoid editing database files directly in cloud when possible

**Reference**: Issue reported by Bianca Hettinger, 27 Oct 2025

---

### Issue: CONSTRUCTION_TYPES.csv Year Validation Errors

**Symptom**:
```
Invalid type for year_end/year_start (e.g., 1960.0)
```

**Root Cause**: Year fields saved as float instead of integer in CSV.

**Solution**:
1. Open `CONSTRUCTION_TYPES.csv` in text editor or Excel
2. Ensure `year_start` and `year_end` are formatted as integers (e.g., 1960, not 1960.0)
3. In Excel: Format cells as "Number" with 0 decimal places
4. Save as CSV (UTF-8) and re-upload

**Reference**: Issue reported by Ana Perez, 20 Oct 2025

---

### Issue: Missing or Empty Use Type Fields (use_type2, use_type3)

**Symptom**: Export Results summary only shows few buildings instead of all.

**Root Cause**: Empty cells in zone.shp for `use_type2`, `use_type2r`, `use_type3`, `use_type3r`.

**Solution**:
1. In CEA Dashboard, click "Input Editor" (bottom corner)
2. Select all buildings (click "Select All" at top)
3. Click "Edit Selection"
4. Set:
   - `use_type2` → "NONE"
   - `use_type2r` → 0
   - `use_type3` → "NONE"
   - `use_type3r` → 0
5. Save changes (top right near account login)
6. Re-run "Export Results to CSV"

**Reference**: Issue reported by Yuyao (Tongji), 4 Dec 2025

---

### Issue: Encoding Error (cp950) on Windows

**Symptom**: CEA fails to read input files with encoding errors on Chinese/Asian language Windows.

**Solution**:
1. Go to Windows Settings → Time & Language → Language & Region
2. Click "Administrative language settings"
3. Under "Language for non-Unicode programs", click "Change system locale"
4. Check "Beta: Use Unicode UTF-8 for worldwide language support"
5. Restart computer
6. All programs will now default to UTF-8

**Reference**: Solution provided by Chia-Wei Lee, 24 Sept 2025

---

## Energy Demand Simulation

### Issue: EUI Values Show Zero in Hourly Analytics

**Symptom**: `demand_hourly_EUI.csv` shows 0.000 for all hourly values.

**Root Cause**: Significant figure rounding (hourly EUI kWh/m² is very small, e.g., 0.0004).

**Workaround**:
1. Use `demand_hourly.csv` (non-normalised) instead
2. Manually calculate EUI: Divide demand by total building area
3. CEA team acknowledges this as a known limitation
4. Use daily/monthly/yearly EUI outputs for analysis

**Reference**: Issue reported by Silvia Dimitrova & Ioannis Galetakis, 20-21 Nov 2025

---

### Issue: Same Demand Results Despite Different Schedules

**Symptom**: Office and residential buildings show identical demand despite different use types.

**Root Causes**:
1. CEA doesn't delete previous results when running subset of buildings
2. Downloaded results contain old data from previous runs

**Solution**:
1. When running building clusters separately:
   - Create a new scenario for each cluster
   - Or delete `/outputs/demand/` folder before running new cluster
2. Recommended workflow:
   - Run DAYSIM once for all buildings (longest step)
   - Download and backup DAYSIM results
   - Duplicate "base" scenario for each demand run variant
3. Verify building names in output CSVs match your current selection

**Reference**: Issue reported by Silvia Dimitrova, 21 Nov 2025

---

### Issue: Long Runtime for Energy Demand (Never Completes)

**Symptom**: Energy Demand Part 2 runs for hours/overnight without completing.

**Root Causes**:
1. Non-fatal warnings/errors prevent CEA from exiting gracefully
2. Empty or unmapped building inputs (e.g., geometry without archetype)
3. Cloud server overload

**Solutions**:
1. Check for warning messages - CEA Cloud doesn't always terminate on warnings
2. Ensure all buildings have:
   - Valid geometry (closed polygons)
   - Assigned archetypes (run archetype mapper)
   - Complete database definitions
3. Try running subset of buildings first to isolate problematic ones
4. Check building B1729 and similar: ensure all modified geometries are remapped

**Reference**: Issues reported by:
- Ana Perez & Reva Saksena, 24-25 Oct 2025
- Bianca Hettinger, 26-27 Oct 2025

---

## Thermal Networks

### Issue: Street Network Connectivity Errors

**Symptom**:
```
ERROR: Buildings [B1003, B1004, ...] cannot be connected to street network
```

**Root Causes**:
1. Disconnected street segments (tolerance limit recently stricter in CEA v4)
2. Buildings modified/deleted but streets not updated
3. Non-simple polylines (arcs, curves) in street network

**Solutions**:
1. **Check street connectivity** in QGIS:
   - Use Snapping tool: [QGIS Snapping Documentation](https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/editing_geometry_attributes.html)
   - Ensure all building access points connect to main trunk roads
   - Remove superfluous streets after deleting buildings

2. **Fix geometry issues**:
   - Convert arcs/curves to polylines (street networks must use simple LineString)
   - Avoid "PlanarCurve" and "ArcCurve" geometries
   - Redraw problematic streets as simple polylines

3. **Adjust tolerance** (temporary fix):
   - In "Thermal Network Part 1" parameters
   - Open "Steiner Tree Parameters"
   - Increase `connection-candidates` from 2 to 3

4. **Simplify network**:
   - You don't need all streets - only those connecting building clusters
   - Focus on key access roads, not decorative/internal paths

**Reference**: Issues reported by:
- Ana Perez & Reva Saksena, 14-17 Nov 2025
- Yuyao (Tongji), 27 Nov - 2 Dec 2025

---

### Issue: Only 6 Streets Imported from 190 Curves

**Symptom**: Street import from Rhino/Grasshopper only recognises a few polylines.

**Root Cause**: Non-polyline geometries (arcs, curves) not compatible with CEA.

**Solution**:
1. In Rhino: Select all street curves
2. Convert to polylines: `Convert` → `ToPolyline`
3. Ensure all curves are joined as single polylines per street
4. Check curve types: Only "LineCurve" and "PolylineCurve" supported
5. Delete or redraw "PlanarCurve" and "ArcCurve" features

**Reference**: Issue reported by Yuyao (Tongji), 30 Nov - 2 Dec 2025

---

### Issue: Thermal Network Part 2 Error - "All network types failed to process"

**Symptom**:
```
ValueError: All network types failed to process (DC). See errors above.
```

**Root Causes**:
1. Invalid geometry in zone.shp (unclosed polygons, self-intersections)
2. Missing or incorrect heat exchanger definitions
3. Supply system component mismatches

**Solutions**:
1. **Validate geometry**:
   ```
   ValueError: Invalid geometries found: N0010, N0011, N0090
   ```
   - Check these buildings in QGIS for:
     - Unclosed polygons (open curves)
     - Self-intersecting edges
     - Two separate unclosed curves treated as one building

2. **Check heat exchanger database**:
   - Ensure `HEAT_EXCHANGERS.csv` has required codes (HEX3, HEX4, etc.)
   - Apply correct HEX types:
     - HEX3 → tertiary_components of SUPPLY_COOLING_AS3
     - HEX4 → secondary_components of SUPPLY_HEATING_AS1

**Reference**: Issues reported by:
- Ana Perez (thermal network error), 1 Dec 2025
- Noah Adriany (geometry error), 3 Dec 2025

---

## Supply System Optimisation

### Issue: "None of the components chosen... can generate/absorb required energy carrier"

**Symptom**:
```
ERROR: None of the components chosen for the secondary category
can generate/absorb the required energy carrier T0B.

ERROR: None of the components chosen for the tertiary category
can generate/absorb the required energy carrier T30W.
```

**Root Cause**: Component capacity definition missing or exceeds database limits.

**Solutions**:
1. **Check component capacity**:
   - For UNITARY_AIR_CONDITIONERS: Maximum capacity ~1900 W
   - For VAPOR_COMPRESSION_CHILLERS: Check capacity limits in database
   - Error example: "code: AC1 - capacity: 102238.0W" (too high for AC1)

2. **Fix capacity values**:
   - Open `inputs/database/COMPONENTS/CONVERSION/`
   - Find relevant component CSV (e.g., `UNITARY_AIR_CONDITIONERS.csv`)
   - Adjust capacity or switch to appropriate component type
   - For high capacities, use centralized systems (not unitary AC)

3. **Check heat exchanger assignment**:
   - Verify HEX types match required energy carriers
   - Ensure secondary/tertiary components properly defined

**Important**: District-scale optimisation should only run for ≤50 buildings (not entire scenarios).

**Reference**: Issues reported by:
- Bianca Hettinger, 27 Oct 2025
- Ana Perez & Mathias Niffeler, 27-28 Oct 2025

---

### Issue: Supply Optimisation - Long Runtime / Never Completes

**Symptom**: Supply system optimisation runs for hours without results.

**Root Causes**:
1. Too many buildings selected (district-scale optimisation)
2. Cloud storage full
3. Invalid supply system definitions

**Solutions**:
1. **Reduce building count**:
   - District-scale: Maximum ~50 buildings
   - Building-scale: Run all buildings, but check for errors first

2. **Clean up cloud storage**:
   - Delete unused projects and scenarios
   - Download and archive old results
   - Cloud full storage impacts all users

3. **Run building-scale first**: Test on single buildings to identify database issues

**Reference**: Issues reported by Ana Perez & Bianca Hettinger, 26-27 Oct 2025; Cloud storage warning by Zhongming Shi

---

### Issue: "negative cooling load to VCC" Error

**Symptom**:
```
ValueError: ('negative cooling load to VCC: ', nan)
```

**Root Cause**: Cooling system configuration producing invalid (negative or NaN) loads.

**Solution**:
1. Check cooling schedules in use-type definitions
2. Verify cooling setpoints and setbacks are logical
3. Ensure ARU/AHU/SCU supply temperatures are properly configured
4. Review HVAC_COOLING assembly definitions

**Reference**: Issue reported by Ana Perez, 27 Oct 2025

---

## Emission Timeline & LCA

### Issue: Emission Timeline - Missing PV Data Error

**Symptom**:
```
ERROR: PV data missing for panel type: PV1_kgCO2e
Please run 'emissions' script with include_pv=True and pv_codes=['PV1_kgCO2e']
```

**Root Causes**:
1. CEA backend bug (fixed Dec 2025)
2. PV checkbox unchecked in emission timeline parameters despite running emissions with PV

**Solutions**:
1. **Temporary workaround** (before fix):
   - In emission-timeline plot parameters
   - Under "envelope-components"
   - **Uncheck 'pv'** (counterintuitive but necessary)

2. **Proper solution** (after Dec 5 2025 backend update):
   - Ensure you've run "Emissions" script with PV included
   - Check 'pv' in envelope-component for emission-timeline
   - Plot should work correctly

**Reference**: Issue reported by Silvia Dimitrova, 3-6 Dec 2025; Fixed by dev team Dec 5, 2025

---

### Issue: Emission Timeline - ModuleNotFoundError

**Symptom**:
```
ModuleNotFoundError: No module named 'cea.analysis.lca.primary_energy'
```

**Root Cause**: CEA internal module path error (backend issue).

**Status**: **Fixed** by development team (Dec 4, 2025).

**Solution**: Update to latest CEA version or use CEA Cloud (auto-updated).

**Reference**: Issue reported by Silvia Dimitrova, 3 Dec 2025

---

## Cloud Platform Issues

### Issue: Cannot Download Scenario / Download Incomplete

**Symptom**:
- Download stops midway (especially for large scenarios >10GB)
- Network instability interrupts download
- Cannot restart interrupted download

**Solutions**:
1. **Download selectively**:
   - Select only "Inputs" and "Summary" (not raw output)
   - Summary contains aggregated results in concise format
   - Raw outputs can be very large (10-16GB)

2. **Use stable network**:
   - Avoid downloading large files on unstable WiFi
   - Use wired connection if possible

3. **Reduce output file size**:
   - Delete intermediate simulation files from scenario
   - Only keep final results

4. **Download via email link**:
   - CEA Cloud sends download link via email after generation
   - Try email link if dashboard download fails

**Reference**: Issue reported by Yuyao (Tongji), 4 Dec 2025

---

### Issue: Export Results Summary - Only Few Buildings Appear

**Symptom**: Export results CSV only contains a few buildings instead of all simulated.

**Root Causes**:
1. Empty cells in use_type fields (see [Data Input Issues](#issue-missing-or-empty-use-type-fields))
2. Previous export results not cleared before new export
3. Buildings filtered incorrectly

**Solutions**:
1. Fill empty use_type fields with "NONE" and 0 (see detailed solution above)
2. Re-run "Export Results to CSV" after fixing inputs
3. Check timestamp folders in `export/results/` - use latest folder
4. Verify building filter settings in export parameters

**Reference**: Issue reported by Yuyao (Tongji), 4 Dec 2025

---

### Issue: Changes Not Saving / Format Helper Shows No Errors But Issues Persist

**Symptom**: CEA-4 Format Helper reports no issues, but simulations still fail.

**Root Cause**: Database changes made in Cloud UI not persisting due to synchronisation issues.

**Workaround**:
1. **Always work locally when modifying databases extensively**:
   - Download scenario
   - Edit locally
   - Re-upload
2. After cloud edits:
   - Download scenario immediately to verify changes
   - Re-upload if changes didn't persist
3. Use Format Helper after re-uploading to confirm

**Reference**: Issue reported by Bianca Hettinger, 27 Oct 2025

---

## Workflow Best Practices

### Recommended Scenario Workflow for Design Iterations

**Problem**: Running variants (e.g., 2025 vs 2060 scenarios) causes file conflicts and long runtimes.

**Best Practice**:

```
1. Base Scenario Setup
   ├── Create "Base" scenario
   ├── Run DAYSIM (longest step) for all buildings
   ├── Download & backup: inputs + DAYSIM results
   └── DO NOT run demand yet

2. For Each Design Variant
   ├── Duplicate "Base" scenario → "Variant_A", "Variant_B", etc.
   ├── Modify inputs (geometry, archetypes, schedules, etc.)
   ├── Re-run archetype mapper
   ├── Run Energy Demand Part 1 & 2
   ├── Run other analyses (emissions, networks, optimisation)
   └── Export results

3. Comparison
   ├── Download all variant results
   ├── Compare in external tools (Excel, Python, R)
   └── Use CEA plots for initial visualisation
```

**Benefits**:
- DAYSIM only run once (saves hours)
- Each variant independent (no file conflicts)
- Easy rollback if needed
- Clear result organisation

---

### Database Editing Workflow

**Recommended Steps**:

1. **Start with Template Database**:
   - Use Zurich database as reference
   - Copy-paste similar components and modify

2. **Edit Locally** (for complex changes):
   - Download scenario
   - Edit CSV files in Excel/LibreOffice
   - Save as CSV UTF-8
   - Re-upload to CEA Cloud

3. **Validate Early & Often**:
   - Run CEA-4 Format Helper after major database changes
   - Test on 1-2 buildings before running full scenario
   - Check error logs carefully

4. **Document Your Changes**:
   - Keep a change log (what, why, when)
   - Save database snapshots at key milestones

5. **Common Pitfall**:
   - **Always re-run Archetype Mapper** after:
     - Geometry changes
     - Database modifications
     - Use-type adjustments

---

### Debugging Checklist for Energy Demand Errors

When Energy Demand Part 2 fails, check in this order:

- [ ] **1. Geometry Validity**
  - All polygons closed?
  - No self-intersections?
  - No duplicate building names?

- [ ] **2. Database Completeness**
  - All archetypes defined in `CONSTRUCTION_TYPES.csv`?
  - All referenced ASSEMBLIES exist?
  - All referenced COMPONENTS exist?

- [ ] **3. Schedules**
  - Heating/cooling schedules not all OFF?
  - Setpoints and setbacks defined?
  - Schedule names match use-types?

- [ ] **4. System Assignments**
  - HVAC systems assigned in `air_conditioning.dbf`?
  - Supply systems assigned in `supply_systems.dbf`?
  - Systems exist in database?

- [ ] **5. Temperature Parameters**
  - HVAC system temperatures logical? (supply < setpoint < return)
  - Heat exchanger ΔT values positive?

- [ ] **6. Run Order**
  - Archetype mapper run after geometry/database changes?
  - Energy Demand Part 1 (occupancy) run before Part 2?

---

## Additional Resources

- **CEA Documentation**: https://city-energy-analyst.readthedocs.io/
- **CEA GitHub Issues**: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues
- **CEA Learning Platform**: https://platform.idaida.ch/ (requires registration)
- **Food4Rhino (CEA for Grasshopper)**: https://www.food4rhino.com/en/app/cea4gh

---

## Contributing to This Document

If you encounter a new issue not covered here, please:
1. Document the error message and context
2. Note the resolution steps
3. Submit via GitHub issue or contact CEA support team

This document is a living resource compiled from real user experiences. Your contributions help improve CEA for everyone!
