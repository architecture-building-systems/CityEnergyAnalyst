"""Archetype Lock: keep the archetype-derived building properties consistent with `zone.shp`.

`zone.shp` is authored by the user. The five building-property tables are *derived* from it by
`archetypes_mapper`, which reads each building's archetype key and writes:

    envelope.csv  hvac.csv  indoor_comfort.csv  internal_loads.csv  supply.csv

plus the per-building schedules. Editing those tables directly makes `const_type` stop
describing the building it labels, with nothing recording that it happened.

When **locked**, CEA owns those tables: the input editor renders them read-only, the save
endpoint refuses to write them, and changing a building's archetype key re-runs the mapper for
that building. When **unlocked**, the user owns them, and from that moment CEA can no longer
vouch that they still match -- so the editor treats a previously-mapped-but-now-unlocked
scenario as presumed drifted. This is not verified against file contents (that would mean
hashing the whole derived-tables tree, including one schedule file per building, on every
check and every save -- see `docs/developer/archetype-lock-drift-review.md` for why that was
tried and removed): unlocking itself is the signal, since a user can always hand-edit these
CSVs outside the dashboard regardless of what any in-scenario record claims.

A scenario with no lock file reads as unlocked. That is deliberate: an existing scenario may
already hold hand-edits, and claiming they match the archetype would licence overwriting them.
Scenarios CEA creates are written locked, because they have just been mapped.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


# The input-editor tabs whose contents `archetypes_mapper` owns. Exactly the files it writes.
ARCHETYPE_DERIVED_TABS = ("envelope", "hvac", "indoor-comfort", "internal-loads", "supply")

# The `zone.shp` columns that select a building's archetype. Editing any of them invalidates
# the derived tables. Not `const_type` alone: `use_type1` and its ratios drive indoor comfort
# and internal loads, and `year` selects the archetype vintage.
ARCHETYPE_KEY_COLUMNS = (
    "const_type",
    "use_type1", "use_type1r",
    "use_type2", "use_type2r",
    "use_type3", "use_type3r",
    "year",
)


class LockState(NamedTuple):
    """The lock as recorded on disk."""

    locked: bool
    mapped_at: str | None


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
    )


def write_lock(
    locator: InputLocator,
    *,
    locked: bool,
    mapped_at: str | None = None,
) -> LockState:
    """Record the lock state.

    :param mapped_at: when `archetypes_mapper` was last run for this scenario. Defaults to
        now, which is right whenever this call follows an actual mapper run (locking, or an
        auto-remap during save). Unlocking has not just mapped anything, so it passes the
        previously recorded value through instead of stamping a new one.
    """
    state = LockState(
        locked=bool(locked),
        mapped_at=mapped_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    path = locator.get_archetype_lock_file()
    locator.ensure_parent_folder_exists(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state._asdict(), handle, indent=2, sort_keys=True)
    return state


def is_drifted(locator: InputLocator) -> bool:
    """True once a scenario CEA has mapped before is no longer locked.

    Not verified against file contents -- that would mean hashing the whole derived-tables
    tree (including one schedule file per building) on every check, for a guarantee unlocking
    already defeats: the user can hand-edit these CSVs outside the dashboard regardless of what
    any hash claims. Unlocking is itself the signal that CEA can no longer vouch for them.

    A scenario that has never been mapped is not "drifted" -- there is nothing to drift from.
    """
    state = read_lock(locator)
    return not state.locked and state.mapped_at is not None


def _comparable(value: Any) -> str:
    """Normalise a cell for comparison across the JSON round trip.

    The payload arrives as JSON (so `2000` may be `2000` or `"2000"`, and a shapefile reads
    back as numpy types), and a spurious difference here would re-run the mapper on every
    save. Numbers compare as numbers, everything else as a stripped string.
    """
    if value is None:
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
