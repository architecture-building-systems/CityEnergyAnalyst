# NSIS script for creating the City Energy Analyst installer
!define CEA_TITLE "City Energy Analyst"
!define VER $%CEA_VERSION%

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

Section "Base Installation" Base_Installation_Section
    SectionIn RO  # this section is required so user is unable to uncheck
    SetOutPath "$INSTDIR"

    File "cityenergyanalyst.tar.gz"
    File /r "dependencies"

    SetOutPath "$INSTDIR\dependencies"
    Nsis7z::ExtractWithDetails "$INSTDIR\dependencies\cea-env.7z" "Installing CEA dependencies %s..."
    Delete "$INSTDIR\dependencies\cea-env.7z"
    SetOutPath "$INSTDIR"

    # create hook for cmd shell
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" shell hook -s cmd.exe "$INSTDIR\dependencies\micromamba"'
    # fix pip due to change in python path
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea python -m pip install --upgrade pip --force-reinstall'

    # install CEA from tarball
    DetailPrint "pip installing CityEnergyAnalyst==${VER}"
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea pip install --no-deps "$INSTDIR\cityenergyanalyst.tar.gz"'
    Pop $0 # make sure cea was installed
    DetailPrint 'pip install cityenergyanalyst==${VER} returned $0'
    ${If} "$0" != "0"
        Abort "Could not install CityEnergyAnalyst ${VER} - see Details"
    ${EndIf}
    Delete "$INSTDIR\cityenergyanalyst.tar.gz"
    
    # create cea.config file in the %userprofile% directory by calling `cea --help` and set daysim paths
    nsExec::ExecToLog '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea cea --help'
    Pop $0
    DetailPrint '"cea --help" returned $0'
    ${If} "$0" != "0"
        Abort "Installation failed - see Details"
    ${EndIf}
    #WriteINIStr "$PROFILE\cea.config" radiation daysim-bin-directory "$INSTDIR\Dependencies\Daysim"

    # make sure qt.conf has the correct paths
    #DetailPrint "Updating qt.conf..."
    #${StrRep} $0 "$INSTDIR" "\" "/" # $0 now contains the $INSTDIR with forward slashes instead of backward slashes
    #WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Prefix "$0/Dependencies/Python/Library"
    #WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Binaries "$0/Dependencies/Python/Library/bin"
    #WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Libraries "$0/Dependencies/Python/Library/lib"
    #WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Headers "$0/Dependencies/Python/Library/include/qt"

    # make sure jupyter has access to the ipython kernel
    #nsExec::ExecToLog '"$INSTDIR\cea-env-run.bat" python -m ipykernel install --prefix $INSTDIR\Dependencies\Python'

    # install the CEA-GUI to "dashboard" folder
    File "gui_setup.exe"
    File "dashboard.bat"

    # Run GUI Setup
    DetailPrint "Installing CEA GUI"
    nsExec::ExecToLog '"$INSTDIR\gui_setup.exe" /S /D="$INSTDIR\dashboard"'
    Delete "$INSTDIR\gui_setup.exe"

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

    # Icon for shortcuts
    File "cea-icon.ico"

    # create a shortcut in the $INSTDIR for launching the CEA console
    CreateShortcut "$INSTDIR\CEA Console.lnk" "$WINDIR\System32\cmd.exe" '/K "$INSTDIR\dependencies\cea-env.bat"' \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    # create a shortcut in the $INSTDIR for launching the CEA dashboard
    CreateShortcut "$INSTDIR\CEA Dashboard.lnk" "$INSTDIR\dashboard\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

SectionEnd

Section "Create Start menu shortcuts" Create_Start_Menu_Shortcuts_Section

    # create shortcuts in the start menu for launching the CEA console
    CreateDirectory '$SMPROGRAMS\${CEA_TITLE}'
    CreateShortCut '$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk' "$WINDIR\System32\cmd.exe" '/K "$INSTDIR\dependencies\cea-env.bat"' \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\CEA Dashboard.lnk" "$INSTDIR\dashboard\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" "" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" 0 SW_SHOWNORMAL "" "Uninstall the City Energy Analyst"

SectionEnd

Section /o "Create Desktop shortcuts" Create_Desktop_Shortcuts_Section

    # create shortcuts on the Desktop for launching the CEA console
    CreateShortCut '$DESKTOP\CEA Console.lnk' "$WINDIR\System32\cmd.exe" '/K "$INSTDIR\dependencies\cea-env.bat"' \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    CreateShortcut "$DESKTOP\CEA Dashboard.lnk" "$INSTDIR\dashboard\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

SectionEnd

;Uninstaller Section

Section "Uninstall"

    ; Delete the shortcuts
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Dashboard.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk"
    RMDir /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}"

    Delete /REBOOTOK "$DESKTOP\CEA Console.lnk"
    Delete /REBOOTOK "$DESKTOP\CEA Dashboard.lnk"

    ; Uninstall CEA GUI silently
    DetailPrint 'Uninstalling CityEnergyAnalyst-GUI'
    nsExec::ExecToLog '"$INSTDIR\dashboard\Uninstall CityEnergyAnalyst-GUI.exe" /S'

    ; Delete files in install directory
    Delete /REBOOTOK "$INSTDIR\CEA Console.lnk"
    Delete /REBOOTOK "$INSTDIR\CEA Dashboard.lnk"
    Delete /REBOOTOK "$INSTDIR\cea-icon.ico"
    Delete /REBOOTOK "$INSTDIR\dashboard.bat"
    RMDir /R /REBOOTOK "$INSTDIR\dashboard"
    RMDir /R /REBOOTOK "$INSTDIR\dependencies"

    Delete /REBOOTOK "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

    ; Change current working directory so that it can be deleted
    ; Will only be deleted if the directory is empty
    SetOutPath $TEMP
    RMDir /REBOOTOK "$INSTDIR"

SectionEnd
