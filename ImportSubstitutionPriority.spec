# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

python_root = Path(sys.base_prefix)


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(python_root / 'tcl' / 'tcl8.6'), '_tcl_data'),
        (str(python_root / 'tcl' / 'tk8.6'), '_tk_data'),
        (str(python_root / 'Lib' / 'tkinter'), 'tkinter'),
    ],
    hiddenimports=[
        'src.1_data_loader.loader',
        'src.2_preprocessing.preprocessing',
        'src.3_indicators.indicators',
        'src.4_normalization.normalization',
        'src.5_model.model',
        'src.6_visualization.charts',
        'src.7_export.exporter',
        'src.ui.app',
        'pandas',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'tkinter',
        '_tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.font',
        'tkinter.simpledialog',
        'openpyxl',
        'PIL',
    ],
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
    name='ImportSubstitutionPriority',
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


