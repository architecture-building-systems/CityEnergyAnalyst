# CEA Variable & File Glossary

A reference of the **179** input, intermediate, and output files used by the City Energy Analyst, grouped by feature. Each entry lists the file path, the script that produces it, the scripts that consume it, and the full column schema with type, unit, and valid values.

_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. Re-run after modifying the schema to refresh._

---

## Categories

| # | Category | Files |
|---|----------|------:|
| 00 | [User Inputs](00-user-inputs.md) | 6 |
| 02 | [Solar Radiation Analysis](02-solar-radiation.md) | 4 |
| 03 | [Renewable Energy Potential Assessment](03-renewable-energy.md) | 15 |
| 04 | [Energy Demand Forecasting](04-demand-forecasting.md) | 3 |
| 05 | [Thermal Network Design](05-thermal-network.md) | 25 |
| 06 | [Life Cycle Analysis (BETA)](06-life-cycle-analysis.md) | 24 |
| 07 | [Energy Supply System Optimisation](07-supply-optimisation.md) | 35 |
| 08 | [Data Management](08-data-management.md) | 66 |
| 09 | [Utilities](09-utilities.md) | 1 |

---

## Schema Hygiene

⚠️ **35 stale schema entries** detected — see [Stale Schema Entries](_stale-entries.md) for the cleanup punch list. These are entries in `cea/schemas.yml` with no matching `InputLocator` method; they appear in the per-category pages with a ⚠️ marker.

---

## Reading a Glossary Entry

Each file has a heading with its **locator method** (the function on `InputLocator` that returns its path), followed by:

- **Path** — relative to the scenario folder
- **File type** — `csv`, `shp`, `dbf`, `xlsx`, `epw`, `tif`, etc.
- **Created by** — the script that writes the file (empty for user inputs)
- **Used by** — scripts that read the file downstream
- A column table with **Variable**, **Description**, **Type**, **Unit**, and **Values**

The **Values** column auto-summarises valid ranges: `{min...max}` for numeric, `{true, false}` for boolean, `{a, b, c}` for choice, `alphanumeric` for free-form strings.

---

## How to Regenerate

```bash
pixi run python scripts/generate_tutorial_glossary.py
```

Run this whenever `cea/schemas.yml` changes. The generator is also safe to wire into CI via the same command.
