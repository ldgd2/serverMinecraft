import os
VERSION = os.environ.get('BUILD_VERSION', '2.0.0')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/assets', 'ui/assets')],
    hiddenimports=[
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'cryptography',
        'pywin32',
    ],
    hookspath=[],
    hooksconfig={'hook-webview': {'key': 'value'}},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'numpy', 'pandas', 'webview'],
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
    name=f'MinecraftLauncher_v{VERSION}',
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
    icon='ui/assets/appicon/minecraft.ico',
)
