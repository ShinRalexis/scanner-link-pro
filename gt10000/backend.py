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
VERSION = "1.4"
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


class Backend:
    def __init__(self):
        self.scanner = None
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

    def run(self):
        threading.Thread(target=self.reader, daemon=True).start()
        send({"type": "hello", "version": VERSION, "python": sys.version.split()[0]})
        while True:
            with self.jobs_cv:
                if not self.jobs:
                    self.jobs_cv.wait(BUTTON_POLL_S)
                cmd = self.jobs.pop(0) if self.jobs else None
            if cmd is None:
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
    Backend().run()
