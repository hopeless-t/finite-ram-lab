from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from finite_ram_lab.fast_reinstall_epoch import make_epoch, verify_epoch, verify_full

class EpochTests(unittest.TestCase):
    def test_epoch_changes_on_content_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.whl'; p.write_bytes(b'abcdef')
            e=make_epoch(p)
            self.assertTrue(verify_epoch(p,e)); self.assertTrue(verify_full(p,e))
            p.write_bytes(b'abcdeg')
            self.assertFalse(verify_epoch(p,e)); self.assertFalse(verify_full(p,e))

if __name__ == '__main__': unittest.main()
