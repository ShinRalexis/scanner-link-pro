# Scanner Link Pro: SCSI/USB to Scanner
# Copyright (C) 2026 ShinRalexis
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test del motore dentro Linux: i motori rimasti da avvii precedenti vengono fermati.

Da eseguire nella distribuzione WSL (serve /proc e pyusb):
    python3 -m unittest discover -s tests -p "test_engine.py"
"""

import os
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


@unittest.skipUnless(os.path.isdir("/proc/self"), "serve Linux")
class StaleEngineTest(unittest.TestCase):
    def test_orphans_are_stopped(self):
        from gt10000 import backend
        # due finti motori: il loro comando finisce con gt10000/backend.py come quello vero
        fakes = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "/opt/x/gt10000/backend.py"])
                 for _ in range(2)]
        time.sleep(0.3)
        try:
            self.assertEqual(backend.stop_other_engines(timeout_s=3), 2)
            for p in fakes:
                self.assertIsNotNone(p.wait(5))
        finally:
            for p in fakes:
                if p.poll() is None:
                    p.kill()

    def test_sigterm_exits_cleanly(self):
        # il motore vero, senza scanner aperto: SIGTERM deve farlo uscire da solo, in ordine e in fretta
        import json
        import signal
        engine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gt10000", "backend.py")
        env = dict(os.environ, GT10000_KEEP_OTHERS="1")
        p = subprocess.Popen([sys.executable, "-u", engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, env=env)
        try:
            self.assertEqual(json.loads(p.stdout.readline())["type"], "hello")
            p.send_signal(signal.SIGTERM)
            self.assertEqual(p.wait(3), 0)
        finally:
            if p.poll() is None:
                p.kill()

    def test_nothing_to_stop(self):
        from gt10000 import backend
        self.assertEqual(backend.stop_other_engines(timeout_s=1), 0)


if __name__ == "__main__":
    unittest.main()
