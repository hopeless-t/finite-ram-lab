from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

SCHEMA = "finite-ram-lab.fr-p9-001-minimum-sufficient-resident-projection/v0.1"


@dataclass(frozen=True)
class CanonicalAtom:
    atom_id: str
    size_bytes: int
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkUnit:
    work_id: str
    phase: str
    decision_roots: tuple[str, ...]
    verification_roots: tuple[str, ...]
    recovery_roots: tuple[str, ...]
    capability_roots: tuple[str, ...]


ATOMS = (
    CanonicalAtom("goal", 96),
    CanonicalAtom("world_seed", 64),
    CanonicalAtom("chunk_recipe", 384, ("world_seed",)),
    CanonicalAtom("topology_rules", 768),
    CanonicalAtom(
        "generator_capability",
        2048,
        ("chunk_recipe", "topology_rules"),
    ),
    CanonicalAtom(
        "geometry_manifest",
        1024,
        ("generator_capability",),
    ),
    CanonicalAtom(
        "render_materials",
        4096,
        ("geometry_manifest",),
    ),
    CanonicalAtom(
        "collision_rules",
        640,
        ("topology_rules",),
    ),
    CanonicalAtom(
        "collision_verifier",
        1536,
        ("collision_rules", "geometry_manifest"),
    ),
    CanonicalAtom(
        "provenance",
        512,
        ("goal", "chunk_recipe"),
    ),
    CanonicalAtom(
        "checkpoint_manifest",
        384,
        ("provenance",),
    ),
    CanonicalAtom(
        "recovery_recipe",
        512,
        ("checkpoint_manifest", "generator_capability"),
    ),
    CanonicalAtom("marketplace_catalog", 8192),
    CanonicalAtom("distant_world_chunk", 16384),
    CanonicalAtom("authoring_ui_state", 3072),
    CanonicalAtom("analytics_history", 6144),
)


WORK_UNITS = (
    WorkUnit(
        work_id="GENERATE_CHUNK",
        phase="GENERATE",
        decision_roots=("goal", "generator_capability"),
        verification_roots=("collision_verifier", "provenance"),
        recovery_roots=("recovery_recipe",),
        capability_roots=("generator_capability", "collision_verifier"),
    ),
    WorkUnit(
        work_id="RENDER_NEAR_FIELD",
        phase="FRAME",
        decision_roots=("render_materials",),
        verification_roots=("geometry_manifest",),
        recovery_roots=("checkpoint_manifest",),
        capability_roots=(),
    ),
    WorkUnit(
        work_id="VERIFY_COLLISION",
        phase="VERIFY",
        decision_roots=("collision_verifier",),
        verification_roots=("provenance",),
        recovery_roots=("checkpoint_manifest",),
        capability_roots=("collision_verifier",),
    ),
)


def atom_map(
    atoms: Iterable[CanonicalAtom] = ATOMS,
) -> dict[str, CanonicalAtom]:
    rows = tuple(atoms)
    mapping = {
        atom.atom_id: atom
        for atom in rows
    }
    if len(mapping) != len(rows):
        raise ValueError("duplicate_atom_id")

    for atom in rows:
        if atom.size_bytes <= 0:
            raise ValueError(
                "atom_size_must_be_positive"
            )
        for dependency in atom.requires:
            if dependency not in mapping:
                raise ValueError(
                    "missing_dependency:"
                    f"{atom.atom_id}:"
                    f"{dependency}"
                )

    return mapping


def closure(
    roots: Iterable[str],
    *,
    atoms: dict[str, CanonicalAtom],
) -> frozenset[str]:
    resolved: set[str] = set()
    visiting: set[str] = set()

    def visit(atom_id: str) -> None:
        if atom_id in resolved:
            return
        if atom_id in visiting:
            raise ValueError(
                f"dependency_cycle:{atom_id}"
            )
        if atom_id not in atoms:
            raise ValueError(
                f"unknown_atom:{atom_id}"
            )

        visiting.add(atom_id)
        for dependency in (
            atoms[atom_id].requires
        ):
            visit(dependency)
        visiting.remove(atom_id)
        resolved.add(atom_id)

    for root in roots:
        visit(root)

    return frozenset(resolved)


def contract_requirements(
    work: WorkUnit,
    *,
    atoms: dict[str, CanonicalAtom],
) -> dict[str, frozenset[str]]:
    return {
        "decision": closure(
            work.decision_roots,
            atoms=atoms,
        ),
        "verification": closure(
            work.verification_roots,
            atoms=atoms,
        ),
        "recovery": closure(
            work.recovery_roots,
            atoms=atoms,
        ),
        "capability": closure(
            work.capability_roots,
            atoms=atoms,
        ),
    }


def compile_projection(
    work: WorkUnit,
    *,
    atoms: dict[str, CanonicalAtom],
) -> frozenset[str]:
    requirements = contract_requirements(
        work,
        atoms=atoms,
    )
    selected: set[str] = set()
    for required in requirements.values():
        selected.update(required)
    return frozenset(selected)


def compile_decision_only_projection(
    work: WorkUnit,
    *,
    atoms: dict[str, CanonicalAtom],
) -> frozenset[str]:
    return closure(
        work.decision_roots,
        atoms=atoms,
    )


def evaluate_projection(
    projection: frozenset[str],
    work: WorkUnit,
    *,
    atoms: dict[str, CanonicalAtom],
) -> dict[str, bool]:
    requirements = contract_requirements(
        work,
        atoms=atoms,
    )
    return {
        plane: required.issubset(
            projection
        )
        for plane, required
        in requirements.items()
    }


def projection_bytes(
    projection: Iterable[str],
    *,
    atoms: dict[str, CanonicalAtom],
) -> int:
    return sum(
        atoms[atom_id].size_bytes
        for atom_id in projection
    )


def _minimality_witnesses(
    projection: frozenset[str],
    work: WorkUnit,
    *,
    atoms: dict[str, CanonicalAtom],
) -> dict[str, list[str]]:
    witnesses: dict[str, list[str]] = {}

    for atom_id in sorted(projection):
        reduced = frozenset(
            item
            for item in projection
            if item != atom_id
        )
        evaluation = evaluate_projection(
            reduced,
            work,
            atoms=atoms,
        )
        broken_planes = sorted(
            plane
            for plane, passed
            in evaluation.items()
            if not passed
        )
        witnesses[atom_id] = broken_planes

    return witnesses


def run_panel() -> dict[str, Any]:
    atoms = atom_map()
    full_projection = frozenset(atoms)
    full_bytes = projection_bytes(
        full_projection,
        atoms=atoms,
    )

    work_rows: list[dict[str, Any]] = []
    compiled_total = 0
    decision_only_total = 0
    full_total = 0
    decision_only_false_positive_count = 0
    compiled_mismatches = 0
    minimality_failures: list[
        dict[str, str]
    ] = []
    compiled_sets: list[
        frozenset[str]
    ] = []

    for work in WORK_UNITS:
        compiled = compile_projection(
            work,
            atoms=atoms,
        )
        decision_only = (
            compile_decision_only_projection(
                work,
                atoms=atoms,
            )
        )
        full_evaluation = evaluate_projection(
            full_projection,
            work,
            atoms=atoms,
        )
        compiled_evaluation = (
            evaluate_projection(
                compiled,
                work,
                atoms=atoms,
            )
        )
        decision_evaluation = (
            evaluate_projection(
                decision_only,
                work,
                atoms=atoms,
            )
        )

        if (
            compiled_evaluation
            != full_evaluation
        ):
            compiled_mismatches += 1

        if (
            decision_evaluation[
                "decision"
            ]
            and not all(
                decision_evaluation.values()
            )
        ):
            decision_only_false_positive_count += 1

        witnesses = _minimality_witnesses(
            compiled,
            work,
            atoms=atoms,
        )
        for atom_id, broken_planes in (
            witnesses.items()
        ):
            if not broken_planes:
                minimality_failures.append(
                    {
                        "work_id": (
                            work.work_id
                        ),
                        "atom_id": atom_id,
                    }
                )

        compiled_bytes = projection_bytes(
            compiled,
            atoms=atoms,
        )
        decision_only_bytes = (
            projection_bytes(
                decision_only,
                atoms=atoms,
            )
        )

        full_total += full_bytes
        compiled_total += compiled_bytes
        decision_only_total += (
            decision_only_bytes
        )
        compiled_sets.append(compiled)

        work_rows.append(
            {
                "work_id": work.work_id,
                "phase": work.phase,
                "full_bytes": full_bytes,
                "compiled_bytes": (
                    compiled_bytes
                ),
                "decision_only_bytes": (
                    decision_only_bytes
                ),
                "compiled_fraction": (
                    compiled_bytes
                    / full_bytes
                ),
                "compiled_atoms": sorted(
                    compiled
                ),
                "decision_only_atoms": (
                    sorted(decision_only)
                ),
                "full_contract": (
                    full_evaluation
                ),
                "compiled_contract": (
                    compiled_evaluation
                ),
                "decision_only_contract": (
                    decision_evaluation
                ),
                "minimality_witnesses": (
                    witnesses
                ),
            }
        )

    phase_specific = (
        len(
            {
                tuple(sorted(items))
                for items in compiled_sets
            }
        )
        == len(compiled_sets)
    )
    compiled_savings_fraction = (
        1.0
        - compiled_total
        / full_total
    )
    decision_only_extra_savings_fraction = (
        1.0
        - decision_only_total
        / full_total
    )

    checks = {
        "canonical_universe_has_cold_irrelevant_atoms": (
            any(
                atom.atom_id
                in {
                    "marketplace_catalog",
                    "distant_world_chunk",
                    "authoring_ui_state",
                    "analytics_history",
                }
                for atom in ATOMS
            )
        ),
        "compiled_projection_matches_full_contract_for_every_work_unit": (
            compiled_mismatches == 0
        ),
        "compiled_projection_is_inclusion_minimal_for_declared_contract": (
            not minimality_failures
        ),
        "decision_only_slice_is_caught_as_insufficient": (
            decision_only_false_positive_count
            == len(WORK_UNITS)
        ),
        "compiled_projection_changes_by_phase_or_work": (
            phase_specific
        ),
        "compiled_resident_bytes_are_lower_than_full": (
            compiled_total < full_total
        ),
        "compiled_saves_at_least_20pct_resident_bytes_on_fixture": (
            compiled_savings_fraction
            >= 0.20
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "classification": (
            "SYNTHETIC_CANONICAL_TO_MINIMUM_SUFFICIENT_RESIDENT_PROJECTION"
        ),
        "fixture": {
            "canonical_atom_count": (
                len(ATOMS)
            ),
            "canonical_bytes": full_bytes,
            "work_unit_count": (
                len(WORK_UNITS)
            ),
            "phases": [
                work.phase
                for work in WORK_UNITS
            ],
        },
        "resident_surface": {
            "full_byte_rounds": full_total,
            "compiled_byte_rounds": (
                compiled_total
            ),
            "decision_only_byte_rounds": (
                decision_only_total
            ),
            "compiled_savings_fraction": (
                compiled_savings_fraction
            ),
            "decision_only_extra_savings_fraction": (
                decision_only_extra_savings_fraction
            ),
        },
        "contract": {
            "planes": [
                "decision",
                "verification",
                "recovery",
                "capability",
            ],
            "rule": (
                "runtime projection must preserve every declared plane, not decision output alone"
            ),
        },
        "work_units": work_rows,
        "adversary": {
            "decision_only_false_positive_count": (
                decision_only_false_positive_count
            ),
            "interpretation": (
                "a projection can preserve the immediate decision while silently dropping verification or recovery state; output equality alone is not a sufficient oracle"
            ),
        },
        "minimality": {
            "failures": minimality_failures,
            "interpretation": (
                "every atom selected by the compiler is necessary for at least one declared contract plane on this synthetic fixture"
            ),
        },
        "checks": checks,
        "decision": (
            "TREAT_CANONICAL_STATE_AS_BACKING_TRUTH_AND_COMPILE_A_MINIMUM_SUFFICIENT_RUNTIME_PROJECTION_PER_WORK_UNIT"
        ),
        "pcg_transfer": (
            "the same split maps naturally to world truth versus frame/generation/verification/recovery projections"
        ),
        "next_falsifier": (
            "add measured topology and migration costs; test whether semantic sufficiency remains correct when the cheapest physical placement changes after observation"
        ),
        "claim_ceiling": (
            "SYNTHETIC_DECLARED_DEPENDENCY_FIXTURE_ONLY_NO_PHYSICAL_RAM_OR_PCG_PERFORMANCE_CLAIM"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
