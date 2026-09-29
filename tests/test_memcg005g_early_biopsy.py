from __future__ import annotations
import json,unittest
from pathlib import Path
from finite_ram_lab.memcg005g_early_biopsy import analyze
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005G-A-EARLY-TRANSIENT-BIOPSY-v1.json").read_text())
def row(b,i,low=True,fail=False):
    return {"block":b,"identity":i,"phase":"EARLY" if i<=7 else "STEADY","stratum":"LOW" if low else "HIGH",
      "valid":True,"cpu_match":True,"q64_pass":not fail,"first_touch_delta_pages":0.0 if fail else 64.0,
      "residual_depth_candidate":3 if fail else None,"biopsy_censored_gt64":False}
class T(unittest.TestCase):
    def test_support(self):
        rows=[]
        for b in range(24):
            for i in range(32):
                fail=(i<=7 and b%4==0)
                rows.append(row(b,i,True,fail))
        r=analyze(SPEC,rows);self.assertEqual(r["decision"],"SUPPORT_EARLY_TRANSIENT")
    def test_reject_flat(self):
        rows=[row(b,i,True,False) for b in range(24) for i in range(32)]
        r=analyze(SPEC,rows);self.assertEqual(r["decision"],"REJECT_EARLY_TRANSIENT")
if __name__=="__main__":unittest.main()
