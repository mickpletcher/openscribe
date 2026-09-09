#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "."
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
AppId={{D449BDE3-D28F-422C-9EAA-D85784F2F5AC}
AppName=OpenScribe
AppVersion={#AppVersion}
AppPublisher=Mick
AppPublisherURL=https://github.com/mickpletcher/openscribe
AppSupportURL=https://github.com/mickpletcher/openscribe/issues
AppUpdatesURL=https://github.com/mickpletcher/openscribe/releases
DefaultDirName={localappdata}\Programs\OpenScribe
DefaultGroupName=OpenScribe
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=OpenScribe-Setup-{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\OpenScribe.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=no
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#AppVersion}
LicenseFile={#SourceDir}\LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OpenScribe"; Filename: "{app}\OpenScribe.exe"
Name: "{group}\OpenScribe command line"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoExit -NoLogo -Command Set-Alias openscribe '{app}\openscribe-cli.exe'; & openscribe --help"; WorkingDir: "{userdocs}"
Name: "{group}\Uninstall OpenScribe"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OpenScribe"; Filename: "{app}\OpenScribe.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OpenScribe.exe"; Description: "Open OpenScribe"; Flags: nowait postinstall skipifsilent
