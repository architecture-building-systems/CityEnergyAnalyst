[Setup]
AppName=CEAforArcGIS
AppVersion=1.5
DefaultDirName={pf}\CEAforArcGIS

[Files]
Source: "site-packages\*"; DestDir: "{app}\site-packages"; Flags: ignoreversion recursesubdirs

[PreCompile]
Name: "copy_library.bat";
