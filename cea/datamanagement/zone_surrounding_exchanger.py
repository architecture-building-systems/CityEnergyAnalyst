"""
Move buildings between the zone and the surroundings.

Zone buildings are simulated; surrounding buildings only cast shade. Moving a building changes
what every result was computed for, so the tool deletes existing results (after the user opts in
via ``delete-outputs``) rather than leave totals and per-building files that no longer match.
Solar radiation is kept, since every building still casts the same shade, except for buildings
moved to the surroundings.
"""

import os
import shutil
import tempfile

import geopandas as gpd
import pandas as pd

import cea.config
import cea.inputlocator
from cea.datamanagement import archetype_lock
from cea.datamanagement.archetypes_mapper import remove_building_properties
from cea.datamanagement.constants import OSM_BUILDING_CATEGORIES, OTHER_OSM_CATEGORIES_UNCONDITIONED
from cea.datamanagement.databases_verification import (
    assert_input_geometry_acceptable_values_floor_height,
    assert_input_geometry_only_polygon,
)
from cea.datamanagement.surroundings_helper import generate_empty_surroundings
from cea.datamanagement.utils import VOID_FLOORS_COLUMN, VOID_HEIGHT_COLUMN
from cea.datamanagement.zone_helper import calc_category

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, uuen Company"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "shi@uuen.cloud"
__status__ = "Production"

# Copied from the template building to buildings moved to the zone. Street-level address fields
# (house number, street, postcode, house name) are left blank: they describe one building only.
TEMPLATE_COLUMNS = ['year', 'const_type', 'use_type1', 'use_type1r', 'use_type2', 'use_type2r',
                    'use_type3', 'use_type3r']
MOVED_TO_ZONE_REFERENCE = "CEA - moved from surroundings"
DEFAULT_USE_TYPE = "MULTI_RES"

# Kept when results are deleted: saved canvases are layouts, not results, and radiation stays
# valid because every building still casts the same shade.
KEPT_OUTPUT_FOLDERS = ('canvas',)
KEPT_OUTPUT_DATA_FOLDERS = ('solar-radiation',)


def validate(zone, surroundings, to_surroundings, to_zone, template, delete_outputs):
    """Raise ``ValueError`` if the requested exchange cannot run. Nothing is touched before this
    passes."""
    if not delete_outputs:
        raise ValueError(
            "This tool deletes existing results because they no longer match the zone. "
            "Set 'delete-outputs' to true to continue.")
    if not to_surroundings and not to_zone:
        raise ValueError("Select at least one building to move.")

    both = sorted(set(to_surroundings) & set(to_zone))
    if both:
        raise ValueError(f"Buildings cannot be moved both ways at once: {', '.join(both)}.")

    for moved, source, label in ((to_surroundings, zone, 'zone'), (to_zone, surroundings, 'surroundings')):
        missing = sorted(set(moved) - set(source['name']))
        if missing:
            raise ValueError(f"Not found in the {label}: {', '.join(missing)}.")
        duplicated = sorted(source.loc[source['name'].isin(moved) & source['name'].duplicated(keep=False), 'name'].unique())
        if duplicated:
            raise ValueError(f"These names appear more than once in the {label}, so the building to "
                             f"move is ambiguous: {', '.join(duplicated)}.")

    if set(zone['name']) <= set(to_surroundings):
        raise ValueError("The zone must keep at least one building.")
    if template is not None:
        if template not in set(zone['name']):
            raise ValueError(f"Template building '{template}' is not in the zone.")
        if template in set(to_surroundings):
            raise ValueError(f"Template building '{template}' cannot also be moved to the surroundings.")

    assert_input_geometry_only_polygon(zone[zone['name'].isin(to_surroundings)])
    assert_input_geometry_only_polygon(surroundings[surroundings['name'].isin(to_zone)])


def exchange(zone, surroundings, to_surroundings, to_zone, *, template=None, construction_types=None):
    """Move buildings between ``zone`` and ``surroundings``. Pure: no file I/O.

    :param construction_types: the construction-type archetype database, used to pick
        ``const_type`` from the construction year when no ``template`` is given.
    :return: ``(new_zone, new_surroundings, renamed)``, where ``renamed`` maps each moved
        building whose name was already taken in its destination to its new name.
    """
    is_leaving_zone = zone['name'].isin(to_surroundings)
    is_leaving_surroundings = surroundings['name'].isin(to_zone)
    zone_kept = zone[~is_leaving_zone]
    surroundings_kept = surroundings[~is_leaving_surroundings]
    renamed = {}

    # Zone -> surroundings: keep only what the surroundings describe. An empty surroundings file
    # may carry no coordinate system; it then takes the zone's.
    surroundings_crs = surroundings.crs or zone.crs
    leaving_zone = zone[is_leaving_zone].to_crs(surroundings_crs)
    to_surr = gpd.GeoDataFrame(
        {'name': _unique_names(leaving_zone['name'], set(surroundings_kept['name']), renamed),
         'height_ag': leaving_zone['height_ag'].values,
         'floors_ag': leaving_zone['floors_ag'].values},
        geometry=leaving_zone.geometry.values, crs=surroundings_crs)
    if 'REFERENCE' in surroundings.columns and 'reference' in leaving_zone.columns:
        to_surr['REFERENCE'] = leaving_zone['reference'].values

    # Surroundings -> zone: geometry and heights from the surroundings, the rest from the
    # template building or the same defaults `zone_helper` uses.
    leaving_surr = surroundings[is_leaving_surroundings].to_crs(zone.crs)
    to_zone_df = gpd.GeoDataFrame(
        {'name': _unique_names(leaving_surr['name'], set(zone_kept['name']), renamed),
         'floors_ag': leaving_surr['floors_ag'].values,
         'height_ag': leaving_surr['height_ag'].values,
         'floors_bg': 0,
         'height_bg': 0.0,
         'reference': MOVED_TO_ZONE_REFERENCE},
        geometry=leaving_surr.geometry.values, crs=zone.crs)
    for column in (VOID_HEIGHT_COLUMN, VOID_FLOORS_COLUMN):
        if column in zone.columns:
            to_zone_df[column] = 0
    typology = _template_typology(zone, template) if template is not None else \
        _default_typology(zone, leaving_surr, construction_types)
    for column, values in typology.items():
        to_zone_df[column] = values
    # Every other zone column (address fields) starts blank, to be filled in the Input Editor.
    for column in zone.columns:
        if column not in to_zone_df.columns:
            to_zone_df[column] = '' if zone[column].dtype == object else None
    if len(to_zone_df):
        assert_input_geometry_acceptable_values_floor_height(to_zone_df)

    new_zone = _append(zone_kept, to_zone_df[zone.columns])
    new_surroundings = _append(surroundings_kept, to_surr)
    return new_zone, new_surroundings, renamed


def check_archetypes(moved_in, construction_types, use_types):
    """Raise ``ValueError`` if a building moved to the zone has a construction or use type the
    scenario's archetype database does not define."""
    unknown_const = sorted(set(moved_in['const_type']) - set(construction_types['const_type']))
    used = pd.concat([moved_in[c] for c in ('use_type1', 'use_type2', 'use_type3')])
    unknown_use = sorted(set(used) - set(use_types['use_type']) - {'NONE'})
    if unknown_const or unknown_use:
        unknown = ', '.join(unknown_const + unknown_use)
        raise ValueError(f"Buildings moved to the zone would get types missing from the archetype "
                         f"database: {unknown}. Pick a template building, or add these types to "
                         f"the database first.")


def delete_outputs(locator, removed_buildings):
    """Delete every result except saved canvases and solar radiation, plus the radiation of
    ``removed_buildings``. Return the paths deleted."""
    deleted = []
    export_folder = locator.get_export_folder()
    if os.path.isdir(export_folder):
        shutil.rmtree(export_folder)
        deleted.append(export_folder)

    output_folder = locator.get_output_folder()
    data_folder = os.path.dirname(locator.get_solar_radiation_folder())
    for folder, kept in ((output_folder, KEPT_OUTPUT_FOLDERS), (data_folder, KEPT_OUTPUT_DATA_FOLDERS)):
        if not os.path.isdir(folder):
            continue
        for entry in sorted(os.listdir(folder)):
            path = os.path.join(folder, entry)
            if entry in kept or path == data_folder:
                continue
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            deleted.append(path)

    for building in removed_buildings:
        for path in (locator.get_radiation_building(building),
                     locator.get_radiation_building_sensors(building),
                     locator.get_radiation_metadata(building)):
            if os.path.isfile(path):
                os.remove(path)
                deleted.append(path)
    return deleted


def zone_surrounding_exchanger(locator, to_surroundings, to_zone, template, delete_outputs_confirmed):
    zone = gpd.read_file(locator.get_zone_geometry())
    surroundings_path = locator.get_surroundings_geometry()
    surroundings = gpd.read_file(surroundings_path) if os.path.isfile(surroundings_path) \
        else generate_empty_surroundings(zone.crs)

    validate(zone, surroundings, to_surroundings, to_zone, template, delete_outputs_confirmed)
    construction_types = pd.read_csv(locator.get_database_archetypes_construction_type()) if to_zone else None
    new_zone, new_surroundings, renamed = exchange(
        zone, surroundings, to_surroundings, to_zone, template=template, construction_types=construction_types)
    moved_in = [renamed.get(name, name) for name in to_zone]
    if moved_in:
        # Checked before anything is deleted: the mapper would otherwise fail only after the
        # results are gone and the geometry has changed.
        use_types = pd.read_csv(locator.get_database_archetypes_use_type())
        check_archetypes(new_zone[new_zone['name'].isin(moved_in)], construction_types, use_types)

    for path in delete_outputs(locator, to_surroundings):
        print(f"Deleted {os.path.relpath(path, locator.scenario)}")
    _write_shapefiles({locator.get_zone_geometry(): new_zone, surroundings_path: new_surroundings})

    lock = archetype_lock.read_lock(locator)
    if lock.locked:
        remove_building_properties(locator, to_surroundings)
        if moved_in:
            archetype_lock.remap_and_relock(locator, moved_in)
        else:
            # Nothing was mapped, so keep `mapped_at`; the baselines still drop the removed buildings.
            archetype_lock.write_lock(locator, locked=True, mapped_at=lock.mapped_at)

    for old, new in renamed.items():
        print(f"Renamed {old} to {new}: the name was already taken.")
    if to_surroundings:
        print(f"Moved to the surroundings: {', '.join(renamed.get(n, n) for n in to_surroundings)}")
    if moved_in:
        print(f"Moved to the zone: {', '.join(moved_in)}")
        if not lock.locked:
            print(f"Archetype Lock is off, so no building properties were created for "
                  f"{', '.join(moved_in)}. Run Archetypes Mapper for them, or add them in the "
                  f"Input Editor, before simulating.")
        print(f"Run solar radiation for {', '.join(moved_in)} before simulating "
              f"{'it' if len(moved_in) == 1 else 'them'}.")


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(config.scenario)
    section = config.zone_surrounding_exchanger
    zone_surrounding_exchanger(
        locator,
        to_surroundings=list(section.zone_to_surroundings or []),
        to_zone=list(section.surroundings_to_zone or []),
        template=section.template_building,
        delete_outputs_confirmed=section.delete_outputs,
    )


def _unique_names(names, taken, renamed):
    """Keep each name unless ``taken`` already holds it; then append ``_1``, ``_2``, ...
    Records renames in ``renamed`` and adds every result to ``taken``."""
    result = []
    for name in names:
        new = name
        suffix = 1
        while new in taken:
            new = f"{name}_{suffix}"
            suffix += 1
        if new != name:
            renamed[name] = new
        taken.add(new)
        result.append(new)
    return result


def _template_typology(zone, template):
    row = zone.loc[zone['name'] == template].iloc[0]
    return {column: row[column] for column in TEMPLATE_COLUMNS if column in zone.columns}


def _default_typology(zone, leaving_surroundings, construction_types):
    """The defaults `zone_helper` gives new buildings: use type from the OSM category, else the
    zone's most common use type; the zone's median construction year and its construction type."""
    if leaving_surroundings.empty:
        return {}
    usable = zone.loc[~zone['use_type1'].isin(['NONE', 'PARKING']), 'use_type1']
    fallback_use = usable.mode()[0] if not usable.empty else DEFAULT_USE_TYPE
    categories = leaving_surroundings['category'] if 'category' in leaving_surroundings.columns \
        else pd.Series(None, index=leaving_surroundings.index)
    use_type1 = [OSM_BUILDING_CATEGORIES.get(c) or
                 ("PARKING" if c in OTHER_OSM_CATEGORIES_UNCONDITIONED else fallback_use)
                 for c in categories]
    year = int(zone['year'].median())
    return {
        'year': year,
        'const_type': calc_category(construction_types, [year])[0],
        'use_type1': use_type1, 'use_type1r': 1.0,
        'use_type2': 'NONE', 'use_type2r': 0.0,
        'use_type3': 'NONE', 'use_type3r': 0.0,
    }


def _append(kept, moved):
    if moved.empty:
        return kept
    if kept.empty:
        return moved
    return gpd.GeoDataFrame(pd.concat([kept, moved], ignore_index=True), crs=moved.crs)


def _write_shapefiles(frames):
    """Write each frame to a temporary folder first, then move them all into place, so a
    failure while writing leaves both shapefiles untouched."""
    staged = {}
    try:
        for path, frame in frames.items():
            folder = tempfile.mkdtemp(dir=os.path.dirname(path))
            staged[path] = os.path.join(folder, os.path.basename(path))
            frame.to_file(staged[path])
        for path, staged_path in staged.items():
            folder, stem = os.path.dirname(path), os.path.splitext(os.path.basename(path))[0]
            staged_folder = os.path.dirname(staged_path)
            written = set(os.listdir(staged_folder))
            # Sidecars the new file does not have (e.g. an ArcGIS `.sbn` index) would describe
            # the old geometry.
            for old in os.listdir(folder):
                if os.path.splitext(old)[0] == stem and old not in written:
                    os.remove(os.path.join(folder, old))
            for sidecar in written:
                os.replace(os.path.join(staged_folder, sidecar), os.path.join(folder, sidecar))
    finally:
        for staged_path in staged.values():
            shutil.rmtree(os.path.dirname(staged_path), ignore_errors=True)


if __name__ == '__main__':
    main(cea.config.Configuration())
