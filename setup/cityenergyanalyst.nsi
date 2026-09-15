# NSIS script for creating the City Energy Analyst installer
Unicode true
!define CEA_TITLE "City Energy Analyst"
!define VER $%CEA_VERSION%
!define CEA_GUI_NAME "CEA-4 Desktop"  # references productName from GUI package.json. ensure it is the same
!define CEA_GUI_INSTALL_FOLDER "app"
!define VC_REDIST_URL "https://aka.ms/vs/17/release/vc_redist.x64.exe"

# Anonymous installer telemetry (PostHog EU Cloud). POSTHOG_API_KEY is passed via
# -DPOSTHOG_API_KEY on the makensis command line (a GitHub Actions secret, never
# committed). When it is undefined, the SendTelemetry macro below compiles to a
# no-op and no telemetry code or key is present in the installer at all.
!define POSTHOG_HOST "https://eu.i.posthog.com/capture/"

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
Var InstallStep  ; tracks install progress for telemetry (see SendTelemetry)

; Macro to run a command and abort on failure
!macro RunCommand CommandStr DescriptionStr ErrorMsg
    nsExec::ExecToLog 'cmd /c "${CommandStr} 2>&1"'
    Pop $0  # capture exit code
    DetailPrint '${DescriptionStr} returned $0'
    ${If} "$0" != "0"
        ${If} "$0" == "-1073741515"
            DetailPrint "Install using ${VC_REDIST_URL} and retry."
            Abort "Missing Visual C++ Redistributable (error 0xC0000135)."
        ${Else}
            Abort "${ErrorMsg}"
        ${EndIf}
    ${EndIf}
!macroend

; Macro to uninstall CEA Desktop, with forced removal as fallback
!macro UninstallCEADesktop
    ${If} ${FileExists} "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
        ${If} ${FileExists} "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\Uninstall ${CEA_GUI_NAME}.exe"
            DetailPrint "Uninstalling ${CEA_GUI_NAME}"
            nsExec::ExecToLog '"$INSTDIR\${CEA_GUI_INSTALL_FOLDER}\Uninstall ${CEA_GUI_NAME}.exe" /S'
            Pop $0
            DetailPrint "Uninstaller returned: $0"
            Sleep 1000
        ${EndIf}
        ; Force remove folder if uninstaller failed or did not exist
        ${If} ${FileExists} "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
            RMDir /r /REBOOTOK "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
        ${EndIf}
    ${EndIf}
!macroend

; Fire-and-forget anonymous installer telemetry: counts installs and reports which
; step a failed install died on, so we don't have to rely on users reporting bugs.
; No-op when POSTHOG_API_KEY was not supplied at build time (local/fork builds).
; Must never fail or delay the install:
;  - nsExec::Exec (not ExecToLog) discards the exit code, unlike RunCommand above.
;  - The actual network call happens inside telemetry.ps1, wrapped in try/catch
;    with a short timeout, so a dead network or blocked outbound traffic is silent.
; Anonymity: distinct_id is a fresh GUID generated per install in telemetry.ps1 and
; never written to disk; only OS/arch/version/step/error-code are sent - no paths,
; no username, no hostname.
!macro SendTelemetry EventName Step ErrorCode
    !ifdef POSTHOG_API_KEY
        ${If} ${FileExists} "$PLUGINSDIR\telemetry.ps1"
            nsExec::Exec '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\telemetry.ps1" -ApiKey "${POSTHOG_API_KEY}" -PostHogHost "${POSTHOG_HOST}" -EventName "${EventName}" -CeaVersion "${VER}" -InstallerStep "${Step}" -ErrorCode "${ErrorCode}"'
            Pop $9
        ${EndIf}
    !endif
!macroend

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

!ifdef POSTHOG_API_KEY
!define MUI_COMPONENTSPAGE_TEXT_TOP "This installer sends anonymous installation statistics (OS, CPU architecture, CEA version, and whether the install succeeded) to help us fix problems. No personal data, file paths, or usage data is collected. See docs/privacy for details."
!endif
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
    !insertmacro SendTelemetry "installer_failed" "$InstallStep" "$0"

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

    # remove partially installed CEA Desktop
    !insertmacro UninstallCEADesktop
FunctionEnd

Function BaseInstallationSection
    SetOutPath "$INSTDIR"
    StrCpy $InstallStep "start"

    !ifdef POSTHOG_API_KEY
        File "/oname=$PLUGINSDIR\telemetry.ps1" "telemetry.ps1"
    !endif

    # Check if PowerShell exists
    ${If} ${FileExists} "$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
        StrCpy $LauncherExtension "ps1"  # Use PowerShell
    ${Else}
        StrCpy $LauncherExtension "bat"  # Fallback to batch
    ${EndIf}

    # check if micromamba works first before proceeding
    StrCpy $InstallStep "requirements"
    DetailPrint "Checking requirements"
    CreateDirectory "$INSTDIR\dependencies"
    SetOutPath "$INSTDIR\dependencies"
    File "dependencies\micromamba.exe"
    SetOutPath "$INSTDIR"
    # create hook for cmd shell
    !insertmacro RunCommand '"$INSTDIR\dependencies\micromamba.exe" shell hook -s cmd.exe "$INSTDIR\dependencies\micromamba"' "Setup micromamba" "Error setting up micromamba"

    # Install GUI first so that rollback would not be as painful in case of failure
    # install the CEA Desktop to $CEA_GUI_INSTALL_FOLDER
    StrCpy $InstallStep "gui"
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
    # Note: overwrites micromamba.exe extracted earlier for requirements check
    StrCpy $InstallStep "dependencies"
    File /r "dependencies"

    SetOutPath "$INSTDIR\dependencies"
    Nsis7z::ExtractWithDetails "$INSTDIR\dependencies\cea-env.7z" "Installing CEA dependencies %s..."
    Delete "$INSTDIR\dependencies\cea-env.7z"
    SetOutPath "$INSTDIR"

    # fix pip due to change in python path
    StrCpy $InstallStep "pip"
    !insertmacro RunCommand '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea python -m pip install --upgrade pip --force-reinstall' "Checking pip" "Could not setup pip - see Details"

    # install CEA from wheel
    DetailPrint "pip installing CityEnergyAnalyst==${VER}"
    !insertmacro RunCommand '"$INSTDIR\dependencies\micromamba.exe" run -r "$INSTDIR\dependencies\micromamba" -n cea pip install "$INSTDIR\${WHEEL_FILE}"' "Installing CityEnergyAnalyst" "Could not install CityEnergyAnalyst ${VER} - see Details"
    Delete "$INSTDIR\${WHEEL_FILE}"

    # Run cea --version to check if installation was successful
    StrCpy $InstallStep "verify"
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

    StrCpy $InstallStep "done"
    !insertmacro SendTelemetry "installer_completed" "" ""
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

    ; Uninstall CEA Desktop
    !insertmacro UninstallCEADesktop

    ; Delete files in install directory
    Delete /REBOOTOK "$INSTDIR\CEA Console.lnk"
    Delete /REBOOTOK "$INSTDIR\CEA Desktop.lnk"
    Delete /REBOOTOK "$INSTDIR\cea-icon.ico"
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
