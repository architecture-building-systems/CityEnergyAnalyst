# Archetype Lock: drift-signature review

Status: reviewed 2026-09-12, **signature mechanism removed** (see "Fix applied" below).
Superseded 2026-09-14 -- see "Content verification, reintroduced narrower" at the bottom: a
different, much smaller content check was added back once the derived tabs were split by how
they're actually produced.

## What Archetype Lock actually enforces, and how

Two independent mechanisms did the real work, and neither used the folder hash:

- **Write refusal.** `save_all_inputs` drops the five derived tables (`envelope`, `hvac`,
  `indoor-comfort`, `internal-loads`, `supply`) from the payload whenever `lock.locked` is
  `True`. Gated on a plain boolean.
- **Auto re-map.** `archetype_key_changed()` / `buildings_added()` diff the incoming `zone`
  payload against what's on disk for the archetype-key columns (`const_type`, `use_type1/2/3`
  (+ ratios)) and re-run `archetypes_mapper` only for the buildings that moved. A small,
  targeted comparison — no folder hashing involved.

  `year` is deliberately not one of these columns, despite selecting `const_type` in Zone
  Helper (matched against the construction-standard database's `year_start`/`year_end`
  ranges): that lookup runs once, upstream, in a separate tool. `archetypes_mapper` never reads
  `year`, only the `const_type` Zone Helper already resolved it to, so keying a remap on `year`
  would re-run the mapper for output that cannot change.

## Why the signature added cost without adding a guarantee

`mapped_signature` (a SHA256 of the *entire* `inputs/building-properties/` folder, including
one schedule file per building) was computed by `hash_folder()` — full content read, no
caching — on:

- every `GET /archetype-lock` (via `is_drifted()`), fired once per input-editor page load, and
- every `PUT /all-inputs` while locked, via a `write_lock(...)` call at the end that ran
  **unconditionally**, "in case schedules changed" — even a save that touched nothing
  archetype-related re-hashed the whole tree.

For a district of N buildings this is O(N) file opens plus O(total schedule bytes) of I/O,
repeated from scratch on every check. Under a scaled, stateless deployment with network-backed
scenario storage, that is O(N) network reads per request, not local disk.

In exchange, the signature bought exactly one thing: `is_drifted()`, surfaced only when the
scenario is **unlocked**, where it flags every `archetype_key_columns` cell on the whole `zone`
tab — not per-building, not per-column; any single edit anywhere under `building-properties/`
flips the flag for the entire table.

It also had two correctness gaps that made the guarantee weaker than the mechanism suggested:

1. **Locked-state blind spot.** The unconditional re-fingerprint at the end of every locked save
   re-baselined `mapped_signature` to whatever was currently on disk, without re-verifying it
   against a fresh mapper run. A hand-edit made to a derived table while locked (bypassing the
   dashboard entirely — CEA is a file-based tool, this is always possible) would be silently
   "laundered" into the new trusted baseline by the very next unrelated save.
2. **No visibility outside the scenario.** The hash only covers `inputs/building-properties/`.
   Editing the shared archetype/construction-standard database that `archetypes_mapper` reads
   from — which affects every scenario built against that `const_type` — produces zero
   detectable drift, ever, in any scenario. **Closed** (while locked) by a follow-up: see
   "Database-save trigger" below. Gap (1) is unaffected — it was about the removed hash
   specifically, and stays closed by the hash's removal.

So the actual claim `is_drifted()` could make was never "these tables are consistent with the
archetype." It was closer to "the bytes under `building-properties/` are the same bytes as the
last time something called `write_lock`" — and even that was undermined by (1).

## The insight that made the fix obvious

Once unlocked, drift is close to tautological: the user just told CEA "I am taking ownership of
these tables." Whether they have edited anything *yet* is not really the question worth
answering with a cryptographic hash — the moment ownership changes hands, CEA can no longer
vouch for consistency, full stop. A boolean "has this scenario been mapped by CEA and is it not
currently locked" gives the same UI signal (warn on the `zone` tab's archetype columns) as the
content hash did, for O(1) cost — no folder walk, no file reads.

## Fix applied

- `LockState` no longer carries `mapped_signature`. The `.archetype_lock.json` sidecar now
  stores only `{"locked": bool, "mapped_at": str | None}`.
- `derived_signature()` and the `hash_folder` import are removed from
  `cea/datamanagement/archetype_lock.py`.
- `is_drifted(locator)` is now `not state.locked and state.mapped_at is not None` — a pure JSON
  read, no filesystem walk.
- `save_all_inputs` no longer re-fingerprints on every locked save. `write_lock` is only called
  when an actual re-map happened (buildings changed archetype or were added), to advance
  `mapped_at`.
- `set_archetype_lock` (`PUT /archetype-lock`) no longer computes a signature when locking or
  carries one forward when unlocking.

This removes all `hash_folder` I/O from the Archetype Lock feature. The remaining cost per
request is the small `archetype_key_changed()` comparison (already cheap — no hashing) plus a
few-hundred-byte JSON read/write.

## What did not change

The write-refusal and auto-remap mechanisms are untouched — they never depended on the
signature. The frontend's `driftedColumns` behaviour (highlight the `zone` tab's archetype key
columns once unlocked-and-previously-mapped) is unchanged from the user's point of view; only
how `drifted` is computed on the backend changed.

## Database-save trigger (closes gap 2, locked case only)

`PUT /inputs/databases` (`put_input_database_data`, `cea/interfaces/dashboard/api/inputs.py`)
now closes the other half of gap (2) above: while locked, it re-runs `archetypes_mapper` for
the buildings that reference an archetype row the save actually changed.

The cost this adds is bounded by *archetype* count, not building count: a snapshot of the small
`ARCHETYPES` CSVs and schedule library taken before the write, diffed against the payload
(`archetype_lock.changed_archetype_codes`) — no folder hashing, same shape as
`archetype_key_changed`'s existing zone-side diff. Only when that diff is non-empty does a
`zone.shp` attribute read (`archetype_lock.buildings_using_archetypes`) and the mapper run
follow, and only for the buildings the changed codes actually touch — the same
narrow-to-what-moved approach `save_all_inputs` already uses for `zone.shp` edits, for the same
reason (a district-wide re-derive on every edit would be needlessly slow for a large scenario).

Still open: an **unlocked** scenario is unaffected by a database edit — the user already owns
the derived tables, and the `drifted` flag is the visibility that case gets. And this only
detects a *change*, not a *deletion in use*: deleting a `const_type` a building still
references also counts as "changed" (see `changed_archetype_codes`'s docstring), but the mapper
raises at that point rather than the save refusing up front — a `remap_error` comes back in the
save response instead of a 500, since the database write itself already succeeded and cannot be
rolled back (`CEADatabase.save`'s own FIXME).

## Content verification, reintroduced narrower (2026-09-14)

"The insight that made the fix obvious" above still holds for *why the whole folder-hash was
too expensive*, but it understated a real gap: unlocking-alone-as-signal meant a hand-edit to a
derived table (`envelope.csv`, `internal_loads.csv`, ...) was never actually distinguished from
"nothing changed" — the flag was the same either way, always on once unlocked. That gap is
exactly the scenario this module's own opening docstring describes ("editing those tables
directly makes `const_type` stop describing the building it labels, with nothing recording that
it happened"). A per-building, content-derived check was reintroduced to close it, but not by
resurrecting `hash_folder` over the whole tree — by splitting the five derived tabs by *how*
`archetypes_mapper` actually produces them, and using the cheapest correct check for each kind.

**`envelope`, `hvac`, `supply`** are a pure lookup on `const_type`
(`typology_df.merge(construction_type_DB, on='const_type')`). A building's value is entirely
determined by its current `const_type` plus the current construction-type database — nothing
else. So nothing is stored for these at all: the input editor, which already has the current
construction-type database and the current derived-table values loaded, compares them directly,
live. This is exact (not an approximation) and cannot go stale, since it's evaluated against
*now* rather than against a snapshot from whenever the scenario was last locked.

**`indoor-comfort`, `internal-loads`** are a ratio-weighted average across up to three
`use_type`s (`calculate_average_multiuse`), too involved to cheaply re-derive client-side. For
these, `write_lock` self-computes and stores, in `.archetype_lock.json`:

- `mapped_use_types` — every building's `use_type1/2/3`+ratios, plain values, as of the mapper
  run this lock follows. Catches "the key moved but nothing re-derived it" (the same failure
  mode `archetype_key_changed` catches for a save, just as a standing baseline instead of a
  payload diff).
- `mapped_computed_values` — each building's own column values for these two tabs
  (`archetypes_mapper.INDOOR_COMFORT_FIELDS`/`INTERNAL_LOADS_FIELDS` — the mapper's own column
  lists, not re-transcribed), not a digest of them (see "Baseline values instead of a hash"
  below for why). Catches a direct hand-edit to one of these two tables. Deliberately a coarse
  "might have drifted" signal, not a claim the ratio math came out wrong.

Both are computed once, at a genuine mapper event (locking, an auto-remap during save, a
database-triggered remap, scenario creation — anywhere `write_lock(locked=True)` is already
called), from three bounded file reads when the caller omits the baselines (the common case):
one `zone.shp` read for `mapped_use_types`, plus `indoor_comfort.csv` and `internal_loads.csv`
for `mapped_computed_values` — not the other three tabs, not one file per building. Never
recomputed on a mere check. `is_drifted()` itself
stays a cheap, coarse, `use_type`-only server-side fallback for a caller with nothing else
loaded; the full per-building, per-tab check lives client-side in the input editor, which
already has the zone table and all five derived tables loaded to render the editor regardless.

This avoids both of the original signature's failure modes: there is no "unconditional
re-fingerprint on every locked save" to launder a hand-edit into the trusted baseline (the
baseline only ever moves where a real mapper run just happened), and it answers a question the
plain boolean never could — reverting a key edit back to its original value clears the flag
again, with no re-lock needed, since the check is a live comparison, not a one-way switch.
`year` still contributes nothing to either check, for the same reason noted above: it isn't part
of `const_type`'s lookup key or the `use_type`-driven computed tabs' inputs.

## Baseline values instead of a hash (2026-09-15)

`mapped_computed_hashes` (the previous name for the field above) stored one SHA256 digest per
building per tab, computed by `_hash_computed_row` over a `_comparable`-normalised payload. The
frontend then had to reproduce that exact algorithm — a from-scratch SHA-256 implementation
(`archetypeHash.js`) plus a hand-matched port of `_comparable`'s `repr(float(x))` normalisation —
just to answer "does this cell still equal what was hashed". That is two independent
implementations of the same computation that have to agree byte-for-byte forever, pinned
together only by a cross-repo test fixture (this file's `_hash_computed_row` unit tests and the
GUI's `archetypeHash.test.js`), with no mechanism to catch the two silently drifting apart
beyond that fixture happening to be re-run.

The check only ever needed value *equality*, and the frontend already has a value-equality
comparator (`valuesEqual`, used for `mapped_use_types` and the three lookup tabs) — no digest
required. So `write_lock` now stores the raw column values per building
(`mapped_computed_values`, this file's `_read_computed_values`) instead of a hash of them, and
the frontend diffs each column against that baseline directly. This deletes the entire
SHA-256/`_comparable`-port from the GUI (`archetypeHash.js` and its test), removes the
cross-repo fixture-sync burden, and — as a side effect — a hand-edit to `indoor-comfort`/
`internal-loads` can now be pinned to the exact column that disagrees with the baseline, the
same as the three lookup tabs already do; the hash's "can't tell which cell" limitation was an
artefact of hashing, not of the underlying data. The `GET /archetype-lock` response's
`computed_tab_columns` field also goes away with it: the frontend no longer needs a separate
column list to know what to hash, since the keys of each building's own baseline are the
columns to compare.

Cost: the lock sidecar and the `GET /archetype-lock` response now carry full baseline rows (7 +
13 columns per building) instead of one hash string per tab per building — a larger payload,
but the same category of data `mapped_use_types` already ships this way, not a new I/O pattern,
and still the same bounded file reads at write time as before (`zone.shp`, `indoor_comfort.csv`,
`internal_loads.csv`).
