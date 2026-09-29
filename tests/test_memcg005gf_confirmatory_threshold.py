from __future__ import annotations
import json,unittest
from pathlib import Path
from finite_ram_lab.memcg005gf_confirmatory_threshold import analyze,capacity_for
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005G-F-CONFIRMATORY-THRESHOLD-LOCALIZATION-v1.json").read_text())
def row(b,i,fail=False):
    c=capacity_for(SPEC,b,i)
    return {"block":b,"identity":i,"capacity_pages":c,"stratum":"LOW","valid":True,
      "cpu_match":True,"q64_pass":not fail,"first_touch_delta_pages":0.0 if fail else 64.0}
class T(unittest.TestCase):
    def test_balance(self):
        for b in range(48):
            xs=[capacity_for(SPEC,b,i) for i in range(60)]
            for c in SPEC["capacities"]:self.assertEqual(xs.count(c),10)
    def test_localizes_t11(self):
        rows=[];seen={}
        for b in range(48):
            for i in range(60):
                c=capacity_for(SPEC,b,i);k=(b,c);seen[k]=seen.get(k,0)+1
                fail=(c>=11 and seen[k]<=1)
                rows.append(row(b,i,fail))
        r=analyze(SPEC,rows)
        self.assertEqual(r["threshold"]["map_T"],11)
        self.assertEqual(r["decision"],"SUPPORT_LOCALIZED_T")
if __name__=="__main__":unittest.main()
