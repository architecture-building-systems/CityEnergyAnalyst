@REM Set up the environment for using the CEA - assumes the CEA is installed and this file is in the root
@REM of the installation
@REM
@REM set up environment variables
@REM SET PATH=%~dp0Dependencies\Python;%~dp0Dependencies\Python\Scripts;%PATH%
@REM SET PATH=%~dp0Dependencies\Python\Library\bin;%~dp0Dependencies\Daysim;%PATH%
@REM SET PYTHONHOME=%~dp0Dependencies\Python
@REM SET GDAL_DATA=%~dp0Dependencies\Python\Library\share\gdal
@REM SET PROJ_LIB=%~dp0Dependencies\Python\Library\share\proj
@CALL "%~dp0Dependencies\Python\Scripts\activate.bat"
@SET PROMPT=(CEA) $P$G
@SET RAYPATH=%~dp0Dependencies\Daysim