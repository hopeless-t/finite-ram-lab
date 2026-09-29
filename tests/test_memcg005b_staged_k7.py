from __future__ import annotations
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from finite_ram_lab.memcg005b_staged_k7 import analyze_trials
ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005B-THREE-CPU-STAGED-K7-v1.json").read_text())
def trial(b,m,state,valid=True):
    return {"block":b,"m":m,"valid_state":valid,"invalid_reason":None if valid else "x",
            "target_state":state if valid else "INVALID","insertions":[],"target_probe":{}}
def matrix(k=7):
    return [trial(b,int(m),"ABSENT" if int(m)>=k else "PRESENT") for b in range(4) for m in SPEC["tested_m"]]
class T(unittest.TestCase):
    def test_k7(self):
        r=analyze_trials(SPEC,matrix(7)); self.assertEqual(r["decision"],"SUPPORT_STAGED_K7"); self.assertEqual(r["best_k_by_errors"],[7])
    def test_k8_rejects(self):
        r=analyze_trials(SPEC,matrix(8)); self.assertEqual(r["decision"],"REJECT_STAGED_K7"); self.assertEqual(r["best_k_by_errors"],[8])
    def test_invalid_prevents_support(self):
        rows=matrix(7)
        for t in rows:
            if t["m"]==7 and t["block"] in {0,1}: t["valid_state"]=False; t["target_state"]="INVALID"; t["invalid_reason"]="x"
        r=analyze_trials(SPEC,rows); self.assertNotEqual(r["decision"],"SUPPORT_STAGED_K7")
    def test_worker_compiles(self):
        gcc=shutil.which("gcc")
        if not gcc:self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"w"; subprocess.run([gcc,"-O2","-Wall","-Wextra","-std=c11",str(ROOT/"experiments/memcg005b_worker.c"),"-o",str(out)],check=True)
            self.assertTrue(out.exists())
if __name__=="__main__":unittest.main()
