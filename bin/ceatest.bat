rem script used to test the cea by the jenkins
rem creates a conda environment (deleting the old one first)

set PATH=%USERPROFILE%\Miniconda2\Scripts\;%PATH%
set PATH=%PROGRAMDATA%\Miniconda2\Scripts\;%PATH%
echo %USERPROFILE%
where conda
pause
conda env remove -y -q --name cea
conda env create -q
set PATH=C:\Users\darthoma\AppData\Local\conda\conda\envs\cea;%PATH%
set PATH=C:\Users\darthoma\AppData\Local\conda\conda\envs\cea\Scripts;%PATH%
where pip
pip install .[dev]
where cea
cea test

