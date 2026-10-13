# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test del ponte verso Linux: adattatore nei due modelli, errori di virtualizzazione (lato Windows).

    python -m unittest discover -s tests -p "test_bridge.py"
"""

import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app"))
import bridge  # noqa: E402

HEADER = "Connected:\nBUSID  VID:PID    DEVICE                       STATE\n"


class AdapterTest(unittest.TestCase):
    def setUp(self):
        self._saved = bridge._run, bridge.usbipd_exe, bridge._adapter_id
        bridge.usbipd_exe = lambda: "usbipd.exe"

    def tearDown(self):
        bridge._run, bridge.usbipd_exe, bridge._adapter_id = self._saved

    def listing(self, rows):
        out = (HEADER + "\n".join(rows) + "\n").encode("utf-8")
        bridge._run = lambda args, timeout=60: types.SimpleNamespace(stdout=out, stderr=b"", returncode=0)

    def test_first_model(self):
        self.listing(["1-1    046d:c52b  USB Receiver                 Not shared",
                      "2-3    0789:00c0  USB-SCSI                     Attached"])
        self.assertEqual(bridge.adapter_state(), ("collegato", "2-3"))
        self.assertEqual(bridge._adapter_id, "0789:00c0")

    def test_second_model(self):
        # stessa scheda, identificativo 0004: prima del 1.0.1 risultava "assente"
        self.listing(["4-2    0789:0004  USB Mass Storage Device      Not shared"])
        self.assertEqual(bridge.adapter_state(), ("non condiviso", "4-2"))
        self.assertEqual(bridge._adapter_id, "0789:0004")

    def test_absent(self):
        self.listing(["1-1    046d:c52b  USB Receiver                 Not shared"])
        self.assertEqual(bridge.adapter_state(), ("assente", None))

    def test_virtualization_errors(self):
        self.assertTrue(bridge.virtualization_problem(
            "Error code: Wsl/Service/CreateInstance/CreateVm/HCS/0x80370102"))
        self.assertTrue(bridge.virtualization_problem("HCS_E_HYPERV_NOT_INSTALLED"))
        self.assertFalse(bridge.virtualization_problem("Importazione completata."))
        self.assertFalse(bridge.virtualization_problem(None))


if __name__ == "__main__":
    unittest.main()
