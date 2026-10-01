from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Iterable


USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class ActionUse:
    workflow: str
    line: int
    target: str
    kind: str
    repository: str | None
    ref: str | None
    pinned: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "workflow": self.workflow,
            "line": self.line,
            "target": self.target,
            "kind": self.kind,
            "repository": self.repository,
            "ref": self.ref,
            "pinned": self.pinned,
        }


def classify_use(workflow: str, line_no: int, target: str) -> ActionUse:
    if target.startswith("./") or target.startswith("$/"):
        return ActionUse(workflow,line_no,target,"LOCAL",None,None,True)
    if target.startswith("docker://"):
        # Docker image digests need a different verifier; do not silently call tags pinned.
        image=target[len("docker://"):]
        pinned="@sha256:" in image
        return ActionUse(workflow,line_no,target,"DOCKER",image,None,pinned)
    if "@" not in target:
        return ActionUse(workflow,line_no,target,"INVALID_EXTERNAL",None,None,False)
    repository,ref=target.rsplit("@",1)
    pinned=bool(FULL_SHA_RE.fullmatch(ref))
    return ActionUse(workflow,line_no,target,"GITHUB_ACTION",repository,ref,pinned)


def scan_workflow_text(workflow: str, text: str) -> tuple[ActionUse,...]:
    if not workflow.startswith(".github/workflows/"):
        raise ValueError("workflow_path_invalid")
    rows=[]
    for line_no,line in enumerate(text.splitlines(),1):
        match=USES_RE.match(line)
        if match:
            rows.append(classify_use(workflow,line_no,match.group(1)))
    return tuple(rows)


def audit_workflows(files: Iterable[tuple[str,str]]) -> dict[str,object]:
    uses=[]
    workflow_count=0
    for path,text in files:
        workflow_count+=1
        uses.extend(scan_workflow_text(path,text))
    external=[row for row in uses if row.kind in {"GITHUB_ACTION","DOCKER","INVALID_EXTERNAL"}]
    unpinned=[row for row in external if not row.pinned]
    return {
        "schema":"finite-ram-lab.github-actions-pin-audit/v0.1",
        "workflow_count":workflow_count,
        "uses_count":len(uses),
        "external_use_count":len(external),
        "unpinned_external_count":len(unpinned),
        "unpinned":[row.as_dict() for row in unpinned],
        "all_external_pinned":len(unpinned)==0,
        "lockfile_authority":"NONE",
        "workflow_rewrite_performed":False,
    }


def lockfile_preflight(
    *,
    lock_version: str | None,
    known_preview_versions: frozenset[str]=frozenset({"v0.0.1","v0.0.2","v0.0.3"}),
)->dict[str,object]:
    if lock_version is None:
        return {
            "status":"MISSING",
            "reason":"actions_lock_absent",
            "rewrite_authorized":False,
        }
    if lock_version not in known_preview_versions:
        return {
            "status":"REVIEW",
            "reason":"lock_schema_version_unknown",
            "rewrite_authorized":False,
        }
    return {
        "status":"PREVIEW_SCHEMA_RECOGNIZED",
        "reason":"schema_is_pre_1_0_and_may_break",
        "rewrite_authorized":False,
    }
