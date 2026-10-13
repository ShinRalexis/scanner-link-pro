# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tema scuro neutro e controlli disegnati su Canvas per l'interfaccia dello scanner.

I controlli ttk su Windows non si lasciano colorare in modo coerente in scuro: questi
pochi componenti (pulsante, selettore a segmenti, cursore, barra di avanzamento) coprono
tutto quello che serve, con stati hover, pressione, disattivato e focus da tastiera.
"""

import tkinter as tk
import tkinter.font as tkfont


class Theme:
    # neutri senza dominante: attorno a un'illustrazione un grigio colorato falserebbe il giudizio sui colori
    BG = "#1c1c1d"          # attorno al vetro
    GLASS = "#29292b"       # vetro vuoto
    GRID = "#323235"
    PANEL = "#242426"       # barra superiore e pannello laterale
    FIELD = "#2e2e31"       # fondo dei controlli
    FIELD_HOVER = "#363639"
    SELECTED = "#46464b"
    BORDER = "#3a3a3e"
    TEXT = "#ededee"
    TEXT_2 = "#b0b0b5"
    TEXT_3 = "#96969c"
    DISABLED = "#6c6c72"
    ACCENT = "#2b73d6"       # azione principale, selezione, avanzamento
    ACCENT_HOVER = "#3a82e4"
    ACCENT_PRESS = "#2563bb"
    ACCENT_BRIGHT = "#5ea2ff"  # contorno della selezione sopra le immagini
    OK = "#3fb950"
    WAIT = "#d9a441"
    ERROR = "#f0524f"

    # Segoe UI non copre giapponese, coreano e cinese: per queste lingue i caratteri di sistema adatti
    CJK_FONTS = {"ja": "Yu Gothic UI", "ko": "Malgun Gothic", "zh": "Microsoft YaHei UI"}

    def __init__(self, root, f, lang="it"):
        self.f = f
        families = set(tkfont.families(root))
        base = "Segoe UI Variable Text" if "Segoe UI Variable Text" in families else "Segoe UI"
        display = "Segoe UI Variable Display" if "Segoe UI Variable Display" in families else "Segoe UI"
        semibold = base + " Semibold" if base + " Semibold" in families else base
        strong = (semibold, 10)
        cjk = self.CJK_FONTS.get(lang)
        if cjk and cjk in families:
            base = display = cjk
            semibold = cjk + " Semibold" if cjk + " Semibold" in families else cjk
            strong = (semibold, 10) if semibold != cjk else (cjk, 10, "bold")
        bold = strong[2:] or ()
        self.font = (base, 10)
        self.font_small = (base, 9)
        self.font_label = (base, 9)
        self.font_strong = strong
        self.font_button = strong
        self.font_section = (strong[0], 11) + tuple(bold)
        self.font_title = (display, 13, "bold")
        self.font_mono = ("Cascadia Mono" if "Cascadia Mono" in families else "Consolas", 8)

    def px(self, v):
        return int(round(v * self.f))


def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, splinesteps=12, **kw)


class _CanvasWidget(tk.Canvas):
    def __init__(self, parent, theme, height, takefocus=True):
        super().__init__(parent, height=theme.px(height), bg=parent["bg"], highlightthickness=0,
                         takefocus=1 if takefocus else 0, bd=0)
        self.t = theme
        self.hover = False
        self.pressed = False
        self.enabled = True
        self.focused = False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self._set("hover", True))
        self.bind("<Leave>", lambda e: self._set("hover", False))
        self.bind("<FocusIn>", lambda e: self._set("focused", True))
        self.bind("<FocusOut>", lambda e: self._set("focused", False))

    def _set(self, name, value):
        setattr(self, name, value)
        self.draw()

    def set_enabled(self, enabled):
        if enabled != self.enabled:
            self.enabled = enabled
            self.configure(cursor="hand2" if enabled else "arrow", takefocus=1 if enabled else 0)
            self.draw()

    def size(self):
        return max(self.winfo_width(), 2), max(self.winfo_height(), 2)

    def focus_ring(self, x1, y1, x2, y2, r):
        if self.focused and self.enabled:
            rounded_rect(self, x1 + 1, y1 + 1, x2 - 1, y2 - 1, r, fill="", outline=self.t.ACCENT_BRIGHT,
                         width=max(1, self.t.px(1.5)))

    def draw(self):
        raise NotImplementedError


class Button(_CanvasWidget):
    """kind: primary (azione principale), secondary, ghost (solo testo), danger."""

    def __init__(self, parent, theme, text, command, kind="secondary", height=34, chevron=False):
        super().__init__(parent, theme, height)
        self.text = text
        self.command = command
        self.kind = kind
        self.chevron = chevron   # freccia verso il basso: il pulsante apre un menu
        self.configure(cursor="hand2")
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Return>", lambda e: self._invoke())
        self.bind("<space>", lambda e: self._invoke())

    def set(self, text=None, kind=None, command=None):
        if text is not None:
            self.text = text
        if kind is not None:
            self.kind = kind
        if command is not None:
            self.command = command
        self.draw()

    def _press(self, e):
        if self.enabled:
            self.pressed = True
            self.focus_set()
            self.draw()

    def _release(self, e):
        was = self.pressed
        self.pressed = False
        self.draw()
        w, h = self.size()
        if was and 0 <= e.x <= w and 0 <= e.y <= h:
            self._invoke()

    def _invoke(self):
        if self.enabled and self.command:
            self.command()

    def fit_width(self, min_width=0):
        """Larghezza adatta al testo (che cambia lunghezza da una lingua all'altra)."""
        font = tkfont.Font(font=self.t.font_button if self.kind != "ghost" else self.t.font)
        extra = self.t.px(22) if self.chevron else 0
        self.configure(width=max(min_width, font.measure(self.text) + self.t.px(32) + extra))

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        r = t.px(6)
        if self.kind == "primary":
            fill = t.ACCENT_PRESS if self.pressed else t.ACCENT_HOVER if self.hover else t.ACCENT
            fg, outline = "#ffffff", ""
        elif self.kind == "danger":
            fill = "#5a2a2a" if self.pressed else "#4a2626" if self.hover else "#3d2324"
            fg, outline = "#ffd9d8", "#6b3434"
        elif self.kind == "ghost":
            fill = t.FIELD_HOVER if self.pressed else t.FIELD if self.hover else self["bg"]
            fg, outline = t.TEXT_2 if not self.hover else t.TEXT, ""
        else:
            fill = t.SELECTED if self.pressed else t.FIELD_HOVER if self.hover else t.FIELD
            fg, outline = t.TEXT, t.BORDER
        if not self.enabled:
            fill = t.FIELD if self.kind != "ghost" else self["bg"]
            fg, outline = t.DISABLED, t.BORDER if self.kind not in ("ghost",) else ""
        rounded_rect(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=outline)
        tx = w / 2
        if self.chevron:
            # testo spostato a sinistra e freccia disegnata a destra
            cx, cy, s = w - t.px(16), h / 2, t.px(4)
            self.create_line(cx - s, cy - s / 2, cx, cy + s / 2, cx + s, cy - s / 2, fill=fg,
                             width=max(1, t.px(1.5)), capstyle="round", joinstyle="round")
            tx = (w - t.px(22)) / 2 + t.px(2)
        self.create_text(tx, h / 2, text=self.text, fill=fg,
                         font=t.font_button if self.kind != "ghost" else t.font)
        self.focus_ring(0, 0, w, h, r)


class InfoButton(_CanvasWidget):
    """Pulsante tondo con la "i" disegnata: apre una spiegazione. Al passaggio si accende d'azzurro."""

    def __init__(self, parent, theme, command, size=18):
        super().__init__(parent, theme, size)
        self.configure(width=theme.px(size), cursor="hand2")
        self.command = command
        self.bind("<ButtonPress-1>", lambda e: self._set("pressed", True))
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Return>", lambda e: self.command())
        self.bind("<space>", lambda e: self.command())

    def _release(self, e):
        was = self.pressed
        self._set("pressed", False)
        w, h = self.size()
        if was and 0 <= e.x <= w and 0 <= e.y <= h:
            self.command()

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        d = min(w, h) - 2
        x0, y0 = (w - d) / 2, (h - d) / 2
        lit = self.hover or self.focused
        fill = t.ACCENT_PRESS if self.pressed else t.ACCENT if lit else t.FIELD
        outline = t.ACCENT_BRIGHT if lit else t.BORDER
        fg = "#ffffff" if lit else t.TEXT_2
        self.create_oval(x0, y0, x0 + d, y0 + d, fill=fill, outline=outline, width=max(1, t.px(1)))
        # la "i" è disegnata: un carattere cambierebbe aspetto da una lingua all'altra
        cx, cy, s = w / 2, h / 2, d / 18
        self.create_oval(cx - 1.4 * s, cy - 5.6 * s, cx + 1.4 * s, cy - 2.8 * s, fill=fg, outline="")
        self.create_line(cx, cy - 0.6 * s, cx, cy + 4.8 * s, fill=fg, width=max(1.5, 2.6 * s), capstyle="round")


class ProfileCards(_CanvasWidget):
    """Schede affiancate per i profili rapidi: nome e dettaglio; quella che corrisponde alle impostazioni
    correnti è evidenziata. options: [(nome, dettaglio, valore)]; selected_fn() ritorna il valore attivo."""

    def __init__(self, parent, theme, options, selected_fn, command, height=54, tip_fn=None):
        super().__init__(parent, theme, height, takefocus=False)
        self.options = options
        self.selected_fn = selected_fn
        self.command = command
        self.hover_i = None
        self.configure(cursor="hand2")
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: self._hover_at(None), add="+")
        self.bind("<ButtonRelease-1>", self._click)
        # suggerimento della scheda sotto il puntatore; passando a un'altra scheda riparte
        self.tip = Tooltip(self, theme, lambda: tip_fn(self.hover_i or 0)) if tip_fn else None

    def index_at(self, x):
        w, _ = self.size()
        return max(0, min(len(self.options) - 1, int(x * len(self.options) / w)))

    def _hover_at(self, i):
        if i != self.hover_i:
            self.hover_i = i
            self.draw()
            if self.tip and i is not None:
                self.tip._schedule()

    def _motion(self, e):
        self._hover_at(self.index_at(e.x) if self.enabled else None)

    def _click(self, e):
        if self.enabled:
            self.command(self.options[self.index_at(e.x)][2])

    def _fit(self, text, font, width):
        f = tkfont.Font(font=font)
        if f.measure(text) <= width:
            return text
        while text and f.measure(text + "...") > width:
            text = text[:-1]
        return text + "..."

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        n = len(self.options)
        gap = t.px(6)
        cw = (w - gap * (n - 1)) / n
        active = self.selected_fn()
        for i, (name, detail, value) in enumerate(self.options):
            x1 = i * (cw + gap)
            x2 = x1 + cw
            sel = value == active
            if not self.enabled:
                fill, outline, fg, fg2 = t.FIELD, t.BORDER, t.DISABLED, t.DISABLED
            elif sel:
                fill, outline, fg, fg2 = t.SELECTED, t.ACCENT_BRIGHT, t.TEXT, t.TEXT_2
            else:
                fill = t.FIELD_HOVER if i == self.hover_i else t.FIELD
                outline, fg, fg2 = t.BORDER, t.TEXT, t.TEXT_3
            rounded_rect(self, x1 + 1, 1, x2 - 1, h - 1, t.px(6), fill=fill, outline=outline)
            inner = cw - t.px(10)
            self.create_text((x1 + x2) / 2, h * 0.37, text=self._fit(name, t.font_button, inner), fill=fg,
                             font=t.font_button)
            self.create_text((x1 + x2) / 2, h * 0.70, text=self._fit(detail, t.font_small, inner), fill=fg2,
                             font=t.font_small)


class Collapsible(tk.Frame):
    """Sezione a tendina: intestazione cliccabile con freccia, contenuto in self.body.

    In self.extra si possono mettere piccoli controlli accanto al titolo (restano visibili anche a sezione
    chiusa e non aprono la tendina); set_summary scrive un promemoria a destra dell'intestazione.
    """

    def __init__(self, parent, theme, title, expanded=False, on_toggle=None):
        bg = parent["bg"]
        super().__init__(parent, bg=bg)
        self.t = theme
        self.expanded = expanded
        self.on_toggle = on_toggle
        self.header = tk.Frame(self, bg=bg, cursor="hand2")
        self.header.pack(fill="x")
        # titolo allineato agli altri titoli del pannello; freccia in fondo a destra
        size = theme.px(14)
        self.title = tk.Label(self.header, text=title, bg=bg, fg=theme.TEXT, font=theme.font_section, anchor="w",
                              cursor="hand2")
        self.title.pack(side="left")
        self.extra = tk.Frame(self.header, bg=bg)
        self.extra.pack(side="left", padx=(theme.px(6), 0))
        self.arrow = tk.Canvas(self.header, width=size, height=size, bg=bg, highlightthickness=0, bd=0,
                               takefocus=1, cursor="hand2")
        self.arrow.pack(side="right")
        self.summary = tk.Label(self.header, text="", bg=bg, fg=theme.TEXT_3, font=theme.font_small, cursor="hand2")
        self.summary.pack(side="right", padx=(0, theme.px(8)))
        self.body = tk.Frame(self, bg=bg)
        self.hover = False
        for w in (self.header, self.arrow, self.title, self.summary):
            w.bind("<Button-1>", lambda e: self.toggle())
            w.bind("<Enter>", lambda e: self._hover(True))
            w.bind("<Leave>", lambda e: self._hover(False))
        self.arrow.bind("<Return>", lambda e: self.toggle())
        self.arrow.bind("<space>", lambda e: self.toggle())
        self.arrow.bind("<FocusIn>", lambda e: self._hover(True))
        self.arrow.bind("<FocusOut>", lambda e: self._hover(False))
        self._apply()

    def _hover(self, on):
        self.hover = on
        self.title.configure(fg=self.t.ACCENT_BRIGHT if on else self.t.TEXT)
        self._draw_arrow()

    def _draw_arrow(self):
        c, s = self.arrow, self.t.px(14)
        c.delete("all")
        fg = self.t.ACCENT_BRIGHT if self.hover else self.t.TEXT_2
        m, w = s / 2, max(1.5, self.t.px(1.6))
        if self.expanded:     # punta in giù
            pts = (m - s * 0.28, m - s * 0.14, m, m + s * 0.14, m + s * 0.28, m - s * 0.14)
        else:                 # punta a destra
            pts = (m - s * 0.14, m - s * 0.28, m + s * 0.14, m, m - s * 0.14, m + s * 0.28)
        c.create_line(*pts, fill=fg, width=w, capstyle="round", joinstyle="round")

    def _apply(self):
        if self.expanded:
            self.body.pack(fill="x", pady=(self.t.px(8), 0))
        else:
            self.body.pack_forget()
        self._draw_arrow()

    def toggle(self):
        self.expanded = not self.expanded
        self._apply()
        if self.on_toggle:
            self.on_toggle(self.expanded)

    def set_summary(self, text, fg=None):
        self.summary.configure(text=text, fg=fg or self.t.TEXT_3)


class Segmented(_CanvasWidget):
    """Selettore a segmenti legato a una variabile; un valore fuori elenco non seleziona nulla."""

    def __init__(self, parent, theme, options, variable, command=None, height=32):
        super().__init__(parent, theme, height)
        self.options = options
        self.var = variable
        self.command = command
        self.hover_index = None
        self.configure(cursor="hand2")
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: (setattr(self, "hover_index", None), self.draw()))
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Left>", lambda e: self._step(-1))
        self.bind("<Right>", lambda e: self._step(1))
        variable.trace_add("write", lambda *a: self.draw())

    def _index_at(self, x):
        w, _ = self.size()
        return min(len(self.options) - 1, max(0, int(x / (w / len(self.options)))))

    def _motion(self, e):
        i = self._index_at(e.x)
        if i != self.hover_index:
            self.hover_index = i
            self.draw()

    def _select(self, i):
        if not self.enabled:
            return
        value = self.options[i][1]
        if str(self.var.get()) != str(value):
            self.var.set(value)
            if self.command:
                self.command()

    def _click(self, e):
        self.focus_set()
        self._select(self._index_at(e.x))

    def _step(self, d):
        values = [str(v) for _, v in self.options]
        cur = str(self.var.get())
        i = values.index(cur) + d if cur in values else 0
        self._select(max(0, min(len(values) - 1, i)))

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        r = t.px(6)
        rounded_rect(self, 1, 1, w - 1, h - 1, r, fill=t.FIELD, outline=t.BORDER)
        n = len(self.options)
        seg = (w - 2) / n
        cur = str(self.var.get())
        pad = t.px(3)
        for i, (label, value) in enumerate(self.options):
            x1 = 1 + i * seg
            x2 = x1 + seg
            selected = str(value) == cur
            if selected:
                rounded_rect(self, x1 + pad, 1 + pad, x2 - pad, h - 1 - pad, t.px(4),
                             fill=t.SELECTED if self.enabled else t.FIELD_HOVER, outline="")
            elif self.hover_index == i and self.enabled:
                rounded_rect(self, x1 + pad, 1 + pad, x2 - pad, h - 1 - pad, t.px(4), fill=t.FIELD_HOVER, outline="")
            if not self.enabled:
                fg = t.DISABLED
            else:
                fg = t.TEXT if selected else t.TEXT_2
            self.create_text((x1 + x2) / 2, h / 2, text=label, fill=fg,
                             font=t.font_strong if selected else t.font)
        self.focus_ring(0, 0, w, h, r)


class Slider(_CanvasWidget):
    """Cursore a valori interi, con lo zero come riferimento e il valore scritto a destra."""

    def __init__(self, parent, theme, variable, lo, hi, command=None, height=26, fmt=None, value_width=40):
        super().__init__(parent, theme, height)
        self.var = variable
        self.lo, self.hi = lo, hi
        self.command = command
        # fmt(valore) -> testo mostrato a destra; value_width: spazio riservato a quel testo
        self.fmt = fmt or (lambda v: ("%+d" % v) if v else "0")
        self.value_width = value_width
        self.configure(cursor="hand2")
        self.bind("<ButtonPress-1>", self._drag)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<Left>", lambda e: self._set_value(self.var.get() - 1))
        self.bind("<Right>", lambda e: self._set_value(self.var.get() + 1))
        self.bind("<Double-Button-1>", lambda e: self._set_value(0))
        variable.trace_add("write", lambda *a: self.draw())

    def _track(self):
        w, h = self.size()
        return self.t.px(8), w - self.t.px(self.value_width), h / 2

    def _set_value(self, v):
        v = max(self.lo, min(self.hi, int(v)))
        if v != self.var.get():
            self.var.set(v)
            if self.command:
                self.command()

    def _drag(self, e):
        if not self.enabled:
            return
        self.focus_set()
        x1, x2, _ = self._track()
        frac = (e.x - x1) / max(1, x2 - x1)
        self._set_value(round(self.lo + frac * (self.hi - self.lo)))

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        x1, x2, cy = self._track()
        v = self.var.get()
        pos = lambda val: x1 + (val - self.lo) / (self.hi - self.lo) * (x2 - x1)  # noqa: E731
        th = t.px(2)
        self.create_rectangle(x1, cy - th, x2, cy + th, fill=t.BORDER, outline="")
        zero = pos(0)
        self.create_rectangle(min(zero, pos(v)), cy - th, max(zero, pos(v)), cy + th,
                              fill=t.ACCENT if self.enabled else t.DISABLED, outline="")
        self.create_line(zero, cy - t.px(6), zero, cy + t.px(6), fill=t.TEXT_3)
        rad = t.px(7) if (self.hover or self.focused) and self.enabled else t.px(6)
        knob = t.TEXT if self.enabled else t.DISABLED
        self.create_oval(pos(v) - rad, cy - rad, pos(v) + rad, cy + rad, fill=knob, outline="")
        if self.focused and self.enabled:
            self.create_oval(pos(v) - rad - 3, cy - rad - 3, pos(v) + rad + 3, cy + rad + 3,
                             outline=t.ACCENT_BRIGHT, width=max(1, t.px(1.5)))
        self.create_text(w - t.px(4), cy, text=self.fmt(v), anchor="e", fill=t.TEXT_2, font=t.font)


class PathField(_CanvasWidget):
    """Campo che mostra un percorso con l'icona di una cartella; il clic esegue command."""

    def __init__(self, parent, theme, variable, command, height=36):
        super().__init__(parent, theme, height)
        self.var = variable
        self.command = command
        self._font = tkfont.Font(font=theme.font)
        self.configure(cursor="hand2")
        self.bind("<ButtonPress-1>", lambda e: self._set("pressed", True))
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Return>", lambda e: self.command())
        self.bind("<space>", lambda e: self.command())
        variable.trace_add("write", lambda *a: self.draw())
        Tooltip(self, theme, lambda: self.var.get())

    def _release(self, e):
        was = self.pressed
        self.pressed = False
        self.draw()
        w, h = self.size()
        if was and self.enabled and 0 <= e.x <= w and 0 <= e.y <= h:
            self.command()

    def _fit(self, text, width):
        if self._font.measure(text) <= width:
            return text
        keep = len(text)
        while keep > 6:
            keep -= 1
            cut = text[:keep // 2] + "..." + text[-(keep - keep // 2):]
            if self._font.measure(cut) <= width:
                return cut
        return "..."

    def draw(self):
        self.delete("all")
        t = self.t
        w, h = self.size()
        r = t.px(6)
        fill = t.FIELD_HOVER if (self.hover or self.pressed) and self.enabled else t.FIELD
        rounded_rect(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=t.BORDER)
        # icona cartella disegnata: linguetta in alto a sinistra e corpo
        ix, cy = t.px(12), h / 2
        iw, ih = t.px(16), t.px(12)
        color = t.TEXT_2 if self.enabled else t.DISABLED
        self.create_polygon(ix, cy - ih / 2, ix + iw * 0.42, cy - ih / 2, ix + iw * 0.55, cy - ih / 2 + t.px(2),
                            ix + iw, cy - ih / 2 + t.px(2), ix + iw, cy + ih / 2, ix, cy + ih / 2,
                            fill="", outline=color, width=max(1, t.px(1.3)), joinstyle="round")
        tx = ix + iw + t.px(10)
        text = self._fit(self.var.get(), w - tx - t.px(10))
        self.create_text(tx, cy, text=text, anchor="w", fill=t.TEXT if self.enabled else t.DISABLED, font=t.font)
        self.focus_ring(0, 0, w, h, r)


class Tooltip:
    """Testo che compare sotto il widget dopo una breve sosta del mouse."""

    def __init__(self, widget, theme, text_fn, delay_ms=500):
        self.widget, self.t, self.text_fn, self.delay = widget, theme, text_fn, delay_ms
        self.win = None
        self.job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, e=None):
        self._hide()
        self.job = self.widget.after(self.delay, self._show)

    def _show(self):
        self.win = tk.Toplevel(self.widget)
        self.win.wm_overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        self.win.configure(bg=self.t.BORDER)
        tk.Label(self.win, text=self.text_fn(), bg=self.t.FIELD, fg=self.t.TEXT, font=self.t.font_small,
                 padx=self.t.px(8), pady=self.t.px(4), justify="left", wraplength=self.t.px(320)).pack(padx=1, pady=1)
        self.win.update_idletasks()
        # sotto il widget, ma spostato a sinistra se un testo lungo uscirebbe dallo schermo
        margin = self.t.px(8)
        right_edge = self.widget.winfo_screenwidth() - margin
        x = min(self.widget.winfo_rootx(), right_edge - self.win.winfo_reqwidth())
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + self.t.px(4)
        self.win.wm_geometry("+%d+%d" % (max(margin, x), y))

    def _hide(self, e=None):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None
        if self.win:
            self.win.destroy()
            self.win = None


class ScrollArea(tk.Frame):
    """Area verticale scorrevole con barra sottile disegnata; la barra compare solo se serve.

    I contenuti vanno in self.body. Rotellina del mouse attiva quando il puntatore è sopra l'area.
    """

    def __init__(self, parent, theme):
        bg = parent["bg"]
        super().__init__(parent, bg=bg)
        self.t = theme
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=theme.px(24))
        self.bar = tk.Canvas(self, width=theme.px(10), bg=bg, highlightthickness=0, bd=0)
        self.bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self._drag_from = None
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", self._wheel))
        self.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))
        self.bar.bind("<ButtonPress-1>", self._bar_press)
        self.bar.bind("<B1-Motion>", self._bar_drag)

    def _overflow(self):
        first, last = self.canvas.yview()
        return last - first < 0.999

    def _on_body(self, e):
        self.canvas.configure(scrollregion=(0, 0, e.width, e.height))
        self.draw_bar()

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)
        self.draw_bar()

    def _wheel(self, e):
        if self._overflow():
            self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
            self.draw_bar()

    def _bar_press(self, e):
        first, last = self.canvas.yview()
        h = max(self.bar.winfo_height(), 1)
        if first * h <= e.y <= last * h:
            self._drag_from = (e.y, first)
        else:
            self._drag_from = None
            self.canvas.yview_moveto(e.y / h - (last - first) / 2)
            self.draw_bar()

    def _bar_drag(self, e):
        if self._drag_from:
            y0, first0 = self._drag_from
            self.canvas.yview_moveto(first0 + (e.y - y0) / max(self.bar.winfo_height(), 1))
            self.draw_bar()

    def draw_bar(self):
        self.bar.delete("all")
        if not self._overflow():
            return
        first, last = self.canvas.yview()
        h = self.bar.winfo_height()
        w = self.bar.winfo_width()
        r = self.t.px(2)
        rounded_rect(self.bar, w / 2 - r, first * h + 2, w / 2 + r, last * h - 2, r, fill=self.t.SELECTED,
                     outline="")


class Progress(tk.Canvas):
    def __init__(self, parent, theme, height=6):
        super().__init__(parent, height=theme.px(height), bg=parent["bg"], highlightthickness=0, bd=0)
        self.t = theme
        self.value = 0.0
        self.active = False
        self.bind("<Configure>", lambda e: self.draw())

    def set(self, value, active=True):
        self.value = max(0.0, min(1.0, value))
        self.active = active
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 2), max(self.winfo_height(), 2)
        rounded_rect(self, 0, 0, w, h, h / 2, fill=self.t.FIELD, outline="")
        if self.value > 0:
            rounded_rect(self, 0, 0, max(h, w * self.value), h, h / 2,
                         fill=self.t.ACCENT if self.active else self.t.OK, outline="")


class StatusDot(tk.Canvas):
    def __init__(self, parent, theme):
        size = theme.px(10)
        super().__init__(parent, width=size, height=size, bg=parent["bg"], highlightthickness=0, bd=0)
        self.t = theme
        self.size = size

    def set(self, level):
        color = {"ok": self.t.OK, "wait": self.t.WAIT, "error": self.t.ERROR}.get(level, self.t.TEXT_3)
        self.delete("all")
        self.create_oval(1, 1, self.size - 1, self.size - 1, fill=color, outline="")


def label(parent, theme, text="", font=None, fg=None, **kw):
    return tk.Label(parent, text=text, bg=parent["bg"], fg=fg or theme.TEXT_2, font=font or theme.font_label,
                    anchor="w", justify="left", **kw)


def link(parent, theme, text, command):
    lab = tk.Label(parent, text=text, bg=parent["bg"], fg=theme.TEXT_2, font=theme.font_small, cursor="hand2",
                   takefocus=1)
    lab.bind("<Enter>", lambda e: lab.configure(fg=theme.ACCENT_BRIGHT))
    lab.bind("<Leave>", lambda e: lab.configure(fg=theme.TEXT_2))
    lab.bind("<Button-1>", lambda e: command())
    lab.bind("<Return>", lambda e: command())
    return lab


def entry(parent, theme, variable):
    return tk.Entry(parent, textvariable=variable, bg=theme.FIELD, fg=theme.TEXT, insertbackground=theme.TEXT,
                    relief="flat", font=theme.font, highlightthickness=1, highlightbackground=theme.BORDER,
                    highlightcolor=theme.ACCENT_BRIGHT, selectbackground=theme.ACCENT, selectforeground="#ffffff",
                    disabledbackground=theme.FIELD, disabledforeground=theme.DISABLED)


def center_on_work_area(root):
    """Centra la finestra, cornice e barra del titolo comprese, nell'area utile del desktop
    (esclusa la barra delle applicazioni). La finestra deve essere già mappata."""
    try:
        import ctypes
        from ctypes import wintypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        work = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(work), 0)  # SPI_GETWORKAREA
        outer = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(outer))
        # bordi visibili: Windows 10/11 aggiunge attorno alla finestra bordi invisibili di qualche pixel
        visible = wintypes.RECT()
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(visible), ctypes.sizeof(visible)) != 0:
            visible = outer
        vw, vh = visible.right - visible.left, visible.bottom - visible.top
        left = work.left + (work.right - work.left - vw) // 2
        top = max(work.top, work.top + (work.bottom - work.top - vh) // 2)
        x = outer.left + (left - visible.left)
        y = outer.top + (top - visible.top)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)  # NOSIZE|NOZORDER|NOACTIVATE
    except (AttributeError, OSError):
        pass


def dark_title_bar(root):
    """Barra del titolo scura su Windows 10/11 (attributo DWM 20)."""
    try:
        import ctypes
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        for attr in (20, 19):
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), 4) == 0:
                break
    except (AttributeError, OSError):
        pass
