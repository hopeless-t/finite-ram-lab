#!/usr/bin/env python3
import json,glob,math
rows=[]
for p in glob.glob('experiments/rsf-llm/results/*.json'):
 try:r=json.load(open(p))
 except Exception:continue
 if 'accuracy' not in r:continue
 rows.append({'file':p,'system':r.get('model_id',r.get('system')),'accuracy':r['accuracy'],'brier':r.get('brier'),'ece':r.get('ece'),'latency_ms':r.get('median_latency_ms'),'rss_mib':r.get('peak_rss_bytes',0)/1048576,'params':r.get('parameters',0),'prompt':r.get('prompt')})
rows.sort(key=lambda x:(-x['accuracy'],x['rss_mib']))
for x in rows:print(json.dumps(x,ensure_ascii=False))
