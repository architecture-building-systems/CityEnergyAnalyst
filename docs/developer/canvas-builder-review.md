# Canvas Builder review — improvements, not started

Status: reviewed 2026-10-25, **not started**. A list of improvements for later PRs, not a record
of work done. Covers the GUI `src/features/canvas/` (~16,800 lines) and the backend canvas API
(`api/canvas.py`, `lib/canvas_storage.py`, `lib/canvas_capture.py`, ~1,400 lines).

Reviewed by area — persistence, backend API, safety, fetching, duplication, dead code, docs,
tests. Not reviewed line by line: the logic inside `canvasStore.js`, `CanvasColumn.jsx`,
`PathwayMultiView.jsx` and `NavigatorCard.jsx`.

## 1. Safety and data integrity (backend) — do first

| Issue | Where | Fix |
|---|---|---|
| Card ids are used as folder names unchecked: export writes plot HTML to `data/<card_id>/`, and ids come from the saved YAML (`Dict[str, CardConfig]`, unconstrained). A crafted canvas (PUT body or imported zip) can make export write outside the canvas folder — most serious in the deployed app. | `canvas_capture.py` (`_capture_plot_card`), `locator.get_canvas_card_data_folder`, `canvas_storage.py` models | Constrain card ids to the generated hex shape in the models; keep the export write under the canvas folder (resolved-path check). |
| Zip import has no limits: the whole upload is read into memory; no cap on size, unpacked size or file count; the path check splits on `/` only, so `\` names are not caught (Windows server). | `api/canvas.py` (`import_canvas`), `canvas_storage.py` (`_zip_top_level`, `import_canvas_zip`) | Size / unpacked-size / member-count caps; check every resolved member path stays inside the target folder. |
| YAML writes are not atomic: a crash or concurrent read mid-write leaves a truncated file, and the canvas no longer loads. | `canvas_storage.py` (`_write_yaml`) | Write to a temp file in the same folder, then `os.replace`. |
| Last write wins, silently: two tabs or users autosaving one canvas overwrite each other. | `write_canvas`, autosave in `useCanvasPersistence.js` | Optimistic check on `updated_at` (reject a save based on an older version; GUI reloads or warns). |

## 2. Performance

- **No plot render cache.** Each plot card in each column runs its plot script on every open
  (`POST /reports/plot-custom` → `plot_dispatch.render_plot_html`); only 30 s of React Query
  caching. 4 columns × 5 plots = 20 script runs per open, per user when deployed. Cache by
  (script, parameters, input files' mtimes), as `map_layers/base.py::cache_output` does.
- **KPI values refetch on every mount** (`staleTime: 0` in `useFetchKpis.js::useFetchKpiValue`).
  `useKpiCacheInvalidator` already clears KPI queries when a tool finishes, so a longer stale
  time is safe.
- **Autosave always sends the full bundle** (all three YAMLs) although `PUT /canvas/{name}`
  accepts any subset. Fine locally; needless traffic on network storage.

## 3. Code health

- **Dead hooks** in `hooks/useCanvasData.js`: `useFetchWhatifs`, `useFetchSummary`,
  `useFetchFeatures`, `useFetchToolParams` — no callers (the `useFetchToolParams` in
  `features/tools/` is a different function). Check whether the `/reports/whatifs`,
  `/reports/summary`, `/reports/features` endpoints have other callers before removing them.
- **Duplicated map-view helpers:** `VIEW_STATE_KEYS` + snapshot helpers in both
  `FeatureCardMap.jsx` and `PathwayMultiView.jsx`, alongside `utils/mapView.js`. Merge.
- **Fragile pathway-state column identity:** a `pathway-state` column is identified by a
  client-built path (`canvasStore.js::childStateScenarioPath`), translated back to parent +
  state per request (`scenarioRequestContext`). A caller that is not such a column gets the raw
  path sent as a scenario name — the cause of the pathway-multi row-map bug. Store
  `{ scenario, pathwayName, year }` as the identity instead. Medium refactor, own PR.
- **Stale "Phase N" comments** describing done work as future: `canvasStore.js` (Phase 2e, 5,
  6), `CanvasColumn.jsx` (Phase 6, 7).
- **Oversized files:** `canvasStore.js` 1,409, `CanvasColumn.jsx` 1,270, `PathwayMultiView.jsx`
  1,102, `NavigatorCard.jsx` 1,034 lines. Split `canvasStore.js` by slice (cards, views,
  persistence, pathway) first.
- **`features/canvas/CLAUDE.md` is 837 lines** against the repo's <150-line guideline; trim to
  patterns and gotchas, move explanation to `docs/`.
- **Undo doesn't redraw map cards:** undo restores `mapView` / `filters` /
  `mapLayerParameters` on the card but not in the card's live map store, until the next change.

## 4. Tests

- **GUI:** 10 test files, all utilities, hooks and the map-view work. Untested: core store
  actions (`addCard`, `applyCardLayouts` fan-out, view transitions, undo) and
  `useCanvasPersistence` (debounce, load resync, undo flush).
- **Backend:** no tests for the canvas API, storage or export capture (nothing in `cea/tests`).
  Add with the section 1 fixes.

## Suggested order

1. Section 1, with backend tests — small to medium, highest value for the deployed app.
2. Quick clean-up: dead hooks, duplicated helpers, stale comments, KPI stale time — small.
3. Plot render cache — medium.
4. Column identity refactor; `canvasStore.js` split — one PR each.
