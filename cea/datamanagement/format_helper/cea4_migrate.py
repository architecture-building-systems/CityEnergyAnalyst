"""
Mirgate the format of the input data to CEA-4 format after verification.

"""
import csv
import os
import cea.config
import time
import pandas as pd
import geopandas as gpd



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.datamanagement.format_helper.cea4_migrate_db import rename_dict, add_occupied_bg, hs_bg_in_envelope
from cea.datamanagement.format_helper.cea4_verify import cea4_verify, verify_shp, \
    COLUMNS_ZONE_4, print_verification_results_4, path_to_input_file_without_db_4, CSV_BUILDING_PROPERTIES_3_CSV
from cea.datamanagement.format_helper.cea4_verify_db import check_directory_contains_csv
from cea.datamanagement.utils import migrate_void_deck_data
from cea.utilities.dbf import dbf_to_dataframe

COLUMNS_ZONE_3 = ['Name', 'floors_bg', 'floors_ag', 'height_bg', 'height_ag']
CSV_BUILDING_PROPERTIES_3 = ['air_conditioning', 'architecture', 'indoor_comfort', 'internal_loads', 'supply_systems', 'typology']

COLUMNS_TYPOLOGY_3 = ['Name', 'YEAR', 'STANDARD', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']
COLUMNS_SURROUNDINGS_3 = ['Name', 'height_ag', 'floors_ag']
COLUMNS_AIR_CONDITIONING_3 = ['Name',
                              'type_cs', 'type_hs', 'type_dhw', 'type_ctrl', 'type_vent',
                              'heat_starts', 'heat_ends', 'cool_starts', 'cool_ends']
COLUMNS_ARCHITECTURE_3 = ['Name',
                          'Hs_ag', 'Hs_bg', 'Ns', 'Es', 'wwr_north', 'wwr_west', 'wwr_east', 'wwr_south',
                          'type_cons', 'type_leak', 'type_floor', 'type_part', 'type_base', 'type_roof', 'type_wall',
                          'type_win', 'type_shade']
COLUMNS_INDOOR_COMFORT_3 = ['Name',
                            'Tcs_set_C', 'Ths_set_C', 'Tcs_setb_C', 'Ths_setb_C', 'Ve_lsp', 'RH_min_pc', 'RH_max_pc']
COLUMNS_INTERNAL_LOADS_3 = ['Name',
                            'Occ_m2p', 'Qs_Wp', 'X_ghp', 'Ea_Wm2', 'El_Wm2', 'Ed_Wm2', 'Ev_kWveh', 'Qcre_Wm2',
                            'Vww_ldp', 'Vw_ldp', 'Qhpro_Wm2', 'Qcpro_Wm2', 'Epro_Wm2']
COLUMNS_SUPPLY_SYSTEMS_3 = ['Name',
                            'type_cs', 'type_hs', 'type_dhw', 'type_el']
columns_mapping_dict_name = {'Name': 'name'}
columns_mapping_dict_typology = {'YEAR': 'year',
                                 'STANDARD': 'const_type',
                                 '1ST_USE': 'use_type1',
                                 '1ST_USE_R': 'use_type1r',
                                 '2ND_USE': 'use_type2',
                                 '2ND_USE_R': 'use_type2r',
                                 '3RD_USE': 'use_type3',
                                 '3RD_USE_R': 'use_type3r'
                                 }

columns_mapping_dict_envelope = {'Hs_ag': 'Hs',
                                 'Hs_bg': 'occupied_bg',
                                 'Ns': 'Ns',
                                 'Es': 'Es',
                                 'wwr_north': 'wwr_north',
                                 'wwr_south': 'wwr_south',
                                 'wwr_east': 'wwr_east',
                                 'wwr_west': 'wwr_west',
                                 'type_cons': 'type_mass',
                                 'type_leak': 'type_leak',
                                 'type_floor': 'type_floor',
                                 'type_part': 'type_part', 'type_roof': 'type_roof',
                                 'type_base': 'type_base',
                                 'type_wall': 'type_wall',
                                 'type_win': 'type_win',
                                 'type_shade': 'type_shade',
                                 }


columns_mapping_dict_hvac = {'type_cs': 'hvac_type_cs',
                             'type_hs': 'hvac_type_hs',
                             'type_dhw': 'hvac_type_dhw',
                             'type_ctrl': 'hvac_type_ctrl',
                             'type_vent': 'hvac_type_vent',
                             'cool_starts': 'hvac_cool_starts',
                             'cool_ends': 'hvac_cool_ends',
                             'heat_starts': 'hvac_heat_starts',
                             'heat_ends': 'hvac_heat_ends',
                             }

columns_mapping_dict_supply = {'type_cs': 'supply_type_cs',
                               'type_hs': 'supply_type_hs',
                               'type_dhw': 'supply_type_dhw',
                               'type_el': 'supply_type_el',
                               }

COLUMNS_ZONE_TYPOLOGY_3 = ['Name', 'STANDARD', 'YEAR', '1ST_USE', '1ST_USE_R', '2ND_USE', '2ND_USE_R', '3RD_USE', '3RD_USE_R']

## --------------------------------------------------------------------------------------------------------------------
## The paths to the input files for CEA-3
## --------------------------------------------------------------------------------------------------------------------

# The paths are relatively hardcoded for now without using the inputlocator script.
# This is because we want to iterate over all scenarios, which is currently not possible with the inputlocator script.
def path_to_input_file_without_db_3(scenario, item,building_name=None):

    if item == "zone":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "zone.shp")
    elif item == "surroundings":
        path_to_input_file = os.path.join(scenario, "inputs", "building-geometry", "surroundings.shp")
    elif item == "air_conditioning":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "air_conditioning.dbf")
    elif item == "air_conditioning_csv":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "air_conditioning.csv")
    elif item == "architecture":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "architecture.dbf")
    elif item == "architecture_csv":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "architecture.csv")
    elif item == "indoor_comfort":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "indoor_comfort.dbf")
    elif item == "internal_loads":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "internal_loads.dbf")
    elif item == "supply_systems":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply_systems.dbf")
    elif item == "supply_systems_csv":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "supply_systems.csv")
    elif item == "typology":
        path_to_input_file = os.path.join(scenario, "inputs", "building-properties", "typology.dbf")
    elif item == 'streets':
        path_to_input_file = os.path.join(scenario, "inputs", "networks", "streets.shp")
    elif item == 'terrain':
        path_to_input_file = os.path.join(scenario, "inputs", "topography", "terrain.tif")
    elif item == 'weather':
        path_to_input_file = os.path.join(scenario, "inputs", "weather", "weather.epw")
    elif item == 'schedules':
        if building_name is None:
            path_to_input_file = os.path.join(scenario, "inputs", "building-properties", 'schedules')
        else:
            path_to_input_file = os.path.join(scenario, "inputs", "building-properties", 'schedules', "{building}.csv".format(building=building_name))
    else:
        raise ValueError(f"Unknown item {item}")

    return path_to_input_file


## --------------------------------------------------------------------------------------------------------------------
## Helper functions
## --------------------------------------------------------------------------------------------------------------------


def verify_name_duplicates_3(scenario, item):
    """
    Verify if there are duplicate names in the 'name' column of a .csv or .shp file.

    Parameters:
        file_path (str): Path to the input file (either .csv or .shp).

    Returns:
        list: A list of duplicate names, or an empty list if no duplicates are found.
    """
    # Construct the CSV file path
    file_path = path_to_input_file_without_db_3(scenario, item)

    # Check file type and load as a DataFrame
    if file_path.endswith('.dbf'):
        try:
            df = dbf_to_dataframe(file_path)
        except Exception as e:
            raise ValueError(f"Error reading DBF file: {e}")
    elif file_path.endswith('.shp'):
        try:
            df = gpd.read_file(file_path)
        except Exception as e:
            raise ValueError(f"Error reading shapefile: {e}")
    elif file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")
    else:
        raise ValueError("Unsupported file type. Please provide a .csv or .shp file.")

    # Find duplicate names
    if 'Name' in df.columns:
        list_names_duplicated = df['Name'][df['Name'].duplicated()].tolist()
    elif 'name' in df.columns:
        list_names_duplicated = df['name'][df['name'].duplicated()].tolist()
    else:
        raise ValueError(f"neither 'Name' nor 'name' column found in {file_path}")

    return list_names_duplicated

def verify_dbf_3(scenario, item, required_columns):
    """
    Verify if a DBF file contains all required columns.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        item (str): Identifier for the CSV file.
        required_columns (list): List of column names to verify.

    Returns:
        A list of missing columns, or an empty list if all columns are present.
    """
    # Construct the CSV file path
    dbf_path = path_to_input_file_without_db_3(scenario, item)

    # Check if the CSV file exists
    if not os.path.isfile(dbf_path):
        raise FileNotFoundError(f".dbf file not found: {dbf_path}")

    # Load the CSV file
    try:
        df = dbf_to_dataframe(dbf_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Get the column names from the CSV file
    dbf_columns = df.columns.tolist()

    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in dbf_columns]

    return missing_columns


def verify_csv_3(scenario, item, required_columns):
    """
    Verify if a DBF file contains all required columns.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        item (str): Identifier for the CSV file.
        required_columns (list): List of column names to verify.

    Returns:
        A list of missing columns, or an empty list if all columns are present.
    """
    # Construct the CSV file path
    csv_path = path_to_input_file_without_db_3(scenario, item)

    # Check if the CSV file exists
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f".csv file not found: {csv_path}")

    # Load the CSV file
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Get the column names from the CSV file
    dbf_columns = df.columns.tolist()

    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in dbf_columns]

    return missing_columns



def replace_shapefile_dbf(scenario, item, new_dataframe, list_attributes_3):
    """
    Replace the DBF file of a shapefile with the contents of a new DataFrame,
    ensuring matching of `['Name']` in the shapefile and `['name']` in the new DataFrame.

    :param shapefile_path: Path to the shapefile (without file extension).
    :param new_dataframe: pandas DataFrame with the new data to replace the DBF file.
    """
    # Load the original shapefile
    shapefile_path = path_to_input_file_without_db_3(scenario, item)
    gdf = gpd.read_file(shapefile_path)

    # Convert the DataFrame to a GeoDataFrame
    new_gdf = gpd.GeoDataFrame(new_dataframe, geometry=gdf['geometry'], crs=gdf.crs)  # Replace CRS with your specific CRS

    # Save the updated shapefile
    new_gdf.to_file(shapefile_path, driver="ESRI Shapefile")


def verify_file_exists_3(scenario, items):
    """
    Verify if the files in the provided list exist for a given scenario.

    Parameters:
        scenario (str): Path or identifier for the scenario.
        items (list): List of file identifiers to check.

    Returns:
        list: A list of missing file identifiers, or an empty list if all files exist.
    """
    list_missing_files = []
    for file in items:
        path = path_to_input_file_without_db_3(scenario, file)
        if not os.path.isfile(path):
            list_missing_files.append(file)
    return list_missing_files


def migrate_dbf_to_csv(scenario, item, required_columns, columns_mapping_dict=None, verbose=False):
    """
    Migrate a DBF file to CSV format with column renaming.

    Args:
        scenario: The scenario path
        item: The item name (e.g., 'air_conditioning')
        required_columns: List of required columns
    """
    list_missing_columns = verify_dbf_3(scenario, item, required_columns)
    if list_missing_columns:
        print(f'! Ensure column(s) are present in the {item}.dbf: {list_missing_columns}')
    else:
        if 'Name' not in list_missing_columns:
            list_names_duplicated = verify_name_duplicates_3(scenario, item)
            if list_names_duplicated:
                print(f'! Ensure name(s) are unique in {item}.dbf: {list_names_duplicated} is duplicated.')
            else:
                df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, item))
                df.rename(columns=columns_mapping_dict_name, inplace=True)
                if columns_mapping_dict:
                    df.rename(columns=columns_mapping_dict, inplace=True)
                # if 'Hs_bg' in df.columns:
                if 'occupied_bg' in df.columns:
                    if df['occupied_bg'].dtype != 'bool':
                        df = add_occupied_bg(scenario, df)
                if 'void_deck' in df.columns:
                    df.drop(columns='void_deck', inplace=True)
                df.to_csv(path_to_input_file_without_db_4(scenario, item), index=False)
                os.remove(path_to_input_file_without_db_3(scenario, item))
                if verbose:
                    print(f'- {item}.dbf has been migrated from CEA-3 to CEA-4 format.')


def update_header(scenario, item, columns_mapping_dict, list_missing_columns):
    """
    Update the column headers of a DBF file, rename columns based on mapping,
    and return the missing columns after renaming.

    Parameters:
    - scenario (str): Path to the scenario.
    - item (str): Identifier for the file.
    - columns_mapping_dict (dict): Dictionary mapping old column names to new column names.
    - list_missing_columns (list): List of expected columns that should be present.

    Returns:
    - list: Updated list of missing columns.
    """
    try:
        # Read the DBF file into a DataFrame
        df = pd.read_csv(path_to_input_file_without_db_4(scenario, item))

        if df.empty:
            print(f"Warning: {item} is empty. No changes made.")
            return list_missing_columns  # Return original missing columns

        # Rename columns
        df.rename(columns=columns_mapping_dict, inplace=True)

        # Save the updated DataFrame back to CSV
        df.to_csv(path_to_input_file_without_db_4(scenario, item), index=False)

        # Get the new list of headers
        list_header = df.columns.tolist()

        # Find the columns still missing after renaming
        list_missing_new = sorted(set(list_missing_columns) - set(list_header))

        return list_missing_new

    except Exception as e:
        print(f"Error updating header for {item}: {e}")
        return list_missing_columns  # Return original missing columns in case of error


def modify_csv_files(scenario, verbose=False):
    """
    Process .csv files from one directory to another.
    Also, compile specific rows from .csv files into a combined DataFrame.

    Parameters:
    - scenario: The scenario path.

    Returns:
    - None
    """
    # Paths
    schedules_directory_3 = path_to_input_file_without_db_3(scenario, 'schedules')
    schedules_directory_4 = path_to_input_file_without_db_4(scenario, 'schedules')
    compiled_rows = []

    if not check_directory_contains_csv(schedules_directory_3):
        return

    # Ensure the target directory exists
    os.makedirs(schedules_directory_4, exist_ok=True)

    # Iterate through files in the source directory
    for root, _, files in os.walk(schedules_directory_3):
        for file in files:
            old_file_path = os.path.join(root, file)
            new_file_path = os.path.join(schedules_directory_4, file)

            # Handle .csv files: Process and save
            if file.endswith('.csv') and file != 'MONTHLY_MULTIPLIERS.csv':
                try:
                    # Read the CSV file
                    building_name = os.path.splitext(file)[0]
                    with open(old_file_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)

                    # Extract the second row for compilation: monthly multiplier
                    headers_multiplier = ['name',
                                          'Jan', 'Feb', 'Mar',
                                          'Apr', 'May', 'Jun',
                                          'Jul', 'Aug', 'Sep',
                                          'Oct', 'Nov', 'Dec']
                    second_row = {headers_multiplier[i]: value for i, value in enumerate(rows[1])}
                    second_row['name'] = building_name
                    compiled_rows.append(second_row)

                    # Clean and process the remaining data
                    # Extract rows 3 to 74
                    other_rows = rows[3:75]  # Remember Python indexing starts at 0
                    headers_schedules = rows[2]
                    schedules_df = pd.DataFrame(other_rows, columns=headers_schedules)
                    schedules_df.rename(columns=rename_dict, inplace=True)
                    for col in schedules_df.columns:
                        try:
                            schedules_df[col] = pd.to_numeric(schedules_df[col])
                        except (ValueError, TypeError):
                            pass  # Keep original values if conversion fails

                    # Drop the original 'day' and 'hour' columns
                    if 'day' in schedules_df.columns:
                        schedules_df.drop(columns=['day'], inplace=True)
                    if 'hour' in schedules_df.columns:
                        schedules_df.drop(columns=['hour'], inplace=True)

                    # Create the 'hour' column
                    hour_values = (
                        ['Weekday_{:02d}'.format(i) for i in range(24)] +
                        ['Saturday_{:02d}'.format(i) for i in range(24)] +
                        ['Sunday_{:02d}'.format(i) for i in range(24)]
                    )

                    # Add the new 'hour' column as a Series
                    schedules_df.insert(0, 'hour', pd.Series(hour_values, index=schedules_df.index[:72]))

                    # Save the cleaned data
                    schedules_df.to_csv(new_file_path, index=False)
                    if verbose:
                        print(f"Saved {building_name} to {new_file_path}")
                except Exception as e:
                    print(f"Error processing {file}: {e}")

    # Create and save the compiled DataFrame
    if compiled_rows:
        compiled_multiplier_df = pd.DataFrame(compiled_rows)
        compiled_multiplier_path = path_to_input_file_without_db_4(scenario, 'schedules', 'MONTHLY_MULTIPLIERS')
        compiled_multiplier_df.to_csv(compiled_multiplier_path, index=False)
        if verbose:
            print(f"Saved MONTHLY_MULTIPLIER to: {compiled_multiplier_path}")


def csv_to_csv(scenario, item_csv, required_columns_3, columns_mapping_dict, verbose=False):
    item = item_csv[:-4] if len(item_csv) >= 4 else item_csv
    list_missing_columns = verify_csv_3(scenario, item_csv, required_columns_3)
    if 'Name' not in list_missing_columns or 'name' not in list_missing_columns:
        list_names_duplicated = verify_name_duplicates_3(scenario, item_csv)
        if list_names_duplicated:
            if verbose:
                print(f'! Ensure name(s) are unique in {item_csv}.dbf: {list_names_duplicated} is duplicated.')

        df = pd.read_csv(path_to_input_file_without_db_3(scenario, item_csv))
        df.rename(columns=columns_mapping_dict_name, inplace=True)
        if columns_mapping_dict:
            df.rename(columns=columns_mapping_dict, inplace=True)
        df.to_csv(path_to_input_file_without_db_4(scenario, item), index=False)
        os.remove(path_to_input_file_without_db_3(scenario, item_csv))
        if verbose:
            print(f'- {item_csv}.dbf has been migrated from CEA-3 to CEA-4 format.')


## --------------------------------------------------------------------------------------------------------------------
## Migrate to CEA-4 format from CEA-3 format
## --------------------------------------------------------------------------------------------------------------------

def migrate_cea3_to_cea4(scenario, verbose=False):

    #0. verify if everything is already in the correct format for CEA-4
    dict_missing = cea4_verify(scenario)
    if all(not value for value in dict_missing.values()):
        pass
    elif hs_bg_in_envelope(scenario):
        envelope = add_occupied_bg(
            scenario=scenario,
            envelope=pd.read_csv(os.path.join(scenario, "inputs", "building-properties", "envelope.csv")).rename(
                columns={'Hs_ag': 'Hs', 'Hs_bg': 'occupied_bg'}))
        envelope.to_csv(os.path.join(scenario, "inputs", "building-properties", "envelope.csv"), index=False)
    else:
        # Verify missing files for CEA-3 and CEA-4 formats
        list_missing_files_shp_building_geometry_4 = dict_missing.get('building-geometry')
        list_missing_files_dbf_building_properties_3 = verify_file_exists_3(scenario, CSV_BUILDING_PROPERTIES_3)
        list_missing_files_dbf_building_properties_3_csv = verify_file_exists_3(scenario, CSV_BUILDING_PROPERTIES_3_CSV)
        list_missing_files_csv_building_properties_4 = dict_missing.get('building-properties')
        list_missing_files_csv_building_properties_schedules_4 = dict_missing.get('schedules')

        # Verify missing attributes/columns for CEA-4 format
        list_missing_attributes_zone_4 = dict_missing.get('zone')
        list_missing_attributes_surroundings_4 = dict_missing.get('surroundings')
        list_missing_columns_air_conditioning_4 = dict_missing.get('hvac')
        list_missing_columns_architecture_4 = dict_missing.get('envelope')
        list_missing_columns_indoor_comfort_4 = dict_missing.get('indoor_comfort')
        list_missing_columns_internal_loads_4 = dict_missing.get('internal_loads')
        list_missing_columns_supply_systems_4 = dict_missing.get('supply')
        list_missing_columns_building_properties_schedules_buildings_4 = dict_missing.get('buildings')
        list_missing_columns_building_properties_schedules_monthly_multipliers_4 = dict_missing.get('monthly_multipliers')

        #1. about zone.shp and surroundings.shp
        if 'zone' not in list_missing_files_shp_building_geometry_4:
            list_missing_attributes_zone_3 = verify_shp(scenario, 'zone', COLUMNS_ZONE_3)
            if not list_missing_attributes_zone_3 and list_missing_attributes_zone_4:
                # print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp follows the CEA-3 format.')
                zone_df_3 = gpd.read_file(path_to_input_file_without_db_3(scenario, 'zone'))
                zone_df_3.rename(columns=columns_mapping_dict_name, inplace=True)
                if 'typology' not in list_missing_files_dbf_building_properties_3:
                    list_missing_attributes_typology_3 = verify_dbf_3(scenario, 'typology', COLUMNS_TYPOLOGY_3)
                    if not list_missing_attributes_typology_3 and list_missing_attributes_zone_4:
                        # print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'typology.shp follows the CEA-3 format.')
                        typology_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'typology'))
                        typology_df = typology_df[COLUMNS_ZONE_TYPOLOGY_3]
                        typology_df.rename(columns=columns_mapping_dict_typology, inplace=True)
                        zone_df_4 = pd.merge(zone_df_3, typology_df, left_on=['name'], right_on=["Name"], how='left')
                        zone_df_4.drop(columns=['Name'], inplace=True)

                        # bring void_deck from architecture.dbf to zone.shp
                        if 'void_deck' not in list_missing_columns_architecture_4:
                            void_deck_df = dbf_to_dataframe(path_to_input_file_without_db_3(scenario, 'architecture'))[['Name', 'void_deck']]
                            zone_df_4 = pd.merge(zone_df_4, void_deck_df, left_on=['name'], right_on=["Name"], how='left')
                        else:
                            zone_df_4['void_deck'] = 0  # if void deck already does not exist in the architecture/envelope file, create a new column in the zone.shp with zeros

                        zone_df_4 = zone_df_4[COLUMNS_ZONE_4]
                        replace_shapefile_dbf(scenario, 'zone', zone_df_4, COLUMNS_ZONE_3)
                        if verbose:
                            print('- zone.shp and typology.dbf have been merged and migrated to CEA-4 format.')
                    else:
                        raise ValueError('! typology.dbf exists but does not follow the CEA-3 format. CEA cannot proceed with the data migration. '
                                         'Check the following column(s) for CEA-3 format: {list_missing_attributes_typology_3}.'.format(list_missing_attributes_typology_3=list_missing_attributes_typology_3)
                                         )
                else:
                    print("! CEA is unable to produce a zone.shp compatible to CEA-4 format. To enable the migration, ensure typology.dbf (CEA-3 format) is present in building-properties folder.")

            elif list_missing_attributes_zone_3 and not list_missing_attributes_zone_4:
                pass
                # print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'zone.shp already follows the CEA-4 format.')
            else:
                if list_missing_attributes_zone_4[0] == 'void_deck' and len(list_missing_attributes_zone_4) == 1:
                    config = cea.config.Configuration()
                    locator = cea.inputlocator.InputLocator(config.scenario)
                    migrate_void_deck_data(locator)
                else:
                    raise ValueError('! zone.shp exists but follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration. Check the following column(s) for CEA-3 format: {list_missing_attributes_zone_3}.'.format(list_missing_attributes_zone_3=list_missing_attributes_zone_3), 'Check the following column(s) for CEA-4 format: {list_missing_attributes_zone_4}.'.format(list_missing_attributes_zone_4=list_missing_attributes_zone_4)
                                 )
        else:
            print("! Ensure zone.shp (CEA-3 format) is present in building-geometry folder.")

        if 'surroundings' not in list_missing_files_shp_building_geometry_4:
            list_missing_attributes_surroundings_3 = verify_shp(scenario, 'surroundings', COLUMNS_SURROUNDINGS_3)
            if not list_missing_attributes_surroundings_3 and list_missing_attributes_surroundings_4:
                # print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp follows the CEA-3 format.')
                surroundings_df = gpd.read_file(path_to_input_file_without_db_3(scenario, 'surroundings'))
                surroundings_df.rename(columns=columns_mapping_dict_name, inplace=True)
                replace_shapefile_dbf(scenario, 'surroundings', surroundings_df, COLUMNS_SURROUNDINGS_3)
                if verbose:
                    print('- surroundings.shp has been migrated from CEA-3 to CEA-4 format.')

            elif list_missing_attributes_surroundings_3 and not list_missing_attributes_surroundings_4:
                pass
                # print('For Scenario: {scenario}, '.format(scenario=scenario_name), 'surroundings.shp already follows the CEA-4 format.')
            else:
                if list_missing_attributes_zone_4[0] == 'void_deck' and len(list_missing_attributes_zone_4) == 1:
                    config = cea.config.Configuration()
                    locator = cea.inputlocator.InputLocator(config.scenario)
                    migrate_void_deck_data(locator)
                else:
                    raise ValueError('surroundings.shp exists but follows neither the CEA-3 nor CEA-4 format. CEA cannot proceed with the data migration. Check the following column(s) for CEA-3 format: {list_missing_attributes_surroundings_3}.'.format(list_missing_attributes_surroundings_3=list_missing_attributes_surroundings_3), 'Check the following column(s) for CEA-4 format: {list_missing_attributes_surroundings_4}.'.format(list_missing_attributes_surroundings_4=list_missing_attributes_surroundings_4)
                                 )
        else:
            print('! (optional) Run Surroundings Helper to generate surroundings.shp after the data migration.')

        #2. about the .dbf files in the building-properties folder to be migrated to .csv files
        if 'hvac' in list_missing_files_csv_building_properties_4 and not list_missing_columns_air_conditioning_4:
            if 'air_conditioning' not in list_missing_files_dbf_building_properties_3:
                migrate_dbf_to_csv(scenario, 'air_conditioning', COLUMNS_AIR_CONDITIONING_3, columns_mapping_dict_hvac, verbose=verbose)
            elif 'air_conditioning_csv' not in list_missing_files_dbf_building_properties_3_csv:
                csv_to_csv(scenario, 'air_conditioning_csv', COLUMNS_AIR_CONDITIONING_3, columns_mapping_dict_hvac, verbose=verbose)
            else:
                print("! Ensure either air_conditioning.dbf (CEA-3 naming) or hvac.csv (CEA-4 naming) is present in building-properties folder. Run Archetypes-Helper to generate hvac.csv.")
        elif 'air_conditioning' not in list_missing_files_csv_building_properties_4 and list_missing_columns_air_conditioning_4:
            list_missing_columns_air_conditioning_4_updated = update_header(scenario,'air_conditioning', columns_mapping_dict_hvac, list_missing_columns_air_conditioning_4)
            if verbose and list_missing_columns_air_conditioning_4_updated:
                print('! Ensure column(s) are present in air_conditioning.dbf (CEA-3 naming) or hvac.csv (CEA-4 naming): {list_missing_columns_air_conditioning_4}.'.format(list_missing_columns_air_conditioning_4=list_missing_columns_air_conditioning_4))
        else:
            pass

        if 'envelope' in list_missing_files_csv_building_properties_4 and not list_missing_columns_architecture_4:
            if 'architecture' not in list_missing_files_dbf_building_properties_3:
                migrate_dbf_to_csv(scenario, 'architecture', COLUMNS_ARCHITECTURE_3, columns_mapping_dict_envelope, verbose=verbose)
            elif 'architecture_csv' not in list_missing_files_dbf_building_properties_3_csv:
                csv_to_csv(scenario, 'architecture_csv', COLUMNS_ARCHITECTURE_3, columns_mapping_dict_envelope, verbose=verbose)
            else:
                print("! Ensure either architecture.dbf (CEA-3 naming) or envelope.csv (CEA-4 naming) is present in building-properties folder. Run Archetypes-Helper to generate envelope.csv.")
        elif 'architecture' not in list_missing_files_csv_building_properties_4 and list_missing_columns_architecture_4:
            list_missing_columns_architecture_4_updated = update_header(scenario,'architecture', columns_mapping_dict_envelope, list_missing_columns_architecture_4)
            if verbose and list_missing_columns_architecture_4_updated:
                print('! Ensure column(s) are present in  architecture.dbf (CEA-3 naming) or envelope.csv (CEA-4 naming): {list_missing_columns_architecture_4}.'.format(list_missing_columns_architecture_4=list_missing_columns_architecture_4))
        else:
            pass

        if 'indoor_comfort' in list_missing_files_csv_building_properties_4 and not list_missing_columns_indoor_comfort_4:
            if 'indoor_comfort' not in list_missing_files_dbf_building_properties_3:
                migrate_dbf_to_csv(scenario, 'indoor_comfort', COLUMNS_INDOOR_COMFORT_3, verbose=verbose)
            else:
                print("! Ensure either indoor_comfort.dbf or indoor_comfort.csv is present in building-properties folder. Run Archetypes-Helper to generate indoor_comfort.csv.")
        elif 'indoor_comfort' not in list_missing_files_csv_building_properties_4 and list_missing_columns_indoor_comfort_4:
            if verbose:
                print('! Ensure column(s) are present in indoor_comfort.csv: {list_missing_columns_indoor_comfort_4}.'.format(list_missing_columns_indoor_comfort_4=list_missing_columns_indoor_comfort_4))
        else:
            pass

        if 'internal_loads' in list_missing_files_csv_building_properties_4 and not list_missing_columns_internal_loads_4:
            if 'internal_loads' not in list_missing_files_dbf_building_properties_3:
                migrate_dbf_to_csv(scenario, 'internal_loads', COLUMNS_INTERNAL_LOADS_3, verbose=verbose)
            else:
                print("! Ensure either internal_loads.dbf or internal_loads.csv is present in building-properties folder. Run Archetypes-Helper to generate internal_loads.csv.")
        elif 'internal_loads' not in list_missing_files_csv_building_properties_4 and list_missing_columns_internal_loads_4:
            if verbose:
                print('! Ensure column(s) are present in internal_loads.csv: {list_missing_columns_internal_loads_4}.'.format(list_missing_columns_internal_loads_4=list_missing_columns_internal_loads_4))
        else:
            pass

        if 'supply' in list_missing_files_csv_building_properties_4 and not list_missing_columns_supply_systems_4:
            if 'supply_systems' not in list_missing_files_dbf_building_properties_3:
                migrate_dbf_to_csv(scenario, 'supply_systems', COLUMNS_SUPPLY_SYSTEMS_3, columns_mapping_dict_supply, verbose=verbose)
            elif 'supply_systems_csv' not in list_missing_files_dbf_building_properties_3_csv:
                csv_to_csv(scenario, 'supply_systems_csv', COLUMNS_SUPPLY_SYSTEMS_3, columns_mapping_dict_supply, verbose=verbose)
            else:
                print("! Ensure either supply_systems.dbf (CEA-3 naming) or supply.csv (CEA-4 naming) is present in building-properties folder. Run Archetypes-Helper to generate supply.csv.")
        elif 'supply_systems' not in list_missing_files_csv_building_properties_4 and list_missing_columns_supply_systems_4:
            list_missing_columns_supply_systems_4_updated = update_header(scenario,'supply_systems', columns_mapping_dict_supply, list_missing_columns_supply_systems_4)
            if verbose and list_missing_columns_supply_systems_4_updated:
                print('! Ensure column(s) are present in supply_systems.dbf (CEA-3 naming) or supply.csv (CEA-4 naming): {list_missing_columns_supply_system_4}.'.format(list_missing_columns_supply_system_4=list_missing_columns_supply_systems_4))
        else:
            pass

        if 'typology' not in list_missing_files_dbf_building_properties_3:
            typology_path = path_to_input_file_without_db_3(scenario, 'typology')
            if os.path.exists(typology_path):
                os.remove(typology_path)
                if verbose:
                    print('- typology.dbf has been removed as it is no longer needed by CEA-4.')

        #3. about .csv files under the "inputs/building-properties/schedules" folder
        if list_missing_files_csv_building_properties_schedules_4:
            if list_missing_files_csv_building_properties_schedules_4 == ['MONTHLY_MULTIPLIERS']:
                modify_csv_files(scenario, verbose=False)
            else:
                print('! Ensure .csv file(s) are present building-properties/schedules folder: {building}. Run Archetypes Mapper to generate the missing .csv files.'.format(building=', '.join(map(str, list_missing_files_csv_building_properties_schedules_4))))
        else:
            if list_missing_columns_building_properties_schedules_buildings_4:
                print('! Ensure column(s) are present in the (schedule) .csv file of each building in building-properties/schedules folder: {columns}. Run Archetypes Mapper to generate the missing columns.'.format(columns=', '.join(map(str, list_missing_columns_building_properties_schedules_buildings_4))))
            elif list_missing_columns_building_properties_schedules_monthly_multipliers_4:
                print('! Ensure column(s) are present in MONTHLY_MULTIPLIERS.csv in building-properties/schedules folder: {columns}. Run Archetypes Mapper to generate the missing columns.'.format(columns=', '.join(map(str, list_missing_columns_building_properties_schedules_monthly_multipliers_4))))
        # # Print: End
        # print('-' * 49)

## --------------------------------------------------------------------------------------------------------------------
## Main function
## --------------------------------------------------------------------------------------------------------------------


def main(config: cea.config.Configuration):
    # Start the timer
    t0 = time.perf_counter()
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    scenario = config.scenario
    scenario_name = os.path.basename(scenario)

    # Print: Start
    div_len = 37 - len(scenario_name)
    print('-' * 39)
    print("-" * 1 + ' Scenario: {scenario} '.format(scenario=scenario_name) + "-" * div_len)

    # Execute the verification
    migrate_cea3_to_cea4(scenario)

    # Execute the verification again
    dict_missing = cea4_verify(scenario)

    # Print the verification results
    print_verification_results_4(scenario_name, dict_missing)

    # Print: End
    # print("-" * 1 + ' Scenario: {scenario} - end '.format(scenario=scenario_name) + "-" * 50)
    print('+' * 104)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of data migration from CEA-3 to CEA-4 is now completed - time elapsed: %.2f seconds' % time_elapsed)

if __name__ == '__main__':
    main(cea.config.Configuration())
