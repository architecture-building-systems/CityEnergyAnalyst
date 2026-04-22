# Multi-Phase Thermal Network

Module: `cea.technologies.thermal_network.common.phasing`

## Data Model

Each **phase** corresponds to one `network-name` (e.g. `sub1`, `sub2`, `sub3`)
plus a completion year. A phase owns a complete per-phase layout (nodes +
edges + connected buildings), **not** a delta from the previous phase. The
multi-phase tool reconciles phases via `get_all_edges_across_phases()` which
takes the union of edge IDs seen in any phase's simulation result.

### Canonical Edge Identity (IMPORTANT)

Per-phase `name` columns (e.g. `PIPE0`, `PIPE1`, ...) are **NOT** stable
across phases. Each Part-1 run numbers its pipes independently starting
from `PIPE0`, so sub1's `PIPE1` and sub2's `PIPE1` may be **completely
different physical pipes**, while the same physical pipe can have
different names in each phase.

The engine must therefore key on **canonical edge id** — a sorted pair of
mm-rounded endpoint coordinates (`CanonicalEdgeId`). Helpers:

- `_canonical_edge_id(geom, precision=3)` → sorted `((x0,y0),(x1,y1))` tuple
- `_build_edge_maps(edges_gdf)` → `(name→cid, cid→name)` for one phase
- each phase dict carries `edge_name_to_cid` and `edge_cid_to_name`

Keyed by canonical id (not name):
- `phase_result['edge_diameters']`
- `phase_result['edge_lengths']`
- `sizing_decisions`
- `get_all_edges_across_phases` return set

Per-phase local names are recovered for display in CSV/shapefile writers
via the `edge_cid_to_name` map on each phase. Writers use the first-seen
name when the canonical id is shared across phases.

**Upstream invariant**: `network-layout` (Part 1) preserves original pipe
names via `_resolve_duplicate_pipe_names` — only genuine name collisions
are renamed. A blanket re-number would break cross-phase alignment even
at the name level (though the canonical-id keying protects against it
downstream regardless).

## Physical Model: Sunk Infrastructure

**Invariant**: once a pipe is installed in any phase, it stays in the trench
forever. No salvage value, no removal cost, no physical downsize. Connected
buildings, however, can change freely between phases (add or remove).

Consequences:

- Phase-N flow simulation uses only phase N's connected set. Decommissioned
  buildings contribute zero demand to phase N.
- A pipe whose downstream building was decommissioned is labelled **`idle`**
  in that phase: preserved DN, zero CAPEX, zero OPEX, still visible in the
  timeline shapefiles so the user can see "the pipe is there, just not
  flowing."
- A pipe that is reactivated later (its consumer comes back) keeps the
  originally-installed DN if demand fits, or triggers a `replace` if demand
  grew.
- The cost engine already computes the union of edges, so no separate
  `installed_edges_gdf` is needed — the union via `get_all_edges_across_phases`
  is authoritative.

## Per-Phase Action Vocabulary

Every edge × phase pair gets one action from:

| Action | Meaning | CAPEX |
|---|---|---|
| `none` | edge has not been installed yet in any prior phase | 0 |
| `install` | edge is being installed for the first time this phase | full |
| `replace` | required DN > installed DN, replace at multiplier | replace × multiplier |
| `keep` | required DN ≤ installed DN, pipe still flowing | 0 |
| `idle` | installed earlier, no flow this phase (building decommissioned) | 0 |

Downstream consumers that check `action` only match against `'install'` and
`'replace'` for cost accumulation (lines 565, 882, 885, 1070 in `phasing.py`).
New labels `'idle'` and `'keep'` fall through those checks safely.

## Pre-Flight Graph Check

`validate_phases()` calls `_validate_phase_graph()` per phase to catch the
footgun where decommissioning a trunk-middle building disconnects a
downstream branch. Error format names the orphaned consumer nodes. No check
for chronological order via `prev_buildings ⊆ curr_buildings` — reductions
are intentionally allowed.

## Shapefile Column Name Constraints

ESRI shapefiles truncate attribute names to **10 characters** silently.
Column names in the timeline/per-phase shapefiles use short forms:

- `ph_intro` / `yr_intro` — first phase the edge/node was introduced
- `ph_last` / `yr_last` — last active phase
- `idle_final` — 1 if the edge is idle in the final phase
- `num_repl`, `cost_USD`, `DN_final` — pre-existing short names

CSV outputs are not subject to this limit and use readable long names
(`phase_introduced`, `phase_last_seen`, etc.). If you add new attributes to
a shapefile writer, check the width **before** shipping — `pyogrio` only
emits a runtime warning, it doesn't fail.

## Reporting Fidelity

- `save_phasing_summary` — per-phase aggregates. Has `num_idle` column for
  transparency.
- `save_edges_timeline_csv` — one row per (edge, phase). Iterates over
  `sizing_decisions` (the union), skipping `action='none'` rows. DN is
  preserved during idle phases.
- `save_nodes_timeline_csv` — one row per unique node. Includes
  `phase_introduced` / `phase_last_seen` so the timeline can show when a
  building was decommissioned (backwards-compatible; readers that only look
  at `phase_introduced` still work).
- `save_final_network_shapefiles` — unions all edges ever installed, so
  idle pipes are still drawn. `idle_final` attribute lets the viewer grey
  them out.
- `save_phase_layout_shapefiles` — per-phase shapefile includes idle edges
  (pulled from the union geometry lookup) but NOT decommissioned consumer
  nodes — those belong in the timeline view, not the per-phase view.

## Files

- `phasing.py` — everything. ~1450 lines.
- `run_loop.py` — single-phase runner; not phasing-aware.
- `geometry.py` — node/edge extraction; rejects duplicate node IDs (relevant
  to Part 1 output, not Part 2b).

## Tests

`cea/tests/test_phasing_reductions.py` — unit tests for validation, sizing,
and reporting under reduction scenarios. Uses synthetic phase fixtures; no
CEA scenario required.
