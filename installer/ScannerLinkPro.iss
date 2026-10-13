; Scanner Link Pro: SCSI/USB to Scanner
; Copyright (C) 2026 ShinRalexis
; SPDX-License-Identifier: GPL-2.0-or-later
; Installatore di Scanner Link Pro (Inno Setup 6.5 o successivo).
; Si costruisce con installer\build.ps1: prima PyInstaller (build\dist\ScannerLinkPro), poi questo script.
;
; Cosa fa:
;   - installa il programma in Programmi, con menu Start, icona sul Desktop (facoltativa) e disinstallatore;
;   - installa usbipd-win se manca (passa l'adattatore USB al Linux interno);
;   - installa WSL se manca (poi serve un riavvio);
;   - copia il backup del Linux interno: il programma lo importa al primo avvio, nel profilo di chi lo usa;
;   - passa al programma la lingua scelta qui.
; Non contiene il driver originale Logitec (riferimenti\), che non è nostro.

#define AppName "Scanner Link Pro"
#define AppVersion "1.0.2"
#define AppExe "ScannerLinkPro.exe"
#define Usbipd "usbipd-win_5.3.0_x64.msi"
#define Root ".."

[Setup]
AppId={{6E1B3F0A-8C2D-4E57-9A41-2F7C5B9D3E10}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=ShinRalexis
AppPublisherURL=https://github.com/ShinRalexis
AppSupportURL=https://github.com/ShinRalexis/scanner-link-pro
AppComments=SCSI/USB to Scanner
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
; solo Windows x64: su ARM il pacchetto di usbipd-win incluso non funzionerebbe
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.19041
OutputDir=output
OutputBaseFilename=ScannerLinkPro-Setup-{#AppVersion}
SetupIconFile={#Root}\app\icona.ico
LicenseFile={#Root}\LICENSE
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
WizardSmallImageFile=wizard_small_55.bmp,wizard_small_110.bmp
WizardImageFile=wizard_164.bmp,wizard_328.bmp
ShowLanguageDialog=yes
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName}: SCSI/USB to Scanner
CloseApplications=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "ja"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "ko"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "zh"; MessagesFile: "lang\ChineseSimplified.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
en.AppDescription=Use old Epson SCSI scanners on modern Windows through a Logitec USB-SCSI adapter
it.AppDescription=Usa i vecchi scanner Epson SCSI su Windows moderno tramite un adattatore Logitec USB-SCSI
es.AppDescription=Usa los antiguos escáneres Epson SCSI en Windows moderno con un adaptador Logitec USB-SCSI
de.AppDescription=Alte Epson-SCSI-Scanner unter modernem Windows mit einem Logitec-USB-SCSI-Adapter nutzen
fr.AppDescription=Utilisez les anciens scanners Epson SCSI sous Windows moderne via un adaptateur Logitec USB-SCSI
ja.AppDescription=Logitec USB-SCSI アダプターで、古い Epson SCSI スキャナーを最新の Windows で使えます
ko.AppDescription=Logitec USB-SCSI 어댑터로 오래된 Epson SCSI 스캐너를 최신 Windows에서 사용합니다
zh.AppDescription=通过 Logitec USB-SCSI 适配器，在新版 Windows 上使用旧款 Epson SCSI 扫描仪
ru.AppDescription=Старые сканеры Epson SCSI в современной Windows через адаптер Logitec USB-SCSI

en.StatusUsbipd=Installing usbipd-win (passes the USB adapter to the built-in Linux)...
it.StatusUsbipd=Installazione di usbipd-win (passa l'adattatore USB al Linux interno)...
es.StatusUsbipd=Instalando usbipd-win (pasa el adaptador USB al Linux interno)...
de.StatusUsbipd=usbipd-win wird installiert (reicht den USB-Adapter an das interne Linux weiter)...
fr.StatusUsbipd=Installation de usbipd-win (transmet l'adaptateur USB au Linux intégré)...
ja.StatusUsbipd=usbipd-win をインストールしています（USB アダプターを内蔵 Linux に渡します）...
ko.StatusUsbipd=usbipd-win 설치 중(USB 어댑터를 내장 Linux로 전달합니다)...
zh.StatusUsbipd=正在安装 usbipd-win（将 USB 适配器交给内置 Linux）...
ru.StatusUsbipd=Установка usbipd-win (передает USB-адаптер встроенному Linux)...

en.StatusWSL=Installing WSL, the Windows Subsystem for Linux...
it.StatusWSL=Installazione di WSL, il sottosistema Linux di Windows...
es.StatusWSL=Instalando WSL, el subsistema de Windows para Linux...
de.StatusWSL=WSL, das Windows-Subsystem für Linux, wird installiert...
fr.StatusWSL=Installation de WSL, le sous-système Windows pour Linux...
ja.StatusWSL=WSL（Windows Subsystem for Linux）をインストールしています...
ko.StatusWSL=WSL(Linux용 Windows 하위 시스템) 설치 중...
zh.StatusWSL=正在安装 WSL（适用于 Linux 的 Windows 子系统）...
ru.StatusWSL=Установка WSL, подсистемы Windows для Linux...

en.WSLFailed=WSL could not be installed automatically. Run "wsl --install" as administrator, restart the computer, then start Scanner Link Pro.
it.WSLFailed=Non sono riuscito a installare WSL. Esegui "wsl --install" da amministratore, riavvia il computer e poi avvia Scanner Link Pro.
es.WSLFailed=No se pudo instalar WSL automáticamente. Ejecuta "wsl --install" como administrador, reinicia el equipo y luego abre Scanner Link Pro.
de.WSLFailed=WSL konnte nicht automatisch installiert werden. "wsl --install" als Administrator ausführen, den Computer neu starten und dann Scanner Link Pro öffnen.
fr.WSLFailed=WSL n'a pas pu être installé automatiquement. Exécutez « wsl --install » en administrateur, redémarrez l'ordinateur, puis lancez Scanner Link Pro.
ja.WSLFailed=WSL を自動でインストールできませんでした。管理者として「wsl --install」を実行し、PC を再起動してから Scanner Link Pro を起動してください。
ko.WSLFailed=WSL을 자동으로 설치하지 못했습니다. 관리자 권한으로 "wsl --install"을 실행하고 컴퓨터를 다시 시작한 뒤 Scanner Link Pro를 실행하세요.
zh.WSLFailed=无法自动安装 WSL。请以管理员身份运行“wsl --install”，重启电脑后再启动 Scanner Link Pro。
ru.WSLFailed=Не удалось автоматически установить WSL. Выполните «wsl --install» от имени администратора, перезагрузите компьютер и запустите Scanner Link Pro.

en.UsbipdFailed=usbipd-win could not be installed. You can install it later from https://github.com/dorssel/usbipd-win
it.UsbipdFailed=Non sono riuscito a installare usbipd-win. Puoi installarlo dopo da https://github.com/dorssel/usbipd-win
es.UsbipdFailed=No se pudo instalar usbipd-win. Puedes instalarlo después desde https://github.com/dorssel/usbipd-win
de.UsbipdFailed=usbipd-win konnte nicht installiert werden. Es lässt sich später von https://github.com/dorssel/usbipd-win installieren
fr.UsbipdFailed=usbipd-win n'a pas pu être installé. Vous pourrez l'installer plus tard depuis https://github.com/dorssel/usbipd-win
ja.UsbipdFailed=usbipd-win をインストールできませんでした。後で https://github.com/dorssel/usbipd-win からインストールできます
ko.UsbipdFailed=usbipd-win을 설치하지 못했습니다. 나중에 https://github.com/dorssel/usbipd-win 에서 설치할 수 있습니다
zh.UsbipdFailed=无法安装 usbipd-win。之后可从 https://github.com/dorssel/usbipd-win 安装
ru.UsbipdFailed=Не удалось установить usbipd-win. Его можно установить позже: https://github.com/dorssel/usbipd-win

en.FirstRun=On first start the program sets up its built-in Linux (about one minute). Connect the Logitec adapter and switch the scanner on before starting it.
it.FirstRun=Al primo avvio il programma prepara il suo Linux interno (circa un minuto). Collega l'adattatore Logitec e accendi lo scanner prima di avviarlo.
es.FirstRun=En el primer inicio el programa prepara su Linux interno (alrededor de un minuto). Conecta el adaptador Logitec y enciende el escáner antes de abrirlo.
de.FirstRun=Beim ersten Start richtet das Programm sein internes Linux ein (etwa eine Minute). Vor dem Start den Logitec-Adapter anschließen und den Scanner einschalten.
fr.FirstRun=Au premier démarrage, le programme prépare son Linux intégré (environ une minute). Branchez l'adaptateur Logitec et allumez le scanner avant de le lancer.
ja.FirstRun=初回起動時に、プログラムは内蔵 Linux を準備します（約1分）。起動する前に Logitec アダプターを接続し、スキャナーの電源を入れてください。
ko.FirstRun=처음 실행할 때 프로그램이 내장 Linux를 준비합니다(약 1분). 실행하기 전에 Logitec 어댑터를 연결하고 스캐너를 켜세요.
zh.FirstRun=首次启动时，程序会准备其内置 Linux（约一分钟）。启动前请连接 Logitec 适配器并打开扫描仪。
ru.FirstRun=При первом запуске программа подготовит встроенный Linux (около минуты). Перед запуском подключите адаптер Logitec и включите сканер.

en.UninstallLinux=Also remove the built-in Linux of Scanner Link Pro (WSL distribution GT10000, about 250 MB)? Settings, calibration and scans are kept.
it.UninstallLinux=Rimuovere anche il Linux interno di Scanner Link Pro (distribuzione WSL GT10000, circa 250 MB)? Impostazioni, calibrazione e scansioni restano.
es.UninstallLinux=¿Quitar también el Linux interno de Scanner Link Pro (distribución WSL GT10000, unos 250 MB)? Se conservan la configuración, la calibración y los escaneos.
de.UninstallLinux=Auch das interne Linux von Scanner Link Pro entfernen (WSL-Distribution GT10000, etwa 250 MB)? Einstellungen, Kalibrierung und Scans bleiben erhalten.
fr.UninstallLinux=Supprimer aussi le Linux intégré de Scanner Link Pro (distribution WSL GT10000, environ 250 Mo) ? Les réglages, le calibrage et les numérisations sont conservés.
ja.UninstallLinux=Scanner Link Pro の内蔵 Linux（WSL ディストリビューション GT10000、約 250 MB）も削除しますか？設定、キャリブレーション、スキャンは残ります。
ko.UninstallLinux=Scanner Link Pro의 내장 Linux(WSL 배포판 GT10000, 약 250 MB)도 제거할까요? 설정, 캘리브레이션, 스캔은 유지됩니다.
zh.UninstallLinux=是否同时删除 Scanner Link Pro 的内置 Linux（WSL 发行版 GT10000，约 250 MB）？设置、校准和扫描结果会保留。
ru.UninstallLinux=Удалить также встроенный Linux Scanner Link Pro (дистрибутив WSL GT10000, около 250 МБ)? Настройки, калибровка и отсканированные файлы сохранятся.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "build\dist\ScannerLinkPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Root}\gt10000\*.py"; DestDir: "{app}\gt10000"; Flags: ignoreversion
Source: "{#Root}\linux\GT10000-debian.tar"; DestDir: "{app}\linux"; Flags: ignoreversion
Source: "{#Root}\setup\provision.sh"; DestDir: "{app}\setup"; Flags: ignoreversion
Source: "{#Root}\LEGGIMI.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "{#Root}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "redist\{#Usbipd}"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; Comment: "{cm:AppDescription}"; AppUserModelID: "ScannerLinkPro"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Comment: "{cm:AppDescription}"; AppUserModelID: "ScannerLinkPro"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent; Check: not WSLNeedsRestart

[UninstallDelete]
Type: filesandordirs; Name: "{app}\gt10000\__pycache__"

[Code]
var
  RestartForWSL: Boolean;

function Sys(const Path: String): String;
begin
  Result := ExpandConstant('{sys}\') + Path;
end;

function RunHidden(const Exe, Params: String): Integer;
var
  Code: Integer;
begin
  if not Exec(Exe, Params, '', SW_HIDE, ewWaitUntilTerminated, Code) then
    Code := -1;
  Result := Code;
end;

function WSLReady(): Boolean;
begin
  Result := RunHidden(Sys('wsl.exe'), '--status') = 0;
end;

function UsbipdInstalled(): Boolean;
begin
  Result := FileExists(ExpandConstant('{commonpf64}\usbipd-win\usbipd.exe'));
end;

function WSLNeedsRestart(): Boolean;
begin
  Result := RestartForWSL;
end;

function NeedRestart(): Boolean;
begin
  Result := RestartForWSL;
end;

{ lingua scelta qui = lingua del programma, se non ne ha già una }
procedure SaveLanguage();
var
  Dir, FileName: String;
begin
  Dir := ExpandConstant('{userappdata}\GT10000Scanner');
  FileName := Dir + '\impostazioni.json';
  if not FileExists(FileName) then
  begin
    ForceDirectories(Dir);
    SaveStringToFile(FileName, '{"language": "' + ActiveLanguage() + '"}', False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not UsbipdInstalled() then
    begin
      WizardForm.StatusLabel.Caption := CustomMessage('StatusUsbipd');
      if RunHidden(Sys('msiexec.exe'), '/i "' + ExpandConstant('{tmp}\{#Usbipd}') + '" /qn /norestart') <> 0 then
        if not UsbipdInstalled() then
          SuppressibleMsgBox(CustomMessage('UsbipdFailed'), mbError, MB_OK, IDOK);
    end;
    if not WSLReady() then
    begin
      WizardForm.StatusLabel.Caption := CustomMessage('StatusWSL');
      if RunHidden(Sys('wsl.exe'), '--install --no-distribution') = 0 then
        RestartForWSL := True
      else
        SuppressibleMsgBox(CustomMessage('WSLFailed'), mbError, MB_OK, IDOK);
    end;
    SaveLanguage();
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
    WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption + #13#10#13#10 + CustomMessage('FirstRun');
end;

{ il Linux interno esiste? WSL annota le distribuzioni dell'utente nel registro }
function DistroRegistered(): Boolean;
var
  Keys: TArrayOfString;
  Name: String;
  I: Integer;
begin
  Result := False;
  if RegGetSubkeyNames(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Lxss', Keys) then
    for I := 0 to GetArrayLength(Keys) - 1 do
      if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Lxss\' + Keys[I],
                             'DistributionName', Name) and (Name = 'GT10000') then
        Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep <> usUninstall then
    Exit;
  if DistroRegistered() and
     (SuppressibleMsgBox(CustomMessage('UninstallLinux'), mbConfirmation, MB_YESNO, IDNO) = IDYES) then
  begin
    RunHidden(Sys('wsl.exe'), '--unregister GT10000');
    DelTree(ExpandConstant('{localappdata}\ScannerLinkPro'), True, True, True);
  end;
end;
