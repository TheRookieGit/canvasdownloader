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
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='Canvas下载助手.app',
    bundle_identifier='com.canvasdownloader.app',
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False'
    },
) 