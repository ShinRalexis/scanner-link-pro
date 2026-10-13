# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Scanner Epson GT-10000+: interfaccia Windows.

La scansione vera la fa il motore Linux nella distribuzione WSL "GT10000" (vedi bridge.py);
qui ci sono anteprima, scelta dell'area, impostazioni e salvataggio nei Documenti.
"""

import ctypes
import datetime
import json
import mmap
import os
import re
import shutil
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge  # noqa: E402
import i18n  # noqa: E402
import ui  # noqa: E402
from i18n import Msg, tr  # noqa: E402
from ui import Theme as T  # noqa: E402

try:
    import destripe  # noqa: E402  correzione righe: serve numpy, il resto del programma no
except ImportError:
    destripe = None

APP_NAME = "Scanner Link Pro"
APP_SUBTITLE = "SCSI/USB to Scanner"
# icone: accanto al programma, oppure nella cartella dei dati di PyInstaller se installato
ICON_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GT10000Scanner")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "impostazioni.json")
CALIBRATION_FILE = os.path.join(SETTINGS_DIR, "calibrazione_righe.npz")

MODES = [("mode_color", "color"), ("mode_gray", "gray"), ("mode_lineart", "lineart")]
FORMATS = [("JPEG", "jpg"), ("PNG", "png"), ("TIFF", "tif"), ("PDF", "pdf")]
DPI_CHOICES = [150, 200, 300, 600, 1200]
# compressione per JPEG e PDF: (qualità JPEG, sottocampionamento del colore: 0 = 4:4:4, 2 = 4:2:0).
# Misurato su una pagina A4 a colori: a 300 dpi 1,7 MB con "max", 0,6 MB con "balanced"; a 200 dpi
# con "compact" circa 0,2 MB. Le scansioni di stampa (retino) pesano un po' di più.
QUALITY = {"max": (95, 0), "balanced": (82, 2), "compact": (65, 2)}
# scelta rapida: (chiave, nome, impostazioni); scorciatoie Ctrl+1, Ctrl+2, Ctrl+3 nello stesso ordine
PROFILES = [
    ("document", "profile_document", {"mode": "color", "dpi": 200, "format": "pdf", "quality": "compact"}),
    ("medium", "profile_medium", {"mode": "color", "dpi": 300, "format": "jpg", "quality": "balanced"}),
    ("art", "profile_art", {"mode": "color", "dpi": 600, "format": "tif", "quality": "max"}),
]
# stati dell'adattatore restituiti da bridge.adapter_state() e chiave della loro traduzione
ADAPTER_STATES = {"assente": "state_absent", "non condiviso": "state_not_shared", "condiviso": "state_shared",
                  "collegato": "state_attached", "sconosciuto": "state_unknown", "usbipd mancante": "state_no_usbipd"}
PRESETS = [
    ("preset_glass", "vetro", "full"),
    ("A3", "a3", (297, 420)),
    ("A4", "a4", (210, 297)),
    ("preset_a4_land", "a4o", (297, 210)),
    ("A5", "a5", (148, 210)),
    ("10 x 15", "f10", (100, 150)),
    ("13 x 18", "f13", (130, 180)),
]
LINKS = [
    ("Liberapay", "https://liberapay.com/MetaDarko"),
    ("GitHub", "https://github.com/ShinRalexis/scanner-link-pro"),
]
PREVIEW_DPI = 50
LARGE_SCAN_BYTES = 1024 * 1024 * 1024
LONG_SCAN_SECONDS = 10 * 60
# velocità misurata con l'adattatore USB 1.1; viene aggiornata dopo ogni scansione vera
DEFAULT_SPEED_BPS = 540 * 1024
# misurato il 2026-09-29: oltre 600 dpi il sensore non aggiunge dettaglio in orizzontale
OPTICAL_DPI = 600               # GT-10000+ misurato; gli altri modelli lo dicono con FS I (motore 1.4)
# risoluzione ottica dei modelli che non rispondono a FS I (nome restituito dallo scanner)
KNOWN_OPTICAL = {"GT-10000": 600, "ES-6000": 600}
# le scansioni vere vanno su disco durante l'acquisizione: un A3 a 1200 dpi supera gli 800 MB
SPOOL_DIR = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "GT10000Scanner")


def documents_dir():
    buf = ctypes.create_unicode_buffer(260)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:
        return buf.value
    return os.path.join(os.path.expanduser("~"), "Documents")


human_size = i18n.size
human_time = i18n.duration


def gamma_of(step):
    """Gradino del cursore Gamma: 0 = curva standard dello scanner (circa 2,2, misurata), +-0,2 per gradino."""
    return None if step == 0 else round(2.2 + 0.2 * step, 1)


def threshold_of(step):
    """Gradino del cursore Soglia (bianco e nero): 128 al centro, 24 livelli per gradino."""
    return max(1, min(254, 128 + 24 * step))


def encoder_options(fmt, img_mode, quality):
    """Parametri di Pillow per salvare: qualità e colore per JPEG e PDF; nel PDF il bianco e nero resta a
    1 bit e Pillow usa la compressione dei fax (CCITT G4), che con un parametro di qualità darebbe errore."""
    q, sub = QUALITY.get(quality, QUALITY["max"])
    if fmt == "jpg" or (fmt == "pdf" and img_mode != "1"):
        return {"quality": q, "subsampling": sub}
    return {}


def label_of(key):
    """Etichetta tradotta; le sigle come "A3" o "10 x 15" non hanno traduzione e restano come sono."""
    return tr(key) if key in i18n.STRINGS else key


def bytes_per_line(mode, width):
    return width * 3 if mode == "color" else width if mode == "gray" else (width + 7) // 8


def image_from(mode, width, height, data):
    if mode == "color":
        return Image.frombytes("RGB", (width, height), data)
    if mode == "gray":
        return Image.frombytes("L", (width, height), data)
    # il GT-10000 manda bit 1 = bianco, come il modo "1" di Pillow (misurato su carta bianca:
    # 100% dei punti a 1); un decoder invertito produceva scansioni in negativo
    return Image.frombytes("1", (width, height), data)


def clean_spool():
    """Toglie i file temporanei di scansioni interrotte da una chiusura brusca (più vecchi di un giorno)."""
    try:
        for name in os.listdir(SPOOL_DIR):
            path = os.path.join(SPOOL_DIR, name)
            if name.endswith(".raw") and time.time() - os.path.getmtime(path) > 86400:
                os.remove(path)
    except OSError:
        pass


def load_icons():
    """Icona del programma: piastrella completa per le misure grandi, solo scanner e cavo per le piccole."""
    big = Image.open(os.path.join(ICON_DIR, "icona.png")).convert("RGBA")
    small = Image.open(os.path.join(ICON_DIR, "icona_piccola.png")).convert("RGBA")
    return [big.resize((s, s), Image.LANCZOS) for s in (256, 64)] + \
        [small.resize((s, s), Image.LANCZOS) for s in (48, 32, 16)]


def ellipsize_middle(text, limit):
    return text if len(text) <= limit else text[:limit // 2 - 1] + "..." + text[-(limit // 2 - 2):]


def system_language():
    """Lingua di Windows, se il programma la conosce; altrimenti inglese (primo avvio senza impostazioni)."""
    codes = {0x10: "it", 0x09: "en", 0x0A: "es", 0x07: "de", 0x0C: "fr", 0x11: "ja", 0x12: "ko", 0x04: "zh",
             0x19: "ru"}
    try:
        return codes.get(ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF, "en")
    except (AttributeError, OSError):
        return "en"


class Settings:
    def __init__(self):
        self.data = {"mode": "color", "dpi": 300, "format": "jpg", "prefix": "Scansione",
                     "folder": os.path.join(documents_dir(), "Scansioni GT-10000"),
                     "brightness": 0, "sharpness": 0, "area_mm": None, "preset": "a4",
                     "speed_bps": DEFAULT_SPEED_BPS, "language": system_language(),
                     "gamma_step": 0, "threshold_step": 0, "pages": "single", "streaks": "off",
                     "quality": "max"}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (OSError, ValueError):
            pass
        if self.data.get("preset") not in [p[1] for p in PRESETS] + ["custom"]:
            self.data["preset"] = "custom" if self.data.get("area_mm") else "a4"

    def save(self):
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass


class StreakHelp:
    """Finestra che spiega la correzione righe: disegno prima e dopo, quattro risposte brevi, calibrazione."""

    SECTIONS = [("streaks_help_h1", "streaks_help_b1"), ("streaks_help_h2", "streaks_help_b2"),
                ("streaks_help_h3", "streaks_help_b3"), ("streaks_help_h4", "streaks_help_b4")]

    def __init__(self, app):
        self.app = app
        t, px = app.t, app.t.px
        width = px(468)
        win = self.win = tk.Toplevel(app.root, bg=T.PANEL)
        win.withdraw()
        win.title(tr("lbl_streaks") + " - " + APP_NAME)
        win.transient(app.root)
        win.resizable(False, False)
        body = tk.Frame(win, bg=T.PANEL)
        body.pack(fill="both", expand=True, padx=px(26), pady=(px(22), px(20)))
        tk.Label(body, text=tr("lbl_streaks"), bg=T.PANEL, fg=T.TEXT, font=t.font_title, anchor="w").pack(fill="x")

        self.art = tk.Canvas(body, width=width, height=px(168), bg=T.PANEL, highlightthickness=0, bd=0)
        self.art.pack(pady=(px(14), px(2)))
        self.draw_art(width, px(168))

        for head, text in self.SECTIONS:
            tk.Label(body, text=tr(head), bg=T.PANEL, fg=T.TEXT, font=t.font_strong, anchor="w").pack(
                fill="x", pady=(px(12), px(3)))
            tk.Label(body, text=tr(text), bg=T.PANEL, fg=T.TEXT_2, font=t.font, anchor="w", justify="left",
                     wraplength=width).pack(fill="x")

        # stato della calibrazione, con il pallino come nella barra in alto
        cal = app.calibration
        state = tk.Frame(body, bg=T.PANEL)
        state.pack(fill="x", pady=(px(16), 0))
        dot = ui.StatusDot(state, t)
        dot.set("ok" if cal else "wait")
        dot.pack(side="left", padx=(0, px(8)))
        text = (tr("streaks_info", date=cal.date, n=cal.visible_streaks("color")) if cal
                else tr("streaks_help_not_cal"))
        tk.Label(state, text=text, bg=T.PANEL, fg=T.TEXT_2, font=t.font_small, anchor="w").pack(side="left")

        tk.Frame(body, bg=T.BORDER, height=1).pack(fill="x", pady=(px(14), px(14)))
        buttons = tk.Frame(body, bg=T.PANEL)
        buttons.pack(fill="x")
        close = ui.Button(buttons, t, tr("btn_close"), self.close, height=36)
        close.fit_width(px(96))
        close.pack(side="right")
        ready = destripe is not None and app.scanner_info is not None and app.job is None
        calib = ui.Button(buttons, t, tr("btn_calibrate_now"), self.calibrate,
                          kind="secondary" if cal else "primary", height=36)
        calib.fit_width(px(120))
        calib.pack(side="right", padx=(0, px(8)))
        calib.set_enabled(ready)
        if not ready:
            hint = tr("streaks_no_numpy") if destripe is None else tr("streaks_help_need_scanner")
            tk.Label(buttons, text=hint, bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w", justify="left",
                     wraplength=width - px(260)).pack(side="left", fill="x")

        win.bind("<Escape>", lambda e: self.close())
        win.protocol("WM_DELETE_WINDOW", self.close)
        # centrata sulla finestra principale
        win.update_idletasks()
        root = app.root
        x = root.winfo_rootx() + (root.winfo_width() - win.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - win.winfo_reqheight()) // 3
        win.geometry("+%d+%d" % (max(0, x), max(0, y)))
        win.deiconify()
        ui.dark_title_bar(win)
        win.grab_set()
        close.focus_set()

    def draw_art(self, width, height):
        """Due pagine di rivista: a sinistra con la riga ciano, a destra pulita; freccia in mezzo."""
        c, px = self.art, self.app.t.px
        gap = px(56)
        pw, ph = (width - gap) // 2, height - px(26)
        for i, x in enumerate((0, pw + gap)):
            streak = i == 0
            ui.rounded_rect(c, x, 0, x + pw, ph, px(6), fill="#f3f0e8", outline="")
            # foto in alto, titolo e righe di testo sotto
            m = px(12)
            c.create_rectangle(x + m, m, x + pw - m, m + ph * 0.42, fill="#c9714c", outline="")
            c.create_rectangle(x + m, m + ph * 0.24, x + pw - m, m + ph * 0.42, fill="#8a5a43", outline="")
            c.create_oval(x + pw * 0.62, m + px(8), x + pw * 0.62 + px(22), m + px(30), fill="#f2c46b", outline="")
            y = m + ph * 0.42 + px(10)
            c.create_rectangle(x + m, y, x + pw * 0.66, y + px(7), fill="#5b5750", outline="")
            y += px(15)
            while y + px(4) < ph - m:
                right = x + pw - m - (px(28) if int(y) % 3 == 0 else 0)
                c.create_rectangle(x + m, y, right, y + px(4), fill="#cbc6ba", outline="")
                y += px(9)
            if streak:
                # la riga: meno rosso e meno verde, su tutta l'altezza della pagina
                sx = x + int(pw * 0.42)
                sw = max(2, px(4))
                c.create_rectangle(sx, 0, sx + sw, ph, fill="#c9e6ea", outline="")
                c.create_rectangle(sx, m, sx + sw, m + ph * 0.24, fill="#97705f", outline="")
                c.create_rectangle(sx, m + ph * 0.24, sx + sw, m + ph * 0.42, fill="#5f5246", outline="")
                y = m + ph * 0.42 + px(10)
                c.create_rectangle(sx, y, sx + sw, y + px(7), fill="#3d4a4c", outline="")
                y += px(15)
                while y + px(4) < ph - m:
                    c.create_rectangle(sx, y, sx + sw, y + px(4), fill="#a4c2c4", outline="")
                    y += px(9)
            label = tr("streaks_help_before" if streak else "streaks_help_after")
            c.create_text(x + pw / 2, ph + px(14), text=label, fill=T.TEXT_3, font=self.app.t.font_small)
        # freccia
        ax, ay = pw + gap / 2, ph / 2
        s = px(10)
        c.create_line(ax - s, ay, ax + s, ay, fill=T.ACCENT_BRIGHT, width=max(2, px(2)), capstyle="round")
        c.create_line(ax + s * 0.3, ay - s * 0.7, ax + s, ay, ax + s * 0.3, ay + s * 0.7, fill=T.ACCENT_BRIGHT,
                      width=max(2, px(2)), capstyle="round", joinstyle="round")

    def close(self):
        try:
            self.win.grab_release()
        except tk.TclError:
            pass
        self.win.destroy()

    def calibrate(self):
        self.close()
        self.app.start_calibration()


class App:
    def __init__(self, root):
        self.root = root
        self.settings = Settings()
        self.backend = None
        self.scanner_info = None
        self.job = None            # scansione in corso
        self.job_counter = 0
        self.preview_image = None  # anteprima a PREVIEW_DPI dell'intero vetro
        self.glass_mm = (297.18, 431.8)
        self.area_mm = self.settings.data.get("area_mm")
        self.resolutions = [50, 75, 100, 150, 200, 300, 400, 600, 800, 1200, 1600, 2400]
        self.drag = None
        self.last_file = None
        self.closing = False
        self.events_local = []     # eventi dai thread di lavoro (append è atomico)
        self._base_cache = None
        # testi conservati come Msg: al cambio di lingua l'interfaccia li ritraduce
        self._status = (Msg("status_starting"), "wait")
        self._progress = (None, 0.0, True)
        self.log_entries = []
        self.last_info = None
        self.sequence = None       # sequenza di pagine in corso
        self.calibration = self.load_calibration()
        self.calib = None          # calibrazione righe in corso: letture fatte e da fare
        self.recovery_tried = False  # già tentato di ricollegare l'adattatore bloccato?
        self.expanded = {"adjust": False, "streaks": False}    # sezioni a tendina: chiuse all'avvio
        i18n.set_language(self.settings.data.get("language", "it"))

        root.title(APP_NAME)
        # con la scala di Windows (es. 150%) Tk ragiona in pixel fisici: dimensioni proporzionate
        self.f = root.winfo_fpixels("1i") / 96.0
        self.t = T(root, self.f, i18n.language())
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = int(min(sw * 0.86, 1280 * self.f)), int(min(sh * 0.92, 980 * self.f))
        # invisibile finché non è centrata, così non si vede il salto di posizione
        root.attributes("-alpha", 0.0)
        root.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 2))
        root.minsize(int(960 * self.f), int(680 * self.f))
        root.configure(bg=T.BG)
        try:
            root.iconbitmap(default=os.path.join(ICON_DIR, "icona.ico"))
            self._icons = [ImageTk.PhotoImage(im) for im in load_icons()]
            root.iconphoto(True, *self._icons)
        except (OSError, tk.TclError):
            pass
        root.option_add("*Menu.background", T.FIELD)
        root.option_add("*Menu.foreground", T.TEXT)
        root.option_add("*Menu.activeBackground", T.ACCENT)
        root.option_add("*Menu.activeForeground", "#ffffff")
        self._build()
        ui.dark_title_bar(root)
        root.update()
        ui.center_on_work_area(root)
        root.attributes("-alpha", 1.0)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Control-Return>", lambda e: self.start_scan())
        for i, (key, _, _) in enumerate(PROFILES):
            root.bind("<Control-Key-%d>" % (i + 1), lambda e, k=key: self.apply_profile(k))
        root.bind("<Escape>", lambda e: self.cancel_scan())
        root.after(100, self.poll_events)
        root.after(200, self.connect)
        clean_spool()

    # costruzione interfaccia

    def _build(self):
        t, px = self.t, self.t.px

        top = tk.Frame(self.root, bg=T.PANEL, height=px(52))
        top.pack(fill="x")
        top.pack_propagate(False)
        # marchio: icona, nome e sottotitolo
        brand = tk.Frame(top, bg=T.PANEL)
        brand.pack(side="left", padx=(px(16), px(18)))
        try:
            mark = Image.open(os.path.join(ICON_DIR, "icona_piccola.png")).convert("RGBA")
            self._brand_icon = ImageTk.PhotoImage(mark.resize((px(32), px(32)), Image.LANCZOS))
            tk.Label(brand, image=self._brand_icon, bg=T.PANEL, bd=0).pack(side="left", padx=(0, px(10)))
        except OSError:
            pass
        names = tk.Frame(brand, bg=T.PANEL)
        names.pack(side="left")
        tk.Label(names, text=APP_NAME, bg=T.PANEL, fg=T.TEXT, font=t.font_title, anchor="w").pack(fill="x")
        tk.Label(names, text=APP_SUBTITLE, bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w").pack(fill="x")
        self.status_dot = ui.StatusDot(top, t)
        self.status_dot.pack(side="left", padx=(0, px(8)))
        self.status_label = tk.Label(top, text="", bg=T.PANEL, fg=T.TEXT_2, font=t.font, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.reconnect_btn = ui.Button(top, t, tr("btn_reconnect"), self.connect, height=32)
        self.reconnect_btn.fit_width(px(110))
        self.reconnect_btn.pack(side="right", padx=(px(8), px(16)))
        self.lang_btn = ui.Button(top, t, i18n.language_name(), self.show_language_menu, height=32, chevron=True)
        self.lang_btn.fit_width(px(110))
        self.lang_btn.pack(side="right")
        ui.Tooltip(self.lang_btn, t, lambda: tr("lbl_language"))
        # ultima scansione: miniatura e nome, cliccabili, a sinistra di Riconnetti
        self.last_frame = tk.Frame(top, bg=T.PANEL, cursor="hand2")
        self.last_thumb = tk.Label(self.last_frame, bg=T.FIELD, bd=0)
        self.last_thumb.pack(side="left", padx=(0, px(10)))
        info = tk.Frame(self.last_frame, bg=T.PANEL)
        info.pack(side="left")
        self.last_name = tk.Label(info, text="", bg=T.PANEL, fg=T.TEXT, font=t.font_small, anchor="w")
        self.last_name.pack(fill="x")
        self.last_detail = tk.Label(info, text="", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w")
        self.last_detail.pack(fill="x")
        for wdg in (self.last_frame, self.last_thumb, info, self.last_name, self.last_detail):
            wdg.bind("<Button-1>", lambda e: self.open_last())
        tk.Frame(self.root, bg=T.BORDER, height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=T.BG)
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=T.PANEL, width=px(344))
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        tk.Frame(body, bg=T.BORDER, width=1).pack(side="right", fill="y")
        self._build_side(side)

        center = tk.Frame(body, bg=T.BG)
        center.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(center, bg=T.BG, highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, padx=px(8), pady=(px(8), 0))
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        bar = tk.Frame(center, bg=T.BG)
        bar.pack(fill="x", padx=px(20), pady=(px(6), px(14)))
        self.preset_var = tk.StringVar(value=self.settings.data.get("preset", "a4"))
        self.preset_seg = ui.Segmented(bar, t, [(label_of(p[0]), p[1]) for p in PRESETS], self.preset_var,
                                       command=self.apply_preset, height=30)
        self.preset_seg.configure(width=px(520))
        self.preset_seg.pack(side="left")
        self.area_label = tk.Label(bar, text="", bg=T.BG, fg=T.TEXT_2, font=t.font, anchor="e")
        self.area_label.pack(side="right")

        self.set_status(Msg("status_starting"), "wait")
        self.set_busy(True)
        self.apply_preset(initial=True)

    def _section(self, parent, title, first=False):
        px = self.t.px
        tk.Label(parent, text=title, bg=T.PANEL, fg=T.TEXT, font=self.t.font_section, anchor="w").pack(
            fill="x", pady=(0 if first else px(16), px(6)))

    def _field_label(self, parent, text):
        row = tk.Frame(parent, bg=T.PANEL)
        row.pack(fill="x", pady=(0, self.t.px(3)))
        ui.label(row, self.t, text).pack(side="left")
        return row

    def _build_side(self, side):
        t, px = self.t, self.t.px
        # in basso, sempre visibili: stima, avanzamento, pulsanti e link
        bottom = tk.Frame(side, bg=T.PANEL)
        bottom.pack(side="bottom", fill="x", padx=px(22), pady=(0, px(14)))
        # sopra, le impostazioni: scorrono se lo schermo non è abbastanza alto
        self.side_scroll = ui.ScrollArea(side, t)
        self.side_scroll.pack(fill="both", expand=True, pady=(px(16), 0))
        inner = tk.Frame(self.side_scroll.body, bg=T.PANEL)
        inner.pack(fill="both", expand=True, padx=(px(22), px(12)), pady=(0, px(10)))

        # scelta rapida: tre profili che impostano modalità, risoluzione, formato e compressione
        self._section(inner, tr("sec_quick"), first=True)
        self.profile_cards = ui.ProfileCards(
            inner, t, [(tr(name), self.profile_detail(key), key) for key, name, _ in PROFILES],
            self.active_profile, self.apply_profile,
            tip_fn=lambda i: tr(PROFILES[i][1] + "_tip", shortcut="Ctrl+%d" % (i + 1)))
        self.profile_cards.pack(fill="x")

        self._section(inner, tr("sec_acquisition"))
        self._field_label(inner, tr("lbl_mode"))
        self.mode_var = tk.StringVar(value=self.settings.data["mode"])
        self.mode_seg = ui.Segmented(inner, t, [(tr(k), v) for k, v in MODES], self.mode_var, command=self.update_estimate)
        self.mode_seg.pack(fill="x", pady=(0, px(8)))

        row = self._field_label(inner, tr("lbl_resolution"))
        self.dpi_var = tk.StringVar(value=str(self.settings.data["dpi"]))
        self.more_dpi = ui.link(row, t, tr("dpi_more"), self.show_dpi_menu)
        self.more_dpi.pack(side="right")
        self.dpi_seg = ui.Segmented(inner, t, [(str(d), str(d)) for d in DPI_CHOICES], self.dpi_var,
                                    command=self.update_estimate)
        self.dpi_seg.pack(fill="x")
        self.dpi_note = tk.Label(inner, text="", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w",
                                 justify="left", wraplength=px(296))
        self.dpi_note.pack(fill="x", pady=(px(6), 0))

        # Regolazioni e Correzione righe: a tendina, chiuse all'avvio; a destra un promemoria dello stato
        adjust = self.adjust_box = ui.Collapsible(inner, t, tr("sec_adjust"), self.expanded["adjust"],
                                                  on_toggle=lambda v: self.expanded.__setitem__("adjust", v))
        adjust.pack(fill="x", pady=(px(16), 0))
        box = adjust.body
        self._field_label(box, tr("lbl_brightness"))
        self.bright_var = tk.IntVar(value=self.settings.data["brightness"])
        self.bright = ui.Slider(box, t, self.bright_var, -4, 3)
        self.bright.pack(fill="x", pady=(0, px(2)))
        self._field_label(box, tr("lbl_sharpness"))
        self.sharp_var = tk.IntVar(value=self.settings.data["sharpness"])
        self.sharp = ui.Slider(box, t, self.sharp_var, -2, 2)
        self.sharp.pack(fill="x", pady=(0, px(2)))
        # terzo cursore: Gamma per colore e grigi, Soglia per il bianco e nero
        tone_row = tk.Frame(box, bg=T.PANEL)
        tone_row.pack(fill="x", pady=(0, px(3)))
        self.tone_label = ui.label(tone_row, t, "")
        self.tone_label.pack(side="left")
        self.tone_box = tk.Frame(box, bg=T.PANEL)
        self.tone_box.pack(fill="x")
        self.gamma_var = tk.IntVar(value=self.settings.data.get("gamma_step", 0))
        self.gamma = ui.Slider(self.tone_box, t, self.gamma_var, -4, 4, value_width=82,
                               fmt=lambda v: tr("gamma_standard") if v == 0 else "γ " + i18n.number(gamma_of(v)))
        self.thr_var = tk.IntVar(value=self.settings.data.get("threshold_step", 0))
        self.thr = ui.Slider(self.tone_box, t, self.thr_var, -4, 4, value_width=48,
                             fmt=lambda v: str(threshold_of(v)))
        for var in (self.bright_var, self.sharp_var, self.gamma_var, self.thr_var):
            var.trace_add("write", lambda *a: self.update_adjust_summary())

        streaks = self.streak_box = ui.Collapsible(inner, t, tr("lbl_streaks"), self.expanded["streaks"],
                                                   on_toggle=lambda v: self.expanded.__setitem__("streaks", v))
        streaks.pack(fill="x", pady=(px(16), 0))
        self.streak_help_btn = ui.InfoButton(streaks.extra, t, self.show_streak_help)
        self.streak_help_btn.pack(side="left")
        ui.Tooltip(self.streak_help_btn, t, lambda: tr("streaks_help_tip"))
        box = streaks.body
        self.streak_var = tk.StringVar(value=self.settings.data.get("streaks", "off") if self.calibration else "off")
        self.streak_seg = ui.Segmented(box, t, [(tr("streaks_off"), "off"), (tr("streaks_on"), "on")],
                                       self.streak_var, command=self.on_streaks_changed)
        self.streak_seg.pack(fill="x")
        self.streak_var.trace_add("write", lambda *a: self.update_streak_summary())
        self.streak_note = tk.Label(box, text="", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w",
                                    justify="left", wraplength=px(296))
        self.streak_note.pack(fill="x", pady=(px(6), 0))
        self.calib_link = ui.link(box, t, tr("streaks_calibrate"), self.start_calibration)
        self.calib_link.pack(anchor="w", pady=(px(4), 0))
        self.update_adjust_summary()
        self.update_streak_summary()

        self._section(inner, tr("sec_file"))
        self.format_var = tk.StringVar(value=self.settings.data["format"])
        self.format_seg = ui.Segmented(inner, t, FORMATS, self.format_var, command=self.update_estimate)
        self.format_seg.pack(fill="x", pady=(0, px(8)))
        # compressione: solo dove il formato la permette (JPEG, PDF a colori o in grigi)
        self.quality_box = tk.Frame(inner, bg=T.PANEL)
        self.quality_box.pack(fill="x")
        self.quality_row = self._field_label(self.quality_box, tr("lbl_quality"))
        self.quality_var = tk.StringVar(value=self.settings.data.get("quality", "max"))
        self.quality_seg = ui.Segmented(self.quality_box, t, [(tr("quality_max"), "max"),
                                                              (tr("quality_balanced"), "balanced"),
                                                              (tr("quality_compact"), "compact")],
                                        self.quality_var, command=self.update_estimate)
        self.quality_seg.pack(fill="x", pady=(0, px(8)))
        self.quality_note = tk.Label(self.quality_box, text="", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small,
                                     anchor="w", justify="left", wraplength=px(296))
        self._field_label(inner, tr("lbl_pages"))
        self.pages_var = tk.StringVar(value=self.settings.data.get("pages", "single"))
        self.pages_seg = ui.Segmented(inner, t, [(tr("pages_single"), "single"), (tr("pages_sequence"), "sequence")],
                                      self.pages_var, command=self.on_pages_changed)
        self.pages_seg.pack(fill="x")
        # riga della nota: visibile solo in Sequenza, altrimenti lascerebbe uno spazio vuoto
        seq_row = self.seq_row = tk.Frame(inner, bg=T.PANEL)
        seq_row.pack(fill="x", pady=(px(3), px(6)))
        self._seq_row_pady = (px(3), px(6))
        self.seq_note = tk.Label(seq_row, text="", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small, anchor="w",
                                 justify="left", wraplength=px(200))
        self.seq_note.pack(side="left", fill="x", expand=True)
        self.seq_end_link = ui.link(seq_row, t, tr("seq_end"), self.end_sequence)
        self._field_label(inner, tr("lbl_name"))
        self.prefix_var = tk.StringVar(value=self.settings.data["prefix"])
        self.prefix_entry = ui.entry(inner, t, self.prefix_var)
        self.prefix_entry.pack(fill="x", ipady=px(4), pady=(0, px(8)))
        self._field_label(inner, tr("lbl_folder"))
        self.folder_var = tk.StringVar(value=self.settings.data["folder"])
        self.folder_field = ui.PathField(inner, t, self.folder_var, self.choose_folder)
        self.folder_field.pack(fill="x")
        folder_buttons = tk.Frame(inner, bg=T.PANEL)
        folder_buttons.pack(fill="x", pady=(px(8), 0))
        folder_buttons.columnconfigure((0, 1), weight=1, uniform="cartella")
        ui.Button(folder_buttons, t, tr("btn_change_folder"), self.choose_folder, height=32).grid(
            row=0, column=0, sticky="ew", padx=(0, px(4)))
        ui.Button(folder_buttons, t, tr("btn_open_folder"), self.open_folder, height=32).grid(
            row=0, column=1, sticky="ew", padx=(px(4), 0))

        # parte bassa (creata in cima al metodo): stima, avanzamento, azioni, registro, link

        foot = tk.Frame(bottom, bg=T.PANEL)
        foot.pack(side="bottom", fill="x", pady=(px(12), 0))
        self.log_toggle = ui.link(foot, t, tr("log_show"), self.toggle_log)
        self.log_toggle.pack(side="left")
        for i, (text, url) in enumerate(reversed(LINKS)):
            if i:
                tk.Label(foot, text="·", bg=T.PANEL, fg=T.TEXT_3, font=t.font_small).pack(side="right", padx=px(6))
            ui.link(foot, t, text, lambda u=url: webbrowser.open(u)).pack(side="right")

        # il registro sta in una finestra a parte: è diagnostica, il pannello resta alle impostazioni
        self.log_win = tk.Toplevel(self.root, bg=T.PANEL)
        self.log_win.title(tr("log_window_title") + " - " + APP_NAME)
        self.log_win.geometry("%dx%d" % (px(620), px(360)))
        self.log_win.protocol("WM_DELETE_WINDOW", self.toggle_log)
        self.log_win.withdraw()
        self.log_text = tk.Text(self.log_win, font=t.font_mono, wrap="word", relief="flat",
                                bg=T.BG, fg=T.TEXT_2, insertbackground=T.TEXT, selectbackground=T.ACCENT,
                                padx=px(12), pady=px(10), state="disabled", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True)

        buttons = tk.Frame(bottom, bg=T.PANEL)
        buttons.pack(side="bottom", fill="x", pady=(px(14), px(4)))
        buttons.columnconfigure(0, weight=2)
        buttons.columnconfigure(1, weight=3)
        self.preview_btn = ui.Button(buttons, t, tr("btn_preview"), self.start_preview, height=40)
        self.preview_btn.grid(row=0, column=0, sticky="ew", padx=(0, px(8)))
        self.scan_btn = ui.Button(buttons, t, tr("btn_scan"), self.start_scan, kind="primary", height=40)
        self.scan_btn.grid(row=0, column=1, sticky="ew")

        self.progress = ui.Progress(bottom, t)
        self.progress.pack(side="bottom", fill="x", pady=(px(8), 0))
        self.progress_label = tk.Label(bottom, text="", bg=T.PANEL, fg=T.TEXT_2, font=t.font_small, anchor="w")
        self.progress_label.pack(side="bottom", fill="x")

        self.summary = tk.Label(bottom, text="", bg=T.PANEL, fg=T.TEXT, font=t.font_strong, anchor="w")
        self.summary.pack(side="bottom", fill="x", pady=(px(10), px(2)))
        tk.Frame(bottom, bg=T.BORDER, height=1).pack(side="bottom", fill="x")

    # stato e registro

    @staticmethod
    def as_msg(text):
        """Msg dell'interfaccia così com'è; testo del motore Linux riconosciuto e reso traducibile."""
        return text if isinstance(text, Msg) else i18n.from_backend(str(text))

    @classmethod
    def engine_msg(cls, msg):
        """Messaggio del motore: con chiave dal motore 1.1 in poi, altrimenti riconosciuto dal testo."""
        if isinstance(msg.get("message"), Msg):
            return msg["message"]
        key = msg.get("key")
        if key in i18n.STRINGS:
            return Msg(key, **msg.get("args", {}))
        return cls.as_msg(msg.get("message", ""))

    def set_status(self, text, level="ok"):
        msg = self.as_msg(text)
        self._status = (msg, level)
        self.status_dot.set(level)
        self.status_label.configure(text=str(msg), fg=T.ERROR if level == "error" else T.TEXT_2)

    def set_progress_text(self, msg):
        self._progress = (msg, self._progress[1], self._progress[2])
        self.progress_label.configure(text=str(msg) if msg else "")

    def set_progress(self, value, active=True):
        self._progress = (self._progress[0], value, active)
        self.progress.set(value, active=active)

    def log(self, text):
        msg = self.as_msg(text)
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_entries.append((stamp, msg))
        self._log_append(stamp, msg)

    def _log_append(self, stamp, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", "%s  %s\n" % (stamp, msg))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def toggle_log(self):
        if self.log_win.state() == "withdrawn":
            self.log_win.deiconify()
            ui.dark_title_bar(self.log_win)
            self.log_text.see("end")
            self.log_toggle.configure(text=tr("log_hide"))
        else:
            self.log_win.withdraw()
            self.log_toggle.configure(text=tr("log_show"))

    def set_busy(self, busy, scanning=False):
        ready = not busy and self.scanner_info is not None
        self.preview_btn.set_enabled(ready)
        if scanning:
            self.scan_btn.set(text=tr("btn_cancel"), kind="danger", command=self.cancel_scan)
            self.scan_btn.set_enabled(True)
        else:
            self.scan_btn.set(text=tr("btn_scan"), kind="primary", command=self.start_scan)
            self.scan_btn.set_enabled(ready)
        self.reconnect_btn.set_enabled(not scanning)
        self.lang_btn.set_enabled(not scanning)
        for wdg in (self.mode_seg, self.dpi_seg, self.format_seg, self.preset_seg, self.bright, self.sharp,
                    self.gamma, self.thr, self.pages_seg, self.streak_seg, self.profile_cards, self.quality_seg):
            wdg.set_enabled(not scanning)

    # connessione

    def connect(self):
        if self.job:
            return
        self.scanner_info = None
        self.recovery_tried = False
        self.set_busy(True)
        self.set_status(Msg("status_linux_starting"), "wait")
        if self.backend:
            self.backend.stop()
            self.backend = None
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        post = lambda kind, **msg: self.events_local.append((kind, msg))  # noqa: E731
        try:
            if not bridge.distro_installed():
                # primo avvio del programma installato: il Linux interno si importa dal backup
                if not os.path.exists(bridge.LINUX_BACKUP):
                    post("fatal", message=Msg("fatal_no_distro", name=bridge.DISTRO))
                    return
                if not bridge.wsl_available():
                    post("fatal", message=Msg("fatal_no_wsl"))
                    return
                post("status", message=Msg("status_preparing_linux"))
                ok, out = bridge.import_distro()
                if out:
                    post("log", message=Msg(raw=out))
                if not ok:
                    post("fatal", message=Msg("fatal_virtualization" if bridge.virtualization_problem(out)
                                              else "fatal_linux_import"))
                    return
                post("log", message=Msg("log_linux_imported", path=bridge.LINUX_HOME))
            if not bridge.usbipd_exe():
                post("fatal", message=Msg("fatal_no_usbipd"))
                return
            state, busid = bridge.adapter_state()
            state_msg = Msg(ADAPTER_STATES.get(state, "state_unknown"))
            if busid:
                post("log", message=Msg("log_adapter_state_bus", state=state_msg, bus=busid))
            else:
                post("log", message=Msg("log_adapter_state", state=state_msg))
            if state == "assente":
                post("fatal", message=Msg("fatal_adapter_absent"))
                return
            if state == "non condiviso":
                post("status", message=Msg("status_need_auth"))
                bridge.bind_adapter_elevated()
                state, busid = bridge.adapter_state()
                if state == "non condiviso":
                    post("fatal", message=Msg("fatal_auth_denied"))
                    return
            if bridge.sync_driver():
                post("log", message=Msg("log_driver_updated"))
            backend = bridge.Backend()
            backend.start()
            post("backend", backend=backend)
            if state != "collegato":
                post("status", message=Msg("status_attaching"))
                # a freddo WSL impiega qualche secondo ad avviarsi: si riprova
                ok, out = False, ""
                for attempt in range(4):
                    time.sleep(1.0 + 2 * attempt)
                    ok, out = bridge.attach_adapter()
                    if ok or bridge.adapter_state()[0] == "collegato":
                        ok = True
                        break
                if not ok:
                    post("log", message=Msg(raw=out))
                    post("fatal", message=Msg("fatal_attach_failed"))
                    return
            backend.send(cmd="open", wait_s=30)
        except Exception as e:
            post("fatal", message=Msg("fatal_startup_error", error=e))

    def poll_events(self):
        while self.events_local:
            kind, msg = self.events_local.pop(0)
            self.handle(kind, msg)
        if self.backend:
            try:
                for _ in range(200):
                    kind, msg = self.backend.events.get_nowait()
                    self.handle(kind, msg)
            except Exception:
                pass
        if not self.closing:
            self.root.after(30, self.poll_events)

    def ready_text(self):
        i = self.scanner_info
        return Msg("ready", vendor=i["vendor"], model=i["model"], fw=i["firmware"], id=i["scsi_id"])

    def handle(self, kind, msg):
        if kind == "backend":
            self.backend = msg["backend"]
        elif kind == "log":
            self.log(self.engine_msg(msg))
        elif kind == "status":
            self.set_status(self.engine_msg(msg), "wait")
            self.log(self.engine_msg(msg))
        elif kind == "fatal":
            self.set_status(msg["message"], "error")
            self.log(msg["message"])
            self.set_busy(False)
        elif kind == "hello":
            self.log(Msg("log_engine_started", version=msg.get("python")))
        elif kind == "opened":
            self.on_opened(msg)
        elif kind == "button":
            self.on_button()
        elif kind == "begin":
            self.on_begin(msg)
        elif kind == "data":
            self.on_data(msg)
        elif kind == "end":
            self.on_end(msg)
        elif kind == "saved":
            self.on_saved(msg)
        elif kind == "calibrated":
            self.on_calibrated(msg["calibration"])
        elif kind == "calib_offsets":
            self.on_calib_offsets(msg["calibration"], msg["target"])
        elif kind == "calib_error":
            self.log(Msg("log_error", error=msg["message"]))
            self.finish_job(Msg("calib_failed"))
            messagebox.showerror(APP_NAME, tr("dlg_calib_error", error=msg["message"]))
        elif kind == "save_error":
            self.log(Msg("log_save_error", error=msg["message"]))
            self.finish_job(Msg("progress_save_error"))
            messagebox.showerror(APP_NAME, tr("dlg_save_error", error=msg["message"]))
        elif kind == "cancelled":
            self.log(Msg("scan_cancelled"))
            self.finish_job(Msg("scan_cancelled"))
        elif kind == "error":
            error = self.engine_msg(msg) if msg.get("message") else Msg("error_generic")
            self.log(Msg("log_error", error=error))
            if msg.get("trace"):
                self.log(Msg(raw=msg["trace"]))
            if self.job:
                # il motore riapre lo scanner da solo al comando successivo: si può riprovare subito
                self.finish_job(Msg("progress_scan_error"))
                self.set_status(error, "error")
            elif self.adapter_stuck(msg) and not self.recovery_tried:
                self.recover_adapter()
            else:
                self.scanner_info = None
                self.set_status(error, "error")
                self.set_busy(False)
        elif kind == "virtualization":
            # WSL non riesce ad avviare la sua macchina virtuale: lo si dice chiaro, il resto non serve
            self.virtualization_off = True
            self.set_status(Msg("fatal_virtualization"), "error")
            self.log(Msg("fatal_virtualization"))
        elif kind == "exit":
            if getattr(self, "virtualization_off", False):
                self.scanner_info = None
                self.set_busy(False)
                return
            if not self.closing:
                self.log(Msg("log_engine_closed"))
                if self.job:
                    self.finish_job(Msg("scan_interrupted"))
                self.scanner_info = None
                self.set_status(Msg("status_engine_closed"), "error")
                self.set_busy(False)

    # adattatore bloccato

    # errori all'apertura che un motore interrotto a metà comando può lasciare dietro di sé: l'adattatore
    # Logitec non risponde più finché non viene scollegato e ricollegato (provato il 2026-10-13)
    STUCK_KEYS = ("b_no_scanner", "b_cmd_rejected", "b_status_timeout", "b_usb_error", "b_no_answer")

    def adapter_stuck(self, msg):
        return msg.get("key") in self.STUCK_KEYS or "Errno 16" in str(msg.get("message", ""))

    def recover_adapter(self):
        """Un tentativo automatico: scollega e ricollega l'adattatore (usbipd), poi riapre lo scanner."""
        self.recovery_tried = True
        self.scanner_info = None          # niente scansioni mentre l'adattatore viene ricollegato
        self.set_busy(True)
        self.set_status(Msg("status_adapter_reset"), "wait")
        self.log(Msg("status_adapter_reset"))

        def work():
            bridge.detach_adapter()
            time.sleep(2)
            ok, out = bridge.attach_adapter()
            if not ok and out:
                self.events_local.append(("log", {"message": Msg(raw=out)}))
            if self.backend:
                self.backend.send(cmd="open", wait_s=30)

        threading.Thread(target=work, daemon=True).start()

    def on_opened(self, msg):
        self.recovery_tried = False
        self.scanner_info = msg
        self.glass_mm = (msg["width_mm"], msg["height_mm"])
        self.resolutions = msg["resolutions"]
        # livelli B4-B6: luminosità da -3; B4: niente colore (motore 1.4 in poi)
        self.bright.lo = msg.get("brightness_min", -4)
        if self.bright_var.get() < self.bright.lo:
            self.bright_var.set(self.bright.lo)
        self.bright.draw()
        if not self.color_ok() and self.mode_var.get() == "color":
            self.mode_var.set("gray")
        self.profile_cards.options = [(tr(name), self.profile_detail(key), key) for key, name, _ in PROFILES]
        self.profile_cards.draw()
        self._base_cache = None
        self.set_status(self.ready_text(), "ok")
        self.log(Msg("log_scanner_ready", vendor=msg["vendor"], product=msg["product"], level=msg["level"],
                     w="%.0f" % msg["width_mm"], h="%.0f" % msg["height_mm"]))
        self.set_busy(False)
        self.apply_preset(initial=True)

    def on_button(self):
        """Pulsante blu dello scanner: avvia la scansione con le impostazioni correnti."""
        if self.job or not self.scanner_info:
            return
        self.log(Msg("log_button"))
        self.start_scan()

    def show_dpi_menu(self):
        if self.job:
            return
        menu = tk.Menu(self.root, tearoff=0)
        for d in self.resolutions:
            optical = self.optical_dpi()
            note = "" if not optical else tr("dpi_optical") if d == optical else \
                tr("dpi_interpolated") if d > optical else ""
            menu.add_radiobutton(label="%d dpi  (%s)" % (d, note) if note else "%d dpi" % d, value=str(d),
                                 variable=self.dpi_var, command=self.update_estimate)
        x = self.more_dpi.winfo_rootx()
        y = self.more_dpi.winfo_rooty() + self.more_dpi.winfo_height()
        menu.tk_popup(x, y)

    # area di scansione

    def apply_preset(self, initial=False):
        key = self.preset_var.get()
        value = {p[1]: p[2] for p in PRESETS}.get(key)
        gw, gh = self.glass_mm
        if value == "full":
            self.area_mm = [0, 0, gw, gh]
        elif value:
            self.area_mm = [0, 0, min(value[0], gw), min(value[1], gh)]
        elif not self.area_mm:
            self.area_mm = [0, 0, 210, 297]
        self.clamp_area()
        self.update_estimate()
        self.redraw()

    def clamp_area(self):
        gw, gh = self.glass_mm
        x, y, w, h = self.area_mm
        w = max(5, min(w, gw))
        h = max(5, min(h, gh))
        x = max(0, min(x, gw - w))
        y = max(0, min(y, gh - h))
        self.area_mm = [x, y, w, h]

    def glass_geometry(self):
        """Origine e scala (pixel per mm) del vetro; a sinistra e in alto resta spazio per i righelli."""
        px = self.t.px
        cw = max(self.canvas.winfo_width(), 50)
        ch = max(self.canvas.winfo_height(), 50)
        ml, mt, mr, mb = px(34), px(26), px(12), px(8)
        gw, gh = self.glass_mm
        scale = max(0.1, min((cw - ml - mr) / gw, (ch - mt - mb) / gh))
        ox = ml + (cw - ml - mr - gw * scale) / 2
        oy = mt + (ch - mt - mb - gh * scale) / 2
        return ox, oy, scale

    def mm_to_canvas(self, x, y):
        ox, oy, s = self.glass_geometry()
        return ox + x * s, oy + y * s

    def canvas_to_mm(self, cx, cy):
        ox, oy, s = self.glass_geometry()
        gw, gh = self.glass_mm
        return min(max((cx - ox) / s, 0), gw), min(max((cy - oy) / s, 0), gh)

    def _glass_images(self, s):
        """Vetro con anteprima, in versione normale e scurita; ricalcolato solo se serve."""
        gw, gh = self.glass_mm
        size = (max(1, int(round(gw * s))), max(1, int(round(gh * s))))
        key = (size, id(self.preview_image))
        if self._base_cache and self._base_cache[0] == key:
            return self._base_cache[1], self._base_cache[2]
        base = Image.new("RGB", size, T.GLASS)
        img = self.preview_image
        if img is not None:
            disp = (max(1, int(round(img.width * 25.4 / PREVIEW_DPI * s))),
                    max(1, int(round(img.height * 25.4 / PREVIEW_DPI * s))))
            base.paste(img.resize(disp, Image.LANCZOS), (0, 0))
        else:
            d = ImageDraw.Draw(base)
            for mm in range(50, int(gw), 50):
                d.line([(mm * s, 0), (mm * s, size[1])], fill=T.GRID)
            for mm in range(50, int(gh), 50):
                d.line([(0, mm * s), (size[0], mm * s)], fill=T.GRID)
        dim = base.point(lambda v: int(v * 0.42))
        self._base_cache = (key, base, dim)
        return base, dim

    def redraw(self):
        c = self.canvas
        t, px = self.t, self.t.px
        ox, oy, s = self.glass_geometry()
        gw, gh = self.glass_mm
        base, dim = self._glass_images(s)
        c.delete("all")
        # righelli in millimetri
        for mm in range(0, int(gw) + 1, 10):
            x = ox + mm * s
            major = mm % 50 == 0
            c.create_line(x, oy - px(8 if major else 4), x, oy - 1, fill=T.TEXT_3 if major else T.BORDER)
            if major:
                c.create_text(x, oy - px(10), text=str(mm), anchor="s", fill=T.TEXT_3, font=t.font_small)
        for mm in range(0, int(gh) + 1, 10):
            y = oy + mm * s
            major = mm % 50 == 0
            c.create_line(ox - px(8 if major else 4), y, ox - 1, y, fill=T.TEXT_3 if major else T.BORDER)
            if major:
                c.create_text(ox - px(11), y, text=str(mm), anchor="e", fill=T.TEXT_3, font=t.font_small)
        c.create_text(ox - px(11), oy - px(10), text="mm", anchor="se", fill=T.TEXT_3, font=t.font_small)

        x, y, w, h = self.area_mm or [0, 0, gw, gh]
        box = (int(round(x * s)), int(round(y * s)), int(round((x + w) * s)), int(round((y + h) * s)))
        view = dim.copy()
        view.paste(base.crop(box), box[:2])
        self._view_tk = ImageTk.PhotoImage(view)
        c.create_image(ox, oy, image=self._view_tk, anchor="nw")
        if self.preview_image is None and not (self.job and self.job["preview"]):
            cx, cy = self.mm_to_canvas(x + w / 2, y + h / 2)
            # in alcune lingue la frase è lunga: va a capo dentro la selezione
            wrap = max(px(240), w * s - px(24))
            c.create_text(cx, cy - px(12), text=tr("glass_empty_title"), fill=T.TEXT_2, font=t.font_section,
                          width=wrap, justify="center")
            c.create_text(cx, cy + px(4), fill=T.TEXT_3, font=t.font, justify="center", anchor="n",
                          text=tr("glass_empty_hint"), width=wrap)

        ax, ay = self.mm_to_canvas(x, y)
        bx, by = self.mm_to_canvas(x + w, y + h)
        c.create_rectangle(ax, ay, bx, by, outline=T.ACCENT_BRIGHT, width=max(2, px(1.5)))
        job = self.job
        if job and not job["preview"] and job.get("total"):
            # posizione della testina durante la scansione
            frac = min(1.0, job["done"] / job["total"])
            hy = ay + (by - ay) * frac
            c.create_line(ax, hy, bx, hy, fill=T.ACCENT_BRIGHT, width=max(2, px(2)))
        else:
            r = px(4)
            for hx, hy in ((ax, ay), (bx, ay), (ax, by), (bx, by)):
                c.create_rectangle(hx - r, hy - r, hx + r, hy + r, fill="#ffffff", outline=T.ACCENT_BRIGHT)
        self.area_label.configure(text=tr("area_label", w="%.0f" % w, h="%.0f" % h, x="%.0f" % x, y="%.0f" % y))

    def on_press(self, e):
        if not self.area_mm or self.job:
            self.drag = None
            return
        mx, my = self.canvas_to_mm(e.x, e.y)
        x, y, w, h = self.area_mm
        ax, ay = self.mm_to_canvas(x, y)
        bx, by = self.mm_to_canvas(x + w, y + h)
        grip = 9 * self.f
        corners = {"nw": (ax, ay), "ne": (bx, ay), "sw": (ax, by), "se": (bx, by)}
        for name, (hx, hy) in corners.items():
            if abs(e.x - hx) <= grip and abs(e.y - hy) <= grip:
                self.drag = ("corner", name, list(self.area_mm))
                return
        if ax <= e.x <= bx and ay <= e.y <= by:
            self.drag = ("move", (mx, my), list(self.area_mm))
        else:
            self.drag = ("new", (mx, my), None)

    def on_drag(self, e):
        if not self.drag:
            return
        mx, my = self.canvas_to_mm(e.x, e.y)
        kind, ref, orig = self.drag
        if kind == "new":
            sx, sy = ref
            self.area_mm = [min(sx, mx), min(sy, my), max(abs(mx - sx), 5), max(abs(my - sy), 5)]
        elif kind == "move":
            sx, sy = ref
            self.area_mm = [orig[0] + mx - sx, orig[1] + my - sy, orig[2], orig[3]]
        else:
            x0, y0, x1, y1 = orig[0], orig[1], orig[0] + orig[2], orig[1] + orig[3]
            if "w" in ref:
                x0 = mx
            if "e" in ref:
                x1 = mx
            if "n" in ref:
                y0 = my
            if "s" in ref:
                y1 = my
            self.area_mm = [min(x0, x1), min(y0, y1), max(abs(x1 - x0), 5), max(abs(y1 - y0), 5)]
        self.clamp_area()
        self.preset_var.set("custom")
        self.redraw()

    def on_release(self, e):
        self.drag = None
        self.update_estimate()

    # stime e impostazioni

    def current_dpi(self):
        try:
            return int(self.dpi_var.get())
        except ValueError:
            return 300

    def estimate(self):
        dpi = self.current_dpi()
        x, y, w, h = self.area_mm or [0, 0] + list(self.glass_mm)
        width = int(round(w * dpi / 25.4)) & ~7
        height = int(round(h * dpi / 25.4))
        size = bytes_per_line(self.mode_var.get(), width) * height
        speed = self.settings.data.get("speed_bps") or DEFAULT_SPEED_BPS
        return width, height, size, size / speed + 8

    def update_estimate(self):
        if not self.area_mm:
            return
        width, height, size, seconds = self.estimate()
        self.summary.configure(text=tr("summary", w=width, h=height, size=human_size(size), time=human_time(seconds)))
        dpi = self.current_dpi()
        other = dpi not in DPI_CHOICES
        self.more_dpi.configure(text=tr("dpi_more_value", dpi=dpi) if other else tr("dpi_more"))
        optical = self.optical_dpi()
        if not optical:
            self.dpi_note.configure(text="", fg=T.TEXT_3)
        elif dpi > optical:
            self.dpi_note.configure(text=tr("dpi_note_over", dpi=optical), fg=T.WAIT)
        else:
            self.dpi_note.configure(text=tr("dpi_note_optical", dpi=optical), fg=T.TEXT_3)
        self.update_tone()
        self.update_quality()
        self.update_sequence_note()
        self.update_streak_note()
        self.profile_cards.draw()

    def update_quality(self):
        fmt, lineart = self.format_var.get(), self.mode_var.get() == "lineart"
        choose = fmt == "jpg" or (fmt == "pdf" and not lineart)
        for w in (self.quality_row, self.quality_seg, self.quality_note):
            w.pack_forget()
        if choose:
            self.quality_row.pack(fill="x", pady=(0, self.t.px(3)))
            self.quality_seg.pack(fill="x", pady=(0, self.t.px(8)))
        else:
            self.quality_note.configure(text=tr("quality_g4_note" if fmt == "pdf" else "quality_lossless_note"))
            self.quality_note.pack(fill="x", pady=(0, self.t.px(8)))

    # scelta rapida

    def optical_dpi(self):
        """Risoluzione ottica: dallo scanner (FS I), dai modelli noti, oppure None se non si sa."""
        info = self.scanner_info
        if not info:
            return OPTICAL_DPI
        if info.get("optical_dpi"):
            return info["optical_dpi"]
        model = str(info.get("model") or info.get("product") or "")
        return next((v for k, v in KNOWN_OPTICAL.items() if model.upper().startswith(k)), None)

    def color_ok(self):
        return not self.scanner_info or self.scanner_info.get("color", True)

    def profile_settings(self, key):
        """Impostazioni del profilo adattate allo scanner collegato (risoluzione ottica, colore)."""
        cfg = dict(next(c for k, _, c in PROFILES if k == key))
        if key == "art":
            cfg["dpi"] = self.optical_dpi() or cfg["dpi"]
        if self.resolutions and cfg["dpi"] not in self.resolutions:
            cfg["dpi"] = min(self.resolutions, key=lambda d: abs(d - cfg["dpi"]))
        if not self.color_ok():
            cfg["mode"] = "gray"
        return cfg

    def profile_detail(self, key):
        cfg = self.profile_settings(key)
        return "%s · %d dpi" % (dict((v, k) for k, v in FORMATS)[cfg["format"]], cfg["dpi"])

    def active_profile(self):
        if not hasattr(self, "quality_var"):
            return None
        for key, _, _ in PROFILES:
            cfg = self.profile_settings(key)
            if (self.mode_var.get() == cfg["mode"] and self.current_dpi() == cfg["dpi"]
                    and self.format_var.get() == cfg["format"]
                    and (cfg["format"] not in ("jpg", "pdf") or self.quality_var.get() == cfg["quality"])):
                return key
        return None

    def apply_profile(self, key):
        if self.job:
            return
        name = next(n for k, n, _ in PROFILES if k == key)
        cfg = self.profile_settings(key)
        self.mode_var.set(cfg["mode"])
        self.dpi_var.set(str(cfg["dpi"]))
        self.format_var.set(cfg["format"])
        self.quality_var.set(cfg["quality"])
        self.update_estimate()
        self.collect_settings()
        self.log(Msg("log_profile", name=Msg(name)))

    def update_tone(self):
        lineart = self.mode_var.get() == "lineart"
        self.tone_label.configure(text=tr("lbl_threshold") if lineart else tr("lbl_gamma"))
        show, hide = (self.thr, self.gamma) if lineart else (self.gamma, self.thr)
        if not show.winfo_ismapped():
            hide.pack_forget()
            show.pack(fill="x")

    def collect_settings(self):
        d = self.settings.data
        d["mode"] = self.mode_var.get()
        d["dpi"] = self.current_dpi()
        d["format"] = self.format_var.get()
        d["prefix"] = self.prefix_var.get().strip() or tr("default_prefix")
        d["folder"] = self.folder_var.get()
        d["brightness"] = self.bright_var.get()
        d["sharpness"] = self.sharp_var.get()
        d["gamma_step"] = self.gamma_var.get()
        d["threshold_step"] = self.thr_var.get()
        d["pages"] = self.pages_var.get()
        d["streaks"] = self.streak_var.get()
        d["quality"] = self.quality_var.get()
        d["area_mm"] = self.area_mm
        d["preset"] = self.preset_var.get()
        self.settings.save()
        return d

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get(), title=tr("dlg_choose_folder"))
        if folder:
            self.folder_var.set(os.path.normpath(folder))
            self.collect_settings()

    def open_folder(self):
        folder = self.folder_var.get()
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def open_last(self):
        if self.last_file and os.path.exists(self.last_file):
            os.startfile(self.last_file)

    # scansione

    def start_preview(self):
        self._start_job(preview=True)

    def start_scan(self):
        if self.job or not self.scanner_info:
            return
        width, height, size, seconds = self.estimate()
        os.makedirs(SPOOL_DIR, exist_ok=True)
        free = shutil.disk_usage(SPOOL_DIR).free
        if free < size * 1.2:
            messagebox.showerror(APP_NAME, tr("dlg_no_space", need=human_size(size * 1.2), free=human_size(free)))
            return
        if size > LARGE_SCAN_BYTES or seconds > LONG_SCAN_SECONDS:
            if not messagebox.askyesno(APP_NAME, tr("dlg_large_scan", size=human_size(size), time=human_time(seconds))):
                return
        self._start_job(preview=False)

    def _start_job(self, preview, calib=None):
        if not self.backend or not self.scanner_info or self.job:
            return
        s = self.collect_settings()
        self.job_counter += 1
        job = {"id": self.job_counter, "preview": preview, "buf": bytearray(), "done": 0,
               "t0": time.monotonic(), "last_draw": 0.0, "settings": dict(s), "spool": None, "calib": calib}
        if calib:
            # lettura del coperchio con curva lineare (tutto il vetro a 600 x 50 dpi, circa 18 MB a colori,
            # oppure un quadratino attorno a una riga per misurare lo scarto di una risoluzione)
            cmd = dict(mode=calib["mode"], dpi=calib["dpi"], dpi_y=calib["dpi_y"], area_mm=calib["area_mm"],
                       preview=calib["preview"], gamma=1.0)
            self.set_status(Msg("status_calibrating", n=self.calib["done"] + 1, total=self.calib["total"]), "wait")
        elif preview:
            cmd = dict(mode="color" if self.color_ok() else "gray", dpi=PREVIEW_DPI, area_mm=None, preview=True,
                       brightness=s["brightness"],
                       sharpness=s["sharpness"], gamma=gamma_of(s["gamma_step"]))
            self.set_status(Msg("status_previewing"), "wait")
        else:
            os.makedirs(SPOOL_DIR, exist_ok=True)
            job["spool_path"] = os.path.join(SPOOL_DIR, "scan_%d_%d.raw" % (os.getpid(), job["id"]))
            job["spool"] = open(job["spool_path"], "wb")
            cmd = dict(mode=s["mode"], dpi=s["dpi"], area_mm=self.area_mm, preview=False,
                       brightness=s["brightness"], sharpness=s["sharpness"], gamma=gamma_of(s["gamma_step"]),
                       threshold=threshold_of(s["threshold_step"]))
            self.set_status(Msg("status_scanning"), "wait")
        self.job = job
        self.set_progress(0)
        self.set_progress_text(Msg("progress_preparing"))
        self.set_busy(True, scanning=True)
        self.backend.send(cmd="scan", id=job["id"], **cmd)

    def cancel_scan(self):
        if self.job and self.backend:
            self.backend.send(cmd="cancel")
            self.set_progress_text(Msg("progress_cancelling"))

    def on_begin(self, msg):
        if not self.job:
            return
        self.job.update(width=msg["width"], height=msg["height"], bpl=msg["bytes_per_line"],
                        mode=msg["mode"], dpi=msg["dpi"], total=msg["bytes_per_line"] * msg["height"],
                        # posizione sul vetro, dal motore 1.3: serve alla correzione righe
                        dpi_y=msg.get("dpi_y", msg["dpi"]), left=msg.get("left"), top=msg.get("top"))
        if self.job["preview"]:
            self.preview_image = None

    def on_data(self, msg):
        job = self.job
        if not job or "total" not in job:
            return
        payload = msg["payload"]
        if job["spool"]:
            job["spool"].write(payload)
        else:
            job["buf"] += payload
        job["done"] += len(payload)
        done = job["done"]
        frac = min(done / max(job["total"], 1), 1.0)
        self.set_progress(frac)
        elapsed = time.monotonic() - job["t0"]
        speed = done / elapsed if elapsed > 0 else 0
        remaining = (job["total"] - done) / speed if speed > 0 else 0
        self.set_progress_text(Msg("progress_running", pct=int(frac * 100), speed=i18n.Size(speed),
                                   time=i18n.Duration(remaining)))
        now = time.monotonic()
        if now - job["last_draw"] > (0.4 if job["preview"] else 1.0):
            job["last_draw"] = now
            if job["preview"]:
                lines = done // job["bpl"]
                if lines:
                    self.preview_image = image_from(job["mode"], job["width"], lines,
                                                    bytes(job["buf"][:lines * job["bpl"]])).convert("RGB")
            self.redraw()

    def on_end(self, msg):
        job = self.job
        if not job:
            return
        seconds = msg.get("seconds", 0)
        if job.get("calib"):
            self.on_calib_pass(job)
            return
        if job["preview"]:
            lines = len(job["buf"]) // job["bpl"]
            if lines and self.streaks_active(job):
                try:
                    destripe.correct_buffer(job["buf"], self.calibration, job["mode"], job["width"], lines,
                                            **self.geometry(job))
                except Exception as e:
                    self.log(Msg("log_streaks_error", error=e))
            self.preview_image = image_from(job["mode"], job["width"], lines,
                                            bytes(job["buf"][:lines * job["bpl"]])).convert("RGB")
            self.finish_job(Msg("preview_done", time=i18n.Duration(seconds)))
            self.redraw()
            return
        job["spool"].close()
        job["spool"] = None
        # solo scansioni grandi: in quelle piccole prevalgono riscaldamento e preparazione (circa 8 s)
        if job["done"] > 20 * 1024 * 1024 and seconds > 20:
            measured = job["done"] / (seconds - 8)
            old = self.settings.data.get("speed_bps") or DEFAULT_SPEED_BPS
            self.settings.data["speed_bps"] = int((old + measured) / 2)
        self.set_progress_text(Msg("progress_saving"))
        job["target"], job["append"] = self.target_path(job["settings"])
        threading.Thread(target=self._save_worker, args=(job, seconds), daemon=True).start()

    def _save_worker(self, job, seconds):
        s = job["settings"]
        path = None
        try:
            lines = job["done"] // job["bpl"]
            if lines and self.streaks_active(job):
                try:
                    n = destripe.correct_file(job["spool_path"], self.calibration, job["mode"], job["width"], lines,
                                              **self.geometry(job))
                    self.events_local.append(("log", {"message": Msg("log_streaks_applied", n=n)}))
                except Exception as e:
                    self.events_local.append(("log", {"message": Msg("log_streaks_error", error=e)}))
            os.makedirs(s["folder"], exist_ok=True)
            path = job["target"]
            dpi = (job["dpi"], job["dpi"])
            with open(job["spool_path"], "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                view = memoryview(mm)
                try:
                    img = image_from(job["mode"], job["width"], lines, view[:lines * job["bpl"]])
                finally:
                    view.release()
            size = img.size
            pixels = size[0] * size[1]
            fmt = s["format"]
            opts = encoder_options(fmt, img.mode, s.get("quality"))
            if fmt == "jpg":
                out = img.convert("L") if img.mode == "1" else img
                out.save(path, "JPEG", dpi=dpi, optimize=pixels < 40_000_000, **opts)
            elif fmt == "png":
                img.save(path, "PNG", dpi=dpi, compress_level=6 if pixels < 60_000_000 else 3)
            elif fmt == "tif":
                img.save(path, "TIFF", dpi=dpi, compression="group4" if img.mode == "1" else "tiff_lzw")
            else:
                # in sequenza le pagine successive si aggiungono allo stesso PDF; il bianco e nero resta a 1 bit
                img.save(path, "PDF", resolution=float(job["dpi"]), append=job["append"], **opts)
            thumb = img.convert("RGB") if img.mode != "RGB" else img.copy()
            thumb.thumbnail((self.t.px(36), self.t.px(36)), Image.LANCZOS)
            del img
            self.events_local.append(("saved", {"path": path, "seconds": seconds, "size": size, "thumb": thumb,
                                                "bytes": os.path.getsize(path), "append": job["append"]}))
        except Exception as e:
            self.events_local.append(("save_error", {"message": str(e)}))
        finally:
            try:
                os.remove(job["spool_path"])
            except OSError:
                pass

    # correzione righe

    @staticmethod
    def load_calibration():
        if destripe is None or not os.path.exists(CALIBRATION_FILE):
            return None
        try:
            return destripe.Calibration.load(CALIBRATION_FILE)
        except Exception:
            return None

    def streaks_active(self, job):
        return (destripe is not None and self.calibration is not None and job.get("left") is not None
                and job["settings"].get("streaks") == "on" and job["mode"] in ("color", "gray"))

    @staticmethod
    def geometry(job):
        return dict(dpi=job["dpi"], dpi_y=job["dpi_y"], left=job["left"], top=job["top"],
                    gamma=gamma_of(job["settings"]["gamma_step"]), preview=job["preview"])

    def update_adjust_summary(self):
        if not hasattr(self, "adjust_box"):
            return
        changed = any(v.get() != 0 for v in (self.bright_var, self.sharp_var, self.gamma_var, self.thr_var))
        self.adjust_box.set_summary(tr("adjust_modified") if changed else "", T.WAIT)

    def update_streak_summary(self):
        if not hasattr(self, "streak_box"):
            return
        on = self.streak_var.get() == "on"
        self.streak_box.set_summary(tr("streaks_on" if on else "streaks_off"), T.OK if on else T.TEXT_3)

    def update_streak_note(self):
        if not hasattr(self, "streak_note"):
            return
        fg = T.TEXT_3
        if destripe is None:
            text, fg = tr("streaks_no_numpy"), T.WAIT
        elif self.mode_var.get() == "lineart":
            text = tr("streaks_lineart")
        elif not self.calibration:
            text = tr("streaks_need_cal")
        else:
            text = tr("streaks_info", date=self.calibration.date, n=self.calibration.visible_streaks("color"))
        self.streak_note.configure(text=text, fg=fg)

    def show_streak_help(self):
        StreakHelp(self)

    def on_streaks_changed(self):
        if self.streak_var.get() == "on" and not self.calibration:
            self.streak_var.set("off")
            if destripe is None:
                messagebox.showinfo(APP_NAME, tr("streaks_no_numpy"))
            elif messagebox.askyesno(APP_NAME, tr("dlg_streaks_need_cal")):
                self.start_calibration(ask=False)
        self.collect_settings()
        self.update_streak_note()

    def start_calibration(self, ask=True):
        if self.job or not self.scanner_info:
            return
        if destripe is None:
            messagebox.showinfo(APP_NAME, tr("streaks_no_numpy"))
            return
        if ask and not messagebox.askokcancel(APP_NAME, tr("dlg_calibrate")):
            return
        modes = ("color", "gray") if self.color_ok() else ("gray",)
        first = [{"name": m, "mode": m, "dpi": destripe.CAL_DPI, "dpi_y": destripe.CAL_DPI_Y, "area_mm": None,
                  "preview": False} for m in modes]
        self.calib = {"todo": first, "scans": {}, "done": 0, "total": len(first), "cal": None}
        self._start_job(preview=False, calib=first[0])

    def on_calib_pass(self, job):
        c, p = self.calib, job["calib"]
        lines = len(job["buf"]) // job["bpl"]
        c["scans"][p["name"]] = {"data": bytes(job["buf"][:lines * job["bpl"]]), "width": job["width"],
                                 "height": lines, "dpi": job["dpi"], "left": job.get("left") or 0,
                                 "top": job.get("top") or 0, "preview": p["preview"]}
        c["todo"].pop(0)
        c["done"] += 1
        if c["todo"]:
            self.job = None
            self._start_job(preview=False, calib=c["todo"][0])
            return
        # le analisi durano qualche secondo: il lavoro resta aperto finché non finiscono
        threading.Thread(target=self._calib_worker, daemon=True).start()

    def _calib_worker(self):
        c = self.calib
        try:
            if c["cal"] is None:
                # prima fase: sensibilità delle colonne dal coperchio
                scans = {k: (v["data"], v["width"], v["height"]) for k, v in c["scans"].items()
                         if k in ("color", "gray")}
                cal, _ = destripe.Calibration.from_scans(scans)
                cal.offsets, cal.offset_preview = {}, None
                target = cal.streak_target()
                if target:
                    self.events_local.append(("calib_offsets", {"calibration": cal, "target": target}))
                    return
            else:
                # seconda fase: scarto d'origine a ogni risoluzione, dalla riga più evidente
                cal = c["cal"]
                for name, v in c["scans"].items():
                    if not name.startswith("off_"):
                        continue
                    shift = cal.measure_offset(v["data"], v["width"], v["height"], v["dpi"], v["left"], v["top"],
                                               v["preview"])
                    if shift is None:
                        continue
                    if v["preview"]:
                        cal.offset_preview = shift
                    else:
                        cal.offsets[v["dpi"]] = shift
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            cal.save(CALIBRATION_FILE)
            self.events_local.append(("calibrated", {"calibration": cal}))
        except destripe.CalibrationError as e:
            self.events_local.append(("calib_error", {"message": Msg(e.key, **e.args_)}))
        except Exception as e:
            self.events_local.append(("calib_error", {"message": Msg(raw=str(e))}))

    def on_calib_offsets(self, cal, target):
        """Dopo le letture del coperchio: un quadratino attorno alla riga più evidente a ogni risoluzione."""
        c = self.calib
        if c is None:
            return
        c["cal"] = cal
        size = destripe.OFFSET_AREA_MM
        gw, gh = self.glass_mm
        x, y = target
        area = [max(0.0, min(gw - size, x - size / 2)), max(0.0, min(gh - size, y - size / 2)), size, size]
        passes = [{"name": "off_%d" % d, "mode": "color", "dpi": d, "dpi_y": None, "area_mm": area, "preview": False}
                  for d in destripe.OFFSET_DPIS if d in self.resolutions]
        if PREVIEW_DPI in self.resolutions:
            passes.append({"name": "off_preview", "mode": "color", "dpi": PREVIEW_DPI, "dpi_y": None,
                           "area_mm": area, "preview": True})
        c["todo"], c["total"] = passes, c["total"] + len(passes)
        self.log(Msg("log_calib_offsets", n=len(passes)))
        self.job = None
        self._start_job(preview=False, calib=passes[0])

    def on_calibrated(self, cal):
        self.calibration = cal
        self.streak_var.set("on")
        self.collect_settings()
        self.log(Msg("log_calib_done", n=cal.visible_streaks("color"), g=cal.visible_streaks("gray")))
        if cal.offsets:
            shifts = ["%d dpi %+.2f" % (d, v) for d, v in sorted(cal.offsets.items())]
            if cal.offset_preview is not None:
                shifts.append("%s %+.2f" % (tr("btn_preview"), cal.offset_preview))
            self.log(Msg("log_calib_offsets_done", list=", ".join(shifts)))
        self.finish_job(Msg("calib_done"))
        self.update_streak_note()

    # più pagine

    def target_path(self, s):
        """Percorso del file e se aggiungerlo a un PDF esistente, secondo la modalità Singola o Sequenza."""
        folder, prefix, fmt = s["folder"], s["prefix"], s["format"]
        if s.get("pages") != "sequence":
            stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            return os.path.join(folder, "%s_%s.%s" % (prefix, stamp, fmt)), False
        key = (folder, prefix, fmt)
        seq = self.sequence
        if seq and seq["key"] != key:
            self.end_sequence()
            seq = None
        if fmt == "pdf":
            if seq and os.path.exists(seq["pdf"]):
                return seq["pdf"], True
            stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            return os.path.join(folder, "%s_%s.pdf" % (prefix, stamp)), False
        return os.path.join(folder, "%s_%03d.%s" % (prefix, self.next_number(s), fmt)), False

    @staticmethod
    def next_number(s):
        """Primo numero libero dopo l'ultimo file prefisso_NNN.ext già presente nella cartella."""
        rx = re.compile(r"^%s_(\d{3,})\.%s$" % (re.escape(s["prefix"]), re.escape(s["format"])), re.I)
        try:
            names = os.listdir(s["folder"])
        except OSError:
            names = []
        used = [int(m.group(1)) for m in map(rx.match, names) if m]
        return max(used, default=0) + 1

    def on_pages_changed(self):
        if self.pages_var.get() != "sequence":
            self.end_sequence()
        self.update_sequence_note()

    def end_sequence(self):
        if self.sequence and self.sequence["pages"]:
            self.log(Msg("log_seq_end", n=self.sequence["pages"]))
        self.sequence = None
        self.update_sequence_note()

    def update_sequence_note(self):
        if not hasattr(self, "seq_note"):
            return
        seq = self.sequence
        if self.pages_var.get() != "sequence":
            self.seq_note.configure(text="")
            self.seq_end_link.pack_forget()
            self.seq_row.pack_forget()
            self.pages_seg.pack_configure(pady=(0, self.t.px(8)))
            return
        if not self.seq_row.winfo_ismapped():
            self.pages_seg.pack_configure(pady=0)
            self.seq_row.pack(fill="x", pady=self._seq_row_pady, after=self.pages_seg)
        s = {"folder": self.folder_var.get(), "prefix": self.prefix_var.get().strip() or tr("default_prefix"),
             "format": self.format_var.get()}
        if seq and seq["pages"]:
            name = os.path.basename(seq["pdf"] if seq["pdf"] else seq["last"])
            text = tr("seq_status_pdf" if seq["pdf"] else "seq_status_files", n=seq["pages"], name=name)
            if not self.seq_end_link.winfo_ismapped():
                self.seq_end_link.pack(side="right", anchor="n")
        else:
            self.seq_end_link.pack_forget()
            if s["format"] == "pdf":
                text = tr("seq_note_pdf")
            else:
                text = tr("seq_note_files", name="%s_%03d.%s" % (s["prefix"], self.next_number(s), s["format"]))
        self.seq_note.configure(text=text + "\n" + tr("seq_button_hint"))

    def on_saved(self, msg):
        self.last_file = msg["path"]
        self.last_info = msg
        s = self.settings.data
        if s.get("pages") == "sequence":
            seq = self.sequence or {"key": (s["folder"], s["prefix"], s["format"]), "pages": 0,
                                    "pdf": msg["path"] if s["format"] == "pdf" else None, "last": None}
            seq["pages"] += 1
            seq["last"] = msg["path"]
            self.sequence = seq
            if msg.get("append"):
                self.log(Msg("log_pdf_page", n=seq["pages"], path=msg["path"]))
            self.update_sequence_note()
        self.set_progress(1.0, active=False)
        self._show_last()
        self.log(Msg("log_saved", path=msg["path"], w=msg["size"][0], h=msg["size"][1],
                     time=i18n.Duration(msg["seconds"])))
        self.finish_job(Msg("scan_done", time=i18n.Duration(msg["seconds"])))
        self.collect_settings()

    def _show_last(self):
        msg = self.last_info
        if not msg:
            return
        self._last_thumb = ImageTk.PhotoImage(msg["thumb"])
        self.last_thumb.configure(image=self._last_thumb)
        self.last_name.configure(text=tr("last_name", name=ellipsize_middle(os.path.basename(msg["path"]), 34)))
        self.last_detail.configure(text=tr("last_detail", w=msg["size"][0], h=msg["size"][1],
                                           size=human_size(msg["bytes"])))
        if not self.last_frame.winfo_ismapped():
            self.last_frame.pack(side="right", padx=(0, self.t.px(10)))

    def finish_job(self, text):
        job = self.job
        if job and job.get("spool"):
            job["spool"].close()
            try:
                os.remove(job["spool_path"])
            except OSError:
                pass
        if job and job.get("calib"):
            self.calib = None
        self.job = None
        self.set_progress_text(text)
        if self.scanner_info:
            self.set_status(self.ready_text(), "ok")
        self.set_busy(False)
        self.redraw()

    # lingua

    def show_language_menu(self):
        if self.job:
            return
        menu = tk.Menu(self.root, tearoff=0)
        current = tk.StringVar(value=i18n.language())
        self._lang_var = current  # il menu tiene solo un riferimento debole alla variabile
        for code, name in i18n.LANGUAGES:
            menu.add_radiobutton(label=name, value=code, variable=current,
                                 command=lambda c=code: self.set_language(c))
        menu.tk_popup(self.lang_btn.winfo_rootx(), self.lang_btn.winfo_rooty() + self.lang_btn.winfo_height())

    def set_language(self, code):
        if self.job or code == i18n.language():
            return
        self.collect_settings()
        old_defaults = set(i18n.STRINGS["default_prefix"])
        i18n.set_language(code)
        d = self.settings.data
        d["language"] = code
        if d.get("prefix") in old_defaults:
            # il nome predefinito dei file segue la lingua; uno scelto a mano resta com'è
            d["prefix"] = tr("default_prefix")
        self.settings.save()
        self.log(Msg("log_language", name=i18n.language_name(code)))
        self.rebuild()

    def rebuild(self):
        """Ricostruisce tutta l'interfaccia nella lingua corrente, conservando lo stato."""
        status, progress = self._status, self._progress
        log_visible = self.log_win.state() != "withdrawn"
        for child in self.root.winfo_children():
            child.destroy()
        self.t = T(self.root, self.f, i18n.language())
        self._base_cache = None
        self._build()
        for stamp, msg in self.log_entries:
            self._log_append(stamp, msg)
        self.set_status(*status)
        self.set_progress_text(progress[0])
        self.set_progress(progress[1], progress[2])
        self._show_last()
        self.set_busy(False)
        if log_visible:
            self.toggle_log()
        self.redraw()

    def on_close(self):
        if self.job and not messagebox.askyesno(APP_NAME, tr("dlg_close_scanning")):
            return
        self.closing = True
        try:
            self.collect_settings()
        except Exception:
            pass
        if self.backend:
            if self.job:
                self.backend.send(cmd="cancel")
            self.backend.stop()
        if self.job and self.job.get("spool"):
            self.job["spool"].close()
            try:
                os.remove(self.job["spool_path"])
            except OSError:
                pass
        self.root.destroy()



def already_running():
    """Un'istanza sola: se il programma è già aperto lo si porta in primo piano e si esce."""
    global _instance_mutex
    try:
        _instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\ScannerLinkPro")
        if ctypes.windll.kernel32.GetLastError() != 183:          # ERROR_ALREADY_EXISTS
            return False
        hwnd = ctypes.windll.user32.FindWindowW(None, APP_NAME)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)                # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        return True
    except (AttributeError, OSError):
        return False


def main():
    if already_running():
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScannerLinkPro")
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
