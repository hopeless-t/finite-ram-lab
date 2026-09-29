from __future__ import annotations
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path

from finite_ram_lab.memcg005e_baseline_stratified import analyze_trials

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005E-BASELINE-STRATIFIED-FIRST-TOUCH-v1.json").read_text())

def mk(b,arm,i,low,ok,valid=True):
    pages=100.0 if low else 116.0
    target=1 if arm=="local_p" else 3
    return {
        "block":b,"arm":arm,"identity":i,"valid":valid,
        "cpu_match":valid,"q64_pass":ok,
        "touch_delta_pages":64.0 if ok else 0.0,
        "migration_delta_pages":0.0,
        "pre_current_pages":pages,
        "stratum":"LOW" if low else "HIGH",
        "affinity_to_go_us":100.0+i,
        "observed_cpu":target,
    }

def support_matrix():
    out=[]
    low_seen=0
    high_seen=0
    for b in range(4):
        for arm in SPEC["arms"]:
            for i in range(32):
                low=i<16
                if low:
                    ok=low_seen not in {0,65}
                    low_seen+=1
                else:
                    ok=(high_seen%2)==0
                    high_seen+=1
                out.append(mk(b,arm,i,low,ok))
    return out

class T(unittest.TestCase):
    def test_support(self):
        r=analyze_trials(SPEC,support_matrix())
        self.assertEqual(r["decision"],"SUPPORT_BASELINE_GATE")
        self.assertGreaterEqual(r["LOW"]["valid_n"],100)
        self.assertLess(r["primary_fisher"]["one_sided_p"],1e-6)

    def test_reject_low_failure(self):
        rows=[]
        low_idx=0
        for b in range(4):
            for arm in SPEC["arms"]:
                for i in range(32):
                    low=i<16
                    if low:
                        ok=(low_idx%5)!=0
                        low_idx+=1
                    else:
                        ok=(i%2)==0
                    rows.append(mk(b,arm,i,low,ok))
        r=analyze_trials(SPEC,rows)
        self.assertEqual(r["decision"],"REJECT_BASELINE_GATE")

    def test_worker_compiles(self):
        gcc=shutil.which("gcc")
        if not gcc:self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"w"
            subprocess.run([
                gcc,"-O2","-Wall","-Wextra","-std=c11",
                str(ROOT/"experiments/memcg005d_worker.c"),
                "-o",str(out),
            ],check=True)
            self.assertTrue(out.exists())

if __name__=="__main__":unittest.main()
