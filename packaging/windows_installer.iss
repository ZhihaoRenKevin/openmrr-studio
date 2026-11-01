; Inno Setup 6 Installer Script for OpenMRR Studio (Windows 10 / 11 x64)
; Installs cleanly without requiring Administrator privileges, creates Start Menu
; and optional Desktop shortcuts, and provides standard Windows Add/Remove Programs uninstall.

#ifndef MyAppVersion
  #define MyAppVersion "3.3.0"
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "OpenMRR-Studio-v3.3.0-Windows-Setup-x64"
#endif

[Setup]
AppId={{8D4F6A2E-5C31-4B9E-A18F-90E12C4D77B3}
AppName=OpenMRR Studio
AppVersion={#MyAppVersion}
AppPublisher=Zhihao Ren
AppPublisherURL=https://github.com/ZhihaoRenKevin/openmrr-studio
AppSupportURL=https://github.com/ZhihaoRenKevin/openmrr-studio/issues
DefaultDirName={autopf}\OpenMRR Studio
DefaultGroupName=OpenMRR Studio
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=openmrr.ico
UninstallDisplayIcon={app}\OpenMRR Studio.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\OpenMRR Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\OpenMRR Studio"; Filename: "{app}\OpenMRR Studio.exe"
Name: "{autodesktop}\OpenMRR Studio"; Filename: "{app}\OpenMRR Studio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OpenMRR Studio.exe"; Description: "{cm:LaunchProgram,OpenMRR Studio}"; Flags: nowait postinstall skipifsilent
