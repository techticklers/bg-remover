; Inno Setup Script for Bulk Background Remover
; Builds single installer: BulkBackgroundRemover_Setup.exe

#define MyAppName "Bulk Background Remover"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "Localhost Photo Tools"
#define MyAppURL "http://127.0.0.1:8501"
#define MyAppExeName "BulkBackgroundRemover.exe"

[Setup]
AppId={{E68F550B-78AE-4DA6-B10E-85F7560B01D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist_installer
OutputBaseFilename=BulkBackgroundRemover_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Source files bundled from PyInstaller distribution folder
Source: "dist\BulkBackgroundRemover\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
