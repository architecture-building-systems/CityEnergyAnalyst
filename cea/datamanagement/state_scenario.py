import shutil
import os
from cea.config import Configuration
from cea.inputlocator import InputLocator
import pandas as pd
import geopandas as gpd
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup


def create_state_in_time_scenario(config: Configuration, year_of_state: int) -> None:
    """
    Create a new state-in-time scenario based on the current scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        locator (InputLocator): The input locator object for file paths.
        year_of_state (int): The year of the event scenario. If a building year is larger than this year, it will not be included in the event scenario.
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

def modify_state_construction(config: Configuration, year_of_state: int, modify_recipe: dict[str, dict[str, dict[str, float]]]) -> None:
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
                        "U": 0.2,
                        "GHG_kgCO2m2": 40,
                        "GHG_biogenic_kgCO2m2": -5,
                        "Service_Life": 40
                    }
                },
                "STANDARD2": {
                    "wall": {
                        "U": 0.25,
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
    state_locator = InputLocator(InputLocator(config.scenario).get_state_in_time_scenario_folder(year_of_state))
    archetype_df = pd.read_csv(state_locator.get_database_archetypes_construction_type(), index_col="const_type")
    envelope_lookup = EnvelopeLookup.from_locator(state_locator)
    for archetype in archetypes_to_modify:
        if archetype not in archetype_df.index:
            raise ValueError(f"Archetype '{archetype}' not found in construction type database.")
        for component, modifications in modify_recipe[archetype].items():
            code_current = archetype_df.at[archetype, f"type_{component}"]
            # create a new component code by "(capitalized component)_(archetype)_year_(event_year)"
            component_db = envelope_lookup._df_for(component)
            code_new = f"{component.capitalize()}_{archetype}_year_{year_of_state}"

            if code_new in component_db.index:
                code_new = shift_code_name_plus1(component_db, code_new)
            component_db.loc[code_new] = component_db.loc[code_current]

            for field, new_value in modifications.items():
                envelope_lookup.set_item_value(code_new, field, new_value)

            archetype_df.at[archetype, f"type_{component}"] = code_new

    # save both the modified archetype df and the envelope database
    archetype_df.reset_index(inplace=True)
    archetype_df.to_csv(state_locator.get_database_archetypes_construction_type(), index=False)
    envelope_lookup.envelope.save(state_locator)
    
def shift_code_name_plus1(db, code_prefix):
    n = db[db["code"].str.startswith(code_prefix)].shape[0]
    return code_prefix + f"_{n + 1}"