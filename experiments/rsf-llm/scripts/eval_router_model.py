#!/usr/bin/env python3
import argparse,json,math,resource,statistics,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM

classes=['authority','deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
letters='ABCDEFGH'
prompt='''Classify the request. Return exactly one letter and no explanation.
A permission-sensitive request that must not be executed automatically
B deterministic calculation/parsing/validation
C local repository or computer task delegated to a harness
D fresh/external information lookup
E small semantic classification/extraction/IR
F complex long reasoning/planning/synthesis
G ambiguous or underspecified
H ordinary conversational explanation or question'''

def encode(tok,text):
    m=[{'role':'system','content':prompt},{'role':'user','content':'Request:\n'+text+'\nAnswer:'}]
    if getattr(tok,'chat_template',None):
        return tok.apply_chat_template(m,tokenize=True,add_generation_prompt=True,return_tensors='pt',return_dict=True)
    return tok(prompt+'\nRequest:\n'+text+'\nAnswer:',return_tensors='pt')

def metrics(records):
    n=len(records)
    acc=sum(r['ok'] for r in records)/n
    br=sum(r['brier'] for r in records)/n
    ec=0.0
    for i in range(10):
        b=[r for r in records if i/10<=r['conf']<(i+1)/10 or (i==9 and r['conf']==1)]
        if b: ec+=len(b)/n*abs(sum(r['ok'] for r in b)/len(b)-sum(r['conf'] for r in b)/len(b))
    return acc,br,ec

def main():
    a=argparse.ArgumentParser();a.add_argument('--model',required=True);a.add_argument('--revision',required=True);a.add_argument('--corpus',required=True);a.add_argument('--out',required=True);x=a.parse_args()
    rows=[json.loads(s) for s in Path(x.corpus).read_text().splitlines() if s.strip()]
    t=time.perf_counter();tok=AutoTokenizer.from_pretrained(x.model,revision=x.revision);tok_s=time.perf_counter()-t
    t=time.perf_counter();model=AutoModelForCausalLM.from_pretrained(x.model,revision=x.revision);model.eval();load_s=time.perf_counter()-t
    ids=[]
    for ch in letters:
        q=tok.encode(ch,add_special_tokens=False)
        if len(q)!=1: raise RuntimeError((ch,q))
        ids.append(q[0])
    rec=[];lat=[]
    with torch.inference_mode():
        for row in rows:
            enc=encode(tok,row['input']);t=time.perf_counter();o=model(**enc);lat.append((time.perf_counter()-t)*1000)
            p=torch.softmax(o.logits[0,-1,ids].float(),dim=0).cpu().tolist();j=max(range(8),key=p.__getitem__)
            expected=row['expected_semantic_outcome']['route'];pred=classes[j];conf=p[j]
            b=sum((p[k]-(1.0 if classes[k]==expected else 0.0))**2 for k in range(8))/8
            rec.append({'id':row['id'],'expected':expected,'predicted':pred,'conf':conf,'ok':pred==expected,'brier':b})
    acc,br,ec=metrics(rec);s=sorted(lat)
    out={'model_id':x.model,'revision':x.revision,'parameters':sum(p.numel() for p in model.parameters()),'dtype':str(next(model.parameters()).dtype),'attempted':len(rec),'accuracy':acc,'brier':br,'ece':ec,'median_latency_ms':statistics.median(lat),'p95_latency_ms':s[math.ceil(.95*len(s))-1],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'tokenizer_load_seconds':tok_s,'model_load_seconds':load_s,'failures':[r for r in rec if not r['ok']]}
    Path(x.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in out if k not in ('failures',)},ensure_ascii=False,indent=2));print('failures',len(out['failures']))
if __name__=='__main__':main()
