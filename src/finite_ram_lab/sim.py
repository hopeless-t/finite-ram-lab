from __future__ import annotations

import math
import random
from collections import OrderedDict, defaultdict, deque
from typing import Iterable


def lru_faults(trace: Iterable[int], capacity: int) -> int:
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    resident: OrderedDict[int, None] = OrderedDict()
    faults = 0

    for page in trace:
        if page in resident:
            resident.move_to_end(page)
            continue
        faults += 1
        if len(resident) >= capacity:
            resident.popitem(last=False)
        resident[page] = None

    return faults


def opt_faults(trace: list[int], capacity: int) -> int:
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    future: dict[int, deque[int]] = defaultdict(deque)
    for index, page in enumerate(trace):
        future[page].append(index)

    resident: set[int] = set()
    faults = 0

    for index, page in enumerate(trace):
        q = future[page]
        if q and q[0] == index:
            q.popleft()

        if page in resident:
            continue

        faults += 1
        if len(resident) >= capacity:
            victim = max(resident, key=lambda p: future[p][0] if future[p] else math.inf)
            resident.remove(victim)
        resident.add(page)

    return faults


def _sample_hot(rng: random.Random, hot: list[int], cold: list[int], hot_prob: float) -> int:
    if cold and rng.random() > hot_prob:
        return rng.choice(cold)
    return rng.choice(hot)


def generate_trace(family: str, rng: random.Random, length: int, universe: int, capacity: int) -> list[int]:
    if length <= 0 or universe <= 1 or capacity <= 0:
        raise ValueError("invalid trace parameters")

    pages = list(range(universe))
    hot_n = max(2, min(universe - 1, max(2, capacity - 1)))
    hot = pages[:hot_n]
    cold = pages[hot_n:]

    if family == "stable_hotset":
        return [_sample_hot(rng, hot, cold, 0.92) for _ in range(length)]

    if family == "sequential_scan":
        trace: list[int] = []
        scan = cold if cold else pages
        while len(trace) < length:
            for _ in range(max(8, capacity * 2)):
                trace.append(rng.choice(hot))
                if len(trace) >= length:
                    return trace
            for page in scan:
                trace.append(page)
                if len(trace) >= length:
                    return trace
        return trace

    if family == "shifting_hotset":
        split = length // 2
        first = [_sample_hot(rng, hot, cold, 0.94) for _ in range(split)]
        shifted_start = max(0, min(universe - hot_n, universe // 2))
        hot2 = pages[shifted_start : shifted_start + hot_n]
        hot2_set = set(hot2)
        cold2 = [p for p in pages if p not in hot2_set]
        second = [_sample_hot(rng, hot2, cold2, 0.94) for _ in range(length - split)]
        return first + second

    if family == "bursty":
        trace = []
        burst = cold[: max(1, min(len(cold), capacity * 2))] or pages
        period = max(20, capacity * 5)
        for i in range(length):
            trace.append(rng.choice(burst) if i % period < max(2, capacity // 2) else rng.choice(hot))
        return trace

    raise ValueError(f"unknown family: {family}")
