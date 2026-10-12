#!/usr/bin/env python3
import argparse,hashlib,json,time
from pathlib import Path
from shoal_runtime import ShoalRouter
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
mp=ROOT/a.manifest; man=json.loads(mp.read_text(encoding='utf-8'))
if man.get('status')!='sealed_unspent': raise SystemExit(f"refuse: status={man.get('status')}")
hold=ROOT/man['holdout_file']; got=hashlib.sha256(hold.read_bytes()).hexdigest()
if got!=man['holdout_sha256']: raise SystemExit('refuse: hash mismatch')
rows=[json.loads(x) for x in hold.read_text(encoding='utf-8').splitlines() if x.strip()]
router=ShoalRouter('.work/rsf-llm/llm-jp-150m-semantic7-lora-v1',temperature=.5,min_confidence=.8)
def stats(rec):
 out={'rows':len(rec),'accuracy':sum(x['correct'] for x in rec)/len(rec),'by_expected':{},'by_source':{},'failures':[x for x in rec if not x['correct']]}
 for k in sorted({x['expected'] for x in rec}):
  z=[x for x in rec if x['expected']==k]; out['by_expected'][k]={'n':len(z),'accuracy':sum(x['correct'] for x in z)/len(z)}
 for k in sorted({x['source'] for x in rec}):
  z=[x for x in rec if x['source']==k]; out['by_source'][k]={'n':len(z),'accuracy':sum(x['correct'] for x in z)/len(z)}
 return out
hy=[]; t0=time.perf_counter()
for r in rows:
 d=router.route(r['input']); exp=r['expected_semantic_outcome']['route']; hy.append({'id':r['id'],'expected':exp,'predicted':d.route,'correct':d.route==exp,'confidence':d.confidence,'source':d.source,'signals':list(d.signals)})
h=stats(hy); h['wall_seconds']=time.perf_counter()-t0; h['model_active_rows']=sum(x['source'] not in ('0b_single_signal','policy_guard') for x in hy); h['model_active_fraction']=h['model_active_rows']/len(hy)
mo=[]; t1=time.perf_counter()
for r in rows:
 exp=r['expected_semantic_outcome']['route']
 if router._authority(r['input']): pred,conf,source='authority',1.0,'policy_guard'
 else: pred,conf,_=router._model(r['input']); source='semantic7_only'
 mo.append({'id':r['id'],'expected':exp,'predicted':pred,'correct':pred==exp,'confidence':conf,'source':source})
m=stats(mo); m['wall_seconds']=time.perf_counter()-t1
res={'protocol':man['protocol']+'-first-and-final','holdout_sha256':got,'evaluated_unix':int(time.time()),'hybrid_shoal':h,'policy_plus_semantic7_only':m,'frozen_config':{'adapter':'.work/rsf-llm/llm-jp-150m-semantic7-lora-v1','temperature':.5,'min_confidence':.8,'authority_externalized':True,'lazy_load':True,'calculator_0b':True},'rule_after_eval':'This holdout is spent; tune only against a newly sealed next holdout.'}
out=ROOT/a.out; out.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
man['status']='spent'; man['evaluated_unix']=res['evaluated_unix']; man['result_file']=str(out.relative_to(ROOT)); mp.write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'hybrid_accuracy':h['accuracy'],'model_active_fraction':h['model_active_fraction'],'hybrid_by_expected':h['by_expected'],'hybrid_by_source':h['by_source'],'hybrid_failures':len(h['failures']),'policy_plus_semantic7_only_accuracy':m['accuracy'],'model_only_failures':len(m['failures']),'status':'spent'},ensure_ascii=False,indent=2))
