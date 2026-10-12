#!/usr/bin/env python3
import argparse,json,math,resource,statistics,time
from collections import Counter,defaultdict
from pathlib import Path
CLASSES=['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
def grams(s,nmin=2,nmax=5):
 s='^'+''.join(s.lower().split())+'$'; out=[]
 for n in range(nmin,nmax+1): out.extend(s[i:i+n] for i in range(max(0,len(s)-n+1)))
 return out
def ece(rec):
 z=0.0;n=len(rec)
 for i in range(10):
  b=[x for x in rec if i/10<=x['conf']<(i+1)/10 or (i==9 and x['conf']==1)]
  if b:z+=len(b)/n*abs(sum(x['ok'] for x in b)/len(b)-sum(x['conf'] for x in b)/len(b))
 return z
def main():
 p=argparse.ArgumentParser();p.add_argument('--train',required=True);p.add_argument('--test',required=True);p.add_argument('--out',required=True);p.add_argument('--model-out',required=True);a=p.parse_args()
 train=[json.loads(x) for x in Path(a.train).read_text(encoding='utf-8').splitlines() if x.strip()];test=[json.loads(x) for x in Path(a.test).read_text(encoding='utf-8').splitlines() if x.strip()]
 counts={c:Counter() for c in CLASSES}; totals=Counter(); docs=Counter(); vocab=set()
 for r in train:
  c=r['expected_semantic_outcome']['route'];docs[c]+=1
  for g in grams(r['input']):counts[c][g]+=1;totals[c]+=1;vocab.add(g)
 V=len(vocab);N=len(train); rec=[];lat=[]
 for r in test:
  t=time.perf_counter_ns(); gs=grams(r['input']);scores=[]
  for c in CLASSES:
   s=math.log((docs[c]+1)/(N+len(CLASSES)))
   den=totals[c]+V
   for g in gs:s+=math.log((counts[c][g]+1)/den)
   scores.append(s)
  mx=max(scores);ex=[math.exp(s-mx) for s in scores];sm=sum(ex);pr=[v/sm for v in ex];j=max(range(len(pr)),key=pr.__getitem__);lat.append((time.perf_counter_ns()-t)/1e6)
  exp=r['expected_semantic_outcome']['route'];br=sum((pr[k]-(1 if CLASSES[k]==exp else 0))**2 for k in range(len(CLASSES)))/len(CLASSES)
  rec.append({'id':r['id'],'expected':exp,'predicted':CLASSES[j],'conf':pr[j],'ok':CLASSES[j]==exp,'brier':br})
 model={'kind':'char-ngram-multinomial-nb','nmin':2,'nmax':5,'classes':CLASSES,'docs':dict(docs),'totals':dict(totals),'vocab_size':V,'counts':{c:dict(counts[c]) for c in CLASSES}}
 Path(a.model_out).write_text(json.dumps(model,ensure_ascii=False,separators=(',',':')),encoding='utf-8');mb=Path(a.model_out).stat().st_size
 out={'system':'char-ngram-multinomial-nb','train_rows':N,'attempted':len(rec),'vocab_size':V,'model_bytes':mb,'accuracy':sum(x['ok'] for x in rec)/len(rec),'brier':statistics.mean(x['brier'] for x in rec),'ece':ece(rec),'median_latency_ms':statistics.median(lat),'p95_latency_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'failures':[x for x in rec if not x['ok']]};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='failures'},ensure_ascii=False,indent=2));print('failures',len(out['failures']))
if __name__=='__main__':main()
