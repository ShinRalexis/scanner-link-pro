# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Motore di scansione che gira dentro la distribuzione WSL "GT10000".

Protocollo con l'interfaccia Windows, su stdin/stdout:
  stdin   una riga JSON per comando: open, scan, cancel, quit
  stdout  una riga JSON per messaggio; un messaggio {"type": "data", "length": n}
          è seguito da esattamente n byte grezzi dell'immagine.
"""

import json
import os
import signal
import sys
import threading
import time
import traceback

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gt10000.esci import GT10000, ScanCancelled, ScanParams, ScannerError  # noqa: E402
from gt10000.lubsc import AdapterNotFound, LubscAdapter, ScsiError, find_adapter  # noqa: E402
from gt10000.messages import Note, payload  # noqa: E402

# 1.1: i messaggi portano anche "key" e "args"; scansione con gamma e soglia
# 1.2: evento "button" quando si preme il pulsante blu dello scanner
VERSION = "1.5"
# a riposo il pulsante si interroga 4 volte al secondo; mai durante una scansione
BUTTON_POLL_S = 0.25

_out = sys.stdout.buffer
_out_lock = threading.Lock()


def send(msg, payload=None):
    line = (json.dumps(msg) + "\n").encode("utf-8")
    with _out_lock:
        _out.write(line)
        if payload:
            _out.write(payload)
        _out.flush()


def log(message):
    """Registro: Note con chiave traducibile, oppure testo semplice."""
    send(dict({"type": "log"}, **payload(message)))


def status(note):
    send(dict({"type": "status"}, **payload(note)))


def stop_other_engines(timeout_s=12.0):
    """Ferma gli altri motori in esecuzione e ritorna quanti erano.

    Un motore resta orfano quando lato Windows il processo viene terminato invece di chiuso con "quit"
    (programma chiuso a forza, Riconnetti mentre WSL è ancora lento a partire): continua a tenere
    l'adattatore e il motore nuovo trova "Resource busy". Lo scanner lo usa un programma alla volta,
    quindi il motore più recente ha ragione. Si cerca in /proc: il Linux minimale non ha ps.

    Si chiede di fermarsi con SIGTERM: il motore finisce il comando in corso (o annulla la scansione) e
    rilascia l'adattatore. Ucciderlo a metà di un comando lascia il bus SCSI bloccato fino a quando lo
    scanner non viene spento e riacceso (provato il 2026-10-13): SIGKILL solo se non esce entro il tempo.
    """
    me = os.getpid()
    others = []
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == me:
            continue
        try:
            with open("/proc/%s/cmdline" % name, "rb") as f:
                args = f.read().split(b"\0")
        except OSError:
            continue
        if any(a.endswith(b"gt10000/backend.py") for a in args):
            others.append(int(name))
    for pid in others:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline and any(os.path.exists("/proc/%d" % pid) for pid in others):
        time.sleep(0.1)
    for pid in others:
        if os.path.exists("/proc/%d" % pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    return len(others)


class Backend:
    def __init__(self):
        self.scanner = None
        self.stopped_engines = 0     # motori orfani fermati all'avvio (vedi stop_other_engines)
        self.stop_requested = threading.Event()   # SIGTERM: uscire al primo momento sicuro
        self.cancel_flag = threading.Event()
        self.jobs = []
        self.jobs_cv = threading.Condition()
        self.button_ok = False       # interrogare il pulsante solo con lo scanner aperto e senza errori
        self.button_prev = False

    def reader(self):
        """Legge stdin in un thread a parte, così 'cancel' arriva anche durante una scansione."""
        for raw in sys.stdin.buffer:
            try:
                cmd = json.loads(raw.decode("utf-8"))
            except ValueError:
                continue
            if cmd.get("cmd") == "cancel":
                self.cancel_flag.set()
                continue
            with self.jobs_cv:
                self.jobs.append(cmd)
                self.jobs_cv.notify()
        with self.jobs_cv:
            self.jobs.append({"cmd": "quit"})
            self.jobs_cv.notify()

    def request_stop(self, signum=None, frame=None):
        """SIGTERM: niente uscita immediata, che lascerebbe un comando SCSI a metà; si annulla l'eventuale
        scansione e si esce dal ciclo principale al primo momento sicuro."""
        self.stop_requested.set()
        self.cancel_flag.set()

    def run(self):
        signal.signal(signal.SIGTERM, self.request_stop)
        threading.Thread(target=self.reader, daemon=True).start()
        send({"type": "hello", "version": VERSION, "python": sys.version.split()[0]})
        if self.stopped_engines:
            log(Note("b_stale_engines", n=self.stopped_engines))
        while True:
            if self.stop_requested.is_set():
                self.close()
                return
            with self.jobs_cv:
                if not self.jobs:
                    self.jobs_cv.wait(BUTTON_POLL_S)
                cmd = self.jobs.pop(0) if self.jobs else None
            if cmd is None:
                if not self.stop_requested.is_set():
                    self.poll_button()
                continue
            name = cmd.get("cmd")
            if name == "quit":
                self.close()
                return
            try:
                if name == "open":
                    self.open(cmd.get("wait_s", 30))
                elif name == "scan":
                    self.scan(cmd)
                else:
                    send(dict({"type": "error"}, **payload(Note("b_unknown_cmd", cmd=name))))
            except ScanCancelled:
                send({"type": "cancelled", "id": cmd.get("id")})
            except (ScannerError, ScsiError, AdapterNotFound, OSError) as e:
                self.drop_scanner()
                send(dict({"type": "error", "id": cmd.get("id")}, **payload(e)))
            except Exception as e:  # errore di programmazione: meglio vederlo per intero
                self.drop_scanner()
                send({"type": "error", "id": cmd.get("id"), "message": "%s: %s" % (type(e).__name__, e),
                      "trace": traceback.format_exc()})

    def poll_button(self):
        """Avvisa l'interfaccia al passaggio da rilasciato a premuto (una pressione lunga conta una volta)."""
        if self.scanner is None or not self.button_ok or not self.scanner.identity.has_button:
            return
        try:
            pressed = self.scanner.button_pressed()
        except Exception:
            # scanner spento o riacceso: si riprende dopo la prossima apertura o scansione riuscita
            self.button_ok = False
            return
        if pressed and not self.button_prev:
            send({"type": "button"})
        self.button_prev = pressed

    def drop_scanner(self):
        if self.scanner is not None:
            try:
                self.scanner.close()
            except Exception:
                pass
            self.scanner = None

    def close(self):
        self.drop_scanner()

    def open(self, wait_s):
        self.drop_scanner()
        deadline = time.monotonic() + wait_s
        announced = False
        while find_adapter() is None:
            if self.stop_requested.is_set():
                return
            if not announced:
                status(Note("b_wait_adapter"))
                announced = True
            if time.monotonic() > deadline:
                raise AdapterNotFound("b_adapter_not_visible")
            time.sleep(0.5)
        status(Note("b_adapter_found"))
        self.scanner = GT10000(adapter=LubscAdapter(), log=log)
        self.button_ok, self.button_prev = True, False
        ident = self.scanner.identity
        vendor, product, rev = self.scanner.inquiry
        send({"type": "opened", "vendor": vendor, "product": product, "firmware": rev,
              "model": ident.model, "scsi_id": self.scanner.target, "level": ident.level,
              "resolutions": ident.resolutions, "width_mm": ident.width_mm, "height_mm": ident.height_mm,
              "base_dpi": ident.base_dpi, "optical_dpi": ident.optical_dpi, "color": ident.color_ok,
              "brightness_min": ident.brightness_range[0], "button": ident.has_button})

    def scan(self, cmd):
        if self.scanner is None:
            self.open(10)
        self.cancel_flag.clear()
        area = cmd.get("area_mm")
        p = ScanParams(mode=cmd.get("mode", "color"), dpi=int(cmd.get("dpi", 300)),
                       dpi_y=int(cmd["dpi_y"]) if cmd.get("dpi_y") else None,
                       area_mm=tuple(area) if area else None,
                       brightness=int(cmd.get("brightness", 0)), sharpness=int(cmd.get("sharpness", 0)),
                       threshold=int(cmd.get("threshold", 128)), preview=bool(cmd.get("preview", False)),
                       gamma=float(cmd["gamma"]) if cmd.get("gamma") else None)
        job = cmd.get("id")
        # posizione dell'area in punti: serve all'interfaccia per la correzione righe
        left, top, _, _ = self.scanner.compute_area(p)

        def on_begin(width, height, bpl):
            send({"type": "begin", "id": job, "width": width, "height": height, "bytes_per_line": bpl,
                  "mode": p.mode, "dpi": p.dpi, "dpi_y": p.dpi_y or p.dpi, "left": left, "top": top})

        def on_data(block):
            send({"type": "data", "id": job, "length": len(block)}, block)

        t0 = time.monotonic()
        self.button_ok = False
        try:
            result = self.scanner.scan(p, cancel=self.cancel_flag.is_set, on_begin=on_begin, on_data=on_data)
        finally:
            # anche dopo un annullamento; dopo un errore lo scanner viene chiuso e l'ascolto resta spento
            self.button_ok, self.button_prev = True, False
        send({"type": "end", "id": job, "width": result.width, "height": result.height,
              "seconds": round(time.monotonic() - t0, 1)})


if __name__ == "__main__":
    # GT10000_KEEP_OTHERS: solo per i test, per non fermare il motore di un programma aperto
    stopped = 0 if os.environ.get("GT10000_KEEP_OTHERS") else stop_other_engines()
    if "--stop-others" in sys.argv:
        # usato dall'interfaccia quando un motore non risponde alla chiusura: pulizia e basta
        sys.exit(0)
    backend = Backend()
    backend.stopped_engines = stopped
    backend.run()
    # uscita immediata: il thread che legge i comandi è fermo su stdin, e la chiusura normale di Python
    # con quel thread ancora attivo può terminare con un abort (codice -6)
    sys.stdout.flush()
    os._exit(0)
