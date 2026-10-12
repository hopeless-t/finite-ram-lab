#!/usr/bin/env python3
from __future__ import annotations
import json, time
from dataclasses import dataclass
from pathlib import Path

GIB=1024**3


def _meminfo() -> dict[str,int]:
    out={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        if ':' not in line: continue
        k,v=line.split(':',1); parts=v.strip().split()
        if not parts: continue
        try: n=int(parts[0])
        except ValueError: continue
        out[k]=n*1024 if len(parts)>1 and parts[1].lower()=='kb' else n
    return out


def _psi_memory() -> dict[str,dict[str,float]]:
    out={}
    p=Path('/proc/pressure/memory')
    if not p.exists(): return out
    for line in p.read_text().splitlines():
        parts=line.split(); row={}
        for item in parts[1:]:
            if '=' not in item: continue
            k,v=item.split('=',1)
            try: row[k]=float(v)
            except ValueError: pass
        out[parts[0]]=row
    return out


def _self_rss_bytes() -> int:
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1])*1024
    return 0


def resource_snapshot() -> dict:
    m=_meminfo(); total=m.get('MemTotal',0); avail=m.get('MemAvailable',m.get('MemFree',0)); psi=_psi_memory()
    return {
        'monotonic_ns':time.monotonic_ns(),
        'mem_total_bytes':total,
        'mem_available_bytes':avail,
        'mem_available_fraction':(avail/total if total else None),
        'self_rss_bytes':_self_rss_bytes(),
        'psi_memory_some_avg10':psi.get('some',{}).get('avg10'),
        'psi_memory_full_avg10':psi.get('full',{}).get('avg10'),
    }

@dataclass
class Admission:
    admit: bool
    state: str
    reason: str
    estimated_bytes: int
    reserve_bytes: int
    available_bytes: int
    psi_some_avg10: float

class ByteBudgetGovernor:
    """Finite-RAM admission control with a hysteresis deadband.

    Enters PRESSURE if post-admission available bytes would fall below the enter reserve
    or PSI some avg10 crosses enter_psi. Leaves PRESSURE only after the larger exit
    reserve is restored and PSI drops below exit_psi.
    """
    def __init__(self, *, model_estimated_bytes:int=1536*1024**2,
                 enter_reserve_bytes:int=3*GIB, exit_reserve_bytes:int=5*GIB,
                 enter_psi:float=0.10, exit_psi:float=0.02,
                 state_path:str|Path|None=None):
        if exit_reserve_bytes < enter_reserve_bytes: raise ValueError('exit reserve must be >= enter reserve')
        if exit_psi > enter_psi: raise ValueError('exit psi must be <= enter psi')
        self.model_estimated_bytes=model_estimated_bytes
        self.enter_reserve_bytes=enter_reserve_bytes; self.exit_reserve_bytes=exit_reserve_bytes
        self.enter_psi=enter_psi; self.exit_psi=exit_psi
        self.state_path=Path(state_path) if state_path else None
        self.state='NORMAL'
        if self.state_path and self.state_path.exists():
            try: self.state=json.loads(self.state_path.read_text()).get('state','NORMAL')
            except Exception: pass
    def _persist(self, snapshot, reason):
        if not self.state_path: return
        self.state_path.parent.mkdir(parents=True,exist_ok=True)
        self.state_path.write_text(json.dumps({'state':self.state,'reason':reason,'updated_unix':time.time(),'snapshot':snapshot},ensure_ascii=False,separators=(',',':'))+'\n')
    def decide(self, snapshot:dict|None=None, estimated_bytes:int|None=None) -> Admission:
        s=snapshot or resource_snapshot(); est=self.model_estimated_bytes if estimated_bytes is None else estimated_bytes
        avail=int(s.get('mem_available_bytes') or 0); psi=float(s.get('psi_memory_some_avg10') or 0.0)
        post=avail-est
        if self.state=='PRESSURE':
            if post >= self.exit_reserve_bytes and psi <= self.exit_psi:
                self.state='NORMAL'; reason='pressure_recovered_hysteresis'
            else: reason='pressure_hold_hysteresis'
        else:
            if post < self.enter_reserve_bytes:
                self.state='PRESSURE'; reason='byte_reserve_enter'
            elif psi >= self.enter_psi:
                self.state='PRESSURE'; reason='psi_enter'
            else: reason='within_byte_and_psi_budget'
        self._persist(s,reason)
        return Admission(self.state=='NORMAL',self.state,reason,est,self.exit_reserve_bytes if self.state=='PRESSURE' else self.enter_reserve_bytes,avail,psi)

class BoundedControlState:
    """Durable receipts may grow; resident controller state is byte bounded."""
    def __init__(self, durable_jsonl:Path, resident_json:Path, budget_bytes:int=4096):
        self.durable_jsonl=durable_jsonl; self.resident_json=resident_json; self.budget_bytes=budget_bytes
    def append(self, receipt:dict) -> dict:
        self.durable_jsonl.parent.mkdir(parents=True,exist_ok=True)
        with self.durable_jsonl.open('a',encoding='utf-8') as f: f.write(json.dumps(receipt,ensure_ascii=False,separators=(',',':'))+'\n')
        entries=[]
        if self.resident_json.exists():
            try: entries=json.loads(self.resident_json.read_text()).get('entries',[])
            except Exception: entries=[]
        compact={k:receipt.get(k) for k in ('ts_unix','trace_id','route','source','handoff','authority','status','elapsed_ms')}
        entries.append(compact)
        def blob(es): return (json.dumps({'budget_bytes':self.budget_bytes,'entries':es},ensure_ascii=False,separators=(',',':'))+'\n').encode()
        while entries and len(blob(entries))>self.budget_bytes: entries.pop(0)
        encoded=blob(entries)
        self.resident_json.parent.mkdir(parents=True,exist_ok=True)
        self.resident_json.write_bytes(encoded)
        return {'durable_bytes':self.durable_jsonl.stat().st_size,'resident_bytes':len(encoded),'resident_entries':len(entries),'budget_bytes':self.budget_bytes}
