# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test della conversione dei dati grezzi in immagine (lato Windows, serve Pillow).

    python -m unittest discover -s tests -p "test_app*.py"
"""

import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("scanner_app", os.path.join(HERE, "..", "app", "scanner_app.pyw"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class LineartTest(unittest.TestCase):
    def test_paper_is_white(self):
        # carta bianca: lo scanner manda tutti i bit a 1
        img = app.image_from("lineart", 16, 2, bytes([0xFF]) * 4)
        self.assertEqual(img.convert("L").getpixel((3, 1)), 255)

    def test_pencil_is_black(self):
        # primo punto di ogni riga a 0 = segno scuro
        img = app.image_from("lineart", 8, 1, bytes([0x7F]))
        self.assertEqual(img.convert("L").getpixel((0, 0)), 0)
        self.assertEqual(img.convert("L").getpixel((1, 0)), 255)


class SaveOptionsTest(unittest.TestCase):
    """Compressione dei file salvati: scelta per JPEG e PDF, 1 bit nei PDF in bianco e nero."""

    @staticmethod
    def page(mode="RGB"):
        # pagina con un po' di rumore, come una scansione di carta stampata
        import random
        from PIL import Image
        rnd = random.Random(3)
        img = Image.new("RGB", (400, 560), (240, 236, 228))
        px = img.load()
        for y in range(0, 560, 2):
            for x in range(0, 400, 2):
                v = rnd.randint(-18, 18)
                px[x, y] = (200 + v, 120 + v, 90 + v) if 80 < y < 300 else (235 + v // 3,) * 3
        return img.convert(mode)

    def size(self, img, fmt, quality, **kw):
        import io
        b = io.BytesIO()
        img.save(b, "JPEG" if fmt == "jpg" else "PDF", **app.encoder_options(fmt, img.mode, quality), **kw)
        return b.getvalue()

    def test_options(self):
        self.assertEqual(app.encoder_options("jpg", "RGB", "max"), {"quality": 95, "subsampling": 0})
        self.assertEqual(app.encoder_options("pdf", "L", "compact"), {"quality": 65, "subsampling": 2})
        self.assertEqual(app.encoder_options("pdf", "1", "compact"), {})     # 1 bit: niente qualità JPEG
        self.assertEqual(app.encoder_options("png", "RGB", "compact"), {})
        self.assertEqual(app.encoder_options("tif", "RGB", "max"), {})
        self.assertEqual(app.encoder_options("jpg", "RGB", "boh"), {"quality": 95, "subsampling": 0})

    def test_compact_is_smaller(self):
        img = self.page()
        for fmt in ("jpg", "pdf"):
            big, mid, small = (len(self.size(img, fmt, q)) for q in ("max", "balanced", "compact"))
            self.assertGreater(big, mid, fmt)
            self.assertGreater(mid, small, fmt)
            self.assertLess(small, big / 2, fmt)

    def test_lineart_pdf_uses_fax_compression(self):
        data = self.size(self.page("L").point(lambda v: 255 if v > 160 else 0).convert("1"), "pdf", "max")
        self.assertIn(b"CCITTFaxDecode", data)

    def test_profiles_are_consistent(self):
        formats = {v for _, v in app.FORMATS}
        for key, name, cfg in app.PROFILES:
            self.assertIn(cfg["format"], formats, key)
            self.assertIn(cfg["quality"], app.QUALITY, key)
            self.assertIn(cfg["mode"], {v for _, v in app.MODES}, key)
        self.assertEqual([k for k, _, _ in app.PROFILES], ["document", "medium", "art"])


if __name__ == "__main__":
    unittest.main()
