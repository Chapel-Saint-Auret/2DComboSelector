#define AppName "2DComboSelector"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "2DComboSelector contributors"
#define AppURL "https://github.com/Chapel-Saint-Auret/2DComboSelector"
#define AppExeName "combo_selector.exe"

[Setup]
AppId={{918030FA-71F2-4B0A-997A-65536BBBEA20}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=2DComboSelector-{#AppVersion}-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=src\combo_selector\resources\icons\app_icon.ico
WizardImageFile=src\combo_selector\resources\icons\installer_wizard.bmp

[Files]
Source: "dist\combo_selector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; AppUserModelID: "ChapelSaintAuret.2DComboSelector"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; AppUserModelID: "ChapelSaintAuret.2DComboSelector"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
