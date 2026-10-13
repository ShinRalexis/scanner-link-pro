# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Trasporto SCSI su USB per l'adattatore Logitec LUB-SC / LUB-MSC (VID 0789, PID 00C0).

L'adattatore non segue lo standard USB Mass Storage (classe FF, protocollo proprietario
del bus driver Logitec "NINJAUSB"). Il protocollo qui sotto è ricavato dal driver
originale LUBSC2K.SYS 1.33.06 (Windows 2000/XP):

  selezione bersaglio  vendor OUT  (0x40) bRequest 5, wValue = (ID << 8) | 7, nessun dato
  fase comando         class OUT   (0x21) bRequest 0, wValue 0, wIndex 0, CDB lungo 12 byte
  fase dati            bulk OUT 0x01 oppure bulk IN 0x81 (pacchetti corti ammessi)
  fase stato           vendor IN   (0xC0) bRequest 0, 8 byte:
                         [0] 1 o 4 = comando concluso, altro = ancora in corso (ripetere)
                         [1] errore adattatore (0 = nessuno, 0x11 = nessun dispositivo)
                         [2] stato SCSI (0 = GOOD, 2 = CHECK CONDITION)

La selezione resta valida finché non si cambia ID, come fa il driver originale.
"""

import time

import usb.core
import usb.util

from .messages import KeyedError

VID = 0x0789
PIDS = (0x00C0, 0x0004)
HOST_ID = 7

EP_OUT = 0x01
EP_IN = 0x81

STATUS_GOOD = 0x00
STATUS_CHECK_CONDITION = 0x02
STATUS_BUSY = 0x08


class ScsiError(KeyedError):
    def __init__(self, key, status=None, sense_data=None, **args):
        super().__init__(key, **args)
        self.status = status
        self.sense = sense_data


class AdapterNotFound(KeyedError):
    pass


class LubscAdapter:
    def __init__(self, dev=None, timeout_ms=10000):
        if dev is None:
            dev = find_adapter()
        if dev is None:
            raise AdapterNotFound("b_adapter_not_found")
        self.dev = dev
        self.timeout_ms = timeout_ms
        self._selected = None
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except (NotImplementedError, usb.core.USBError):
            pass
        try:
            dev.set_configuration()
        except usb.core.USBError:
            # già configurato (capita su Windows con WinUSB)
            pass
        usb.util.claim_interface(dev, 0)
        self._clear_halts()

    def close(self):
        try:
            usb.util.release_interface(self.dev, 0)
        finally:
            usb.util.dispose_resources(self.dev)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _clear_halts(self):
        for ep in (EP_OUT, EP_IN):
            try:
                self.dev.clear_halt(ep)
            except usb.core.USBError:
                pass

    def select(self, target):
        self.dev.ctrl_transfer(0x40, 5, (target << 8) | HOST_ID, 0, None, timeout=self.timeout_ms)
        self._selected = target

    def _status(self, timeout_s):
        deadline = time.monotonic() + timeout_s
        while True:
            st = bytes(self.dev.ctrl_transfer(0xC0, 0, 0, 0, 8, timeout=self.timeout_ms))
            # A volte l'adattatore risponde con 7 byte invece di 8 e tutti i campi slittano di
            # una posizione: una risposta corta non vale, si rilegge come fa LUBSC2K.SYS (0x13464).
            if len(st) == 8 and st[0] in (1, 4):
                return st
            if time.monotonic() > deadline:
                raise ScsiError("b_status_timeout", st=st.hex())
            time.sleep(0.005)

    def command(self, target, cdb, data_out=None, data_in_len=0, timeout_s=30.0, check=True):
        """Esegue un comando SCSI. Ritorna i byte letti (fase dati IN) oppure b''."""
        if len(cdb) > 12:
            raise ValueError("CDB più lungo di 12 byte")
        cdb = bytes(cdb) + bytes(12 - len(cdb))
        if self._selected != target:
            self.select(target)
        tmo = int(timeout_s * 1000)
        try:
            self.dev.ctrl_transfer(0x21, 0, 0, 0, cdb, timeout=tmo)
        except usb.core.USBError as e:
            # L'adattatore va in stallo sulla fase comando quando il bersaglio non risponde
            # alla selezione o chiude subito con CHECK CONDITION: lo stato dice quale dei due.
            st = self._status_after_stall()
            if st is None or st[1] == 0x11:
                self._selected = None
                raise ScsiError("b_no_answer", status=st, id=target, cmd="%02X" % cdb[0], err=e) from e
            if st[2] == STATUS_CHECK_CONDITION and check:
                sense = self.request_sense(target)
                raise ScsiError("b_check_condition", status=st, sense_data=sense, cmd="%02X" % cdb[0],
                                sense=sense.hex()) from e
            raise ScsiError("b_cmd_rejected", status=st, cmd="%02X" % cdb[0], st=st.hex()) from e
        try:
            data = b""
            if data_out:
                self.dev.write(EP_OUT, data_out, timeout=tmo)
            elif data_in_len:
                data = self._read_in(data_in_len, tmo)
            st = self._status(timeout_s)
        except usb.core.USBError as e:
            self._clear_halts()
            self._selected = None
            raise ScsiError("b_usb_error", cmd="%02X" % cdb[0], err=e) from e
        if st[1] == 0x11:
            raise ScsiError("b_no_device", status=st, id=target)
        if st[1] != 0:
            raise ScsiError("b_adapter_error", status=st, code="%02X" % st[1], cmd="%02X" % cdb[0], st=st.hex())
        if check and st[2] == STATUS_CHECK_CONDITION:
            sense = self.request_sense(target)
            raise ScsiError("b_check_condition", status=st, sense_data=sense, cmd="%02X" % cdb[0],
                            sense=sense.hex())
        if check and st[2] not in (STATUS_GOOD,):
            raise ScsiError("b_scsi_status", status=st, code="%02X" % st[2], cmd="%02X" % cdb[0], st=st.hex())
        return data

    def _status_after_stall(self):
        # subito dopo uno stallo anche la prima lettura di stato può fallire
        for _ in range(5):
            try:
                st = bytes(self.dev.ctrl_transfer(0xC0, 0, 0, 0, 8, timeout=self.timeout_ms))
                if len(st) == 8:
                    return st
            except usb.core.USBError:
                time.sleep(0.01)
        return None

    def clear_unit_attention(self, target, attempts=4):
        """Consuma le UNIT ATTENTION (accensione, reset del bus) finché il bersaglio è pronto."""
        for _ in range(attempts):
            sense = self.request_sense(target)
            if len(sense) < 3 or sense[2] & 0x0F == 0:
                return
        self.test_unit_ready(target)

    def _read_in(self, length, tmo):
        out = bytearray()
        chunk = 0x10000
        while len(out) < length:
            want = min(chunk, length - len(out))
            got = bytes(self.dev.read(EP_IN, want, timeout=tmo))
            out += got
            if len(got) < want:
                break
        return bytes(out)

    # comandi SCSI generici

    def inquiry(self, target, length=36, timeout_s=5.0):
        # risponde in pochi millisecondi: un'attesa breve tiene corta la ricerca sul bus anche quando
        # l'adattatore non risponde (prima: 30 s per ognuno dei 7 ID)
        return self.command(target, bytes([0x12, 0, 0, 0, length, 0]), data_in_len=length, timeout_s=timeout_s)

    def request_sense(self, target, length=18):
        return self.command(target, bytes([0x03, 0, 0, 0, length, 0]), data_in_len=length, check=False)

    def test_unit_ready(self, target):
        self.command(target, bytes(6))

    def scan_bus(self):
        """Ritorna [(id, inquiry)] dei dispositivi presenti sul bus SCSI."""
        found = []
        for target in range(8):
            if target == HOST_ID:
                continue
            try:
                found.append((target, self.inquiry(target)))
            except ScsiError:
                continue
        return found


def find_adapter():
    for pid in PIDS:
        dev = usb.core.find(idVendor=VID, idProduct=pid)
        if dev is not None:
            return dev
    return None


def describe_inquiry(data):
    vendor = data[8:16].decode("ascii", "replace").strip()
    product = data[16:32].decode("ascii", "replace").strip()
    rev = data[32:36].decode("ascii", "replace").strip()
    return vendor, product, rev
