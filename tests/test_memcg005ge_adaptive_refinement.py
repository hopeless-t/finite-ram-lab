from __future__ import annotations
import json,unittest
from pathlib import Path
from finite_ram_lab.memcg005ge_adaptive_refinement import analyze,capacity_for
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005G-E-ADAPTIVE-CAPACITY-REFINEMENT-v1.json").read_text())
def row(b,i,fail=False):
    c=capacity_for(SPEC,b,i)
    return {"block":b,"identity":i,"capacity_pages":c,"stratum":"LOW","valid":True,
      "cpu_match":True,"q64_pass":not fail,"first_touch_delta_pages":0.0 if fail else 64.0}
class T(unittest.TestCase):
    def test_balance(self):
        for b in range(16):
            xs=[capacity_for(SPEC,b,i) for i in range(80)]
            for c in SPEC["capacities"]:self.assertEqual(xs.count(c),10)
    def test_step_shape(self):
        rows=[]
        seen={}
        for b in range(16):
            for i in range(80):
                c=capacity_for(SPEC,b,i);key=(b,c);seen[key]=seen.get(key,0)+1
                fail=(c>=19 and seen[key]<=2)
                rows.append(row(b,i,fail))
        r=analyze(SPEC,rows)
        self.assertIn(r["discovery_label"],{"DISCOVERY_HARD_STEP","DISCOVERY_SMOOTH","UNRESOLVED_TRANSITION"})
        self.assertTrue(9<=r["threshold_posterior"]["median"]<=32)
if __name__=="__main__":unittest.main()
