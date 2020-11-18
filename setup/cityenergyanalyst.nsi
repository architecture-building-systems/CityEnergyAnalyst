# NSIS script for creating the City Energy Analyst installer
SetCompressor /FINAL lzma

; include logic library
!include 'LogicLib.nsh'

; include the modern UI stuff
!include "MUI2.nsh"

; include some string functions
!include "StrFunc.nsh"
${StrRep}

# icon stuff
!define MUI_ICON "cea-icon.ico"


# download CEA conda env from here
;!define CEA_ENV_URL "https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/download/v${VER}/Dependencies.7z"
!define CEA_ENV_URL "https://www.dropbox.com/s/2tusftdoivvp9ox/Dependencies.7z?dl=1"
!define CEA_ENV_FILENAME "Dependencies.7z"
!define RELATIVE_GIT_PATH "Dependencies\cmder\vendor\git-for-windows\bin\git.exe"
!define CEA_REPO_URL "https://github.com/architecture-building-systems/CityEnergyAnalyst.git"
;!define CEA_ELECTRON_URL "https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/download/v${VER}/win-unpacked.7z"
!define CEA_ELECTRON_URL "https://github.com/architecture-building-systems/CityEnergyAnalyst/releases/download/v3.8.0a0/win-unpacked.7z"

!define CEA_TITLE "City Energy Analyst"

!define PIP_INSTALL '"$INSTDIR\pip-install.bat"'

# figure out the version based on cea\__init__.py
!system "get_version.exe"
!include "cea_version.txt"

Name "${CEA_TITLE} ${VER}"

!define MUI_FILE "savefile"
!define MUI_BRANDINGTEXT "${CEA_TITLE} ${VER}"
CRCCheck On


OutFile "Output\Setup_CityEnergyAnalyst_${VER}.exe"


;--------------------------------
;Folder selection page

InstallDir "$DOCUMENTS\CityEnergyAnalyst"

;Request application privileges for Windows Vista
RequestExecutionLevel user

;--------------------------------
;Interface Settings

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
    SectionIn RO  # this section is required
    SetOutPath "$INSTDIR"

    File "cea-icon.ico"
    File "cea-env.bat"
    File "pip-install.bat"
    File "cea-env-run.bat"
    CreateDirectory $INSTDIR\Dependencies\cmder\config\profile.d
    File /oname=Dependencies\cmder\config\profile.d\cea-cmder-config.bat "cmder-config.bat"
    File "dashboard.bat"

    # install cmder (incl. git and bash... woohoo!!)
    File /r "Dependencies"
    SetOutPath "$INSTDIR\Dependencies\cmder"
    Nsis7z::ExtractWithDetails "cmder.7z" "Installing CEA Console %s..."
    Delete "cmder.7z"
    SetOutPath "$INSTDIR"

    # install the CEA-GUI
    File /r "win-unpacked"

    # create a shortcut in the $INSTDIR for launching the CEA console
    CreateShortcut "$INSTDIR\CEA Console.lnk" "$INSTDIR\Dependencies\cmder\cmder.exe" "/single" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL \
        CONTROL|SHIFT|F10 "Launch the CEA Console"

    # create a shortcut in the $INSTDIR for launching the CEA dashboard
    CreateShortcut "$INSTDIR\CEA Dashboard.lnk" "$INSTDIR\win-unpacked\CityEnergyAnalyst.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

    CreateShortcut "$INSTDIR\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"
    
    # make sure qt.conf has the correct paths
    DetailPrint "Updating qt.conf..."
    ${StrRep} $0 "$INSTDIR" "\" "/" # $0 now constains the $INSTDIR with forward slashes instead of backward slashes
    WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Prefix "$0/Dependencies/Python/Library"
    WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Binaries "$0/Dependencies/Python/Library/bin"
    WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Libraries "$0/Dependencies/Python/Library/lib"
    WriteINIStr "$INSTDIR\Dependencies\Python\qt.conf" Paths Headers "$0/Dependencies/Python/Library/include/qt"

    # install CEA from tarball
    DetailPrint "Pip installing CityEnergyAnalyst==${VER}"
    nsExec::ExecToLog '${PIP_INSTALL} --force-reinstall --no-deps "$INSTDIR\Dependencies\cityenergyanalyst.tar.gz"'

    # make sure cea was installed
    Pop $0
    DetailPrint 'pip install cityenergyanalyst==${VER} returned $0'
    ${If} "$0" != "0"
        Abort "Could not install CityEnergyAnalyst ${VER} - see Details"
    ${EndIf}
    
    # create cea.config file in the %userprofile% directory by calling `cea --help` and set daysim paths
    nsExec::ExecToLog '"$INSTDIR\cea-env-run.bat" cea --help'
    Pop $0
    DetailPrint '"cea --help" returned $0'
    ${If} "$0" != "0"
        Abort "Installation failed - see Details"
    ${EndIf}
    WriteINIStr "$PROFILE\cea.config" radiation daysim-bin-directory "$INSTDIR\Dependencies\Daysim"

    # make sure jupyter has access to the ipython kernel
    nsExec::ExecToLog '"$INSTDIR\cea-env-run.bat" python -m ipykernel install --prefix $INSTDIR\Dependencies\Python'

    # add sphinx so we can cea-doc html...
    nsExec::ExecToLog '${PIP_INSTALL} --force-reinstall --no-deps sphinx'

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

SectionEnd

Section "Create Start menu shortcuts" Create_Start_Menu_Shortcuts_Section

    # create shortcuts in the start menu for launching the CEA console
    CreateDirectory '$SMPROGRAMS\${CEA_TITLE}'
    CreateShortCut '$SMPROGRAMS\${CEA_TITLE}\CEA Console.lnk' '$INSTDIR\Dependencies\cmder\cmder.exe' '/single' \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL CONTROL|SHIFT|F10 "Launch the CEA Console"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\CEA Dashboard.lnk" "$INSTDIR\win-unpacked\CityEnergyAnalyst.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Launch the CEA Dashboard"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"

    CreateShortcut "$SMPROGRAMS\${CEA_TITLE}\Uninstall CityEnergy Analyst.lnk" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" "" \
        "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe" 0 SW_SHOWNORMAL "" "Uninstall the City Energy Analyst"

SectionEnd

Section /o "Developer version" Clone_Repository_Section

    DetailPrint "Cloning GitHub Repository ${CEA_REPO_URL}"
    nsExec::ExecToLog '"$INSTDIR\${RELATIVE_GIT_PATH}" clone ${CEA_REPO_URL}'
    DetailPrint "Binding CEA to repository"
    nsExec::ExecToLog '${PIP_INSTALL} -e "$INSTDIR\CityEnergyAnalyst"'

SectionEnd

Section /o "Create Desktop shortcuts" Create_Desktop_Shortcuts_Section

    # create shortcuts on the Desktop for launching the CEA console
    CreateShortCut '$DESKTOP\CEA Console.lnk' '$INSTDIR\Dependencies\cmder\cmder.exe' '/single' \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL CONTROL|SHIFT|F10 "Launch the CEA Console"

    CreateShortcut "$DESKTOP\CEA Dashboard.lnk" "$INSTDIR\win-unpacked\CityEnergyAnalyst.exe" "" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWMAXIMIZED "" "Launch the CEA Dashboard"

    CreateShortcut "$DESKTOP\cea.config.lnk" "$WINDIR\notepad.exe" "$PROFILE\cea.config" \
        "$INSTDIR\cea-icon.ico" 0 SW_SHOWNORMAL "" "Open CEA Configuration file"

SectionEnd

;--------------------------------
;Descriptions

;Language strings
;  LangString DESC_SecDummy ${LANG_ENGLISH} "A test section."

  ;Assign language strings to sections
;  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
;    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
;  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
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

  SetOutPath $TEMP
  Delete /REBOOTOK "$INSTDIR\Uninstall_CityEnergyAnalyst_${VER}.exe"

  RMDir /R /REBOOTOK "$INSTDIR"

SectionEnd