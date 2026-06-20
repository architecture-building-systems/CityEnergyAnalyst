# Stale Schema Entries

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`._

**35** entries in `cea/schemas.yml` have no matching method on `InputLocator` (`cea/inputlocator.py`). They are dead schema definitions left behind after refactors and can be removed.

Of those, **8** are still referenced by name (as string literals) in `cea/datamanagement/databases_verification.py`. Those references must be updated or removed before the schema entry can be deleted safely.

---

## Punch list

| Locator name | Category | Path | Still referenced by string? |
|--------------|----------|------|:---:|
| `get_building_property_schedules_monthly_multiplier` | Data Management | `inputs/building-properties/schedules/MONTHLY_MULTIPLIERS.csv` |  |
| `get_database_air_conditioning_systems` | Data Management | `inputs/technology/assemblies/HVAC.xlsx` | yes |
| `get_database_components_conversion_absorption_chillers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/ABSORPTION_CHILLERS.csv` |  |
| `get_database_components_conversion_boilers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/BOILERS.csv` |  |
| `get_database_components_conversion_bore_holes` | Data Management | `inputs/database/COMPONENTS/CONVERSION/BORE_HOLES.csv` |  |
| `get_database_components_conversion_cogeneration_plants` | Data Management | `inputs/database/COMPONENTS/CONVERSION/COGENERATION_PLANTS.csv` |  |
| `get_database_components_conversion_cooling_towers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/COOLING_TOWERS.csv` |  |
| `get_database_components_conversion_fuel_cells` | Data Management | `inputs/database/COMPONENTS/CONVERSION/FUEL_CELLS.csv` |  |
| `get_database_components_conversion_heat_exchangers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/HEAT_EXCHANGERS.csv` |  |
| `get_database_components_conversion_heat_pumps` | Data Management | `inputs/database/COMPONENTS/CONVERSION/HEAT_PUMPS.csv` |  |
| `get_database_components_conversion_hydraulic_pumps` | Data Management | `inputs/database/COMPONENTS/CONVERSION/HYDRAULIC_PUMPS.csv` |  |
| `get_database_components_conversion_photovoltaic_panels` | Data Management | `inputs/database/COMPONENTS/CONVERSION/PHOTOVOLTAIC_PANELS.csv` |  |
| `get_database_components_conversion_photovoltaic_thermal_panels` | Data Management | `inputs/database/COMPONENTS/CONVERSION/PHOTOVOLTAIC_THERMAL_PANELS.csv` |  |
| `get_database_components_conversion_power_transformers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/POWER_TRANSFORMERS.csv` |  |
| `get_database_components_conversion_solar_collectors` | Data Management | `inputs/database/COMPONENTS/CONVERSION/SOLAR_COLLECTORS.csv` |  |
| `get_database_components_conversion_thermal_energy_storages` | Data Management | `inputs/database/COMPONENTS/CONVERSION/THERMAL_ENERGY_STORAGES.csv` |  |
| `get_database_components_conversion_unitary_air_conditioners` | Data Management | `inputs/database/COMPONENTS/CONVERSION/UNITARY_AIR_CONDITIONERS.csv` |  |
| `get_database_components_conversion_vapor_compression_chillers` | Data Management | `inputs/database/COMPONENTS/CONVERSION/VAPOR_COMPRESSION_CHILLERS.csv` |  |
| `get_database_components_feedstocks_biogas` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/BIOGAS.csv` |  |
| `get_database_components_feedstocks_coal` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/COAL.csv` |  |
| `get_database_components_feedstocks_drybiomass` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/DRYBIOMASS.csv` |  |
| `get_database_components_feedstocks_grid` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/GRID.csv` |  |
| `get_database_components_feedstocks_hydrogen` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/HYDROGEN.csv` |  |
| `get_database_components_feedstocks_naturalgas` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/NATURALGAS.csv` |  |
| `get_database_components_feedstocks_oil` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/OIL.csv` |  |
| `get_database_components_feedstocks_solar` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/SOLAR.csv` |  |
| `get_database_components_feedstocks_wetbiomass` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/WETBIOMASS.csv` |  |
| `get_database_components_feedstocks_wood` | Data Management | `inputs/database/COMPONENTS/FEEDSTOCKS/FEEDSTOCKS_LIBRARY/WOOD.csv` |  |
| `get_database_construction_standards` | Data Management | `inputs/technology/archetypes/CONSTRUCTION_STANDARDS.xlsx` | yes |
| `get_database_conversion_systems` | Data Management | `inputs/technology/components/CONVERSION.xlsx` | yes |
| `get_database_distribution_systems` | Data Management | `inputs/technology/components/DISTRIBUTION.xlsx` | yes |
| `get_database_envelope_systems` | Data Management | `inputs/technology/assemblies/ENVELOPE.xlsx` | yes |
| `get_database_feedstocks` | Data Management | `inputs/technology/components/FEEDSTOCKS.xlsx` | yes |
| `get_database_supply_assemblies` | Data Management | `inputs/technology/assemblies/SUPPLY.xlsx` | yes |
| `get_database_use_types_properties` | Data Management | `inputs/technology/archetypes/use_types/USE_TYPE_PROPERTIES.xlsx` | yes |

---

## How to clean up

For each entry above:

1. Confirm no `InputLocator` method is being added back — `grep -n 'def get_<name>' cea/inputlocator.py`.
2. Remove the entry from `cea/schemas.yml`.
3. If the locator appears in the 'still referenced by string' column above, also remove or replace its entry in `cea/datamanagement/databases_verification.py` (around lines 416-423).
4. Re-run `scripts/generate_tutorial_glossary.py` to regenerate the glossary and this report.

[← Back to Glossary index](index.md)
