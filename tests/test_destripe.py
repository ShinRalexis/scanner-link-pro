# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test della correzione righe su dati sintetici (lato Windows, serve numpy).

    python -m unittest discover -s tests -p "test_destripe.py"
"""

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import destripe  # noqa: E402

W, H = 2400, 850                 # 101 mm di vetro a 600 dpi, 431 mm a 50 dpi
STREAK = slice(1200, 1240)       # riga larga 1,7 mm


def attenuation(y_mm):
    """Riga come quella misurata: dal 2% in alto al 20% in fondo al vetro."""
    return 1 - (0.02 + 0.18 * y_mm / 431.8)


def lid(seed=1, speck=False, document=False, level=230.0):
    rng = np.random.default_rng(seed)
    img = level + rng.normal(0, 1.0, (H, W, 3))
    y_mm = (np.arange(H) + 0.5) / destripe.CAL_DPI_Y * 25.4
    img[:, STREAK, 0] *= attenuation(y_mm)[:, None]
    img[:, STREAK, 1] *= (1 + attenuation(y_mm)[:, None]) / 2
    if speck:                    # granello sul coperchio: una sola fascia
        img[100:120, 1800:1810, :] *= 0.7
    if document:
        img[0:400, 300:1500, :] = 90
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def calibrate(**kw):
    img = lid(**kw)
    return destripe.Calibration.from_scans({"color": (img.tobytes(), W, H)})


def encode_std(lin):
    return np.interp(lin, destripe.STD_TO_LIN, destripe.LEVELS)


class DestripeTest(unittest.TestCase):
    def setUp(self):
        # dati sintetici senza lo scarto d'origine del vero scanner (provato a parte)
        self._offsets = dict(destripe.X_OFFSET), destripe.X_OFFSET_PREVIEW
        destripe.X_OFFSET = {k: 0.0 for k in destripe.X_OFFSET}
        destripe.X_OFFSET_PREVIEW = 0.0

    def tearDown(self):
        destripe.X_OFFSET, destripe.X_OFFSET_PREVIEW = self._offsets

    def test_origin_offset_moves_the_streak(self):
        cal, _ = calibrate()

        def centre():
            active, mean = cal.column_factors("color", 300, 0, 1200)
            loss = np.clip(1 - mean[10, :, 0], 0, None)
            return float((active * loss).sum() / loss.sum())

        base = centre()
        destripe.X_OFFSET[300] = 6.0                   # 6 colonne a 600 dpi = 3 punti a 300 dpi
        self.assertAlmostEqual(centre() - base, 3.0, delta=0.05)
        # al bordo sinistro l'impronta esce dal vetro calibrato: lì la sensibilità vale 1, non 0
        _, mean = cal.column_factors("color", 300, 0, 50)
        self.assertTrue(mean.size == 0 or mean.min() > 0.5)

    def test_streak_found_speck_ignored(self):
        cal, info = calibrate(speck=True)
        cols = cal.parts["color"][0]
        self.assertTrue(set(range(1200, 1240)) <= set(cols.tolist()))
        self.assertFalse(np.any((cols >= 1795) & (cols < 1815)), "il granello locale non è una riga")
        self.assertEqual(info["color"], 1)
        self.assertEqual(cal.visible_streaks("color"), 1)

    def test_correction_standard_curve(self):
        cal, _ = calibrate()
        rng = np.random.default_rng(7)
        top = 4000                                     # area da 339 mm in giù, a 300 dpi
        h, w, dpi, left = 300, 400, 300, 450           # colonne 450-849 a 300 dpi = 900-1699 a 600
        lin = rng.uniform(5, 200, (h, w, 3))
        y_mm = (top + np.arange(h) + 0.5) / dpi * 25.4
        seen = lin.copy()
        cols300 = slice(600 - left, 620 - left)        # la riga a 300 dpi: colonne 600-619
        seen[:, cols300, 0] *= attenuation(y_mm)[:, None]
        seen[:, cols300, 1] *= (1 + attenuation(y_mm)[:, None]) / 2
        img = np.rint(encode_std(seen)).astype(np.uint8)
        truth = encode_std(lin)
        before = np.abs(img[:, cols300].astype(float) - truth[:, cols300]).max()
        n = destripe.correct(img, cal, "color", dpi=dpi, dpi_y=dpi, left=left, top=top, gamma=None)
        after = np.abs(img[:, cols300].astype(float) - truth[:, cols300]).max()
        self.assertGreater(n, 0)
        self.assertGreater(before, 15)
        self.assertLess(after, 4.0)
        # fuori dalla riga non cambia nulla
        np.testing.assert_array_equal(img[:, :100], np.rint(encode_std(seen[:, :100])).astype(np.uint8))

    def test_correction_user_gamma_and_white(self):
        cal, _ = calibrate()
        g = 2.4
        lin = np.full((50, W, 3), 120.0)
        y_mm = (9000 + np.arange(50) + 0.5) / 600 * 25.4
        lin[:, STREAK, 0] *= attenuation(y_mm)[:, None]
        img = np.rint(255 * (lin / 255) ** (1 / g)).astype(np.uint8)
        img[:, 1210, :] = 255                          # punto bianco saturo sulla riga
        destripe.correct(img, cal, "color", dpi=600, dpi_y=600, left=0, top=9000, gamma=g)
        expected = 255 * (120 / 255) ** (1 / g)
        core = img[:, 1200:1240, 0].astype(float)
        core = np.delete(core, 10, axis=1)
        self.assertLess(np.abs(core - expected).max(), 2.5)
        self.assertTrue(np.all(img[:, 1210, :] == 255), "un punto a 255 resta a 255")

    def test_save_and_load(self):
        cal, _ = calibrate()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cal.npz")
            cal.save(path)
            back = destripe.Calibration.load(path)
        self.assertEqual(back.date, cal.date)
        self.assertEqual(back.width, W)
        np.testing.assert_array_equal(back.parts["color"][0], cal.parts["color"][0])
        np.testing.assert_allclose(back.parts["color"][1], cal.parts["color"][1])

    def test_file_in_place(self):
        cal, _ = calibrate()
        img = np.full((40, 200, 3), 200, np.uint8)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "scan.raw")
            img.tofile(path)
            n = destripe.correct_file(path, cal, "color", 200, 40, dpi=600, dpi_y=600, left=1150, top=0, gamma=2.2)
            out = np.fromfile(path, np.uint8).reshape(40, 200, 3)
        self.assertGreater(n, 0)
        self.assertTrue(np.all(out[:, 60:80, 0] > 200), "la riga si schiarisce")
        np.testing.assert_array_equal(out[:, :40], img[:, :40])

    def test_not_empty_glass(self):
        img = lid(document=True)
        with self.assertRaises(destripe.CalibrationError) as ctx:
            destripe.analyze(img.tobytes(), W, H, 3)
        self.assertEqual(ctx.exception.key, "calib_err_not_empty")

    def test_full_width_sheet_is_not_empty(self):
        img = lid()
        img[200:500] = 70                               # foglio scuro largo quanto il vetro
        with self.assertRaises(destripe.CalibrationError) as ctx:
            destripe.analyze(img.tobytes(), W, H, 3)
        self.assertEqual(ctx.exception.key, "calib_err_not_empty")

    def test_lamp_warming_is_not_an_object(self):
        # prime righe più scure in modo uniforme (lampada ancora in assestamento): non è "qualcosa sul vetro"
        img = lid().astype(np.float32)
        ramp = np.linspace(0.7, 1.0, 60)
        img[:60] *= ramp[:, None, None]
        cols, _, groups = destripe.analyze(np.clip(img, 0, 255).astype(np.uint8).tobytes(), W, H, 3)
        self.assertTrue(set(range(1200, 1240)) <= set(cols.tolist()))
        self.assertEqual(groups, 1)

    def test_dark_lid(self):
        img = lid(level=60)
        with self.assertRaises(destripe.CalibrationError) as ctx:
            destripe.analyze(img.tobytes(), W, H, 3)
        self.assertEqual(ctx.exception.key, "calib_err_dark")

    def test_standard_curve_is_increasing(self):
        self.assertEqual(len(destripe.STD_TO_LIN), 256)
        self.assertTrue(np.all(np.diff(destripe.STD_TO_LIN) > 0))


if __name__ == "__main__":
    unittest.main()
