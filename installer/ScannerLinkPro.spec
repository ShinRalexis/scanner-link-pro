# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later
# PyInstaller: l'interfaccia Windows in una cartella con ScannerLinkPro.exe, senza bisogno di Python.
# Si costruisce con installer\build.ps1 (che poi crea l'installatore con Inno Setup).
import os

ROOT = os.path.dirname(SPECPATH)            # cartella del progetto
APP = os.path.join(ROOT, "app")

a = Analysis(
    [os.path.join(APP, "scanner_app.pyw")],
    pathex=[APP],
    datas=[(os.path.join(APP, name), ".") for name in ("icona.ico", "icona.png", "icona_piccola.png")],
    hiddenimports=["destripe"],
    excludes=["matplotlib", "scipy", "pandas", "IPython", "pytest", "setuptools", "pydoc_data"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ScannerLinkPro",
    icon=os.path.join(APP, "icona.ico"),
    console=False,
    version=os.path.join(SPECPATH, "version_info.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="ScannerLinkPro")
