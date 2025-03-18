#define MyAppName "Canvas下载助手"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "Canvas下载助手.exe"
#define PythonVersion "3.11.4"
#define PythonInstallerName "python-3.11.4-amd64.exe"
#define PythonDownloadURL "https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe"

[Setup]
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=Canvas下载助手安装包
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
PrivilegesRequired=admin

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 主程序文件
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; Python安装程序
Source: "{tmp}\{#PythonInstallerName}"; DestDir: "{tmp}"; Flags: external deleteafterinstall; ExternalSize: 27880448

; 安装脚本
Source: "install_dependencies.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 可选的运行程序
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// 定义Python注册表位置
const
  PYTHON_KEY = 'Software\Python\PythonCore\3.11\InstallPath';
  PYTHON_KEY_WOW64 = 'Software\Wow6432Node\Python\PythonCore\3.11\InstallPath';

var
  PythonInstallationNeeded: Boolean;
  DependenciesPage: TOutputMsgMemoWizardPage;
  DownloadPage: TDownloadWizardPage;
  
// 检查Python是否已安装
function IsPythonInstalled(): Boolean;
var
  InstallPath: String;
begin
  // 检查标准注册表位置
  Result := RegQueryStringValue(HKLM, PYTHON_KEY, '', InstallPath) or
            RegQueryStringValue(HKCU, PYTHON_KEY, '', InstallPath) or
            RegQueryStringValue(HKLM, PYTHON_KEY_WOW64, '', InstallPath) or
            RegQueryStringValue(HKCU, PYTHON_KEY_WOW64, '', InstallPath);
  
  // 如果找到注册表项，进一步检查python.exe是否存在
  if Result then
    Result := FileExists(AddBackslash(InstallPath) + 'python.exe');
end;

// 检查canvassyncer是否已安装
function IsCanvasSyncerInstalled(): Boolean;
var
  PipOutput: AnsiString;
  ExecResult: Integer;
  PythonPath: String;
begin
  Result := False;
  
  // 如果Python已安装，则检查canvassyncer
  if IsPythonInstalled() then
  begin
    if RegQueryStringValue(HKLM, PYTHON_KEY, '', PythonPath) or
       RegQueryStringValue(HKCU, PYTHON_KEY, '', PythonPath) or
       RegQueryStringValue(HKLM, PYTHON_KEY_WOW64, '', PythonPath) or
       RegQueryStringValue(HKCU, PYTHON_KEY_WOW64, '', PythonPath) then
    begin
      PythonPath := AddBackslash(PythonPath);
      
      // 检查canvassyncer模块是否已安装
      if Exec(PythonPath + 'python.exe', '-c "import canvassyncer; print(''installed'')"', '', SW_HIDE, ewWaitUntilTerminated, ExecResult) then
      begin
        Result := (ExecResult = 0);
      end;
    end;
  end;
end;

// 创建自定义表单
procedure InitializeWizard;
begin
  // 检查是否需要安装Python
  PythonInstallationNeeded := not IsPythonInstalled();

  // 创建下载页面
  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);

  // 创建依赖信息页面
  DependenciesPage := CreateOutputMsgMemoPage(wpReady, '环境检查', 
    '安装程序将检查并安装必要的依赖', 
    '安装程序将执行以下操作:', '');
end;

// 更新依赖信息页面
procedure CurPageChanged(CurPageID: Integer);
var
  Info: String;
begin
  if CurPageID = DependenciesPage.ID then
  begin
    Info := '';
    
    // 检查Python
    if IsPythonInstalled() then
      Info := Info + '- Python: 已安装' + #13#10
    else
      Info := Info + '- Python: 未安装，将自动安装' + #13#10;
      
    // 检查canvassyncer
    if IsCanvasSyncerInstalled() then
      Info := Info + '- canvassyncer: 已安装' + #13#10
    else
      Info := Info + '- canvassyncer: 未安装，将自动安装' + #13#10;
      
    // 检查PyQt5
    if Exec('python', '-c "import PyQt5; print(''installed'')"', '', SW_HIDE, ewWaitUntilTerminated, 0) then
      Info := Info + '- PyQt5: 已安装' + #13#10
    else
      Info := Info + '- PyQt5: 未安装，将自动安装' + #13#10;
      
    Info := Info + #13#10 + '点击"下一步"继续安装并自动安装缺少的依赖。';
    
    DependenciesPage.RichEditViewer.Lines.Text := Info;
  end;
end;

// 下载文件
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = wpReady then
  begin
    if PythonInstallationNeeded then
    begin
      DownloadPage.Clear;
      DownloadPage.Add('{#PythonDownloadURL}', '{#PythonInstallerName}', '');
      DownloadPage.Show;
      
      try
        try
          DownloadPage.Download;
        except
          Log('下载Python安装程序时出错: ' + GetExceptionMessage);
          MsgBox('下载Python安装程序失败。请确保您的网络连接正常并重试。', mbError, MB_OK);
          Result := False;
        end;
      finally
        DownloadPage.Hide;
      end;
    end;
  end;
end;

// 安装Python
procedure InstallPython;
var
  ErrorCode: Integer;
  PythonArgs: String;
begin
  PythonArgs := '/passive InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1';
  
  Log('开始安装Python...');
  if not Exec(ExpandConstant('{tmp}\{#PythonInstallerName}'), PythonArgs, '', SW_SHOW, ewWaitUntilTerminated, ErrorCode) then
  begin
    Log('安装Python时发生错误，错误代码: ' + IntToStr(ErrorCode));
    MsgBox('安装Python时发生错误。请手动安装Python 3.11.4后再运行此安装程序。', mbError, MB_OK);
  end
  else
    Log('Python安装完成');
end;

// 安装依赖
procedure InstallDependencies;
var
  ErrorCode: Integer;
  InstallerPath: String;
begin
  InstallerPath := ExpandConstant('{app}\install_dependencies.bat');
  
  Log('开始安装Python依赖...');
  if not Exec(InstallerPath, '', '', SW_SHOW, ewWaitUntilTerminated, ErrorCode) then
  begin
    Log('安装依赖时发生错误，错误代码: ' + IntToStr(ErrorCode));
    MsgBox('安装Python依赖时发生错误。您可能需要手动运行安装脚本。', mbError, MB_OK);
  end
  else
    Log('依赖安装完成');
end;

// 安装后的操作
procedure CurStepChanged(CurStep: TSetupStep);
begin
  // 在安装完成后安装依赖
  if CurStep = ssPostInstall then
  begin
    Log('安装后处理开始...');
    
    // 如果需要，安装Python
    if PythonInstallationNeeded then
    begin
      Log('需要安装Python');
      InstallPython;
    end;
    
    // 安装Python依赖
    InstallDependencies;
  end;
end; 