"""Finite RAM Lab research utilities."""

from __future__ import annotations

from typing import Any

__version__ = "0.2.0"
__all__ = ["PreparedTrace", "native_status", "prepare_trace"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .adaptive_cache_engine import PreparedTrace, native_status, prepare_trace

        values = {
            "PreparedTrace": PreparedTrace,
            "native_status": native_status,
            "prepare_trace": prepare_trace,
        }
        return values[name]
    raise AttributeError(name)
