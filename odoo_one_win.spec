# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['odoo_one.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/stylesheet.qss', 'ui'),
           ('ui/img/*.svg', 'ui/img'),
           ('data/*.json', 'data'),
           ],
    hiddenimports=[],
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
    name='odoo_one.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['ui\\icon.ico'],
)
