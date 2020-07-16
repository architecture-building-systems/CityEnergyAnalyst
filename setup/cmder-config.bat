REM This file is placed in $INSTDIR\Dependencies\cmder\config\profile.d...
SET CEA-INSTDIR=%~dp0..\..\..\..
PUSHD %CEA-INSTDIR%
SET CEA-INSTDIR=%CD%
POPD

CALL %CEA-INSTDIR%\cea-env.bat
ALIAS find="%CEA-INSTDIR%\Dependencies\cmder\vendor\git-for-windows\usr\bin\find.exe" $*