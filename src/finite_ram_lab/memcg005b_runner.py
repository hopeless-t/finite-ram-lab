from __future__ import annotations
import argparse,json,os,subprocess,time
from pathlib import Path
from typing import Any
from .memcg005b_staged_k7 import load_spec,analyze_trials

def _run(cmd,check=True): return subprocess.run(cmd,text=True,capture_output=True,check=check)
def _lines(p): return p.read_text().splitlines() if p.exists() else []
def _wait(pred,timeout=10.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(.02)
    raise TimeoutError("receipt timeout")

def _start(worker,root,name,prep_cpu):
    fifo=root/(name+".fifo"); status=root/(name+".status")
    if fifo.exists(): fifo.unlink()
    os.mkfifo(fifo); status.write_text("")
    _run(["sudo","systemd-run","--quiet","--collect",f"--unit={name}",
          "-p","MemoryAccounting=yes","-p",f"CPUAffinity={prep_cpu}",
          str(worker),"--control",str(fifo),"--status",str(status),"--max-pages","128"])
    _wait(lambda:any(x.startswith("READY ") for x in _lines(status)))
    ready=next(x for x in _lines(status) if x.startswith("READY "))
    if "touched=0" not in ready: raise RuntimeError("nonzero READY")
    cpu=int(next(x for x in ready.split() if x.startswith("cpu=")).split("=")[1])
    if cpu!=prep_cpu: raise RuntimeError("READY not on prep CPU")
    cg=_run(["systemctl","show",f"{name}.service","--property=ControlGroup","--value"]).stdout.strip()
    return {"name":name,"fifo":fifo,"status":status,"cg":Path("/sys/fs/cgroup")/cg.lstrip("/"),"ready":ready}

def _send(u,cmd,prefix=None):
    before=sum(x.startswith(prefix) for x in _lines(u["status"])) if prefix else 0
    with u["fifo"].open("w") as f: f.write(cmd+"\n"); f.flush()
    if prefix: _wait(lambda:sum(x.startswith(prefix) for x in _lines(u["status"]))>before)

def _cur(u): return int((u["cg"]/ "memory.current").read_text())
def _migrate(u,cpu):
    _send(u,f"MIGRATE {cpu}","MIGRATE ")
    line=[x for x in _lines(u["status"]) if x.startswith("MIGRATE ")][-1]
    return line
def _touch_delta(u,page):
    a=_cur(u); _send(u,"TOUCH_ONE","TOUCH "); b=_cur(u)
    return (b-a)/page,a,b
def _stop(u):
    try:_send(u,"STOP")
    except Exception:pass
    _run(["sudo","systemctl","stop",u["name"]+".service"],check=False)

def _q64(spec,d): return float(spec["q64_min_pages"])<=d<=float(spec["q64_max_pages"])
def _state(spec,d):
    if _q64(spec,d): return "ABSENT"
    if abs(d)<float(spec["present_abs_lt_pages"]): return "PRESENT"
    return "AMBIGUOUS"

def run_replica(spec,block,m,worker,root,prep_cpu,stock_cpu):
    runid=os.getenv("GITHUB_RUN_ID","x"); prefix=f"fr-m5b-{runid}-{block}-m{m}"
    units=[]
    try:
        roles=[("w",i) for i in range(int(spec["wash_count"]))]+[("t",0)]+[("c",i) for i in range(1,m+1)]
        by={}
        for role,idx in roles:
            u=_start(worker,root,f"{prefix}-{role}{idx}",prep_cpu); units.append(u); by[f"{role}{idx}"]=u
        page=int(spec["required_page_size"]); insertions=[]
        sequence=[f"w{i}" for i in range(int(spec["wash_count"]))]+["t0"]+[f"c{i}" for i in range(1,m+1)]
        for key in sequence:
            mig=_migrate(by[key],stock_cpu)
            d,a,b=_touch_delta(by[key],page)
            rec={"identity":key,"migrate_receipt":mig,"delta_pages":d,
                 "pre_current_bytes":a,"post_current_bytes":b,"q64_verified":_q64(spec,d)}
            insertions.append(rec)
            if not rec["q64_verified"]:
                return {"experiment_id":spec["experiment_id"],"block":block,"m":m,
                        "valid_state":False,"invalid_reason":f"{key}:INSERT_NOT_Q64",
                        "insertions":insertions,"target_probe":None,"target_state":"INVALID"}
        d,a,b=_touch_delta(by["t0"],page); state=_state(spec,d)
        return {"experiment_id":spec["experiment_id"],"block":block,"m":m,
                "valid_state":state in {"PRESENT","ABSENT"},
                "invalid_reason":None if state in {"PRESENT","ABSENT"} else "TARGET_PROBE_AMBIGUOUS",
                "insertions":insertions,
                "target_probe":{"delta_pages":d,"pre_current_bytes":a,"post_current_bytes":b},
                "target_state":state}
    finally:
        for u in reversed(units): _stop(u)

def main():
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
        for m in [int(x) for x in spec["tested_m"]]:
            rr=root/f"m-{m}"; rr.mkdir(parents=True,exist_ok=True)
            t=run_replica(spec,a.block,m,Path(a.worker).resolve(),rr,prep,stock)
            (root/f"trial-{a.block}-m{m}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
    else:
        trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*-m*.json"))]
        r=analyze_trials(spec,trials); out=Path(a.json_out); out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"decision":r["decision"],"support_blocks":r["support_blocks"],"complete_valid_blocks":r["complete_valid_blocks"],"best_k":r["best_k_by_errors"]},sort_keys=True))
if __name__=="__main__": main()
