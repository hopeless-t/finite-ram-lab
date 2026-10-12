#!/usr/bin/env python3
import argparse,json,math,resource,statistics,time
from collections import Counter
from pathlib import Path
C=['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
def grams(s):
 s='^'+''.join(s.lower().split())+'$';return [s[i:i+n] for n in range(2,6) for i in range(max(0,len(s)-n+1))]
def fit(rows):
 cnt={c:Counter() for c in C};tot=Counter();docs=Counter();v=set()
 for r in rows:
  c=r['expected_semantic_outcome']['route'];docs[c]+=1
  for g in grams(r['input']):cnt[c][g]+=1;tot[c]+=1;v.add(g)
 return cnt,tot,docs,v
def logits(text,m):
 cnt,tot,docs,v=m;V=len(v);N=sum(docs.values());out=[]
 for c in C:
  s=math.log((docs[c]+1)/(N+len(C)));den=tot[c]+V
  for g in grams(text):s+=math.log((cnt[c][g]+1)/den)
  out.append(s)
 return out
def probs(ls,T):
 mx=max(ls);e=[math.exp((x-mx)/T) for x in ls];z=sum(e);return [x/z for x in e]
def nll(rows,m,T):
 z=0
 for r in rows:
  p=probs(logits(r['input'],m),T);j=C.index(r['expected_semantic_outcome']['route']);z-=math.log(max(p[j],1e-15))
 return z/len(rows)
def ece(rec):
 n=len(rec);z=0
 for i in range(10):
  b=[r for r in rec if i/10<=r['conf']<(i+1)/10 or (i==9 and r['conf']==1)]
  if b:z+=len(b)/n*abs(sum(r['ok'] for r in b)/len(b)-sum(r['conf'] for r in b)/len(b))
 return z
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--test',required=True);ap.add_argument('--out',required=True);ap.add_argument('--model-out',required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in Path(a.source).read_text(encoding='utf-8').splitlines() if x.strip()];by={c:[] for c in C}
 for r in rows:by[r['expected_semantic_outcome']['route']].append(r)
 train=sum((by[c][:8] for c in C),[]);cal=sum((by[c][8:10] for c in C),[]);m=fit(train)
 grid=[0.25,0.5,0.75,1,1.5,2,3,4,6,8,12,16,24,32];vals=[(nll(cal,m,T),T) for T in grid];best_nll,T=min(vals)
 test=[json.loads(x) for x in Path(a.test).read_text(encoding='utf-8').splitlines() if x.strip()];rec=[];lat=[]
 for r in test:
  t=time.perf_counter_ns();p=probs(logits(r['input'],m),T);j=max(range(len(C)),key=p.__getitem__);lat.append((time.perf_counter_ns()-t)/1e6);exp=r['expected_semantic_outcome']['route'];br=sum((p[k]-(1 if C[k]==exp else 0))**2 for k in range(len(C)))/len(C);rec.append({'id':r['id'],'expected':exp,'predicted':C[j],'conf':p[j],'ok':C[j]==exp,'brier':br})
 cnt,tot,docs,v=m;model={'kind':'char-ngram-multinomial-nb-temperature','temperature':T,'train_rows':len(train),'calibration_rows':len(cal),'calibration_nll':best_nll,'docs':dict(docs),'totals':dict(tot),'vocab_size':len(v),'counts':{c:dict(cnt[c]) for c in C}};Path(a.model_out).write_text(json.dumps(model,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 coverage={};
 for th in [0.2,0.25,0.3,0.35,0.4,0.5,0.6,0.7,0.8,0.9]:
  accpt=[r for r in rec if r['conf']>=th];coverage[str(th)]={'coverage':len(accpt)/len(rec),'selective_accuracy':sum(r['ok'] for r in accpt)/len(accpt) if accpt else None,'escalation_rate':1-len(accpt)/len(rec),'accepted':len(accpt)}
 out={'system':'char-ngram-nb-tempcal','train_rows':len(train),'calibration_rows':len(cal),'temperature':T,'calibration_nll':best_nll,'attempted':len(rec),'model_bytes':Path(a.model_out).stat().st_size,'accuracy':sum(r['ok'] for r in rec)/len(rec),'brier':statistics.mean(r['brier'] for r in rec),'ece':ece(rec),'median_latency_ms':statistics.median(lat),'p95_latency_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'coverage':coverage,'failures':[r for r in rec if not r['ok']]};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='failures'},ensure_ascii=False,indent=2));print('failures',len(out['failures']))
if __name__=='__main__':main()
