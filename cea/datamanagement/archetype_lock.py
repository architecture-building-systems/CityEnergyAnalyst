"""Archetype Lock: keep the archetype-derived building properties consistent with `zone.shp`.

`zone.shp` is authored by the user. The five building-property tables are *derived* from it by
`archetypes_mapper`, which reads each building's archetype key and writes:

    envelope.csv  hvac.csv  indoor_comfort.csv  internal_loads.csv  supply.csv

plus the per-building schedules. Editing those tables directly makes `const_type` stop
describing the building it labels, with nothing recording that it happened.

When **locked**, CEA owns those tables: the input editor renders them read-only, the save
endpoint refuses to write them, and changing a building's archetype key re-runs the mapper for
that building. Saving the *archetype database itself* (the `ARCHETYPES` tables the mapper reads
from) re-runs the mapper too, but only for the buildings that reference the codes that changed
-- see `changed_archetype_codes` / `buildings_using_archetypes`, used by
`put_input_database_data`. When **unlocked**, the user owns them, and CEA can no longer vouch
that they still match -- `is_drifted` gives a cheap, coarse answer for a caller with nothing
else loaded, but the real check is content-derived and lives client-side (see below), where the
input editor already has everything it needs without an extra read.

Two different derivations need two different checks (`docs/developer/archetype-lock-drift-review.md`
has the full history, including the whole-folder hash this replaced):

- `envelope`, `hvac`, `supply` are a pure lookup on `const_type` -- a building's value is
  entirely determined by its current `const_type` plus the current construction-type database,
  nothing else. So there is nothing to store: compare the current value directly against
  `construction_type_database[current const_type]`, live. This is exact, not approximate, and
  it is never stale since it is evaluated against *now*.
- `indoor-comfort`, `internal-loads` are a ratio-weighted average across up to three
  `use_type`s (`calculate_average_multiuse`), too involved to cheaply re-derive client-side. For
  these, `mapped_use_types` (plain values) catches "the key moved but nothing re-derived it",
  and `mapped_computed_values` (each tab's own column values, per building) catches "the table
  itself was hand-edited" -- compared client-side with a plain value-equality check, the same
  one already used for `mapped_use_types` and the lookup tabs, rather than a content hash: it
  used to be a SHA256 per building per tab, which meant reimplementing Python's hashing and
  float normalisation in the frontend byte-for-byte just to answer "did this change". Storing
  the values instead of a digest of them needs no such twin implementation, and incidentally
  reports *which* column disagrees rather than only "something in this row might have".

A scenario with no lock file reads as unlocked. That is deliberate: an existing scenario may
already hold hand-edits, and claiming they match the archetype would licence overwriting them.
Scenarios CEA creates are written locked, because they have just been mapped.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, NamedTuple

import pandas as pd

if TYPE_CHECKING:
    from cea.datamanagement.database.archetypes import Archetypes
    from cea.inputlocator import InputLocator

logger = logging.getLogger(__name__)


# The input-editor tabs whose contents `archetypes_mapper` owns. Exactly the files it writes.
ARCHETYPE_DERIVED_TABS = ("envelope", "hvac", "indoor-comfort", "internal-loads", "supply")

# The `zone.shp` columns that select a building's archetype. Editing any of them invalidates
# the derived tables. Not `const_type` alone: `use_type1` and its ratios drive indoor comfort
# and internal loads.

ARCHETYPE_KEY_COLUMNS = (
    "const_type",
    "use_type1", "use_type1r",
    "use_type2", "use_type2r",
    "use_type3", "use_type3r",
)

# The `zone.shp` columns that select a building's `use_type` mix -- the archetype key for the two
# *computed* tabs (`indoor-comfort`, `internal-loads`). Deliberately excludes `const_type`: the
# other three derived tabs are a pure lookup on it, checked live against the construction-type
# database client-side, so nothing about `const_type` needs to be stored as a baseline at all.
ARCHETYPE_USE_TYPE_COLUMNS = (
    "use_type1", "use_type1r",
    "use_type2", "use_type2r",
    "use_type3", "use_type3r",
)

# The two derived tabs that are a ratio-weighted average, not a straight lookup, and so need a
# stored content baseline (`mapped_computed_values`) rather than a live re-derivation. Sourced
# from `archetypes_mapper`'s own column lists -- not re-transcribed here -- so the two never
# drift apart, and so the baseline never picks up a field the mapper itself does not write (e.g.
# a `reference` column added to the tab's rendered schema later).
_COMPUTED_TAB_COLUMNS: dict[str, tuple[str, ...]] = {}


def computed_tab_columns() -> dict[str, tuple[str, ...]]:
    """`{tab: columns}` for the two ratio-derived tabs, lazily imported to avoid a module-load
    cycle (`archetypes_mapper` does not import `archetype_lock`, but importing it eagerly here
    would still make this module pay for pulling in the whole mapper at import time)."""
    if not _COMPUTED_TAB_COLUMNS:
        from cea.datamanagement.archetypes_mapper import INDOOR_COMFORT_FIELDS, INTERNAL_LOADS_FIELDS
        _COMPUTED_TAB_COLUMNS["indoor-comfort"] = INDOOR_COMFORT_FIELDS
        _COMPUTED_TAB_COLUMNS["internal-loads"] = INTERNAL_LOADS_FIELDS
    return _COMPUTED_TAB_COLUMNS


_COMPUTED_TAB_LOCATOR_METHOD = {
    "indoor-comfort": "get_building_comfort",
    "internal-loads": "get_building_internal",
}


class LockState(NamedTuple):
    """The lock as recorded on disk."""

    locked: bool
    mapped_at: str | None
    mapped_use_types: dict[str, dict[str, Any]] | None = None
    mapped_computed_values: dict[str, dict[str, dict[str, Any]]] | None = None


UNLOCKED = LockState(locked=False, mapped_at=None)


def read_lock(locator: InputLocator) -> LockState:
    """The recorded lock state. A missing or unreadable file reads as unlocked.

    Unreadable is treated as unlocked rather than raising: a corrupt sidecar must not stop a
    user opening their scenario, and unlocked is the state that changes nothing on disk.
    """
    path = locator.get_archetype_lock_file()
    if not os.path.isfile(path):
        return UNLOCKED

    try:
        with open(path, encoding="utf-8") as handle:
            payload: dict[str, Any] = json.load(handle)
    except (OSError, ValueError):
        return UNLOCKED

    return LockState(
        locked=bool(payload.get("locked", False)),
        mapped_at=payload.get("mapped_at"),
        mapped_use_types=payload.get("mapped_use_types"),
        mapped_computed_values=payload.get("mapped_computed_values"),
    )


def _json_safe(value: Any) -> Any:
    """A cell as something `json.dump` can serialise: `NaN`/numpy scalars become plain values.

    `pandas`/`geopandas` hand back `numpy.float64`, `numpy.int64`, and `NaN` (a float, not
    `None`) for missing cells -- none of which `json.dump` accepts as-is, and a `NaN` would
    round-trip through `json.load` as an unparseable bare token if it somehow were written.
    """
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _read_use_types(locator: InputLocator) -> dict[str, dict[str, Any]]:
    """Every building's `use_type1/2/3` + ratios as `zone.shp` currently holds them.

    Narrow read: `name` plus `ARCHETYPE_USE_TYPE_COLUMNS`, geometry never parsed -- this is
    cheap enough to run on every lock/relock without a second thought.
    """
    import geopandas

    path = locator.get_zone_geometry()
    frame = geopandas.read_file(path, columns=["name", *ARCHETYPE_USE_TYPE_COLUMNS], ignore_geometry=True)

    if "name" not in frame.columns:
        raise KeyError(f"{path} has no `name` field")

    keys = frame.set_index("name")
    columns = [c for c in ARCHETYPE_USE_TYPE_COLUMNS if c in keys.columns]
    return {
        str(name).strip(): {column: _json_safe(row[column]) for column in columns}
        for name, row in keys.iterrows()
    }


def _read_computed_values(locator: InputLocator) -> dict[str, dict[str, dict[str, Any]]]:
    """`{building: {tab: {column: value}}}` for `indoor-comfort` and `internal-loads`, from disk
    right now -- the raw baseline a re-lock stamps.

    Plain values, not a digest of them: the frontend compares each column against this baseline
    with the same value-equality check it already uses for `mapped_use_types` and the lookup
    tabs, so this needs no hashing (or a second implementation of Python's float/JSON
    normalisation) on either side. Fixed column order per tab (`computed_tab_columns()[tab]`,
    not whatever order the CSV happens to have) keeps the baseline free of anything the mapper
    itself does not write (e.g. a `reference` column added to the tab's rendered schema later).

    Two bounded file reads (not one per building, not the other three tabs) -- this only runs
    at a genuine mapper event (locking, an auto-remap, scenario creation), never on a mere
    check, so the cost profile is nothing like the removed whole-folder-per-check signature.
    """
    values: dict[str, dict[str, dict[str, Any]]] = {}
    for tab, locator_method in _COMPUTED_TAB_LOCATOR_METHOD.items():
        path = getattr(locator, locator_method)()
        table = pd.read_csv(path).set_index("name")
        present_columns = [c for c in computed_tab_columns()[tab] if c in table.columns]
        for name, row in table.iterrows():
            values.setdefault(str(name).strip(), {})[tab] = {
                column: _json_safe(row[column]) for column in present_columns
            }
    return values


def write_lock(
    locator: InputLocator,
    *,
    locked: bool,
    mapped_at: str | None = None,
    mapped_use_types: dict[str, dict[str, Any]] | None = None,
    mapped_computed_values: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> LockState:
    """Record the lock state.

    :param mapped_at: when `archetypes_mapper` was last run for this scenario. Defaults to
        now, which is right whenever this call follows an actual mapper run (locking, or an
        auto-remap during save). Unlocking has not just mapped anything, so it passes the
        previously recorded value through instead of stamping a new one.
    :param mapped_use_types: every building's `use_type1/2/3`+ratios as of the mapper run this
        call follows. Self-computed from `zone.shp` when locking and not given -- the same
        "the caller has just mapped, so read the truth now" rule `mapped_at` follows, which is
        what lets `remap_and_relock` and `create_new_scenario` keep calling
        `write_lock(locator, locked=True)` with nothing extra. Unlocking passes the previous
        value through unchanged: nothing was mapped, so the baseline must not move.
    :param mapped_computed_values: `indoor-comfort` and `internal-loads`'s own column values per
        building, for the same reason and under the same self-computation rule. `None` for
        either param when the relevant file cannot be read -- the lock still succeeds; the
        scenario then behaves like one without a baseline until the next successful lock
        re-establishes one.
    """
    if locked and mapped_use_types is None:
        try:
            mapped_use_types = _read_use_types(locator)
        except (OSError, ValueError, KeyError, RuntimeError) as e:
            logger.warning(f"Could not read archetype-lock use-type baseline from zone.shp: {e}")
            mapped_use_types = None

    if locked and mapped_computed_values is None:
        try:
            mapped_computed_values = _read_computed_values(locator)
        except (OSError, ValueError, KeyError, RuntimeError) as e:
            logger.warning(f"Could not read archetype-lock computed-tab baseline: {e}")
            mapped_computed_values = None

    state = LockState(
        locked=bool(locked),
        mapped_at=mapped_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        mapped_use_types=mapped_use_types,
        mapped_computed_values=mapped_computed_values,
    )
    path = locator.get_archetype_lock_file()
    locator.ensure_parent_folder_exists(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state._asdict(), handle, indent=2, sort_keys=True)
    return state


def is_drifted(locator: InputLocator, state: LockState | None = None) -> bool:
    """A cheap, coarse drift signal for a caller with no tables loaded.

    This is *not* the primary check -- that lives client-side in the input editor, which
    already has the current zone table and all five derived tables loaded and can compare them
    against `mapped_use_types`/`mapped_computed_values` (for the two computed tabs) and the
    construction-type database directly (for the three lookup tabs), per building and per tab.
    This function only compares `use_type1/2/3`+ratios -- one small `zone.shp` read -- so it
    cannot see a `const_type`-only change or a hand-edit to a derived table; it exists for a
    consumer that has none of that data loaded and just needs *some* answer cheaply.

    :param state: pass an already-read `LockState` to avoid parsing the sidecar twice (e.g. a
        route that already called `read_lock` for other fields in its response).
    """
    if state is None:
        state = read_lock(locator)
    if state.locked:
        return False
    if state.mapped_at is None:
        return False
    if state.mapped_use_types is None:
        return True  # legacy sidecar, or zone.shp was unreadable when locked -- no baseline

    try:
        current = _read_use_types(locator)
    except (OSError, ValueError, KeyError, RuntimeError):
        return True  # can't verify now either -- fail conservative, not "fine"

    if current.keys() != state.mapped_use_types.keys():
        return True

    for building, baseline_row in state.mapped_use_types.items():
        current_row = current.get(building)
        if current_row is None or current_row != baseline_row:
            return True
    return False


def _comparable(value: Any) -> str:
    """Normalise a cell for comparison across the JSON round trip.

    The payload arrives as JSON (so `2000` may be `2000` or `"2000"`, and a shapefile/CSV reads
    back as numpy types with a blank cell as `NaN` rather than `None`), and a spurious
    difference here would re-run the mapper on every save. `None` and `NaN` compare equal (both
    mean "missing"), numbers compare as numbers, everything else as a stripped string.
    """
    if pd.isna(value):
        return ""
    try:
        return repr(float(value))
    except (TypeError, ValueError):
        return str(value).strip()


def buildings_added(incoming_zone: Any, existing_zone: Any) -> list[str]:
    """Buildings present in the payload that are not yet on disk.

    A new building has no previous archetype to have moved away from, so
    `archetype_key_changed` skips it -- but it still needs derived rows, and while locked CEA
    is the one that owes them. Without this a building added to a locked scenario would sit
    with no envelope, HVAC, comfort, loads or supply until something else happened to run the
    mapper.

    :return: sorted building names.
    """
    if not incoming_zone:
        return []
    if existing_zone is None or len(existing_zone) == 0:
        return sorted(incoming_zone)
    return sorted(set(incoming_zone) - set(existing_zone.index))


def archetype_key_changed(incoming_zone: Any, existing_zone: Any) -> list[str]:
    """Buildings whose archetype key differs between the payload and what is on disk.

    Compared server-side rather than trusting a change log from the client: the lock is only a
    guarantee if the server decides for itself what changed.

    :param incoming_zone: the `zone` table from the save payload,
        `{building: {column: value}}`.
    :param existing_zone: the zone table currently on disk, as a DataFrame indexed by name.
    :return: sorted building names whose key moved. Buildings that are new on this save are
        not included -- they have no previous archetype to have moved away from, and the
        caller maps them by other means.
    """
    if not incoming_zone or existing_zone is None or len(existing_zone) == 0:
        return []

    columns = [c for c in ARCHETYPE_KEY_COLUMNS if c in existing_zone.columns]
    if not columns:
        return []

    moved = set()
    for building, incoming_row in (incoming_zone or {}).items():
        if building not in existing_zone.index:
            continue  # new building, not a change of key
        existing_row = existing_zone.loc[building]
        for column in columns:
            if column not in (incoming_row or {}):
                continue
            if _comparable(incoming_row[column]) != _comparable(existing_row[column]):
                moved.add(building)
                break

    return sorted(moved)


def buildings_needing_remap(incoming_zone: Any, existing_zone: Any) -> list[str]:
    """Buildings whose derived tables the save must regenerate.

    Two reasons, and callers should not have to know both: the building's archetype moved, or
    it is new and has no derived rows at all.

    :return: sorted building names.
    """
    return sorted(
        set(archetype_key_changed(incoming_zone, existing_zone))
        | set(buildings_added(incoming_zone, existing_zone))
    )


def _codes_differing(
    existing: pd.DataFrame | None,
    incoming: pd.DataFrame | None,
) -> set[str]:
    """Row labels (the archetype code, e.g. a `const_type` or `use_type`) whose row differs.

    Both frames are indexed by the code. A code present in only one of the two frames counts
    as differing (added/removed codes must not be silently ignored -- a building that still
    references a deleted code needs to surface that, not be skipped). Compared over the union
    of columns, with a missing column normalising to `""`, so a column added or dropped also
    registers. Values are run through `_comparable` for the same reason `archetype_key_changed`
    uses it: a JSON round trip (`2000` vs `"2000"`) must not read as a change.
    """
    existing_index = set(existing.index) if existing is not None else set()
    incoming_index = set(incoming.index) if incoming is not None else set()

    differing = existing_index ^ incoming_index
    for code in existing_index & incoming_index:
        existing_row = existing.loc[code]
        incoming_row = incoming.loc[code]
        columns = set(existing_row.index) | set(incoming_row.index)
        for column in columns:
            existing_value = existing_row[column] if column in existing_row else None
            incoming_value = incoming_row[column] if column in incoming_row else None
            if _comparable(existing_value) != _comparable(incoming_value):
                differing.add(code)
                break

    return differing


def _schedule_library_codes_differing(
    existing: dict[str, pd.DataFrame],
    incoming: dict[str, pd.DataFrame],
) -> set[str]:
    """Use-type codes whose schedule library CSV (`SCHEDULES_LIBRARY/<use_type>.csv`) differs.

    Keyed by use type, one DataFrame of hourly rows per code -- not indexed by anything callers
    can use for a row-wise compare, so this compares records directly rather than via
    `_codes_differing`.
    """
    differing = set(existing) ^ set(incoming)
    for code in set(existing) & set(incoming):
        existing_records = existing[code].to_dict(orient="records")
        incoming_records = incoming[code].to_dict(orient="records")
        if [
            {k: _comparable(v) for k, v in row.items()} for row in existing_records
        ] != [
            {k: _comparable(v) for k, v in row.items()} for row in incoming_records
        ]:
            differing.add(code)

    return differing


def changed_archetype_codes(
    incoming: "Archetypes",
    existing: "Archetypes",
) -> tuple[set[str], set[str]]:
    """`(const_type codes, use_type codes)` whose definition differs between payload and disk.

    Compared server-side rather than trusted from the client's change log, for the same reason
    `archetype_key_changed` is: the lock is only a guarantee if the server decides for itself
    what changed. A `const_type` drives envelope/hvac/supply; a `use_type` drives indoor
    comfort, internal loads and the per-building schedules, so each is compared against every
    source `archetypes_mapper` reads for that side.

    :return: sorted-independent sets of changed codes -- deleted codes are included, since a
        building that still references a code someone just removed cannot be silently skipped.
    """
    const_types = _codes_differing(
        existing.construction.construction_types, incoming.construction.construction_types)

    use_types = _codes_differing(
        existing.use.use_types, incoming.use.use_types)
    use_types |= _codes_differing(
        existing.use.schedules.monthly_multipliers, incoming.use.schedules.monthly_multipliers)
    use_types |= _schedule_library_codes_differing(
        existing.use.schedules._library, incoming.use.schedules._library)

    return const_types, use_types


def buildings_using_archetypes(
    zone_df: Any,
    *,
    const_types: set[str],
    use_types: set[str],
) -> list[str]:
    """Buildings whose derived rows a change to those archetype codes invalidates.

    `const_type` drives envelope/hvac/supply; `use_type1`/`use_type2`/`use_type3` drive indoor
    comfort, internal loads and the schedules -- a hit against any of the four columns counts.

    :param zone_df: the `zone` table, as a DataFrame with `const_type` and `use_type1..3`
        columns (row label or a `name` column, either way only the columns above are read).
    :return: sorted building names. Empty if neither set has anything in it, or `zone_df` has
        none of the expected columns.
    """
    if not const_types and not use_types:
        return []

    matched = pd.Series(False, index=zone_df.index)
    if const_types and "const_type" in zone_df.columns:
        matched |= zone_df["const_type"].astype(str).isin(const_types)
    if use_types:
        for column in ("use_type1", "use_type2", "use_type3"):
            if column in zone_df.columns:
                matched |= zone_df[column].astype(str).isin(use_types)

    if "name" in zone_df.columns:
        return sorted(zone_df.loc[matched, "name"])
    return sorted(zone_df.index[matched])
