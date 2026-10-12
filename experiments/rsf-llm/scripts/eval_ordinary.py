#!/usr/bin/env python3
import argparse,json,resource,time
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoConfig,AutoModelForCausalLM,AutoModelForImageTextToText

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--revision',required=True);p.add_argument('--corpus',required=True);p.add_argument('--out',required=True);p.add_argument('--max-new',type=int,default=64);a=p.parse_args()
 rows=[json.loads(x) for x in Path(a.corpus).read_text(encoding='utf-8').splitlines() if x.strip()]
 tok=AutoTokenizer.from_pretrained(a.model,revision=a.revision);cfg=AutoConfig.from_pretrained(a.model,revision=a.revision)
 model=(AutoModelForImageTextToText.from_pretrained(a.model,revision=a.revision,dtype=torch.float32) if cfg.model_type=='qwen3_5' else AutoModelForCausalLM.from_pretrained(a.model,revision=a.revision,dtype=torch.float32));model.eval();rec=[]
 for row in rows:
  msgs=[{'role':'system','content':'日本語で、質問に短く普通に役立つ回答をしてください。'},{'role':'user','content':row['input']}]
  enc=tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,return_tensors='pt',return_dict=True)
  t=time.perf_counter()
  with torch.inference_mode():o=model.generate(**enc,max_new_tokens=a.max_new,do_sample=False)
  txt=tok.decode(o[0][enc['input_ids'].shape[1]:],skip_special_tokens=True).strip();low=txt.lower();groups=[]
  for group in row['must_any']: groups.append(any(str(k).lower() in low for k in group))
  rec.append({'id':row['id'],'input':row['input'],'output':txt,'group_hits':groups,'score':sum(groups)/len(groups),'latency_ms':(time.perf_counter()-t)*1000})
 out={'model_id':a.model,'revision':a.revision,'attempted':len(rec),'ordinary_concept_score':sum(x['score'] for x in rec)/len(rec),'fully_satisfied_rate':sum(all(x['group_hits']) for x in rec)/len(rec),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'records':rec};Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='records'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
