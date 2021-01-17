REM script used to test the cea by the jenkins for each pull request
SET CEA=C:\ProgramData\ceajenkins\ceatest-py3

SET PATH=%CEA%\Python;%CEA%\Python\Scripts;%PATH%
SET PATH=%CEA%\Python\Library\bin;%CEA%\Daysim;%PATH%

SET PYTHONHOME=%CEA%\Python
SET RAYPATH=%CEA%\Daysim
SET GDAL_DATA=%CEA%\Python\Library\share\gdal
SET PROJ_LIB=%CEA%\Python\Library\share

"%CEA%\Python\python.exe" -u -m pip install --no-deps -e .

REM: remove *.pyc files
PUSHD cea
DEL /S /Q *.pyc
POPD

"%CEA%\Python\python.exe" -u -m cea.interfaces.cli.cli test --workflow quick

if %errorlevel% neq 0 exit /b %errorlevel%
