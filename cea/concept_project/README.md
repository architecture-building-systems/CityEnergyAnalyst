# CONCEPT - Connecting District Energy and Power Systems in Future Singaporean New Towns

## Installation

Tested with Windows 10

1. Install CityEnergyAnalyst: http://city-energy-analyst.readthedocs.io/en/latest/getting-started.html#install-and-set-up
    * Use Anaconda Python 2.x version
    * Use CEA commit `63c6d029fe7f6f94bbda6002e96663901bd1d5fa`
    * In `CityEnergyAnalyst/environment.yml` change `libtiff=4.0.9=vc9_0` to `libtiff=4.0.9`
2. Install Gitkraken: https://www.gitkraken.com/download
3. Install KDiff: https://sourceforge.net/projects/kdiff3/
4. Open Gitkraken:
	1. Sign in
	2. Go to `File > Preferences > General`
	3. For `Merge Tool` select `KDiff` and for `Diff Tool` select `KDiff`
	4. Go to `File > Clone Repo > Bitbucket.org`
	5. Click `Connect to Bitbucket` and follow instructions in web browser
	6. Go back to `File > Clone Repo > Bitbucket.org`
	7. Select `TUMCREATE_ESTL > concept`, select a location at `Where to clone to` and click `Clone the repo!`
	8. Go to `File > Preferences > Git Flow`
	9. Click `Initialize Git Flow`
5. Open `Anaconda Prompt` from the start menu:
	1. Run `activate cea`
	2. Run `cd path_to_concept_directory` (replace `path_to_concept_directory` with your path)
	3. Run `pip install -e .`
	4. Run `cd external/building_model/`
	5. Run `pip install -e .`
    6. Fix Fiona/GDAL installation: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/1741
        1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/
        2. Download `Fiona‑1.8.4‑cp27‑cp27m‑win_amd64.whl` and `GDAL‑2.2.4‑cp27‑cp27m‑win_amd64.whl`
        3. Run `cd path_to_download_folder`
        4. Run `pip install Fiona-1.8.4-cp27-cp27m-win_amd64.whl --upgrade`
        5. Run `pip install GDAL-2.2.4-cp27-cp27m-win_amd64.whl --upgrade`
6. Open PyCharm:
	1. Click `Open` and point to location of the concept directory
	2. Go to `File > Settings > Project: concept > Project Interpreter`
	3. Click on the settings button (looks like a wheel) and click `Add Local...`
	4. Go to `System Interpreter` and click `...`
	5. Point to the location of your conda `cea` environment, usually at `C:\Users\your_username\AppData\Local\conda\conda\envs\cea\python.exe` (replace `your_username`)

## Development workflow

Note: Before committing/merging/pushing/pulling changes to/from the repository, close all programs to avoid access errors.

* Development is based on Python 2.7 for compatibility to CEA
* Development follows the CEA guidelines: http://city-energy-analyst.readthedocs.io/en/latest/developer-walk-through.html
* Development/versioning follows the GitFlow principle: https://datasift.github.io/gitflow/IntroducingGitFlow.html
* Dependencies are noted in `setup.py`
* Use relative paths and platform-independent path names
* Coding style follows these rules:
	* Variable/function names are in lowercase and underscore_case, hence all letters are lowercase and all words are seperated by underscores
	* Variable/function names should avoid abbreviations
