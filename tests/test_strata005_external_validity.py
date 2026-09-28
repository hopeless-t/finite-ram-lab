from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from finite_ram_lab.strata005_external_validity import ARMS, load_spec, schedule_rows, write_schedule

SPEC={"memory_high_mib":[144,176],"arms":list(ARMS),"base_schedule_seed":2026092807}

class Strata005Tests(unittest.TestCase):
    def test_schedule_complete_deterministic(self):
        self.assertEqual(schedule_rows(SPEC,144,0),schedule_rows(SPEC,144,0))
        self.assertEqual({x["arm"] for x in schedule_rows(SPEC,144,0)},set(ARMS))
        self.assertEqual(len(schedule_rows(SPEC,144,0)),5)
    def test_pressure_changes_schedule_key(self):
        self.assertNotEqual(schedule_rows(SPEC,144,0),schedule_rows(SPEC,176,0))
    def test_rejects_unfrozen_pressure(self):
        with self.assertRaises(ValueError): schedule_rows(SPEC,160,0)
    def test_schedule_lf_only(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"s.csv"; write_schedule(SPEC,144,0,p); raw=p.read_bytes()
        self.assertNotIn(b"\r",raw); self.assertEqual(raw.count(b"\n"),6)

if __name__=="__main__": unittest.main()
