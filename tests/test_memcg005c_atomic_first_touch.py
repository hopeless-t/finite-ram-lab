from __future__ import annotations
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path
from finite_ram_lab.memcg005c_atomic_first_touch import analyze_trials

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005C-ATOMIC-FIRST-TOUCH-v1.json").read_text())

def mk(block,arm,i,ok):
    return {"block":block,"arm":arm,"identity":i,"q64_pass":ok,
            "delta_pages":64.0 if ok else 0.0}

def matrix(atomic_fail=0,two_fail=8):
    out=[]
    for b in range(4):
        for arm,fail in [("atomic",atomic_fail),("two_step",two_fail)]:
            for i in range(23):
                # distribute failures deterministically across blocks/ids
                global_i=b*23+i
                out.append(mk(b,arm,i,global_i<92-fail))
    return out

class T(unittest.TestCase):
    def test_support(self):
        r=analyze_trials(SPEC,matrix(atomic_fail=1,two_fail=8))
        self.assertEqual(r["decision"],"SUPPORT_ATOMIC_PATH")
        self.assertGreaterEqual(r["perfect_atomic_blocks"],3)
    def test_reject(self):
        r=analyze_trials(SPEC,matrix(atomic_fail=8,two_fail=8))
        self.assertEqual(r["decision"],"REJECT_ATOMIC_PATH")
    def test_worker_compiles(self):
        gcc=shutil.which("gcc")
        if not gcc:self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"w"
            subprocess.run([gcc,"-O2","-Wall","-Wextra","-std=c11",
                str(ROOT/"experiments/memcg005c_worker.c"),"-o",str(out)],check=True)
            self.assertTrue(out.exists())

if __name__=="__main__": unittest.main()
