# 在Windows系统上打包Canvas下载助手

以下是在Windows系统上为Canvas下载助手创建独立安装包的步骤：

## 必要准备

1. 安装Python 3.8或更高版本
2. 安装所需的依赖包：

```cmd
pip install canvassyncer PyQt5 pyinstaller
```

## 打包步骤

1. 下载源代码到本地文件夹

2. 创建一个与下面内容相同的`canvas_downloader_win.spec`文件：

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['canvas_downloader_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['canvassyncer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Canvas下载助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

3. 在命令提示符中执行：

```cmd
pyinstaller canvas_downloader_win.spec
```

4. 打包完成后，可执行文件将位于`dist`文件夹中

## 创建安装程序（可选）

如果需要创建安装程序，可以使用Inno Setup：

1. 下载并安装[Inno Setup](https://jrsoftware.org/isdl.php)

2. 创建以下内容的脚本文件，命名为`setup.iss`：

```iss
[Setup]
AppName=Canvas下载助手
AppVersion=0.1.0
DefaultDirName={pf}\Canvas下载助手
DefaultGroupName=Canvas下载助手
OutputDir=output
OutputBaseFilename=Canvas下载助手_安装程序
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\Canvas下载助手.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Canvas下载助手"; Filename: "{app}\Canvas下载助手.exe"
Name: "{commondesktop}\Canvas下载助手"; Filename: "{app}\Canvas下载助手.exe"
```

3. 运行Inno Setup，打开并编译此脚本

4. 安装程序将生成在`output`文件夹中 