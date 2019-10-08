import shutil
import os

source_folder = "E:\\ipese_new\\osmose_mk\\results\\HCS_base_coil"
tech = "HCS_base_coil"
# source_folder = "E:\HCS_results_1006\WTP_OFF"
all_source_sub_folders = os.listdir(source_folder)


def move_and_create_directory(dir):
    if os.path.isdir(dir) == False:
        os.makedirs(dir)
    shutil.move(src, dir)


for folder in all_source_sub_folders:
    src = os.path.join(source_folder, folder)
    bui_use = 'HOT'
    if bui_use in folder:
        dir = "E:\\HCS_results_1006\\WTP_"+ bui_use + "\\" + folder.split(bui_use+'_')[1] + "\\" + tech
        move_and_create_directory(dir)