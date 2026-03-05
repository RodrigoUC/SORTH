# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[('data/input', 'data/input'), ('assets', 'assets'), ('README.md', '.'), ('../CREDITS.md', '.')],
    hiddenimports=['PyQt6'],
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
    name='SORTH',
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
    icon=['C:\\Users\\Rodri\\OneDrive\\Desktop\\Horas asistente\\SORTH\\project_root\\assets\\sorth.ico'],
)
