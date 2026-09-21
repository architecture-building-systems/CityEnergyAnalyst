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

; for scrubbing paths out of the CEA Desktop installer log before it is sent
; as telemetry (see ReportGuiLog / SendTelemetry)
!include "StrFunc.nsh"
${Using:StrFunc} StrRep

Var LauncherExtension
Var InstallStep  ; tracks install progress for telemetry (see SendTelemetry)
Var GuiLogTail   ; last line of the CEA Desktop installer's own log, see ReportGuiLog
Var InstallAttemptCount  ; this run's attempt number since the last success, see ReadInstallAttempts
Var PrevInstallStep      ; step a previous failed attempt died on, if any, see ReadInstallAttempts
Var RepeatFailure        ; "1" if this run failed at the same step as the previous attempt

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

; Reads the tail of the CEA Desktop installer's own breadcrumb log (written by
; CityEnergyAnalyst-GUI's build/installer.nsh as it progresses, so it survives
; even when that installer exits via Quit rather than a catchable failure) into
; the Details pane, and leaves a sanitized, length-capped token describing the
; last stage reached in $GuiLogTail for SendTelemetry. Must not touch $0 (holds
; the real exit code) or $InstallStep - uses $R0-$R3 only.
Function ReportGuiLog
    StrCpy $GuiLogTail ""
    ClearErrors
    FileOpen $R0 "$APPDATA\${CEA_GUI_NAME}\logs\installer.log" r
    ${If} ${Errors}
        DetailPrint "No CEA Desktop installer log found at $APPDATA\${CEA_GUI_NAME}\logs\installer.log"
        Return
    ${EndIf}

    ; only read the last ~8KB so a long log can't stall or flood the Details pane
    FileSeek $R0 0 END $R1
    ${If} $R1 > 8192
        IntOp $R2 $R1 - 8192
        FileSeek $R0 $R2 SET
        FileRead $R0 $R3  # discard the partial line this seek landed inside
    ${Else}
        FileSeek $R0 0 SET
    ${EndIf}

    ; read through to EOF - bounded already by the 8KB seek above, so this
    ; can't run away, but it must not stop early: stopping partway through a
    ; large window would leave $GuiLogTail on an earlier line instead of the
    ; log's actual last line.
    DetailPrint "---- CEA Desktop installer log (tail) ----"
    ${Do}
        ClearErrors
        FileRead $R0 $R3
        ${If} ${Errors}
            ${Break}
        ${EndIf}
        DetailPrint "$R3"
        StrCpy $GuiLogTail "$R3"
    ${Loop}
    FileClose $R0
    DetailPrint "---- end of log: $APPDATA\${CEA_GUI_NAME}\logs\installer.log ----"

    ; defence-in-depth: the log is ours and only ever contains short stage
    ; tokens, but strip anything path-like before this ever reaches telemetry
    ${StrRep} $GuiLogTail "$GuiLogTail" "$INSTDIR" ""
    ${StrRep} $GuiLogTail "$GuiLogTail" "$PROFILE" ""
    ${StrRep} $GuiLogTail "$GuiLogTail" "$APPDATA" ""
    ${StrRep} $GuiLogTail "$GuiLogTail" "$TEMP" ""
    StrCpy $GuiLogTail "$GuiLogTail" 64
FunctionEnd

; Fire-and-forget anonymous installer telemetry: counts installs and reports which
; step a failed install died on, so we don't have to rely on users reporting bugs.
; No-op when POSTHOG_API_KEY was not supplied at build time (local/fork builds).
; Must never fail or delay the install:
;  - Launched with plain (non-blocking) Exec, not nsExec::Exec/ExecWait. A stalled
;    connection (e.g. a firewall that silently drops packets instead of refusing
;    the connection) is not reliably bounded by -TimeoutSec in telemetry.ps1, so
;    the installer must not wait on it at all - it fires the process and moves on.
;  - The script is copied to $TEMP, not $PLUGINSDIR: NSIS deletes $PLUGINSDIR as
;    soon as the installer exits, which would race a detached async process that
;    is still opening the file. $TEMP is not cleaned up by NSIS, so the detached
;    powershell.exe can safely outlive the installer.
;  - The actual network call happens inside telemetry.ps1, wrapped in try/catch
;    with a short timeout, so a dead network or blocked outbound traffic is silent.
; Anonymity: distinct_id is a fresh GUID generated per install in telemetry.ps1 and
; never written to disk; only OS/arch/version/step/error-code/error-detail/retry
; info are sent - no paths, no username, no hostname, and nothing that could
; link two events to the same person or machine (RetryCount/RepeatFailure come
; from a local marker that is never itself transmitted or persisted anywhere
; but this machine - see ReadInstallAttempts). ErrorDetail is a short, sanitized
; token (see ReportGuiLog) describing which stage the bundled CEA Desktop
; installer reached, not free text - pass "" when there is none.
!macro SendTelemetry EventName Step ErrorCode ErrorDetail RetryCount RepeatFailure
    !ifdef POSTHOG_API_KEY
        ${If} ${FileExists} "$TEMP\cea-installer-telemetry.ps1"
            Exec '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$TEMP\cea-installer-telemetry.ps1" -ApiKey "${POSTHOG_API_KEY}" -PostHogHost "${POSTHOG_HOST}" -EventName "${EventName}" -CeaVersion "${VER}" -InstallerStep "${Step}" -ErrorCode "${ErrorCode}" -ErrorDetail "${ErrorDetail}" -RetryCount "${RetryCount}" -RepeatFailure "${RepeatFailure}"'
        ${EndIf}
    !endif
!macroend

; Separate from SendTelemetry above because an uninstall has nothing
; meaningful to put in Step/ErrorCode/ErrorDetail/RetryCount - it reports
; DaysBucket (a coarse "same_day"/"within_week"/"within_month"/"over_month"/
; "unknown" bucket, see WriteInstallRecord/un.ReportUninstall) and whether this
; was ever a completed install, instead. Needs its own copy of the telemetry
; script extracted into the uninstaller (see un.UninstallSection) - the
; original $TEMP copy from install time may be long gone by uninstall time.
!macro SendUninstallTelemetry EventName DaysBucket WasCompletedInstall
    !ifdef POSTHOG_API_KEY
        ${If} ${FileExists} "$TEMP\cea-uninstaller-telemetry.ps1"
            Exec '"$WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$TEMP\cea-uninstaller-telemetry.ps1" -ApiKey "${POSTHOG_API_KEY}" -PostHogHost "${POSTHOG_HOST}" -EventName "${EventName}" -CeaVersion "${VER}" -DaysSinceInstall "${DaysBucket}" -WasCompletedInstall "${WasCompletedInstall}"'
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
!define MUI_COMPONENTSPAGE_TEXT_TOP "This installer sends anonymous statistics used only to improve the installer itself. No personal data (name, files, etc.) are collected. See docs/privacy for details."
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

; Local, never-transmitted bookkeeping so telemetry can tell "one person stuck
; retrying the same step" apart from "many different one-off failures" -
; without ever sending or storing anything that identifies a person or
; machine. Only the derived attempt count and same-step flag are sent; the
; marker file itself never leaves this machine and is deleted on success.

; Reads %APPDATA%\CityEnergyAnalyst\installer-attempts.txt (two lines: attempt
; count, then the step it last failed at) to compute this run's attempt
; number and whether it's retrying after the same failure. A missing or
; unreadable file just means "first try" - must never affect the real install.
Function ReadInstallAttempts
    StrCpy $InstallAttemptCount 1
    StrCpy $PrevInstallStep ""
    ClearErrors
    FileOpen $R0 "$APPDATA\CityEnergyAnalyst\installer-attempts.txt" r
    ${If} ${Errors}
        Return
    ${EndIf}
    FileRead $R0 $R1
    FileRead $R0 $PrevInstallStep
    FileClose $R0
    ClearErrors
    StrCpy $R1 $R1 -2               ; drop the trailing \r\n we wrote
    StrCpy $PrevInstallStep $PrevInstallStep -2
    IntOp $InstallAttemptCount $R1 + 1
FunctionEnd

; Records this run's outcome for a subsequent retry to read via
; ReadInstallAttempts above. Called on every failure with the step reached.
Function WriteInstallAttempt
    ClearErrors
    CreateDirectory "$APPDATA\CityEnergyAnalyst"
    FileOpen $R0 "$APPDATA\CityEnergyAnalyst\installer-attempts.txt" w
    IfErrors writeAttempt_done
    FileWrite $R0 "$InstallAttemptCount$\r$\n"
    FileWrite $R0 "$InstallStep$\r$\n"
    FileClose $R0
    writeAttempt_done:
    ClearErrors
FunctionEnd

; Clears the retry marker on a successful install, so a later reinstall or
; upgrade starts counting attempts fresh rather than inheriting an old streak.
Function ClearInstallAttempts
    ClearErrors
    Delete "$APPDATA\CityEnergyAnalyst\installer-attempts.txt"
    ClearErrors
FunctionEnd

; Written once on a fully successful install; read (and removed) by
; un.ReportUninstall so the uninstaller can report roughly how long ago this
; was installed and whether it ever completed - never a precise date and
; never anything that identifies a person or machine, just local bookkeeping
; the uninstaller reports as a coarse bucket. Day arithmetic here is a
; deliberately approximate serial (year*372 + month*31 + day), not real
; calendar math - fine for coarse buckets, off by a few days across short
; months near a month boundary.
Function WriteInstallRecord
    ${GetTime} "" "L" $R1 $R2 $R3 $R4 $R5 $R6 $R7
    ; $R1=Day $R2=Month $R3=Year (see ceaLogWrite in the GUI installer's
    ; build/installer.nsh for why GetTime's outputs land in this order)
    IntOp $R4 $R3 * 372
    IntOp $R5 $R2 * 31
    IntOp $R4 $R4 + $R5
    IntOp $R4 $R4 + $R1
    ClearErrors
    CreateDirectory "$APPDATA\CityEnergyAnalyst"
    FileOpen $R0 "$APPDATA\CityEnergyAnalyst\installer-record.txt" w
    IfErrors writeRecord_done
    FileWrite $R0 "$R4$\r$\n"
    FileClose $R0
    writeRecord_done:
    ClearErrors
FunctionEnd

Function .onInstFailed
    StrCpy $RepeatFailure "0"
    ${If} $PrevInstallStep != ""
    ${AndIf} $PrevInstallStep == $InstallStep
        StrCpy $RepeatFailure "1"
    ${EndIf}
    Call WriteInstallAttempt
    !insertmacro SendTelemetry "installer_failed" "$InstallStep" "$0" "$GuiLogTail" "$InstallAttemptCount" "$RepeatFailure"

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
    Call ReadInstallAttempts

    !ifdef POSTHOG_API_KEY
        File "/oname=$TEMP\cea-installer-telemetry.ps1" "telemetry.ps1"
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

    # Run GUI Setup. /CEABUNDLE tells the GUI installer it was launched from here
    # (see CityEnergyAnalyst-GUI's build/installer.nsh), so its own telemetry can
    # tell a bundled install apart from a standalone install or auto-update.
    DetailPrint "Installing CEA Desktop"
    ExecWait '"$INSTDIR\gui_setup.exe" /CEABUNDLE /S /D="$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"' $0
    DetailPrint "CEA Desktop installer returned: $0"
    ${If} "$0" != "0"
        Call ReportGuiLog
        Abort "Installation failed - see Details. CEA Desktop installer log: $APPDATA\${CEA_GUI_NAME}\logs\installer.log"
    ${EndIf}
    ${IfNot} ${FileExists} "$INSTDIR\${CEA_GUI_INSTALL_FOLDER}"
        Call ReportGuiLog
        ; $0 still holds "0" from the ExecWait above (a real success code, not a
        ; failure), so overwrite it before SendTelemetry (via .onInstFailed)
        ; reports it as error_code - otherwise this failure would look like a
        ; successful install.
        StrCpy $0 "gui_dir_missing"
        Abort "Installation failed: Something went wrong with CEA Desktop setup. Install directory not found. CEA Desktop installer log: $APPDATA\${CEA_GUI_NAME}\logs\installer.log"
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
    Call ClearInstallAttempts
    Call WriteInstallRecord
    !insertmacro SendTelemetry "installer_completed" "$InstallStep" "" "" "$InstallAttemptCount" "0"
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

; Reads the marker WriteInstallRecord left behind (if any) to report roughly
; how long ago this was installed and whether it was ever a fully completed
; install, bucketed coarsely - never a precise date, never anything that
; identifies a person or machine. A missing file just means this uninstaller
; is running against an install that never completed (e.g. a leftover
; uninstaller from a partial install a user ran manually).
Function un.ReportUninstall
    StrCpy $R5 "unknown"
    StrCpy $R6 "0"
    ClearErrors
    FileOpen $R0 "$APPDATA\CityEnergyAnalyst\installer-record.txt" r
    ${If} ${Errors}
        Goto un_reportUninstall_send
    ${EndIf}
    FileRead $R0 $R1
    FileClose $R0
    ClearErrors
    StrCpy $R1 $R1 -2
    StrCpy $R6 "1"

    ${GetTime} "" "L" $R2 $R3 $R4 $R7 $R8 $R9 $R8
    ; $R2=Day $R3=Month $R4=Year (today) - see WriteInstallRecord
    IntOp $R7 $R4 * 372
    IntOp $R8 $R3 * 31
    IntOp $R7 $R7 + $R8
    IntOp $R7 $R7 + $R2
    IntOp $R7 $R7 - $R1   ; approx days since install

    ${If} $R7 <= 0
        StrCpy $R5 "same_day"
    ${ElseIf} $R7 <= 7
        StrCpy $R5 "within_week"
    ${ElseIf} $R7 <= 31
        StrCpy $R5 "within_month"
    ${Else}
        StrCpy $R5 "over_month"
    ${EndIf}

    un_reportUninstall_send:
    Delete "$APPDATA\CityEnergyAnalyst\installer-record.txt"
    Delete "$APPDATA\CityEnergyAnalyst\installer-attempts.txt"
    !insertmacro SendUninstallTelemetry "uninstaller_run" "$R5" "$R6"
FunctionEnd

Function un.UninstallSection
    !ifdef POSTHOG_API_KEY
        File "/oname=$TEMP\cea-uninstaller-telemetry.ps1" "telemetry.ps1"
    !endif
    Call un.ReportUninstall

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
