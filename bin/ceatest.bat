rem script used to test the cea by the jenkins
rem creates a conda environment (deleting the old one first)

set PATH=%USERPROFILE%\Miniconda2\Scripts\;%PATH%
set PATH=%PROGRAMDATA%\Miniconda2\Scripts\;%PATH%
echo %USERPROFILE%
where conda
set CONDA_ENVS_PATH=%LOCALAPPDATA%\conda\conda\envs
conda env remove -y -q --name cea
conda env create -q
set PATH=%LOCALAPPDATA%\conda\conda\envs\cea;%PATH%
set PATH=%LOCALAPPDATA%\conda\conda\envs\cea\Scripts;%PATH%
set CONDA_DEFAULT_ENV=cea
%LOCALAPPDATA%\conda\conda\envs\cea\Scripts\pip.exe install .[dev]
where cea
cea test

