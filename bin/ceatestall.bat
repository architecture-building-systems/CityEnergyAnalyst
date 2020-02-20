REM script used to test the cea by the jenkins
SET CEA=%USERPROFILE%\Documents\CityEnergyAnalyst
SET PATH=%CEA%\Dependencies\Python;%CEA%\Dependencies\Python\Scripts;%CEA%\Dependencies\Daysim;%PATH%
SET PYTHONHOME=%CEA%\Dependencies\Python
SET PYTHONHOME=%CEA%\Dependencies\Python
SET GDAL_DATA=%CEA%\Dependencies\Python\Library\share\gdal
SET PROJ_LIB=%CEA%\Dependencies\Python\Library\share
SET RAYPATH=%CEA%\Dependencies\Daysim
"%CEA%\Dependencies\Python\python.exe" -u -m pip install -e .
cea test --reference-cases open --tasks all --verbosity 1
if %errorlevel% neq 0 exit /b %errorlevel%



