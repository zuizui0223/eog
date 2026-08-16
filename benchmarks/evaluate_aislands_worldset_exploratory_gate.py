#!/usr/bin/env python3
"""Evaluate the response-free A-Islands world-set exploratory development gate.

This benchmark asks a deliberately narrow question before any independent confirmation:
Does retaining the identities of the 12 frozen A-Islands analyst-choice scenarios expose
structure that the aggregate ``connected_frequency`` necessarily discards?

The gate is response-free. It consumes only the output of
``run_aislands_worldset_exploratory.py`` and rejects held-out incidence, AUC,
concordance, fitted pointwise support, or generic response/label fields.

This is exploratory development evidence on a previously viewed system. A PASS cannot
promote the integrated EOG framework; it only justifies freezing an independent
confirmatory ecological system. A FAIL stops this integrated direction by default.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


EXPECTED_WORLD_COUNT = 12
FORBIDDEN_COLUMNS = {
    "heldout_presence",
    "heldout_absence",
    "heldout_label",
    "support_auc",
    "reachability_auc",
    "concordance",
    "pointwise_support",
    "response",
    "label",
}
REQUIRED_COLUMNS = {
    "world_count",
    "support_count",
    "connected_frequency",
    "world_class",
    "geo_environment_class_disagreement",
    "supporting_world_ids",
    "unsupported_world_ids",
}
DECISION_RULE = (
    "PASS only if at least one connected-frequency/support-count level contains multiple "
    "distinct supporting-world identity sets, at least one row inside such a frequency-"
    "collision group also has geography-versus-environment class disagreement, and the "
    "candidate set contains contingent rows. Otherwise FAIL."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_world_ids(value: object) -> tuple[str, ...]:
    ids = tuple(sorted(item for item in str(value).split(";") if item))
    if len(ids) != len(set(ids)):
        raise ValueError("supporting_world_ids contains duplicates")
    return ids


def _as_bool(value: object) -> bool:
    text = str(value).strip().casefold()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def evaluate_rows(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    declared = [dict(row) for row in rows]
    if not declared:
        raise ValueError("at least one exploratory candidate row is required")

    columns = set(declared[0])
    forbidden = sorted(columns & FORBIDDEN_COLUMNS)
    if forbidden:
        raise ValueError(f"response-bearing columns are forbidden: {forbidden}")
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        raise ValueError(f"missing required exploratory columns: {missing}")

    identities_by_support_count: dict[int, set[tuple[str, ...]]] = defaultdict(set)
    rows_by_support_count: Counter[int] = Counter()
    parsed_rows: list[tuple[int, tuple[str, ...], str, bool]] = []
    world_counts: set[int] = set()

    for row in declared:
        if set(row) != columns:
            raise ValueError("all exploratory rows must have the same schema")
        world_count = int(row["world_count"])
        support_count = int(row["support_count"])
        if world_count != EXPECTED_WORLD_COUNT:
            raise ValueError(
                f"A-Islands exploratory universe must contain {EXPECTED_WORLD_COUNT} worlds"
            )
        if support_count < 0 or support_count > world_count:
            raise ValueError("support_count lies outside the declared world universe")

        supporting = _parse_world_ids(row["supporting_world_ids"])
        unsupported = _parse_world_ids(row["unsupported_world_ids"])
        if len(supporting) != support_count:
            raise ValueError("support_count does not match supporting_world_ids")
        if set(supporting) & set(unsupported):
            raise ValueError("supporting and unsupported world IDs overlap")
        if len(supporting) + len(unsupported) != world_count:
            raise ValueError("supporting/unsupported IDs do not cover the declared worlds")

        expected_frequency = support_count / world_count
        if abs(float(row["connected_frequency"]) - expected_frequency) > 1e-12:
            raise ValueError("connected_frequency does not equal support_count/world_count")

        world_class = str(row["world_class"])
        if support_count == 0:
            expected_class = "excluded_under_declared_scenarios"
        elif support_count == world_count:
            expected_class = "robust"
        else:
            expected_class = "contingent"
        if world_class != expected_class:
            raise ValueError("world_class is inconsistent with support_count")

        disagreement = _as_bool(row["geo_environment_class_disagreement"])
        identities_by_support_count[support_count].add(supporting)
        rows_by_support_count[support_count] += 1
        parsed_rows.append((support_count, supporting, world_class, disagreement))
        world_counts.add(world_count)

    if world_counts != {EXPECTED_WORLD_COUNT}:
        raise ValueError("exploratory rows do not share the frozen A-Islands universe")

    collision_levels = tuple(
        sorted(
            support_count
            for support_count, identities in identities_by_support_count.items()
            if len(identities) > 1
        )
    )
    collision_level_set = set(collision_levels)
    collision_rows = sum(rows_by_support_count[level] for level in collision_levels)
    interpretable_collision_rows = sum(
        1
        for support_count, _identity, _world_class, disagreement in parsed_rows
        if support_count in collision_level_set and disagreement
    )
    contingent_rows = sum(world_class == "contingent" for _, _, world_class, _ in parsed_rows)
    disagreement_rows = sum(disagreement for _, _, _, disagreement in parsed_rows)

    gate_pass = bool(
        collision_levels
        and interpretable_collision_rows > 0
        and contingent_rows > 0
    )

    return {
        "status": (
            "exploratory_world_identity_added_information"
            if gate_pass
            else "exploratory_no_world_identity_added_information"
        ),
        "gate_pass": gate_pass,
        "decision_rule": DECISION_RULE,
        "claim_boundary": (
            "Previously viewed A-Islands system; response-free exploratory development "
            "evidence only. PASS can justify an independently frozen confirmation but "
            "cannot itself promote the integrated EOG framework."
        ),
        "n_candidate_rows": len(declared),
        "n_contingent_rows": int(contingent_rows),
        "geo_environment_class_disagreement_count": int(disagreement_rows),
        "support_counts_with_multiple_world_identities": list(collision_levels),
        "rows_in_frequency_collision_groups": int(collision_rows),
        "interpretable_collision_rows": int(interpretable_collision_rows),
        "world_identity_variants_by_support_count": {
            str(level): len(identities_by_support_count[level])
            for level in sorted(identities_by_support_count)
        },
    }


def run(rows_path: Path, output_path: Path) -> dict[str, object]:
    with rows_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        result = evaluate_rows(reader)
    result["rows_sha256"] = _sha256(rows_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.rows, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
