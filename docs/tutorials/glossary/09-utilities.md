# Utilities

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Do not hand-edit — re-run the script to refresh._

Files in this category: **1**

---

## Files

- [`get_multi_criteria_analysis`](#get_multi_criteria_analysis)

---

### `get_multi_criteria_analysis`

- **Path**: `outputs/data/multicriteria/gen_2_multi_criteria_analysis.csv`
- **File type**: `csv`
- **Created by**: `multi_criteria_analysis`
- **Used by**: _(none)_

| Variable | Description | Type | Unit | Values |
|----------|-------------|------|------|--------|
| `Capex_a_sys_building_scale_USD` | Annualized Capital costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Capex_a_sys_district_scale_USD` | Capital costs of district-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_a_sys_USD` | Capital costs of all systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_building_scale_USD` | Capital costs of building-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_district_scale_USD` | Capital costs of district-scale systems | float | `[USD 2015]` | {0.0...n} |
| `Capex_total_sys_USD` | Capital costs of all systems | float | `[USD 2015]` | {0.0...n} |
| `generation` | Generation or iteration | int | `[-]` | {0...n} |
| `GHG_rank` | Rank for emissions | float | `[-]` | {0.0...n} |
| `GHG_sys_building_scale_tonCO2` | Green house gas emissions of building-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_district_scale_tonCO2` | Green house gas emissions of building-scale systems | float | `[ton CO2-eq/yr]` | {0.0...n} |
| `GHG_sys_tonCO2` | Green house gas emissions of all systems | float | `[ton CO2-eq]` | {0.0...n} |
| `individual` | system number | int | `[-]` | {0...n} |
| `individual_name` | Name of system | string | `NA` | alphanumeric |
| `normalized_Capex_total` | normalization of CAPEX | float | `[-]` | {0.0...n} |
| `normalized_emissions` | normalization of GHG | float | `[-]` | {0.0...n} |
| `normalized_Opex` | Normalization of OPEX | float | `[-]` | {0.0...n} |
| `normalized_TAC` | normalization of TAC | float | `[-]` | {0.0...n} |
| `Opex_a_sys_building_scale_USD` | Operational costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_district_scale_USD` | Operational costs of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `Opex_a_sys_USD` | Operational costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_rank` | Rank of TAC | float | `[-]` | {0.0...n} |
| `TAC_sys_building_scale_USD` | Equivalent annual costs of building-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_district_scale_USD` | Equivalent annual of district-scale systems | float | `[USD 2015/yr]` | {0.0...n} |
| `TAC_sys_USD` | Equivalent annual costs of all systems | float | `[USD 2015/yr]` | {0.0...n} |
| `user_MCDA` | Best system according to user mult-criteria weights | float | `[-]` | {0.0...n} |
| `user_MCDA_rank` | Rank of Best system according to user mult-criteria weights | float | `[-]` | {0.0...n} |

---

[← Data Management](08-data-management.md) | [Glossary index](index.md)
