; Скрипт Inno Setup для создания инсталлятора ChatList
; Версия: 1.0.0

#define AppName "ChatList"
#define AppVersion "1.0.0"
#define AppPublisher "ChatList"
#define AppURL "https://github.com/Artser/ChatList"
#define AppExeName "ChatList_v1.0.0.exe"
#define AppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
; Основные настройки
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer
OutputBaseFilename=ChatList_Setup_v{#AppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; Информация о программе
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} - Приложение для сравнения ответов разных нейросетей
VersionInfoCopyright=Copyright (C) 2024

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Основной исполняемый файл
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Иконка приложения
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
; База данных (если нужно создать пустую)
; Source: "chatlist.db"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Удаление базы данных при удалении программы (опционально)
; Type: files; Name: "{app}\chatlist.db"
; Удаление логов при удалении программы (опционально)
; Type: filesandordirs; Name: "{app}\logs"
; Удаление настроек при удалении программы (опционально)
; Type: files; Name: "{app}\*.db"

[Code]
// Кастомный код для проверок и действий при установке/удалении
procedure InitializeUninstallProgressForm();
begin
  // Можно добавить кастомные действия при удалении
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Можно добавить проверки перед установкой
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  case CurUninstallStep of
    usUninstall:
      begin
        // Действия перед удалением
        // Можно добавить запрос подтверждения удаления данных
      end;
    usPostUninstall:
      begin
        // Действия после удаления
      end;
  end;
end;

