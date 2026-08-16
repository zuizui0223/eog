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
EXPECTED_GEOGRAPHY_WORLD_COUNT = 4
EXPECTED_ENVIRONMENT_WORLD_COUNT = 8
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
    "geography_support_count",
    "geography_world_count",
    "geography_world_class",
    "environment_support_count",
    "environment_world_count",
    "environment_world_class",
    "geo_environment_class_disagreement",
    "supporting_world_ids",
    "unsupported_world_ids",
}
DECISION_RULE = (
    "PASS only if at least one connected-frequency/support-count level contains multiple "
    "distinct supporting-world identity sets AND multiple geography-versus-environment "
    "support decompositions, at least one row in such a group has geography-versus-"
    "environment class disagreement, and contingent rows exist. Otherwise FAIL."
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
        raise ValueError("world-ID field contains duplicates")
    return ids


def _as_bool(value: object) -> bool:
    text = str(value).strip().casefold()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _world_class(support_count: int, total_count: int) -> str:
    if support_count == 0:
        return "excluded_under_declared_scenarios"
    if support_count == total_count:
        return "robust"
    return "contingent"


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
    decompositions_by_support_count: dict[int, set[tuple[int, int]]] = defaultdict(set)
    rows_by_support_count: Counter[int] = Counter()
    parsed_rows: list[tuple[int, str, bool]] = []
    declared_universe: frozenset[str] | None = None

    for row in declared:
        if set(row) != columns:
            raise ValueError("all exploratory rows must have the same schema")

        world_count = int(row["world_count"])
        support_count = int(row["support_count"])
        geography_world_count = int(row["geography_world_count"])
        environment_world_count = int(row["environment_world_count"])
        if world_count != EXPECTED_WORLD_COUNT:
            raise ValueError(
                f"A-Islands exploratory universe must contain {EXPECTED_WORLD_COUNT} worlds"
            )
        if geography_world_count != EXPECTED_GEOGRAPHY_WORLD_COUNT:
            raise ValueError("A-Islands geography-only universe must contain four worlds")
        if environment_world_count != EXPECTED_ENVIRONMENT_WORLD_COUNT:
            raise ValueError("A-Islands environmental universe must contain eight worlds")
        if geography_world_count + environment_world_count != world_count:
            raise ValueError("geography/environment world families do not cover the universe")
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

        row_universe = frozenset((*supporting, *unsupported))
        if declared_universe is None:
            declared_universe = row_universe
            geography_ids = {world for world in row_universe if world.endswith("env_none")}
            if len(geography_ids) != EXPECTED_GEOGRAPHY_WORLD_COUNT:
                raise ValueError("world IDs do not identify exactly four geography-only worlds")
        elif row_universe != declared_universe:
            raise ValueError("candidate rows do not share one frozen world-ID universe")

        geo_support = sum(world.endswith("env_none") for world in supporting)
        env_support = support_count - geo_support
        if int(row["geography_support_count"]) != geo_support:
            raise ValueError("geography_support_count does not match supporting_world_ids")
        if int(row["environment_support_count"]) != env_support:
            raise ValueError("environment_support_count does not match supporting_world_ids")

        expected_frequency = support_count / world_count
        if abs(float(row["connected_frequency"]) - expected_frequency) > 1e-12:
            raise ValueError("connected_frequency does not equal support_count/world_count")

        expected_world_class = _world_class(support_count, world_count)
        expected_geo_class = _world_class(geo_support, geography_world_count)
        expected_env_class = _world_class(env_support, environment_world_count)
        if str(row["world_class"]) != expected_world_class:
            raise ValueError("world_class is inconsistent with support_count")
        if str(row["geography_world_class"]) != expected_geo_class:
            raise ValueError("geography_world_class is inconsistent with geography support")
        if str(row["environment_world_class"]) != expected_env_class:
            raise ValueError("environment_world_class is inconsistent with environment support")

        disagreement = _as_bool(row["geo_environment_class_disagreement"])
        if disagreement != (expected_geo_class != expected_env_class):
            raise ValueError("geo_environment_class_disagreement is inconsistent with family classes")

        identities_by_support_count[support_count].add(supporting)
        decompositions_by_support_count[support_count].add((geo_support, env_support))
        rows_by_support_count[support_count] += 1
        parsed_rows.append((support_count, expected_world_class, disagreement))

    identity_collision_levels = {
        level for level, identities in identities_by_support_count.items() if len(identities) > 1
    }
    decomposition_collision_levels = {
        level
        for level, decompositions in decompositions_by_support_count.items()
        if len(decompositions) > 1
    }
    informative_levels = tuple(sorted(identity_collision_levels & decomposition_collision_levels))
    informative_level_set = set(informative_levels)

    collision_rows = sum(rows_by_support_count[level] for level in informative_levels)
    interpretable_collision_rows = sum(
        1
        for support_count, _world_class_value, disagreement in parsed_rows
        if support_count in informative_level_set and disagreement
    )
    contingent_rows = sum(world_class == "contingent" for _, world_class, _ in parsed_rows)
    disagreement_rows = sum(disagreement for _, _, disagreement in parsed_rows)

    gate_pass = bool(
        informative_levels
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
        "support_counts_with_multiple_world_identities": sorted(identity_collision_levels),
        "support_counts_with_multiple_geo_environment_decompositions": sorted(
            decomposition_collision_levels
        ),
        "informative_frequency_collision_levels": list(informative_levels),
        "rows_in_informative_frequency_collision_groups": int(collision_rows),
        "interpretable_collision_rows": int(interpretable_collision_rows),
        "world_identity_variants_by_support_count": {
            str(level): len(identities_by_support_count[level])
            for level in sorted(identities_by_support_count)
        },
        "geo_environment_decomposition_variants_by_support_count": {
            str(level): len(decompositions_by_support_count[level])
            for level in sorted(decompositions_by_support_count)
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
