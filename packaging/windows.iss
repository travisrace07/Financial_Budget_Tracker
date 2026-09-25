; Compile from the repository root: ISCC.exe packaging\windows.iss
[Setup]
AppId={{B77A2738-BF68-46F9-BBA3-1482D7E590B4}
AppName=Ledger
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\Ledger
DefaultGroupName=Ledger
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Ledger-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Ledger.exe
CloseApplications=yes

[Files]
Source: "..\dist\Ledger\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Ledger"; Filename: "{app}\Ledger.exe"
Name: "{autodesktop}\Ledger"; Filename: "{app}\Ledger.exe"

[Run]
Filename: "{app}\Ledger.exe"; Description: "Open Ledger"; Flags: nowait postinstall skipifsilent
