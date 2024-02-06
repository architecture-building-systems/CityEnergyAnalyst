# NSIS script for creating the City Energy Analyst installer
; include logic library
!include 'LogicLib.nsh'

; include the modern UI stuff
!include "MUI2.nsh"

; include some string functions
#!include "StrFunc.nsh"
#${StrRep}

!define CEA_TITLE "City Energy Analyst"
!define VER $%CEA_VERSION%
!define CEA_REPO_URL "https://github.com/architecture-building-systems/CityEnergyAnalyst.git"

Name "${CEA_TITLE} ${VER}"
OutFile "Output\Setup_CityEnergyAnalyst_${VER}.exe"
SetCompressor /FINAL lzma
CRCCheck On

;--------------------------------
;Sets the default installation directory
InstallDir "$DOCUMENTS\CityEnergyAnalyst"

;Request application privileges for Windows Vista
RequestExecutionLevel user

;--------------------------------
;Interface Settings

!define MUI_ICON "cea-icon.ico"
!define MUI_FILE "savefile"
!define MUI_BRANDINGTEXT "${CEA_TITLE} ${VER}"
!define MUI_ABORTWARNING

;--------------------------------
;Pages

!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Base Installation" Base_Installation_Section
    SectionIn RO  # this section is required so user is unable to uncheck
    SetOutPath "$INSTDIR"

    # install the CEA-GUI to "dashboard" folder
    File /r "CityEnergyAnalyst-GUI-win32-x64"
    Rename "CityEnergyAnalyst-GUI-win32-x64" "dashboard"

    # add micromamba
    File "micromamba.exe"
    Rename "micromamba.exe" "dependencies\micromamba.exe"

    # Icon for shortcuts
    File "cea-icon.ico"

    File "activate.bat"
    File "cea-env.bat"
    File "..\conda-lock.yml"
    File "cityenergyanalyst.tar.gz"

    # create CEA conda environment
    DetailPrint "micromamba create -n cea -f conda-lock.yml"
    nsExec::ExecToLog '"$INSTDIR\activate.bat" micromamba create -n cea -f conda-lock.yml'

    # create CEA conda environment
    DetailPrint "micromamba create -n cea -f conda-lock.yml"
    nsExec::ExecToLog '"$INSTDIR\cea-env.bat" micromamba install git -c conda-forge'

    # install CEA from tarball
    DetailPrint "pip installing CityEnergyAnalyst==${VER}"
    nsExec::ExecToLog '"$INSTDIR\cea-env.bat" pip install --no-deps "$INSTDIR\cityenergyanalyst.tar.gz"'
    Pop $0 # make sure cea was installed
    DetailPrint 'pip install cityenergyanalyst==${VER} returned $0'
    ${If} "$0" != "0"
        Abort "Could not install CityEnergyAnalyst ${VER} - see Details"
    ${EndIf}
    
    # create cea.config file in the %userprofile% directory by calling `cea --help` and set daysim paths
    nsExec::ExecToLog '"$INSTDIR\cea-env.bat" cea --help'
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

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

    # create a shortcut in the $INSTDIR for launching the CEA console
    CreateShortcut "$INSTDIR\CEA Console.lnk" "$%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" \
        "-ExecutionPolicy ByPass -NoExit -Command '& $INSTDIR\dependencies\micromamba.exe shell hook -s powershell | Out-String | Invoke-Expression; micromamba activate cea'" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    # create a shortcut in the $INSTDIR for launching the CEA dashboard
    CreateShortcut "$INSTDIR\CEA Dashboard.lnk" "$INSTDIR\dashboard\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

    CreateShortcut "$INSTDIR\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"

SectionEnd

Section "Create Start menu shortcuts" Create_Start_Menu_Shortcuts_Section

    # create shortcuts in the start menu for launching the CEA console
    CreateDirectory '$SMPROGRAMS\${CEA_TITLE}'
    CreateShortCut '$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk' "$%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" \
        "-ExecutionPolicy ByPass -NoExit -Command '& $INSTDIR\dependencies\micromamba.exe shell hook -s powershell | Out-String | Invoke-Expression; micromamba activate cea'" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\CEA Dashboard.lnk" "$INSTDIR\CityEnergyAnalyst-GUI-win32-x64\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" "" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" 0 SW_SHOWNORMAL "" "Uninstall the City Energy Analyst"

SectionEnd

Section /o "Developer version" Clone_Repository_Section

    DetailPrint "Cloning GitHub Repository ${CEA_REPO_URL}"
    nsExec::ExecToLog '"$INSTDIR\cea-env.bat" git clone ${CEA_REPO_URL}'
    DetailPrint "Binding CEA to repository"
    nsExec::ExecToLog '"$INSTDIR\cea-env.bat" pip install -e "$INSTDIR\CityEnergyAnalyst"'

SectionEnd

Section /o "Create Desktop shortcuts" Create_Desktop_Shortcuts_Section

    # create shortcuts on the Desktop for launching the CEA console
    CreateShortCut '$DESKTOP\CEA Console.lnk' "$%WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe" \
        "-ExecutionPolicy ByPass -NoExit -Command '& $INSTDIR\dependencies\micromamba.exe shell hook -s powershell | Out-String | Invoke-Expression; micromamba activate cea'" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Console"

    CreateShortcut "$DESKTOP\CEA Dashboard.lnk" "$INSTDIR\CityEnergyAnalyst-GUI-win32-x64\CityEnergyAnalyst-GUI.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWMAXIMIZED "" "Launch the CEA Dashboard"

    CreateShortcut "$DESKTOP\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"

SectionEnd

;Uninstaller Section

Section "Uninstall"

    ; Delete the shortcuts
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\CEA Dashboard.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\cea.config.lnk"
    Delete /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk"
    RMDir /REBOOTOK "$SMPROGRAMS\${CEA_TITLE}"

    Delete /REBOOTOK "$DESKTOP\CEA Console.lnk"
    Delete /REBOOTOK "$DESKTOP\CEA Dashboard.lnk"
    Delete /REBOOTOK "$DESKTOP\cea.config.lnk"

    ; Delete the cea.config file
    Delete /REBOOTOK "$PROFILE\cea.config"

    ; Delete files in install directory
    Delete /REBOOTOK "$INSTDIR\CEA Console.lnk"
    Delete /REBOOTOK "$INSTDIR\CEA Dashboard.lnk"
    Delete /REBOOTOK "$INSTDIR\cea.config.lnk"
    Delete /REBOOTOK "$INSTDIR\cea-icon.ico"
    RMDir /R /REBOOTOK "$INSTDIR\dashboard"
    RMDir /R /REBOOTOK "$INSTDIR\dependencies"

    Delete /REBOOTOK "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

    ; Change current working directory so that it can be deleted
    ; Will only be deleted if the directory is empty
    SetOutPath $TEMP
    RMDir /REBOOTOK "$INSTDIR"

SectionEnd