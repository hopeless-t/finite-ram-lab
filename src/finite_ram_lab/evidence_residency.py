from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "evidence-residency-v1"
VALID_TIERS = {"HOT", "WARM", "COLD"}
_HEX = set("0123456789abcdef")


class EvidenceResidencyError(ValueError):
    """Evidence-residency contract violation."""


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _content_set_digest(files: list[dict[str, Any]]) -> str:
    stable = [
        {
            "path": item["path"],
            "size_bytes": item["size_bytes"],
            "sha256": item["sha256"],
        }
        for item in files
    ]
    return _sha256_bytes(_canonical_json(stable).encode("utf-8"))


def _normalized_rel(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError as exc:
        raise EvidenceResidencyError(
            f"path is outside evidence root: {path}"
        ) from exc
    value = rel.as_posix()
    if not value or value == "." or value.startswith("../"):
        raise EvidenceResidencyError(f"invalid relative path: {value!r}")
    return value


def _validate_sha256(value: object, *, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EvidenceResidencyError(f"{field} must be 64 lowercase hex chars")
    if any(ch not in _HEX for ch in value):
        raise EvidenceResidencyError(f"{field} must be 64 lowercase hex chars")
    return value


def _validate_storage_refs(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise EvidenceResidencyError("storage_refs must be a list")
    out: list[dict[str, str]] = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise EvidenceResidencyError(f"storage_refs[{i}] must be an object")
        if set(item) != {"tier", "provider", "locator"}:
            raise EvidenceResidencyError(
                f"storage_refs[{i}] must contain exactly tier/provider/locator"
            )
        tier = item["tier"]
        provider = item["provider"]
        locator = item["locator"]
        if tier not in VALID_TIERS:
            raise EvidenceResidencyError(
                f"storage_refs[{i}].tier must be HOT/WARM/COLD"
            )
        if not isinstance(provider, str) or not provider:
            raise EvidenceResidencyError(
                f"storage_refs[{i}].provider must be non-empty"
            )
        if not isinstance(locator, str) or not locator:
            raise EvidenceResidencyError(
                f"storage_refs[{i}].locator must be non-empty"
            )
        out.append(
            {"tier": tier, "provider": provider, "locator": locator}
        )
    return out


def validate_manifest(manifest: object) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise EvidenceResidencyError("manifest must be a JSON object")

    required = {
        "schema_version",
        "experiment_id",
        "run_id",
        "source_commit",
        "created_at_utc",
        "residency_tier",
        "content_set_sha256",
        "file_count",
        "total_bytes",
        "files",
        "storage_refs",
    }
    optional = {"origin"}
    extra = set(manifest) - required - optional
    missing = required - set(manifest)
    if missing:
        raise EvidenceResidencyError(
            f"manifest missing fields: {sorted(missing)}"
        )
    if extra:
        raise EvidenceResidencyError(
            f"manifest has unsupported fields: {sorted(extra)}"
        )

    if manifest["schema_version"] != SCHEMA_VERSION:
        raise EvidenceResidencyError(
            f"unsupported schema_version: {manifest['schema_version']!r}"
        )
    for key in ("experiment_id", "run_id", "source_commit", "created_at_utc"):
        if not isinstance(manifest[key], str) or not manifest[key]:
            raise EvidenceResidencyError(f"{key} must be a non-empty string")

    if manifest["residency_tier"] not in VALID_TIERS:
        raise EvidenceResidencyError("residency_tier must be HOT/WARM/COLD")

    _validate_sha256(
        manifest["content_set_sha256"],
        field="content_set_sha256",
    )

    if (
        isinstance(manifest["file_count"], bool)
        or not isinstance(manifest["file_count"], int)
        or manifest["file_count"] < 0
    ):
        raise EvidenceResidencyError("file_count must be a non-negative integer")
    if (
        isinstance(manifest["total_bytes"], bool)
        or not isinstance(manifest["total_bytes"], int)
        or manifest["total_bytes"] < 0
    ):
        raise EvidenceResidencyError("total_bytes must be a non-negative integer")

    files = manifest["files"]
    if not isinstance(files, list):
        raise EvidenceResidencyError("files must be a list")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, item in enumerate(files):
        if not isinstance(item, dict):
            raise EvidenceResidencyError(f"files[{i}] must be an object")
        if set(item) != {"path", "size_bytes", "sha256"}:
            raise EvidenceResidencyError(
                f"files[{i}] must contain exactly path/size_bytes/sha256"
            )
        path = item["path"]
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or path == "."
            or ".." in Path(path).parts
        ):
            raise EvidenceResidencyError(
                f"files[{i}].path must be a safe relative path"
            )
        if path in seen:
            raise EvidenceResidencyError(f"duplicate manifest path: {path}")
        seen.add(path)

        size = item["size_bytes"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise EvidenceResidencyError(
                f"files[{i}].size_bytes must be non-negative"
            )
        digest = _validate_sha256(
            item["sha256"],
            field=f"files[{i}].sha256",
        )
        normalized.append(
            {"path": path, "size_bytes": size, "sha256": digest}
        )

    if normalized != sorted(normalized, key=lambda x: x["path"]):
        raise EvidenceResidencyError("files must be sorted by path")

    if manifest["file_count"] != len(normalized):
        raise EvidenceResidencyError("file_count does not match files")
    if manifest["total_bytes"] != sum(x["size_bytes"] for x in normalized):
        raise EvidenceResidencyError("total_bytes does not match files")
    if manifest["content_set_sha256"] != _content_set_digest(normalized):
        raise EvidenceResidencyError(
            "content_set_sha256 does not match file manifest"
        )

    storage_refs = _validate_storage_refs(manifest["storage_refs"])

    origin = manifest.get("origin")
    if origin is not None and not isinstance(origin, dict):
        raise EvidenceResidencyError("origin must be an object when present")

    return {
        **manifest,
        "files": normalized,
        "storage_refs": storage_refs,
    }


def _collect_files(
    root: Path,
    *,
    exclude: Iterable[Path] = (),
) -> list[dict[str, Any]]:
    excluded = {p.resolve() for p in exclude}
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise EvidenceResidencyError(
                f"symlink is not allowed in evidence bundle: {path}"
            )
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in excluded:
            continue
        rel = _normalized_rel(resolved, root)
        files.append(
            {
                "path": rel,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return files


def build_manifest(
    root: str | Path,
    *,
    experiment_id: str,
    run_id: str,
    source_commit: str,
    residency_tier: str,
    storage_refs: list[dict[str, str]] | None = None,
    origin: dict[str, Any] | None = None,
    exclude: Iterable[str | Path] = (),
) -> dict[str, Any]:
    base = Path(root).resolve()
    if not base.is_dir():
        raise EvidenceResidencyError(
            f"evidence root is not a directory: {base}"
        )
    if residency_tier not in VALID_TIERS:
        raise EvidenceResidencyError(
            "residency_tier must be HOT/WARM/COLD"
        )
    for key, value in (
        ("experiment_id", experiment_id),
        ("run_id", run_id),
        ("source_commit", source_commit),
    ):
        if not isinstance(value, str) or not value:
            raise EvidenceResidencyError(f"{key} must be non-empty")

    excluded = [
        (Path(p).resolve() if Path(p).is_absolute() else (base / p).resolve())
        for p in exclude
    ]
    files = _collect_files(base, exclude=excluded)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "source_commit": source_commit,
        "created_at_utc": _utc_now(),
        "residency_tier": residency_tier,
        "content_set_sha256": _content_set_digest(files),
        "file_count": len(files),
        "total_bytes": sum(x["size_bytes"] for x in files),
        "files": files,
        "storage_refs": storage_refs or [],
    }
    if origin is not None:
        manifest["origin"] = origin
    return validate_manifest(manifest)


def write_manifest(
    root: str | Path,
    out: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    output = Path(out)
    base = Path(root).resolve()
    exclude = list(kwargs.pop("exclude", ()))
    try:
        output.resolve().relative_to(base)
    except ValueError:
        pass
    else:
        exclude.append(output)

    manifest = build_manifest(base, exclude=exclude, **kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_manifest(
    root: str | Path,
    manifest_path: str | Path,
    *,
    allow_extra: bool = False,
) -> dict[str, Any]:
    base = Path(root).resolve()
    manifest_file = Path(manifest_path).resolve()
    if not base.is_dir():
        raise EvidenceResidencyError(
            f"evidence root is not a directory: {base}"
        )
    manifest = validate_manifest(
        json.loads(manifest_file.read_text(encoding="utf-8"))
    )

    expected = {item["path"]: item for item in manifest["files"]}
    missing: list[str] = []
    mismatched: list[dict[str, Any]] = []

    for rel, item in expected.items():
        path = base / rel
        if not path.is_file():
            missing.append(rel)
            continue
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        if (
            actual_size != item["size_bytes"]
            or actual_sha != item["sha256"]
        ):
            mismatched.append(
                {
                    "path": rel,
                    "expected_size_bytes": item["size_bytes"],
                    "actual_size_bytes": actual_size,
                    "expected_sha256": item["sha256"],
                    "actual_sha256": actual_sha,
                }
            )

    exclude = []
    try:
        manifest_file.relative_to(base)
    except ValueError:
        pass
    else:
        exclude.append(manifest_file)
    actual_entries = _collect_files(base, exclude=exclude)
    actual_paths = {item["path"] for item in actual_entries}
    extra = sorted(actual_paths - set(expected))

    passed = (
        not missing
        and not mismatched
        and (allow_extra or not extra)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "root": str(base),
        "manifest": str(manifest_file),
        "content_set_sha256": manifest["content_set_sha256"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "missing": sorted(missing),
        "mismatched": mismatched,
        "extra": extra,
        "allow_extra": allow_extra,
    }


def parse_storage_ref(value: str) -> dict[str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise EvidenceResidencyError(
            "storage ref must be TIER:PROVIDER:LOCATOR"
        )
    ref = {
        "tier": parts[0].upper(),
        "provider": parts[1],
        "locator": parts[2],
    }
    return _validate_storage_refs([ref])[0]
