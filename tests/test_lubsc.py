# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test del trasporto Logitec con un adattatore finto (nessun hardware necessario).

Si lancia dentro il Linux interno:
    wsl -d GT10000 -- python3 -m unittest discover -s "/mnt/d/Scanner Epson GT-10000+/tests"
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gt10000 import lubsc  # noqa: E402


class FakeDev:
    """Risponde alle letture di stato (vendor IN 0) con la sequenza data."""

    def __init__(self, statuses, data_in=b""):
        self.statuses = [bytes.fromhex(s) for s in statuses]
        self.data_in = data_in

    def is_kernel_driver_active(self, interface):
        return False

    def set_configuration(self):
        pass

    def clear_halt(self, ep):
        pass

    def ctrl_transfer(self, bm, request, value, index, data=None, timeout=None):
        if bm == 0xC0 and request == 0:
            return bytearray(self.statuses.pop(0))
        return len(data) if data else 0

    def write(self, ep, data, timeout=None):
        return len(data)

    def read(self, ep, length, timeout=None):
        return bytearray(self.data_in[:length])


def adapter(dev):
    with mock.patch.object(lubsc.usb.util, "claim_interface"):
        return lubsc.LubscAdapter(dev)


class StatusTest(unittest.TestCase):
    def test_short_status_is_read_again(self):
        # 7 byte al posto di 8: i campi slittano e il flag 0x10 finiva al posto dello stato SCSI
        dev = FakeDev(["01001000000001", "0100001000000001"])
        adapter(dev).command(2, bytes([0x0A, 0, 0, 0, 1, 0]), data_out=b"\x06")
        self.assertEqual(dev.statuses, [])

    def test_status_in_progress_is_polled(self):
        dev = FakeDev(["0000000000000000", "0100000000000024"], data_in=bytes(36))
        data = adapter(dev).command(2, bytes([0x12, 0, 0, 0, 36, 0]), data_in_len=36)
        self.assertEqual(len(data), 36)

    def test_check_condition_is_reported(self):
        # stato CHECK CONDITION, poi REQUEST SENSE con sense key 5
        dev = FakeDev(["0100020000000000", "0100000000000008"], data_in=bytes.fromhex("f000050000000000"))
        with self.assertRaises(lubsc.ScsiError) as ctx:
            adapter(dev).command(2, bytes([0x08, 0, 0, 0, 1, 0]), data_in_len=1)
        self.assertEqual(ctx.exception.sense[2], 5)

    def test_no_device(self):
        dev = FakeDev(["0111000000000000"])
        with self.assertRaises(lubsc.ScsiError):
            adapter(dev).command(3, bytes(6))


if __name__ == "__main__":
    unittest.main()
