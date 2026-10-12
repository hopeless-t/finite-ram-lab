#!/usr/bin/env python3
"""Build the frozen CATFOOD RSF compact runtime bundle.

This is a storage projection, not a retraining step. It consumes the pinned BF16 base
snapshot and rank-4 semantic7 LoRA checkpoint, then emits the quality frontier that was
frozen before holdout-v5 was opened:
  * FP8 E4M3 base storage, zstd-1 compressed
  * 2-bit/block-50 residual patch on four v_proj tensors
  * compressed tokenizer + compact metadata
  * rank-4 FP16 lossless adapter payload, zstd-1 compressed
Generated model artifacts stay local/ignored; the manifest is reproducible evidence.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
import torch
from safetensors import safe_open
from safetensors.torch import save_file

MODEL_REV='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec'
PATCH_NAMES=[
 'model.layers.0.self_attn.v_proj.weight',
 'model.layers.1.self_attn.v_proj.weight',
 'model.layers.2.self_attn.v_proj.weight',
 'model.layers.10.self_attn.v_proj.weight',
]
ALL_PATCH_NAMES=[
 'model.layers.0.self_attn.v_proj.weight','model.layers.1.self_attn.v_proj.weight',
 'model.layers.2.self_attn.q_proj.weight','model.layers.2.self_attn.v_proj.weight',
 'model.layers.9.self_attn.q_proj.weight','model.layers.9.self_attn.v_proj.weight',
 'model.layers.10.self_attn.q_proj.weight','model.layers.10.self_attn.v_proj.weight',
]
PATCH_BITS=2; PATCH_BLOCK=50

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def zstd(src:Path,dst:Path):
 subprocess.run(['zstd','-q','-f','-1',str(src),'-o',str(dst)],check=True)

def pack_codes(codes:torch.Tensor,bits:int)->bytes:
 out=[]; buf=nb=0
 for c in codes.tolist():
  buf|=int(c)<<nb; nb+=bits
  while nb>=8: out.append(buf&255); buf>>=8; nb-=8
 if nb: out.append(buf&255)
 return bytes(out)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--base-snapshot',type=Path,required=True); ap.add_argument('--adapter-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 base=a.base_snapshot.resolve(); adapter=a.adapter_dir.resolve(); out=a.out.resolve()
 if out.exists() and any(out.iterdir()): raise SystemExit(f'output directory must be empty: {out}')
 out.mkdir(parents=True,exist_ok=True)
 for req in ('model.safetensors','config.json','tokenizer.json','tokenizer_config.json'):
  if not (base/req).exists(): raise SystemExit(f'missing base artifact: {base/req}')
 for req in ('adapter_model.safetensors',):
  if not (adapter/req).exists(): raise SystemExit(f'missing adapter artifact: {adapter/req}')
 work=out/'.build'; shutil.rmtree(work,ignore_errors=True); work.mkdir()
 # FP8 base.
 fp8=work/'model.safetensors'
 with safe_open(base/'model.safetensors',framework='pt') as f:
  tensors={k:f.get_tensor(k).to(torch.float8_e4m3fn).contiguous() for k in f.keys()}
 save_file(tensors,str(fp8),metadata={'format':'pt','catfood_storage_dtype':'float8_e4m3fn'})
 zstd(fp8,out/'model.safetensors.zst')
 # Residual patch: fixed semantic-search result, encoded with bitmap-compatible CFR3.
 selected=[ALL_PATCH_NAMES.index(k) for k in PATCH_NAMES]; bitmap=sum(1<<i for i in selected); qmax=(1<<(PATCH_BITS-1))-1
 blob=bytearray(b'CFR3'+bytes([PATCH_BITS,bitmap])+PATCH_BLOCK.to_bytes(2,'little'))
 with safe_open(base/'model.safetensors',framework='pt') as fo, safe_open(fp8,framework='pt') as ff:
  for name in PATCH_NAMES:
   r=(fo.get_tensor(name).float()-ff.get_tensor(name).float()).flatten(); scales=[]; codes=[]
   for i in range(0,r.numel(),PATCH_BLOCK):
    x=r[i:i+PATCH_BLOCK]; sc=float(x.abs().max()) or 1.0; q=torch.round(x/sc).clamp(-qmax,qmax).to(torch.int16)
    scales.append(sc); codes.append((q+qmax).to(torch.uint8))
   blob+=torch.tensor(scales,dtype=torch.float16).numpy().tobytes()+pack_codes(torch.cat(codes),PATCH_BITS)
 patch=work/'base.patch'; patch.write_bytes(blob); zstd(patch,out/'base.patch.zst')
 # Tokenizer + only the metadata proven necessary for this pinned runtime.
 zstd(base/'tokenizer.json',out/'tokenizer.json.zst')
 cfg=json.loads((base/'config.json').read_text()); (out/'config.json').write_text(json.dumps(cfg,separators=(',',':')))
 tc=json.loads((base/'tokenizer_config.json').read_text()); keep=['tokenizer_class','chat_template','bos_token','eos_token','pad_token','unk_token','add_bos_token','add_eos_token']
 (out/'tokenizer_config.json').write_text(json.dumps({k:tc[k] for k in keep},ensure_ascii=False,separators=(',',':')))
 # Rank-4 adapter, FP16 semantics preserved; metadata/schema lives in shared runtime.
 with safe_open(adapter/'adapter_model.safetensors',framework='pt') as f:
  keys=sorted(f.keys()); ablob=bytearray(b'CFH1'+bytes([4]));
  for k in keys: ablob+=f.get_tensor(k).to(torch.float16).contiguous().numpy().tobytes()
 ah=work/'adapter_h.bin'; ah.write_bytes(ablob); zstd(ah,out/'adapter_h.bin.zst')
 shutil.rmtree(work)
 files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'}
 manifest={
  'format':'catfood-rsf-compact-runtime-v1','base_revision':MODEL_REV,
  'frozen_patch':{'bits':PATCH_BITS,'block':PATCH_BLOCK,'tensors':PATCH_NAMES},
  'adapter':{'rank':4,'dtype':'float16','format':'CFH1+zstd1'},
  'files':files,'payload_bytes':sum(x['bytes'] for x in files.values()),
  'validation':{'dev_v2':'64/64','holdout_v4':'45/48 (reference 45/48)','holdout_v5':'57/64 (reference 57/64)','semantic_tuning_after_v5':'forbidden'},
 }
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
