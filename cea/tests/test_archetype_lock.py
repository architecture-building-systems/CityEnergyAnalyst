"""Archetype-Lock: CEA owns the archetype-derived tables while locked.

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
import warnings

import geopandas as gpd
import pandas as pd
import pytest

from cea.datamanagement import archetype_lock
from cea.datamanagement.archetype_lock import (
    ARCHETYPE_DERIVED_TABS,
    ARCHETYPE_KEY_COLUMNS,
    archetype_key_changed,
    derived_signature,
    is_drifted,
    read_lock,
    write_lock,
)


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
    assert state.mapped_signature is None


def test_an_unreadable_lock_file_reads_as_unlocked(tmp_path):
    """A corrupt sidecar must not stop a user opening their scenario."""
    from cea.inputlocator import InputLocator

    locator = InputLocator(str(tmp_path))
    (tmp_path / "inputs").mkdir()
    with open(locator.get_archetype_lock_file(), "w", encoding="utf-8") as handle:
        handle.write("{not json")

    assert read_lock(locator).locked is False


# --------------------------------------------------------------------------- signature


def test_the_signature_tracks_the_derived_tables(locator):
    signature = derived_signature(locator)
    write_lock(locator, locked=True, signature=signature)
    assert is_drifted(locator) is False

    path = locator.get_building_architecture()
    original = pd.read_csv(path)
    try:
        edited = original.copy()
        edited.loc[0, "Hs"] = 0.42
        edited.to_csv(path, index=False)
        assert is_drifted(locator) is True
    finally:
        # The scenario fixture is module-scoped, so put the file back or later tests inherit
        # a hand-edit and start asserting against the wrong baseline.
        original.to_csv(path, index=False)
        write_lock(locator, locked=True, signature=derived_signature(locator))

    assert is_drifted(locator) is False


def test_a_scenario_that_was_never_mapped_is_not_drifted(tmp_path):
    """Nothing to drift from -- do not warn about a scenario CEA has never mapped."""
    from cea.inputlocator import InputLocator

    assert is_drifted(InputLocator(str(tmp_path))) is False


def test_the_signature_survives_duplicating_a_scenario(locator, tmp_path):
    """Users duplicate scenarios constantly; that must not read as drift.

    `hash_folder` keys on paths relative to the folder, so the digest does not move with the
    scenario. Hashing absolute paths would have made every copy look modified.
    """
    import shutil

    from cea.inputlocator import InputLocator

    copy = tmp_path / "copy"
    shutil.copytree(locator.scenario, copy)
    assert derived_signature(InputLocator(str(copy))) == derived_signature(locator)


# --------------------------------------------------------------------------- archetype key


def test_the_archetype_key_is_more_than_const_type():
    """`use_type1` drives indoor comfort and internal loads, `year` selects the vintage.

    Re-mapping only on `const_type` would leave a building switched from OFFICE to MULTI_RES
    with stale comfort and loads, and nothing saying so.
    """
    for column in ("const_type", "use_type1", "use_type1r", "year"):
        assert column in ARCHETYPE_KEY_COLUMNS


def zone_on_disk():
    return pd.DataFrame({
        "name": ["B1", "B2"],
        "const_type": ["STANDARD1", "STANDARD2"],
        "use_type1": ["OFFICE", "MULTI_RES"],
        "year": [2000, 1990],
        "height_ag": [9.0, 12.0],
    }).set_index("name")


@pytest.mark.parametrize("payload, expected", [
    ({"B1": {"const_type": "STANDARD1", "use_type1": "OFFICE"}}, []),
    ({"B1": {"const_type": "STANDARD4"}}, ["B1"]),
    ({"B1": {"use_type1": "MULTI_RES"}}, ["B1"]),
    ({"B1": {"year": 2001}}, ["B1"]),
    ({"B1": {"height_ag": 99.0}}, []),          # geometry is not an archetype key
    ({"B2": {"year": 1991}, "B1": {"const_type": "X"}}, ["B1", "B2"]),
    ({"B9": {"const_type": "STANDARD1"}}, []),  # new building, no previous key
])
def test_archetype_key_changes_are_detected_server_side(payload, expected):
    """Decided from the payload against disk, never from a change log the client sends."""
    assert archetype_key_changed(payload, zone_on_disk()) == expected


def test_a_json_round_trip_does_not_look_like_a_change():
    """`year` arrives as 2000 or "2000" depending on the client.

    Comparing them as strings would re-run the mapper on every save of every building.
    """
    assert archetype_key_changed({"B1": {"year": "2000"}}, zone_on_disk()) == []
    assert archetype_key_changed({"B1": {"year": 2000.0}}, zone_on_disk()) == []


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
    write_lock(locator, locked=True, signature=derived_signature(locator))
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
    write_lock(locator, locked=True, signature=derived_signature(locator))
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
    write_lock(locator, locked=True, signature=derived_signature(locator))
    result = save(locator, zone_overrides={"B1000": {"const_type": "STANDARD1"}})

    assert result["remapped_buildings"] == ["B1000"]
    assert "envelope" in result["tables"]
    assert float(result["tables"]["envelope"]["B1000"]["Hs"]) == pytest.approx(
        float(envelope_value(locator)))


def test_a_locked_save_leaves_the_scenario_undrifted(locator):
    """The signature is refreshed after the save, including when schedules were rewritten."""
    write_lock(locator, locked=True, signature=derived_signature(locator))
    save(locator, zone_overrides={"B1000": {"const_type": "STANDARD2"}})
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
    write_lock(locator, locked=False, signature=None)
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


def test_unlocking_keeps_the_fingerprint_so_drift_stays_measurable(locator):
    """Unlocking must carry the last mapping's fingerprint forward.

    Clearing it makes `is_drifted` fall back to "never mapped", so every subsequent edit reads
    as no-drift -- and marking the drifted `const_type` cells is the entire reason for
    unlocking. The bug is silent: the UI simply never warns.
    """
    set_locked(locator, True)
    assert lock_state(locator) == (True, False)

    set_locked(locator, False)
    assert lock_state(locator) == (False, False), "unlocking alone changes nothing"

    path = locator.get_building_architecture()
    original = pd.read_csv(path)
    try:
        edited = original.copy()
        edited.loc[0, "Hs"] = 0.11
        edited.to_csv(path, index=False)
        assert lock_state(locator) == (False, True), "an edit while unlocked must show as drift"
    finally:
        original.to_csv(path, index=False)

    assert archetype_lock.read_lock(locator).mapped_signature is not None


def test_relocking_remaps_and_clears_the_drift(locator):
    """Re-locking is the point of no return: it regenerates the derived tables."""
    set_locked(locator, True)
    set_locked(locator, False)

    path = locator.get_building_architecture()
    edited = pd.read_csv(path)
    edited.loc[0, "Hs"] = 0.11
    edited.to_csv(path, index=False)
    assert lock_state(locator) == (False, True)

    result = set_locked(locator, True)

    assert result["remapped"] is True
    assert result["building_count"] == len(pd.read_csv(path))
    assert pd.read_csv(path).loc[0, "Hs"] != 0.11, "the hand-edit is replaced by the archetype value"
    assert lock_state(locator) == (True, False)


def test_unlocking_never_touches_the_files(locator):
    """Only re-locking is destructive. Unlocking is a statement of ownership."""
    set_locked(locator, True)
    before = derived_signature(locator)

    result = set_locked(locator, False)

    assert result["remapped"] is False
    assert derived_signature(locator) == before


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

    write_lock(locator, locked=True, signature=derived_signature(locator))
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


def test_zone_stays_editable_while_locked(locator):
    """The lock restricts *where* you say something, not what you can do.

    Only the archetype-derived tabs are CEA's. `zone` -- and `surroundings` and `trees` --
    stay fully editable, including bulk edit, because that is where the user authors.
    """
    from cea.datamanagement.archetype_lock import ARCHETYPE_DERIVED_TABS

    for tab in ("zone", "surroundings", "trees"):
        assert tab not in ARCHETYPE_DERIVED_TABS

    write_lock(locator, locked=True, signature=derived_signature(locator))
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")
    before = float(zone.loc["B1000", "height_ag"])

    result = save(locator, zone_overrides={"B1000": {"height_ag": before + 6.0}})

    after = float(gpd.read_file(locator.get_zone_geometry()).set_index("name").loc["B1000", "height_ag"])
    assert after == pytest.approx(before + 6.0), "a zone edit lands while locked"
    # Geometry is not an archetype key, so nothing needed re-deriving.
    assert result.get("remapped_buildings", []) == []
