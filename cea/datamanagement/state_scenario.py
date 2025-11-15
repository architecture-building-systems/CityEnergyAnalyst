import os
import shutil
from typing import Any

import geopandas as gpd
import pandas as pd
import yaml

from cea.config import Configuration
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM


def create_state_in_time_scenario(config: Configuration, year_of_state: int) -> None:
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
    locator = InputLocator(config.scenario)
    time_specific_scenario_folder = locator.get_state_in_time_scenario_folder(year_of_state)
    input_folder_path = locator.get_input_folder()
    state_locator = InputLocator(time_specific_scenario_folder)
    # copy all files from the input folder to the event scenario folder
    shutil.copytree(input_folder_path, state_locator.get_input_folder(), dirs_exist_ok=True) # make sure existing files are overwritten
    add_year_in_yaml(config, year_of_state)
    return None

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

def modify_state_construction(config: Configuration, year_of_state: int, modify_recipe: dict[str, dict[str, dict[str, float | int]]]) -> None:
    """
    Modify the construction recipe of buildings in the event scenario based on the provided modification dictionary.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario.
        modify_recipe (dict): A dictionary specifying the modifications to be made to the construction recipes.
            For example:
            ```
            {
                "STANDARD1": {
                    "wall": {
                        "U": 0.3,
                        "GHG_kgCO2m2": 50,
                        "GHG_biogenic_kgCO2m2": -10,
                        "Service_Life": 50
                    },
                    "roof": {
                        "U": 0.25,
                        "GHG_kgCO2m2": None, # keep current value
                        "GHG_biogenic_kgCO2m2": None, # keep current value
                        "Service_Life": None # keep current value
                    }
                },
                "STANDARD2": {
                    "wall": {
                        "U": None, # keep current value
                        "GHG_kgCO2m2": 45,
                        "GHG_biogenic_kgCO2m2": -8,
                        "Service_Life": 60
                    }
                }
            }
            ```
            Note that the outer dictionary keys are archetype names, the middle dictionary keys are component types. 
            These fields are sensitive to capitalization and must match exactly the envelope database column names.
    Returns:
        None
    """
    archetypes_to_modify = modify_recipe.keys()
    if not archetypes_to_modify:
        remove_state_in_time_scenario(config, year_of_state)
        raise ValueError(f"No archetypes specified for modification in the event scenario. The state-in-time scenario for year {year_of_state} has been deleted.")
    state_locator = InputLocator(InputLocator(config.scenario).get_state_in_time_scenario_folder(year_of_state))
    archetype_df = pd.read_csv(state_locator.get_database_archetypes_construction_type(), index_col="const_type")
    envelope_lookup = EnvelopeLookup.from_locator(state_locator)
    dbs_overall_modified = 0
    for archetype in archetypes_to_modify:
        if archetype not in archetype_df.index:
            raise ValueError(f"Archetype '{archetype}' not found in construction type database.")
        for component, modifications in modify_recipe[archetype].items():
            db_modified = 0
            code_current = archetype_df.at[archetype, f"type_{component}"]
            # create a new component code by "(capitalized component)_(archetype)_YEAR_(event_year)"
            component_db = envelope_lookup._df_for(component)
            code_new = f"{component.capitalize()}_{archetype}_YEAR_{year_of_state}"

            if code_new in component_db.index:
                code_new = shift_code_name_plus1(component_db, code_new)
            new_row = component_db.loc[code_current].copy()
            new_row.name = code_new

            for field, new_value in modifications.items():
                if new_value is not None:
                    component_field_name = envelope_lookup._col(component, field)
                    new_row[component_field_name] = new_value
                    db_modified += 1

            if db_modified:
                description_new = f"Modified {component} for archetype {archetype} in year {year_of_state}, based on {code_current}, fields modified: {', '.join(modifications.keys())}"
                new_row["description"] = description_new
                component_db.loc[new_row.name, :] = new_row
                archetype_df.at[archetype, f"type_{component}"] = code_new
                
            dbs_overall_modified += db_modified

    # save both the modified archetype df and the envelope database
    if not dbs_overall_modified:
        print(f"No modifications were made to the envelope database in year {year_of_state}.")
        return
    archetype_df.reset_index(inplace=True)
    archetype_df.to_csv(state_locator.get_database_archetypes_construction_type(), index=False)
    envelope_lookup.envelope.save(state_locator)
    log_modifications(config, year_of_state, modify_recipe)
    return None

def log_modifications(config: Configuration, year_of_state: int, modify_recipe: dict[str, dict[str, dict[str, float | int]]]) -> None:
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
    
def shift_code_name_plus1(db, code_prefix):
    n = db[db.index.str.startswith(code_prefix)].shape[0]
    return code_prefix + f"_{n + 1}"

def create_modify_recipe(config: Configuration) -> dict[str, dict[str, dict[str, float | int]]]:
    """
    Build modification recipe, pruning None-valued fields and empty components / archetypes.
    """
    config_section = config.district_events
    archetypes_to_modify = config_section.archetypes
    if not archetypes_to_modify:
        raise ValueError("No archetypes specified for modification in the event scenario.")

    modify_recipe: dict[str, dict[str, dict[str, float | int]]] = {}

    for archetype in archetypes_to_modify:
        raw_components = {
            "wall": {
                "U": config_section.wall_u_value,
                "GHG_kgCO2m2": config_section.wall_ghg_emission,
                "GHG_biogenic_kgCO2m2": config_section.wall_ghg_biogenic_emission,
                "Service_Life": config_section.wall_lifetime,
            },
            "roof": {
                "U": config_section.roof_u_value,
                "GHG_kgCO2m2": config_section.roof_ghg_emission,
                "GHG_biogenic_kgCO2m2": config_section.roof_ghg_biogenic_emission,
                "Service_Life": config_section.roof_lifetime,
            },
            "base": {
                "U": config_section.base_u_value,
                "GHG_kgCO2m2": config_section.base_ghg_emission,
                "GHG_biogenic_kgCO2m2": config_section.base_ghg_biogenic_emission,
                "Service_Life": config_section.base_lifetime,
            },
        }

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

def check_district_timeline_log_yaml_integrity(config: Configuration):
    """Basic check to see if all the existing state-in-time scenarios are logged in the district_timeline_log.yml.
    It only checks if the year in `state_{year}` also exists in the yaml log file.

    :param config: _description_
    :type config: Configuration
    """
    main_locator = InputLocator(config.scenario)
    dict_from_yaml = load_log_yaml(main_locator)
    existing_years_in_yml = set(dict_from_yaml.keys())
    # check all existing state-in-time folders
    existing_years_in_folders = set()
    district_timeline_folder = main_locator.get_district_timeline_states_folder()
    if os.path.exists(district_timeline_folder):
        for folder_name in os.listdir(district_timeline_folder):
            if folder_name.startswith("state_"):
                year_str = folder_name.replace("state_", "")
                try:
                    year = int(year_str)
                    existing_years_in_folders.add(year)
                except ValueError:
                    print(f"Warning: Invalid state-in-time folder name '{folder_name}' in district timeline folder.")

    # ideally the two sets should be equal
    years_only_in_folders = existing_years_in_folders - existing_years_in_yml
    years_only_in_yml = existing_years_in_yml - existing_years_in_folders
    if years_only_in_folders:
        raise ValueError(f"The following state-in-time years exist in folders but not in the district timeline log file: {sorted(years_only_in_folders)}")
    
    if years_only_in_yml:
        raise ValueError(f"The following state-in-time years exist in the district timeline log file but not in folders: {sorted(years_only_in_yml)}")

    return dict_from_yaml


def load_log_yaml(locator: InputLocator) -> dict[int, dict[str, Any]]:
    yml_path = locator.get_district_timeline_log_file()
    if not os.path.exists(yml_path):
        raise FileNotFoundError(
            f"District timeline log file '{yml_path}' does not exist."
        )
    with open(yml_path, "r") as f:
        existing_data_in_yml: dict[int, dict[str, Any]] = yaml.safe_load(f) or {}
    if not existing_data_in_yml:
        raise ValueError(f"District timeline log file '{yml_path}' is empty.")
    return existing_data_in_yml


def save_log_yaml(locator: InputLocator, log_data: dict[int, dict[str, Any]]) -> None:
    yml_path = locator.get_district_timeline_log_file()
    os.makedirs(os.path.dirname(yml_path), exist_ok=True)
    with open(yml_path, "w") as f:
        yaml.dump(log_data, f)


def add_year_in_yaml(config: Configuration, year_of_state: int) -> None:
    """Add a new year entry in the district timeline log yaml file if it does not exist.

    :param config: _description_
    :type config: Configuration
    :param year_of_state: _description_
    :type year_of_state: int
    """
    locator = InputLocator(config.scenario)
    log_data = load_log_yaml(locator)
    if year_of_state not in log_data:
        log_data[year_of_state] = {
            "created_at": str(pd.Timestamp.now()),
            "modifications": {},
        }
        save_log_yaml(locator, log_data)


def del_year_in_yaml(config: Configuration, year_of_state: int) -> None:
    """Delete a year entry in the district timeline log yaml file.

    :param config: _description_
    :type config: Configuration
    :param year_of_state: _description_
    :type year_of_state: int
    """
    locator = InputLocator(config.scenario)
    log_data = load_log_yaml(locator)
    if year_of_state in log_data:
        del log_data[year_of_state]
        save_log_yaml(locator, log_data)


def main(config: Configuration) -> None:
    year_of_state = config.district_events.year_of_event
    locator = InputLocator(config.scenario)
    if year_of_state is None:
        raise ValueError("Year of event must be specified in the configuration.")
    event_scenario_folder = locator.get_state_in_time_scenario_folder(year_of_state)
    if not os.path.exists(event_scenario_folder):
        create_state_in_time_scenario(config, year_of_state)
    modify_recipe = create_modify_recipe(config)
    # delete_unexisting_buildings_from_event_scenario(config, year_of_state)
    modify_state_construction(config, year_of_state, modify_recipe)
    print(f"State-in-time scenario for year {year_of_state} created successfully. See folder: {event_scenario_folder}")
    check_district_timeline_log_yaml_integrity(config)

if __name__ == "__main__":
    main(Configuration())