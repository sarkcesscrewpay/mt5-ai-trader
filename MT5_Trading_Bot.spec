# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\mcp_mt5\\trading\\starter_example.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config')],
    hiddenimports=['numpy', 'pandas', 'scipy', 'sklearn', 'xgboost', 'lightgbm', 'dotenv', 'yaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MT5_Trading_Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
