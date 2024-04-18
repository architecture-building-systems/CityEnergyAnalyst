
import os
import shutil



def create_folders_with_format(destination_path, R_range, year_range, sia_range, s_values, total_folders):
    folders_created = 0
    for R in R_range:
        for year in year_range:
            if R in [1, 19] :
                sia_values = [380]
            elif R == 34 :
                sia_values = [2024]
            else:
                sia_values = sia_range
            for sia in sia_values:
                for s in s_values:
                    folder_name = f"R{R}_{year}_sia{sia}_{s}"
                    folder_path = os.path.join(destination_path, folder_name)
                    os.makedirs(folder_path)
                    copy_files_to_folder(folder_path)
                    folders_created += 1
                    if folders_created >= total_folders:
                        return


def copy_files_to_folder(folder_path):
    source_Geo = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\building-geometry"
    source_Terrain = r"C:\Users\mmeshkin\Documents\Speed2Zero\Code_Input_Output\Python_Automated_inputs\inputs\topography"

    destination_Geo = os.path.join(folder_path, "inputs", "building-geometry")
    shutil.copy(source_Geo, destination_Geo)

    destination_Terrain = os.path.join(folder_path, "inputs", "topography")
    shutil.copy(source_Terrain, destination_Terrain)



# rates, years, standards inputs:
destination_path = r"C:\Users\mmeshkin\Documents\Speed2Zero\CEA_Automated_Senarios\All_inOne_18April"
R_range = [1, 19, 34]
year_range = [2040, 2060]
sia_range = [380, 2024]
s_values = ['S7', 'S8', 'S9', 'S10', 'S12']
total_folders = 30

create_folders_with_format(destination_path, R_range, year_range, sia_range, s_values,total_folders)





