#!/usr/bin/env python3
import argparse, json, math, os, re, subprocess, tempfile, time
from dataclasses import dataclass
from pathlib import Path
from finite_ram_control import ByteBudgetGovernor, resource_snapshot


MODEL='llm-jp/llm-jp-3-150m-instruct3'
REV='5be263e1a3613cd5c163f41ad828c8de6a2aa6ec'
REPO_ROOT=Path(__file__).resolve().parents[3]
DEFAULT_ADAPTER=REPO_ROOT/'.work'/'rsf-llm'/'llm-jp-150m-semantic7-lora-v1'
DEFAULT_GOV_STATE=REPO_ROOT/'.work'/'rsf-llm'/'resource-governor-state.json'

def _read_payload(path):
    p=Path(path)
    if p.suffix=='.zst': return subprocess.run(['zstd','-q','-d','-c',str(p)],capture_output=True,check=True).stdout
    return p.read_bytes()
CLASSES=['deterministic','harness','retrieval','tiny_model','larger_model','unknown','ordinary']
LETTERS='ABCDEFG'
PROMPT='''AuthorityはMVCA側で別判定します。依頼のsemantic intentだけを7分類し、説明せずA〜Gの1文字だけ返してください。\nA 決定論的な計算・構文検査・変換。\nB ローカルPCやrepositoryをHarnessで扱う。\nC 最新・外部情報を検索取得。\nD 短い意味分類・抽出・Canonical IR化。\nE 長い推論・計画・複雑な統合。\nF 情報不足・曖昧なのでUNKNOWN。\nG 普通の質問への説明・会話。'''

AUTHORITY=[
    r'送金',r'振込',r'資金移動',r'借入',r'投資(?:注文|を|へ|$)',r'秘密(?:鍵|情報)',r'認証(?:情報|トークン)',
    r'なりすま',r'なり代わ',r'本人として',r'金融取引',r'株(?:式)?(?:注文|を買|を購入)',r'契約(?:へ|を|同意)',r'有料契約',r'第三者へ(?:送|渡)',r'公開(?:チャネル|repository).*秘密',r'(?:秘密|private).*?(?:API.?key|APIキー|credential|token|トークン)',r'(?:API.?key|APIキー|credential|token|トークン).*?(?:公開|外へ|送|貼)',r'有料購入'
]
SIGNALS={
'deterministic':[r'計算',r'換算',r'変換',r'構文',r'parse',r'正規表現',r'括弧',r'昇順',r'二進',r'十進',r'16進',r'SHA-?256',r'base64',r'列数',r'(?:秒|分|時間).*?(?:秒|分|時間)'],
'harness':[r'ローカル',r'手元.*git status',r'git\s+status.*(?:取得|確認|見て|観測)',r'pwd.*(?:確認|取得|観測)',r'HEAD.*(?:SHA|取得|確認|観測|取って)',r'[A-Za-z0-9_./-]+\.(?:md|txt|json|jsonl|py|sh|yaml|yml|toml|csv|log).*(?:byte|バイト|サイズ|更新日時)',r'GAYA',r'repositor',r'\brepo\b',r'worktree',r'(?:branch|HEAD).*(?:確認|差分|変更|名|取得)',r'checkpoint.*(?:一覧|サイズ|確認|取得)',r'build',r'test',r'lint',r'script.*実行',r'フォルダ.*(?:容量|使用量)',r'directory.*容量',r'repo内'],
'retrieval':[r'今日',r'最新',r'一次情報',r'現在の公式',r'support matrix',r'公式(?:サイト|ドキュメント|発表|情報|status|リリース)',r'remote',r'現在公開',r'配布元',r'価格',r'利用規約',r'ライセンス',r'発表年',r'サポート終了',r'API仕様'],
'tiny_model':[r'分類して',r'抽出して',r'抜き出して',r'正規化',r'canonical',r'二値',r'二択',r'だけ判定',r'判定して',r'返して',r'だけ抜いて',r'対象名',r'だけ構造化',r'動詞と対象',r'severity'],
'larger_model':[r'統合して',r'総合比較',r'研究方針',r'ロードマップ',r'反証',r'設計し直',r'新仮説',r'因果仮説',r'長期運用',r'優先順位',r'共通設計原理',r'研究プログラム',r'総括して',r'再利用可能な原理',r'複数repo.*成果'],
'ordinary':[r'とは(?:何|どう)',r'って何',r'違い(?:を|は)',r'説明して',r'教えて',r'なぜ',r'長所と短所',r'ざっくり',r'何が変わる',r'使い分け',r'初心者向け']}

@dataclass
class Decision:
    route:str
    confidence:float
    source:str
    handoff:str
    authority:str='allowed'
    signals:tuple=()

class ShoalRouter:
    def __init__(self, adapter_dir, temperature=1.5, min_confidence=0.80, governor=None):
        self.temperature=temperature; self.min_confidence=min_confidence; self.adapter_dir=adapter_dir
        state=DEFAULT_GOV_STATE
        self.governor=governor or ByteBudgetGovernor(state_path=state)
        self.last_admission=None
        self.tok=None; self.model=None; self.cand=None; self.prefix_ids=None; self.prefix_cache=None
    def _authority(self,text):
        return any(re.search(p,text,re.I) for p in AUTHORITY)
    def _signals(self,text):
        found=[k for k,patterns in SIGNALS.items() if any(re.search(p,text,re.I) for p in patterns)]
        norm=text.translate(str.maketrans('０１２３４５６７８９×÷','0123456789*/'))
        if re.search(r'(?<![A-Za-z0-9_])(?:\(?\s*)?\d+(?:\.\d+)?\s*[+*/-]\s*\d+(?:\.\d+)?',norm) and 'deterministic' not in found:
            found.append('deterministic')
        return tuple(found)
    def _ensure_model(self):
        if self.model is not None: return
        import torch
        from peft import LoraConfig, PeftConfig, PeftModel, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
        source=os.environ.get('CATFOOD_BASE_MODEL',MODEL); src_kw={'revision':REV} if source==MODEL else {}; archive=os.environ.get('CATFOOD_BASE_ZST')
        if archive:
            parent=Path(archive).parent; tmp_root='/dev/shm' if Path('/dev/shm').is_dir() else None
            with tempfile.TemporaryDirectory(prefix='catfood-base-',dir=tmp_root) as td:
                td=Path(td)
                for name in ('config.json','generation_config.json','tokenizer_config.json','special_tokens_map.json'):
                    if (parent/name).exists(): (td/name).symlink_to((parent/name).resolve())
                if (parent/'tokenizer.json.zst').exists():
                    with (td/'tokenizer.json').open('wb') as out: subprocess.run(['zstd','-q','-d','-c',str(parent/'tokenizer.json.zst')],stdout=out,check=True)
                elif (parent/'tokenizer.json').exists(): (td/'tokenizer.json').symlink_to((parent/'tokenizer.json').resolve())
                tok=AutoTokenizer.from_pretrained(td)
                with (td/'model.safetensors').open('wb') as out: subprocess.run(['zstd','-q','-d','-c',archive],stdout=out,check=True)
                base=AutoModelForCausalLM.from_pretrained(td,dtype=torch.float32)
        else:
            tok=AutoTokenizer.from_pretrained(source,**src_kw); base=AutoModelForCausalLM.from_pretrained(source,dtype=torch.float32,**src_kw)
        tok.padding_side='left'; tok.pad_token=tok.pad_token or tok.eos_token
        patch=os.environ.get('CATFOOD_BASE_PATCH')
        if patch:
            raw=_read_payload(patch); magic=raw[:4]; assert magic in (b'CFR1',b'CFR2',b'CFR3'); bits=raw[4]; qmax=(1<<(bits-1))-1; off=5; mask=(1<<bits)-1
            names=['model.layers.0.self_attn.v_proj.weight','model.layers.1.self_attn.v_proj.weight','model.layers.2.self_attn.q_proj.weight','model.layers.2.self_attn.v_proj.weight','model.layers.9.self_attn.q_proj.weight','model.layers.9.self_attn.v_proj.weight','model.layers.10.self_attn.q_proj.weight','model.layers.10.self_attn.v_proj.weight']; params=dict(base.named_parameters())
            if magic==b'CFR3':
                bitmap=raw[off]; off+=1; selected=[i for i in range(len(names)) if bitmap&(1<<i)]; block=int.from_bytes(raw[off:off+2],'little'); off+=2
            else:
                nk=raw[off]; off+=1; selected=list(range(nk)); block=int.from_bytes(raw[off:off+2],'little') if magic==b'CFR2' else 0; off+=2 if magic==b'CFR2' else 0
            global_scales=None
            if magic==b'CFR1': global_scales=torch.frombuffer(bytearray(raw[off:off+2*len(selected)]),dtype=torch.float16).float(); off+=2*len(selected)
            with torch.no_grad():
                for j,idx in enumerate(selected):
                    k=names[idx]; n=params[k].numel()
                    if magic in (b'CFR2',b'CFR3'): ns=(n+block-1)//block; scales=torch.frombuffer(bytearray(raw[off:off+2*ns]),dtype=torch.float16).float(); off+=2*ns
                    nb=(n*bits+7)//8; packed=raw[off:off+nb]; off+=nb; vals=[]; buf=have=0
                    for byte in packed:
                        buf|=int(byte)<<have; have+=8
                        while have>=bits: vals.append((buf&mask)-qmax); buf>>=bits; have-=bits
                    q=torch.tensor(vals[:n],dtype=params[k].dtype)
                    if magic in (b'CFR2',b'CFR3'): q*=scales.repeat_interleave(block)[:n].to(q.dtype)
                    else: q*=float(global_scales[j])
                    params[k].add_(q.reshape(params[k].shape))
        adapter=Path(self.adapter_dir)
        if (adapter/'adapter_h.bin').exists() or (adapter/'adapter_h.bin.zst').exists() or (adapter/'adapter_q.bin').exists() or (adapter/'adapter_q.bin.zst').exists() or (adapter/'adapter_q.safetensors').exists() or (adapter/'adapter_int4.safetensors').exists() or (adapter/'adapter_int8.safetensors').exists():
            from peft.utils.save_and_load import get_peft_model_state_dict, set_peft_model_state_dict
            from safetensors import safe_open
            hpath=(adapter/'adapter_h.bin') if (adapter/'adapter_h.bin').exists() else (adapter/'adapter_h.bin.zst'); hraw=_read_payload(hpath) if hpath.exists() else None
            qpath=(adapter/'adapter_q.bin') if (adapter/'adapter_q.bin').exists() else (adapter/'adapter_q.bin.zst'); qraw=_read_payload(qpath) if qpath.exists() else None; qmagic=qraw[:4] if qraw else b''
            if hraw is not None:
                assert hraw[:4]==b'CFH1'; rank=hraw[4]; cfg=LoraConfig(task_type='CAUSAL_LM',r=rank,lora_alpha=2*rank,target_modules=['q_proj','v_proj'],bias='none',inference_mode=True)
            elif qmagic in (b'CFQ2',b'CFQ3'):
                rank=qraw[5]; cfg=LoraConfig(task_type='CAUSAL_LM',r=rank,lora_alpha=2*rank,target_modules=['q_proj','v_proj'],bias='none',inference_mode=True)
            else: cfg=PeftConfig.from_pretrained(adapter)
            model=get_peft_model(base,cfg); state={}
            if hraw is not None:
                targets=get_peft_model_state_dict(model); off=5
                for k in sorted(targets):
                    n=targets[k].numel(); nb=2*n; state[k]=torch.frombuffer(bytearray(hraw[off:off+nb]),dtype=torch.float16).float().reshape(targets[k].shape); off+=nb
            elif qraw is not None:
                targets=get_peft_model_state_dict(model); keys=sorted(targets); raw=qraw; assert raw[:4] in (b'CFQ1',b'CFQ2',b'CFQ3'); bits=raw[4]; qmax=(1<<(bits-1))-1; off=6 if raw[:4] in (b'CFQ2',b'CFQ3') else 5
                if raw[:4]==b'CFQ3': scales=torch.frombuffer(bytearray(raw[off:off+len(keys)]),dtype=torch.uint8).view(torch.float8_e5m2).float(); off+=len(keys)
                else: scales=torch.frombuffer(bytearray(raw[off:off+2*len(keys)]),dtype=torch.float16).float(); off+=2*len(keys)
                mask=(1<<bits)-1
                for i,k in enumerate(keys):
                    n=targets[k].numel(); nb=(n*bits+7)//8; packed=raw[off:off+nb]; off+=nb; vals=[]; buf=have=0
                    for byte in packed:
                        buf|=int(byte)<<have; have+=8
                        while have>=bits: vals.append((buf&mask)-qmax); buf>>=bits; have-=bits
                    state[k]=(torch.tensor(vals[:n],dtype=torch.float32)*float(scales[i])).reshape(targets[k].shape)
            elif (adapter/'adapter_q.safetensors').exists():
                targets=get_peft_model_state_dict(model)
                with safe_open(adapter/'adapter_q.safetensors',framework='pt') as f:
                    bits=int(f.metadata()['bits']); qmax=(1<<(bits-1))-1; keys=sorted(k for k in f.keys() if k!='__scales__'); scales=f.get_tensor('__scales__')
                    for i,k in enumerate(keys):
                        packed=f.get_tensor(k).to(torch.uint8).tolist(); vals=[]; buf=nb=0; mask=(1<<bits)-1
                        for byte in packed:
                            buf |= int(byte)<<nb; nb += 8
                            while nb>=bits:
                                vals.append((buf&mask)-qmax); buf >>= bits; nb -= bits
                        n=targets[k].numel(); q=torch.tensor(vals[:n],dtype=torch.float32).reshape(targets[k].shape)
                        scheme=(f.metadata() or {}).get('scheme','tensor')
                        if scheme.startswith('block'):
                            block=int(scheme[5:]); sc=scales[i].float().repeat_interleave(block)[:n].reshape(targets[k].shape); state[k]=q*sc
                        elif scales.ndim==2:
                            sc=scales[i].float(); state[k]=q*(sc[:,None] if '.lora_A.' in k else sc[None,:])
                        else:
                            state[k]=q*float(scales[i])
            elif (adapter/'adapter_int4.safetensors').exists():
                qmeta=json.loads((adapter/'quant.json').read_text())
                with safe_open(adapter/'adapter_int4.safetensors',framework='pt') as f:
                    for k in f.keys():
                        b=f.get_tensor(k).to(torch.uint8); lo=(b&15).to(torch.int8); hi=((b>>4)&15).to(torch.int8); lo=torch.where(lo>=8,lo-16,lo); hi=torch.where(hi>=8,hi-16,hi); q=torch.stack((lo,hi),dim=1).flatten()[:qmeta[k]['numel']]; state[k]=(q.float()*qmeta[k]['scale']).reshape(qmeta[k]['shape'])
            else:
                scales=json.loads((adapter/'scales.json').read_text())
                with safe_open(adapter/'adapter_int8.safetensors',framework='pt') as f:
                    for k in f.keys(): state[k]=f.get_tensor(k).float()*scales[k]
            set_peft_model_state_dict(model,state)
        else:
            model=PeftModel.from_pretrained(base,adapter)
        model.eval()
        self.tok=tok; self.model=model; self.cand=[tok.encode(x,add_special_tokens=False)[0] for x in LETTERS]
        # Finite-RAM shared-prefix residency: discover only the token prefix that is
        # provably identical across varied user texts, then cache its KV state.
        probes=['A','ZZZZZZZZZZZZZZ','前の続きやって','CPUとGPUはどう使い分ける？']
        seqs=[]
        for q in probes:
            msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+q+'\n分類:'}]
            rendered=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
            seqs.append(tok(rendered,return_tensors='pt',add_special_tokens=False).input_ids[0].tolist())
        cp=0
        for i in range(min(map(len,seqs))):
            if len({row[i] for row in seqs}) != 1: break
            cp += 1
        if cp > 0:
            import torch
            prefix=torch.tensor([seqs[0][:cp]],dtype=torch.long)
            with torch.inference_mode(): self.prefix_cache=model(input_ids=prefix,use_cache=True).past_key_values
            self.prefix_ids=seqs[0][:cp]
    def _model(self,text):
        self._ensure_model()
        import torch
        msgs=[{'role':'system','content':PROMPT},{'role':'user','content':'依頼: '+text+'\n分類:'}]
        rendered=self.tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        enc=self.tok(rendered,return_tensors='pt',add_special_tokens=False,truncation=True,max_length=384)
        t0=time.perf_counter()
        with torch.inference_mode():
            use_prefix=(self.prefix_ids is not None and enc.input_ids.shape[1]>len(self.prefix_ids) and enc.input_ids[0,:len(self.prefix_ids)].tolist()==self.prefix_ids)
            if use_prefix:
                import copy
                cache=copy.copy(self.prefix_cache); cache.layers=[copy.copy(layer) for layer in self.prefix_cache.layers]
                logits=self.model(input_ids=enc.input_ids[:,len(self.prefix_ids):],past_key_values=cache,use_cache=False).logits[0,-1,self.cand].float()
            else:
                logits=self.model(**enc).logits[0,-1,self.cand].float()
        p=torch.softmax(logits/self.temperature,dim=-1)
        j=int(torch.argmax(p)); return CLASSES[j],float(p[j]),(time.perf_counter()-t0)*1000
    @staticmethod
    def _handoff(route):
        return {'deterministic':'deterministic_tool','harness':'local_harness','retrieval':'retrieval_surface','tiny_model':'tiny_semantic_specialist','larger_model':'larger_reasoner','unknown':'clarify_or_observe','ordinary':'ordinary_qa_specialist'}.get(route,'larger_reasoner')
    def route(self,text):
        if self._authority(text):
            return Decision('authority',1.0,'policy_guard','require_user_confirmation','requires_confirmation',())
        signals=self._signals(text)
        if len(signals)==1:
            r=signals[0]
            return Decision(r,0.99,'0b_single_signal',self._handoff(r),'allowed',signals)
        admission=self.governor.decide(resource_snapshot())
        self.last_admission=admission
        if not admission.admit:
            return Decision('unknown',1.0,'resource_pressure_handoff','larger_reasoner','allowed',signals)
        pred,conf,_lat=self._model(text)
        if len(signals)>1 and pred not in signals:
            return Decision('unknown',conf,'signal_model_conflict','clarify_or_larger_reasoner','allowed',signals)
        if len(signals)>1 and pred in signals and conf >= 0.55:
            return Decision(pred,conf,'signal_model_agreement',self._handoff(pred),'allowed',signals)
        if conf < self.min_confidence and pred not in ('larger_model','unknown'):
            return Decision('unknown',conf,'low_confidence_handoff','larger_reasoner','allowed',signals)
        return Decision(pred,conf,'semantic7_model',self._handoff(pred),'allowed',signals)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('text',nargs='?'); ap.add_argument('--adapter',default=str(DEFAULT_ADAPTER)); ap.add_argument('--temperature',type=float,default=0.5); ap.add_argument('--debug',action='store_true'); a=ap.parse_args()
    if not a.text: raise SystemExit('text required')
    r=ShoalRouter(a.adapter,temperature=a.temperature).route(a.text)
    out={'surface':'ordinary_llm','handoff':r.handoff,'authority':r.authority}
    if a.debug: out.update({'route':r.route,'confidence':r.confidence,'source':r.source,'signals':r.signals})
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__': main()
