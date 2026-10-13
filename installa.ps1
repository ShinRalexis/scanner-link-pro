# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later
# Installa o ripara lo Scanner Epson GT-10000+ su Windows.
# Si puo' rilanciare quando si vuole: salta i passi gia' fatti.
#
#   1. Python con Pillow (interfaccia grafica) e numpy (correzione righe)
#   2. usbipd-win (passa l'adattatore USB-SCSI al Linux interno)
#   3. distribuzione WSL "GT10000" (Debian minimale con Python e pyusb) + driver
#   4. condivisione dell'adattatore Logitec (una volta sola, chiede l'autorizzazione)
#   5. collegamenti su Desktop e menu Start

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Distro = 'GT10000'
$LinuxDir = Join-Path $Root 'linux'
$Backup = Join-Path $LinuxDir 'GT10000-debian.tar'
$Usbipd = 'C:\Program Files\usbipd-win\usbipd.exe'
# l'adattatore Logitec esiste con due identificativi USB (il driver originale li dichiara entrambi)
$HardwareIds = @('0789:00c0', '0789:0004')

function Step($text) { Write-Host ""; Write-Host "== $text" -ForegroundColor Cyan }
function Ok($text) { Write-Host "   $text" -ForegroundColor Green }
function Warn($text) { Write-Host "   $text" -ForegroundColor Yellow }

function To-WslPath($path) {
    $full = (Resolve-Path $path).Path
    return '/mnt/' + $full.Substring(0, 1).ToLower() + $full.Substring(2).Replace('\', '/')
}

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Distro-Installed {
    $names = (wsl.exe -l -q) -replace "`0", ''
    return [bool]($names | Where-Object { $_.Trim() -eq $Distro })
}

Step 'Python, Pillow e numpy'
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python -or $python -like '*WindowsApps*') {
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    Refresh-Path
}
python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) { python -m pip install --user --quiet pillow }
python -c "import numpy" 2>$null
if ($LASTEXITCODE -ne 0) { python -m pip install --user --quiet numpy }
$pythonw = Join-Path (Split-Path (python -c "import sys; print(sys.executable)")) 'pythonw.exe'
Ok "Python: $pythonw"

Step 'usbipd-win'
if (-not (Test-Path $Usbipd)) {
    winget install --id dorssel.usbipd-win -e --silent --accept-package-agreements --accept-source-agreements
}
if (-not (Test-Path $Usbipd)) { throw 'Installazione di usbipd-win non riuscita' }
Ok (& $Usbipd --version)

Step 'WSL'
wsl.exe --status *> $null
if ($LASTEXITCODE -ne 0) {
    Warn 'WSL non e'' installato. Esegui "wsl --install" da amministratore, riavvia e rilancia questo script.'
    exit 1
}
Ok 'WSL presente'

Step "Distribuzione Linux $Distro"
if (-not (Distro-Installed)) {
    New-Item -ItemType Directory -Force $LinuxDir | Out-Null
    if (Test-Path $Backup) {
        Ok 'Importo il backup gia'' configurato'
        wsl.exe --import $Distro $LinuxDir $Backup --version 2
    } elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        Ok 'Scarico Debian 13 minimale tramite Docker'
        $tar = Join-Path $env:TEMP 'gt10000-rootfs.tar'
        docker pull -q debian:trixie-slim | Out-Null
        docker rm -f gt10000-rootfs 2>$null | Out-Null
        docker create --name gt10000-rootfs debian:trixie-slim | Out-Null
        docker export gt10000-rootfs -o $tar
        docker rm gt10000-rootfs | Out-Null
        wsl.exe --import $Distro $LinuxDir $tar --version 2
        Remove-Item $tar
    } else {
        throw "Serve Docker Desktop oppure il file $Backup per creare il Linux interno"
    }
}
wsl.exe -d $Distro -u root -- sh (To-WslPath (Join-Path $Root 'setup\provision.sh'))
if ($LASTEXITCODE -ne 0) { throw 'Preparazione del Linux interno non riuscita' }
$driverSrc = To-WslPath (Join-Path $Root 'gt10000')
wsl.exe -d $Distro -u root -- sh -c "rm -rf /opt/gt10000/gt10000 && cp -r '$driverSrc' /opt/gt10000/gt10000 && rm -rf /opt/gt10000/gt10000/__pycache__"
Ok 'Driver copiato in /opt/gt10000'
if (-not (Test-Path $Backup)) {
    wsl.exe --terminate $Distro | Out-Null
    wsl.exe --export $Distro $Backup
    Ok "Backup del Linux interno: $Backup"
}

Step 'Adattatore Logitec USB-SCSI'
$line = (& $Usbipd list) | Where-Object { $l = $_; $HardwareIds | Where-Object { $l -match $_ } } | Select-Object -First 1
$HardwareId = $HardwareIds | Where-Object { $line -match $_ } | Select-Object -First 1
if (-not $line) {
    Warn 'Adattatore non collegato: collegalo quando vuoi, il programma lo condividera'' al primo avvio.'
} elseif ($line -match 'Not shared') {
    Start-Process -FilePath $Usbipd -ArgumentList "bind --hardware-id $HardwareId" -Verb RunAs -Wait
    Ok 'Adattatore condiviso con Linux'
} else {
    Ok 'Adattatore gia'' condiviso'
}

Step 'Collegamenti'
$shell = New-Object -ComObject WScript.Shell
$targets = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Scanner Link Pro (sorgenti).lnk'),
    (Join-Path ([Environment]::GetFolderPath('Programs')) 'Scanner Link Pro (sorgenti).lnk')
)
# collegamenti della versione dai sorgenti: "(sorgenti)" nel nome, per non confonderli con quelli
# dell'installatore ("Scanner Link Pro"); si tolgono quelli col vecchio nome (fino al 2026-10-12 il
# programma si chiamava Scanner GT-10000+)
foreach ($old in @('Desktop', 'Programs')) {
    $oldLnk = Join-Path ([Environment]::GetFolderPath($old)) 'Scanner GT-10000+.lnk'
    if (Test-Path $oldLnk) { Remove-Item $oldLnk }
}
foreach ($lnkPath in $targets) {
    $lnk = $shell.CreateShortcut($lnkPath)
    $lnk.TargetPath = $pythonw
    $lnk.Arguments = '"' + (Join-Path $Root 'app\scanner_app.pyw') + '"'
    $lnk.WorkingDirectory = Join-Path $Root 'app'
    $lnk.IconLocation = (Join-Path $Root 'app\icona.ico') + ',0'
    $lnk.Description = 'Scanner Link Pro: SCSI/USB to Scanner (Epson GT-10000+ con adattatore Logitec USB-SCSI)'
    $lnk.Save()
    Ok $lnkPath
}

Write-Host ""
Write-Host 'Fatto. Avvia "Scanner Link Pro (sorgenti)" dal Desktop o dal menu Start.' -ForegroundColor Green
