REM script used to test the cea by the jenkins for each pull request
SET CEA=C:\ProgramData\ceajenkins\ceatest
SET PATH=%CEA%\Python;%CEA%\Python\Scripts;%CEA%\Daysim;%PATH%
SET PYTHONHOME=%CEA%\Python
SET GDAL_DATA=%CEA%\Python\Library\share\gdal
SET PROJ_LIB=%CEA%\Python\Library\share
SET RAYPATH=%CEA%\Daysim
"%CEA%\Python\python.exe" -u -m pip install -e .

"%CEA%\Python\python.exe" -u -m cea.interfaces.cli.cli test --workflow quick

if %errorlevel% neq 0 exit /b %errorlevel%
