from finite_ram_lab.memcg_trace_observer import (
    classify_uncharge_stack,
    discover_target_memcg,
    parse_trace,
    probe_definitions,
    required_symbols,
    successful_stock_consumes,
    summarize_target_uncharge,
    target_refills,
)


TRACE = """
worker-4242  [003] ....  10.000001: frl_obs_try_charge: (try_charge_memcg+0x0/0x100) memcg=ffff888012340000 request_pages=1
worker-4242  [003] ....  10.000010: frl_obs_refill: (refill_stock+0x0/0x100) memcg=ffff888012340000 pages=63
worker-4242  [011] ....  10.010000: frl_obs_consume: (consume_stock+0x0/0x100 <- try_charge_memcg) memcg=ffff888012340000 request_pages=1 ret=1
kworker/3:1-55 [003] ....  10.020000: frl_obs_uncharge: (memcg_uncharge+0x0/0x80) memcg=ffff888012340000 pages=17
 => memcg_uncharge
 => drain_stock
 => refill_stock
 => some_other_memcg_path
kswapd0-77   [009] ....  10.030000: frl_obs_uncharge: (memcg_uncharge+0x0/0x80) memcg=ffff8880dead0000 pages=31
 => memcg_uncharge
 => uncharge_batch
 => __mem_cgroup_uncharge_folios
"""


def test_probe_contract_mentions_expected_symbols():
    defs = probe_definitions()
    text = "\n".join(item.definition for item in defs)
    for symbol in required_symbols():
        assert symbol in text


def test_parse_and_discover_target_memcg():
    events = parse_trace(TRACE)
    assert len(events) == 5

    target = discover_target_memcg(
        events,
        worker_pid=4242,
    )
    assert target == int("ffff888012340000", 16)

    refills = target_refills(
        events,
        target_memcg=target,
    )
    assert len(refills) == 1
    assert refills[0].fields["pages"] == 63

    consumes = successful_stock_consumes(
        events,
        target_memcg=target,
    )
    assert len(consumes) == 1
    assert consumes[0].cpu == 11


def test_stock_slot_eviction_classification():
    events = parse_trace(TRACE)
    target = discover_target_memcg(
        events,
        worker_pid=4242,
    )
    summary = summarize_target_uncharge(
        events,
        target_memcg=target,
    )

    assert summary["events"] == 1
    assert summary["pages"] == 17
    assert summary["by_origin"] == {
        "STOCK_SLOT_EVICTION_OR_OVERFLOW": {
            "events": 1,
            "pages": 17,
        }
    }


def test_uncharge_stack_taxonomy():
    assert (
        classify_uncharge_stack(
            ["memcg_uncharge", "drain_stock", "refill_stock"]
        )
        == "STOCK_SLOT_EVICTION_OR_OVERFLOW"
    )
    assert (
        classify_uncharge_stack(
            [
                "memcg_uncharge",
                "drain_stock",
                "drain_local_memcg_stock",
            ]
        )
        == "STOCK_GLOBAL_DRAIN"
    )
    assert (
        classify_uncharge_stack(
            ["memcg_uncharge", "uncharge_batch"]
        )
        == "FOLIO_UNCHARGE_BATCH"
    )
    assert (
        classify_uncharge_stack(
            ["memcg_uncharge", "__mem_cgroup_uncharge"]
        )
        == "FOLIO_UNCHARGE_SINGLE"
    )
    assert (
        classify_uncharge_stack(
            ["memcg_uncharge", "obj_cgroup_release"]
        )
        == "OBJCG_RELEASE"
    )


def test_other_memcg_is_excluded():
    events = parse_trace(TRACE)
    target = discover_target_memcg(
        events,
        worker_pid=4242,
    )
    summary = summarize_target_uncharge(
        events,
        target_memcg=target,
    )
    assert summary["pages"] != 31
