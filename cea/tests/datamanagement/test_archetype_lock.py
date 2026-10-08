"""Archetype Lock: CEA owns the archetype-derived tables while locked.

`zone.shp` is authored; `envelope.csv`, `hvac.csv`, `indoor_comfort.csv`,
`internal_loads.csv`, `supply.csv` and the per-building schedules are derived from it by
`archetypes_mapper`. Editing the derived tables directly makes `const_type` stop describing the
building it labels.

The enforcement lives in `save_all_inputs`, not in the UI. The input editor holds every table
in memory and PUTs all of them on each save, so a merely *stale* client -- one opened before
the lock, or holding values that predate an auto-remap -- would otherwise write over tables it
never meant to touch.
"""

import json
import os
import warnings

import geopandas as gpd
import pandas as pd
import pytest

from cea.datamanagement import archetype_lock
from cea.datamanagement.archetype_lock import (
    ARCHETYPE_DERIVED_TABS,
    archetype_key_changed,
    is_drifted,
    read_lock,
    write_lock,
)
from cea.datamanagement.archetype_lock import _read_computed_values


@pytest.fixture(scope="module")
def locator():
    from cea.inputlocator import ReferenceCaseOpenLocator

    return ReferenceCaseOpenLocator()


# --------------------------------------------------------------------------- lock state


def test_a_scenario_without_a_lock_file_reads_as_unlocked(tmp_path):
    """Existing scenarios may already hold hand-edits.

    Reading them as locked would claim those edits match the archetype, licensing CEA to
    overwrite them. Absent-means-unlocked also means no migration is needed.
    """
    from cea.inputlocator import InputLocator

    state = read_lock(InputLocator(str(tmp_path)))
    assert state.locked is False
    assert state.mapped_at is None


def test_an_unreadable_lock_file_reads_as_unlocked(tmp_path):
    """A corrupt sidecar must not stop a user opening their scenario."""
    from cea.inputlocator import InputLocator

    locator = InputLocator(str(tmp_path))
    (tmp_path / "inputs").mkdir()
    with open(locator.get_archetype_lock_file(), "w", encoding="utf-8") as handle:
        handle.write("{not json")

    assert read_lock(locator).locked is False


# --------------------------------------------------------------------------- drift


def test_a_locked_scenario_is_not_drifted(locator):
    write_lock(locator, locked=True)
    assert is_drifted(locator) is False


def test_an_unlocked_but_never_mapped_scenario_is_not_drifted(tmp_path):
    """Nothing to drift from -- do not warn about a scenario CEA has never mapped."""
    from cea.inputlocator import InputLocator

    assert is_drifted(InputLocator(str(tmp_path))) is False


def test_unlocking_keeps_the_baseline_and_the_scenario_undrifted(locator):
    """Unlocking with the baseline carried forward: the `use_type` keys have not moved, so the
    coarse fallback -- all it can check without the tables loaded -- reports no drift."""
    write_lock(locator, locked=True)
    previous = read_lock(locator)
    assert previous.mapped_use_types is not None, "locking stamps what it mapped against"
    assert previous.mapped_computed_values is not None

    write_lock(locator, locked=False, mapped_at=previous.mapped_at,
               mapped_use_types=previous.mapped_use_types,
               mapped_computed_values=previous.mapped_computed_values)
    assert is_drifted(locator) is False


def test_a_sidecar_written_before_the_baseline_existed_reads_as_drifted(tmp_path):
    """A scenario mapped by an older CEA has `mapped_at` but no `mapped_use_types`.

    There is no baseline to compare against, so the honest answer is "cannot vouch for it" --
    one re-lock re-baselines it. Written as raw JSON on purpose: this is the on-disk shape of
    the file an older CEA left behind, not something `write_lock` can still produce.
    """
    from cea.inputlocator import InputLocator

    locator = InputLocator(str(tmp_path))
    (tmp_path / "inputs").mkdir()
    with open(locator.get_archetype_lock_file(), "w", encoding="utf-8") as handle:
        json.dump({"locked": False, "mapped_at": "2026-01-01T00:00:00+00:00"}, handle)

    assert read_lock(locator).mapped_use_types is None
    assert is_drifted(locator) is True


# ------------------------------------------------------------------ computed-tab baseline (unit)


def test_read_computed_values_matches_the_csv_on_disk(locator):
    """The baseline captured for the two computed tabs is the raw column values, not a digest
    of them -- so the frontend can compare it directly with a plain value-equality check
    instead of reimplementing this module's hashing/normalisation."""
    values = _read_computed_values(locator)

    comfort_on_disk = pd.read_csv(locator.get_building_comfort()).set_index("name")
    building = comfort_on_disk.index[0]
    for column in archetype_lock.computed_tab_columns()["indoor-comfort"]:
        assert values[building]["indoor-comfort"][column] == pytest.approx(
            comfort_on_disk.loc[building, column])


def test_read_computed_values_only_carries_the_tabs_own_columns(locator):
    """A stray column (`name`, `REFERENCE`, or another tab's field) must not leak into the
    baseline -- only the tab's own fixed column list, so an unrelated schema addition elsewhere
    cannot flip the comparison."""
    values = _read_computed_values(locator)
    building = next(iter(values))
    assert set(values[building]["indoor-comfort"]) == set(
        archetype_lock.computed_tab_columns()["indoor-comfort"])


def test_read_computed_values_normalises_missing_to_none(tmp_path):
    """A `NaN` cell (pandas' spelling for missing) must come back JSON-safe (`None`), not a
    float `json.dump` cannot serialise -- a fresh scenario copy, not the shared module-scoped
    fixture, since this leaves a blanked cell on disk."""
    import math
    import shutil

    from cea.inputlocator import InputLocator, ReferenceCaseOpenLocator

    source = ReferenceCaseOpenLocator()
    scenario_copy = tmp_path / "scenario"
    shutil.copytree(source.scenario, scenario_copy)
    isolated = InputLocator(str(scenario_copy))

    path = isolated.get_building_comfort()
    table = pd.read_csv(path)
    table.loc[0, "Ve_lsp"] = math.nan
    table.to_csv(path, index=False)

    values = _read_computed_values(isolated)
    building = table.loc[0, "name"]
    assert values[building]["indoor-comfort"]["Ve_lsp"] is None


def test_the_two_computed_tabs_do_not_share_a_column_list():
    assert set(archetype_lock.computed_tab_columns()["indoor-comfort"]).isdisjoint(
        archetype_lock.computed_tab_columns()["internal-loads"])


# --------------------------------------------------------------------------- archetype key


def zone_on_disk():
    return pd.DataFrame({
        "name": ["B1", "B2"],
        "const_type": ["STANDARD1", "STANDARD2"],
        "use_type1": ["OFFICE", "MULTI_RES"],
        "use_type1r": [1.0, 1.0],
        "year": [2000, 1990],
        "height_ag": [9.0, 12.0],
    }).set_index("name")


@pytest.mark.parametrize("payload, expected", [
    ({"B1": {"const_type": "STANDARD1", "use_type1": "OFFICE"}}, []),
    ({"B1": {"const_type": "STANDARD4"}}, ["B1"]),
    ({"B1": {"use_type1": "MULTI_RES"}}, ["B1"]),
    ({"B1": {"year": 2001}}, []),                # year is not an archetype key -- see test_year_is_not_an_archetype_key
    ({"B1": {"height_ag": 99.0}}, []),          # geometry is not an archetype key
    ({"B2": {"year": 1991}, "B1": {"const_type": "X"}}, ["B1"]),
    ({"B9": {"const_type": "STANDARD1"}}, []),  # new building, no previous key
])
def test_archetype_key_changes_are_detected_server_side(payload, expected):
    """Decided from the payload against disk, never from a change log the client sends."""
    assert archetype_key_changed(payload, zone_on_disk()) == expected


def test_a_json_round_trip_does_not_look_like_a_change():
    """A ratio arrives as 0.5 or "0.5" depending on the client.

    Comparing them as strings would re-run the mapper on every save of every building.
    """
    assert archetype_key_changed({"B1": {"use_type1r": "1.0"}}, zone_on_disk()) == []
    assert archetype_key_changed({"B1": {"use_type1r": 1.0}}, zone_on_disk()) == []


# --------------------------------------------------------------------------- enforcement


def save(locator, tables=None, zone_overrides=None):
    """Drive `save_all_inputs` the way the input editor does."""
    import asyncio

    from cea.interfaces.dashboard.api.inputs import (
        InputForm,
        get_building_properties,
        save_all_inputs,
    )

    scenario = locator.scenario
    store = get_building_properties(scenario)
    payload = {k: (v if k in ("zone", "envelope") else None)
               for k, v in store["tables"].items()}
    if tables:
        for tab, rows in tables.items():
            payload[tab] = rows

    zone_shp = gpd.read_file(locator.get_zone_geometry())
    geojson = json.loads(zone_shp.to_crs("EPSG:4326").to_json())
    if zone_overrides:
        for building, columns in zone_overrides.items():
            payload["zone"][building].update(columns)
            for feature in geojson["features"]:
                if feature["properties"]["name"] == building:
                    feature["properties"].update(columns)

    form = InputForm(tables=payload, geojsons={"zone": geojson},
                     crs={"zone": zone_shp.crs.to_proj4()}, schedules={})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(save_all_inputs(scenario, form))


def envelope_value(locator, building="B1000", column="Hs"):
    return pd.read_csv(locator.get_building_architecture()).set_index("name").loc[building, column]


def test_a_locked_save_does_not_write_the_derived_tables(locator):
    """The stale-client case. The editor sends these tables on every save."""
    write_lock(locator, locked=True)
    before = envelope_value(locator)

    store_tables = {"envelope": {"B1000": {"Hs": 0.99}}}
    result = save(locator, tables=None)
    # drive it with a modified copy of the real payload
    from cea.interfaces.dashboard.api.inputs import get_building_properties
    tables = get_building_properties(locator.scenario)["tables"]
    tables["envelope"]["B1000"]["Hs"] = 0.99
    result = save(locator, tables={"envelope": tables["envelope"]})

    assert "envelope" in result["skipped_tables"]
    assert envelope_value(locator) == before
    assert store_tables  # the payload carried the edit; disk did not take it


def test_the_remap_does_not_truncate_the_derived_tables(locator):
    """The lock maps only the buildings whose archetype moved, and the rest must survive.

    `archetypes_mapper` used to replace each derived table with just the buildings it was
    given, so this would leave a one-row `envelope.csv`. It now merges the subset in -- see
    `test_archetypes_mapper_subset.py` -- and this asserts the lock depends on that.
    """
    write_lock(locator, locked=True)
    building_count = len(pd.read_csv(locator.get_building_architecture()))
    assert building_count > 1, "the fixture must have several buildings for this to mean anything"

    result = save(locator, zone_overrides={"B1000": {"const_type": "STANDARD4"}})

    assert result["remapped_buildings"] == ["B1000"], "report what the user changed"
    for path in (locator.get_building_architecture(), locator.get_building_air_conditioning(),
                 locator.get_building_comfort(), locator.get_building_internal(),
                 locator.get_building_supply()):
        assert len(pd.read_csv(path)) == building_count, f"{path} lost buildings"


def test_the_save_response_returns_the_remapped_tables(locator):
    """Without this the client keeps what it sent, and its next save overwrites the re-map.

    That is the failure this feature exists to prevent, and it happens on the *second* save of
    an ordinary edit -- not in any adversarial case.
    """
    write_lock(locator, locked=True)
    result = save(locator, zone_overrides={"B1000": {"const_type": "STANDARD1"}})

    assert result["remapped_buildings"] == ["B1000"]
    assert "envelope" in result["tables"]
    assert float(result["tables"]["envelope"]["B1000"]["Hs"]) == pytest.approx(
        float(envelope_value(locator)))


def test_a_locked_save_leaves_the_scenario_undrifted(locator):
    """Staying locked short-circuits `is_drifted` before any comparison runs."""
    write_lock(locator, locked=True)
    save(locator, zone_overrides={"B1000": {"const_type": "STANDARD2"}})
    assert is_drifted(locator) is False


def test_a_locked_save_rebaselines_the_whole_district_not_just_the_remapped_building(locator):
    """A save re-maps only the buildings whose key moved, but `write_lock` re-reads `zone.shp`
    and both derived tables in full -- the baseline must cover every building, not just the one
    that changed, or the very next unlock would read every untouched building as drifted."""
    write_lock(locator, locked=True)
    result = save(locator, zone_overrides={"B1000": {"use_type1": "MULTI_RES"}})
    assert result["remapped_buildings"] == ["B1000"], "a partial remap is the case under test"

    previous = read_lock(locator)
    assert set(previous.mapped_use_types) >= {"B1000", "B1010"}, (
        "the baseline must name buildings this save never touched too")

    write_lock(locator, locked=False, mapped_at=previous.mapped_at,
               mapped_use_types=previous.mapped_use_types,
               mapped_computed_values=previous.mapped_computed_values)
    assert is_drifted(locator) is False


def test_the_derived_tabs_are_exactly_what_the_mapper_writes(locator):
    """If the mapper gains an output, the lock must cover it or a gap opens silently."""
    from cea.interfaces.dashboard.api.inputs import INPUTS

    mapper_outputs = {
        "envelope": locator.get_building_architecture(),
        "hvac": locator.get_building_air_conditioning(),
        "indoor-comfort": locator.get_building_comfort(),
        "internal-loads": locator.get_building_internal(),
        "supply": locator.get_building_supply(),
    }
    assert set(ARCHETYPE_DERIVED_TABS) == set(mapper_outputs)
    for tab, path in mapper_outputs.items():
        assert getattr(locator, INPUTS[tab]["location"])() == path


def test_an_unlocked_save_behaves_exactly_as_before(locator):
    """Unlocked is the pre-existing behaviour: no skipping, no mapper, no lock writes."""
    write_lock(locator, locked=False)
    before = envelope_value(locator)

    from cea.interfaces.dashboard.api.inputs import get_building_properties
    tables = get_building_properties(locator.scenario)["tables"]
    tables["envelope"]["B1000"]["Hs"] = 0.55
    result = save(locator, tables={"envelope": tables["envelope"]})

    assert result["skipped_tables"] == []
    assert "remapped_buildings" not in result
    assert envelope_value(locator) == pytest.approx(0.55), "the edit lands while unlocked"
    assert envelope_value(locator) != before

    assert archetype_lock.read_lock(locator).locked is False


# --------------------------------------------------------------------------- transitions


def lock_state(locator):
    import asyncio

    from cea.interfaces.dashboard.api.inputs import get_archetype_lock

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        state = asyncio.run(get_archetype_lock(locator.scenario))
    return state["locked"], state["drifted"]


def set_locked(locator, locked):
    import asyncio

    from cea.interfaces.dashboard.api.inputs import ArchetypeLockForm, set_archetype_lock

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(set_archetype_lock(locator.scenario, ArchetypeLockForm(locked=locked)))


def toggle_zone_use_type1(locator, building):
    """Flip `use_type1` straight in `zone.shp`, the way an external tool (QGIS, a script) would.

    Deliberately not through `save_all_inputs`: the coarse fallback exists to catch exactly
    this -- a key moved by something other than the dashboard -- so the test has to move it the
    same way, not through the very save path this feature does not need to be told about.

    Toggles between two known-valid use types rather than setting a fixed target: `locator` is
    a module-scoped fixture other tests in this file also save `use_type1` edits against, so a
    hardcoded target could coincide with whatever an earlier test already left on disk and
    silently turn this into a no-op.
    """
    zone = gpd.read_file(locator.get_zone_geometry())
    current = zone.loc[zone["name"] == building, "use_type1"].iloc[0]
    new_value = "MULTI_RES" if current != "MULTI_RES" else "OFFICE"
    zone.loc[zone["name"] == building, "use_type1"] = new_value
    zone.to_file(locator.get_zone_geometry())
    return new_value


def test_unlocking_a_freshly_mapped_scenario_is_not_drifted(locator):
    """Unlocking is a change of ownership, not evidence of a change of content.

    The `use_type` keys the derived tables were mapped from are still the keys on disk, so the
    coarse fallback -- comparing exactly those -- still says they match. It just no longer
    promises to keep matching from here.
    """
    set_locked(locator, True)
    assert lock_state(locator) == (True, False)
    before = archetype_lock.read_lock(locator)

    set_locked(locator, False)

    assert lock_state(locator) == (False, False)
    after = archetype_lock.read_lock(locator)
    assert after.mapped_at == before.mapped_at, "unlocking has not mapped anything"
    assert after.mapped_use_types == before.mapped_use_types, "and must not move the baseline"
    assert after.mapped_computed_values == before.mapped_computed_values


def test_an_external_key_edit_while_unlocked_reads_as_drifted(locator):
    """The scenario this coarse fallback exists for: a `use_type` moved by something other than
    the dashboard, while unlocked, so no auto-remap ever saw it."""
    set_locked(locator, True)
    set_locked(locator, False)
    assert lock_state(locator) == (False, False)

    toggle_zone_use_type1(locator, "B1000")
    assert lock_state(locator) == (False, True)


def test_relocking_remaps_and_clears_the_drift(locator):
    """Re-locking is the point of no return: it regenerates the derived tables and re-baselines
    against whatever `zone.shp` says right now."""
    set_locked(locator, True)
    set_locked(locator, False)

    toggle_zone_use_type1(locator, "B1000")
    assert lock_state(locator) == (False, True)

    result = set_locked(locator, True)

    assert result["remapped"] is True
    assert lock_state(locator) == (True, False)

    set_locked(locator, False)
    assert lock_state(locator) == (False, False), "re-locking re-baselined against the new key"


def test_relocking_overwrites_a_hand_edited_derived_table(locator):
    """Re-locking is destructive to the derived tables regardless of whether the coarse
    server-side fallback happened to notice anything -- `envelope.csv` is a lookup tab, which
    this fallback never checks (that verification lives client-side against the live database),
    so this deliberately does not assert drift mid-test, only that locking always regenerates."""
    set_locked(locator, True)
    set_locked(locator, False)

    path = locator.get_building_architecture()
    edited = pd.read_csv(path)
    edited.loc[0, "Hs"] = 0.11
    edited.to_csv(path, index=False)

    result = set_locked(locator, True)

    assert result["remapped"] is True
    assert result["building_count"] == len(pd.read_csv(path))
    assert pd.read_csv(path).loc[0, "Hs"] != 0.11, "the hand-edit is replaced by the archetype value"


def test_unlocking_never_touches_the_files(locator):
    """Only re-locking is destructive. Unlocking is a statement of ownership."""
    set_locked(locator, True)
    before = pd.read_csv(locator.get_building_architecture())
    before_state = archetype_lock.read_lock(locator)

    result = set_locked(locator, False)

    assert result["remapped"] is False
    pd.testing.assert_frame_equal(pd.read_csv(locator.get_building_architecture()), before)
    after_state = archetype_lock.read_lock(locator)
    assert (after_state.mapped_at, after_state.mapped_use_types, after_state.mapped_computed_values) == (
        before_state.mapped_at, before_state.mapped_use_types, before_state.mapped_computed_values), (
        "unlocking flips one flag and records nothing new")


# --------------------------------------------------------------------------- added buildings


def test_a_new_building_triggers_a_remap(locator):
    """A building added while locked has no derived rows at all.

    `archetype_key_changed` skips it -- there is no previous archetype for it to have moved
    away from -- so without `buildings_added` it would sit with no envelope, HVAC, comfort,
    loads or supply until something else happened to run the mapper.
    """
    from cea.datamanagement.archetype_lock import buildings_added

    on_disk = pd.DataFrame({"name": ["B1", "B2"], "const_type": ["S1", "S2"]}).set_index("name")

    assert buildings_added({"B1": {}}, on_disk) == []
    assert buildings_added({"B1": {}, "B9": {}}, on_disk) == ["B9"]
    assert buildings_added({"B8": {}, "B9": {}}, on_disk) == ["B8", "B9"]

    # A key change and a new building both need the mapper; the save takes the union.
    assert archetype_key_changed({"B9": {"const_type": "S1"}}, on_disk) == [], (
        "a new building has no key change to report")


def test_adding_a_building_while_locked_gives_it_derived_rows(locator):
    """The wiring, not just the helper: save a zone with a new building and check it is mapped."""
    import asyncio
    import copy
    import json

    from cea.interfaces.dashboard.api.inputs import (
        InputForm,
        get_building_properties,
        save_all_inputs,
    )

    write_lock(locator, locked=True)
    envelope_before = set(pd.read_csv(locator.get_building_architecture())["name"])
    assert "B_NEW" not in envelope_before

    store = get_building_properties(locator.scenario)
    tables = {k: (v if k in ("zone", "envelope") else None) for k, v in store["tables"].items()}

    zone_shp = gpd.read_file(locator.get_zone_geometry())
    geojson = json.loads(zone_shp.to_crs("EPSG:4326").to_json())

    # Clone an existing building, shifted so the footprints do not coincide.
    template = copy.deepcopy(geojson["features"][0])
    template["properties"]["name"] = "B_NEW"
    template["geometry"]["coordinates"] = [
        [[x + 0.01, y + 0.01] for x, y in ring] for ring in template["geometry"]["coordinates"]
    ]
    geojson["features"].append(template)
    tables["zone"]["B_NEW"] = dict(template["properties"])

    form = InputForm(tables=tables, geojsons={"zone": geojson},
                     crs={"zone": zone_shp.crs.to_proj4()}, schedules={})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = asyncio.run(save_all_inputs(locator.scenario, form))

    assert "B_NEW" in result["remapped_buildings"], "a new building must trigger the mapper"
    envelope_after = set(pd.read_csv(locator.get_building_architecture())["name"])
    assert "B_NEW" in envelope_after, "the new building must get derived rows"

    previous = read_lock(locator)
    assert "B_NEW" in previous.mapped_use_types, "the remap that added it must also baseline it"
    write_lock(locator, locked=False, mapped_at=previous.mapped_at,
               mapped_use_types=previous.mapped_use_types,
               mapped_computed_values=previous.mapped_computed_values)
    assert is_drifted(locator) is False


def test_zone_stays_editable_while_locked(locator):
    """The lock restricts *where* you say something, not what you can do.

    Only the archetype-derived tabs are CEA's. `zone` -- and `surroundings` and `trees` --
    stay fully editable, including bulk edit, because that is where the user authors.
    """
    from cea.datamanagement.archetype_lock import ARCHETYPE_DERIVED_TABS

    for tab in ("zone", "surroundings", "trees"):
        assert tab not in ARCHETYPE_DERIVED_TABS

    write_lock(locator, locked=True)
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")
    before = float(zone.loc["B1000", "height_ag"])

    result = save(locator, zone_overrides={"B1000": {"height_ag": before + 6.0}})

    after = float(gpd.read_file(locator.get_zone_geometry()).set_index("name").loc["B1000", "height_ag"])
    assert after == pytest.approx(before + 6.0), "a zone edit lands while locked"
    # Geometry is not an archetype key, so nothing needed re-deriving.
    assert result.get("remapped_buildings", []) == []


# --------------------------------------------------------------------------- database-save trigger
#
# `zone.shp`-side drift (a building's archetype key moving) is covered above via `save()` /
# `save_all_inputs`. This covers the other side: editing the archetype *database* itself, which
# `archetypes_mapper` reads from but `save_all_inputs` never touches.


def save_database(locator, mutate):
    """Drive `PUT /inputs/databases` the way the database editor does.

    :param mutate: called with the dict `GET /inputs/databases` returned; edits it in place.
    """
    import asyncio

    from cea.interfaces.dashboard.api.inputs import (
        get_input_database_data,
        put_input_database_data,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        payload = asyncio.run(get_input_database_data(locator.scenario))
        mutate(payload)
        return asyncio.run(put_input_database_data(locator.scenario, payload))


def test_editing_a_const_type_remaps_only_buildings_using_it(locator):
    """`const_type` drives envelope/hvac/supply. STANDARD4 belongs to B1010 alone."""
    write_lock(locator, locked=True)
    before = envelope_value(locator, building="B1010", column="Hs")

    result = save_database(
        locator,
        lambda payload: payload["archetypes"]["construction"]["construction_types"]
        ["STANDARD4"].__setitem__("Hs", before + 0.05),
    )

    assert result["remapped_buildings"] == ["B1010"]
    assert envelope_value(locator, building="B1010", column="Hs") == pytest.approx(before + 0.05)
    # A building with a different const_type must be untouched.
    assert envelope_value(locator, building="B1000") != pytest.approx(before + 0.05)


def test_editing_a_use_type_remaps_buildings_referencing_it_in_any_slot(locator):
    """`use_type1/2/3` all drive indoor comfort and internal loads.

    SERVERROOM appears only as B1011's `use_type2` -- not its primary use -- so this also
    checks the second/third slots are read, not only `use_type1`.
    """
    write_lock(locator, locked=True)

    result = save_database(
        locator,
        lambda payload: payload["archetypes"]["use"]["use_types"]["SERVERROOM"]
        .__setitem__("El_Wm2", 999.0),
    )

    assert result["remapped_buildings"] == ["B1011"]


def test_editing_a_schedule_library_file_remaps_its_use_type(locator):
    """The per-use schedule CSVs are a source the mapper reads, same as the two archetype
    tables -- an edit there must trigger the same targeted re-map and rewrite the affected
    buildings' schedule files."""
    write_lock(locator, locked=True)
    schedule_path = locator.get_building_weekly_schedules("B1011")
    before_mtime = os.path.getmtime(schedule_path)

    def edit_servreroom_library(payload):
        rows = payload["archetypes"]["use"]["schedules"]["_library"]["SERVERROOM"]
        for row in rows:
            row["appliances"] = (row["appliances"] or 0) + 1

    result = save_database(locator, edit_servreroom_library)

    assert "B1011" in result["remapped_buildings"]
    assert os.path.getmtime(schedule_path) != before_mtime, "the schedule file must be rewritten"


def test_a_components_only_edit_does_not_remap_anything(locator):
    """The mapper never reads COMPONENTS or ASSEMBLIES -- nothing there can invalidate a
    derived table, so a save touching only those must not run the mapper at all."""
    write_lock(locator, locked=True)
    before = envelope_value(locator, building="B1010")

    result = save_database(locator, lambda payload: None)

    assert result.get("remapped_buildings", []) == []
    assert envelope_value(locator, building="B1010") == before


def test_a_byte_identical_resave_does_not_remap_anything(locator):
    """A JSON round trip must not look like a change -- `2000` vs `"2000"`, `NaN` vs `None`.

    Mirrors `test_a_json_round_trip_does_not_look_like_a_change` for the zone-key side.
    """
    write_lock(locator, locked=True)

    result = save_database(locator, lambda payload: None)

    assert result.get("remapped_buildings", []) == []


def test_an_unlocked_database_save_does_not_remap_anything(locator):
    """Unlocked means the user owns the derived tables -- CEA must not touch them here either,
    for the same reason `save_all_inputs` skips its own auto-remap while unlocked."""
    write_lock(locator, locked=False)
    before = envelope_value(locator, building="B1010")

    result = save_database(
        locator,
        lambda payload: payload["archetypes"]["construction"]["construction_types"]
        ["STANDARD4"].__setitem__("Hs", before + 0.05),
    )

    assert "remapped_buildings" not in result
    assert envelope_value(locator, building="B1010") == before


def test_a_database_remap_advances_the_lock_and_stays_undrifted(locator):
    """The scenario must still read as locked and not drifted, with `mapped_at` advanced."""
    import time

    write_lock(locator, locked=True)
    before = read_lock(locator)
    time.sleep(1.1)  # `mapped_at`'s resolution is whole seconds (see `write_lock`)

    def bump_hs(payload):
        # Bump relative to the database's own current value, not the envelope's -- an earlier
        # test in this module may have left the two diverged (that is the unlocked case's
        # whole point), and comparing against the wrong side could coincidentally match what
        # is already on disk and silently skip the re-map this test means to trigger.
        row = payload["archetypes"]["construction"]["construction_types"]["STANDARD4"]
        row["Hs"] = row["Hs"] + 0.05

    save_database(locator, bump_hs)

    state = read_lock(locator)
    assert state.locked is True
    assert state.mapped_at != before.mapped_at
    assert is_drifted(locator) is False
    assert state.mapped_computed_values == before.mapped_computed_values, (
        "a const_type-only database edit does not touch a single use_type-derived row")


def test_deleting_a_referenced_const_type_reports_a_remap_error_without_failing_the_save(locator):
    """The database write already succeeded and cannot be rolled back (`CEADatabase.save`'s
    own FIXME), so a mapper failure afterwards -- here, deleting a `const_type` a building
    (B1010) still references -- must surface as `remap_error` in a 200, not turn an already-
    successful save into a 500."""
    import asyncio

    from cea.interfaces.dashboard.api.inputs import get_input_database_data

    write_lock(locator, locked=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original_row = asyncio.run(get_input_database_data(locator.scenario))[
            "archetypes"]["construction"]["construction_types"]["STANDARD4"]

    try:
        result = save_database(
            locator,
            lambda payload: payload["archetypes"]["construction"]["construction_types"]
            .pop("STANDARD4"),
        )

        assert "remap_error" in result
        assert "remapped_buildings" not in result
        assert "STANDARD4" in result["remap_error"]
    finally:
        # Restore it -- this module-scoped fixture is shared with every test after this one.
        save_database(
            locator,
            lambda payload: payload["archetypes"]["construction"]["construction_types"]
            .__setitem__("STANDARD4", original_row),
        )


def test_create_new_scenario_locks_right_after_it_maps(tmp_path):
    """A freshly mapped scenario has nothing to distrust yet, so it should start locked rather
    than requiring the user to toggle Archetype Lock on by hand -- matching this module's own
    docstring claim ("Scenarios CEA creates are written locked, because they have just been
    mapped"), which nothing enforced before this change.

    `create_new_scenario` (`cea/interfaces/dashboard/api/project.py`) is a large, multi-step
    FastAPI route with no existing test scaffold -- zone/surroundings/weather/terrain/street
    generation are internal closures, not patchable module attributes -- so a full end-to-end
    drive of the route is disproportionate here (it is covered manually instead, see the
    plan's verification section: "Create a new scenario and confirm Archetype Lock reads as
    on"). This instead guards the specific ordering by inspecting the source: `write_lock`
    must be called, and it must come after `archetypes_mapper` and before the temp scenario is
    moved to its final path -- moved too early and `write_lock` would write the lock file into
    a directory `shutil.move` is about to relocate out from under it.
    """
    import inspect

    import cea.interfaces.dashboard.api.project as project_api

    source = inspect.getsource(project_api.create_new_scenario)
    mapper_pos = source.index("archetypes_mapper(config)")
    lock_pos = source.index("archetype_lock.write_lock(locator, locked=True)")
    move_pos = source.index("shutil.move(")

    assert mapper_pos < lock_pos < move_pos, (
        "the new scenario must be mapped, then locked, before it is moved to its final path")
