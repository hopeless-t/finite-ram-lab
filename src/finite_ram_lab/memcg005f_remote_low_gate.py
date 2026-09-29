from __future__ import annotations

import argparse
import json
import mmap
import os
import struct
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

from scipy.stats import fisher_exact

OFF_READY=0
OFF_MODE=4
OFF_TARGET=8
OFF_GO=12
OFF_DONE=16
OFF_STOP=20
OFF_OBS_CPU=24
OFF_TOUCHED=28
OFF_ERROR=32
CONTROL_BYTES=4096

def load_spec(path:str|Path)->dict[str,Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _run(cmd:list[str],*,check:bool=True)->subprocess.CompletedProcess[str]:
    return subprocess.run(cmd,text=True,capture_output=True,check=check)

def _u32(mm:mmap.mmap,off:int)->int:
    return struct.unpack_from("<I",mm,off)[0]

def _set_u32(mm:mmap.mmap,off:int,value:int)->None:
    struct.pack_into("<I",mm,off,int(value))

def _wait(pred,timeout:float=10.0)->None:
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(0.001)
    raise TimeoutError("shared-latch timeout")

def _proc_cpu(pid:int)->int:
    text=Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    tail=text[text.rfind(")")+2:].split()
    return int(tail[36])

def _wait_cpu(pid:int,cpu:int,timeout:float=5.0)->None:
    _wait(lambda:_proc_cpu(pid)==cpu,timeout)

def _current(cg:Path)->int:
    return int((cg/"memory.current").read_text(encoding="utf-8").strip())

def _start(worker:Path,root:Path,name:str,prep_cpu:int)->dict[str,Any]:
    shared=root/f"{name}.ctl"
    fd=os.open(shared,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600)
    os.ftruncate(fd,CONTROL_BYTES)
    mm=mmap.mmap(fd,CONTROL_BYTES,access=mmap.ACCESS_WRITE)
    uid=os.getuid()
    _run([
        "sudo","systemd-run","--quiet","--collect",
        f"--unit={name}",f"--uid={uid}",
        "-p","MemoryAccounting=yes",
        "-p",f"CPUAffinity={prep_cpu}",
        str(worker),"--shared",str(shared),"--max-pages","8",
    ])
    _wait(lambda:_u32(mm,OFF_READY)==1)
    pid=int(_run([
        "systemctl","show",f"{name}.service","--property=MainPID","--value"
    ]).stdout.strip())
    cg_text=_run([
        "systemctl","show",f"{name}.service","--property=ControlGroup","--value"
    ]).stdout.strip()
    cg=Path("/sys/fs/cgroup")/cg_text.lstrip("/")
    _wait_cpu(pid,prep_cpu)
    if _u32(mm,OFF_TOUCHED)!=0:
        raise RuntimeError("pre-touch contamination")
    return {"name":name,"pid":pid,"cg":cg,"fd":fd,"mm":mm}

def _stop(u:dict[str,Any])->None:
    try:_set_u32(u["mm"],OFF_STOP,1)
    except Exception:pass
    _run(["sudo","systemctl","stop",u["name"]+".service"],check=False)
    try:
        u["mm"].close()
        os.close(u["fd"])
    except Exception:pass

def _is_q64(spec:dict[str,Any],d:float)->bool:
    return float(spec["q64_min_pages"])<=d<=float(spec["q64_max_pages"])

def run_probe(spec:dict[str,Any],*,worker:Path,root:Path,block:int,identity:int,
              prep_cpu:int,stock_cpu:int)->dict[str,Any]:
    runid=os.getenv("GITHUB_RUN_ID","local")
    name=f"fr-m5f-{runid}-{block}-{identity}"
    u=_start(worker,root,name,prep_cpu)
    page=int(spec["required_page_size"])
    try:
        pre=_current(u["cg"])
        pre_pages=pre/page
        stratum="LOW" if pre_pages<=float(spec["low_threshold_pages"]) else "HIGH"

        t0=time.monotonic_ns()
        os.sched_setaffinity(u["pid"],{stock_cpu})
        _wait_cpu(u["pid"],stock_cpu)
        mid=_current(u["cg"])
        _set_u32(u["mm"],OFF_MODE,2)
        _set_u32(u["mm"],OFF_TARGET,stock_cpu)
        _set_u32(u["mm"],OFF_DONE,0)
        _set_u32(u["mm"],OFF_ERROR,0)
        affinity_to_go_us=(time.monotonic_ns()-t0)/1000.0
        _set_u32(u["mm"],OFF_GO,1)

        _wait(lambda:_u32(u["mm"],OFF_DONE)==1)
        post=_current(u["cg"])

        migration_delta=(mid-pre)/page
        touch_delta=(post-mid)/page
        observed=_u32(u["mm"],OFF_OBS_CPU)
        worker_error=_u32(u["mm"],OFF_ERROR)
        touched=_u32(u["mm"],OFF_TOUCHED)
        cpu_match=observed==stock_cpu
        valid=worker_error==0 and touched==1 and cpu_match

        return {
            "experiment_id":spec["experiment_id"],
            "block":block,
            "identity":identity,
            "prep_cpu":prep_cpu,
            "stock_cpu":stock_cpu,
            "pre_current_pages":pre_pages,
            "stratum":stratum,
            "migration_delta_pages":migration_delta,
            "touch_delta_pages":touch_delta,
            "q64_pass":_is_q64(spec,touch_delta),
            "affinity_to_go_us":affinity_to_go_us,
            "observed_cpu":observed,
            "cpu_match":cpu_match,
            "worker_error":worker_error,
            "touched":touched,
            "valid":valid,
        }
    finally:
        _stop(u)

def _summary(rows:list[dict[str,Any]])->dict[str,Any]:
    valid=[r for r in rows if r["valid"]]
    ok=sum(bool(r["q64_pass"]) for r in valid)
    n=len(valid)
    zero=sum(float(r["touch_delta_pages"])==0.0 for r in valid)
    other=sum((not bool(r["q64_pass"])) and float(r["touch_delta_pages"])!=0.0 for r in valid)
    return {
        "valid_n":n,
        "q64_successes":ok,
        "failures":n-ok,
        "success_rate":ok/n if n else None,
        "zero_delta":zero,
        "other_delta":other,
    }

def _quartiles(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    rs=sorted([r for r in rows if r["valid"]],key=lambda r:float(r["affinity_to_go_us"]))
    n=len(rs); out=[]
    for q in range(4):
        chunk=rs[q*n//4:(q+1)*n//4]
        if not chunk: continue
        ok=sum(bool(r["q64_pass"]) for r in chunk)
        out.append({
            "quartile":q+1,"n":len(chunk),
            "latency_us_min":float(chunk[0]["affinity_to_go_us"]),
            "latency_us_max":float(chunk[-1]["affinity_to_go_us"]),
            "q64_successes":ok,"success_rate":ok/len(chunk),
        })
    return out

def analyze_trials(spec:dict[str,Any],trials:list[dict[str,Any]])->dict[str,Any]:
    blocks=int(spec["runner_blocks"]); nident=int(spec["identities_per_block"])
    expected={(b,i) for b in range(blocks) for i in range(nident)}
    got={(int(t["block"]),int(t["identity"])) for t in trials}
    if got!=expected: raise ValueError("incomplete trial matrix")

    threshold=float(spec["low_threshold_pages"])
    for t in trials:
        expected_s="LOW" if float(t["pre_current_pages"])<=threshold else "HIGH"
        if t["stratum"]!=expected_s: raise ValueError("stratum mismatch")

    cpu_mismatches=sum(not bool(t["cpu_match"]) for t in trials)
    valid=[t for t in trials if t["valid"]]
    low=[t for t in valid if t["stratum"]=="LOW"]
    high=[t for t in valid if t["stratum"]=="HIGH"]
    ls=_summary(low); hs=_summary(high)

    fisher_p=None; fisher_or=None
    if ls["valid_n"] and hs["valid_n"]:
        f=fisher_exact([
            [ls["q64_successes"],ls["failures"]],
            [hs["q64_successes"],hs["failures"]],
        ],alternative="greater")
        fisher_p=float(f.pvalue); fisher_or=float(f.statistic)

    block_rows=[]; bad_blocks=0; support_blocks=True
    for b in range(blocks):
        l=[t for t in low if int(t["block"])==b]
        h=[t for t in high if int(t["block"])==b]
        lbs=_summary(l); hbs=_summary(h)
        if lbs["valid_n"]>=int(spec["reject_block_min_low_n"]) and lbs["success_rate"]<float(spec["reject_block_low_success_rate"]):
            bad_blocks+=1
        if lbs["valid_n"]>=int(spec["support_block_min_low_n"]) and lbs["success_rate"]<float(spec["support_block_low_success_rate"]):
            support_blocks=False
        block_rows.append({"block":b,"LOW":lbs,"HIGH":hbs})

    all_other=sum(
        (not bool(t["q64_pass"])) and float(t["touch_delta_pages"])!=0.0
        for t in valid
    )
    high_condition=(
        hs["valid_n"]<int(spec["support_high_min_n"])
        or hs["success_rate"]<=float(spec["support_high_max_success_rate"])
    )
    fisher_condition=(
        hs["valid_n"]==0
        or (fisher_p is not None and fisher_p<float(spec["support_fisher_p_max"]))
    )

    support=(
        ls["valid_n"]>=int(spec["support_min_low_n"])
        and ls["success_rate"]>=float(spec["support_low_success_rate"])
        and support_blocks
        and high_condition
        and fisher_condition
        and cpu_mismatches==0
        and all_other==0
    )
    reject=(
        (ls["valid_n"]>=int(spec["reject_min_low_n"]) and ls["success_rate"]<float(spec["reject_low_success_rate"]))
        or bad_blocks>=int(spec["reject_bad_block_count"])
    )
    decision="SUPPORT_REMOTE_LOW_GATE" if support else "REJECT_REMOTE_LOW_GATE" if reject else "INCONCLUSIVE"

    hist=Counter(str(int(round(float(t["pre_current_pages"])))) for t in valid)
    migration=Counter(str(float(t["migration_delta_pages"])) for t in valid)

    return {
        "experiment_id":spec["experiment_id"],
        "decision":decision,
        "threshold_pages":threshold,
        "cpu_mismatches":cpu_mismatches,
        "LOW":ls,"HIGH":hs,
        "admission_yield":ls["valid_n"]/len(valid) if valid else None,
        "primary_fisher":{"odds_ratio":fisher_or,"one_sided_p":fisher_p},
        "blocks":block_rows,
        "affinity_to_go_quartiles":_quartiles(valid),
        "pre_current_histogram":dict(sorted(hist.items(),key=lambda kv:int(kv[0]))),
        "migration_delta_histogram":dict(migration),
        "all_other_delta_failures":all_other,
        "trials":trials,
        "inference_boundary":"Hosted REMOTE_LOW admission-gate validation only; no slot-capacity inference.",
    }

def main()->None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    rb=sub.add_parser("run-block"); rb.add_argument("--spec",required=True); rb.add_argument("--block",type=int,required=True); rb.add_argument("--worker",required=True); rb.add_argument("--out-root",required=True)
    ag=sub.add_parser("aggregate"); ag.add_argument("--spec",required=True); ag.add_argument("--input-root",required=True); ag.add_argument("--json-out",required=True)
    a=p.parse_args(); spec=load_spec(a.spec)

    if a.cmd=="run-block":
        cpus=sorted(os.sched_getaffinity(0))
        if len(cpus)<3: raise RuntimeError("requires >=3 CPUs")
        control,prep,stock=cpus[0],cpus[1],cpus[-1]
        if len({control,prep,stock})<3: raise RuntimeError("CPU roles not distinct")
        os.sched_setaffinity(0,{control})
        root=Path(a.out_root); root.mkdir(parents=True,exist_ok=True)
        (root/"cpu-receipt.json").write_text(json.dumps({"control_cpu":control,"prep_cpu":prep,"stock_cpu":stock},indent=2)+"\n")
        for i in range(int(spec["identities_per_block"])):
            rr=root/f"id-{i}"; rr.mkdir(parents=True,exist_ok=True)
            t=run_probe(spec,worker=Path(a.worker).resolve(),root=rr,block=a.block,identity=i,prep_cpu=prep,stock_cpu=stock)
            (root/f"trial-{a.block}-{i}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
        return

    trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*.json"))]
    r=analyze_trials(spec,trials)
    out=Path(a.json_out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":r["decision"],"LOW":r["LOW"],"HIGH":r["HIGH"],"admission_yield":r["admission_yield"]},sort_keys=True))

if __name__=="__main__": main()
