@TITLE CEA Dashboard
@SET MAMBA_ROOT_PREFIX=%~dp0dependencies\micromamba
@CALL %windir%\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& '%~dp0dependencies\micromamba.exe' shell hook -s powershell | Out-String | Invoke-Expression ; micromamba activate cea ; cea dashboard"
