from __future__ import annotations
import json, math, statistics
from pathlib import Path
from typing import Any

def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _in(x: float, lo: float, hi: float) -> bool:
    return lo <= x <= hi

def _event_r(spec: dict[str, Any], trial: dict[str, Any]) -> int | None:
    for row in trial["validation"]:
        d=float(row["delta_pages"])
        if _in(d,float(spec["validation_event_min_pages"]),float(spec["validation_event_max_pages"])):
            return int(row["touch"])
    return None

def analyze_trials(spec: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    expected={(b,a) for b in range(int(spec["runner_blocks"])) for a in spec["arms"]}
    got={(int(t["block"]),t["arm"]) for t in trials}
    if got != expected: raise ValueError("incomplete trial matrix")
    blocks=[]; support=0; calibrated_rs=[]
    pred=int(spec["predicted_r"]); tol=int(spec["r_tolerance"])
    for b in range(int(spec["runner_blocks"])):
        by={t["arm"]:t for t in trials if int(t["block"])==b}
        c=by["calibrated"]; n=by["no_hold"]; u=by["control_no_prime"]
        cal=float(c["calibration_delta_pages"])
        stable=max([float(x) for x in c["passive_drop_pages"]] or [0.0]) < float(spec["significant_passive_drop_pages"])
        r=_event_r(spec,c); rn=_event_r(spec,n); ru=_event_r(spec,u)
        calibrated_rs.append(r)
        ok=_in(cal,float(spec["calibration_min_pages"]),float(spec["calibration_max_pages"])) and stable and r is not None and abs(r-pred)<=tol
        support += int(ok)
        blocks.append({"block":b,"calibrated_r":r,"no_hold_r":rn,"control_no_prime_r":ru,"hold_stable":stable,"supports":ok})
    no_hold_bad=sum(1 for x in blocks if x["no_hold_r"] is None or abs(x["no_hold_r"]-pred)>tol)
    cal_bad=sum(1 for x in blocks if x["calibrated_r"] is None or abs(x["calibrated_r"]-pred)>tol)
    control_all_exact=all(x["control_no_prime_r"] is not None and abs(x["control_no_prime_r"]-pred)<=tol for x in blocks)
    if support>=int(spec["required_support_blocks"]) and no_hold_bad<=cal_bad and not control_all_exact:
        decision="SUPPORT_CALIBRATED_STOCK"
    elif support<=1:
        decision="REJECT_CALIBRATED_STOCK"
    else:
        decision="INCONCLUSIVE"
    observed=[x for x in calibrated_rs if x is not None]
    candidates=range(1,129)
    abs_error={str(k):sum(abs(x-k) for x in observed) for k in candidates}
    best=min(candidates,key=lambda k:(abs_error[str(k)],k)) if observed else None
    arbitrary_bits=7*len(observed)
    fixed_bits=7 + sum(math.log2(1+abs(x-pred)) for x in observed)
    return {"experiment_id":spec["experiment_id"],"decision":decision,"support_blocks":support,
      "calibrated_r":calibrated_rs,"best_r_by_absolute_error":best,
      "absolute_error":abs_error,"mdl":{"fixed_r64_bits":fixed_bits,"arbitrary_location_bits":arbitrary_bits},
      "blocks":blocks,"inference_boundary":"Calibration of hosted Linux memcg stock phase only; not seven-slot capacity and not a hardware-memory law."}
