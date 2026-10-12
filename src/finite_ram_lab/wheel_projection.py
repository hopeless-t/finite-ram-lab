from __future__ import annotations

import base64
import csv
import hashlib
import io
import py_compile
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

HOT_MODULES_V1 = (
    "finite_ram_lab/__init__.py",
    "finite_ram_lab/__main__.py",
    "finite_ram_lab/cli.py",
    "finite_ram_lab/fast_cli.py",
    "finite_ram_lab/cache_ops.py",
    "finite_ram_lab/adaptive_cache_engine.py",
    "finite_ram_lab/sim.py",
    "finite_ram_lab/operational_runtime.py",
)
PROJECTION_ID = "hot-pyc-v1"


def _record_row(name: str, data: bytes) -> list[str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return [name, f"sha256={digest}", str(len(data))]


def _compile_pyc(source: bytes, logical_name: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="frl-hot-pyc-") as td:
        root = Path(td)
        src = root / "module.py"
        out = root / "module.pyc"
        src.write_bytes(source)
        py_compile.compile(
            str(src),
            cfile=str(out),
            dfile=logical_name,
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        return out.read_bytes()


def project_hot_pyc_wheel(
    source_wheel: str | Path,
    output_wheel: str | Path,
    *,
    hot_modules: tuple[str, ...] = HOT_MODULES_V1,
) -> dict[str, Any]:
    source = Path(source_wheel)
    output = Path(output_wheel)
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source, "r") as zin:
        files = {info.filename: zin.read(info.filename) for info in zin.infolist() if not info.is_dir()}

    missing = [name for name in hot_modules if name not in files]
    if missing:
        raise RuntimeError(f"hot projection modules missing from wheel: {missing}")

    record_names = [name for name in files if name.endswith(".dist-info/RECORD")]
    if len(record_names) != 1:
        raise RuntimeError(f"expected one wheel RECORD, found {record_names}")
    record_name = record_names[0]
    files.pop(record_name)

    added: list[str] = []
    for name in hot_modules:
        pyc_name = name[:-3] + ".pyc"
        files[pyc_name] = _compile_pyc(files[name], name)
        added.append(pyc_name)

    rows = [_record_row(name, data) for name, data in sorted(files.items())]
    rows.append([record_name, "", ""])
    record_buffer = io.StringIO(newline="")
    csv.writer(record_buffer).writerows(rows)
    files[record_name] = record_buffer.getvalue().encode("utf-8")

    tmp = output.with_name(f".{output.name}.{sys.implementation.cache_tag}.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            zout.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    tmp.replace(output)

    return {
        "projection_id": PROJECTION_ID,
        "python_cache_tag": sys.implementation.cache_tag,
        "hot_modules": list(hot_modules),
        "added_pyc": added,
        "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
