from __future__ import annotations
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from finite_ram_lab.memcg005f_remote_low_gate import analyze_trials

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"specs/MEMCG-005F-REMOTE-LOW-ADMISSION-GATE-v1.json").read_text())

def mk(b,i,low,ok):
    return {
        "block":b,"identity":i,"valid":True,"cpu_match":True,
        "pre_current_pages":99.0 if low else 116.0,
        "stratum":"LOW" if low else "HIGH",
        "q64_pass":ok,
        "touch_delta_pages":64.0 if ok else 0.0,
        "migration_delta_pages":0.0,
        "affinity_to_go_us":120.0+i,
    }

def support_matrix():
    rows=[]; low_idx=0; high_idx=0
    for b in range(4):
        for i in range(64):
            low=i<40
            if low:
                ok=low_idx not in {0,81,122}
                low_idx+=1
            else:
                ok=(high_idx%4)==0
                high_idx+=1
            rows.append(mk(b,i,low,ok))
    return rows

class T(unittest.TestCase):
    def test_support(self):
        r=analyze_trials(SPEC,support_matrix())
        self.assertEqual(r["decision"],"SUPPORT_REMOTE_LOW_GATE")
        self.assertGreaterEqual(r["LOW"]["valid_n"],120)
        self.assertGreaterEqual(r["LOW"]["success_rate"],0.97)

    def test_reject_low(self):
        rows=[]; li=0
        for b in range(4):
            for i in range(64):
                low=i<40
                if low:
                    ok=(li%5)!=0
                    li+=1
                else:
                    ok=(i%4)==0
                rows.append(mk(b,i,low,ok))
        r=analyze_trials(SPEC,rows)
        self.assertEqual(r["decision"],"REJECT_REMOTE_LOW_GATE")

    def test_worker_compiles(self):
        gcc=shutil.which("gcc")
        if not gcc:self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"w"
            subprocess.run([gcc,"-O2","-Wall","-Wextra","-std=c11",
                str(ROOT/"experiments/memcg005d_worker.c"),"-o",str(out)],check=True)
            self.assertTrue(out.exists())

if __name__=="__main__":unittest.main()
