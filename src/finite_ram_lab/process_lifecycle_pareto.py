from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .fast_reinstall_epoch import identity, make_epoch, verify_epoch
from .fast_reinstall_loop import run_measured
from .fast_reinstall_loop_v2 import build_wheel_isolated

WORK_BODY = r'''
def work(seed):
    rng = random.Random(seed)
    trace = generate_trace("shifting_hotset", rng, 12000, 257, 41)
    core = {
        "seed": seed,
        "trace_sha256": hashlib.sha256(bytes((x % 256 for x in trace))).hexdigest(),
        "lru_faults": lru_faults(trace, 41),
        "opt_faults": opt_faults(trace, 41),
        "trace_len": len(trace),
    }
    core["semantic_sha256"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return core
'''.strip()

COLD_CODE = (
    "import hashlib,json,random,sys\n"
    "from finite_ram_lab.sim import generate_trace,lru_faults,opt_faults\n"
    + WORK_BODY
    + "\nprint(json.dumps(work(int(sys.argv[1])),sort_keys=True))\n"
)

WORKER_CODE = (
    "import hashlib,json,random,sys,resource\n"
    "from finite_ram_lab.sim import generate_trace,lru_faults,opt_faults\n"
    + WORK_BODY
    + r'''
print(json.dumps({"ready": True, "ru_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
for line in sys.stdin:
    line=line.strip()
    if not line:
        continue
    if line == "STOP":
        break
    seed=int(line)
    out=work(seed)
    out["ru_maxrss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(out,sort_keys=True),flush=True)
'''
)


def rss_kib(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return 0


def parse_last_json(stdout: str) -> dict[str, Any]:
    lines=[x for x in stdout.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError("no JSON output")
    return json.loads(lines[-1])


def cold_call(repo: Path, wheel: Path, epoch: dict[str, Any], seed: int) -> dict[str, Any]:
    env=dict(os.environ); env["PYTHONPATH"]=str(wheel); env.pop("PYTHONDONTWRITEBYTECODE",None)
    t0=time.perf_counter_ns()
    if not verify_epoch(wheel, epoch):
        raise RuntimeError("artifact epoch changed")
    measured=run_measured([sys.executable,"-c",COLD_CODE,str(seed)],cwd=repo,env=env,poll_s=0.001)
    elapsed=time.perf_counter_ns()-t0
    if measured["returncode"] != 0:
        raise RuntimeError(measured["stderr"][-2000:])
    return {"elapsed_ns":elapsed,"peak_rss_kib":measured["peak_rss_kib"],"payload":parse_last_json(measured["stdout"])}


def warm_call(worker: subprocess.Popen[str], wheel: Path, epoch: dict[str, Any], seed: int) -> dict[str, Any]:
    assert worker.stdin is not None and worker.stdout is not None
    t0=time.perf_counter_ns()
    if not verify_epoch(wheel, epoch):
        raise RuntimeError("artifact epoch changed")
    worker.stdin.write(f"{seed}\n"); worker.stdin.flush()
    line=worker.stdout.readline()
    elapsed=time.perf_counter_ns()-t0
    if not line:
        raise RuntimeError("worker exited without response")
    return {"elapsed_ns":elapsed,"resident_rss_kib":rss_kib(worker.pid),"payload":json.loads(line)}


def percentile(xs: list[float], q: float) -> float:
    ys=sorted(xs); return float(ys[max(0,min(len(ys)-1,int(len(ys)*q)-1))])


def run(repo: Path, out: Path, *, blocks: int, seed: int) -> dict[str, Any]:
    out.mkdir(parents=True,exist_ok=True)
    wheel, build=build_wheel_isolated(repo,out/"artifacts")
    epoch=make_epoch(wheel)
    env=dict(os.environ); env["PYTHONPATH"]=str(wheel); env.pop("PYTHONDONTWRITEBYTECODE",None)
    start=time.perf_counter_ns()
    worker=subprocess.Popen([sys.executable,"-u","-c",WORKER_CODE],cwd=repo,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    assert worker.stdout is not None
    ready_line=worker.stdout.readline()
    startup_ns=time.perf_counter_ns()-start
    if not ready_line:
        err=worker.stderr.read() if worker.stderr else ""
        raise RuntimeError(f"worker failed to start: {err[-2000:]}")
    ready=json.loads(ready_line)
    idle_rss=rss_kib(worker.pid)
    rows=[]
    try:
        for block in range(blocks):
            request_seed=seed+block
            arms=["cold_process","warm_worker"]
            random.Random(seed+block*3571).shuffle(arms)
            pair={}
            for order,arm in enumerate(arms):
                result=(cold_call(repo,wheel,epoch,request_seed) if arm=="cold_process" else warm_call(worker,wheel,epoch,request_seed))
                pair[arm]=result["payload"]["semantic_sha256"]
                row={"block":block,"order":order,"arm":arm,"seed":request_seed,**result}
                rows.append(row)
            if pair["cold_process"] != pair["warm_worker"]:
                raise RuntimeError(f"semantic mismatch block {block}")
    finally:
        if worker.poll() is None and worker.stdin is not None:
            worker.stdin.write("STOP\n"); worker.stdin.flush(); worker.wait(timeout=5)
    by_arm={}
    for arm in ["cold_process","warm_worker"]:
        g=[r for r in rows if r["arm"]==arm]
        ms=[r["elapsed_ns"]/1e6 for r in g]
        by_arm[arm]={"n":len(g),"median_ms":float(statistics.median(ms)),"p95_ms":percentile(ms,.95),"min_ms":float(min(ms)),"max_ms":float(max(ms))}
        if arm=="cold_process": by_arm[arm]["median_peak_rss_kib"]=float(statistics.median(r["peak_rss_kib"] for r in g))
        else:
            by_arm[arm]["median_resident_rss_kib"]=float(statistics.median(r["resident_rss_kib"] for r in g))
            by_arm[arm]["max_resident_rss_kib"]=max(r["resident_rss_kib"] for r in g)
    by_arm["warm_worker"]["speedup_vs_cold"]=by_arm["cold_process"]["median_ms"]/by_arm["warm_worker"]["median_ms"]
    # In-process lower bound: imports are already resident; vary seed identically.
    from .sim import generate_trace,lru_faults,opt_faults
    import hashlib as _hashlib, json as _json
    lower=[]; lower_hashes=[]
    for block in range(blocks):
        s=seed+block; t0=time.perf_counter_ns(); rng=random.Random(s); trace=generate_trace("shifting_hotset",rng,12000,257,41)
        core={"seed":s,"trace_sha256":_hashlib.sha256(bytes((x%256 for x in trace))).hexdigest(),"lru_faults":lru_faults(trace,41),"opt_faults":opt_faults(trace,41),"trace_len":len(trace)}
        core["semantic_sha256"]=_hashlib.sha256(_json.dumps(core,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        lower.append((time.perf_counter_ns()-t0)/1e6); lower_hashes.append(core["semantic_sha256"])
    result={
      "experiment_id":"FRL-REINSTALL-004-PROCESS-PARETO-v1",
      "blocks":blocks,
      "semantic_pairs_match":True,
      "worker_startup_ms":startup_ns/1e6,
      "worker_idle_rss_kib":idle_rss,
      "worker_ready":ready,
      "canonical_build_residue_delta_bytes":build["canonical_residue_delta_bytes"],
      "arms":by_arm,
      "inproc_lower_bound":{"median_ms":float(statistics.median(lower)),"p95_ms":percentile(lower,.95)},
    }
    result["warm_gap_over_inproc_ms"]=by_arm["warm_worker"]["median_ms"]-result["inproc_lower_bound"]["median_ms"]
    result["warm_overhead_fraction_vs_inproc"]=(by_arm["warm_worker"]["median_ms"]/result["inproc_lower_bound"]["median_ms"])-1
    (out/"trials.jsonl").write_text("".join(json.dumps(r,sort_keys=True)+"\n" for r in rows))
    (out/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",default="."); p.add_argument("--out",required=True); p.add_argument("--blocks",type=int,default=100); p.add_argument("--seed",type=int,default=20261012); a=p.parse_args()
    print(json.dumps(run(Path(a.repo).resolve(),Path(a.out).resolve(),blocks=a.blocks,seed=a.seed),indent=2,sort_keys=True))

if __name__=="__main__": main()
