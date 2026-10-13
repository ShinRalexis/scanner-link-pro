#!/bin/sh
# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later
# Prepara la distribuzione WSL "GT10000" (Debian minimale): solo Python 3 e pyusb.
# Il driver dello scanner è in spazio utente, quindi non servono moduli del kernel.
set -e

cat > /etc/wsl.conf <<'CONF'
[boot]
systemd=false

[interop]
appendWindowsPath=false

[user]
default=root
CONF

if ! python3 -c "import usb.core" 2>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends python3 python3-usb usbutils >/dev/null
    apt-get clean
    rm -rf /var/lib/apt/lists/*
fi
mkdir -p /opt/gt10000
python3 -c "import usb.core, sys; print('Python', sys.version.split()[0], 'pyusb', usb.__version__)"
