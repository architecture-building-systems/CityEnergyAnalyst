@SET MAMBA_ROOT_PREFIX=%~dp0micromamba
@CALL %~dp0micromamba.exe shell hook
@CALL %MAMBA_ROOT_PREFIX%\condabin\mamba_hook.bat

@REM run the command
@CALL %*