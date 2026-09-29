from __future__ import annotations
import argparse, json, os, subprocess, time
from pathlib import Path
from typing import Any
from .memcg004_calibrated_stock import load_spec, analyze_trials

def _run(cmd:list[str],check=True):
    return subprocess.run(cmd,text=True,capture_output=True,check=check)

def _lines(p:Path):
    return p.read_text().splitlines() if p.exists() else []

def _wait(pred,timeout=10.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(.02)
    raise TimeoutError("worker receipt timeout")

def _start(worker:Path,root:Path,name:str,cpu:int):
    fifo=root/(name+".fifo"); status=root/(name+".status")
    if fifo.exists(): fifo.unlink()
    os.mkfifo(fifo); status.write_text("")
    _run(["sudo","systemd-run","--quiet","--collect",f"--unit={name}",
          "-p","MemoryAccounting=yes","-p",f"CPUAffinity={cpu}",
          str(worker),"--control",str(fifo),"--status",str(status),"--max-pages","256"])
    _wait(lambda:any(x.startswith("READY ") for x in _lines(status)))
    ready=next(x for x in _lines(status) if x.startswith("READY "))
    if "touched=0" not in ready: raise RuntimeError("worker not zero-touch at READY")
    show=_run(["systemctl","show",f"{name}.service","--property=ControlGroup","--value"]).stdout.strip()
    return {"name":name,"fifo":fifo,"status":status,"cg":Path("/sys/fs/cgroup")/show.lstrip("/"),"ready":ready}

def _send(u,cmd):
    before=sum(x.startswith("TOUCH ") for x in _lines(u["status"]))
    with u["fifo"].open("w") as f: f.write(cmd+"\n"); f.flush()
    if cmd=="TOUCH_ONE":
        _wait(lambda:sum(x.startswith("TOUCH ") for x in _lines(u["status"]))>before)

def _cur(u): return int((u["cg"]/"memory.current").read_text().strip())
def _touch_delta(u,page):
    a=_cur(u); _send(u,"TOUCH_ONE"); b=_cur(u)
    return (b-a)/page,a,b

def _stop(u):
    try:_send(u,"STOP")
    except Exception:pass
    _run(["sudo","systemctl","stop",u["name"]+".service"],check=False)

def run_trial(spec:dict[str,Any],block:int,arm:str,worker:Path,root:Path,cpu:int):
    page=int(spec["required_page_size"]); u=_start(worker,root,f"fr-m4-{os.getenv('GITHUB_RUN_ID','x')}-{block}-{arm}",cpu)
    try:
        cal=0.0; cal_touch=None
        if arm!="control_no_prime":
            for i in range(1,int(spec["max_prime_touches"])+1):
                d,_,_=_touch_delta(u,page)
                if float(spec["calibration_min_pages"])<=d<=float(spec["calibration_max_pages"]):
                    cal=d; cal_touch=i; break
            if cal_touch is None: raise RuntimeError("no calibration Q64 event")
        passive=[]
        if arm!="no_hold":
            prev=_cur(u)
            for _ in range(int(spec["hold_samples"])):
                now=_cur(u); passive.append((prev-now)/page); prev=now
        validation=[]
        for i in range(1,int(spec["validation_touches"])+1):
            d,a,b=_touch_delta(u,page)
            validation.append({"touch":i,"delta_pages":d,"pre_current_bytes":a,"post_current_bytes":b})
        return {"experiment_id":spec["experiment_id"],"block":block,"arm":arm,
                "ready":u["ready"],"calibration_touch":cal_touch,"calibration_delta_pages":cal,
                "passive_drop_pages":passive,"validation":validation}
    finally:_stop(u)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    rb=sub.add_parser("run-block"); rb.add_argument("--spec",required=True); rb.add_argument("--block",type=int,required=True); rb.add_argument("--worker",required=True); rb.add_argument("--out-root",required=True)
    ag=sub.add_parser("aggregate"); ag.add_argument("--spec",required=True); ag.add_argument("--input-root",required=True); ag.add_argument("--json-out",required=True)
    a=p.parse_args(); spec=load_spec(a.spec)
    if a.cmd=="run-block":
        cpus=sorted(os.sched_getaffinity(0))
        if len(cpus)<2: raise RuntimeError("requires >=2 CPUs")
        control,stock=cpus[0],cpus[1]; os.sched_setaffinity(0,{control})
        root=Path(a.out_root); root.mkdir(parents=True,exist_ok=True)
        for arm in spec["arms"]:
            t=run_trial(spec,a.block,arm,Path(a.worker).resolve(),root,stock)
            (root/f"trial-{a.block}-{arm}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
    else:
        trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*.json"))]
        result=analyze_trials(spec,trials); out=Path(a.json_out); out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"decision":result["decision"],"support_blocks":result["support_blocks"],"calibrated_r":result["calibrated_r"]},sort_keys=True))
if __name__=="__main__":main()
