# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Correzione delle righe verticali con una calibrazione sul coperchio chiuso.

Il GT-10000+ legge il vetro con un sensore lineare che scorre dall'alto in basso: un granello di polvere
nell'ottica toglie luce sempre alle stesse colonne e lascia una riga per tutta la lunghezza della pagina
(sul nostro esemplare, a 122 mm, rosso e verde fino al 19% in meno: la riga ciano). È lo stesso difetto
dei satelliti a scansione "pushbroom" e si corregge allo stesso modo, con una calibrazione relativa:

1. si legge il coperchio bianco a vetro vuoto, a 600 x 50 dpi e con curva lineare (gamma 1,0);
2. per ogni fascia di 20 mm si fa il profilo delle colonne e lo si divide per la sua mediana mobile su
   255 colonne (10,8 mm, molto più larga della riga, che misura circa 2 mm): quello che resta è la
   sensibilità relativa di ogni colonna;
3. lungo il vetro ogni colonna si liscia con una mediana su 5 fasce e una media su 3: un granello sul
   vetro o sul coperchio occupa una o due fasce e sparisce, una riga vera attraversa tutto il vetro e
   resta; si correggono solo le colonne che restano oltre l'1,5% (sotto, in codifica, è meno di un livello);
4. in scansione ogni punto torna lineare con la curva dello scanner, si divide per il fattore della sua
   colonna (mediato sull'impronta a 600 dpi e interpolato lungo il vetro, perché la riga misurata
   cresce dall'alto in basso) e si ricodifica. I punti a 255 restano 255: oltre il bianco non si sa.

Serve numpy (solo qui: il resto del programma usa Pillow).
"""

import datetime

import numpy as np

CAL_DPI = 600          # risoluzione orizzontale della calibrazione: quella ottica
CAL_DPI_Y = 50         # in verticale basta poco: la riga è uguale su tutta la colonna
BAND_MM = 20.0         # altezza delle fasce
WINDOW = 255           # colonne della mediana mobile (10,8 mm a 600 dpi)
THRESHOLD = 0.015      # scarto minimo, dopo la lisciatura, per correggere una colonna
MIN_EFFECT = 0.003     # sotto questo scarto una colonna di uscita non si tocca
# Origine orizzontale delle scansioni rispetto alla calibrazione a 600 dpi, in colonne a 600 dpi.
# Misurata il 12/10/2026 leggendo il coperchio a ogni risoluzione con curva lineare: fino a 300 dpi lo
# scanner riduce la risoluzione in un altro modo e la riga cade circa 5 colonne (0,2 mm) più a destra;
# senza questo scarto la correzione lasciava un doppio bordo (a 300 dpi, errore da 0,041 a 0,015).
X_OFFSET = {50: 7.75, 75: 5.5, 100: 6.25, 150: 5.25, 200: 4.75, 300: 5.0, 400: 2.5, 600: 1.0, 800: 2.0,
            1200: 1.75}
X_OFFSET_PREVIEW = 9.0           # anteprima a 50 dpi in modalità veloce
# Le calibrazioni nuove misurano gli scarti dello scanner collegato (measure_offset): questa tabella
# vale solo per i file di calibrazione vecchi, che non li hanno.
OFFSET_DPIS = (50, 75, 100, 150, 200, 300, 400, 600, 800, 1200)   # risoluzioni misurate in calibrazione
OFFSET_AREA_MM = 14.0            # quadrato letto attorno alla riga più evidente
OFFSET_MIN_STREAK = 0.05         # sotto il 5% la riga non basta per misurare lo scarto
BAND_LINES = int(round(BAND_MM / 25.4 * CAL_DPI_Y))
BAND_PITCH_MM = BAND_LINES * 25.4 / CAL_DPI_Y        # 39 righe = 19,81 mm

# Curva standard dello scanner (ESC Z predefinito), da valore codificato a valore lineare.
# Misurata il 12/10/2026 confrontando due scansioni della stessa copertina, una con la curva standard
# e una con gamma 1,0: in ombra è una potenza di 1,95; il bianco del coperchio (circa 230 lineare)
# è già oltre il 255 codificato.
STD_TO_LIN = np.array((
    0.0, 0.1, 0.1, 0.2, 0.2, 0.2, 0.3, 0.3, 0.4, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.3, 1.5, 1.6,
    1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.5, 3.7, 3.9, 4.2, 4.5, 4.8, 5.1, 5.4, 5.6, 5.9, 6.2, 6.6,
    6.9, 7.3, 7.6, 8.0, 8.3, 8.7, 9.1, 9.4, 9.8, 10.2, 10.7, 11.1, 11.5, 12.0, 12.4, 12.9, 13.4, 13.9,
    14.4, 14.9, 15.4, 16.0, 16.6, 17.2, 17.8, 18.5, 19.1, 19.8, 20.4, 21.1, 21.7, 22.4, 23.0, 23.6,
    24.2, 24.7, 25.2, 25.8, 26.3, 26.8, 27.3, 27.9, 28.4, 29.0, 29.5, 30.1, 30.7, 31.3, 31.9, 32.5,
    33.1, 33.8, 34.4, 35.1, 35.7, 36.4, 37.1, 37.8, 38.5, 39.3, 40.0, 40.7, 41.4, 42.2, 42.9, 43.7,
    44.4, 45.2, 45.9, 46.7, 47.4, 48.2, 49.0, 49.8, 50.5, 51.3, 52.1, 53.0, 53.8, 54.7, 55.5, 56.4,
    57.3, 58.2, 59.0, 59.9, 60.8, 61.7, 62.7, 63.6, 64.6, 65.5, 66.6, 67.6, 68.6, 69.5, 70.5, 71.4,
    72.3, 73.2, 74.1, 74.9, 75.8, 76.6, 77.5, 78.3, 79.2, 80.1, 81.0, 81.9, 82.8, 83.7, 84.6, 85.6,
    86.5, 87.5, 88.6, 89.6, 90.6, 91.6, 92.6, 93.6, 94.6, 95.6, 96.7, 97.7, 98.8, 99.9, 100.9, 102.0,
    103.0, 104.1, 105.2, 106.3, 107.3, 108.4, 109.5, 110.5, 111.6, 112.7, 113.8, 114.9, 116.0, 117.2,
    118.3, 119.4, 120.6, 121.7, 122.8, 123.9, 125.1, 126.2, 127.4, 128.5, 129.7, 130.9, 132.1, 133.2,
    134.4, 135.6, 136.8, 138.0, 139.2, 140.4, 141.7, 142.9, 144.1, 145.3, 146.6, 147.8, 149.1, 150.4,
    151.7, 152.9, 154.2, 155.5, 156.8, 158.0, 159.3, 160.6, 161.9, 163.2, 164.5, 165.9, 167.2, 168.5,
    169.9, 171.2, 172.6, 173.9, 175.3, 176.6, 178.0, 179.3, 180.7, 182.1, 183.4, 184.8, 186.2, 187.6,
    189.0, 190.4, 191.8, 193.2, 194.7, 196.1, 197.6, 199.1, 200.6, 202.3, 204.1, 206.3, 208.6, 211.1,
    214.2, 218.0), np.float32)
LEVELS = np.arange(256, dtype=np.float32)
# strettamente crescente (in ombra l'arrotondamento ripete i valori): serve per invertirla
STD_TO_LIN += LEVELS * 1e-3


class CalibrationError(Exception):
    """Calibrazione non valida; key è la chiave del messaggio da mostrare."""

    def __init__(self, key, **args):
        super().__init__(key)
        self.key = key
        self.args_ = args


def _running_median(profiles):
    pad = WINDOW // 2
    padded = np.pad(profiles, ((0, 0), (pad, pad), (0, 0)), mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(padded, WINDOW, axis=1), axis=-1)


def analyze(data, width, height, channels):
    """Dalla lettura del coperchio (lineare, CAL_DPI x CAL_DPI_Y) alle colonne con riga e ai loro fattori.

    Ritorna (colonne, fattori[fasce, colonne, canali], numero di righe distinte).
    """
    img = np.frombuffer(data, np.uint8, width * height * channels).reshape(height, width, channels)
    img = img.astype(np.float32)
    white = float(np.median(img))
    if white < 120:
        raise CalibrationError("calib_err_dark", level=int(white))
    if (img >= 255).mean() > 0.01:
        raise CalibrationError("calib_err_saturated")
    # un foglio o un accessorio sul vetro: molti punti nettamente più scuri della loro riga, oppure
    # righe intere molto più scure del coperchio (un foglio largo quanto il vetro). Il confronto con la
    # riga e non con tutto il vetro lascia passare le variazioni uniformi di luce (lampada appena accesa)
    rows = np.median(img, axis=1, keepdims=True)
    if (img < 0.75 * rows).mean() > 0.005 or (rows < 0.6 * white).mean() > 0.02:
        raise CalibrationError("calib_err_not_empty")
    band = BAND_LINES
    nb = height // band
    if nb < 5:
        raise CalibrationError("calib_err_short")
    prof = np.stack([img[b * band:(b + 1) * band].mean(0) for b in range(nb)])
    ratio = prof / np.maximum(_running_median(prof), 1.0)
    # lungo il vetro: mediana su 5 fasce (toglie i granelli), poi media su 3 (toglie il rumore)
    padded = np.pad(ratio, ((2, 2), (0, 0), (0, 0)), mode="edge")
    med = np.median(np.lib.stride_tricks.sliding_window_view(padded, 5, axis=0), axis=-1)
    padded = np.pad(med, ((1, 1), (0, 0), (0, 0)), mode="edge")
    smooth = (padded[:-2] + padded[1:-1] + padded[2:]) / 3
    mask = (np.abs(smooth - 1) > THRESHOLD).any(axis=0)          # colonne, canali
    none = np.zeros_like(mask[:1])
    mask = mask | np.r_[mask[1:], none] | np.r_[none, mask[:-1]]   # una colonna di margine
    edge = WINDOW // 2                                           # ai bordi la mediana non è affidabile
    mask[:edge] = mask[-edge:] = False
    cols = np.flatnonzero(mask.any(1))
    factors = np.where(mask[cols][None], smooth[:, cols], 1.0).astype(np.float32)
    return cols.astype(np.int32), factors, count_streaks(cols)


def count_streaks(cols):
    """Righe distinte: gruppi di colonne separati da più di 3 colonne."""
    return int(np.count_nonzero(np.diff(np.r_[-10, cols]) > 4)) if len(cols) else 0


class Calibration:
    """Fattori per colonna, per colore e per grigi; si salva in un file .npz."""

    def __init__(self, parts, date, width, offsets=None, offset_preview=None):
        self.parts = parts      # {"color": (colonne, fattori), "gray": (...)}
        self.date = date
        self.width = width
        # scarti d'origine misurati {dpi: colonne a 600 dpi}; None = file vecchio, si usa X_OFFSET
        self.offsets = offsets
        self.offset_preview = offset_preview

    @classmethod
    def from_scans(cls, scans):
        """scans: {"color": (dati, larghezza, altezza), "gray": (...)}."""
        parts, info = {}, {}
        width = 0
        for mode, (data, w, h) in scans.items():
            cols, factors, groups = analyze(data, w, h, 3 if mode == "color" else 1)
            parts[mode] = (cols, factors)
            info[mode] = groups
            width = w
        return cls(parts, datetime.date.today().isoformat(), width), info

    def visible_streaks(self, mode="color", level=0.04):
        """Righe che si vedono a occhio (oltre il 4% in qualche punto del vetro)."""
        if mode not in self.parts:
            return 0
        cols, factors = self.parts[mode]
        return count_streaks(cols[(np.abs(factors - 1) > level).any(axis=(0, 2))])

    def streak_target(self):
        """Dove leggere per misurare gli scarti: (x_mm, y_mm) della riga più evidente, oppure None.

        Tra le fasce dove la riga supera il 5% si sceglie la più in alto, così il carrello fa poca strada.
        """
        if "color" not in self.parts:
            return None
        cols, factors = self.parts["color"]
        if not len(cols):
            return None
        dev = np.abs(factors - 1).max(axis=2)                       # fasce, colonne
        best = int(dev.max(axis=0).argmax())
        if dev[:, best].max() < OFFSET_MIN_STREAK:
            return None
        bands = np.flatnonzero(dev[:, best] >= OFFSET_MIN_STREAK)
        y_mm = (bands[0] + 0.5) * BAND_PITCH_MM
        return float(cols[best]) / CAL_DPI * 25.4, float(max(y_mm, OFFSET_AREA_MM / 2))

    def x_offset(self, dpi, preview=False):
        """Di quante colonne a 600 dpi la scansione cade più a destra della calibrazione."""
        if self.offsets is None:
            return x_offset(dpi, preview)
        if preview and self.offset_preview is not None:
            return self.offset_preview
        if not self.offsets:
            return 0.0
        # risoluzione non misurata: quella misurata più vicina dello stesso tipo (fino a 300 o da 400)
        same = [d for d in self.offsets if (d < 400) == (dpi < 400)] or list(self.offsets)
        return self.offsets[min(same, key=lambda d: abs(d - dpi))]

    def save(self, path):
        arrays = {"date": np.array(self.date), "width": np.array(self.width)}
        if self.offsets is not None:
            dpis = sorted(self.offsets)
            arrays["offset_dpi"] = np.array(dpis, np.int32)
            arrays["offset_val"] = np.array([self.offsets[d] for d in dpis], np.float32)
            arrays["offset_preview"] = np.array(np.nan if self.offset_preview is None else self.offset_preview)
        for mode, (cols, factors) in self.parts.items():
            arrays[mode + "_cols"], arrays[mode + "_factors"] = cols, factors
        with open(path, "wb") as f:
            np.savez_compressed(f, **arrays)

    @classmethod
    def load(cls, path):
        with np.load(path) as z:
            parts = {m: (z[m + "_cols"], z[m + "_factors"]) for m in ("color", "gray") if m + "_cols" in z}
            offsets = preview = None
            if "offset_dpi" in z:
                offsets = {int(d): float(v) for d, v in zip(z["offset_dpi"], z["offset_val"])}
                pv = float(z["offset_preview"])
                preview = None if np.isnan(pv) else pv
            return cls(parts, str(z["date"]), int(z["width"]), offsets, preview)

    def column_factors(self, mode, dpi, left, width, preview=False):
        """Fattori per le colonne di uscita: media sull'impronta di ogni punto a 600 dpi.

        Ritorna (indici delle colonne da correggere, fattori[fasce, colonne, canali]).
        """
        mean = self.footprint(mode, dpi, left, width, self.x_offset(dpi, preview))
        active = np.flatnonzero((np.abs(mean - 1) > MIN_EFFECT).any(axis=(0, 2)))
        return active, mean[:, active].astype(np.float32)

    def footprint(self, mode, dpi, left, width, offset):
        """Sensibilità media sull'impronta di ogni colonna di uscita, con lo scarto indicato."""
        cols, factors = self.parts[mode]
        nb, _, ch = factors.shape
        full = np.ones((nb, self.width + 1, ch), np.float32)
        full[:, cols] = factors
        cum = np.concatenate([np.zeros((nb, 1, ch)), np.cumsum(full, axis=1, dtype=np.float64)], axis=1)

        def integral(x):                 # integrale della sensibilità da 0 a x (x anche frazionario)
            xc = np.clip(x, 0, self.width)
            k = np.floor(xc).astype(int)
            # fuori dal vetro calibrato la sensibilità vale 1
            return cum[:, k] + ((xc - k)[None, :, None] * full[:, k]) + (x - xc)[None, :, None]

        j = np.arange(width)
        a = (left + j) * CAL_DPI / dpi - offset
        b = a + CAL_DPI / dpi
        return (integral(b) - integral(a)) / (CAL_DPI / dpi)

    def measure_offset(self, data, width, height, dpi, left, top, preview=False):
        """Scarto d'origine da una lettura lineare (gamma 1,0, colore) del coperchio attorno a una riga.

        Si confronta il profilo delle colonne con la calibrazione spostata di 0,25 in 0,25 colonne a
        600 dpi; ritorna lo scarto migliore, oppure None se la riga non si riconosce.
        """
        img = np.frombuffer(data, np.uint8, width * height * 3).reshape(height, width, 3).astype(np.float32)
        prof = img.mean(0)                                          # colonne, canali
        edge = max(1, width // 4)
        ref = np.median(np.concatenate([prof[:edge], prof[-edge:]]), axis=0)
        obs = prof / np.maximum(ref, 1.0)
        nb = self.parts["color"][1].shape[0]
        t = np.clip((top + height / 2) / dpi * 25.4 / BAND_PITCH_MM - 0.5, 0, nb - 1)
        i0 = int(t)
        i1, w = min(i0 + 1, nb - 1), t - int(t)
        best, best_err = None, None
        for s in np.arange(-16, 16.01, 0.25):
            mean = self.footprint("color", dpi, left, width, s)
            pred = mean[i0] * (1 - w) + mean[i1] * w
            err = float(np.mean((obs - pred) ** 2))
            if best_err is None or err < best_err:
                best, best_err = float(s), err
        flat = float(np.mean((obs - 1) ** 2))
        # la riga deve spiegare bene il profilo, altrimenti la misura non vale
        return best if best_err < flat * 0.5 else None


def x_offset(dpi, preview=False):
    """Di quante colonne a 600 dpi la scansione cade più a destra della calibrazione."""
    if preview:
        return X_OFFSET_PREVIEW
    if dpi in X_OFFSET:
        return X_OFFSET[dpi]
    return X_OFFSET[300] if dpi < 400 else X_OFFSET[1200]


def correct(img, cal, mode, dpi, dpi_y, left, top, gamma=None, preview=False, chunk=512):
    """Corregge sul posto img (array uint8 di forma righe, colonne, canali).

    left e top sono la posizione dell'area in punti alla risoluzione di scansione; gamma None significa
    curva standard dello scanner; preview indica la lettura veloce dell'anteprima. Ritorna il numero di
    colonne corrette.
    """
    if mode not in cal.parts:
        return 0
    h, w, _ = img.shape
    active, mean = cal.column_factors(mode, dpi, left, w, preview)
    if not active.size:
        return 0
    nb = mean.shape[0]
    for r0 in range(0, h, chunk):
        r1 = min(h, r0 + chunk)
        y_mm = (top + np.arange(r0, r1) + 0.5) / dpi_y * 25.4
        t = np.clip(y_mm / BAND_PITCH_MM - 0.5, 0, nb - 1)
        i0 = np.floor(t).astype(int)
        i1 = np.minimum(i0 + 1, nb - 1)
        wt = (t - i0)[:, None, None]
        f = mean[i0] * (1 - wt) + mean[i1] * wt                     # righe, colonne, canali
        block = img[r0:r1, active, :].astype(np.float32)
        if gamma is None:
            lin = np.interp(block, LEVELS, STD_TO_LIN) / f
            out = np.interp(lin, STD_TO_LIN, LEVELS)
        else:
            out = block / np.power(f, 1.0 / gamma)
        out = np.where(block >= 255, 255, out)
        img[r0:r1, active, :] = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    return int(active.size)


def correct_buffer(buf, cal, mode, width, height, **geom):
    """Come correct, su un bytearray (anteprima)."""
    ch = 3 if mode == "color" else 1
    img = np.frombuffer(buf, np.uint8, width * height * ch).reshape(height, width, ch)
    return correct(img, cal, mode, **geom)


def correct_file(path, cal, mode, width, height, **geom):
    """Come correct, direttamente sul file temporaneo della scansione (anche centinaia di MB)."""
    ch = 3 if mode == "color" else 1
    img = np.memmap(path, np.uint8, "r+", shape=(height, width, ch))
    try:
        return correct(img, cal, mode, **geom)
    finally:
        img.flush()
        del img
