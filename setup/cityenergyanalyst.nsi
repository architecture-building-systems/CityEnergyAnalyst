# NSIS script for creating the City Energy Analyst installer
Unicode true
!define CEA_TITLE "City Energy Analyst"
!define VER $%CEA_VERSION%
!define CEA_GUI_NAME "CEA-4 Desktop"  # references productName from GUI package.json. ensure it is the same
!define CEA_GUI_INSTALL_FOLDER "app"

# Request the highest possible execution level for the current user
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_DEFAULT_CURRENTUSER
!define MULTIUSER_INSTALLMODE_INSTDIR "CityEnergyAnalyst"
!define MULTIUSER_INSTALLMODE_FUNCTION onMultiUserModeChanged
# !define MULTIUSER_MUI

!include MultiUser.nsh

; include logic library
!include 'LogicLib.nsh'

; include the modern UI stuff
!include "MUI2.nsh"

Var LauncherExtension

Name "${CEA_TITLE} ${VER}"
OutFile "Output\Setup_CityEnergyAnalyst_${VER}.exe"
SetCompressor /FINAL lzma
CRCCheck On

;--------------------------------
;Request application privileges for Windows Vista
#RequestExecutionLevel user

;--------------------------------
;Interface Settings

!define MUI_ICON "cea-icon.ico"
!define MUI_FILE "savefile"
!define MUI_BRANDINGTEXT "${CEA_TITLE} ${VER}"
!define MUI_ABORTWARNING

;--------------------------------
;Pages

!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
# !insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Callback Functions

Function .onInit
    !insertmacro MULTIUSER_INIT
FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

Function onMultiUserModeChanged
# set default installation directory to Documents if CurrentUser mode
${If} $MultiUser.InstallMode == "CurrentUser"
    StrCpy $INSTDIR "$DOCUMENTS\${MULTIUSER_INSTALLMODE_INSTDIR}"
${EndIf}
FunctionEnd

;--------------------------------
;Installer Sections

Function .onInstFailed
    # Ensure temporary files are cleaned up
    DetailPrint "Installation failed, cleaning up temporary files..."

    ${If} ${FileExists} "$INSTDIR\cityenergyanalyst.tar.gz"
        Delete /REBOOTOK "$INSTDIR\cityenergyanalyst.tar.gz"
    ${EndIf}

    ${If} ${FileExists} "$INSTDIR\dependencies"
        RMDir /r /REBOOTOK "$INSTDIR\dependencies"
    ${EndIf}
    
    ${If} ${FileExists} "$INSTDIR\gui_setup.exe"
        Delete /REBOOTOK "$INSTDIR\gui_setup.exe"
    ${EndIf}


FunctionEnd

Function BaseInstallationSection
    SetOutPath "$INSTDIR"

    # Check if PowerShell exists
    ${If} ${FileExists} "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
        StrCpy $LauncherExtension "ps1"  # Use PowerShell
    ${Else}
        StrCpy $LauncherExtension "bat"  # Fallback to batch
    ${EndIf}

    # Install GUI first so that rollback would not be as painful in case of failure
    # install the CEA Desktop to $CEA_GUI_INSTALL_FOLDER
    File "gui_setup.exe"

    # Run GUI Setup
    DetailPrint "Installing CEA Desktop"
    ExecWait '"$INSTDIR\gui_setup.exe" /S /D="$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"' $0
    DetailPrint "CEA Desktop installer returned: $0"
    ${If} "$0" != "0"
        Abort "Installation failed - see Details"
    ${EndIf}
    ${IfNot} ${FileExists} "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
        Abort "Installation failed: Something went wrong with CEA Desktop setup. Install directory not found."
    ${EndIf}
    Delete "$INSTDIR\gui_setup.exe"

    File "${WHEEL_FILE}"
    File /r "dependencies"

    SetOutPath "$INSTDIR\dependencies"
    Nsis7z::ExtractWithDetails "$INSTDIR\dependencies\cea-env.7z" "Installing CEA dependencies %s..."
    Delete "$INSTDIR\dependencies\cea-env.7z"
    SetOutPath "$INSTDIR"

    # create hook for cmd shell
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" shell hook -s cmd.exe "$INSTDIR\dependencies\micromamba"'
    # fix pip due to change in python path
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea python -m pip install --upgrade pip --force-reinstall'

    # install CEA from wheel
    DetailPrint "pip installing CityEnergyAnalyst==${VER}"
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea pip install "$INSTDIR\${WHEEL_FILE}"'
    Pop $0 # make sure cea was installed
    DetailPrint 'pip install cityenergyanalyst==${VER} returned $0'
    ${If} "$0" != "0"
        Abort "Could not install CityEnergyAnalyst ${VER} - see Details"
    ${EndIf}
    Delete "$INSTDIR\${WHEEL_FILE}"
    
    # Run cea --version to check if installation was successful
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea cea --version'
    Pop $0
    DetailPrint '"cea --version" returned $0'
    ${If} "$0" != "0"
        Abort "Installation failed - see Details"
    ${EndIf}

    # make sure jupyter has access to the ipython kernel
    #nsExec::ExecToLog '"$INSTDIR\cea-env-run.bat" python -m ipykernel install --prefix $INSTDIR\Dependencies\Python'

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

    # Icon for shortcuts
    File "cea-icon.ico"

    # create a shortcut in the $INSTDIR for launching the CEA console
    ${If} $LauncherExtension == "ps1"
        CreateShortcut "$INSTDIR\CEA Console.lnk" "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-ExecutionPolicy ByPass -NoExit -File "$INSTDIR\dependencies\cea-env.ps1"' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${Else}
        CreateShortcut "$INSTDIR\CEA Console.lnk" "$WINDIR\System32\cmd.exe" '/K ""$INSTDIR\dependencies\cea-env.bat""' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${EndIf}

    # create a shortcut in the $INSTDIR for launching the CEA Desktop
    CreateShortcut "$INSTDIR\CEA Desktop.lnk" "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\${CEA_GUI_NAME}.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch CEA Desktop"
FunctionEnd

Function CreateStartMenuShortcutsSection
    # create shortcuts in the start menu for launching the CEA console
    CreateDirectory '$SMPROGRAMS\${CEA_TITLE}'
    ${If} $LauncherExtension == "ps1"
        CreateShortCut '$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk' "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-ExecutionPolicy ByPass -NoExit -File "$INSTDIR\dependencies\cea-env.ps1"' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${Else}
        CreateShortCut '$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk' "$WINDIR\System32\cmd.exe" '/K ""$INSTDIR\dependencies\cea-env.bat""' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${EndIf}

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\CEA Desktop.lnk" "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\${CEA_GUI_NAME}.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch CEA Desktop"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" "" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" 0 SW_SHOWNORMAL "" "Uninstall the City Energy Analyst"
FunctionEnd

Function CreateDesktopShortcutsSection
    # create shortcuts on the Desktop for launching the CEA console
    ${If} $LauncherExtension == "ps1"
        CreateShortCut '$DESKTOP\CEA Console.lnk' "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" '-ExecutionPolicy ByPass -NoExit -File "$INSTDIR\dependencies\cea-env.ps1"' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${Else}
        CreateShortCut '$DESKTOP\CEA Console.lnk' "$WINDIR\System32\cmd.exe" '/K ""$INSTDIR\dependencies\cea-env.bat""' \
            "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"
    ${EndIf}

    CreateShortcut "$DESKTOP\CEA Desktop.lnk" "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\${CEA_GUI_NAME}.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch CEA Desktop"
FunctionEnd

Function un.UninstallSection
    ; Delete the shortcuts
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Desktop.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk"
    RMDir /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}"

    Delete /REBOOTOK "$DESKTOP\CEA Console.lnk"
    Delete /REBOOTOK "$DESKTOP\CEA Desktop.lnk"

    ; Uninstall CEA Desktop silently
    DetailPrint 'Uninstalling ${CEA_GUI_NAME}'
    nsExec::ExecToLog '"$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\Uninstall ${CEA_GUI_NAME}.exe" /S'
    Pop $0
    DetailPrint "Uninstaller returned: $0"
    
    ; Optional: Add a small delay to ensure all processes are terminated
    Sleep 1000

    ; Delete files in install directory
    Delete /REBOOTOK "$INSTDIR\CEA Console.lnk"
    Delete /REBOOTOK "$INSTDIR\CEA Desktop.lnk"
    Delete /REBOOTOK "$INSTDIR\cea-icon.ico"
    RMDir /R /REBOOTOK "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
    RMDir /R /REBOOTOK "$INSTDIR\dependencies"

    Delete /REBOOTOK "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"
FunctionEnd

Section "Base Installation" Base_Installation_Section
    SectionIn RO  # this section is required so user is unable to uncheck
    Call BaseInstallationSection
SectionEnd

Section "Create Start menu shortcuts" Create_Start_Menu_Shortcuts_Section
    Call CreateStartMenuShortcutsSection
SectionEnd

Section /o "Create Desktop shortcuts" Create_Desktop_Shortcuts_Section
    Call CreateDesktopShortcutsSection
SectionEnd

Section "Uninstall"
    Call un.UninstallSection
SectionEnd
