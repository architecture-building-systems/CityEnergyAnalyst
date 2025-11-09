import shutil
import os
from cea.config import Configuration
from cea.inputlocator import InputLocator
import pandas as pd
import geopandas as gpd
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup


def create_event_scenario(config: Configuration, event_year: int) -> None:
    """
    Create a new event scenario based on the current scenario and the provided event content.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        locator (InputLocator): The input locator object for file paths.
        event_year (int): The year of the event scenario. If a building year is larger than this year, it will not be included in the event scenario.
        event_content (dict): A dictionary containing the content of the event scenario.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_event_scenario_folder(event_year)
    input_folder_path = locator.get_input_folder()
    locator_event = InputLocator(event_scenario_folder)
    # copy all files from the input folder to the event scenario folder
    shutil.copytree(input_folder_path, locator_event.get_input_folder(), dirs_exist_ok=True) # make sure existing files are overwritten
    return None

def del_event_scenario(config: Configuration, event_year: int) -> None:
    """
    Delete an existing event scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        event_year (int): The year of the event scenario to be deleted.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_event_scenario_folder(event_year)
    shutil.rmtree(event_scenario_folder, ignore_errors=True)
    return None

def delete_unexisting_buildings_from_event_scenario(config: Configuration, event_year: int) -> list[str]:
    """
    Delete buildings from the event scenario that do not yet exist in the specified event year.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        event_year (int): The year of the event scenario. If a building year is larger than this year, it will be deleted from the event scenario.
    Returns:
        list[str]: A list of building names that were deleted from the event scenario.
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_event_scenario_folder(event_year)
    # ensure the event scenario folder exists
    locator_event = InputLocator(event_scenario_folder)
    if not os.path.exists(locator_event.get_zone_geometry()):
        raise FileNotFoundError(f"Event scenario folder for year {event_year} does not exist.")
    
    builings_to_delete = []
    buildings_gdf_current = gpd.read_file(locator.get_zone_geometry())
    for _, building in buildings_gdf_current.iterrows():
        building_year = building.get('year', None)

        if building_year is not None and building_year > event_year:
            builings_to_delete.append(building['name'])

    # delete all files related to the buildings to delete
    for building_name in builings_to_delete:
        delete_building_schedule(locator_event, building_name)

    # delete buildings from geometry file
    geometry_gdf_event, _, _ = shapefile_to_WSG_and_UTM(locator_event.get_zone_geometry())
    geometry_gdf_event.set_index('name', inplace=True)
    geometry_gdf_event = geometry_gdf_event.drop(builings_to_delete)
    verify_input_geometry_zone(geometry_gdf_event.reset_index())
    geometry_gdf_event.to_file(locator_event.get_zone_geometry())

    monthly_multiplier_df_path = (
        locator_event.get_building_weekly_schedules_monthly_multiplier_csv()
    )
    envelope_df_path = locator_event.get_building_architecture()
    hvac_df_path = locator_event.get_building_air_conditioning()
    indoor_comfort_df_path = locator_event.get_building_comfort()
    internal_loads_df_path = locator_event.get_building_internal()
    supply_df_path = locator_event.get_building_supply()
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

def delete_building_schedule(locator_event: InputLocator, building_name: str) -> None:
    """
    Delete the schedule file related to a specific building in the event scenario.
    This includes the following file:
    - building schedule file (`locator.get_building_occupancy_schedule(building_name)`)
    """
    schedule_file_path = locator_event.get_building_weekly_schedules(building_name)
    if os.path.exists(schedule_file_path):
        os.remove(schedule_file_path)
    return None

def modify_event_construction(config: Configuration, event_year: int, modify_recipe: dict[str, dict[str, dict[str, float]]]) -> None:
    """
    Modify the construction recipe of buildings in the event scenario based on the provided modification dictionary.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        event_year (int): The year of the event scenario.
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
    event_locator = InputLocator(InputLocator(config.scenario).get_event_scenario_folder(event_year))
    archetype_df = pd.read_csv(event_locator.get_database_archetypes_construction_type(), index_col="const_type")
    envelope_lookup = EnvelopeLookup.from_locator(event_locator)
    for archetype in archetypes_to_modify:
        if archetype not in archetype_df.index:
            raise ValueError(f"Archetype '{archetype}' not found in construction type database.")
        for component, modifications in modify_recipe[archetype].items():
            current_component_code = archetype_df.at[archetype, f"type_{component}"]
            # create a new component code by "(capitalized component)_(archetype)_year_(event_year)"
            component_db = envelope_lookup._df_for(component)
            new_component_code = f"{component.capitalize()}_{archetype}_year_{event_year}"

            if new_component_code in component_db.index:
                new_component_code = shift_code_name_plus1(component_db, new_component_code)
            component_db.loc[new_component_code] = component_db.loc[current_component_code]

            for field, new_value in modifications.items():
                envelope_lookup.set_item_value(new_component_code, field, new_value)

            archetype_df.at[archetype, f"type_{component}"] = new_component_code

    # save both the modified archetype df and the envelope database
    archetype_df.reset_index(inplace=True)
    archetype_df.to_csv(event_locator.get_database_archetypes_construction_type(), index=False)
    envelope_lookup.envelope.save(event_locator)
    
def shift_code_name_plus1(db, code_prefix):
    n = db[db["code"].str.startswith(code_prefix)].shape[0]
    return code_prefix + f"_{n + 1}"