; Inno Setup script for BuffetApp
; Build this after running PyInstaller onedir build

#ifndef MyAppVersion
	#define MyAppVersion "1.0.0"
#endif

[Setup]
AppName=BuffetApp
AppVersion={#MyAppVersion}
DefaultDirName={pf}\BuffetApp
DefaultGroupName=BuffetApp
; OutputDir relative to this .iss directory -> installer\dist
OutputDir=dist
OutputBaseFilename=BuffetApp_{#MyAppVersion}_Setup
Compression=lzma
SolidCompression=no
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=no
WizardStyle=modern
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Copy the PyInstaller onedir output (adjust Name if different)
Source: "..\dist\BuffetApp\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BuffetApp"; Filename: "{app}\\BuffetApp.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\BuffetApp"; Filename: "{app}\\BuffetApp.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Run]
Filename: "{app}\\BuffetApp.exe"; Description: "Iniciar BuffetApp"; Flags: nowait postinstall skipifsilent
