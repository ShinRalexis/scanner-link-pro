# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Protocollo Epson ESC/I per gli scanner Epson SCSI, collaudato sul GT-10000+ (livello B7).

Ogni comando ESC/I viaggia dentro un SCSI WRITE(6) e ogni risposta dentro un READ(6),
come nel backend SANE epson2. Sequenza e valori seguono epson2-ops.c (scansione standard
a blocchi, senza la "extended scan" FS G).

Altri modelli: i comandi usati esistono uguali dal livello B5 al B8 (tabella epson_cmd di SANE).
Il livello si legge dallo scanner (ESC I) e decide cosa si può chiedere:
  B4      niente colore (manda le righe per colore separate, formato non gestito), niente ESC K
  B5, B6  luminosità da -3 a 3, niente pulsante (ESC !)
  B7, B8  tutto, luminosità da -4 a 3, pulsante
Livelli A, B1-B3, D, F: non supportati (comandi diversi o mancanti).
"""

import time
from dataclasses import dataclass, field

from . import color
from .messages import KeyedError, Note
from .lubsc import LubscAdapter, ScsiError, describe_inquiry

ESC = 0x1B
STX = 0x02
ACK = 0x06
NAK = 0x15

STATUS_FER = 0x80
STATUS_NOT_READY = 0x40
STATUS_AREA_END = 0x20

EXT_STATUS_WARMING = 0x02
FS = 0x1C

MIN_LEVEL = 4

MM_PER_INCH = 25.4


class ScannerError(KeyedError):
    pass


class ScanCancelled(Exception):
    pass


@dataclass
class Identity:
    level: str
    resolutions: list
    max_x: int
    max_y: int
    base_dpi: int
    model: str = ""
    optical_dpi: int = None      # da FS I, se lo scanner lo sa dire

    @property
    def level_num(self):
        """Numero del livello B (es. 7 per "B7"); 0 per gli altri livelli."""
        if self.level[:1] == "B" and self.level[1:2].isdigit():
            return int(self.level[1:2])
        return 0

    @property
    def supported(self):
        return self.level_num >= MIN_LEVEL

    @property
    def color_ok(self):
        return self.level_num >= 5

    @property
    def has_button(self):
        return self.level_num >= 7

    @property
    def brightness_range(self):
        return (-4, 3) if self.level_num >= 7 else (-3, 3)

    @property
    def width_mm(self):
        return self.max_x * MM_PER_INCH / self.base_dpi

    @property
    def height_mm(self):
        return self.max_y * MM_PER_INCH / self.base_dpi


@dataclass
class ScanParams:
    mode: str = "color"          # "color", "gray", "lineart"
    dpi: int = 300
    # risoluzione verticale, se diversa (es. 600 x 50 per la calibrazione righe); None = come dpi
    dpi_y: int = None
    # area in millimetri dall'angolo in alto a sinistra del vetro; None = area massima
    area_mm: tuple = None
    brightness: int = 0          # da -4 a 3
    sharpness: int = 0           # da -2 a 2
    threshold: int = 128         # solo lineart
    preview: bool = False        # velocità alta, per l'anteprima
    # None = curva predefinita dello scanner; un numero = curva personalizzata con quella gamma
    gamma: float = None
    # "scanner" = correzione interna (ESC M 1), "profile" = matrice del modello come SANE, "none" = nessuna
    color_correction: str = "scanner"
    extra: dict = field(default_factory=dict)


@dataclass
class ScanResult:
    width: int
    height: int
    mode: str
    dpi: int
    data: bytes

    @property
    def bytes_per_line(self):
        return bytes_per_line(self.mode, self.width)


def bytes_per_line(mode, width):
    if mode == "color":
        return width * 3
    if mode == "gray":
        return width
    return (width + 7) // 8


class GT10000:
    def __init__(self, adapter=None, target=None, log=None):
        self.log = log or (lambda msg: None)
        self.adapter = adapter or LubscAdapter()
        self.target = target if target is not None else self._find_scanner()
        self.adapter.clear_unit_attention(self.target)
        self.inquiry = describe_inquiry(self.adapter.inquiry(self.target))
        self.initialize()
        self.identity = self.request_identity()
        if not self.identity.supported:
            raise ScannerError("b_level_unsupported", level=self.identity.level)
        self.identity.model = self.request_model() or self.inquiry[1]
        if self.identity.level_num >= 7:
            self.identity.optical_dpi = self.request_optical_dpi()

    def close(self):
        self.adapter.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _find_scanner(self):
        for target, data in self.adapter.scan_bus():
            vendor, product, _ = describe_inquiry(data)
            self.log(Note("b_scsi_device", id=target, device="%s %s" % (vendor, product)))
            if vendor.upper().startswith("EPSON"):
                return target
        raise ScannerError("b_no_scanner")

    # trasporto ESC/I

    def _send(self, data):
        n = len(data)
        self.adapter.command(self.target, bytes([0x0A, 0, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF, 0]),
                             data_out=bytes(data))

    def _recv(self, n, timeout_s=60.0):
        if n <= 0:
            return b""
        out = bytearray()
        # READ(6) porta al massimo 0xFFFFFF byte; restiamo ben sotto per non stressare l'adattatore
        while len(out) < n:
            chunk = min(n - len(out), 0xF000)
            got = self.adapter.command(
                self.target, bytes([0x08, 0, (chunk >> 16) & 0xFF, (chunk >> 8) & 0xFF, chunk & 0xFF, 0]),
                data_in_len=chunk, timeout_s=timeout_s)
            if not got:
                raise ScannerError("b_no_data")
            out += got
        return bytes(out)

    def _expect_ack(self, cmd, params=False):
        r = self._recv(1)
        if r[0] == NAK:
            raise ScannerError("b_nak_params" if params else "b_nak", cmd="ESC " + cmd)
        if r[0] != ACK:
            raise ScannerError("b_unexpected_params" if params else "b_unexpected", cmd="ESC " + cmd, code="%02X" % r[0])

    def cmd_simple(self, cmd):
        self._send(bytes([ESC, ord(cmd)]))
        self._expect_ack(cmd)

    def cmd_param(self, cmd, params):
        self._send(bytes([ESC, ord(cmd)]))
        self._expect_ack(cmd)
        self._send(bytes(params))
        self._expect_ack(cmd, params=True)

    def _info_block(self, cmd):
        self._send(bytes([ESC, ord(cmd)]))
        hdr = self._recv(4)
        if hdr[0] == NAK:
            raise ScannerError("b_esc_unsupported", cmd=cmd)
        if hdr[0] != STX:
            raise ScannerError("b_expected_stx", code="%02X" % hdr[0])
        n = hdr[2] | (hdr[3] << 8)
        return hdr[1], self._recv(n)

    # comandi

    def initialize(self):
        self.cmd_simple("@")

    def request_identity(self):
        _, body = self._info_block("I")
        level = body[0:2].decode("ascii", "replace")
        res = []
        max_x = max_y = 0
        i = 2
        while i + 2 < len(body):
            tag = body[i:i + 1]
            if tag == b"R":
                res.append(body[i + 1] | (body[i + 2] << 8))
                i += 3
            elif tag == b"A":
                max_x = body[i + 1] | (body[i + 2] << 8)
                max_y = body[i + 3] | (body[i + 4] << 8)
                i += 5
            else:
                break
        base = max(res) if res else 600
        return Identity(level=level, resolutions=sorted(set(res)), max_x=max_x, max_y=max_y, base_dpi=base)

    def request_optical_dpi(self):
        """Risoluzione ottica da FS I (identità estesa, livelli B7 e B8), oppure None.

        La risposta è un blocco fisso di 80 byte senza intestazione; chi non conosce il comando
        risponde NAK con un byte solo. Si legge con una sola richiesta, così un NAK non blocca.
        """
        try:
            self._send(bytes([FS, ord("I")]))
            got = self.adapter.command(self.target, bytes([0x08, 0, 0, 0, 80, 0]), data_in_len=80, timeout_s=5.0)
        except ScsiError:
            got = b""
        if len(got) < 8 or got[0] in (NAK, ACK):
            self.initialize()            # stato pulito per i comandi successivi
            return None
        dpi = int.from_bytes(got[4:8], "little")
        return dpi if 100 <= dpi <= 6400 else None

    def request_extended_status(self):
        _, body = self._info_block("f")
        return body

    def button_pressed(self):
        """Pulsante blu di avvio sul pannello: ESC ! (livello B7), primo bit = premuto in questo momento."""
        _, body = self._info_block("!")
        return bool(body) and bool(body[0] & 0x01)

    def request_model(self):
        try:
            body = self.request_extended_status()
        except ScannerError:
            return ""
        return body[26:42].decode("ascii", "replace").strip() if len(body) >= 42 else ""

    def wait_warm_up(self, cancel=None, timeout_s=180):
        deadline = time.monotonic() + timeout_s
        announced = False
        while True:
            body = self.request_extended_status()
            if not (body[0] & EXT_STATUS_WARMING):
                return
            if not announced:
                self.log(Note("b_warming"))
                announced = True
            if cancel and cancel():
                raise ScanCancelled()
            if time.monotonic() > deadline:
                raise ScannerError("b_lamp_timeout")
            time.sleep(1)

    # scansione

    def compute_area(self, p):
        """Ritorna (left, top, width, height) in punti alla risoluzione di scansione."""
        ident = self.identity
        ydpi = p.dpi_y or p.dpi
        full_w = ident.max_x * p.dpi // ident.base_dpi
        full_h = ident.max_y * ydpi // ident.base_dpi
        if p.area_mm is None:
            left, top, width, height = 0, 0, full_w, full_h
        else:
            x, y, w, h = p.area_mm
            left = int(round(x * p.dpi / MM_PER_INCH))
            top = int(round(y * ydpi / MM_PER_INCH))
            width = int(round(w * p.dpi / MM_PER_INCH))
            height = int(round(h * ydpi / MM_PER_INCH))
            left = max(0, min(left, full_w - 8))
            top = max(0, min(top, full_h - 1))
            width = max(8, min(width, full_w - left))
            height = max(1, min(height, full_h - top))
        # larghezza multipla di 8, come fa SANE: evita righe con byte spezzati in lineart
        width &= ~7
        return left, top, width, height

    def scan(self, p: ScanParams, progress=None, cancel=None, on_begin=None, on_data=None):
        """Esegue una scansione.

        Con on_data i blocchi vengono passati man mano e non accumulati (ScanResult.data vuoto).
        on_begin(width, height, bytes_per_line) viene chiamato prima del primo blocco.
        """
        if p.dpi not in self.identity.resolutions:
            raise ScannerError("b_res_unsupported", dpi=p.dpi)
        if p.mode == "color" and not self.identity.color_ok:
            raise ScannerError("b_color_level", level=self.identity.level)
        left, top, width, height = self.compute_area(p)
        bpl = bytes_per_line(p.mode, width)
        self.log(Note("b_scan_start", mode=p.mode, dpi=p.dpi, w=width, h=height, bpl=bpl))

        # dopo uno spegnimento e riaccensione lo scanner riparte con una UNIT ATTENTION
        self.adapter.clear_unit_attention(self.target)
        self.initialize()
        self.wait_warm_up(cancel)

        if p.mode == "color":
            color_mode, depth = 0x13, 8     # B5 e successivi: sequenza di byte RGB
        elif p.mode == "gray":
            color_mode, depth = 0x00, 8
        else:
            color_mode, depth = 0x00, 1
        self.cmd_param("C", [color_mode])
        self.cmd_param("D", [depth])
        if p.mode == "lineart":
            self.cmd_param("B", [0x01])     # nessun retino
        lo, hi = self.identity.brightness_range
        self.cmd_param("L", [max(lo, min(hi, p.brightness)) & 0xFF])
        if p.gamma is None or depth == 1:
            self.cmd_param("Z", [0x01 if depth == 1 else 0x02])   # gamma predefinita
        else:
            # curva personalizzata: ESC Z 3, poi una tabella per canale (ESC z, livello B4 in su)
            self.cmd_param("Z", [0x03])
            table = color.gamma_table(float(p.gamma))
            for channel in b"RGB":
                self.cmd_param("z", bytes([channel]) + table)
        if p.mode == "lineart":
            self.cmd_param("t", [p.threshold & 0xFF])
        if p.mode == "color" and p.color_correction == "none":
            self.cmd_param("M", [0x00])
        else:
            self.cmd_param("M", [0x01])     # correzione colore
            if p.mode == "color" and p.color_correction == "profile":
                self.cmd_param("m", color.color_coefficients())   # matrice del modello (SANE)
        self.cmd_param("Q", [p.sharpness & 0xFF])
        self.cmd_param("g", [1 if p.preview else 0])
        if self.identity.level_num >= 5:
            self.cmd_param("K", [0])     # niente specchio (ESC K, livello B5 in su)
        ydpi = p.dpi_y or p.dpi
        self.cmd_param("R", [p.dpi & 0xFF, p.dpi >> 8, ydpi & 0xFF, ydpi >> 8])
        self.cmd_param("A", [left & 0xFF, left >> 8, top & 0xFF, top >> 8,
                             width & 0xFF, width >> 8, height & 0xFF, height >> 8])
        # righe per blocco: circa 60 KB per richiesta, massimo 255
        lcount = max(1, min(255, 0xF000 // bpl))
        self.cmd_param("d", [lcount])

        if on_begin:
            on_begin(width, height, bpl)
        self._send(bytes([ESC, ord("G")]))
        out = bytearray()
        received = 0
        expected = bpl * height
        while True:
            hdr = self._recv(6)
            if hdr[0] == NAK:
                raise ScannerError("b_start_rejected")
            if hdr[0] != STX:
                raise ScannerError("b_bad_block", code="%02X" % hdr[0])
            status = hdr[1]
            if status & STATUS_FER:
                raise ScannerError("b_fatal", code="%02X" % status)
            if status & STATUS_NOT_READY:
                raise ScannerError("b_busy_other")
            n = (hdr[2] | hdr[3] << 8) * (hdr[4] | hdr[5] << 8)
            block = self._recv(n)
            if p.mode == "color" and (status >> 2) & 0x03 == 0x01:
                block = _grb_to_rgb(block)
            received += len(block)
            if on_data:
                on_data(block)
            else:
                out += block
            if progress:
                progress(min(received, expected), expected)
            if status & STATUS_AREA_END:
                break
            if cancel and cancel():
                self._send(bytes([0x18]))    # CAN: interrompe la scansione
                try:
                    self._recv(1)
                except (ScannerError, ScsiError):
                    pass
                self.initialize()
                raise ScanCancelled()
            self._send(bytes([ACK]))

        lines = received // bpl
        return ScanResult(width=width, height=lines, mode=p.mode, dpi=p.dpi, data=bytes(out[:lines * bpl]))


def _grb_to_rgb(block):
    b = bytearray(block)
    b[0::3], b[1::3] = block[1::3], block[0::3]
    return bytes(b)
