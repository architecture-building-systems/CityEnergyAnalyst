# Recent Changes in Thermal Network Modeling

This document summarizes the transition from legacy thermal network modeling to the current service-aware implementation.

---

## 1. Per-Building Service Differentiation (2025)

### Previous Behavior (Legacy)
Previously, thermal network modeling was an "all-or-nothing" approach for connected buildings:
- If a building was connected to a District Heating (DH) network, CEA assumed it received **all** services defined in the configuration (e.g., both Space Heating AND Domestic Hot Water).
- The `supply_systems.csv` file was only used to determine **if** a building was connected, but not **which** services it received.

### Current Behavior
CEA now differentiates services on a per-building basis.
- **Granular Connections:** Building A can be connected to the DH network for Space Heating only, while Building B connects for both Space Heating and DHW.
- **Logic Sync:** The `Thermal Network Simulation` now reads from a new metadata file (`building_services.json`) to ensure it only calculates loads for the specific services a building has requested.

---

## 2. Input/Output Format Changes

### `supply_systems.csv` (Inputs)
The columns `supply_type_hs` and `supply_type_dhw` are now treated independently.
- **Old Logic:** If either was `DISTRICT`, connect building to ALL network services.
- **New Logic:** 
    - `supply_type_hs == DISTRICT` → Connect for Space Heating.
    - `supply_type_dhw == DISTRICT` → Connect for DHW.
    - Building joins the network if **either** is true.

### `nodes.shp` (Outputs)
The `Type` column for Plant nodes now uses a suffix-based encoding to represent network service priority.
- **Legacy:** `PLANT` or `PLANT_DH`.
- **New:** `PLANT_hs_ww`, `PLANT_ww_hs`, `PLANT_hs`, `PLANT_ww`.
- **Note:** The simulation still supports legacy `PLANT` types by defaulting them to `PLANT_hs_ww`.

### `building_services.json` (New Output)
A new metadata file is generated in the `Layout` folder of each network:
- **Path:** `scenario/outputs/thermal-network/{name}/DH/building_services.json`
- **Format:** JSON dictionary mapping building names to lists of active services.

---

## 3. Service Priority Formalization
The order of services in the `itemised-dh-services` configuration parameter is now strictly respected as a **priority list**. The first item (Index 0) is the "Primary Service" and determines the network's hourly supply temperature. All subsequent items are "Secondary Services" and may trigger booster calculations.