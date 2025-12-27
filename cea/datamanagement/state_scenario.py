import os
import shutil
from typing import Any

import geopandas as gpd
import pandas as pd
import yaml

from cea.config import Configuration
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.archetypes_mapper import archetypes_mapper
from cea.datamanagement.timeline_integrity import check_district_timeline_log_yaml_integrity
from cea.datamanagement.timeline_integrity import compute_state_year_missing_modifications, merge_modify_recipes
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.timeline_log import add_year_in_yaml, del_year_in_yaml, load_log_yaml, save_log_yaml
from cea.datamanagement.state_transaction import FileSnapshot, snapshot_state_year_files
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM


def create_state_in_time_scenario(
    config: Configuration,
    year_of_state: int,
    *,
    update_yaml: bool = True,
) -> None:
    """
    Create a new state-in-time scenario based on the current scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        locator (InputLocator): The input locator object for file paths.
        year_of_state (int): The year of the event scenario. If a building year is larger than
        this year, it will not be included in the event scenario.
        event_content (dict): A dictionary containing the content of the event scenario.
    Returns:
        None
    """
    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(year_of_state)
    input_folder_path = main_locator.get_input_folder()
    state_locator = InputLocator(state_scenario_folder)
    # copy all files from the input folder to the event scenario folder
    shutil.copytree(input_folder_path, state_locator.get_input_folder(), dirs_exist_ok=True) # make sure existing files are overwritten
    if update_yaml:
        add_year_in_yaml(config, year_of_state)
    return None

def _regenerate_building_properties_from_archetypes(locator: InputLocator) -> None:
    """Regenerate building-properties inputs from archetypes.

    This enforces the "archetypes are canonical" assumption: per-building inputs (envelope, hvac, internal loads,
    comfort, supply and schedules) are derived from zone.shp + archetype databases for that state-year.
    """
    list_buildings = locator.get_zone_building_names()
    if not list_buildings:
        return
    archetypes_mapper(
        locator,
        update_architecture_dbf=True,
        update_air_conditioning_systems_dbf=True,
        update_indoor_comfort_dbf=True,
        update_internal_loads_dbf=True,
        update_supply_systems_dbf=True,
        update_schedule_operation_cea=True,
        list_buildings=list_buildings,
    )

def remove_state_in_time_scenario(config: Configuration, year_of_state: int) -> None:
    """
    Delete an existing event scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario to be deleted.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_state_in_time_scenario_folder(year_of_state)
    shutil.rmtree(event_scenario_folder, ignore_errors=True)
    del_year_in_yaml(config, year_of_state)
    return None

def delete_unexisting_buildings_from_event_scenario(config: Configuration, year_of_state: int) -> list[str]:
    """
    Delete buildings from the event scenario that do not yet exist in the specified event year.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario. If a building year is larger than this year, it will be deleted from the event scenario.
    Returns:
        list[str]: A list of building names that were deleted from the event scenario.
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_state_in_time_scenario_folder(year_of_state)
    # ensure the event scenario folder exists
    state_locator = InputLocator(event_scenario_folder)
    if not os.path.exists(state_locator.get_zone_geometry()):
        raise FileNotFoundError(f"Event scenario folder for year {year_of_state} does not exist.")
    
    builings_to_delete = []
    buildings_gdf_current = gpd.read_file(locator.get_zone_geometry())
    for _, building in buildings_gdf_current.iterrows():
        building_year = building.get('year', None)

        if building_year is not None and building_year > year_of_state:
            builings_to_delete.append(building['name'])

    # delete all files related to the buildings to delete
    for building_name in builings_to_delete:
        delete_building_schedule(state_locator, building_name)

    # delete buildings from geometry file
    geometry_gdf, _, _ = shapefile_to_WSG_and_UTM(state_locator.get_zone_geometry())
    geometry_gdf.set_index('name', inplace=True)
    geometry_gdf = geometry_gdf.drop(builings_to_delete)
    verify_input_geometry_zone(geometry_gdf.reset_index())
    geometry_gdf.to_file(state_locator.get_zone_geometry())

    monthly_multiplier_df_path = (
        state_locator.get_building_weekly_schedules_monthly_multiplier_csv()
    )
    envelope_df_path = state_locator.get_building_architecture()
    hvac_df_path = state_locator.get_building_air_conditioning()
    indoor_comfort_df_path = state_locator.get_building_comfort()
    internal_loads_df_path = state_locator.get_building_internal()
    supply_df_path = state_locator.get_building_supply()
    # delete building row from all dfs
    for df_path in [
        monthly_multiplier_df_path,
        envelope_df_path,
        hvac_df_path,
        indoor_comfort_df_path,
        internal_loads_df_path,
        supply_df_path,
    ]:
        if os.path.exists(df_path):
            df = pd.read_csv(df_path, index_col="name")
            df = df.drop(builings_to_delete, errors="ignore")
            df.to_csv(df_path)

    return builings_to_delete

def delete_building_schedule(state_locator: InputLocator, building_name: str) -> None:
    """
    Delete the schedule file related to a specific building in the event scenario.
    This includes the following file:
    - building schedule file (`locator.get_building_occupancy_schedule(building_name)`)
    """
    schedule_file_path = state_locator.get_building_weekly_schedules(building_name)
    if os.path.exists(schedule_file_path):
        os.remove(schedule_file_path)
    return None

def modify_state_construction(
    config: Configuration,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
    *,
    log_data: dict[int, dict[str, Any]] | None = None,
) -> None:
    """
    Modify the construction recipe of buildings in the event scenario based on the provided modification dictionary.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario.
        modify_recipe (dict): A dictionary specifying the material-based modifications to be made to the construction recipes.
            For example:
            ```
            {
                "STANDARD1": {
                    "wall": {
                        "material_name_1": "phenolic_resin_pf",
                        "thickness_1_m": 0.08,
                        "material_name_2": "steel_sheet_galvanised",
                        "thickness_2_m": 0.002,
                        "material_name_3": "concrete_1_percent_steel_reinforcement",
                        "thickness_3_m": 0.10,
                        "Service_Life": 30
                    },
                    "roof": {
                        "material_name_1": "phenolic_resin_pf",
                        "thickness_1_m": None,  # keep current value
                        "material_name_2": None, # keep current value
                        "thickness_2_m": None,   # keep current value
                        "material_name_3": None, # keep current value
                        "thickness_3_m": 0.12,
                        "Service_Life": None     # keep current value
                    },
                    "base": {
                        "material_name_1": "glass_wool_supafil",
                        "thickness_1_m": 0.02,
                        "material_name_2": "brass_bronze_sheet",
                        "thickness_2_m": 0.0,
                        "material_name_3": "stainless_steel_sheet_tinned",
                        "thickness_3_m": 0.0
                    }
                }
            }
            ```
            Note that the outer dictionary keys are archetype names, 
            the middle dictionary keys are component types.
            Field names must match the envelope database column keys 
            (e.g., `material_name_1`, `thickness_1_m`, `Service_Life`).
    Returns:
        None
    """
    modified = _apply_state_construction_changes(config, year_of_state, modify_recipe)
    if not modified:
        print(f"No modifications were made to the envelope database in year {year_of_state}.")
        return
    # Store only the changed fields (delta) for record-keeping.
    if log_data is None:
        log_modifications(config, year_of_state, modify_recipe)
    else:
        _log_modifications_in_memory(log_data, year_of_state, modify_recipe)
    return None


def _apply_state_construction_changes(
    config: Configuration,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
    *,
    trigger_year: int | None = None,
) -> bool:
    """Apply construction changes to the state scenario databases.

    Returns True if any database values were modified.

    NOTE: This does not write to the district timeline YAML. Callers must log appropriately.
    """
    archetypes_to_modify = modify_recipe.keys()
    if not archetypes_to_modify:
        remove_state_in_time_scenario(config, year_of_state)
        raise ValueError(
            f"No archetypes specified for modification in the event scenario. The state-in-time scenario for year {year_of_state} has been deleted."
        )

    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(year_of_state)
    state_locator = InputLocator(state_scenario_folder)

    archetype_df = pd.read_csv(
        state_locator.get_database_archetypes_construction_type(),
        index_col="const_type",
    )
    envelope_lookup = EnvelopeLookup.from_locator(state_locator)
    dbs_overall_modified = 0
    for archetype in archetypes_to_modify:
        if archetype not in archetype_df.index:
            raise ValueError(
                f"Archetype '{archetype}' not found in construction type database."
            )
        for component, modifications in modify_recipe[archetype].items():
            db_modified = 0
            code_current = archetype_df.at[archetype, f"type_{component}"]
            # create a new component code by "(capitalized component)_(archetype)_YEAR_(event_year)"
            envelope_db_name = "floor" if component == "base" else component
            component_db = envelope_lookup._df_for(envelope_db_name)
            code_new = f"{envelope_db_name.capitalize()}_{archetype}_YEAR_{year_of_state}"

            if code_new in component_db.index:
                code_new = shift_code_name_plus1(component_db, code_new)
            new_row = component_db.loc[code_current].copy()
            new_row.name = code_new

            for field, new_value in modifications.items():
                if new_value is not None:
                    if field.startswith("material_name_") or field.startswith("thickness_"):
                        component_field_name = field
                    else:
                        component_field_name = envelope_lookup._col(envelope_db_name, field)
                    new_row[component_field_name] = new_value
                    db_modified += 1

            if db_modified:
                description_new = (
                    f"Modified {component} for archetype {archetype} in year {year_of_state}, based on {code_current}, "
                    f"fields modified: {', '.join(modifications.keys())}"
                )
                if trigger_year is not None:
                    description_new += f" (reconciled due to year {trigger_year})"
                new_row["description"] = description_new
                component_db.loc[new_row.name, :] = new_row
                archetype_df.at[archetype, f"type_{component}"] = code_new

            dbs_overall_modified += db_modified

    if not dbs_overall_modified:
        return False

    archetype_df.reset_index(inplace=True)
    archetype_df.to_csv(state_locator.get_database_archetypes_construction_type(), index=False)
    envelope_lookup.envelope.save(state_locator)
    return True


def _append_future_year_reconciliation_in_memory(
    trigger_year: int,
    affected_year: int,
    applied_recipe: dict[str, dict[str, dict[str, Any]]],
    *,
    log_data: dict[int, dict[str, Any]],
) -> None:
    entry = log_data.get(affected_year, {})
    reconciliations = entry.get("reconciliations", []) or []
    now = str(pd.Timestamp.now())
    reconciliations.append(
        {
            "trigger_year": trigger_year,
            "applied_at": now,
            "modifications": applied_recipe,
        }
    )
    entry["reconciliations"] = reconciliations
    entry["latest_reconciled_at"] = now
    log_data[affected_year] = entry


def _list_existing_state_years(main_locator: InputLocator) -> list[int]:
    years: list[int] = []
    district_timeline_folder = main_locator.get_district_timeline_states_folder()
    if not os.path.exists(district_timeline_folder):
        return years

    for folder_name in os.listdir(district_timeline_folder):
        if not folder_name.startswith("state_"):
            continue
        year_str = folder_name.replace("state_", "")
        try:
            years.append(int(year_str))
        except ValueError:
            print(
                f"Warning: Invalid state-in-time folder name '{folder_name}' in district timeline folder."
            )
    years.sort()
    return years


def _update_future_state_scenarios_after_year_event(
    config: Configuration,
    year_of_state: int,
    *,
    log_data: dict[int, dict[str, Any]],
) -> None:
    """Ensure future state scenarios reflect cumulative district evolution.

    If a state year `Y` is created/modified after later years already exist, those later years may become stale.
    This function updates each existing `state_{year}` for year > Y to include cumulative modifications
    (all changes up to and including that year).

    NOTE: The district timeline YAML is not modified for these future years.
    """
    main_locator = InputLocator(config.scenario)
    existing_state_years = _list_existing_state_years(main_locator)
    affected_years = [y for y in existing_state_years if y > year_of_state]
    if not affected_years:
        return

    print(
        "Warning: Creating or modifying an earlier state year updates already-created future years "
        "(including years that may already have been modified before). "
        f"Affected years: {affected_years}."
    )

    missing_in_yaml = [y for y in affected_years if y not in log_data]
    if missing_in_yaml:
        raise ValueError(
            "The following future state years exist in folders but not in the district timeline log file: "
            f"{sorted(missing_in_yaml)}"
        )

    cumulative_by_year: dict[int, dict[str, dict[str, dict[str, Any]]]] = {}
    cumulative: dict[str, dict[str, dict[str, Any]]] = {}
    for year in sorted(log_data.keys()):
        year_entry = log_data.get(year, {}) or {}
        year_modifications = (year_entry.get("modifications", {}) or {})
        cumulative = merge_modify_recipes(cumulative, year_modifications)
        cumulative_by_year[year] = cumulative

    all_errors: list[str] = []
    updated_years: list[int] = []
    unchanged_years: list[int] = []

    for future_year in affected_years:
        expected = cumulative_by_year.get(future_year, {})
        missing_recipe, errors = compute_state_year_missing_modifications(
            config, future_year, expected
        )
        all_errors.extend(errors)

        if missing_recipe:
            modified = _apply_state_construction_changes(
                config,
                future_year,
                missing_recipe,
                trigger_year=year_of_state,
            )
            if modified:
                _append_future_year_reconciliation_in_memory(
                    trigger_year=year_of_state,
                    affected_year=future_year,
                    applied_recipe=missing_recipe,
                    log_data=log_data,
                )
                updated_years.append(future_year)
            else:
                unchanged_years.append(future_year)
        else:
            unchanged_years.append(future_year)

    if all_errors:
        formatted = "\n".join(f"- {msg}" for msg in all_errors)
        raise ValueError(
            "Errors occurred while updating future state scenarios.\n" + formatted
        )

    if updated_years:
        print(
            "Updated future state scenario databases to include cumulative changes. "
            f"Years updated: {updated_years}."
        )
    if unchanged_years:
        print(
            "No database changes were required for some future years. "
            f"Years unchanged: {unchanged_years}."
        )

def log_modifications(
    config: Configuration,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
) -> None:
    """
    Log the modifications made to the envelope database in a YAML file for record-keeping.
    Parameters:
        state_locator (InputLocator): The input locator object for the event scenario.
        year_of_state (int): The year of the event scenario.
        modify_recipe (dict): The modification recipe used for the modifications.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    yml_path = locator.get_district_timeline_log_file()
    if os.path.exists(yml_path):
        with open(yml_path, "r") as f:
            existing_data: dict[int, dict[str, Any]] = yaml.safe_load(f) or {}
    else:
        existing_data: dict[int, dict[str, Any]] = {}
    current_year_modifications = existing_data.get(year_of_state, {})
    current_year_modifications.setdefault("modifications", {}).update(modify_recipe)
    current_year_modifications["latest_modified_at"] = str(pd.Timestamp.now())
    existing_data[year_of_state] = current_year_modifications
    save_log_yaml(locator, existing_data)


def _log_modifications_in_memory(
    log_data: dict[int, dict[str, Any]],
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
) -> None:
    entry = log_data.get(year_of_state, {})
    entry.setdefault("modifications", {}).update(modify_recipe)
    entry["latest_modified_at"] = str(pd.Timestamp.now())
    log_data[year_of_state] = entry
    
def shift_code_name_plus1(db, code_prefix):
    n = db[db.index.str.startswith(code_prefix)].shape[0]
    return code_prefix + f"_{n + 1}"

def create_modify_recipe(
    config: Configuration,
) -> dict[str, dict[str, dict[str, float | int | str]]]:
    """
    Build modification recipe, pruning None-valued fields and empty components / archetypes.
    """
    config_section = config.district_events
    archetypes_to_modify = config_section.archetypes
    if not archetypes_to_modify:
        raise ValueError("No archetypes specified for modification in the event scenario.")

    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]] = {}

    for archetype in archetypes_to_modify:
        raw_components = {
            "wall": {
                "material_name_1": config_section.wall_material_name_1,
                "thickness_1_m": config_section.wall_thickness_1_m,
                "material_name_2": config_section.wall_material_name_2,
                "thickness_2_m": config_section.wall_thickness_2_m,
                "material_name_3": config_section.wall_material_name_3,
                "thickness_3_m": config_section.wall_thickness_3_m,
                "Service_Life": config_section.wall_lifetime,
            },
            "roof": {
                "material_name_1": config_section.roof_material_name_1,
                "thickness_1_m": config_section.roof_thickness_1_m,
                "material_name_2": config_section.roof_material_name_2,
                "thickness_2_m": config_section.roof_thickness_2_m,
                "material_name_3": config_section.roof_material_name_3,
                "thickness_3_m": config_section.roof_thickness_3_m,
                "Service_Life": config_section.roof_lifetime,
            },
            "base": {
                "material_name_1": config_section.base_material_name_1,
                "thickness_1_m": config_section.base_thickness_1_m,
                "material_name_2": config_section.base_material_name_2,
                "thickness_2_m": config_section.base_thickness_2_m,
                "material_name_3": config_section.base_material_name_3,
                "thickness_3_m": config_section.base_thickness_3_m,
                "Service_Life": config_section.base_lifetime,
            },
        }

        # Material edits are allowed per-layer.
        # You may change only thickness (keep material) or only material (keep thickness);
        # unspecified values are kept from the current envelope DB entry.
        for component, fields in raw_components.items():
            for i in (1, 2, 3):
                mat = fields[f"material_name_{i}"]
                thk = fields[f"thickness_{i}_m"]

                if mat is not None and str(mat).strip() == "":
                    raise ValueError(
                        f"Invalid {component} material name for layer {i} in archetype '{archetype}': empty string."
                    )
                if thk is not None and thk < 0:
                    raise ValueError(
                        f"Invalid {component} thickness for layer {i} in archetype '{archetype}': {thk}. "
                        "Thickness must be >= 0."
                    )

        # Drop None-valued fields per component
        cleaned_components = {
            comp: {k: v for k, v in fields.items() if v is not None}
            for comp, fields in raw_components.items()
        }

        # Drop empty components
        cleaned_components = {c: f for c, f in cleaned_components.items() if f}

        if cleaned_components:
            modify_recipe[archetype] = cleaned_components

    return modify_recipe


def main(config: Configuration) -> None:
    year_of_state = config.district_events.year_of_event
    main_locator = InputLocator(config.scenario)
    if year_of_state is None:
        raise ValueError("Year of event must be specified in the configuration.")

    yml_path = main_locator.get_district_timeline_log_file()
    yml_snapshot = FileSnapshot()
    yml_snapshot.capture([yml_path])

    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(year_of_state)
    state_existed_before = os.path.exists(state_scenario_folder)

    existing_state_years = _list_existing_state_years(main_locator)
    future_years = [y for y in existing_state_years if y > year_of_state]

    file_snapshots_by_year: dict[int, FileSnapshot] = {}
    for snap_year in [year_of_state] + future_years:
        snap_folder = main_locator.get_state_in_time_scenario_folder(snap_year)
        if not os.path.exists(snap_folder):
            continue
        snap_locator = InputLocator(snap_folder)
        file_snapshots_by_year[snap_year] = snapshot_state_year_files(snap_locator)

    log_data = load_log_yaml(main_locator, allow_missing=True, allow_empty=True)

    try:
        if not state_existed_before:
            create_state_in_time_scenario(config, year_of_state, update_yaml=False)
            log_data.setdefault(
                year_of_state,
                {"created_at": str(pd.Timestamp.now()), "modifications": {}},
            )

        try:
            modify_recipe = create_modify_recipe(config)
        except ValueError as e:
            if "No archetypes specified" in str(e):
                modify_recipe = {}
            else:
                raise

        if modify_recipe:
            # delete_unexisting_buildings_from_event_scenario(config, year_of_state)
            modify_state_construction(
                config,
                year_of_state,
                modify_recipe,
                log_data=log_data,
            )
            _update_future_state_scenarios_after_year_event(
                config,
                year_of_state,
                log_data=log_data,
            )

        # Keep building-properties files derived from archetypes for all impacted years.
        for sync_year in [year_of_state] + future_years:
            sync_folder = main_locator.get_state_in_time_scenario_folder(sync_year)
            if not os.path.exists(sync_folder):
                continue
            _regenerate_building_properties_from_archetypes(InputLocator(sync_folder))

        save_log_yaml(main_locator, log_data)
        check_district_timeline_log_yaml_integrity(config)

        print(
            f"State-in-time scenario for year {year_of_state} created successfully. See folder: {state_scenario_folder}"
        )
    except Exception:
        # rollback state folder(s)
        for snap in file_snapshots_by_year.values():
            snap.restore()
        if not state_existed_before and os.path.exists(state_scenario_folder):
            shutil.rmtree(state_scenario_folder, ignore_errors=True)
        # rollback YAML log
        yml_snapshot.restore()
        raise

if __name__ == "__main__":
    main(Configuration())