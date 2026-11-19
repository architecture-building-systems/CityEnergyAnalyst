# PV analytics as Canvas KPI cards — plan

Status: researched 2026-11-16; steps 1–5 implemented the same day on
`update-the-summary-feature`; step 6 is a follow-up. Builds on the Summary & Analytics PV
analytics (`docs/developer/summary-solar-plan.md`, part B).

## Goal

Canvas KPI cards for a final-energy what-if's PV generation-to-load, self-consumption and
self-sufficiency — **computed by the same code as the summary**, so a card and the summary's
annual analytics can never disagree — replacing "Solar Share of Final Energy".

## Principle: one implementation

The summary already has the compute (`cea/import_export/result_summary.py`):
`calc_pv_analytics_by_period(df, period)` (hour-by-hour matching, per period) fed by an hourly
`generation_kWh` / `load_kWh` series. The KPI must call that, not re-implement it.

Not reused from the unmerged branch `adding-sc-ss-for-PV`: its `matched_share` formula (a second
implementation, with a "time period" that means a storage window — a different definition from
the summary's), the `target: formula` parameters and `time_periods` options it needed, and its
`carrier_from_column` (superseded by `classify_carrier_column`, #4139). Its KPI wording and the
`solar.yml` "MOVED" note are worth keeping.

## How KPIs are handled (constraints to follow)

- A KPI reads **one CSV** via one locator method; the resolver hands the loaded DataFrame to
  `calculators.evaluate(formula, df)`. Formula nodes are declared in `schema.py`.
- final-energy KPIs: category `energy-by-carrier`, the shared `whatif_name` parameter block,
  PV cards carry `annotation: installed_pv_by_orientation`; `info_note` = sentence, formula
  line, `in [%]`. The yml header records the source file and moved / dropped KPIs.
- The Canvas picker is registry-driven: **no GUI code** for new cards. A missing source file
  reports *unavailable*.

## Plan

1. **One source for the district series.** The district hourly file `final_energy.csv`
   (`get_final_energy_file(whatif)`) already has `PV_kWh` and `GRID_kWh` — PV and PVT
   electricity against all grid consumption, plants included (correct since #4139). Use it for
   the district in both places:
   - Summary: the district analytics read it (today they sum the buildings, which leaves out
     plants' electricity). Per-building analytics keep reading `B####.csv`.
   - KPI: its source file.
2. **Move the shared compute out of the summary** into a small module both can import without
   pulling in the summary's heavy dependencies, e.g. `cea/analysis/final_energy/pv_analytics.py`:
   `calc_pv_analytics_by_period` (+ its period-label and ratio helpers) and a
   `district_pv_series(df)` that maps `PV_kWh` / `GRID_kWh` to `generation_kWh` / `load_kWh`.
   `result_summary.py` imports them; no behaviour change.
3. **One KPI formula node, delegating:** `kind: pv_analytics`, `metric:
   generation_to_load | self_consumption | self_sufficiency`. The calculator builds the series
   from the source DataFrame, calls `calc_pv_analytics_by_period(series, 'annually')` and returns
   the metric × 100. No other parameters; the period is the year (matched hour by hour).
4. **Three KPIs** in `cea/kpi/definitions/final_energy.yml` — `final_energy.pv_generation_to_load_pct`,
   `final_energy.pv_self_consumption_pct`, `final_energy.pv_self_sufficiency_pct`; source
   `get_final_energy_file`, unit `%`, `better_direction: higher`, the what-if parameter, the PV
   annotation, notes in the house style (load = the what-if's grid electricity incl. heat pumps,
   boosters and plants; matched hour by hour). Update the `solar.yml` header ("MOVED").
5. **Replace `final_energy.solar_share_pct`** ("Solar Share of Final Energy",
   `(PV_MWh + SOLAR_MWh) ÷ TOTAL_MWh`). For PV it approximates generation-to-load (15.9% vs
   16.8% on `baseline_dh` / `with_pv`, nearly all-electric) and drifts with fuel or DH heating
   and solar heat; and it is ill-formed: it adds heat and electricity MWh as equals, and its
   `SOLAR` part includes DHW solar heat (`Qww_sys_SOLAR`) that is already inside `TOTAL` while
   PV is not.
   - Remove its yml entry; record it under the header's moved / dropped list with the reason.
   - **Alias** the old id to `final_energy.pv_generation_to_load_pct` so saved canvases keep
     working: a `KPI_ALIASES` map in `cea/kpi/registry.py` plus one resolve step wherever an id
     is looked up (`resolver.py`, `cea/interfaces/dashboard/api/kpis.py`). Aliases are not listed
     in the picker. The card's saved `whatif_name` carries over (same parameter). Check in the
     GUI that a saved card shows the new label.
6. **Optional follow-up — "Solar Thermal Generation-to-Load"**, symmetric with PV:
   `Σ solar heat generated ÷ Σ hot-water demand (Qww_sys)` — the load is hot water because CEA
   dispatches SC heat to DHW; say so in the note. Not part of this PR. Needs a new column:
   today `SOLAR` (`final_energy.csv` / `final_energy_buildings.csv`) mixes SC heat *delivered*
   to DHW by the tank dispatch (`Qww_sys_SOLAR_kWh`), PVT heat (credited to space heating, not
   DHW) and SC heat *generated* when SC is not the DHW primary; gross SC generation in DHW mode
   is deliberately not persisted (`calculation.py`, after the dispatch). Choose first:
   - **Solar fraction** ("Solar Thermal Share of Hot Water"): Σ delivered solar DHW heat ÷
     Σ `Qww_sys` — standard metric, data already computed; add e.g. `SOLAR_DHW_kWh` to
     `final_energy.csv`. The DHW analogue of PV self-sufficiency.
   - **Generation-to-load**: Σ gross SC heat ÷ Σ `Qww_sys` — mirrors PV, but needs gross SC
     generation persisted.
   Either way users re-run final-energy to see the card. Don't use `SOLAR ÷ Qww_sys`.

## Tests

- The shared module: existing summary tests keep passing after the move (they exercise the same
  function).
- KPI: the three values from a small `final_energy.csv` fixture (noon surplus / night load;
  generation-to-load > 100%); *unavailable* without the what-if; registry validates the new node.
- Consistency: for one fixture what-if, each card's value equals the summary's annual district
  analytics value.
- Alias: resolving `final_energy.solar_share_pct` returns generation-to-load's value; the alias
  is absent from the registry listing.

## Size

One backend PR, about half a day to a day (the alias adds a little). No GUI changes beyond
checking a saved card; no final-energy re-run needed.
