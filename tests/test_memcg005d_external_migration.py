from __future__ import annotations
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from finite_ram_lab.memcg005d_external_migration import analyze_trials

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005D-EXTERNAL-MIGRATION-FIRST-TOUCH-v1.json").read_text())

def mk(block,arm,i,ok,valid=True):
    return {"block":block,"arm":arm,"identity":i,"valid":valid,"cpu_match":valid,
            "q64_pass":ok,"delta_pages":64.0 if ok else 0.0,
            "migration_delta_pages":0.0 if arm=="external_atomic" else None}

def matrix(ext_fail=1,self_fail=12):
    out=[]
    for b in range(4):
        for arm,fail in [("external_atomic",ext_fail),("self_atomic",self_fail)]:
            for i in range(23):
                g=b*23+i
                out.append(mk(b,arm,i,g<92-fail))
    return out

class T(unittest.TestCase):
    def test_support(self):
        r=analyze_trials(SPEC,matrix(ext_fail=1,self_fail=12))
        self.assertEqual(r["decision"],"SUPPORT_EXTERNAL_PATH")
        self.assertGreaterEqual(r["perfect_external_blocks"],3)
    def test_reject(self):
        r=analyze_trials(SPEC,matrix(ext_fail=8,self_fail=8))
        self.assertEqual(r["decision"],"REJECT_EXTERNAL_PATH")
    def test_invalid_cpu_blocks_support(self):
        rows=matrix(ext_fail=1,self_fail=12)
        rows[0]["valid"]=False
        rows[0]["cpu_match"]=False
        r=analyze_trials(SPEC,rows)
        self.assertNotEqual(r["decision"],"SUPPORT_EXTERNAL_PATH")
    def test_worker_compiles(self):
        gcc=shutil.which("gcc")
        if not gcc:self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"w"
            subprocess.run([gcc,"-O2","-Wall","-Wextra","-std=c11",
                str(ROOT/"experiments/memcg005d_worker.c"),"-o",str(out)],check=True)
            self.assertTrue(out.exists())

if __name__=="__main__": unittest.main()
