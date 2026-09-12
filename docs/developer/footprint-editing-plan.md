# Footprint editing (vertices, move, snap) — plan, not started

Status: researched 2026-09-12, **not started**. This is a design plan, not a record of work
done -- nothing described below exists yet.

It follows on from the duplicate-building feature and save-time geometry validation, both of
which are merged; their behaviour is pinned by `cea/tests/test_duplicate_building_save.py` and
`cea/tests/test_save_geometry_validation.py`.

## Three findings from studying the existing code

**1. Vertex editing already ships in CEA.** `DRAW_MODES.edit = 'direct_select'`
(`src/features/map/constants.js:32`). The create-scenario wizard's **Edit** button already does
vertex drag, add (double-click a midpoint) and delete (select + Delete) on the site polygon via
`@mapbox/mapbox-gl-draw`. This work applies a proven in-production pattern to zone buildings; it
is not new capability.

**2. The two maps integrate deck.gl in opposite directions.** This is the crux.

| | Arrangement | Pointer owner |
|---|---|---|
| Wizard (`EditableMap.jsx:288-320`) | `<Map>` › `DrawControl` + `DeckGLOverlay` (`MapboxOverlay`, interleaved) | maplibre — draw works |
| Main map (`Map.jsx:959-978`) | `<DeckGL controller>` › `<Map>` (overlaid) | deck.gl — draw is starved |

The main map must move to interleaved `MapboxOverlay` before draw can receive events. That
migration is the largest and riskiest piece: it touches picking, tooltips, the controller and
viewState sync for the app's primary map.

**3. `DrawControl` mutates a shared singleton — latent bug, and it blocks "move".**

```js
// src/features/map/components/Map/DrawControl.jsx:95-96
var modes = MapboxDraw.modes;        // module-level shared object
modes.simple_select = StaticMode;    // mutated in place
```

Every future `MapboxDraw` instance in the app inherits `StaticMode`. Moving a whole footprint is
`simple_select` with the feature selected and dragged, so this directly blocks it. The wizard
makes it static deliberately (so nobody drags the site boundary by accident), so the fix is
per-instance modes: `{...MapboxDraw.modes, simple_select: StaticMode}` for the wizard, stock
modes for the building editor.

## Phases

0. **Un-share the modes object.** Small, self-contained, fixes a latent bug, hard prerequisite
   for move. Do first regardless of what follows.
1. **Migrate the main map to interleaved `MapboxOverlay`.** No editing. Success = no visible or
   behavioural change; extrusion and floor lines survive since the same deck layers render
   either way. Land and verify this alone.
2. **Edit mode.** Select one building → "Edit footprint": load into draw, hide it from the
   `zone` `PolygonLayer` so it is not drawn twice, `direct_select` for vertices.
3. **Move.** `simple_select` drag on the same feature. Same write path as vertices (one geometry
   replacement either way), so nearly free once 0 and 2 land.
4. **Store wiring.** `updateGeoJsonGeometry` beside the existing `updateGeoJsonProperty` in
   `useUpdateInputs.js`. Add `'geometry'` to `CHANGE_KINDS` — a one-line change now that the
   card, the Save/Discard buttons, `discardChanges` and `resetStore` all read from that list.
   Add a GEOMETRY section to `ChangesSummary`.
5. **Snapping.** `@turf/turf` 7.3.5 is already a dependency; `mapbox-gl-draw-snap-mode` is not —
   implement directly. Snap to neighbouring vertices first, then to the nearest point on an
   edge. Tolerance in **pixels converted to degrees at the current zoom**, never fixed degrees.
   Party walls need *exact* coordinate equality, not proximity, or you get slivers and the
   touching-surface emissions logic misbehaves.
6. **Live validity feedback.** `save_all_inputs` already rejects self-intersecting polygons
   (`shapefile_payload_problems`) — that check was written for this feature. Tint the polygon
   red during the drag via `turf.booleanValid` so a bowtie is obvious immediately, not at save.
7. **Tests.** `updateGeoJsonGeometry` and snap resolution are pure; they belong in the vitest
   suite (`yarn test`, now installed and running — 6 files / 68 tests). Property-test snapping:
   a snapped vertex must be exactly equal to its target.

## Open decisions

- **Phase 1 vs a dedicated editing surface.** Phase 1 is expensive and risky and exists only so
  draw can see pointer events. The alternative is a panel/modal reusing `EditableMap`'s
  structure almost verbatim, showing zone + surroundings so snap targets are visible — much
  lower risk, proven arrangement, but editing happens away from the main map. Recommendation was
  phase 1 for in-place UX, falling back to the dedicated surface if the main map's picking and
  tooltip behaviour proves fragile. **Not decided.**
- **Undo granularity.** Discard throws away all pending changes; there is no per-vertex undo.
  Suggested shipping without it and seeing whether it is missed.
- **Downstream staleness.** Changing a footprint invalidates radiation and demand results and
  nothing detects it. Pre-existing (editing `height_ag` has the same gap) but much easier to hit
  once footprints are editable.
- **Scope.** `surroundings` and `trees` are shapefiles on the same save path; everything
  generalises, but restrict phases 1-6 to `zone` until the interaction is proven.

## Why this also matters

The duplicate-building feature places the copy on the original's exact footprint, which distorts
radiation and demand. Dragging fixes that; until then it is a known caveat.
