# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test del catalogo delle traduzioni (lato Windows).

    python -m unittest discover -s tests -p "test_i18n.py"
"""

import os
import re
import string
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import i18n  # noqa: E402


def fields(template):
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


class CatalogTest(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("it")

    def test_every_key_has_all_languages(self):
        for key, entry in i18n.STRINGS.items():
            self.assertEqual(len(entry), len(i18n.CODES), key)
            for code, text in zip(i18n.CODES, entry):
                self.assertTrue(text.strip(), "%s vuoto in %s" % (key, code))

    def test_placeholders_match_italian(self):
        for key, entry in i18n.STRINGS.items():
            ref = fields(entry[0])
            for code, text in zip(i18n.CODES, entry):
                self.assertEqual(fields(text), ref, "%s in %s" % (key, code))

    def test_placeholders_do_not_clash_with_tr(self):
        # tr(key, **args): un segnaposto {key} darebbe "got multiple values for argument 'key'"
        import inspect
        reserved = set(inspect.signature(i18n.tr).parameters) - {"args", "kwargs"}
        for key, entry in i18n.STRINGS.items():
            self.assertFalse(fields(entry[0]) & reserved, key)

    def test_no_long_dashes(self):
        for key, entry in i18n.STRINGS.items():
            for text in entry:
                self.assertIsNone(re.search("[%s%s]" % (chr(0x2013), chr(0x2014)), text), key)

    def test_backend_messages_are_recognized(self):
        # testi come li producono backend.py, esci.py e lubsc.py
        samples = {
            "In attesa dell'adattatore USB-SCSI...": "b_wait_adapter",
            "Adattatore trovato, cerco lo scanner sul bus SCSI...": "b_adapter_found",
            "ID SCSI 2: EPSON SCANNER GT-10000": "b_scsi_device",
            "Nessuno scanner Epson trovato sul bus SCSI (scanner acceso? cavo collegato?)": "b_no_scanner",
            "Lo scanner rifiuta i parametri di ESC C (NAK)": "b_nak_params",
            "Lo scanner rifiuta ESC G (NAK)": "b_nak",
            "Risposta inattesa a i parametri di ESC d: 15": "b_unexpected_params",
            "Scansione color 50 dpi, 584x850 punti (1752 byte/riga)": "b_scan_start",
            "Riscaldamento lampada in corso...": "b_warming",
            "Stato SCSI 0x10 sul comando 08 (stato 0100100000000001)": "b_scsi_status",
            "CHECK CONDITION sul comando 0A, sense f000060000000000": "b_check_condition",
            "Nessuna risposta dall'ID 3 al comando 12 ([Errno 32] Pipe error)": "b_no_answer",
            "Errore adattatore 0x11 (comando 12, stato 0111000000000000)": "b_adapter_error",
        }
        for text, key in samples.items():
            msg = i18n.from_backend(text)
            self.assertEqual(msg.key, key, text)
            if key != "b_scan_start":
                self.assertEqual(str(msg), text)  # in italiano il messaggio resta identico
        # il codice interno della modalità diventa il nome tradotto
        self.assertEqual(str(i18n.from_backend("Scansione color 50 dpi, 584x850 punti (1752 byte/riga)")),
                         "Scansione Colore 50 dpi, 584x850 punti (1752 byte/riga)")

    def test_engine_templates_match_catalog(self):
        # il motore ha la sua copia dei testi italiani: deve restare identica al catalogo
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from gt10000 import messages
        self.assertEqual(set(messages.TEMPLATES), set(i18n.BACKEND_KEYS))
        for key, text in messages.TEMPLATES.items():
            self.assertEqual(text, i18n.STRINGS[key][0], key)

    def test_engine_payload_is_translated_by_key(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from gt10000 import messages
        data = messages.Note("b_scan_start", mode="gray", dpi=150, w=872, h=1240, bpl=872).payload()
        msg = i18n.Msg(data["key"], **data["args"])
        i18n.set_language("de")
        self.assertEqual(str(msg), "Scan Graustufen 150 dpi, 872x1240 Pixel (872 Byte/Zeile)")

    def test_unknown_backend_message_passes_through(self):
        msg = i18n.from_backend("ValueError: qualcosa di imprevisto")
        self.assertIsNone(msg.key)
        i18n.set_language("ja")
        self.assertEqual(str(msg), "ValueError: qualcosa di imprevisto")

    def test_translation_and_mode(self):
        msg = i18n.from_backend("Scansione gray 150 dpi, 872x1240 punti (872 byte/riga)")
        i18n.set_language("en")
        self.assertEqual(str(msg), "Scanning Grayscale 150 dpi, 872x1240 pixels (872 bytes/line)")
        i18n.set_language("de")
        self.assertEqual(i18n.size(25.5 * 1024 * 1024), "25,5 MB")
        i18n.set_language("fr")
        self.assertEqual(i18n.size(2048), "2,0 Ko")
        i18n.set_language("ja")
        self.assertEqual(i18n.duration(30), "30 秒")


if __name__ == "__main__":
    unittest.main()
