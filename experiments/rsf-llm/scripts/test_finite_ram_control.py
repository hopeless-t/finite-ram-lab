#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from finite_ram_control import ByteBudgetGovernor,BoundedControlState,GIB

def snap(avail_gib,psi=0.0): return {'mem_available_bytes':int(avail_gib*GIB),'psi_memory_some_avg10':psi}

g=ByteBudgetGovernor(model_estimated_bytes=1*GIB,enter_reserve_bytes=3*GIB,exit_reserve_bytes=5*GIB,enter_psi=.10,exit_psi=.02)
a=[]
for s in [snap(10),snap(3.5),snap(5.5),snap(6.2),snap(10,.2),snap(10,.05),snap(10,.0)]:
    x=g.decide(s); a.append({'admit':x.admit,'state':x.state,'reason':x.reason})
expected=[True,False,False,True,False,False,True]
assert [x['admit'] for x in a]==expected,(a,expected)
with tempfile.TemporaryDirectory() as td:
    d=Path(td)/'events.jsonl'; r=Path(td)/'state.json'; j=BoundedControlState(d,r,budget_bytes=512)
    last=None
    for i in range(100):
        last=j.append({'ts_unix':i,'trace_id':f't{i}','route':'ordinary','source':'test','handoff':'ordinary_qa_specialist','authority':'allowed','status':'handoff','elapsed_ms':i/10})
    assert last['resident_bytes']<=512,last
    assert last['durable_bytes']>last['resident_bytes'],last
    assert last['resident_entries']<100,last
print(json.dumps({'status':'FINITE_RAM_CONTROL=PASS','hysteresis':a,'bounded_state':last},separators=(',',':')))
