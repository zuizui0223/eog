#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

try:
    from benchmarks import run_eog_arrival_role_symmetry_v32 as v32
    from benchmarks import run_eog_original_idea_leopold_history_retention_v28 as v28
    from benchmarks import run_eog_grassland_above_below_history_retention_v30 as v30
except ModuleNotFoundError:
    import run_eog_arrival_role_symmetry_v32 as v32
    import run_eog_original_idea_leopold_history_retention_v28 as v28
    import run_eog_grassland_above_below_history_retention_v30 as v30

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_role_mapping_specificity_v33/protocol_v33.json"
V32 = ROOT / "validation/eog_arrival_role_symmetry_v32/result_summary_v32.json"


def _mapping_key(mapping: dict[str, str], histories: list[str]) -> str:
    return "|".join(f"{history}->{mapping[history]}" for history in histories)


def _all_bijections(histories: list[str], identities: list[str]) -> list[dict[str, str]]:
    return [
        dict(zip(histories, permutation, strict=True))
        for permutation in itertools.permutations(identities)
    ]


def _summarize_mapping_ensemble(
    rows: list[dict[str, object]],
    correct_key: str,
) -> dict[str, object]:
    if len({str(row["mapping"]) for row in rows}) != len(rows):
        raise RuntimeError("mapping ensemble contains duplicate mappings")
    correct_rows = [row for row in rows if row["mapping"] == correct_key]
    if len(correct_rows) != 1:
        raise RuntimeError("correct mapping must occur exactly once")
    correct = correct_rows[0]
    correct_r2 = float(correct["partial_r2"])
    incorrect = np.asarray(
        [float(row["partial_r2"]) for row in rows if row["mapping"] != correct_key],
        dtype=float,
    )
    all_scores = np.asarray([float(row["partial_r2"]) for row in rows], dtype=float)
    tol = 1e-12
    rank = 1 + int(np.sum(all_scores > correct_r2 + tol))
    tail = float(np.sum(all_scores >= correct_r2 - tol) / all_scores.size)
    ordered = sorted(
        rows,
        key=lambda row: (-float(row["partial_r2"]), str(row["mapping"])),
    )
    return {
        "correct_mapping": correct_key,
        "correct_partial_r2": correct_r2,
        "incorrect_mapping_count": int(incorrect.size),
        "incorrect_mapping_median_r2": float(np.median(incorrect)),
        "incorrect_mapping_min_r2": float(np.min(incorrect)),
        "incorrect_mapping_max_r2": float(np.max(incorrect)),
        "correct_minus_incorrect_median": float(correct_r2 - np.median(incorrect)),
        "correct_rank_descending": int(rank),
        "exact_upper_tail_mapping_probability": tail,
        "top_five_mappings": ordered[:5],
    }


def _score_v28(protocol: dict, authoritative32: dict) -> dict[str, object]:
    manifest = json.loads(v28.MANIFEST.read_text(encoding="utf-8"))
    source = {
        key: v28.download_source(path, blob)
        for key, (path, blob) in v28.SOURCE.items()
    }
    inputs = v28.build_inputs(source, manifest)
    matrix = np.asarray(inputs["corrected"], dtype=float)
    history = np.asarray(inputs["treatment"], dtype=object)
    context = np.asarray(inputs["genotype"], dtype=object)

    spec = protocol["systems"]["v28_microbiome"]
    histories = list(spec["histories"])
    identities = list(spec["identities"])
    mappings = _all_bijections(histories, identities)
    if len(mappings) != 120:
        raise RuntimeError(f"expected 120 v28 mappings, got {len(mappings)}")

    rows = []
    for mapping in mappings:
        transformed, _ = v32._role_align(
            matrix,
            history,
            identities,
            mapping,
        )
        for original, changed in zip(matrix, transformed, strict=True):
            if not np.array_equal(np.sort(original), np.sort(changed)):
                raise RuntimeError("v28 mapping changed row abundance multiset")
        distance = v28.bray_curtis(transformed)
        partial_r2 = v28.partial_distance_fast(distance, context, history)
        rows.append(
            {
                "mapping": _mapping_key(mapping, histories),
                "partial_r2": float(partial_r2),
            }
        )

    correct_mapping = {history_name: history_name for history_name in histories}
    correct_key = _mapping_key(correct_mapping, histories)
    summary = _summarize_mapping_ensemble(rows, correct_key)
    expected = float(
        authoritative32["v28_microbiome"]["role_aligned_R2"]
    )
    if not np.isclose(summary["correct_partial_r2"], expected, atol=1e-12, rtol=0):
        raise RuntimeError(
            f"v28 correct-mapping gate failed: {summary['correct_partial_r2']} vs {expected}"
        )

    criterion_gap = summary["correct_minus_incorrect_median"] > 0
    criterion_tail = (
        summary["exact_upper_tail_mapping_probability"]
        <= float(spec["primary_prediction"]["exact_upper_tail_mapping_probability_max"])
    )
    return {
        "mapping_count": len(rows),
        **summary,
        "primary_criteria": {
            "correct_above_incorrect_median": bool(criterion_gap),
            "exact_tail_at_or_below_0_05": bool(criterion_tail),
            "supported": bool(criterion_gap and criterion_tail),
        },
        "gates": {
            "v32_correct_role_R2_reproduced": True,
            "all_row_multisets_preserved": True,
            "exactly_120_unique_bijections": True,
        },
    }


def _score_v30(protocol: dict, authoritative32: dict) -> dict[str, object]:
    source_protocol = json.loads(v30.PROTOCOL.read_text(encoding="utf-8"))
    source = source_protocol["source"]
    payloads = {}
    for key in ("shoot", "root", "dictionary"):
        file_spec = source["files"][key]
        payloads[key] = v30._download(
            source["repository"],
            source["pinned_commit"],
            file_spec["path"],
            file_spec["blob_sha"],
        )
    panel = v30._build_panel(
        v30._read_tsv(payloads["shoot"]),
        v30._read_tsv(payloads["root"]),
        source_protocol,
    )
    v30._validate_primary(panel, source_protocol)
    rows0 = panel["rows"]
    matrix = np.vstack([row["shoot"] for row in rows0]).astype(float)
    history = np.asarray([row["history"] for row in rows0], dtype=object)
    block = np.asarray([row["replicate"] for row in rows0], dtype=object)

    spec = protocol["systems"]["v30_grassland"]
    histories = list(spec["histories"])
    identities = list(spec["identities"])
    mappings = _all_bijections(histories, identities)
    if len(mappings) != 6:
        raise RuntimeError(f"expected 6 v30 mappings, got {len(mappings)}")

    rows = []
    for mapping in mappings:
        transformed, _ = v32._role_align(
            matrix,
            history,
            identities,
            mapping,
        )
        for original, changed in zip(matrix, transformed, strict=True):
            if not np.array_equal(np.sort(original), np.sort(changed)):
                raise RuntimeError("v30 mapping changed row abundance multiset")
        distance = v30._bray_curtis(transformed)
        reduced, full = v30._designs(block, history)
        partial_r2 = v30._partial_distance(distance, reduced, full)
        rows.append(
            {
                "mapping": _mapping_key(mapping, histories),
                "partial_r2": float(partial_r2),
            }
        )

    correct_mapping = dict(spec["correct_mapping"])
    correct_key = _mapping_key(correct_mapping, histories)
    summary = _summarize_mapping_ensemble(rows, correct_key)
    expected = float(
        authoritative32["v30_grassland"]["role_aligned_R2"]
    )
    if not np.isclose(summary["correct_partial_r2"], expected, atol=1e-12, rtol=0):
        raise RuntimeError(
            f"v30 correct-mapping gate failed: {summary['correct_partial_r2']} vs {expected}"
        )

    return {
        "mapping_count": len(rows),
        **summary,
        "all_mappings": sorted(
            rows,
            key=lambda row: (-float(row["partial_r2"]), str(row["mapping"])),
        ),
        "gates": {
            "v32_correct_role_R2_reproduced": True,
            "all_row_multisets_preserved": True,
            "exactly_6_unique_bijections": True,
        },
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v33_placebo_mapping_scoring":
        raise RuntimeError("v33 protocol is not frozen")
    authoritative32 = json.loads(V32.read_text(encoding="utf-8"))

    microbiome = _score_v28(protocol, authoritative32)
    grassland = _score_v30(protocol, authoritative32)

    result = {
        "schema": "eog.role_mapping_specificity.result.v33",
        "status": "completed_frozen_mapping_specificity_audit",
        "primary_v28_prediction_supported": bool(
            microbiome["primary_criteria"]["supported"]
        ),
        "systems": {
            "v28_microbiome": microbiome,
            "v30_grassland": grassland,
        },
        "interpretation_contract": {
            "mapping_probability_role": (
                "finite_transformation_specificity_comparison_not_causal_randomization_p"
            )
        },
        "claim_boundary": protocol["claim_boundary"],
    }
    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
