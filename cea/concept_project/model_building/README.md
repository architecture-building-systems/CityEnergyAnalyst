# Building Model

## Getting started

Tested with Windows 10

1. Install Anaconda: https://www.anaconda.com/download/ (Python 3.x version)
2. Install Gitkraken: https://www.gitkraken.com/download
3. (Optional) Install KDiff: https://sourceforge.net/projects/kdiff3/
4. Open Gitkraken:
	1. Sign in
	2. Go to `File > Preferences > General`
	3. For `Merge Tool` select `KDiff` and for `Diff Tool` select `KDiff`
	4. Go to `File > Clone Repo > Bitbucket.org`
	5. Click `Connect to Bitbucket` and follow instructions in web browser
	6. Go back to `File > Clone Repo > Bitbucket.org`
	7. Select `TUMCREATE_ESTL > building_model`, select a location at `Where to clone to` and click `Clone the repo!`
	8. (Optional) Go to `File > Preferences > Git Flow`
	9. (Optional) Click `Initialize Git Flow`
5. Open `Anaconda Prompt` from the start menu:
	1. Run `cd path_to_building_model_directory` (replace `path_to_building_model_directory` with your path)
	2. (Optional) Run `activate environment_name` if you would like to install the model in a specific conda environment
	2. Run `pip install -e .`
6. Open PyCharm:
	1. Click `Open` and point to location of the building_model directory
	2. Go to `File > Settings > Project: building_model > Project Interpreter`
	3. Click on the settings button (looks like a wheel) and click `Add...`
	4. Go to `System Interpreter` and click `...`
	5. Point to the location of your conda environment `environment_name`, usually at `C:\Users\your_username\AppData\Local\Continuum\anaconda3\envs\environment_name\python.exe`

## Development workflow

Note: Before committing/merging/pushing/pulling changes to/from the repository, close all programs to avoid access errors.

* Development is based on Python 3.6
* Development/versioning follows the GitFlow principle: https://datasift.github.io/gitflow/IntroducingGitFlow.html
* Coding style follows these rules:
	* Variable/function names are in lowercase and underscore_case, hence all letters are lowercase and all words are seperated by underscores
	* Variable/function names should avoid abbreviations
