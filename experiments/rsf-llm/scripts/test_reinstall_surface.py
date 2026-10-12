#!/usr/bin/env python3
import json,shutil,tempfile
from pathlib import Path
from shoal_workcell import (
    CAPABILITIES, LAUNCHER, attest_install, doctor_report, ensure_projection,
    footprint_report, install_plan, projection_state, reinstall_projection,
    repair_projection, uninstall_projection,
)

assert len(CAPABILITIES) == 20, CAPABILITIES
doc=doctor_report(); assert doc['status']=='PASS', doc
fp=footprint_report(); assert fp['adapter_model_safetensors_bytes']==399384, fp
att1=attest_install(); att2=attest_install(); assert att1==att2
with tempfile.TemporaryDirectory(dir=Path('.work/rsf-llm')) as td:
    root=Path(td); dest=root/'catfood'
    plan=install_plan(dest); assert plan['planned_action'] in ('hardlink','symlink'), plan
    out=reinstall_projection(dest); assert dest.exists(), out
    assert projection_state(dest)['healthy']
    ensured=ensure_projection(dest); assert ensured['action']=='noop', ensured

    duplicate=root/'duplicate'; shutil.copy2(LAUNCHER,duplicate)
    assert projection_state(duplicate)['state']=='duplicate_copy'
    repaired=repair_projection(duplicate); assert repaired['action']=='atomic_repair_duplicate_to_projection', repaired
    assert projection_state(duplicate)['healthy']

    foreign=root/'foreign'; foreign.write_text('do-not-touch\n')
    refused=uninstall_projection(foreign); assert refused['action']=='refuse_unowned', refused
    assert foreign.read_text()=='do-not-touch\n'

    removed=uninstall_projection(dest); assert removed['action']=='removed_owned_projection', removed
    assert projection_state(dest)['state']=='missing'

    try:
        reinstall_projection(duplicate)
    except FileExistsError:
        overwrite_guard=True
    else:
        overwrite_guard=False
    assert overwrite_guard
print(json.dumps({'status':'REINSTALL_SURFACE=PASS','capability_count':len(CAPABILITIES),'doctor':doc,'footprint':fp,'attestation_stable':True},ensure_ascii=False,separators=(',',':')))
