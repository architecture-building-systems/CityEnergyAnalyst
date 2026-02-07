# Final Energy Backend Implementation Plan

**Date Created:** 2026-02-03
**Purpose:** Define backend structure, file organization, and CSV schemas for final-energy module
**Based On:** Heat rejection results structure (`/outputs/data/heat/{whatif-name}/`)

**Related Documentation:**
- `IMPLEMENTATION_PLAN.md` - Design decisions and calculation approach
- `MIGRATION_REFERENCE.md` - Legacy primary energy logic reference

**Note:** Always use `InputLocator` methods (section 4.2) instead of direct path manipulation with `os.path.join()`.

---

## 1. Directory Structure

```
/outputs/data/final-energy/
├── baseline/                      # Production mode (from supply.csv)
│   ├── B1001.csv                  # Individual building hourly data
│   ├── B1002.csv
│   ├── ...
│   ├── {network_name}_DC_{plant_name}.csv  # District cooling plant
│   ├── {network_name}_DH_{plant_name}.csv  # District heating plant
│   ├── final_energy_buildings.csv          # Compilation: summary by building
│   ├── final_energy.csv                    # Compilation: energy by carrier and service
│   └── supply_configuration.json           # Configuration: supply assemblies + boosters
│
└── {whatif-name}/                 # What-if mode (from supply-type-* parameters)
    ├── B1001.csv                  # Individual building hourly data
    ├── B1002.csv
    ├── ...
    ├── {network_name}_DC_{plant_name}.csv  # District cooling plant
    ├── {network_name}_DH_{plant_name}.csv  # District heating plant
    ├── final_energy_buildings.csv          # Compilation: summary by building
    ├── final_energy.csv                    # Compilation: energy by carrier and service
    └── supply_configuration.json           # Configuration: supply assemblies + boosters
```

**Key Patterns:**
- Each what-if scenario has its own subdirectory
- Special folder name: `baseline/` for production mode (supply.csv)
- District plants saved "as if they are buildings" (same format)

---

## 2. File Types and Schemas

### 2.1 Building Hourly Files (`B####.csv`)

**Purpose:** Hourly final energy consumption by carrier for individual buildings

**Columns:**
```csv
date,                          # Timestamp (YYYY-MM-DD HH:MM:SS)
Qhs_sys_kWh,                   # Space heating demand (system-level)
Qww_sys_kWh,                   # Hot water demand (system-level)
Qcs_sys_kWh,                   # Space cooling demand (system-level)
E_sys_kWh,                     # Electricity demand (system-level)
Qhs_sys_NATURALGAS_kWh,        # Space heating from natural gas
Qhs_sys_OIL_kWh,               # Space heating from oil
Qhs_sys_COAL_kWh,              # Space heating from coal
Qhs_sys_WOOD_kWh,              # Space heating from wood
Qhs_sys_GRID_kWh,              # Space heating from electricity (grid)
Qhs_sys_DH_kWh,                # Space heating from district heating
Qhs_sys_SOLAR_kWh,             # Space heating from solar thermal
Qww_sys_NATURALGAS_kWh,        # Hot water from natural gas
Qww_sys_OIL_kWh,               # Hot water from oil
Qww_sys_COAL_kWh,              # Hot water from coal
Qww_sys_WOOD_kWh,              # Hot water from wood
Qww_sys_GRID_kWh,              # Hot water from electricity (grid)
Qww_sys_DH_kWh,                # Hot water from district heating
Qww_sys_SOLAR_kWh,             # Hot water from solar thermal
Qcs_sys_GRID_kWh,              # Space cooling from electricity (grid)
Qcs_sys_DC_kWh,                # Space cooling from district cooling
E_sys_GRID_kWh,                # Appliances/lighting from electricity (grid)
scale,                         # "BUILDING" (constant for all rows)
case,                          # Case number (e.g., "1", "2", "4.01")
case_description               # Case description (e.g., "Standalone", "DH + standalone cooling")
```

**Data Range:** 8760 rows (full year, hourly)

**Case Definitions:**
- **Case 1:** Standalone (all services building-scale)
- **Case 2:** DH + DC (both heating and cooling from district)
- **Case 3:** DH only (district heating + standalone cooling)
- **Case 4:** DC only (standalone heating + district cooling)
- **Case 4.01:** DC + booster for heating
- **Case 4.02:** DC + booster for DHW

**Key Points:**
- Demand columns (Qhs_sys, Qww_sys, Qcs_sys, E_sys) show total demand before conversion
- Carrier columns show final energy input (after applying efficiency)
- Only non-zero carriers appear (others can be 0 or omitted)
- `scale`, `case`, and `case_description` are constant for all 8760 rows

---

### 2.2 District Plant Hourly Files (`{network_name}_{DC|DH}_{plant_name}.csv`)

**Purpose:** Hourly final energy consumption for district plants (saved "as if they are buildings")

**Naming Convention:**
- `{network_name}` - Network layout name (e.g., "xxx", "qqq")
- `{DC|DH}` - District cooling (DC) or district heating (DH)
- `{plant_name}` - Plant node name from network shapefile (e.g., "NODE_001", "PLANT_A")

**Columns:** Same as building files, but different carriers:
```csv
date,                          # Timestamp (YYYY-MM-DD HH:MM:SS)
Qhs_plant_kWh,                 # Heating supplied by plant (for DH only)
Qcs_plant_kWh,                 # Cooling supplied by plant (for DC only)
Qhs_plant_NATURALGAS_kWh,      # Plant heating from natural gas
Qhs_plant_OIL_kWh,             # Plant heating from oil
Qhs_plant_COAL_kWh,            # Plant heating from coal
Qhs_plant_WOOD_kWh,            # Plant heating from wood
Qhs_plant_GRID_kWh,            # Plant heating from electricity (heat pumps)
Qcs_plant_GRID_kWh,            # Plant cooling from electricity (chillers)
E_plant_GRID_kWh,              # Plant auxiliary electricity (pumps, controls)
scale,                         # "DISTRICT" (constant for all rows)
case,                          # Empty (not applicable to plants)
case_description               # Empty (not applicable to plants)
```

**Data Range:** 8760 rows (full year, hourly)

**Key Differences from Building Files:**
- Column prefix: `_plant_` instead of `_sys_`
- `scale` = "DISTRICT" (instead of "BUILDING")
- `case` and `case_description` are empty
- Only carriers relevant to centralized plants (no individual service breakdowns)

---

### 2.3 Buildings Summary File (`final_energy_buildings.csv`)

**Purpose:** Annual summary statistics for all buildings AND district plants

**Columns:**
```csv
name,                          # Building name (e.g., "B1001") or plant name (e.g., "xxx_DH_plant_001")
type,                          # Entity type: "building" or "plant"
GFA_m2,                        # Gross floor area (empty for plants)
x_coord,                       # X coordinate
y_coord,                       # Y coordinate
scale,                         # "BUILDING" or "DISTRICT"
case,                          # Case number (e.g., "1", "4.01") - empty for plants
case_description,              # Case description - empty for plants
Qhs_sys_MWh,                   # Space heating demand (annual total)
Qww_sys_MWh,                   # Hot water demand (annual total)
Qcs_sys_MWh,                   # Space cooling demand (annual total)
E_sys_MWh,                     # Electricity demand (annual total)
NATURALGAS_MWh,                # Natural gas consumption (annual total)
OIL_MWh,                       # Oil consumption (annual total)
COAL_MWh,                      # Coal consumption (annual total)
WOOD_MWh,                      # Wood consumption (annual total)
GRID_MWh,                      # Electricity consumption (annual total)
DH_MWh,                        # District heating consumption (annual total)
DC_MWh,                        # District cooling consumption (annual total)
SOLAR_MWh,                     # Solar thermal consumption (annual total)
TOTAL_MWh,                     # Total final energy (sum of all carriers)
peak_demand_kW,                # Peak total demand (max of sum across all services)
peak_datetime                  # Timestamp of peak demand
```

**Rows:** One row per building + one row per district plant

**Example:**
```csv
name,type,GFA_m2,x_coord,y_coord,scale,case,case_description,NATURALGAS_MWh,GRID_MWh,DH_MWh,DC_MWh,TOTAL_MWh
B1001,building,5000.0,374097.78,146059.88,BUILDING,1,Standalone,120.5,85.3,0.0,0.0,205.8
B1002,building,3500.0,374110.45,146070.22,BUILDING,3,DH only,0.0,65.2,95.8,0.0,161.0
xxx_DH_NODE_001,plant,,374305.97,146155.99,DISTRICT,,,450.2,120.5,0.0,0.0,570.7
xxx_DC_NODE_001,plant,,374331.24,146171.46,DISTRICT,,,0.0,380.6,0.0,0.0,380.6
```

**Key Points:**
- Combines buildings and plants in single file
- `type` field distinguishes "building" vs "plant"
- `scale` field distinguishes "BUILDING" vs "DISTRICT"
- Plants have empty `GFA_m2`, `case`, and `case_description`
- Carrier columns (NATURALGAS_MWh, GRID_MWh, etc.) aggregate all services
- `TOTAL_MWh` = sum of all carrier columns

---

### 2.4 Final Energy Breakdown File (`final_energy.csv`)

**Purpose:** Detailed breakdown of energy by carrier, service, and entity

**Columns:**
```csv
name,                          # Building/plant name
type,                          # Entity type: "building" or "plant"
scale,                         # "BUILDING" or "DISTRICT"
service,                       # Service type: "space_heating", "hot_water", "space_cooling", "electricity"
demand_column,                 # CEA demand column reference (e.g., "Qhs_sys_kWh", "Qww_sys_kWh", "Qcs_sys_kWh", "E_sys_kWh")
carrier,                       # Energy carrier: "NATURALGAS", "OIL", "COAL", "WOOD", "GRID", "DH", "DC", "SOLAR"
assembly_code,                 # Assembly code (e.g., "SUPPLY_HEATING_AS1", "SUPPLY_HOTWATER_AS3")
component_code,                # Primary component code (e.g., "BO1", "HP1", "CH1")
component_type,                # Component type (e.g., "Boiler", "HeatPump", "VapourCompressionChiller")
efficiency,                    # Component efficiency (min_thermal_eff or COP)
annual_demand_MWh,             # Annual service demand (before conversion)
annual_final_energy_MWh,       # Annual final energy (after conversion)
peak_demand_kW,                # Peak service demand
peak_final_energy_kW,          # Peak final energy
peak_datetime                  # Timestamp of peak
```

**Rows:** Multiple rows per building (one per service-carrier combination)

**Example:**
```csv
name,type,scale,service,demand_column,carrier,assembly_code,component_code,component_type,efficiency,annual_demand_MWh,annual_final_energy_MWh
B1001,building,BUILDING,space_heating,Qhs_sys_kWh,NATURALGAS,SUPPLY_HEATING_AS1,BO1,Boiler,0.85,102.4,120.5
B1001,building,BUILDING,hot_water,Qww_sys_kWh,NATURALGAS,SUPPLY_HOTWATER_AS1,BO1,Boiler,0.85,34.1,40.1
B1001,building,BUILDING,space_cooling,Qcs_sys_kWh,GRID,SUPPLY_COOLING_AS1,CH1,VapourCompressionChiller,3.5,280.5,80.1
B1002,building,BUILDING,space_heating,Qhs_sys_kWh,DH,SUPPLY_HEATING_AS9,,,,87.6,95.8
B1002,building,BUILDING,hot_water,Qww_sys_kWh,DH,SUPPLY_HOTWATER_AS9,,,,56.3,61.5
B1002,building,BUILDING,space_cooling,Qcs_sys_kWh,GRID,SUPPLY_COOLING_AS1,CH1,VapourCompressionChiller,3.5,225.4,64.4
xxx_DH_NODE_001,plant,DISTRICT,space_heating,Qhs_plant_kWh,NATURALGAS,SUPPLY_HEATING_AS9,BO5,Boiler,0.90,405.2,450.2
xxx_DC_NODE_001,plant,DISTRICT,space_cooling,Qcs_plant_kWh,GRID,SUPPLY_COOLING_AS10,CH5,VapourCompressionChiller,4.2,1598.5,380.6
```

**Key Points:**
- One row per building-service-carrier combination
- Shows assembly → component → carrier → efficiency → final energy flow
- District services (DH/DC) have empty component_code/type (centralized at plant)
- Plants show centralized equipment (larger boilers/chillers)
- Enables detailed energy flow analysis and equipment sizing validation
- **demand_column** links back to original CEA demand columns for traceability

---

### 2.5 Supply Configuration File (`supply_configuration.json`)

**Purpose:** Store the supply system configuration used for the final energy calculation

**Structure:**
```json
{
  "metadata": {
    "whatif_name": "my-scenario",
    "mode": "whatif",
    "timestamp": "2026-02-03T19:30:00",
    "cea_version": "4.0.0-beta.6",
    "network_name": "xxx",
    "network_types": ["DH", "DC"]
  },
  "buildings": {
    "B1001": {
      "space_heating": {
        "assembly_code": "SUPPLY_HEATING_AS1",
        "component_code": "BO1",
        "scale": "BUILDING",
        "carrier": "NATURALGAS",
        "efficiency": 0.85
      },
      "space_heating_booster": null,
      "hot_water": {
        "assembly_code": "SUPPLY_HOTWATER_AS1",
        "component_code": "BO1",
        "scale": "BUILDING",
        "carrier": "NATURALGAS",
        "efficiency": 0.85
      },
      "hot_water_booster": null,
      "space_cooling": {
        "assembly_code": "SUPPLY_COOLING_AS1",
        "component_code": "CH1",
        "scale": "BUILDING",
        "carrier": "GRID",
        "efficiency": 3.5
      }
    },
    "B1002": {
      "space_heating": {
        "assembly_code": "SUPPLY_HEATING_AS9",
        "component_code": null,
        "scale": "DISTRICT",
        "carrier": "DH",
        "network_name": "xxx",
        "efficiency": null
      },
      "space_heating_booster": {
        "assembly_code": "SUPPLY_HEATING_AS3",
        "component_code": "BO1",
        "scale": "BUILDING",
        "carrier": "NATURALGAS",
        "efficiency": 0.85,
        "purpose": "Supplement DH when network temp insufficient"
      },
      "hot_water": {
        "assembly_code": "SUPPLY_HOTWATER_AS9",
        "component_code": null,
        "scale": "DISTRICT",
        "carrier": "DH",
        "network_name": "xxx",
        "efficiency": null
      },
      "hot_water_booster": {
        "assembly_code": "SUPPLY_HOTWATER_AS3",
        "component_code": "BO1",
        "scale": "BUILDING",
        "carrier": "NATURALGAS",
        "efficiency": 0.85,
        "purpose": "Raise DHW temp from network supply to target"
      },
      "space_cooling": {
        "assembly_code": "SUPPLY_COOLING_AS1",
        "component_code": "CH1",
        "scale": "BUILDING",
        "carrier": "GRID",
        "efficiency": 3.5
      }
    }
  },
  "plants": {
    "xxx_DH_NODE_001": {
      "network_name": "xxx",
      "network_type": "DH",
      "plant_node_name": "NODE_001",
      "space_heating": {
        "assembly_code": "SUPPLY_HEATING_AS9",
        "component_code": "BO5",
        "carrier": "NATURALGAS",
        "efficiency": 0.90
      },
      "space_heating_booster": null,
      "hot_water": null,
      "hot_water_booster": null
    },
    "xxx_DC_NODE_001": {
      "network_name": "xxx",
      "network_type": "DC",
      "plant_node_name": "NODE_001",
      "space_cooling": {
        "assembly_code": "SUPPLY_COOLING_AS10",
        "component_code": "CH5",
        "carrier": "GRID",
        "efficiency": 4.2
      }
    }
  },
  "parameters": {
    "overwrite_supply_settings": true,
    "supply_type_hs": ["SUPPLY_HEATING_AS1 (building)", "SUPPLY_HEATING_AS9 (district)"],
    "supply_type_dhw": ["SUPPLY_HOTWATER_AS1 (building)", "SUPPLY_HOTWATER_AS9 (district)"],
    "supply_type_cs": ["SUPPLY_COOLING_AS1 (building)", "SUPPLY_COOLING_AS10 (district)"],
    "hs_booster_type": "SUPPLY_HEATING_AS3 (building)",
    "dhw_booster_type": "SUPPLY_HOTWATER_AS3 (building)"
  }
}
```

**Key Fields:**
- **metadata:** Scenario identification and CEA version
- **buildings:** Per-building supply configurations for each service
- **plants:** District plant configurations (one entry per plant)
- **parameters:** Original config parameters that generated this configuration

**Use Cases:**
- **Reproducibility:** Re-run final energy with exact same configuration
- **Comparison:** Compare configurations between what-if scenarios
- **Validation:** Verify which assemblies were used for each building
- **Debugging:** Trace why specific carriers were selected
- **Documentation:** Archive of supply system assumptions for reports

---

## 3. District Plant Naming Convention

### 3.1 File Naming

**Pattern:** `{network_name}_{network_type}_{plant_name}.csv`

**Components:**
- `{network_name}` - Network layout name from network shapefile (e.g., "xxx", "qqq", "main")
- `{network_type}` - "DH" (district heating) or "DC" (district cooling)
- `{plant_name}` - Plant node name from network shapefile (e.g., "NODE_001", "PLANT_A", "CENTRAL")

**Examples:**
- `xxx_DH_NODE_001.csv` - District heating plant "NODE_001" in "xxx" network
- `xxx_DC_NODE_001.csv` - District cooling plant "NODE_001" in "xxx" network
- `qqq_DH_PLANT_A.csv` - District heating plant "PLANT_A" in "qqq" network
- `main_DH_CENTRAL.csv` - District heating plant "CENTRAL" in "main" network

**Important:** Plant names come from the `Name` or `Building` field of PLANT-type nodes in the network shapefile. They are NOT sequential numbers (though they may coincidentally be numbered like "NODE_001").

**Implementation Details:** See Section 7.2 for code examples of reading plant names from shapefiles.

### 3.2 Plant Identification in Compilation Files

In `final_energy_buildings.csv` and `final_energy.csv`:
- **name:** Same as filename without extension (e.g., "xxx_DH_NODE_001", "qqq_DC_PLANT_A")
- **type:** "plant"
- **scale:** "DISTRICT"

### 3.3 Data Source

District plant data comes from:
- **Thermal-network results:** `/outputs/data/thermal-network/{network_name}/`
  - DH plant: Read from plant energy consumption files
  - DC plant: Read from plant energy consumption files
- **Network configuration:** `/inputs/networks/{network_name}/`
  - Plant location (coordinates)
  - Plant equipment specifications

---

## 4. Implementation Steps

### Phase 1: Core Calculation (Priority: HIGH)

**Module:** `cea/analysis/final_energy/calculation.py`

**Functions:**
```python
def calculate_building_final_energy(
    building_name: str,
    locator: InputLocator,
    config: Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy for one building.

    Returns DataFrame with 8760 rows and columns:
    - date, Qhs_sys_kWh, Qww_sys_kWh, Qcs_sys_kWh, E_sys_kWh
    - Qhs_sys_{CARRIER}_kWh, Qww_sys_{CARRIER}_kWh, etc.
    - scale, case, case_description
    """

def calculate_plant_final_energy(
    network_name: str,
    network_type: str,  # 'DH' or 'DC'
    plant_name: str,    # Plant node name from shapefile (e.g., 'NODE_001', 'PLANT_A')
    locator: InputLocator,
    config: Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy for one district plant.

    :param plant_name: Plant node name from network shapefile (e.g., 'NODE_001', 'PLANT_A')

    Returns DataFrame with 8760 rows and columns:
    - date, Qhs_plant_kWh (or Qcs_plant_kWh), E_plant_GRID_kWh
    - Qhs_plant_{CARRIER}_kWh (or Qcs_plant_{CARRIER}_kWh)
    - scale, case, case_description
    """

def aggregate_buildings_summary(
    building_dfs: dict[str, pd.DataFrame],
    plant_dfs: dict[str, pd.DataFrame],
    locator: InputLocator
) -> pd.DataFrame:
    """
    Aggregate hourly data to annual summary.

    Returns DataFrame with one row per building/plant:
    - name, type, GFA_m2, x_coord, y_coord, scale, case, case_description
    - Qhs_sys_MWh, NATURALGAS_MWh, GRID_MWh, etc.
    - TOTAL_MWh, peak_demand_kW, peak_datetime
    """

def create_carriers_breakdown(
    building_dfs: dict[str, pd.DataFrame],
    plant_dfs: dict[str, pd.DataFrame],
    locator: InputLocator,
    config: Configuration
) -> pd.DataFrame:
    """
    Create detailed carrier breakdown by service.

    Returns DataFrame with multiple rows per building/plant:
    - name, type, scale, service, carrier
    - assembly_code, component_code, component_type, efficiency
    - annual_demand_MWh, annual_final_energy_MWh
    """
```

### Phase 2: InputLocator Methods (Priority: HIGH)

**File:** `cea/inputlocator.py`

**New Methods** (add after existing heat rejection methods, around line 1627):

```python
def get_final_energy_folder(self, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/

    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to final energy folder for the what-if scenario
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = os.path.join(self.get_lca_emissions_results_folder(), '..', 'final-energy', whatif_name)
    return os.path.normpath(folder)

def get_final_energy_building_file(self, building_name, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/{building_name}.csv

    :param building_name: Name of the building (e.g., 'B1001')
    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to building hourly final energy file
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = self.get_final_energy_folder(whatif_name)
    return os.path.join(folder, f'{building_name}.csv')

def get_final_energy_plant_file(self, network_name, network_type, plant_name, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/{network_name}_{network_type}_{plant_name}.csv

    :param network_name: Network layout name (e.g., 'xxx', 'qqq')
    :param network_type: 'DH' (district heating) or 'DC' (district cooling)
    :param plant_name: Plant node name from network shapefile (e.g., 'NODE_001', 'PLANT_A')
    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to district plant hourly final energy file

    Example:
        locator.get_final_energy_plant_file('xxx', 'DH', 'NODE_001')
        -> scenario/outputs/data/final-energy/baseline/xxx_DH_NODE_001.csv
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = self.get_final_energy_folder(whatif_name)
    filename = f'{network_name}_{network_type}_{plant_name}.csv'
    return os.path.join(folder, filename)

def get_final_energy_buildings_file(self, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/final_energy_buildings.csv

    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to buildings summary file
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = self.get_final_energy_folder(whatif_name)
    return os.path.join(folder, 'final_energy_buildings.csv')

def get_final_energy_file(self, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/final_energy.csv

    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to final energy breakdown file (by carrier, service, and entity)
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = self.get_final_energy_folder(whatif_name)
    return os.path.join(folder, 'final_energy.csv')

def get_final_energy_supply_configuration_file(self, whatif_name=None):
    """
    scenario/outputs/data/final-energy/{whatif_name}/supply_configuration.json

    :param whatif_name: What-if scenario name. If None, empty, or "(baseline)", uses "baseline" folder.
    :return: Path to supply configuration JSON file
    """
    if not whatif_name or whatif_name.strip() in ["", "(baseline)"]:
        whatif_name = "baseline"
    folder = self.get_final_energy_folder(whatif_name)
    return os.path.join(folder, 'supply_configuration.json')
```

**Usage Example:**
```python
from cea.inputlocator import InputLocator

locator = InputLocator(scenario='/path/to/scenario')

# Building hourly file (production mode)
building_file = locator.get_final_energy_building_file('B1001')
# -> /path/to/scenario/outputs/data/final-energy/baseline/B1001.csv

# Building hourly file (what-if mode)
building_file = locator.get_final_energy_building_file('B1001', whatif_name='my-scenario')
# -> /path/to/scenario/outputs/data/final-energy/my-scenario/B1001.csv

# District plant file
plant_file = locator.get_final_energy_plant_file('xxx', 'DH', 'NODE_001', whatif_name='my-scenario')
# -> /path/to/scenario/outputs/data/final-energy/my-scenario/xxx_DH_NODE_001.csv

# Compilation files
buildings_summary = locator.get_final_energy_buildings_file('my-scenario')
final_energy_breakdown = locator.get_final_energy_file('my-scenario')
config_file = locator.get_final_energy_supply_configuration_file('my-scenario')
```

### Phase 3: Main Script (Priority: HIGH)

**Module:** `cea/analysis/final_energy/main.py`

**Function:**
```python
def main(config: Configuration):
    """
    Main entry point for final-energy script.

    Steps:
    1. Determine mode (production vs what-if)
    2. Get whatif_name from config
    3. Get list of buildings from zone.shp
    4. Calculate final energy for each building
    5. If network selected, calculate for district plants
    6. Save individual hourly files
    7. Generate compilation files
    8. Print summary statistics
    """
```

### Phase 4: Testing (Priority: MEDIUM)

**Module:** `cea/tests/test_final_energy.py`

**Test Cases:**
```python
def test_building_standalone():
    """Test building with all standalone systems (Case 1)"""

def test_building_dh_only():
    """Test building with DH + standalone cooling (Case 3)"""

def test_building_dc_only():
    """Test building with standalone heating + DC (Case 4)"""

def test_building_dh_dc():
    """Test building with both DH and DC (Case 2)"""

def test_district_plant():
    """Test district plant final energy calculation"""

def test_booster_system():
    """Test building with DH + booster for DHW"""

def test_compilation_files():
    """Test aggregation and compilation file generation"""
```

### Phase 5: Documentation (Priority: LOW)

**Files:**
- `cea/analysis/final_energy/README.md` - User guide
- `cea/analysis/final_energy/AGENTS.md` - Agent/developer guide
- Update main docs: `docs/modules/final-energy.rst`

---

## 5. Case Logic

### 5.1 Case Definitions

```python
CASES = {
    1: "Standalone (all services)",
    2: "DH + DC (centralized heating + cooling)",
    3: "DH only (centralized heating + standalone cooling)",
    4: "DC only (standalone heating + centralized cooling)",
    4.01: "DC + booster for space heating",
    4.02: "DC + booster for hot water",
    4.03: "DC + booster for both space heating and hot water",
}
```

### 5.2 Case Determination Logic

```python
def determine_case(
    building_name: str,
    dh_connected: bool,
    dc_connected: bool,
    has_hs_booster: bool,
    has_dhw_booster: bool
) -> tuple[float, str]:
    """
    Determine case number and description for a building.

    Returns: (case_number, case_description)
    """

    if dh_connected and dc_connected:
        return (2, CASES[2])
    elif dh_connected and not dc_connected:
        return (3, CASES[3])
    elif not dh_connected and dc_connected:
        if has_hs_booster and has_dhw_booster:
            return (4.03, CASES[4.03])
        elif has_hs_booster:
            return (4.01, CASES[4.01])
        elif has_dhw_booster:
            return (4.02, CASES[4.02])
        else:
            return (4, CASES[4])
    else:
        return (1, CASES[1])
```

---

## 6. Data Flow Diagram

```
Input Files                 Processing                      Output Files
===========                 ==========                      ============

supply.csv                                                  B1001.csv
  (or config params)  →  calculate_building_final_energy  →  B1002.csv
                            ├─ Read demand from demand/        ...
demand/B####.csv            ├─ Load assemblies/components   B1017.csv
                            ├─ Apply efficiency
assemblies/*.dbf            ├─ Calculate carriers           xxx_DH_plant_001.csv
components/*.dbf            └─ Determine case               xxx_DC_plant_001.csv

thermal-network/            calculate_plant_final_energy
  {network}/                  ├─ Read plant consumption     final_energy_buildings.csv
  plant/                      ├─ Load plant equipment         (summary by entity)
                              └─ Calculate carriers

zone.shp                    aggregate_buildings_summary     final_energy.csv
networks/                     ├─ Sum hourly → annual          (breakdown by service)
  {network}/                  ├─ Calculate peaks
  edges.shp                   └─ Join metadata
  nodes.shp
```

---

## 7. Key Decisions

### 7.1 Whatif Name Handling

**Production Mode (overwrite-supply-settings = False):**
- Uses `supply.csv` for system configurations
- Output folder: `/outputs/data/final-energy/baseline/`
- whatif_name: `"baseline"` (hardcoded)

**What-If Mode (overwrite-supply-settings = True):**
- Uses config parameters (`supply-type-hs`, `supply-type-dhw`, etc.)
- Output folder: `/outputs/data/final-energy/{what-if-name}/`
- whatif_name: From `config.final_energy.what_if_name`

### 7.2 District Plant Naming from Shapefile

**Approach:** Use actual plant node names from network shapefile

```python
# For network "xxx" with plants named in shapefile:
# - Node "NODE_001" (type: PLANT, DH) → xxx_DH_NODE_001.csv
# - Node "PLANT_A" (type: PLANT, DC) → xxx_DC_PLANT_A.csv
# - Node "CENTRAL" (type: PLANT, DH) → xxx_DH_CENTRAL.csv

# For network "qqq" with different naming:
# - Node "001" (type: PLANT, DH) → qqq_DH_001.csv
# - Node "COOLING_PLANT" (type: PLANT, DC) → qqq_DC_COOLING_PLANT.csv
```

**Implementation:**
```python
# Read network shapefile
network_edges = gpd.read_file(locator.get_network_layout_edges_shapefile(network_name, network_type))
network_nodes = gpd.read_file(locator.get_network_layout_nodes_shapefile(network_name, network_type))

# Find PLANT nodes
plant_nodes = network_nodes[network_nodes['Type'] == 'PLANT']

# Get plant names from 'Name' or 'Building' column
for idx, plant_row in plant_nodes.iterrows():
    plant_name = plant_row.get('Name') or plant_row.get('Building')
    plant_file = locator.get_final_energy_plant_file(network_name, network_type, plant_name)
    # Calculate and save plant final energy
```

**Key Points:**
- Plant names come directly from shapefile `Name` or `Building` field
- NO sequential numbering (001, 002, etc.) unless that's the actual node name
- Supports any naming convention used in the network shapefile
- Multiple plants of same type use their individual node names

### 7.3 Missing Data Handling

**If thermal-network results missing:**
- Raise clear error with instructions
- Error message: "Building {name} is connected to district network '{network}' but thermal-network results not found. Please run: cea thermal-network --network-name {network}"

**If supply.csv missing assemblies:**
- Raise clear error with validation message
- Error message: "Building {name} has invalid supply system '{code}' in supply.csv. Available options: {valid_codes}"

**If component database missing:**
- Raise clear error with database path
- Error message: "Component '{code}' not found in database. Check: {database_path}"

---

## 8. Validation Rules

### 8.1 Pre-Calculation Validation

```python
def validate_inputs(
    buildings: list[str],
    network_name: str,
    locator: InputLocator,
    config: Configuration
) -> None:
    """
    Validate all required inputs exist before calculation.

    Checks:
    1. Demand files exist for all buildings
    2. Assemblies database exists and is readable
    3. Components database exists and is readable
    4. If network selected:
       - Network shapefile exists
       - Thermal-network results exist
       - Building connectivity matches supply.csv
    5. Supply.csv contains valid assembly codes
    6. Booster parameters are valid (if used)
    """
```

### 8.2 Post-Calculation Validation

```python
def validate_outputs(
    building_dfs: dict[str, pd.DataFrame],
    plant_dfs: dict[str, pd.DataFrame],
    locator: InputLocator
) -> None:
    """
    Validate calculation results are physically reasonable.

    Checks:
    1. All values are non-negative
    2. Final energy ≥ demand (efficiency ≤ 1.0 makes no sense)
    3. Carrier sum matches total
    4. Peak values are consistent
    5. No NaN or inf values
    6. All buildings have 8760 rows
    """
```

---

## 9. Performance Considerations

### 9.1 Multiprocessing

**Strategy:** Parallelize building calculations

```python
from multiprocessing import Pool

def main(config: Configuration):
    buildings = get_zone_building_names(locator)

    if config.multiprocessing:
        n_processes = get_number_of_processes(config)
        with Pool(n_processes) as pool:
            building_dfs = pool.starmap(
                calculate_building_final_energy,
                [(b, locator, config) for b in buildings]
            )
    else:
        building_dfs = [
            calculate_building_final_energy(b, locator, config)
            for b in buildings
        ]
```

### 9.2 Memory Optimization

**Approach:** Write files immediately, don't hold all in memory

```python
def main(config: Configuration):
    # Process and save one building at a time
    for building in buildings:
        df = calculate_building_final_energy(building, locator, config)
        output_file = locator.get_final_energy_building_file(building, whatif_name)
        df.to_csv(output_file, index=False)

    # Then read back for aggregation (only aggregate stats, not full timeseries)
    summary_df = aggregate_buildings_summary(buildings, locator, whatif_name)
    summary_df.to_csv(locator.get_final_energy_buildings_file(whatif_name), index=False)
```

---

## 10. Summary

### File Count Estimate

For a scenario with:
- 100 buildings
- 1 DH network (1 plant)
- 1 DC network (1 plant)
- 3 what-if scenarios + baseline

**Total files:**
- Hourly files: (100 buildings + 2 plants) × 4 scenarios = **408 files**
- Compilation files: 2 files × 4 scenarios = **8 files**
- **Grand total: 416 files**

### Disk Space Estimate

**Per building hourly file:**
- 8760 rows × ~30 columns × 10 bytes/value ≈ **2.6 MB**

**Per scenario:**
- 102 entities × 2.6 MB = **265 MB**

**Total for 4 scenarios:**
- 4 × 265 MB ≈ **1.06 GB**

### Calculation Time Estimate

**Per building:**
- Read demand: 0.1s
- Load databases: 0.05s (cached)
- Calculate carriers: 0.2s
- Write CSV: 0.1s
- **Total: ~0.45s per building**

**For 100 buildings (8 cores):**
- 100 buildings / 8 cores × 0.45s ≈ **5-6 seconds**

**Including compilation:**
- Buildings: 6s
- Plants: 1s
- Aggregation: 2s
- **Total: ~10 seconds**

---

**END OF BACKEND PLAN**
