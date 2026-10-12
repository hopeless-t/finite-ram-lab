from __future__ import annotations

import argparse, json, os, random, statistics, subprocess, sys, time
from pathlib import Path
from typing import Any

from .fast_reinstall_epoch import make_epoch, verify_epoch
from .fast_reinstall_loop_v2 import build_wheel_isolated
from .template_projection import COLD_CODE, FORK_CODE, WARM_CODE, start_server, server_call, stop, pct


def cold_direct(repo:Path,wheel:Path,epoch:dict[str,Any],seed:int)->dict[str,Any]:
    env=dict(os.environ); env['PYTHONPATH']=str(wheel); env.pop('PYTHONDONTWRITEBYTECODE',None)
    t=time.perf_counter_ns()
    if not verify_epoch(wheel,epoch): raise RuntimeError('artifact epoch changed')
    r=subprocess.run([sys.executable,'-c',COLD_CODE,str(seed)],cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    elapsed=time.perf_counter_ns()-t
    return {'elapsed_ns':elapsed,'payload':json.loads(r.stdout.splitlines()[-1])}

def reprime(repo:Path,wheel:Path,epoch:dict[str,Any],seed:int,code:str)->dict[str,Any]:
    env=dict(os.environ); env['PYTHONPATH']=str(wheel); env.pop('PYTHONDONTWRITEBYTECODE',None)
    total0=time.perf_counter_ns(); p,start_ms,ready=start_server(code,repo,env)
    try:
        call=server_call(p,wheel,epoch,seed)
        total_ns=time.perf_counter_ns()-total0
        return {'elapsed_ns':total_ns,'startup_ms':start_ms,'first_call_ms':call['elapsed_ns']/1e6,'parent_rss_kib':call['parent_rss_kib'],'payload':call['payload'],'ready':ready}
    finally:
        stop(p)

def run(repo:Path,out:Path,*,blocks:int,seed:int)->dict[str,Any]:
    out.mkdir(parents=True,exist_ok=True); wheel,build=build_wheel_isolated(repo,out/'artifacts'); epoch=make_epoch(wheel); rows=[]
    arms=['cold_exec','warm_reprime','fork_reprime']
    for block in range(blocks):
        s=seed+block; order=list(arms); random.Random(seed+block*6151).shuffle(order); hashes={}
        for pos,arm in enumerate(order):
            if arm=='cold_exec': r=cold_direct(repo,wheel,epoch,s)
            elif arm=='warm_reprime': r=reprime(repo,wheel,epoch,s,WARM_CODE)
            else: r=reprime(repo,wheel,epoch,s,FORK_CODE)
            hashes[arm]=r['payload']['semantic_sha256']; rows.append({'block':block,'order':pos,'arm':arm,'seed':s,**r})
        if len(set(hashes.values()))!=1: raise RuntimeError(f'semantic mismatch {block}')
    summary={}
    for arm in arms:
        g=[r for r in rows if r['arm']==arm]; ms=[r['elapsed_ns']/1e6 for r in g]
        d={'n':len(g),'median_ready_to_result_ms':float(statistics.median(ms)),'p95_ms':pct(ms,.95),'min_ms':float(min(ms)),'max_ms':float(max(ms))}
        if arm!='cold_exec':
            d['median_startup_ms']=float(statistics.median(r['startup_ms'] for r in g)); d['median_first_call_ms']=float(statistics.median(r['first_call_ms'] for r in g)); d['median_parent_rss_kib']=float(statistics.median(r['parent_rss_kib'] for r in g)); d['counter_unique']=sorted(set(r['payload']['request_counter'] for r in g))[:10]
        summary[arm]=d
    cold=summary['cold_exec']['median_ready_to_result_ms']
    for arm in ['warm_reprime','fork_reprime']:
        summary[arm]['ratio_vs_cold']=summary[arm]['median_ready_to_result_ms']/cold
        summary[arm]['delta_vs_cold_ms']=summary[arm]['median_ready_to_result_ms']-cold
    result={'experiment_id':'FRL-REINSTALL-006-REPRIME-EVICTION-v1','blocks':blocks,'semantic_triplets_match':True,'canonical_build_residue_delta_bytes':build['canonical_residue_delta_bytes'],'arms':summary,'interpretation_gate':{'reprime_within_10pct_of_cold':min(summary['warm_reprime']['ratio_vs_cold'],summary['fork_reprime']['ratio_vs_cold'])<=1.10}}
    (out/'trials.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows)); (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',default='.'); p.add_argument('--out',required=True); p.add_argument('--blocks',type=int,default=30); p.add_argument('--seed',type=int,default=20261012); a=p.parse_args(); print(json.dumps(run(Path(a.repo).resolve(),Path(a.out).resolve(),blocks=a.blocks,seed=a.seed),indent=2,sort_keys=True))
if __name__=='__main__': main()
