from __future__ import annotations
import argparse,csv,json,math,random,re
from pathlib import Path
import numpy as np
import pandas as pd

F=re.compile(r"timeline-(\d+)-high(\d+)-mode(full|none)-rep(\d+)\.json$")
B=re.compile(r"(?:val002-)?block-(\d+)$")

def spec(p): return json.loads(Path(p).read_text())
def ph(d,n): return next(e for e in d["timeline"] if e["phase"]==n)
def ds(a,b,k): return int(b["os"]["memory_stat"].get(k,0)-a["os"]["memory_stat"].get(k,0))
def de(a,b,k): return int(b["os"]["memory_events"].get(k,0)-a["os"]["memory_events"].get(k,0))

def schedule(s,block):
    rows=[]
    for c in s["conditions"]:
        for r in range(int(c["repeats_per_block"])):
            rows.append({"memory_high_mib":int(c["memory_high_mib"]),"mincore_mode":c["mincore_mode"],"repeat":r})
    random.Random(int(s["base_schedule_seed"])+block*1009).shuffle(rows)
    return [{"order":i,**x} for i,x in enumerate(rows)]

def write_schedule(s,block,out):
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    with Path(out).open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["order","repeat","memory_high_mib","mincore_mode"],lineterminator="\n")
        w.writeheader(); w.writerows(schedule(s,block))

def one(p,block):
    m=F.fullmatch(p.name)
    d=json.loads(p.read_text()); a=ph(d,"BASELINE"); b=ph(d,"BURST_ALLOC"); r=ph(d,"HOTSET_RETOUCH")
    return {"block":block,"order":int(m.group(1)),"memory_high_mib":int(m.group(2)),
      "mincore_mode":m.group(3),"repeat":int(m.group(4)),"status":d["status"],
      "retouch_latency_ms":r.get("phase_latency_ns",0)/1e6,
      "swap_mib_after_burst":b["os"]["memory_swap_current"]/(1024*1024),
      "retouch_pswpin_pages":ds(b,r,"pswpin"),"retouch_pgmajfault":ds(b,r,"pgmajfault"),
      "retouch_pgscan":ds(b,r,"pgscan"),"retouch_pgsteal":ds(b,r,"pgsteal"),
      "oom_delta":de(a,r,"oom"),"oom_kill_delta":de(a,r,"oom_kill")}

def collect(root):
    rows=[]
    for d in sorted(Path(root).glob("*block-*")):
        m=B.fullmatch(d.name)
        if m: rows += [one(p,int(m.group(1))) for p in sorted((d/"raw").glob("timeline-*.json"))]
    if not rows: raise ValueError("no VAL-002 evidence")
    return pd.DataFrame(rows)

def effects(g):
    out=[]
    for b,x in g.groupby("block",sort=True):
        f=np.log(np.maximum(x[x.mincore_mode=="full"].retouch_latency_ms.to_numpy(float),1e-9))
        n=np.log(np.maximum(x[x.mincore_mode=="none"].retouch_latency_ms.to_numpy(float),1e-9))
        z=float(f.mean()-n.mean())
        out.append({"block":int(b),"log_effect":z,"ratio_full_over_none":math.exp(z),
          "full_median_ms":float(np.median(np.exp(f))),"none_median_ms":float(np.median(np.exp(n)))})
    return pd.DataFrame(out)

def perm(g,draws,seed):
    rng=np.random.default_rng(seed); groups=[x for _,x in g.groupby("block",sort=True)]
    def stat(x):
        v=np.log(np.maximum(x.retouch_latency_ms.to_numpy(float),1e-9)); lab=x.mincore_mode.to_numpy()
        return float(v[lab=="full"].mean()-v[lab=="none"].mean())
    obs=float(np.mean([stat(x) for x in groups])); exc=0
    for _ in range(draws):
        z=[]
        for x in groups:
            v=np.log(np.maximum(x.retouch_latency_ms.to_numpy(float),1e-9)); nf=int((x.mincore_mode=="full").sum()); q=rng.permutation(len(v))
            z.append(float(v[q[:nf]].mean()-v[q[nf:]].mean()))
        exc += abs(np.mean(z))>=abs(obs)
    return {"draws":draws,"log_effect":obs,"ratio_full_over_none":math.exp(obs),"two_sided_p":(exc+1)/(draws+1)}

def boot(e,draws,seed):
    rng=np.random.default_rng(seed); x=e.log_effect.to_numpy(float)
    q=np.quantile([rng.choice(x,size=len(x),replace=True).mean() for _ in range(draws)],[.025,.5,.975])
    return {"draws":draws,"ratio_median":math.exp(float(q[1])),"ratio_ci95":[math.exp(float(q[0])),math.exp(float(q[2]))]}

def level(t,l):
    o={}
    for mode in ("full","none"):
        g=t[(t.memory_high_mib==l)&(t.mincore_mode==mode)]
        o[mode]={"trials":len(g),"median_retouch_ms":float(np.median(g.retouch_latency_ms)),
          "p90_retouch_ms":float(np.quantile(g.retouch_latency_ms,.9)),
          "gt50ms_count":int((g.retouch_latency_ms>50).sum()),
          "median_swap_mib_after_burst":float(np.median(g.swap_mib_after_burst)),
          "median_pswpin_pages":float(np.median(g.retouch_pswpin_pages)),
          "median_pgmajfault":float(np.median(g.retouch_pgmajfault))}
    return o

def analyze(s,root):
    t=collect(root); g=t[t.memory_high_mib==int(s["primary_level_mib"])]; e=effects(g)
    expected=int(s["runner_blocks"])*sum(int(c["repeats_per_block"]) for c in s["conditions"])
    checks={"eight_blocks_present":t.block.nunique()==int(s["runner_blocks"]),"96_trials_present":len(t)==expected,
      "all_trials_pass":bool((t.status=="PASS").all()),"no_oom":bool(((t.oom_delta+t.oom_kill_delta)==0).all()),
      "balanced_primary_modes":all((x.mincore_mode=="full").sum()==(x.mincore_mode=="none").sum() for _,x in g.groupby("block"))}
    return t,e,{"experiment_id":"VAL-002","execution_status":"PASS" if all(checks.values()) else "FAIL","checks":checks,
      "total_trials":len(t),"runner_blocks":int(t.block.nunique()),
      "primary":{"permutation":perm(g,int(s["permutation_draws"]),int(s["base_schedule_seed"])+701),
      "cluster_bootstrap":boot(e,int(s["cluster_bootstrap_resamples"]),int(s["base_schedule_seed"])+1701),
      "block_effects":e.to_dict(orient="records")},"levels":{str(l):level(t,l) for l in (160,164,168)}}

def main():
    a=argparse.ArgumentParser(); sub=a.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("schedule"); p.add_argument("--spec",required=True); p.add_argument("--block",type=int,required=True); p.add_argument("--out",required=True)
    p=sub.add_parser("aggregate"); p.add_argument("--spec",required=True); p.add_argument("--input-root",required=True); p.add_argument("--out-dir",required=True)
    x=a.parse_args(); s=spec(x.spec)
    if x.cmd=="schedule": write_schedule(s,x.block,x.out); return
    t,e,z=analyze(s,x.input_root); o=Path(x.out_dir); o.mkdir(parents=True,exist_ok=True)
    t.to_csv(o/"trials.csv",index=False); e.to_csv(o/"block-effects.csv",index=False); (o/"summary.json").write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    print(json.dumps(z,indent=2,sort_keys=True))
    if z["execution_status"]!="PASS": raise SystemExit(1)

if __name__=="__main__": main()
