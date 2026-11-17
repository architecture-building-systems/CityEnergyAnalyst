# Summary & Analytics: solar — plan, not started

Status: implemented on branch `summary-solar-potentials-analytics` (2026-11-16). Kept as the
design record for that PR; delete it once merged if it is no longer useful.

## Why

"Where is solar installed?" is answered in three places: the solar potential tools
(`photovoltaic`, `photovoltaic-thermal`, `solar-collector`), final-energy's
`[solar-technology]` (what a what-if installs, per surface and building), and
`result-summary:solar-technologies`. The third duplicates the others and does not do what it
says. Rule after this change: **potential tools say what could be produced, final-energy says
what is installed, the summary only reports.**

## Findings (`cea/import_export/result_summary.py`)

1. **`solar-technologies` switches families, not panel types.** Picking `PV_PV1` turns on PV
   for every panel type in the database (`_get_solar_metric_lists`; the per-type loop in
   `get_results_path`, ~line 320). Missing result files are skipped per file.
2. **PV analytics are dead code.** `calc_pv_analytics` (generation-to-load, self-consumption,
   self-sufficiency) has no caller since `587b8467b` (2026-04-03), which left
   `# TODO: re-enable with what-if-aware PV analytics`. They used the potential tools' output
   against the demand's grid electricity, per surface, at each selected resolution.
3. **Self-consumption and self-sufficiency compare period totals.**
   `calc_self_consumption_by_period` and `calc_self_sufficiency_by_period` take
   `min(Σgen, Σload)` over each period, which assumes perfect storage within the period: the
   value then depends on the resolution (a year allows shifting energy across seasons), and
   annual self-sufficiency is just generation-to-load capped at 1. The standard definition
   (e.g. Luthander et al. 2015, *Applied Energy*, PV self-consumption review; the load and
   supply cover factors in the net-zero building literature) matches each time step:
   `Σ min(gen_h, load_h)`, then sums over the reported period. The period-total figure is the
   net energy balance, which `calc_solar_energy_penetration_by_period` (generation-to-load,
   `Σgen ÷ Σload`) already reports — that one is correct.
4. **"Installed" area is potential area.** `PV_installed_area_*[m2]`, `PVT_*_installed_area_*`,
   `SC_*_installed_area_*` (65 uses, all in `result_summary.py`) hold the potential tools'
   panel area. Same wording in the plot option `solar_technology_area_installed_for_respective_surface`.
5. **Non-solar potentials are never summarised.** `list_metrics_other_renewables`
   (geothermal, sewage, water body) is defined but nothing appends it.

## Plan

### A. Replace `solar-technologies` with `solar-energy-potentials`

- `cea/default.config` `[result-summary]`: `solar-energy-potentials = true`,
  `BooleanParameter`, help: "Summarise solar energy potentials (PV, PVT and solar collectors)
  for every panel type with results." Remove `solar-technologies`.
- `result_summary.py` (~2737, ~2810): when on, include each family and panel type **that has
  at least one result file** — verify what an empty family writes today and guard it, so a
  PV-only scenario gets no empty PVT/SC outputs.
- Remove `SolarPanelMultiChoiceParameter` (`config.py`; only user is this parameter; plugins
  `cea-pro`, `cea-plugin-bia` don't use it). Keep `SolarPanelChoicesMixin` (final-energy uses it).
  Regenerate `config.pyi`. GUI `Parameter.jsx` case for it can go in the GUI repo.

### B. Re-enable PV analytics, for installed PV

Same three analytics, per building and district, at every selected reporting period (daily,
monthly, seasonally, annually), for each what-if in `what-if-name` (one dropdown since 2026-11-17; was `what-if-name-final-energy`) that has PV.
Gated on `include-advanced-analytics`.

- Hourly, per building, from final-energy `B####.csv`: generation = PV and PVT-electric
  columns; load = all GRID consumption (`E_sys`, boosters, heat pumps), classified with
  `classify_carrier_column` (#4139).
- Formulas (finding 3): self-consumption `Σ min(gen_h, load_h) ÷ Σ gen_h`, self-sufficiency
  `Σ min(gen_h, load_h) ÷ Σ load_h`, matched hour by hour and summed per period;
  generation-to-load `Σ gen ÷ Σ load` unchanged. The district file matches the buildings'
  summed generation and load (buildings share surplus); per-building files don't.
- Totals across surfaces, not per surface. Output: `pv/analytics/pv_installed_<what-if>_…`.
- **Not for potentials** (decided after a first version had them): a potential assumes every
  surface the potential tool considers is installed, and demand outputs carry no grid
  electricity, so the load would differ from the installed case — the two sets would not be
  comparable. Use a final-energy what-if for analytics.

### C. Wording: potential, not installed

- Rename the summary metrics to `*_potential_area_*[m2]` (e.g. `PV_potential_area_roof[m2]`)
  for PV, PVT and SC; update `map_metrics_and_cea_columns` and every use in `result_summary.py`.
  Plots pair raw columns (`area_PV_m2`, `PV_roofs_top_m2`), so they are unaffected.
- Plot option `solar_technology_area_installed_for_respective_surface`: it is a stored value
  (configs, saved canvases) — change only its label/help ("solar panel area of each surface"),
  not the value.
- Breaking for anyone reading exported summary CSVs by column name: call it out in the PR.

### D. Other items

- Finding 5: either add non-solar potentials to the summary (a separate toggle) or delete the
  unused list. Decision needed; not part of A–C.
- Optional follow-up: a PV self-sufficiency KPI from final-energy, which `kpi/definitions/solar.yml`
  dropped for lack of a load column.

## Tests (`cea/tests/`, none cover result-summary solar today)

- Analytics formulas: hourly matching on a small series where period totals and hourly
  matching differ (surplus at noon, deficit at night), at daily and annual resolution.
- Installed source: a fake what-if B####.csv (PV on two facades, GRID from `E_sys` and a
  booster) → expected generation, load and the three values.
- Toggle: PV results only → PV outputs written, no empty PVT/SC outputs; toggle off → none.
- Renamed metrics: `map_metrics_and_cea_columns` round trip for the new names.

## Order and size

C and A first (small, mostly mechanical), then B (medium). About
one to one and a half days including tests. One backend PR; the GUI `Parameter.jsx` clean-up
is separate and optional.
