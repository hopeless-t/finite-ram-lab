from __future__ import annotations
import argparse,json,mmap,os,struct,subprocess,time,math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,betaln,logsumexp
from scipy.stats import beta

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
    caps=spec["capacities"];return int(caps[(block+identity)%len(caps)])

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
    name=f"fr-m5ge-{os.getenv('GITHUB_RUN_ID','local')}-{block}-{identity}"
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

def _ll(rates,rows):
    z=0.
    for p,r in zip(rates,rows):
        p=min(max(float(p),1e-12),1-1e-12)
        z+=r["failures"]*math.log(p)+r["successes"]*math.log(1-p)
    return z

def _posterior_threshold(spec,caps,rows):
    Ts=list(range(spec["step_t_min"],spec["step_t_max"]+1));logm=[]
    pars={}
    for T in Ts:
        lo=[r for c,r in zip(caps,rows) if c<T];hi=[r for c,r in zip(caps,rows) if c>=T]
        fl=sum(r["failures"] for r in lo);sl=sum(r["successes"] for r in lo)
        fh=sum(r["failures"] for r in hi);sh=sum(r["successes"] for r in hi)
        logm.append(betaln(fl+1,sl+1)+betaln(fh+1,sh+1))
        pars[T]=((fl+1,sl+1),(fh+1,sh+1))
    lw=np.array(logm);post=np.exp(lw-logsumexp(lw))
    cdf=np.cumsum(post)
    def q(v): return Ts[int(np.searchsorted(cdf,v))]
    H=float(-np.sum(post*np.log2(post+1e-300)))
    tested=set(caps);eig={}
    for x in range(spec["step_t_min"],spec["step_t_max"]):
        if x in tested: continue
        py=[]
        for T in Ts:
            (al,bl),(ah,bh)=pars[T]
            py.append(al/(al+bl) if x<T else ah/(ah+bh))
        py=np.array(py);P1=float(np.sum(post*py))
        p1=post*py;p1/=p1.sum();p0=post*(1-py);p0/=p0.sum()
        h1=-np.sum(p1*np.log2(p1+1e-300));h0=-np.sum(p0*np.log2(p0+1e-300))
        eig[str(x)]=H-(P1*h1+(1-P1)*h0)
    return {"T_posterior":{str(T):float(p) for T,p in zip(Ts,post)},
      "median":q(.5),"ci90":[q(.05),q(.95)],"ci95":[q(.025),q(.975)],
      "entropy_bits":H,"next_point_eig_bits":eig,
      "max_eig_point":int(max(eig,key=lambda k:eig[k])) if eig else None}

def _models(spec,caps,rows):
    totalf=sum(r["failures"] for r in rows);totaln=sum(r["n"] for r in rows);p=totalf/totaln
    ll0=_ll([p]*len(rows),rows)
    out={"CONSTANT":{"k":1,"loglik":ll0,"aic":2-2*ll0}}
    # hard step MLE over integer T
    best=None
    for T in range(spec["step_t_min"],spec["step_t_max"]+1):
        lo=[r for c,r in zip(caps,rows) if c<T];hi=[r for c,r in zip(caps,rows) if c>=T]
        fl=sum(r["failures"] for r in lo);nl=sum(r["n"] for r in lo)
        fh=sum(r["failures"] for r in hi);nh=sum(r["n"] for r in hi)
        pl=fl/nl;ph=fh/nh
        rates=[pl if c<T else ph for c in caps];L=_ll(rates,rows)
        if best is None or L>best[0]:best=(L,T,pl,ph)
    L,T,pl,ph=best
    out["HARD_STEP"]={"k":3,"loglik":L,"aic":6-2*L,"T":T,"p_low":pl,"p_high":ph}
    # smooth sigmoid with constrained transformed parameters
    x=np.asarray(caps,float)
    def nll(th):
        pL=expit(th[0]);gap=expit(th[1])*(1-pL);pH=pL+gap
        c0=8+24*expit(th[2]);w=math.exp(th[3])
        ps=pL+(pH-pL)*expit((x-c0)/w)
        return -_ll(ps,rows)
    fit=minimize(nll,np.array([-4.,-2.,0.,math.log(4.)]),method="BFGS")
    th=fit.x;pL=expit(th[0]);pH=pL+expit(th[1])*(1-pL);c0=8+24*expit(th[2]);w=math.exp(th[3])
    L=-float(fit.fun)
    out["SMOOTH_SIGMOID"]={"k":4,"loglik":L,"aic":8-2*L,
      "p_low":float(pL),"p_high":float(pH),"c0":float(c0),"w":float(w)}
    llc=0.
    for r in rows:
        pp=r["failures"]/r["n"] if r["n"] else .5;llc+=_ll([pp],[r])
    out["CATEGORICAL"]={"k":len(caps),"loglik":llc,"aic":2*len(caps)-2*llc}
    return out

def analyze(spec,trials):
    expected={(b,i) for b in range(spec["runner_blocks"]) for i in range(spec["identities_per_block"])}
    if {(int(t["block"]),int(t["identity"])) for t in trials}!=expected:raise ValueError("incomplete matrix")
    caps=[int(c) for c in spec["capacities"]]
    valid=[t for t in trials if t["valid"] and t["stratum"]=="LOW"]
    sums={};posts={}
    for c in caps:
        s=_sum([t for t in valid if int(t["capacity_pages"])==c]);sums[str(c)]=s
        posts[str(c)]={"median":float(beta.ppf(.5,s["failures"]+1,s["successes"]+1)),
          "ci95":[float(beta.ppf(.025,s["failures"]+1,s["successes"]+1)),float(beta.ppf(.975,s["failures"]+1,s["successes"]+1))]}
    rows=[sums[str(c)] for c in caps];mods=_models(spec,caps,rows);thr=_posterior_threshold(spec,caps,rows)
    A={k:v["aic"] for k,v in mods.items()};label="UNRESOLVED_TRANSITION"
    if A["HARD_STEP"]<=A["CONSTANT"]-6 and A["HARD_STEP"]<=A["SMOOTH_SIGMOID"]-2 and (thr["ci90"][1]-thr["ci90"][0])<=8:
        label="DISCOVERY_HARD_STEP"
    elif A["SMOOTH_SIGMOID"]<=A["CONSTANT"]-6 and A["SMOOTH_SIGMOID"]<=A["HARD_STEP"]+2 and mods["SMOOTH_SIGMOID"]["w"]>=3:
        label="DISCOVERY_SMOOTH"
    elif A["CATEGORICAL"]<=min(A["HARD_STEP"],A["SMOOTH_SIGMOID"])-6:
        label="DISCOVERY_COMPLEX"
    return {"experiment_id":spec["experiment_id"],"discovery_label":label,
      "by_capacity":sums,"posterior":posts,"models":mods,"threshold_posterior":thr,
      "cpu_mismatches":sum(not t["cpu_match"] for t in trials),
      "other_delta_failures":sum(t["valid"] and t["stratum"]=="LOW" and not t["q64_pass"] and t["first_touch_delta_pages"]!=0 for t in trials),
      "trials":trials}

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
    print(json.dumps({"label":r["discovery_label"],"by_capacity":r["by_capacity"],
      "models":{k:v["aic"] for k,v in r["models"].items()},
      "threshold":r["threshold_posterior"]},sort_keys=True))
if __name__=="__main__":main()
