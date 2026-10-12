#!/usr/bin/env python3
import argparse,json,math,statistics,time
from pathlib import Path
from shoal_runtime import ShoalRouter
ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--adapter',default='.work/rsf-llm/llm-jp-150m-semantic7-lora-v1'); ap.add_argument('--temperature',type=float,default=0.5); ap.add_argument('--out',required=True); a=ap.parse_args()
rows=[json.loads(x) for x in Path(a.data).read_text(encoding='utf-8').splitlines() if x.strip()]
r=ShoalRouter(a.adapter,temperature=a.temperature); rec=[]; t0=time.perf_counter()
for x in rows:
    d=r.route(x['input']); exp=x['expected_semantic_outcome']['route']; rec.append({'id':x['id'],'expected':exp,'predicted':d.route,'correct':d.route==exp,'confidence':d.confidence,'source':d.source,'signals':list(d.signals)})
summary={'rows':len(rec),'accuracy':sum(x['correct'] for x in rec)/len(rec),'wall_seconds':time.perf_counter()-t0,'by_source':{},'by_expected':{},'failures':[x for x in rec if not x['correct']]}
for s in sorted(set(x['source'] for x in rec)):
 z=[x for x in rec if x['source']==s]; summary['by_source'][s]={'n':len(z),'accuracy':sum(x['correct'] for x in z)/len(z)}
for s in sorted(set(x['expected'] for x in rec)):
 z=[x for x in rec if x['expected']==s]; summary['by_expected'][s]={'n':len(z),'accuracy':sum(x['correct'] for x in z)/len(z)}
Path(a.out).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({k:summary[k] for k in ('rows','accuracy','wall_seconds','by_source','by_expected')},ensure_ascii=False,indent=2)); print('failures',len(summary['failures']))
