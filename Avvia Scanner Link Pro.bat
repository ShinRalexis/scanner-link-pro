@echo off
rem Scanner Link Pro: SCSI/USB to Scanner
rem Copyright (C) 2026 ShinRalexis
rem SPDX-License-Identifier: GPL-2.0-or-later
rem Avvia Scanner Link Pro (Epson GT-10000+) senza lasciare aperta la finestra del prompt.
setlocal
set "APP=%~dp0app\scanner_app.pyw"

where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%APP%"
    exit /b 0
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" "%APP%"
    exit /b 0
)

echo Python non trovato. Esegui installa.ps1 nella cartella del programma.
pause
exit /b 1
