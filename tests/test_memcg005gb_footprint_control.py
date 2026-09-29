from __future__ import annotations
import json,unittest
from pathlib import Path
from finite_ram_lab.memcg005gb_footprint_control import analyze,_arm
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005G-B-BIOPSY-FOOTPRINT-CONTROL-v1.json").read_text())
def row(b,i,fail=False):
    return {"block":b,"identity":i,"arm":_arm(b,i),"stratum":"LOW","valid":True,"cpu_match":True,
      "q64_pass":not fail,"first_touch_delta_pages":0.0 if fail else 64.0,
      "pre_current_pages":99.0,"affinity_to_go_us":100.0}
class T(unittest.TestCase):
    def test_balanced_arm_assignment(self):
        for b in range(16):
            arms=[_arm(b,i) for i in range(64)]
            self.assertEqual(arms.count("CAP8"),32);self.assertEqual(arms.count("CAP70"),32)
    def test_support_effect(self):
        rows=[]
        for b in range(16):
            for i in range(64):
                a=_arm(b,i)
                fail=(a=="CAP70" and i%8==((b+1)%8))
                rows.append(row(b,i,fail))
        r=analyze(SPEC,rows)
        self.assertEqual(r["decision"],"SUPPORT_FOOTPRINT_EFFECT")
    def test_reject_no_effect(self):
        rows=[row(b,i,False) for b in range(16) for i in range(64)]
        r=analyze(SPEC,rows)
        self.assertEqual(r["decision"],"REJECT_FOOTPRINT_EFFECT")
if __name__=="__main__":unittest.main()
