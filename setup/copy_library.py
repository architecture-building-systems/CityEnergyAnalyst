"""
copy the esri104 library to the setup folder for inclusion when creating the setup.exe.
"""
import os
import shutil
import subprocess


def main(env):
    env_list = subprocess.check_output(['conda', 'env', 'list'])
    env_list = env_list.split('\n')
    env_line = next(line for line in env_list if line.startswith(env))
    env_parts = env_line.split(None, 1)
    _, env_dir = map(str.strip, env_parts)

    assert os.path.exists(env_dir)
    print 'found environment', env_dir

    env_lib = os.path.join(env_dir, 'Lib', 'site-packages')
    destination = os.path.join(os.path.dirname(__file__), 'site-packages')
    if os.path.exists(destination):
        print 'removing old setup/site-packages'
        shutil.rmtree(destination)
    print 'copying from env/site-packages', env_lib
    shutil.copytree(env_lib, destination)

    # delete some libraries already installed by ArcGIS
    libraries_to_delete = ['numpy', 'scipy', 'matplotlib', 'pandas', 'xlrd', 'xlwt', 'evernote', 'snakeviz']
    for library in libraries_to_delete:
        folder_to_delete = os.path.join(destination, library)
        if os.path.exists(folder_to_delete):
            print 'removing library', folder_to_delete
            shutil.rmtree(folder_to_delete)


if __name__ == '__main__':
    main('esri104')