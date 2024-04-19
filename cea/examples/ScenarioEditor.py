
import os
import shutil
import re

def create_folders_with_format(source_folder1, source_folder2, destination_path, R_range, year_range, sia_range, s_values,
                               total_folders,SubFolderName1,SubFolderName2):
    folders_created = 0
    for R in R_range:
        for year in year_range:
            if R in [1, 19]:
                sia_values = [380]
            elif R == 34:
                sia_values = [2024]
            else:
                sia_values = sia_range
            for sia in sia_values:
                for s in s_values:
                    folder_name = f"R{R}_{year}_SIA{sia}_{s}"
                    folder_path = os.path.join(destination_path, folder_name)
                    os.makedirs(folder_path, exist_ok=True)

                    # Copy all files from source folder to destination subfolder1
                    destination_subfolder1 = os.path.join(folder_path, "input", SubFolderName1)
                    os.makedirs(destination_subfolder1, exist_ok=True)
                    for filename in os.listdir(source_folder1):
                        source_file = os.path.join(source_folder1, filename)
                        destination_file = os.path.join(destination_subfolder1, filename)
                        shutil.copy(source_file, destination_file)

                        # Copy all files from source folder to destination subfolder2
                        destination_subfolder2 = os.path.join(folder_path, "input", SubFolderName2)
                        os.makedirs(destination_subfolder2, exist_ok=True)
                        for filename in os.listdir(source_folder2):
                            source_file = os.path.join(source_folder2, filename)
                            destination_file = os.path.join(destination_subfolder2, filename)
                            shutil.copy(source_file, destination_file)

                    folders_created += 1
                    if folders_created >= total_folders:
                        return


def copy_weather_files(source_folder, destination_path, year, total_folders,SubFolderName3):
    folders_created = 0
    for folder_name in os.listdir(destination_path):
        folder_path = os.path.join(destination_path, folder_name)
        if os.path.isdir(folder_path) and str(year) in folder_name:
            destination_subfolder = os.path.join(folder_path, "input", SubFolderName3)
            os.makedirs(destination_subfolder, exist_ok=True)
            for filename in os.listdir(source_folder):
                if str(year) in filename:
                    source_file = os.path.join(source_folder, filename)
                    destination_file = os.path.join(destination_subfolder, SubFolderName3)
                    shutil.copy(source_file, destination_file)
                    folders_created += 1
                    if folders_created >= total_folders:
                        return


# typology_R1_2040_S7

def copy_typology_files(source_folder, destination_path, R_range, year_range, s_values, sia_range, SubFolderName3):
    for filename in os.listdir(source_folder):
        if filename.startswith("typology_R") and filename.endswith(".dbf"):
            # Extract R, year, and s from filename
            match = re.match(r"typology_R(\d+)_(\d+)_(S\d+)\.dbf", filename)
            if match:
                R = int(match.group(1))
                year = int(match.group(2))
                s = match.group(3)
                print(f"Processing file: {filename}, R: {R}, year: {year}, s: {s}")
                print(f"R_range: {R_range}, year_range: {year_range}, s_values: {s_values}")
                if R in R_range and year in year_range and s in s_values:
                    folder_name = f"R{R}_{year}_SIA{sia_range}_{s}"
                    folder_path = os.path.join(destination_path, folder_name)
                    os.makedirs(folder_path, exist_ok=True)
                    destination_subfolder = os.path.join(folder_path, "input", SubFolderName3)
                    os.makedirs(destination_subfolder, exist_ok=True)
                    source_file = os.path.join(source_folder, filename)
                    destination_file = os.path.join(destination_subfolder, "typology.dbf")
                    shutil.copy(source_file, destination_file)
                else:
                    print("Conditions not matched. Skipping file...")
            else:
                print(f"Filename {filename} does not match the expected pattern.")
        else:
            print(f"Skipping file: {filename} as it does not meet the criteria.")


def copy_folders(source_folder, destination_path, conditioned_folder_name, year_range, sia_range, SubFolderName5):
    conditioned_folder_path = os.path.join(destination_path, conditioned_folder_name)
    os.makedirs(conditioned_folder_path, exist_ok=True)  # Create conditioned folder

    technology_subfolder = os.path.join(conditioned_folder_path, "input", SubFolderName5)
    os.makedirs(technology_subfolder, exist_ok=True)  # Create technology subfolder

    for folder_name in os.listdir(source_folder):
        folder_path = os.path.join(source_folder, folder_name)
        if os.path.isdir(folder_path):
            # Extract year and sia from folder name
            match = re.match(r".*_(\d+)_sia(\d+)_.*", folder_name)
            if match:
                year = int(match.group(1))
                sia = int(match.group(2))
                if year in year_range and sia in sia_range:
                    # Create target folder structure
                    target_folder_path = os.path.join(technology_subfolder, folder_name)
                    os.makedirs(target_folder_path, exist_ok=True)
                    # Copy contents of source folder to target folder
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            source_file_path = os.path.join(root, file)
                            destination_file_path = os.path.join(target_folder_path, file)
                            shutil.copy(source_file_path, destination_file_path)


# rates, years, standards inputs:
destination_path = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\ScenarioEditor"
R_range = [1, 19, 34]
year_range = [2040, 2060]
sia_range = [380, 2024]
s_values = ['S7', 'S8', 'S9', 'S10', 'S12']
total_folders = 30
conditioned_folder_name = "New_CH_2040_SIA380"

source_Geo = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\building-geometry"
source_Terrain= r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\topography"
source_Weather= r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\weather"
source_typology= r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\Typology_AllRates"
source_technology= r"C:\Users\mmeshkin\Documents\CEA_Dataset_pool"

SubFolderName1= "building-geometry"
SubFolderName2= "topography"
SubFolderName3 = "building-properties"
SubFolderName4 = "weather"
SubFolderName5 = "technology"


create_folders_with_format(source_Geo, source_Terrain, destination_path, R_range, year_range, sia_range, s_values, total_folders, SubFolderName1,SubFolderName2)

# copy_typology_files(source_typology, destination_path, R_range, year_range, s_values, 380, SubFolderName3) # Repeat this code for each standard seperatly

# copy_weather_files(source_Weather, destination_path, 2060, total_folders, SubFolderName4) # Repeat this code for each year seperatly

# copy_folders(source_technology, destination_path, conditioned_folder_name, year_range, sia_range, SubFolderName5)



