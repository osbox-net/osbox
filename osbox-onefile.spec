# -*- mode: python ; coding: utf-8 -*-

import sys
import site
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

hiddenimports = []
datas = []
binaries = []

# Get site-packages directories for the current venv
site_packages_dirs = site.getsitepackages()
if hasattr(site, 'getusersitepackages'):
    site_packages_dirs.append(site.getusersitepackages())

# Collect all top-level packages/modules from site-packages
packages = set()
for site_dir in site_packages_dirs:
    site_path = Path(site_dir)
    if not site_path.exists():
        continue
    
    for item in site_path.iterdir():
        # Skip dist-info, egg-info directories
        if item.name.endswith(('.dist-info', '.egg-info', '.egg-link')):
            continue
        # Skip __pycache__
        if item.name == '__pycache__':
            continue
        
        # Check if it's a package (directory with __init__.py) or a module (.py file)
        if item.is_dir() and (item / '__init__.py').exists():
            packages.add(item.name)
        elif item.is_file() and item.suffix == '.py' and item.stem != '__pycache__':
            packages.add(item.stem)

print(f"Found {len(packages)} packages in site-packages")

for pkg in sorted(packages):
    if pkg in ('antigravity', '_virtualenv'):
        continue
    print(f"Collecting {pkg}")
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
        hiddenimports += collect_submodules(pkg)
    except Exception as e:
        print(f"Warning: Failed to collect {pkg}: {e}")

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

