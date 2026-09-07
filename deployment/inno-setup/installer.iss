; ============================================================================
; SIGMA — Script Inno Setup
; Produit Setup_SIGMA.exe : installe le serveur, PostgreSQL embarqué, le
; frontend compilé, et enregistre le tout comme service Windows via NSSM
; (cf cahier des charges §22 et §29).
;
; Compilation :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; (fait automatiquement par .github/workflows/build-windows-installer.yml)
;
; Attend un dossier "dist_staging" (voir ce workflow) contenant :
;   SigmaServer.exe, _internal\, pgsql\, webapp\, nssm.exe
; ============================================================================

#define MyAppName "SIGMA"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Votre établissement"
#define MyAppExeName "SigmaServer.exe"
#define ServiceName "SIGMAServer"
#define HttpPort "8000"

[Setup]
AppId={{8F2B1A6E-3C6D-4E9A-9C1E-SIGMA00001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SIGMA
DefaultGroupName=SIGMA
DisableProgramGroupPage=yes
OutputBaseFilename=Setup_SIGMA
OutputDir=Output
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "dist_staging\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\SIGMA (ouvrir dans le navigateur)"; Filename: "http://localhost:{#HttpPort}"
Name: "{group}\Désinstaller SIGMA"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SIGMA"; Filename: "http://localhost:{#HttpPort}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

; ----------------------------------------------------------------------------
; Installation du service Windows via NSSM.
; Le service démarre automatiquement au boot (§22 : pas de fenêtre CMD requise).
; ----------------------------------------------------------------------------
[Run]
Filename: "{app}\nssm.exe"; Parameters: "install {#ServiceName} ""{app}\{#MyAppExeName}"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppDirectory ""{app}"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} DisplayName ""SIGMA Server"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} Description ""Serveur central SIGMA (API + base de données embarquée)."""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} Start SERVICE_AUTO_START"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppStdout ""C:\ProgramData\SIGMA\logs\service-stdout.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppStderr ""C:\ProgramData\SIGMA\logs\service-stderr.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#ServiceName} AppRotateFiles 1"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "start {#ServiceName}"; Flags: runhidden
Filename: "http://localhost:{#HttpPort}"; Description: "Ouvrir SIGMA dans le navigateur"; Flags: postinstall shellexec skipifsilent nowait

; ----------------------------------------------------------------------------
; Désinstallation : arrête et retire le service. Les données (base de données,
; identifiants générés, journaux) restent dans C:\ProgramData\SIGMA — elles ne
; sont JAMAIS supprimées automatiquement, pour éviter toute perte accidentelle
; de dossiers d'élèves ou de paiements. L'administrateur peut les effacer
; manuellement s'il le souhaite après avoir vérifié ses sauvegardes.
; ----------------------------------------------------------------------------
[UninstallRun]
Filename: "{app}\nssm.exe"; Parameters: "stop {#ServiceName}"; Flags: runhidden; RunOnceId: "StopService"
Filename: "{app}\nssm.exe"; Parameters: "remove {#ServiceName} confirm"; Flags: runhidden; RunOnceId: "RemoveService"

[UninstallDelete]
; Ne supprime que les fichiers du programme, jamais {commonappdata}\SIGMA (les données).
Type: filesandordirs; Name: "{app}"
