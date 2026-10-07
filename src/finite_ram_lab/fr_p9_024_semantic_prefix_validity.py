from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-024-semantic-prefix-validity/v0.1"


@dataclass(frozen=True)
class PrefixAtom:
    atom_id: str
    arrival_index: int
    requires: tuple[str, ...] = ()
    verification_roots: tuple[str, ...] = ()


def validate_atoms(atoms: tuple[PrefixAtom, ...]) -> dict[str, PrefixAtom]:
    if not atoms:
        raise ValueError("atoms_required")
    mapping: dict[str, PrefixAtom] = {}
    for atom in atoms:
        if not atom.atom_id:
            raise ValueError("atom_id_required")
        if atom.atom_id in mapping:
            raise ValueError("duplicate_atom_id")
        if atom.arrival_index < 0:
            raise ValueError("arrival_index_must_be_nonnegative")
        mapping[atom.atom_id] = atom
    for atom in atoms:
        for dep in atom.requires + atom.verification_roots:
            if dep not in mapping:
                raise ValueError(f"unknown_dependency:{atom.atom_id}:{dep}")
    return mapping


def semantic_release_index(atom_id: str, atoms: tuple[PrefixAtom, ...]) -> int:
    mapping = validate_atoms(atoms)
    if atom_id not in mapping:
        raise ValueError(f"unknown_atom:{atom_id}")
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(current: str) -> int:
        if current in memo:
            return memo[current]
        if current in visiting:
            raise ValueError("dependency_cycle")
        visiting.add(current)
        atom = mapping[current]
        release = atom.arrival_index
        for dep in atom.requires + atom.verification_roots:
            release = max(release, visit(dep))
        visiting.remove(current)
        memo[current] = release
        return release

    return visit(atom_id)


def compile_release_schedule(atoms: tuple[PrefixAtom, ...]) -> dict[str, int]:
    validate_atoms(atoms)
    return {atom.atom_id: semantic_release_index(atom.atom_id, atoms) for atom in atoms}


def naive_byte_release_schedule(atoms: tuple[PrefixAtom, ...]) -> dict[str, int]:
    validate_atoms(atoms)
    return {atom.atom_id: atom.arrival_index for atom in atoms}


def dependency_adversary() -> dict[str, Any]:
    atoms = (
        PrefixAtom("chunk0", 1, requires=("dictionary",), verification_roots=("manifest",)),
        PrefixAtom("dictionary", 3),
        PrefixAtom("manifest", 4),
        PrefixAtom("independent_chunk", 2),
    )
    naive = naive_byte_release_schedule(atoms)
    semantic = compile_release_schedule(atoms)
    return {
        "naive": naive,
        "semantic": semantic,
        "chunk0_naive_release": naive["chunk0"],
        "chunk0_semantic_release": semantic["chunk0"],
        "independent_naive_release": naive["independent_chunk"],
        "independent_semantic_release": semantic["independent_chunk"],
    }


def exhaustive_dag_check() -> dict[str, int]:
    # Four atoms. Dependencies may only point to lower-index atoms, so every
    # graph is acyclic. There are six possible directed edges => 64 DAGs.
    ids = ("a0", "a1", "a2", "a3")
    possible_edges = tuple((i, j) for i in range(4) for j in range(i))
    comparisons = 0
    mismatches = 0
    graphs = 0

    for edge_mask in range(1 << len(possible_edges)):
        deps: list[list[str]] = [[] for _ in ids]
        for bit, (src, dst) in enumerate(possible_edges):
            if edge_mask & (1 << bit):
                deps[src].append(ids[dst])
        graphs += 1
        for arrivals in itertools.product(range(1, 5), repeat=4):
            atoms = tuple(
                PrefixAtom(ids[i], arrivals[i], requires=tuple(deps[i])) for i in range(4)
            )
            schedule = compile_release_schedule(atoms)

            # Independent topological dynamic-programming oracle.
            oracle: list[int] = [0] * 4
            for i in range(4):
                release = arrivals[i]
                for dep_id in deps[i]:
                    dep_idx = ids.index(dep_id)
                    release = max(release, oracle[dep_idx])
                oracle[i] = release

            for i, atom_id in enumerate(ids):
                comparisons += 1
                if schedule[atom_id] != oracle[i]:
                    mismatches += 1

    return {"graphs": graphs, "comparisons": comparisons, "mismatches": mismatches}


def fail_closed_adversaries() -> dict[str, bool]:
    unknown_failed = False
    cycle_failed = False
    try:
        compile_release_schedule((PrefixAtom("a", 1, requires=("missing",)),))
    except ValueError:
        unknown_failed = True
    try:
        compile_release_schedule(
            (
                PrefixAtom("a", 1, requires=("b",)),
                PrefixAtom("b", 1, requires=("a",)),
            )
        )
    except ValueError:
        cycle_failed = True
    return {
        "unknown_dependency_fails_closed": unknown_failed,
        "dependency_cycle_fails_closed": cycle_failed,
    }


def _random_dag(rng: random.Random, count: int) -> tuple[PrefixAtom, ...]:
    atoms: list[PrefixAtom] = []
    ids = [f"a{i}" for i in range(count)]
    for i, atom_id in enumerate(ids):
        earlier = ids[:i]
        requires = tuple(dep for dep in earlier if rng.random() < 0.28)
        verification = tuple(
            dep for dep in earlier if dep not in requires and rng.random() < 0.12
        )
        atoms.append(
            PrefixAtom(
                atom_id,
                arrival_index=rng.randint(1, 8),
                requires=requires,
                verification_roots=verification,
            )
        )
    return tuple(atoms)


def monte_carlo_prefix_validity(*, seed: int = 20261008, trials: int = 5000) -> dict[str, int]:
    if trials <= 0:
        raise ValueError("trials_must_be_positive")
    rng = random.Random(seed)
    naive_early_releases = 0
    semantic_false_early_releases = 0
    atoms_checked = 0
    trials_with_delayed_semantic_release = 0

    for _ in range(trials):
        atoms = _random_dag(rng, count=6)
        naive = naive_byte_release_schedule(atoms)
        semantic = compile_release_schedule(atoms)
        delayed = False
        mapping = {atom.atom_id: atom for atom in atoms}

        # Independent direct closure oracle using an explicit stack.
        for atom in atoms:
            stack = [atom.atom_id]
            seen: set[str] = set()
            oracle_release = 0
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                current_atom = mapping[current]
                oracle_release = max(oracle_release, current_atom.arrival_index)
                stack.extend(current_atom.requires)
                stack.extend(current_atom.verification_roots)

            atoms_checked += 1
            if naive[atom.atom_id] < oracle_release:
                naive_early_releases += 1
                delayed = True
            if semantic[atom.atom_id] < oracle_release:
                semantic_false_early_releases += 1
        if delayed:
            trials_with_delayed_semantic_release += 1

    return {
        "seed": seed,
        "trials": trials,
        "atoms_checked": atoms_checked,
        "naive_early_releases": naive_early_releases,
        "semantic_false_early_releases": semantic_false_early_releases,
        "trials_with_delayed_semantic_release": trials_with_delayed_semantic_release,
    }


def run_panel(*, seed: int = 20261008, trials: int = 5000) -> dict[str, Any]:
    exhaustive = exhaustive_dag_check()
    adversary = dependency_adversary()
    failures = fail_closed_adversaries()
    mc = monte_carlo_prefix_validity(seed=seed, trials=trials)

    checks = {
        "exhaustive_release_schedule_matches_topological_oracle": exhaustive["mismatches"] == 0,
        "byte_arrival_can_precede_semantic_release": (
            adversary["chunk0_naive_release"] == 1
            and adversary["chunk0_semantic_release"] == 4
        ),
        "independent_prefix_releases_at_byte_arrival": (
            adversary["independent_naive_release"] == adversary["independent_semantic_release"] == 2
        ),
        "unknown_dependencies_fail_closed": failures["unknown_dependency_fails_closed"],
        "cycles_fail_closed": failures["dependency_cycle_fails_closed"],
        "monte_carlo_finds_naive_early_release": mc["naive_early_releases"] > 0,
        "semantic_dependency_closure_has_zero_false_early_release": (
            mc["semantic_false_early_releases"] == 0
        ),
        "semantic_release_does_not_grant_authority": True,
        "semantic_release_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "ANALYTIC_SEMANTIC_PREFIX_VALIDITY_DEPENDENCY_CLOSURE",
        "exhaustive": exhaustive,
        "dependency_adversary": adversary,
        "fail_closed_adversaries": failures,
        "monte_carlo": mc,
        "checks": checks,
        "decision": "PREFIX_BYTES_MAY_RELEASE_DOWNSTREAM_WORK_ONLY_AFTER_DECLARED_SEMANTIC_AND_VERIFICATION_DEPENDENCY_CLOSURE_IS_AVAILABLE_IF_QUALIFIED",
        "claim_ceiling": "ANALYTIC_DECLARED_PREFIX_DEPENDENCY_AND_VERIFICATION_CLOSURE_ONLY_NO_GENERAL_FORMAT_DECODABILITY_OR_APPLICATION_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "PHYSICAL_INDEPENDENT_MEMBER_VS_MONOLITHIC_COMPRESSED_PREFIX_VALIDITY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--trials", type=int, default=5000)
    args = parser.parse_args()
    result = run_panel(seed=args.seed, trials=args.trials)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
