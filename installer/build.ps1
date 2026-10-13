# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later
# Costruisce l'installatore di Scanner Link Pro: installer\output\ScannerLinkPro-Setup-<versione>.exe
#
#   powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
#
# Serve: Python con Pillow, numpy e PyInstaller; Inno Setup 6.5 o successivo; il backup del Linux interno
# linux\GT10000-debian.tar (lo crea installa.ps1). Il pacchetto di usbipd-win si scarica da solo e se ne
# controlla l'impronta.

$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
$Root = Split-Path -Parent $Here

$UsbipdName = 'usbipd-win_5.3.0_x64.msi'
$UsbipdUrl = "https://github.com/dorssel/usbipd-win/releases/download/v5.3.0/$UsbipdName"
$UsbipdSha256 = '1C984914AEC944DE19B64EFF232421439629699F8138E3DDC29301175BC6D938'

function Step($t) { Write-Host "`n== $t" -ForegroundColor Cyan }

Step 'Controlli'
$tar = Join-Path $Root 'linux\GT10000-debian.tar'
if (-not (Test-Path $tar)) { throw "Manca ${tar}: eseguire prima installa.ps1 per creare il Linux interno" }
python -c "import PIL, numpy, PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) { python -m pip install --user --quiet pillow numpy pyinstaller }
$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
foreach ($p in @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe")) {
    if (-not $iscc -and (Test-Path $p)) { $iscc = $p }
}
if (-not $iscc) { throw 'Inno Setup 6 non trovato (winget install JRSoftware.InnoSetup)' }

Step 'usbipd-win'
$msi = Join-Path $Here "redist\$UsbipdName"
if (-not (Test-Path $msi)) {
    New-Item -ItemType Directory -Force (Split-Path $msi) | Out-Null
    Invoke-WebRequest $UsbipdUrl -OutFile $msi
}
if ((Get-FileHash $msi -Algorithm SHA256).Hash -ne $UsbipdSha256) { throw "Impronta di $UsbipdName diversa da quella attesa" }

Step 'Immagini'
python (Join-Path $Here 'make_images.py')

Step 'Programma (PyInstaller)'
python -m PyInstaller --noconfirm --clean --log-level WARN `
    --distpath (Join-Path $Here 'build\dist') --workpath (Join-Path $Here 'build\work') `
    (Join-Path $Here 'ScannerLinkPro.spec')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller non riuscito' }

Step 'Installatore (Inno Setup)'
& $iscc /Q (Join-Path $Here 'ScannerLinkPro.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup non riuscito' }
Get-ChildItem (Join-Path $Here 'output') -Filter *.exe | ForEach-Object {
    Write-Host ("Fatto: {0} ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) -ForegroundColor Green
}
