#!/usr/bin/env python3
import argparse,json,math,resource,statistics,time
from collections import Counter
from pathlib import Path

CLASSES=['authority','deterministic','harness','retrieval','residual']
RESIDUAL={'tiny_model','larger_model','unknown','ordinary'}
def y(row):
 r=row['expected_semantic_outcome']['route'];return 'residual' if r in RESIDUAL else r
def grams(s):
 s='^'+''.join(s.lower().split())+'$';return [s[i:i+n] for n in range(2,6) for i in range(max(0,len(s)-n+1))]
def split(rows):
 by={c:[] for c in ['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']}
 for r in rows:by[r['expected_semantic_outcome']['route']].append(r)
 tr=[];cal=[]
 for c,rs in by.items():tr+=rs[:8];cal+=rs[8:10]
 return tr,cal
def fit(rows):
 cnt={c:Counter() for c in CLASSES};tot=Counter();v=set()
 for r in rows:
  c=y(r)
  for g in grams(r['input']):cnt[c][g]+=1;tot[c]+=1;v.add(g)
 return cnt,tot,v
def logits(text,m):
 cnt,tot,v=m;V=len(v);out=[]
 for c in CLASSES:
  den=tot[c]+V;s=-math.log(len(CLASSES))
  for g in grams(text):s+=math.log((cnt[c][g]+1)/den)
  out.append(s)
 return out
def probs(ls,T):
 m=max(ls);e=[math.exp((x-m)/T) for x in ls];z=sum(e);return [x/z for x in e]
def nll(rows,m,T):
 z=0
 for r in rows:
  p=probs(logits(r['input'],m),T);z-=math.log(max(p[CLASSES.index(y(r))],1e-15))
 return z/len(rows)
def ece(rec):
 n=len(rec);o=0
 for i in range(10):
  b=[r for r in rec if i/10<=r['confidence']<(i+1)/10 or (i==9 and r['confidence']==1)]
  if b:o+=len(b)/n*abs(sum(r['correct'] for r in b)/len(b)-sum(r['confidence'] for r in b)/len(b))
 return o

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--test',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 src=[json.loads(x) for x in Path(a.source).read_text(encoding='utf-8').splitlines() if x.strip()];tr,cal=split(src);m=fit(tr);grid=[.25,.5,.75,1,1.5,2,3,4,6,8,12,16,24,32];cal_nll,T=min((nll(cal,m,t),t) for t in grid)
 test=[json.loads(x) for x in Path(a.test).read_text(encoding='utf-8').splitlines() if x.strip()];rec=[];lat=[]
 for r in test:
  t=time.perf_counter_ns();p=probs(logits(r['input'],m),T);j=max(range(5),key=p.__getitem__);lat.append((time.perf_counter_ns()-t)/1e6);exp=y(r);br=sum((p[k]-(1 if CLASSES[k]==exp else 0))**2 for k in range(5))/5;rec.append({'id':r['id'],'original_expected':r['expected_semantic_outcome']['route'],'expected':exp,'predicted':CLASSES[j],'confidence':p[j],'correct':CLASSES[j]==exp,'brier':br,'probs':dict(zip(CLASSES,p))})
 out={'system':'char-ngram-nb-externalizer-v0','classes':CLASSES,'train_rows':len(tr),'calibration_rows':len(cal),'temperature':T,'calibration_nll':cal_nll,'attempted':len(rec),'accuracy':sum(r['correct'] for r in rec)/len(rec),'brier':statistics.mean(r['brier'] for r in rec),'ece':ece(rec),'median_latency_ms':statistics.median(lat),'p95_latency_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'records':rec};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='records'},ensure_ascii=False,indent=2));
 for c in CLASSES:
  z=[r for r in rec if r['expected']==c];print(c,sum(r['correct'] for r in z),'/',len(z))
if __name__=='__main__':main()
