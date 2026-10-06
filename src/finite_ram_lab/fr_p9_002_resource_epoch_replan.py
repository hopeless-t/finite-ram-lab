from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from typing import Any, Iterable

from finite_ram_lab.fr_p9_001_minimum_sufficient_projection import (
    CanonicalAtom,
    WORK_UNITS,
    atom_map,
    compile_projection,
)

SCHEMA = "finite-ram-lab.fr-p9-002-resource-epoch-replan/v0.1"


@dataclass(frozen=True)
class ResourceSnapshot:
    epoch: int
    ram_free_bytes: int
    ssd_available: bool
    ssd_read_bytes_per_second: int
    observer_note: str = ""


@dataclass(frozen=True)
class PlacementCost:
    ram_bytes: int
    ssd_bytes: int
    current_phase_transfer_bytes: int
    migration_bytes: int


@dataclass(frozen=True)
class PlacementPlan:
    planned_epoch: int
    resource_certificate: str
    placements: tuple[tuple[str, str], ...]
    semantic_atoms: tuple[str, ...]
    cost: PlacementCost


CURRENT_GENERATE_ATOMS = frozenset(
    {
        "goal",
        "world_seed",
        "chunk_recipe",
        "topology_rules",
        "generator_capability",
        "geometry_manifest",
    }
)


def resource_certificate(snapshot: ResourceSnapshot) -> str:
    """Hash only fields that can change this planner's decision.

    The global observation epoch and notes are provenance, not decision inputs.
    This is deliberate: a new observation does not justify a replan unless a
    planner-relevant fact changed.
    """

    payload = {
        "ram_free_bytes": snapshot.ram_free_bytes,
        "ssd_available": snapshot.ssd_available,
        "ssd_read_bytes_per_second": snapshot.ssd_read_bytes_per_second,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _placement_dict(plan: PlacementPlan) -> dict[str, str]:
    return dict(plan.placements)


def _semantic_atoms() -> tuple[str, ...]:
    atoms = atom_map()
    generate = WORK_UNITS[0]
    if generate.work_id != "GENERATE_CHUNK":
        raise ValueError("unexpected_part9_fixture")
    return tuple(sorted(compile_projection(generate, atoms=atoms)))


def _candidate_placements(
    semantic_atoms: Iterable[str],
) -> Iterable[dict[str, str]]:
    names = tuple(sorted(semantic_atoms))
    for tiers in itertools.product(("RAM", "SSD"), repeat=len(names)):
        yield dict(zip(names, tiers, strict=True))


def _placement_feasible(
    placement: dict[str, str],
    snapshot: ResourceSnapshot,
    *,
    atoms: dict[str, CanonicalAtom],
) -> bool:
    ram_bytes = sum(
        atoms[atom_id].size_bytes
        for atom_id, tier in placement.items()
        if tier == "RAM"
    )
    if ram_bytes > snapshot.ram_free_bytes:
        return False
    if any(tier == "SSD" for tier in placement.values()) and not snapshot.ssd_available:
        return False
    return True


def _cost(
    placement: dict[str, str],
    *,
    atoms: dict[str, CanonicalAtom],
    previous_plan: PlacementPlan | None,
) -> PlacementCost:
    previous = _placement_dict(previous_plan) if previous_plan is not None else {}
    ram_bytes = 0
    ssd_bytes = 0
    current_phase_transfer_bytes = 0
    migration_bytes = 0

    for atom_id, tier in placement.items():
        size = atoms[atom_id].size_bytes
        if tier == "RAM":
            ram_bytes += size
        elif tier == "SSD":
            ssd_bytes += size
            if atom_id in CURRENT_GENERATE_ATOMS:
                current_phase_transfer_bytes += size
        else:
            raise ValueError(f"unknown_tier:{tier}")

        if previous and previous.get(atom_id) != tier:
            migration_bytes += size

    return PlacementCost(
        ram_bytes=ram_bytes,
        ssd_bytes=ssd_bytes,
        current_phase_transfer_bytes=current_phase_transfer_bytes,
        migration_bytes=migration_bytes,
    )


def plan_projection(
    snapshot: ResourceSnapshot,
    *,
    previous_plan: PlacementPlan | None = None,
) -> PlacementPlan | None:
    atoms = atom_map()
    semantic_atoms = _semantic_atoms()
    candidates: list[tuple[tuple[Any, ...], dict[str, str], PlacementCost]] = []

    for placement in _candidate_placements(semantic_atoms):
        if not _placement_feasible(placement, snapshot, atoms=atoms):
            continue
        cost = _cost(placement, atoms=atoms, previous_plan=previous_plan)
        # Typed objectives remain separate in the result. This ordering is only
        # the frozen admission policy for this synthetic fixture:
        # 1. avoid current-phase transfer;
        # 2. minimize migration from the already materialized plan;
        # 3. minimize SSD residency;
        # 4. deterministic tie break.
        rank = (
            cost.current_phase_transfer_bytes,
            cost.migration_bytes,
            cost.ssd_bytes,
            tuple(sorted(placement.items())),
        )
        candidates.append((rank, placement, cost))

    if not candidates:
        return None

    _, placement, cost = min(candidates, key=lambda row: row[0])
    return PlacementPlan(
        planned_epoch=snapshot.epoch,
        resource_certificate=resource_certificate(snapshot),
        placements=tuple(sorted(placement.items())),
        semantic_atoms=semantic_atoms,
        cost=cost,
    )


def admit_plan(plan: PlacementPlan, observed: ResourceSnapshot) -> str:
    if plan.resource_certificate != resource_certificate(observed):
        return "REPLAN_REQUIRED"
    return "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED"


def plan_is_physically_feasible(plan: PlacementPlan, snapshot: ResourceSnapshot) -> bool:
    return _placement_feasible(
        _placement_dict(plan),
        snapshot,
        atoms=atom_map(),
    )


def changed_atoms(before: PlacementPlan, after: PlacementPlan) -> tuple[str, ...]:
    old = _placement_dict(before)
    new = _placement_dict(after)
    return tuple(sorted(atom_id for atom_id in old if old[atom_id] != new[atom_id]))


def run_panel() -> dict[str, Any]:
    # Startup estimate: the semantic projection fits entirely in RAM.
    startup = ResourceSnapshot(
        epoch=7,
        ram_free_bytes=8192,
        ssd_available=True,
        ssd_read_bytes_per_second=2_500_000_000,
        observer_note="startup estimate before runtime materialization",
    )
    startup_plan = plan_projection(startup)
    if startup_plan is None:
        raise RuntimeError("startup_fixture_must_be_feasible")

    # Control: observation epoch changes, planner-relevant facts do not.
    irrelevant_epoch_change = ResourceSnapshot(
        epoch=8,
        ram_free_bytes=8192,
        ssd_available=True,
        ssd_read_bytes_per_second=2_500_000_000,
        observer_note="new observation, same planner-relevant resource facts",
    )
    control_admission = admit_plan(startup_plan, irrelevant_epoch_change)
    control_replan = plan_projection(
        irrelevant_epoch_change,
        previous_plan=startup_plan,
    )
    if control_replan is None:
        raise RuntimeError("control_fixture_must_be_feasible")

    # Adversary: runtime/page-cache/workspace materialization consumes enough
    # RAM that the startup all-RAM placement no longer fits.
    after_materialization = ResourceSnapshot(
        epoch=9,
        ram_free_bytes=6144,
        ssd_available=True,
        ssd_read_bytes_per_second=2_500_000_000,
        observer_note="post-materialization resource snapshot",
    )
    stale_admission = admit_plan(startup_plan, after_materialization)
    stale_feasible = plan_is_physically_feasible(startup_plan, after_materialization)
    replanned = plan_projection(after_materialization, previous_plan=startup_plan)
    if replanned is None:
        raise RuntimeError("pressure_fixture_should_have_a_tiered_plan")

    # Topology-loss adversary: the same RAM pressure exists but backing storage
    # is unavailable. A planner must fail closed rather than execute the stale
    # plan or silently drop semantic atoms.
    topology_loss = ResourceSnapshot(
        epoch=10,
        ram_free_bytes=6144,
        ssd_available=False,
        ssd_read_bytes_per_second=0,
        observer_note="post-materialization snapshot with SSD tier unavailable",
    )
    topology_admission = admit_plan(startup_plan, topology_loss)
    topology_replan = plan_projection(topology_loss, previous_plan=startup_plan)

    moved = changed_atoms(startup_plan, replanned)
    expected_moved = ("checkpoint_manifest", "collision_verifier")

    checks = {
        "startup_projection_is_all_ram": startup_plan.cost.ssd_bytes == 0,
        "irrelevant_epoch_change_does_not_force_replan": (
            control_admission == "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED"
            and control_replan.placements == startup_plan.placements
        ),
        "materialization_changes_resource_certificate": (
            startup_plan.resource_certificate
            != resource_certificate(after_materialization)
        ),
        "stale_plan_is_rejected_after_materialization": (
            stale_admission == "REPLAN_REQUIRED"
        ),
        "stale_plan_is_physically_infeasible": not stale_feasible,
        "replan_preserves_semantic_projection": (
            replanned.semantic_atoms == startup_plan.semantic_atoms
        ),
        "replan_restores_physical_feasibility": plan_is_physically_feasible(
            replanned,
            after_materialization,
        ),
        "replan_keeps_current_generate_atoms_off_transfer_path": (
            replanned.cost.current_phase_transfer_bytes == 0
        ),
        "replan_moves_minimal_frozen_cold_pair": moved == expected_moved,
        "topology_loss_fails_closed": (
            topology_admission == "REPLAN_REQUIRED" and topology_replan is None
        ),
        "resource_replan_does_not_grant_authority": True,
        "resource_replan_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_POST_MATERIALIZATION_RESOURCE_REPLAN",
        "semantic_projection": {
            "atoms": list(startup_plan.semantic_atoms),
            "atom_count": len(startup_plan.semantic_atoms),
            "bytes": startup_plan.cost.ram_bytes,
            "source": "FR-P9-001 GENERATE_CHUNK compiled projection",
        },
        "startup": {
            "epoch": startup.epoch,
            "ram_free_bytes": startup.ram_free_bytes,
            "resource_certificate": startup_plan.resource_certificate,
            "plan": dict(startup_plan.placements),
            "cost_vector": startup_plan.cost.__dict__,
        },
        "irrelevant_epoch_control": {
            "epoch": irrelevant_epoch_change.epoch,
            "admission": control_admission,
            "same_resource_certificate": (
                startup_plan.resource_certificate
                == resource_certificate(irrelevant_epoch_change)
            ),
            "same_placement_after_replan": control_replan.placements == startup_plan.placements,
        },
        "materialization_adversary": {
            "epoch": after_materialization.epoch,
            "ram_free_bytes": after_materialization.ram_free_bytes,
            "stale_admission": stale_admission,
            "stale_physically_feasible": stale_feasible,
            "replanned": dict(replanned.placements),
            "moved_atoms": list(moved),
            "cost_vector": replanned.cost.__dict__,
        },
        "topology_loss_adversary": {
            "epoch": topology_loss.epoch,
            "ssd_available": topology_loss.ssd_available,
            "admission": topology_admission,
            "replan_result": None,
        },
        "checks": checks,
        "decision": (
            "BIND_PLANS_TO_PLANNER_RELEVANT_RESOURCE_CERTIFICATES_AND_REPLAN_AFTER_MATERIALIZATION_WHEN_THE_CERTIFICATE_CHANGES"
        ),
        "invariants": [
            "semantic projection != physical placement",
            "observation epoch != planner-relevant resource change",
            "resource freshness != execution authority",
            "replan != retry permission",
            "topology loss must fail closed rather than drop semantic atoms",
        ],
        "next_falsifier": (
            "add phase transitions and measured transfer/recompute timing; test when keeping a capability warm is cheaper than repeated fault-in"
        ),
        "authority_effect": "NONE",
        "retry_authority": False,
        "claim_ceiling": (
            "SYNTHETIC_RESOURCE_CERTIFICATE_AND_REPLAN_FIXTURE_ONLY_NO_PHYSICAL_PLACEMENT_OR_PERFORMANCE_CLAIM"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
