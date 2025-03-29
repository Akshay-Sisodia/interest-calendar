# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import site
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Get site-packages directory
site_packages = site.getsitepackages()[0]

# Collect Streamlit and related packages
datas = []
binaries = []
hiddenimports = []

# Add essential hidden imports
hiddenimports += [
    'streamlit', 
    'streamlit.runtime', 
    'importlib.metadata',
    'importlib.resources',
    'streamlit_extras',
    'pkg_resources.py2_warn',
    'altair',
    'pandas',
    'numpy',
    'plotly',
    'openpyxl',
    'xlsxwriter'
]

# Collect all Streamlit files
streamlit_a, streamlit_b, streamlit_c = collect_all('streamlit')
datas += streamlit_a
binaries += streamlit_b
hiddenimports += streamlit_c

# Collect metadata files
datas += [(site_packages, 'site-packages')]
streamlit_path = os.path.join(site_packages, 'streamlit')
if os.path.exists(streamlit_path):
    datas += [(streamlit_path, 'streamlit')]
    static_path = os.path.join(streamlit_path, 'runtime', 'static')
    if os.path.exists(static_path):
        datas += [(static_path, 'streamlit/runtime/static')]

# Add our fix_streamlit.py script
datas += [('fix_streamlit.py', '.')]

# Project-specific data
datas += [('src', 'src')]
datas += [('.streamlit', '.streamlit')]

# Create a runtime hook for importlib.metadata
with open('runtime_hook.py', 'w') as f:
    f.write('''
import os
import sys
import importlib

# Add the directory containing fix_streamlit.py to Python path
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
    
    # Try to pre-load the metadata patch
    try:
        import importlib.metadata
        import fix_streamlit
        fix_streamlit.patch_metadata()
    except ImportError:
        print("Warning: importlib.metadata not available in hook")
    except Exception as e:
        print(f"Warning: Error in hook while patching metadata: {e}")
''')

# Project base
block_cipher = None

a = Analysis(
    ['ledger_app_modular.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
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
    name='InterestCalendarLedger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='InterestCalendarLedger',
) 