# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Immagini della procedura d'installazione, ricavate dall'icona del programma (BMP, come vuole Inno Setup)."""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
BG = (255, 255, 255)


def on_background(img, size, box):
    out = Image.new("RGB", size, BG)
    icon = img.resize((box, box), Image.LANCZOS)
    out.paste(icon, ((size[0] - box) // 2, (size[1] - box) // 2), icon)
    return out


def main():
    small = Image.open(os.path.join(APP, "icona_piccola.png")).convert("RGBA")
    big = Image.open(os.path.join(APP, "icona.png")).convert("RGBA")
    for n in (55, 110):                                   # in alto a destra nelle pagine interne
        on_background(small, (n, n), n).save(os.path.join(HERE, "wizard_small_%d.bmp" % n))
    for w, h in ((164, 314), (328, 628)):                 # a sinistra in benvenuto e fine
        panel = Image.new("RGB", (w, h), (232, 244, 246))
        icon = big.resize((int(w * 0.8), int(w * 0.8)), Image.LANCZOS)
        panel.paste(icon, ((w - icon.width) // 2, int(h * 0.30)), icon)
        panel.save(os.path.join(HERE, "wizard_%d.bmp" % w))


if __name__ == "__main__":
    main()
