from __future__ import annotations
import json,unittest
from pathlib import Path
from finite_ram_lab.memcg005gd_dose_response import analyze,capacity_for
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005G-D-FOOTPRINT-DOSE-RESPONSE-v1.json").read_text())
def row(b,i,fail=False):
    c=capacity_for(SPEC,b,i)
    return {"block":b,"identity":i,"capacity_pages":c,"stratum":"LOW","valid":True,"cpu_match":True,
      "q64_pass":not fail,"first_touch_delta_pages":0.0 if fail else 64.0,
      "pre_current_pages":99.0,"affinity_to_go_us":150.0}
class T(unittest.TestCase):
    def test_balance(self):
        for b in range(16):
            xs=[capacity_for(SPEC,b,i) for i in range(72)]
            for c in SPEC["capacities"]: self.assertEqual(xs.count(c),12)
    def test_flat(self):
        rows=[row(b,i,False) for b in range(16) for i in range(72)]
        r=analyze(SPEC,rows)
        self.assertEqual(r["discovery_label"],"FLAT_OR_UNRESOLVED")
    def test_step_candidate(self):
        rows=[]
        for b in range(16):
            seen={c:0 for c in SPEC["capacities"]}
            for i in range(72):
                c=capacity_for(SPEC,b,i);j=seen[c];seen[c]+=1
                fail=(c>=64 and j<3)
                rows.append(row(b,i,fail))
        r=analyze(SPEC,rows)
        self.assertIn(r["discovery_label"],{"DISCOVERY_STEP64_CANDIDATE","DISCOVERY_OTHER_SHAPE"})
if __name__=="__main__":unittest.main()
