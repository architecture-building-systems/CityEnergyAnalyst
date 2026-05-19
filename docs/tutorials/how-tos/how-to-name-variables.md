# Variable naming in CEA

A reference for naming variables in CEA. Read this **before** adding new variables to the code so that names stay consistent with the rest of the codebase.

> 📖 For the full list of variables actually in use (with descriptions, units, and ranges), see the **[Variable & File Glossary](../glossary/index.md)** — auto-generated from `cea/schemas.yml`.

---

## 1. Demand-side load nomenclature

```
(LOAD_TYPE)(LOAD)_(LOSSES)_(UNITS)
```

**Load type**

| Code | Meaning |
|------|---------|
| `Q` | Thermal |
| `E` | Electrical |

**Load**

| Code | Meaning |
|------|---------|
| `al` | Appliances |
| `cdata` | Data-centre cooling |
| `cs` | Space cooling |
| `cre` | Refrigeration |
| `hs` | Space heating |
| `l` | Lighting |
| `pro` | Industrial processes |
| `T` | Total |
| `ww` | Hot water (domestic) |

**Losses**

| Code | Meaning |
|------|---------|
| `sys` | Includes emission, distribution, and storage losses inside the building |
| *(omitted)* | End-use demand, no system losses |

**Units**

| Code | Meaning |
|------|---------|
| `W` | Watts |
| `kWh` | Kilowatt-hours |
| `MWhyr` | Megawatt-hours per year |

**Examples**

- `El_sys_W` — End-use electricity for lighting, including system losses (Watts)
- `El_W` — End-use electricity for lighting, no system losses (Watts)
- `ET_sys_MWhyr` — Total end-use electricity demand including system losses (MWh/yr)

---

## 2. Supply-side load nomenclature

```
(LOAD_TYPE)(LOAD)_(GENERATION_UNIT)_(LOAD_DIRECTION)_(UNITS)
```

Load type, load, and units are the same as above.

**Generation unit codes**

CEA uses component codes from `inputs/database/COMPONENTS/CONVERSION/*.csv`. The most common short codes are:

| Code | Meaning |
|------|---------|
| `PV` | Photovoltaic panel |
| `PVT` | Photovoltaic-thermal hybrid |
| `SC` (`SC1`, `SC2`) | Solar collector — flat-plate (`SC1`) or evacuated tube (`SC2`) |
| `BO*` (e.g. `BO1`, `BO5`) | Boilers — gas, oil, wood, electric, etc. |
| `HP*` (e.g. `HP1`) | Heat pumps — air, water, ground source |
| `CH*` (e.g. `CH1`) | Vapor-compression chillers |
| `CT*` | Cooling towers |
| `FC` | Fuel cell |
| `CCGT` | Combined-cycle gas turbine |
| `GSHP` | Ground-source heat pump |

For the authoritative list, check `inputs/database/COMPONENTS/CONVERSION/`.

**Load direction**

| Code | Meaning |
|------|---------|
| `GRID` | To the local grid |
| `DIRECT` | To the direct load |

**Examples**

- `Qww_PVT_DIRECT_MWhyr` — Heat from PVT supplied to the direct hot-water load (MWh/yr)
- `ET_PV_GRID_MWhyr` — Total PV electricity exported to the grid (MWh/yr)

---

## 3. Cost nomenclature

```
(COST_TYPE_1)_(COST_TYPE_2)_(COST_TYPE_3)_(GENERATION_UNIT)_(UNITS)
```

**Cost type 1**

| Code | Meaning |
|------|---------|
| `Capex` | Capital expenditure |
| `Opex` | Operational expenditure |

**Cost type 2**

| Code | Meaning |
|------|---------|
| `T` | Total |
| `a` / `A` | Annualised |

**Cost type 3**

| Code | Meaning |
|------|---------|
| `var` | Variable |
| `fixed` | Fixed |

**Units**

| Code | Meaning |
|------|---------|
| `USD` | US dollars (year specified by the column, often 2015) |
| `MUSD` | Million USD |
| `USD2015kWh` | Per-kWh price expressed in 2015 US dollars |

**Examples (current column names in CEA outputs)**

- `Capex_a_USD` — Annualised CAPEX, total (USD/yr)
- `Capex_a_building_scale_USD` — Annualised CAPEX, building-scale subset
- `Opex_var_a_USD` — Annualised variable OPEX (USD/yr)
- `Opex_var_buy_USD2015kWh` — Variable OPEX rate for purchased energy (2015 USD per kWh)

---

## 4. Fuel / feedstock nomenclature

```
(FUEL_TYPE)_(FUEL_DIRECTION)_(GENERATION_UNIT)_(UNITS)
```

**Fuel type**

The feedstock codes used in `inputs/database/COMPONENTS/FEEDSTOCKS/`:

| Code | Meaning |
|------|---------|
| `NATURALGAS` | Natural gas |
| `OIL` | Heating oil |
| `COAL` | Coal |
| `WOOD` | Wood |
| `BIOGAS` | Biogas |
| `DRYBIOMASS` | Dry biomass |
| `WETBIOMASS` | Wet biomass |
| `HYDROGEN` | Hydrogen |
| `SOLAR` | On-site solar thermal |
| `GRID` | Grid electricity |

**Fuel direction**

| Code | Meaning |
|------|---------|
| `used` | Fuel consumed by the unit |
| `gen` | Resource produced by the unit |

**Examples**

- `NATURALGAS_used_BO1_W` — Natural gas consumed by boiler type 1 (W)
- `WOOD_used_Furnace_W` — Wood consumed by a furnace (W)

---

## 5. Emissions nomenclature

```
(LCA_TYPE)_(GENERATION_UNIT)_(UNITS)
```

**LCA type**

| Code | Meaning |
|------|---------|
| `GHG` | Greenhouse-gas emissions |
| `PEN` | Primary energy (legacy) |

**Units**

| Code | Meaning |
|------|---------|
| `kgCO2` | Kilograms of CO₂-equivalent |
| `tonCO2` | Tonnes of CO₂-equivalent |
| `kgCO2m2` | kg CO₂-equivalent per m² (intensity) |
| `kgCO2MJ` | kg CO₂-equivalent per MJ (emission factor) |
| `MJoil` | Mega-Joules oil equivalent (legacy PEN) |
| `GJoil` | Giga-Joules oil equivalent (legacy PEN) |

**Examples (current column names in CEA outputs)**

- `GHG_floor_kgCO2m2` — Embodied emissions intensity of the floor envelope component
- `GHG_biogenic_wall_kgCO2m2` — Biogenic carbon stored in the wall envelope (negative)
- `GHG_kgCO2MJ` — Emission factor of an energy carrier

---

## General conventions

- **Snake_case** for column names with units appended (`Qhs_sys_kWh`), not camelCase.
- **Plurals for collections** — use plural names for lists, tuples, sets, dicts (e.g. `buildings`, not `building_list`).
- **No abbreviations** other than loop indices. Short names are not cooler.
- **Domain-faithful names** — names should match the literature so a reader can connect code to publications.
- **Same thing, same name** — don't switch between `temperature_C` and `T_C` in different files for the same quantity.
- **Spelling matters**, including in comments. PyCharm's spellchecker catches most issues.

## When in doubt

- Look at adjacent columns in `cea/schemas.yml` — odds are someone already named this quantity.
- Search the **[Variable & File Glossary](../glossary/index.md)** for similar variables.
- Ask in [Discussions](https://github.com/architecture-building-systems/CityEnergyAnalyst/discussions).
