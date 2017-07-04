# get_version.nsi is a helper script for cityenergyanalyst.nsi: it reads the cea/__init__.py file and extracts the
# version identifier to a file (version.nsh)

OutFile "get_version.exe"
SilentInstall silent
RequestExecutionLevel user

Section

    FileOpen $R0 "$EXEDIR\..\cea\__init__.py" r
    FileRead $R0 $R1
    FileClose $R0
    Push $R1
    Call GetInQuotes
    Pop $R1  # $R1 now contains the version

    # Write it to a !define for use in main script
    FileOpen $R0 "$EXEDIR\cea_version.txt" w
    FileWrite $R0 '!define VER "$R1"'
    FileClose $R0

SectionEnd

Function GetInQuotes
# this function is copied from here: http://nsis.sourceforge.net/GetInQuotes:_Get_string_from_between_quotes
    Exch $R0
    Push $R1
    Push $R2
    Push $R3

    StrCpy $R2 -1
    IntOp $R2 $R2 + 1
    StrCpy $R3 $R0 1 $R2
    StrCmp $R3 "" 0 +3
    StrCpy $R0 ""
    Goto Done
    StrCmp $R3 '"' 0 -5

    IntOp $R2 $R2 + 1
    StrCpy $R0 $R0 "" $R2

    StrCpy $R2 0
    IntOp $R2 $R2 + 1
    StrCpy $R3 $R0 1 $R2
    StrCmp $R3 "" 0 +3
    StrCpy $R0 ""
    Goto Done
    StrCmp $R3 '"' 0 -5

    StrCpy $R0 $R0 $R2
    Done:

    Pop $R3
    Pop $R2
    Pop $R1
    Exch $R0
FunctionEnd