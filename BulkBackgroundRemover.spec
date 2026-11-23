# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

block_cipher = None

# Core application scripts
datas = [
    ('app.py', '.'),
    ('processor.py', '.'),
    ('batch_manager.py', '.'),
    ('hardware.py', '.')
]

# If model was pre-downloaded in models/u2net.onnx, bundle it for offline install
if os.path.exists('models/u2net.onnx'):
    datas.append(('models/u2net.onnx', 'models'))

datas += copy_metadata('streamlit')
datas += copy_metadata('rembg')
datas += copy_metadata('tqdm')
datas += copy_metadata('pillow')
datas += copy_metadata('onnxruntime')
datas += collect_data_files('streamlit')
datas += collect_data_files('rembg')

hiddenimports = [
    'streamlit',
    'streamlit.web.cli',
    'rembg',
    'rembg.sessions',
    'rembg.sessions.u2net',
    'onnxruntime',
    'PIL',
    'PIL.Image',
    'numpy',
    'tqdm'
]

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'notebook', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BulkBackgroundRemover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BulkBackgroundRemover',
)
