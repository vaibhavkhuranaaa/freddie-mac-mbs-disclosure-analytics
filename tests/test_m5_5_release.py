import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m5_5_release  # noqa: E402


class M55ReleaseTests(unittest.TestCase):
    def test_hard_link_clone_keeps_previous_m5_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            active = root / "active"
            bundle = root / "bundle"
            active.mkdir()
            (active / "m5.sqlite").write_bytes(b"old")
            m5_5_release.clone_active_bundle(active, bundle)
            self.assertEqual(
                os.stat(active / "m5.sqlite").st_ino,
                os.stat(bundle / "m5.sqlite").st_ino,
            )
            replacement = bundle / "m5.sqlite.building"
            replacement.write_bytes(b"new")
            replacement.replace(bundle / "m5.sqlite")
            self.assertEqual((active / "m5.sqlite").read_bytes(), b"old")
            self.assertEqual((bundle / "m5.sqlite").read_bytes(), b"new")


if __name__ == "__main__":
    unittest.main()
