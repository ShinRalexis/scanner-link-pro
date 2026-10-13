# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Ponte fra l'interfaccia Windows e il motore di scansione nella distribuzione WSL "GT10000"."""

import ctypes
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time

# nome del Linux interno; un altro nome solo per provare il primo avvio senza toccare quello in uso
DISTRO = os.environ.get("SCANNERLINKPRO_DISTRO", "GT10000")
# l'adattatore Logitec esiste con due identificativi USB: il driver originale li dichiara entrambi
HARDWARE_IDS = ("0789:00c0", "0789:0004")
_adapter_id = HARDWARE_IDS[0]          # quello trovato dall'ultima adapter_state()
# errori di WSL quando la macchina virtuale non può partire (virtualizzazione spenta nel BIOS/UEFI o
# componente "Piattaforma macchina virtuale" mancante): i codici non cambiano con la lingua di Windows
VIRTUALIZATION_ERRORS = ("0x80370102", "0x80370114", "hcs_e_hyperv_not_installed", "virtual machine platform",
                         "enable virtualization")
REMOTE_DIR = "/opt/gt10000"
# programma installato (PyInstaller): driver e backup del Linux stanno accanto all'eseguibile;
# dai sorgenti: nella cartella del progetto
FROZEN = getattr(sys, "frozen", False)
PROJECT_DIR = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER_DIR = os.path.join(PROJECT_DIR, "gt10000")
LINUX_BACKUP = os.path.join(PROJECT_DIR, "linux", "GT10000-debian.tar")
# dove si importa il Linux interno al primo avvio: nel profilo di chi usa il programma
LINUX_HOME = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ScannerLinkPro", "linux")

CREATE_NO_WINDOW = 0x08000000


def _run(args, timeout=60):
    return subprocess.run(args, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)


def _decode(b):
    # wsl.exe scrive i propri messaggi in UTF-16
    if b[:2] in (b"\xff\xfe",) or (len(b) > 1 and b[1:2] == b"\x00"):
        return b.decode("utf-16-le", "replace")
    return b.decode("utf-8", "replace")


def usbipd_exe():
    found = shutil.which("usbipd")
    if found:
        return found
    default = r"C:\Program Files\usbipd-win\usbipd.exe"
    return default if os.path.exists(default) else None


def distro_installed():
    try:
        out = _decode(_run(["wsl.exe", "-l", "-q"]).stdout)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(line.strip().strip("\x00") == DISTRO for line in out.splitlines())


def wsl_available():
    try:
        return _run(["wsl.exe", "--status"], timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def import_distro():
    """Importa il Linux interno dal backup (già pronto: Python, pyusb, configurazione). Ritorna (ok, testo)."""
    os.makedirs(LINUX_HOME, exist_ok=True)
    try:
        r = _run(["wsl.exe", "--import", DISTRO, LINUX_HOME, LINUX_BACKUP, "--version", "2"], timeout=900)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return r.returncode == 0 and distro_installed(), (_decode(r.stdout) + _decode(r.stderr)).strip()


def virtualization_problem(text):
    low = (text or "").lower()
    return any(code in low for code in VIRTUALIZATION_ERRORS)


def adapter_state():
    """Ritorna (stato, busid): stato fra 'assente', 'non condiviso', 'condiviso', 'collegato'."""
    global _adapter_id
    exe = usbipd_exe()
    if not exe:
        return "usbipd mancante", None
    out = _decode(_run([exe, "list"]).stdout)
    for line in out.splitlines():
        low = line.lower()
        found = next((hid for hid in HARDWARE_IDS if hid in low), None)
        if found:
            _adapter_id = found
            busid = line.split()[0]
            if "attached" in low:
                return "collegato", busid
            if "not shared" in low:
                return "non condiviso", busid
            if "shared" in low:
                return "condiviso", busid
            return "sconosciuto", busid
    return "assente", None


def bind_adapter_elevated():
    """Condivide l'adattatore con usbipd (serve una volta sola, chiede l'autorizzazione UAC)."""
    exe = usbipd_exe()
    params = "bind --hardware-id %s" % _adapter_id
    SEE_MASK_NOCLOSEPROCESS = 0x40

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_ulong), ("fMask", ctypes.c_ulong), ("hwnd", ctypes.c_void_p),
                    ("lpVerb", ctypes.c_wchar_p), ("lpFile", ctypes.c_wchar_p),
                    ("lpParameters", ctypes.c_wchar_p), ("lpDirectory", ctypes.c_wchar_p),
                    ("nShow", ctypes.c_int), ("hInstApp", ctypes.c_void_p), ("lpIDList", ctypes.c_void_p),
                    ("lpClass", ctypes.c_wchar_p), ("hkeyClass", ctypes.c_void_p),
                    ("dwHotKey", ctypes.c_ulong), ("hIcon", ctypes.c_void_p), ("hProcess", ctypes.c_void_p)]

    sei = SHELLEXECUTEINFO(cbSize=ctypes.sizeof(SHELLEXECUTEINFO), fMask=SEE_MASK_NOCLOSEPROCESS,
                           lpVerb="runas", lpFile=exe, lpParameters=params, nShow=0)
    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei)):
        return False
    ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 60000)
    ctypes.windll.kernel32.CloseHandle(sei.hProcess)
    return True


def attach_adapter():
    exe = usbipd_exe()
    r = _run([exe, "attach", "--wsl", "--hardware-id", _adapter_id], timeout=60)
    return r.returncode == 0, _decode(r.stdout + r.stderr).strip()


def detach_adapter():
    exe = usbipd_exe()
    if exe:
        try:
            _run([exe, "detach", "--hardware-id", _adapter_id], timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            pass


def sync_driver():
    """Copia il driver nella distribuzione Linux se è cambiato."""
    if not os.path.isdir(DRIVER_DIR):
        return ""        # senza la cartella del driver non si tocca quello già in Linux
    src = "/mnt/" + DRIVER_DIR[0].lower() + DRIVER_DIR[2:].replace("\\", "/")
    script = ('mkdir -p {dst} && [ -d "{src}" ] && if ! diff -rq "{src}" {dst}/gt10000 -x __pycache__ >/dev/null 2>&1; then '
              'rm -rf {dst}/gt10000 && cp -r "{src}" {dst}/gt10000 && rm -rf {dst}/gt10000/__pycache__ '
              '&& echo aggiornato; fi').format(src=src, dst=REMOTE_DIR)
    r = _run(["wsl.exe", "-d", DISTRO, "-u", "root", "--", "sh", "-c", script], timeout=120)
    return _decode(r.stdout).strip()


class Backend:
    """Processo del motore Linux. Gli eventi arrivano in self.events come tuple (tipo, dati)."""

    def __init__(self):
        self.events = queue.Queue()
        self.proc = None
        self._lock = threading.Lock()

    def start(self):
        self.proc = subprocess.Popen(
            ["wsl.exe", "-d", DISTRO, "-u", "root", "--", "python3", "-u", REMOTE_DIR + "/gt10000/backend.py"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW, bufsize=0)
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._stderr_reader, daemon=True).start()

    def _reader(self):
        out = self.proc.stdout
        try:
            while True:
                line = out.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except ValueError:
                    self.events.put(("log", {"message": line.decode("utf-8", "replace").rstrip()}))
                    continue
                if msg.get("type") == "data":
                    n = msg["length"]
                    buf = bytearray()
                    while len(buf) < n:
                        chunk = out.read(n - len(buf))
                        if not chunk:
                            raise EOFError
                        buf += chunk
                    msg["payload"] = bytes(buf)
                self.events.put((msg.get("type"), msg))
        except (EOFError, OSError):
            pass
        self.events.put(("exit", {"code": self.proc.poll()}))

    def _stderr_reader(self):
        for line in self.proc.stderr:
            text = _decode(line).replace("\x00", "").rstrip()
            if virtualization_problem(text):
                self.events.put(("virtualization", {}))
            if text and "locale" not in text.lower() and not text.startswith(("\t", "    ")):
                self.events.put(("log", {"message": "[linux] " + text}))

    def send(self, **cmd):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                self.proc.stdin.write((json.dumps(cmd) + "\n").encode("utf-8"))
                self.proc.stdin.flush()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.send(cmd="quit")
                self.proc.wait(5)
            except (OSError, subprocess.TimeoutExpired):
                self.proc.kill()
                stop_engines()


def stop_engines():
    """Ferma i motori dentro Linux: chiudere wsl.exe da Windows non sempre ferma il processo laggiù."""
    try:
        _run(["wsl.exe", "-d", DISTRO, "-u", "root", "--", "python3", REMOTE_DIR + "/gt10000/backend.py",
              "--stop-others"], timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass


def wait_for(predicate, timeout, step=0.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return False
