# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test della matrice colore (ESC m) e delle curve gamma (ESC z). Non serve hardware.

    python -m unittest discover -s tests -p "test_color.py"
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gt10000 import color  # noqa: E402


class ColorTest(unittest.TestCase):
    def test_rows_sum_to_32(self):
        # lo scanner vuole coefficienti in trentaduesimi con righe che sommano a 1,0
        rnd = color.round_cct(color.GT10000_CCT)
        self.assertEqual([sum(rnd[i * 3:i * 3 + 3]) for i in range(3)], [32, 32, 32])

    def test_identity_encoding(self):
        self.assertEqual(color.color_coefficients(color.IDENTITY_CCT).hex(), "200000002000000020")

    def test_gt10000_profile_bytes(self):
        # valori calcolati come SANE (profilo 0x05 ES-6000H); il bit alto è il segno
        self.assertEqual(color.color_coefficients().hex(), "298292842502858330")

    def test_gamma_tables(self):
        self.assertEqual(color.gamma_table(1.0), bytes(range(256)))
        table = color.gamma_table(2.2)
        self.assertEqual((table[0], table[255]), (0, 255))
        self.assertTrue(all(a <= b for a, b in zip(table, table[1:])))
        self.assertGreater(table[128], 128)   # gamma sopra 1: toni medi più chiari


if __name__ == "__main__":
    unittest.main()
