REM script used to test the cea by the jenkins for each pull request
SET CEA=C:\ProgramData\ceajenkins\ceatest-py3
CALL %CEA%\Python\Scripts\activate.bat
SET PYTHONHOME=%CEA%\Python
SET RAYPATH=%CEA%\Daysim
"%CEA%\Python\python.exe" -u -m pip install --no-deps -e .

"%CEA%\Python\python.exe" -u -m cea.interfaces.cli.cli test --workflow quick

if %errorlevel% neq 0 exit /b %errorlevel%
