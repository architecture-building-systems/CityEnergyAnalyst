REM script used to test the cea by the jenkins when merging to master
SET CEA=C:\ProgramData\ceajenkins\ceatestall
SET PATH=%CEA%\Python;%CEA%\Python\Scripts;%CEA%\Daysim;%PATH%
SET PYTHONHOME=%CEA%\Python
SET GDAL_DATA=%CEA%\Python\Library\share\gdal
SET PROJ_LIB=%CEA%\Python\Library\share
SET RAYPATH=%CEA%\Daysim
"%CEA%\Python\python.exe" -u -m pip install -e .

"%CEA%\Python\python.exe" -u -m cea.interfaces.cli.cli test --workflow slow

if %errorlevel% neq 0 exit /b %errorlevel%



