# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Correzione colore e curve gamma per i comandi ESC m ed ESC z (ESC/I livello B3 e B4 in su).

La matrice e la sua codifica seguono il backend SANE epson2 (epson2-cct.c, epson2-commands.c):
per GT-10000 / ES-6000 SANE usa il profilo 0x05 "ES-6000H" in modalità riflessiva.
"""

import math

# profilo riflessivo 0x05 (ES-6000H), righe R, G, B
GT10000_CCT = (1.1419, -0.0596, -0.0825,
               -0.1234, 1.2812, -0.1413,
               0.0703, -0.5720, 1.5016)

IDENTITY_CCT = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

# ordine in cui lo scanner vuole i 9 coefficienti (G prima di R, come in SANE)
_CC_INDEX = (4, 1, 7, 3, 0, 6, 5, 2, 8)


def _roundup_index(frac):
    index, best = -1, 0.0
    for i, f in enumerate(frac):
        if f >= 0 and best < f:
            index, best = i, f
    return index


def _rounddown_index(frac):
    index, best = -1, 1.0
    for i, f in enumerate(frac):
        if f <= 0 and best > f:
            index, best = i, f
    return index


def round_cct(cct):
    """Coefficienti in trentaduesimi, corretti perché ogni riga sommi a 32 (round_cct di SANE)."""
    mult = [c * 32 for c in cct]
    rnd = [int(math.floor(m + 0.5)) for m in mult]
    for _ in range(2):
        for i in range(3):
            k = i * 3
            if rnd[k] == 11 and rnd[k] == rnd[k + 1] == rnd[k + 2]:
                rnd[k + i] -= 1
                mult[k + i] = rnd[k + i]
        sums = [sum(rnd[i * 3:i * 3 + 3]) for i in range(3)]
        frac = [mult[i] - rnd[i] for i in range(9)]
        for i in range(3):
            k = i * 3
            if sums[i] < 32:
                j = _roundup_index(frac[k:k + 3])
                if j != -1:
                    rnd[k + j] += 1
                    mult[k + j] = rnd[k + j]
                    sums[i] += 1
            elif sums[i] > 32:
                j = _rounddown_index(frac[k:k + 3])
                if j != -1:
                    rnd[k + j] -= 1
                    mult[k + j] = rnd[k + j]
                    sums[i] -= 1
        if sums == [32, 32, 32]:
            break
    return rnd


def _int2cpt(v):
    """Valore con segno nel bit alto, come vuole ESC m."""
    if v >= 0:
        return min(v, 127)
    return 0x80 | min(-v, 127)


def color_coefficients(cct=GT10000_CCT):
    """I 9 byte da inviare dopo ESC m."""
    rnd = round_cct(cct)
    return bytes(_int2cpt(rnd[i]) for i in _CC_INDEX)


def gamma_table(gamma):
    """Tabella di 256 valori per ESC z: uscita = ingresso ^ (1 / gamma)."""
    return bytes(min(255, int(round(255 * (i / 255.0) ** (1.0 / gamma)))) for i in range(256))
