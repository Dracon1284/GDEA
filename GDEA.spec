# -*- mode: python ; coding: utf-8 -*-
"""
Spec de PyInstaller para GDEA.
Genera dist\GDEA\ con GDEA.exe + todas las dependencias.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas    = []
binaries = []
hiddenimports = []

# PyMuPDF: la librería cambió de nombre fitz → pymupdf en v1.24+
# collect_all captura DLLs nativas, datos y submódulos
for pkg in ("pymupdf", "fitz"):
    try:
        d, b, h = collect_all(pkg)
        datas    += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Rich: incluye estilos, temas y datos de markdown
d, b, h = collect_all("rich")
datas    += d
binaries += b
hiddenimports += h

# Módulos locales del paquete gdea
hiddenimports += collect_submodules("gdea")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Excluir paquetes pesados que no se usan
    excludes=[
        "tkinter", "matplotlib", "numpy", "pandas", "scipy",
        "IPython", "jupyter", "notebook", "tornado",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GDEA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # upx puede romper DLLs nativas de PyMuPDF
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="GDEA",
)
