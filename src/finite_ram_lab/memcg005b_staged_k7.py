from __future__ import annotations
import json, math
from pathlib import Path
from typing import Any

def load_spec(path:str|Path)->dict[str,Any]:
    return json.loads(Path(path).read_text())

def _bit(state:str):
    return 0 if state=="PRESENT" else 1 if state=="ABSENT" else None

def analyze_trials(spec:dict[str,Any],trials:list[dict[str,Any]])->dict[str,Any]:
    tested=[int(x) for x in spec["tested_m"]]; nb=int(spec["runner_blocks"])
    expected={(b,m) for b in range(nb) for m in tested}
    got={(int(t["block"]),int(t["m"])) for t in trials}
    if got!=expected: raise ValueError("incomplete replica matrix")

    source={0:"PRESENT",5:"PRESENT",6:"PRESENT",7:"ABSENT",8:"ABSENT"}
    blocks=[]; support=0; complete=0
    invalid_by_m={str(m):0 for m in tested}
    for b in range(nb):
        by={int(t["m"]):t for t in trials if int(t["block"])==b}
        all_valid=all(bool(by[m]["valid_state"]) for m in tested)
        complete += int(all_valid)
        for m in tested:
            if not bool(by[m]["valid_state"]): invalid_by_m[str(m)]+=1
        exact=all_valid and all(by[m]["target_state"]==source[m] for m in tested)
        support += int(exact)
        blocks.append({"block":b,"all_replicas_valid":all_valid,
            "states":{str(m):by[m]["target_state"] for m in tested},
            "supports_staged_k7":exact,
            "invalid_reasons":{str(m):by[m].get("invalid_reason") for m in tested if not by[m]["valid_state"]}})

    cand=[int(x) for x in spec["candidate_k"]]; eps=float(spec["model_error_floor"])
    model={}
    for k in cand:
        obs=[t for t in trials if t["valid_state"] and _bit(t["target_state"]) is not None]
        err=sum(int((int(t["m"])>=k) != bool(_bit(t["target_state"]))) for t in obs)
        n=len(obs)
        ll=(n-err)*-math.log2(1-eps)+err*-math.log2(eps)
        exc=0 if err==0 else math.log2(math.comb(n,err))
        model[str(k)]={"valid_observations":n,"classification_errors":err,
                       "log_loss_bits":ll,"mdl_bits":math.log2(len(cand))+exc}
    minerr=min(v["classification_errors"] for v in model.values())
    best=[int(k) for k,v in model.items() if v["classification_errors"]==minerr]

    systematic=any(v>=2 for v in invalid_by_m.values())
    if support>=int(spec["required_support_blocks"]) and not systematic:
        decision="SUPPORT_STAGED_K7"
    elif complete>=3 and support<=1 and 7 not in best:
        decision="REJECT_STAGED_K7"
    else:
        decision="INCONCLUSIVE"

    return {"experiment_id":spec["experiment_id"],"decision":decision,
            "support_blocks":support,"complete_valid_blocks":complete,
            "invalid_by_m":invalid_by_m,"systematic_invalid":systematic,
            "blocks":blocks,"model_by_k":model,"best_k_by_errors":best,
            "trials":trials,
            "inference_boundary":"Hosted three-CPU staged memcg K7 probe only; not a hardware-memory law."}
