#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from shoal_workcell import CAPABILITIES, doctor_report, footprint_report, reinstall_projection

assert len(CAPABILITIES) == 14, CAPABILITIES
doc=doctor_report(); assert doc['status']=='PASS', doc
fp=footprint_report(); assert fp['adapter_model_safetensors_bytes']==399384, fp
with tempfile.TemporaryDirectory(dir=Path('.work/rsf-llm')) as td:
    dest=Path(td)/'catfood'
    out=reinstall_projection(dest)
    assert dest.exists(), out
    assert out['mode'] in ('hardlink','symlink'), out
    try:
        reinstall_projection(dest)
    except FileExistsError:
        overwrite_guard=True
    else:
        overwrite_guard=False
    assert overwrite_guard
print(json.dumps({'status':'REINSTALL_SURFACE=PASS','capability_count':len(CAPABILITIES),'doctor':doc,'footprint':fp},ensure_ascii=False,separators=(',',':')))
