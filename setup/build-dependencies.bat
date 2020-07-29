REM create the Dependencies.7z file, placing it in the Downloads folder
REM it's meant to be called from a cea-aware conda environment

REM Make sure we have access to the executables needed for this
SET PATH=C:\Program Files\7-Zip;%PATH%
PUSHD %USERPROFILE%\Downloads
REM %~dp0
CALL conda env remove -n cea
CALL conda env create -n cea -f "%~dp0..\environment.yml"
CALL conda activate cea
WHERE python
CALL python -m pip install "%~dp0.."
CALL python -m pip install "%~dp0..\..\cea-workflow-utils"
CALL python -m pip install pandana urbanaccess
CALL python -m pip install jupyter ipython
CALL python -m pip install sphinx
CALL conda deactivate
DEL /F/Q cea.zip
CALL conda-pack -n cea -j -1 --format zip
DEL /F/Q/S "%USERPROFILE%\Downloads\Dependencies" > NUL
RMDIR /Q/S "%USERPROFILE%\Downloads\Dependencies
CALL 7z x cea.zip -oDependencies\Python -y
CALL 7z a Dependencies.7z Dependencies\ -x9 -sdel
