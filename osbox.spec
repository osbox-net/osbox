# -*- mode: python ; coding: utf-8 -*-

import pkgutil
from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = []
datas = []
binaries = []

for pkg in [module.name for module in pkgutil.iter_modules()]:
    if pkg in "antigravity":
        continue
    print("collecting", pkg)
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h
    hiddenimports += collect_submodules(pkg)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='osbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

