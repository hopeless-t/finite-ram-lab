from __future__ import annotations
import argparse,json,mmap,os,struct,subprocess,time,math
from pathlib import Path
import numpy as np
from scipy.special import betaln,logsumexp
from scipy.stats import fisher_exact

OFF_READY=0;OFF_MODE=4;OFF_TARGET=8;OFF_GO=12;OFF_DONE=16;OFF_STOP=20
OFF_OBS_CPU=24;OFF_TOUCHED=28;OFF_ERROR=32;CONTROL_BYTES=4096

def load_spec(p): return json.loads(Path(p).read_text())
def _run(cmd,check=True): return subprocess.run(cmd,text=True,capture_output=True,check=check)
def _u32(mm,o): return struct.unpack_from("<I",mm,o)[0]
def _set(mm,o,v): struct.pack_into("<I",mm,o,int(v))
def _wait(pred,timeout=10):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if pred(): return
        time.sleep(.001)
    raise TimeoutError("timeout")
def _proc_cpu(pid):
    s=Path(f"/proc/{pid}/stat").read_text()
    return int(s[s.rfind(")")+2:].split()[36])
def _wait_cpu(pid,cpu): _wait(lambda:_proc_cpu(pid)==cpu,5)
def _current(cg): return int((cg/"memory.current").read_text().strip())
def _q64(spec,d): return spec["q64_min_pages"]<=d<=spec["q64_max_pages"]
def capacity_for(spec,block,identity):
    caps=spec["capacities"]; return int(caps[(block+identity)%len(caps)])

def _start(worker,root,name,p,max_pages):
    ctl=root/f"{name}.ctl";fd=os.open(ctl,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600)
    os.ftruncate(fd,CONTROL_BYTES);mm=mmap.mmap(fd,CONTROL_BYTES,access=mmap.ACCESS_WRITE)
    _run(["sudo","systemd-run","--quiet","--collect",f"--unit={name}",f"--uid={os.getuid()}",
      "-p","MemoryAccounting=yes","-p",f"CPUAffinity={p}",str(worker),
      "--shared",str(ctl),"--max-pages",str(max_pages)])
    _wait(lambda:_u32(mm,OFF_READY)==1)
    pid=int(_run(["systemctl","show",f"{name}.service","--property=MainPID","--value"]).stdout.strip())
    cgt=_run(["systemctl","show",f"{name}.service","--property=ControlGroup","--value"]).stdout.strip()
    cg=Path("/sys/fs/cgroup")/cgt.lstrip("/");_wait_cpu(pid,p)
    return {"name":name,"pid":pid,"cg":cg,"fd":fd,"mm":mm}
def _stop(u):
    try:_set(u["mm"],OFF_STOP,1)
    except Exception:pass
    _run(["sudo","systemctl","stop",u["name"]+".service"],check=False)
    try:u["mm"].close();os.close(u["fd"])
    except Exception:pass

def run_probe(spec,worker,root,block,identity,p,s):
    cap=capacity_for(spec,block,identity)
    name=f"fr-m5gf-{os.getenv('GITHUB_RUN_ID','local')}-{block}-{identity}"
    u=_start(worker,root,name,p,cap);page=spec["required_page_size"]
    try:
        pre=_current(u["cg"]);pre_pages=pre/page
        stratum="LOW" if pre_pages<=spec["low_threshold_pages"] else "HIGH"
        t0=time.monotonic_ns();os.sched_setaffinity(u["pid"],{s});_wait_cpu(u["pid"],s)
        mid=_current(u["cg"]);mig=(mid-pre)/page;lat=(time.monotonic_ns()-t0)/1000.0
        _set(u["mm"],OFF_MODE,2);_set(u["mm"],OFF_TARGET,s);_set(u["mm"],OFF_DONE,0);_set(u["mm"],OFF_ERROR,0)
        before=_current(u["cg"]);_set(u["mm"],OFF_GO,1);_wait(lambda:_u32(u["mm"],OFF_DONE)==1)
        after=_current(u["cg"]);d=(after-before)/page
        cpu=_u32(u["mm"],OFF_OBS_CPU);err=_u32(u["mm"],OFF_ERROR);touched=_u32(u["mm"],OFF_TOUCHED)
        return {"block":block,"identity":identity,"capacity_pages":cap,
          "pre_current_pages":pre_pages,"stratum":stratum,"migration_delta_pages":mig,
          "affinity_to_go_us":lat,"first_touch_delta_pages":d,"q64_pass":_q64(spec,d),
          "cpu_match":cpu==s,"worker_error":err,"valid":cpu==s and err==0 and touched==1}
    finally:_stop(u)

def _sum(rows):
    n=len(rows);f=sum(not r["q64_pass"] for r in rows)
    return {"n":n,"failures":f,"successes":n-f,"capture_rate":f/n if n else None,
      "zero_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]==0 for r in rows),
      "other_failures":sum((not r["q64_pass"]) and r["first_touch_delta_pages"]!=0 for r in rows)}

def _step_posterior(spec,caps,sums):
    Ts=[int(t) for t in spec["candidate_thresholds"]]
    logs=[];fits={}
    for T in Ts:
        lo=[sums[str(c)] for c in caps if c<T];hi=[sums[str(c)] for c in caps if c>=T]
        fl=sum(r["failures"] for r in lo);sl=sum(r["successes"] for r in lo)
        fh=sum(r["failures"] for r in hi);sh=sum(r["successes"] for r in hi)
        logs.append(betaln(fl+1,sl+1)+betaln(fh+1,sh+1))
        fits[T]={"low":{"failures":fl,"successes":sl,"n":fl+sl,"rate":fl/(fl+sl)},
                 "high":{"failures":fh,"successes":sh,"n":fh+sh,"rate":fh/(fh+sh)}}
    p=np.exp(np.array(logs)-logsumexp(logs))
    order=np.argsort(-p)
    best=Ts[int(order[0])];second=Ts[int(order[1])]
    odds=float(p[order[0]]/p[order[1]]) if p[order[1]]>0 else math.inf
    return {"posterior":{str(T):float(x) for T,x in zip(Ts,p)},
      "map_T":best,"map_mass":float(p[order[0]]),"second_T":second,
      "posterior_odds_map_vs_second":odds,"fits":fits}

def _ll_binom(p,r):
    p=min(max(p,1e-12),1-1e-12)
    return r["failures"]*math.log(p)+r["successes"]*math.log(1-p)

def _aic_models(spec,caps,sums,step):
    rows=[sums[str(c)] for c in caps]
    F=sum(r["failures"] for r in rows);N=sum(r["n"] for r in rows);p=F/N
    L0=sum(_ll_binom(p,r) for r in rows)
    T=step["map_T"];fit=step["fits"][T]
    ps=[fit["low"]["rate"] if c<T else fit["high"]["rate"] for c in caps]
    Ls=sum(_ll_binom(pp,r) for pp,r in zip(ps,rows))
    Lc=0.
    for r in rows:
        pp=r["failures"]/r["n"] if r["n"] else .5
        Lc+=_ll_binom(pp,r)
    return {"CONSTANT":{"aic":2-2*L0},"HARD_STEP":{"aic":6-2*Ls,"T":T},
            "CATEGORICAL":{"aic":2*len(caps)-2*Lc}}

def analyze(spec,trials):
    expected={(b,i) for b in range(spec["runner_blocks"]) for i in range(spec["identities_per_block"])}
    if {(int(t["block"]),int(t["identity"])) for t in trials}!=expected: raise ValueError("incomplete matrix")
    caps=[int(c) for c in spec["capacities"]]
    valid=[t for t in trials if t["valid"] and t["stratum"]=="LOW"]
    sums={str(c):_sum([t for t in valid if int(t["capacity_pages"])==c]) for c in caps}
    step=_step_posterior(spec,caps,sums);mods=_aic_models(spec,caps,sums,step)
    T=step["map_T"];fit=step["fits"][T]
    lo,hi=fit["low"],fit["high"]
    fx=fisher_exact([[hi["failures"],hi["successes"]],[lo["failures"],lo["successes"]]],alternative="two-sided")
    cpu=sum(not t["cpu_match"] for t in trials)
    other=sum(t["valid"] and t["stratum"]=="LOW" and not t["q64_pass"] and t["first_touch_delta_pages"]!=0 for t in trials)
    categorical_bad=mods["CATEGORICAL"]["aic"]<=mods["HARD_STEP"]["aic"]-spec["categorical_aic_reject_margin"]
    support=(cpu==0 and other==0 and step["map_mass"]>=spec["posterior_support_min"]
      and step["posterior_odds_map_vs_second"]>=spec["posterior_odds_min"]
      and lo["rate"]<hi["rate"] and not categorical_bad)
    return {"experiment_id":spec["experiment_id"],
      "decision":"SUPPORT_LOCALIZED_T" if support else "REJECT_OR_UNRESOLVED_HARD_STEP",
      "by_capacity":sums,"threshold":step,"models":mods,
      "frequentist_map_split":{"odds_ratio":float(fx.statistic),"two_sided_p":float(fx.pvalue),
        "risk_difference":hi["rate"]-lo["rate"]},
      "cpu_mismatches":cpu,"other_delta_failures":other,"trials":trials}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    rb=sp.add_parser("run-block");rb.add_argument("--spec",required=True);rb.add_argument("--block",type=int,required=True);rb.add_argument("--worker",required=True);rb.add_argument("--out-root",required=True)
    ag=sp.add_parser("aggregate");ag.add_argument("--spec",required=True);ag.add_argument("--input-root",required=True);ag.add_argument("--json-out",required=True)
    a=ap.parse_args();spec=load_spec(a.spec)
    if a.cmd=="run-block":
        cpus=sorted(os.sched_getaffinity(0));c,p,s=cpus[0],cpus[1],cpus[-1];os.sched_setaffinity(0,{c})
        root=Path(a.out_root);root.mkdir(parents=True,exist_ok=True)
        for i in range(spec["identities_per_block"]):
            rr=root/f"id-{i}";rr.mkdir(parents=True,exist_ok=True)
            t=run_probe(spec,Path(a.worker).resolve(),rr,a.block,i,p,s)
            (root/f"trial-{a.block}-{i}.json").write_text(json.dumps(t,indent=2,sort_keys=True)+"\n")
        return
    trials=[json.loads(x.read_text()) for x in sorted(Path(a.input_root).rglob("trial-*.json"))]
    r=analyze(spec,trials);out=Path(a.json_out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":r["decision"],"by_capacity":r["by_capacity"],
      "threshold":r["threshold"],"models":r["models"]},sort_keys=True))
if __name__=="__main__":main()
