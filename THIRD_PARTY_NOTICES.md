# Third-party notices

Scanner Link Pro is free software, released under the **GNU General Public License, version 2 or
(at your option) any later version** (see [LICENSE](LICENSE)). Copyright (C) 2026 ShinRalexis.

This file lists the third-party work the program builds on or ships with, and where to find its
source code.

## Work the source code is based on

| Component | License | How it is used |
| --- | --- | --- |
| [SANE backends](https://gitlab.com/sane-project/backends), `epson2` backend | GPL-2.0-or-later | The Epson ESC/I protocol in `gt10000/esci.py` follows the command sequence and values of `epson2-ops.c`; the GT-10000 color matrix and its rounding in `gt10000/color.py` follow `epson2-cct.c` and `epson2-commands.c`. This is the main reason the project uses the same license. |
| Logitec LUB-SC / LUB-MSC adapter protocol | n/a | Reconstructed for interoperability by analysing the original Windows 2000/XP driver. No Logitec code or driver file is included in this repository or in the installer. |

## Shipped in the Windows installer

The installer (`ScannerLinkPro-Setup-<version>.exe`) contains the program built with PyInstaller,
the usbipd-win installer package and a minimal Debian system for WSL.

| Component | Version | License | Source |
| --- | --- | --- | --- |
| Python | 3.12.4 | PSF License | <https://www.python.org/downloads/source/> |
| Tcl/Tk (Tkinter) | 8.6.14 | Tcl/Tk License (BSD-style) | <https://www.tcl.tk/software/tcltk/> |
| Pillow | 10.4.0 | MIT-CMU (HPND) | <https://github.com/python-pillow/Pillow> |
| NumPy | 1.26.4 | BSD-3-Clause | <https://github.com/numpy/numpy> |
| OpenBLAS (inside NumPy) | 0.3.23 | BSD-3-Clause | <https://github.com/OpenMathLib/OpenBLAS> |
| PyInstaller bootloader | 6.19.0 | GPL-2.0-or-later with the PyInstaller exception (the bootloader may be used for programs under any license) | <https://github.com/pyinstaller/pyinstaller> |
| usbipd-win | 5.3.0 | GPL-3.0-only | <https://github.com/dorssel/usbipd-win> (installer package signed by its author, shipped unmodified) |
| Inno Setup (installer engine) | 6.x | Inno Setup License | <https://jrsoftware.org/isinfo.php> |
| Debian GNU/Linux system for WSL | 13.7 "trixie" | various free licenses, mostly GPL, LGPL, BSD and MIT; each package carries its own terms in `/usr/share/doc/<package>/copyright` | see below |

### Debian packages in the built-in Linux

The built-in Linux (`linux/GT10000-debian.tar`, imported on first start as the WSL distribution
`GT10000`) is an unmodified minimal Debian 13 with these packages installed. Their exact source code
is available from the Debian archive, for example at
`https://snapshot.debian.org/package/<source package>/<version>/` or
<https://sources.debian.org/>. The program's own scanner engine (`gt10000/`) is copied into
`/opt/gt10000` and is covered by this project's license.

| Package | Version | Source package |
| --- | --- | --- |
| apt | 3.0.3 | apt |
| base-files | 13.8+deb13u7 | base-files |
| base-passwd | 3.6.7 | base-passwd |
| bash | 5.2.37-2+b10 | bash |
| bsdutils | 1:2.41.5-0+deb13u1 | util-linux |
| coreutils | 9.7-3 | coreutils |
| dash | 0.5.12-12 | dash |
| debconf | 1.5.91 | debconf |
| debian-archive-keyring | 2025.1 | debian-archive-keyring |
| debianutils | 5.23.2 | debianutils |
| diffutils | 1:3.10-4 | diffutils |
| dpkg | 1.22.22 | dpkg |
| findutils | 4.10.0-3 | findutils |
| gcc-14-base | 14.2.0-19 | gcc-14 |
| grep | 3.11-4 | grep |
| gzip | 1.13-1+deb13u1 | gzip |
| hostname | 3.25 | hostname |
| init-system-helpers | 1.69~deb13u1 | init-system-helpers |
| libacl1 | 2.3.2-2+b1 | acl |
| libapt-pkg7.0 | 3.0.3 | apt |
| libattr1 | 1:2.5.2-3 | attr |
| libaudit-common | 1:4.0.2-2+deb13u1 | audit |
| libaudit1 | 1:4.0.2-2+deb13u1 | audit |
| libblkid1 | 2.41.5-0+deb13u1 | util-linux |
| libbsd0 | 0.12.2-2 | libbsd |
| libbz2-1.0 | 1.0.8-6 | bzip2 |
| libc-bin | 2.41-12+deb13u4 | glibc |
| libc6 | 2.41-12+deb13u4 | glibc |
| libcap-ng0 | 0.8.5-4+b1 | libcap-ng |
| libcap2 | 1:2.75-10+deb13u1+b3 | libcap2 |
| libcrypt1 | 1:4.4.38-1 | libxcrypt |
| libdb5.3t64 | 5.3.28+dfsg2-9 | db5.3 |
| libdebconfclient0 | 0.280 | cdebconf |
| libexpat1 | 2.8.3-1~deb13u1 | expat |
| libffi8 | 3.4.8-2 | libffi |
| libgcc-s1 | 14.2.0-19 | gcc-14 |
| libgmp10 | 2:6.3.0+dfsg-3 | gmp |
| libhogweed6t64 | 3.10.1-1 | nettle |
| liblastlog2-2 | 2.41.5-0+deb13u1 | util-linux |
| liblz4-1 | 1.10.0-4 | lz4 |
| liblzma5 | 5.8.1-1+deb13u1 | xz-utils |
| libmd0 | 1.1.0-2+b1 | libmd |
| libmount1 | 2.41.5-0+deb13u1 | util-linux |
| libncursesw6 | 6.5+20250216-2 | ncurses |
| libnettle8t64 | 3.10.1-1 | nettle |
| libpam-modules | 1.7.0-5 | pam |
| libpam-modules-bin | 1.7.0-5 | pam |
| libpam-runtime | 1.7.0-5 | pam |
| libpam0g | 1.7.0-5 | pam |
| libpcre2-8-0 | 10.46-1~deb13u2 | pcre2 |
| libpython3-stdlib | 3.13.5-1 | python3-defaults |
| libpython3.13-minimal | 3.13.5-2+deb13u5 | python3.13 |
| libpython3.13-stdlib | 3.13.5-2+deb13u5 | python3.13 |
| libreadline8t64 | 8.2-6 | readline |
| libseccomp2 | 2.6.0-2 | libseccomp |
| libselinux1 | 3.8.1-1 | libselinux |
| libsemanage-common | 3.8.1-1 | libsemanage |
| libsemanage2 | 3.8.1-1 | libsemanage |
| libsepol2 | 3.8.1-1 | libsepol |
| libsmartcols1 | 2.41.5-0+deb13u1 | util-linux |
| libsqlite3-0 | 3.46.1-7+deb13u2 | sqlite3 |
| libssl3t64 | 3.5.7-1~deb13u2 | openssl |
| libstdc++6 | 14.2.0-19 | gcc-14 |
| libsystemd0 | 257.13-1~deb13u1 | systemd |
| libtinfo6 | 6.5+20250216-2 | ncurses |
| libudev1 | 257.13-1~deb13u1 | systemd |
| libusb-1.0-0 | 2:1.0.28-1 | libusb-1.0 |
| libuuid1 | 2.41.5-0+deb13u1 | util-linux |
| libxxhash0 | 0.8.3-2 | xxhash |
| libzstd1 | 1.5.7+dfsg-1 | libzstd |
| login | 1:4.16.0-2+really2.41.5-0+deb13u1 | util-linux |
| login.defs | 1:4.17.4-2 | shadow |
| mawk | 1.3.4.20250131-1 | mawk |
| media-types | 13.0.0 | media-types |
| mount | 2.41.5-0+deb13u1 | util-linux |
| ncurses-base | 6.5+20250216-2 | ncurses |
| ncurses-bin | 6.5+20250216-2 | ncurses |
| netbase | 6.5 | netbase |
| openssl-provider-legacy | 3.5.7-1~deb13u2 | openssl |
| passwd | 1:4.17.4-2 | shadow |
| perl-base | 5.40.1-6+deb13u1 | perl |
| python3 | 3.13.5-1 | python3-defaults |
| python3-minimal | 3.13.5-1 | python3-defaults |
| python3-usb | 1.2.1-2 | pyusb |
| python3.13 | 3.13.5-2+deb13u5 | python3.13 |
| python3.13-minimal | 3.13.5-2+deb13u5 | python3.13 |
| readline-common | 8.2-6 | readline |
| sed | 4.9-2+deb13u1 | sed |
| sqv | 1.3.0-3+b2 | rust-sequoia-sqv |
| sysvinit-utils | 3.14-4 | sysvinit |
| tar | 1.35+dfsg-3.1 | tar |
| tzdata | 2026c-0+deb13u1 | tzdata |
| usbutils | 1:018-2 | usbutils |
| util-linux | 2.41.5-0+deb13u1 | util-linux |
| zlib1g | 1:1.3.dfsg+really1.3.1-1+b1 | zlib |

## Trademarks

Epson and ESC/I are trademarks of Seiko Epson Corporation. Logitec is a trademark of Logitec
Corporation (ELECOM group). Windows and WSL are trademarks of Microsoft Corporation. They are used
only to say which hardware and software this program works with. Scanner Link Pro is an independent
project, not affiliated with, endorsed or supported by any of these companies.
