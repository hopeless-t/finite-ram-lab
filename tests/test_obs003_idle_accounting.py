from __future__ import annotations

from finite_ram_lab.obs003_idle_accounting import (
    classify_idle,
    classify_start_mode,
)


SPEC = {
    "required_page_size": 4096,
    "plus17_ranges": [[114, 117], [179, 180]],
    "neg17_drop_min_pages": 15,
    "neg17_drop_max_pages": 19,
    "meaningful_drop_pages": 2,
    "rss_stable_tolerance_pages": 2,
    "rss_matching_tolerance_pages": 3,
}


def sample(ms: float, current: float, rss_pages: float) -> dict:
    return {
        "elapsed_ms": ms,
        "current_pages": current,
        "status_kib": {
            "VmRSS": int(rss_pages * 4),
            "RssAnon": int(rss_pages * 2),
            "RssFile": int(rss_pages * 2),
            "RssShmem": 0,
            "VmPTE": 16,
        },
    }


def test_start_mode_is_frozen_from_math015():
    assert classify_start_mode(114, SPEC) == "PLUS17"
    assert classify_start_mode(116.5, SPEC) == "PLUS17"
    assert classify_start_mode(179, SPEC) == "PLUS17"
    assert classify_start_mode(180, SPEC) == "PLUS17"
    assert classify_start_mode(113, SPEC) == "OTHER"
    assert classify_start_mode(161, SPEC) == "OTHER"


def test_neg17_without_rss_drop():
    rows = [
        sample(0, 116, 80),
        sample(12, 116, 80),
        sample(16, 99, 80),
        sample(100, 99, 80),
    ]
    result = classify_idle(rows, SPEC)
    assert result["phenotype"] == "IDLE_NEG17_NO_RSS_DROP"
    assert result["current_drop_pages"] == 17
    assert result["neg17_like"] is True


def test_neg17_with_matching_rss_drop():
    rows = [
        sample(0, 116, 80),
        sample(16, 99, 63),
        sample(100, 99, 63),
    ]
    result = classify_idle(rows, SPEC)
    assert result["phenotype"] == "IDLE_NEG17_WITH_RSS_DROP"
    assert result["rss_drop_pages_at_min_current"] == 17


def test_no_drop():
    rows = [
        sample(0, 99, 80),
        sample(100, 98.5, 80),
    ]
    result = classify_idle(rows, SPEC)
    assert result["phenotype"] == "IDLE_NO_DROP"


def test_other_drop():
    rows = [
        sample(0, 116, 80),
        sample(100, 108, 80),
    ]
    result = classify_idle(rows, SPEC)
    assert result["phenotype"] == "IDLE_OTHER_DROP"
