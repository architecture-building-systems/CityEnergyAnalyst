import os


def main():
    result_path = 'C:\\Users\\Zhongming\\Documents\\HCS_mk\\results\\HCS_base_LD'
    run_folders = os.listdir(result_path)
    for run_folder in run_folders:
        model_folder = [result_path, run_folder, 's_001\\plots\\icc\\models']
        path_to_model_folder = os.path.join('', *model_folder)
        files = os.listdir(path_to_model_folder)
        [os.remove(os.path.join(path_to_model_folder, file)) for file in files if '.jpg' in file]
    return


if __name__ == '__main__':
    main()