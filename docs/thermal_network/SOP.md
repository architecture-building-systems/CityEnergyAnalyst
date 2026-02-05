# Thermal Network Standard Operating Procedure (SOP)

This document describes the standard workflow and logic for modeling thermal networks in the City Energy Analyst (CEA). It covers the two-phase architecture, building selection mechanisms, and service priority configuration.

---

## 1. The Two-Phase Architecture

Thermal network modeling in CEA is split into two distinct phases. Understanding this split is critical for correct simulation results.

### Phase 1: Network Layout Generation
- **Script:** `Network Layout`
- **Purpose:** Determines **which** buildings are connected and **where** the pipes (edges) and nodes are located.
- **Inputs:** `zone.shp`, `street_network.shp`, `supply_systems.csv`, and `assemblies_supply_*.csv`.
- **Key Output:** A folder containing `nodes.shp`, `edges.shp`, and `building_services.json`.
- **Constraint:** All building selection and service configuration decisions are finalized during this phase.

### Phase 2: Thermal Simulation
- **Script:** `Thermal Network Simulation`
- **Purpose:** Calculates temperatures, mass flows, thermal losses, and pumping requirements for the **pre-existing layout**.
- **Inputs:** Output of Phase 1 + Demand results (`B001.csv`, etc.).
- **Constraint:** This phase **cannot** add or remove buildings. It strictly simulates the network generated in Phase 1.

---

## 2. Building and Service Selection Logic

CEA uses a hierarchy of logic to determine which buildings connect to the network and which services (e.g., Space Heating vs. DHW) they receive.

### Step 1: Selection Mode
There are two ways to determine building connectivity during the **Layout Phase**.

#### Mode A: Supply.csv Mode (Default)
Set `overwrite-supply-settings = False`.
CEA reads `inputs/building-properties/supply_systems.csv`.
1.  **Lookup Scale:** For each building, CEA looks up the `supply_type_hs` (heating), `supply_type_dhw` (hot water), and `supply_type_cs` (cooling) codes in the corresponding assemblies database (e.g., `databases/CH/systems/assemblies_supply_heating.csv`).
2.  **Filter by Scale:** If the code's `scale` property in the database is `DISTRICT`, the building is assigned that service.
3.  **Connection Rule:** A building is included in the network if **at least one** of its services is set to `DISTRICT`.

#### Mode B: Manual/What-if Mode
Set `overwrite-supply-settings = True`.
CEA ignores `supply_systems.csv`.
1.  **Connected Buildings:** Uses the `connected-buildings` parameter. If blank, **all** zone buildings are included.
2.  **Global Services:** Every included building is assigned **all** services specified in the `itemised-dh-services` parameter.

### Step 2: Demand Filtering
If `consider-only-buildings-with-demand = True`, CEA performs an additional check:
1.  It reads the total demand results.
2.  If a building has **zero annual demand** for its assigned district services (e.g., a building connects for DHW but has 0kWh DHW demand), it is **removed** from the network layout.

### Step 3: Network Service Union
The network itself is configured to provide the **union** of all services required by the connected buildings. For example, if Building A needs Space Heating and Building B needs DHW, the plant is configured as `PLANT_hs_ww` to provide both.

---

## 3. Service Priority & Network Temperature

For District Heating (DH) networks, the network temperature is determined by the **Service Priority**.

### Itemised Services
The `itemised-dh-services` parameter (e.g., `['space_heating', 'domestic_hot_water']`) defines the priority.
- **Primary Service (Index 0):** This service determines the network supply temperature (e.g., 35-45°C for Space Heating priority).
- **Secondary Services:** These services "ride" on the network. If the primary service temperature is too low (e.g., 35°C network vs. 60°C needed for DHW), the substation will calculate the **local booster load** required to bridge the gap.

### Plant Types (nodes.shp "Type" column)
The service configuration is encoded into the `Type` field of the Plant nodes:
- `PLANT_hs_ww`: Space heating is primary. DHW uses a booster.
- `PLANT_ww_hs`: DHW is primary. Space heating is served directly.
- `PLANT_hs`: Only space heating provided.
- `PLANT_ww`: Only DHW provided.

---

## 4. File Formats Reference

### Input: `supply_systems.csv`
- **Location:** `inputs/building-properties/supply_systems.csv`
- **Key Columns:** `name`, `supply_type_hs`, `supply_type_dhw`, `supply_type_cs`.

### Output: `nodes.shp`
- **Location:** `scenario/outputs/thermal-network/{name}/{type}/nodes.shp`
- **Attributes:**
    - `name`: Unique ID (e.g., `B1001`, `NODE5`, `PLANT1`).
    - `type`: Node classification (`CONSUMER`, `PLANT_<services>`, `NONE`).
    - `building`: Name of the connected building (if `CONSUMER`).

### Output: `building_services.json`
- **Location:** `scenario/outputs/thermal-network/{name}/{type}/building_services.json`
- **Purpose:** Maps specific services to specific buildings for the Phase 2 simulation.
- **Structure:**
```json
{
  "network_type": "DH",
  "plant_type": "PLANT_hs_ww",
  "network_services": ["space_heating", "domestic_hot_water"],
  "per_building_services": {
    "B001": ["space_heating", "domestic_hot_water"],
    "B002": ["space_heating"]
  }
}
```