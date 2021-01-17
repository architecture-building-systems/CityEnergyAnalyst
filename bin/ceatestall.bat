REM script used to test the cea by the jenkins when merging to master
SET CEA=C:\ProgramData\ceajenkins\ceatestall-py3
CALL %CEA%\Python\Scripts\activate.bat
SET PYTHONHOME=%CEA%\Python
SET RAYPATH=%CEA%\Daysim
"%CEA%\Python\python.exe" -u -m pip install --no-deps -e .

REM: remove *.pyc files
PUSHD cea
DEL /S /Q *.pyc
POPD

"%CEA%\Python\python.exe" -u -m cea.interfaces.cli.cli test --workflow slow

if %errorlevel% neq 0 exit /b %errorlevel%



