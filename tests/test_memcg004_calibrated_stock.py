from __future__ import annotations
import json, unittest
from pathlib import Path
from finite_ram_lab.memcg004_calibrated_stock import analyze_trials

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-004-CALIBRATED-STOCK-v1.json").read_text())

def trial(block,arm,r,cal=64.0,drop=0.0):
    validation=[{"touch":i,"delta_pages":64.0 if r==i else 0.0} for i in range(1,65)]
    return {"block":block,"arm":arm,"calibration_delta_pages":cal,
            "passive_drop_pages":[drop]*64 if arm!="no_hold" else [],
            "validation":validation}

def matrix(cal_r=64,control_r=17):
    out=[]
    for b in range(4):
        out += [trial(b,"calibrated",cal_r),trial(b,"no_hold",64),trial(b,"control_no_prime",control_r,cal=0.0)]
    return out

class Tests(unittest.TestCase):
    def test_support_r64(self):
        r=analyze_trials(SPEC,matrix())
        self.assertEqual(r["decision"],"SUPPORT_CALIBRATED_STOCK")
        self.assertEqual(r["support_blocks"],4)
        self.assertEqual(r["best_r_by_absolute_error"],64)
    def test_stable_alternative_rejects(self):
        r=analyze_trials(SPEC,matrix(41))
        self.assertEqual(r["decision"],"REJECT_CALIBRATED_STOCK")
        self.assertEqual(r["best_r_by_absolute_error"],41)
    def test_hold_drop_breaks_support(self):
        rows=matrix()
        for t in rows:
            if t["block"]<3 and t["arm"]=="calibrated": t["passive_drop_pages"][3]=16.0
        r=analyze_trials(SPEC,rows)
        self.assertEqual(r["decision"],"REJECT_CALIBRATED_STOCK")
    def test_unprimed_exact_phase_blocks_support(self):
        r=analyze_trials(SPEC,matrix(control_r=64))
        self.assertEqual(r["decision"],"INCONCLUSIVE")

if __name__=="__main__": unittest.main()
