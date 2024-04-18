
import os
import shutil


def create_folders_with_format(source_folder, destination_path, R_range, year_range, sia_range, s_values,
                               total_folders,SubFolderName):
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
                    folder_name = f"R{R}_{year}_sia{sia}_{s}"
                    folder_path = os.path.join(destination_path, folder_name)
                    os.makedirs(folder_path, exist_ok=True)

                    # Copy all files from source folder to destination subfolder
                    destination_subfolder = os.path.join(folder_path, "input", SubFolderName)
                    os.makedirs(destination_subfolder, exist_ok=True)
                    for filename in os.listdir(source_folder):
                        source_file = os.path.join(source_folder, filename)
                        destination_file = os.path.join(destination_subfolder, filename)
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



# rates, years, standards inputs:
destination_path = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\ScenarioEditor"
R_range = [1, 19, 34]
year_range = [2040, 2060]
sia_range = [380, 2024]
s_values = ['S7', 'S8', 'S9', 'S10', 'S12']
total_folders = 30
source_Geo = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\building-geometry"
source_Terrain= r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\topography"
source_Weather=r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\weather"
SubFolderName1= "building-geometry"
SubFolderName2= "topography"
SubFolderName3 = "weather"

create_folders_with_format(source_Geo, destination_path, R_range, year_range, sia_range, s_values, total_folders, SubFolderName1)
create_folders_with_format(source_Terrain, destination_path, R_range, year_range, sia_range, s_values, total_folders, SubFolderName2)
copy_weather_files(source_Weather, destination_path, 2060, total_folders,SubFolderName3)