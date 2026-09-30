#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def require(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, flags=re.MULTILINE) is None:
        raise AssertionError(f"manuscript is missing or disagrees with frozen claim: {label}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manuscript",
        type=Path,
        default=ROOT / "manuscript/bam_identifiability/MANUSCRIPT_DRAFT_V2_1.md",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "manuscript/bam_identifiability/MANUSCRIPT_NUMERIC_AUDIT_V2.json",
    )
    args = parser.parse_args()

    manuscript = args.manuscript.read_text(encoding="utf-8")

    deterministic = load_json("validation/known_truth_bam_v3/result_summary_v3.json")
    restrictiveness = load_json(
        "validation/restrictiveness_ambiguity_v3_1/audit_summary_v3_1.json"
    )
    temporal = load_json(
        "validation/independent_stochastic_temporal_v3_2/result_summary_v3_2.json"
    )
    landscapes = load_json(
        "validation/multilandscape_stochastic_bam_v4/result_summary_v4.json"
    )
    measurement = load_json(
        "validation/bam_identifiability_theory_v1/"
        "targeted_measurement_exact_audit_summary_v1.json"
    )

    expected_counts = deterministic["pooled_unique_counts"]
    assert expected_counts == {
        "E0": 0,
        "E1": 25,
        "E2": 159,
        "E3": 275,
        "E4": 565,
        "E5": 768,
        "E6": 768,
    }
    assert deterministic["eligible_truth_count"] == 768
    assert deterministic["verdicts"]["G2_M_final_bottleneck"] == "REFUTED"

    assert restrictiveness["strict_support_inclusion_pair_count"] == 304
    assert restrictiveness["nesting_monotonicity_violations"] == 0
    assert restrictiveness["frozen_truth_scenarios"]["joint_ABM"] == {
        "support_size": 33,
        "compatible_world_count": 32,
    }
    assert restrictiveness["frozen_truth_scenarios"]["distance_limited"] == {
        "support_size": 96,
        "compatible_world_count": 4,
    }
    assert restrictiveness["frozen_truth_scenarios"]["barrier_limited"] == {
        "support_size": 96,
        "compatible_world_count": 4,
    }

    assert temporal["static_support_classes"]["count"] == 8
    assert temporal["temporal_signature_classes"]["count"] == 20
    assert temporal["static_M_equivalent_pair_count"] == 48
    assert temporal["realised_temporal_split_pair_count"] == 19
    assert temporal["temporal_strict_gain_runs"] == 256
    assert temporal["planned_runs"] == 384

    assert landscapes["planned_landscape_count"] == 8
    assert landscapes["eligible_landscape_count"] == 6
    assert landscapes["design_stop_count"] == 2
    assert landscapes["eligible_stochastic_runs"] == 1152

    maxima = measurement["exact_maximum_measurements"]
    assert maxima["A"] == 1
    assert maxima["B"] == 2
    assert maxima["AB_joint"] == 3
    assert maxima["M"] == 2
    assert measurement["truth_cases"] == 768
    assert measurement["failures"] == 0

    # Manuscript-facing frozen numeric claims.
    checks = {
        "positive-only zero bound": r"0/768",
        "evidence ladder": r"0 at E0, 25 at E1, 159 at E2, 275 at E3, 565 at E4, and 768 at both E5 and E6",
        "restrictiveness audit": r"304 strict positive-support inclusions and zero nesting violations",
        "joint ABM support": r"support size 33 and remained compatible with all 32 candidate worlds",
        "movement comparator": r"support size 96 and only four compatible worlds",
        "temporal classes": r"eight static support classes into 20 temporal signature classes",
        "temporal pairs": r"48 static M-equivalent pairs, 19 were split",
        "temporal strict gain": r"256/384 stochastic runs",
        "multilandscape denominator": r"six eligible landscapes contributed 1,152 stochastic runs",
        "design stops": r"two joint-fragmented landscapes remained DESIGN_STOP",
        "measurement maxima": r"one node for A, two for B, three for joint A\+B and two for M accessibility",
    }
    for label, pattern in checks.items():
        require(manuscript, pattern, label)

    result = {
        "schema": "eog.bam_identifiability.manuscript_numeric_audit.v2",
        "status": "PASS",
        "manuscript": str(args.manuscript.relative_to(ROOT)),
        "source_fingerprints": {
            "deterministic_v3": deterministic["result_fingerprint"],
            "restrictiveness_v3_1": restrictiveness["result_fingerprint"],
            "temporal_v3_2": temporal["result_fingerprint"],
            "multilandscape_v4": landscapes["result_fingerprint"],
            "measurement_exact_audit": measurement["result_fingerprint"],
        },
        "frozen_claims": {
            "evidence_ladder_counts": expected_counts,
            "truth_cases": 768,
            "restrictiveness_pairs": 304,
            "temporal_strict_gain_runs": 256,
            "temporal_runs": 384,
            "eligible_landscapes": 6,
            "design_stops": 2,
            "eligible_stochastic_runs": 1152,
            "exact_measurement_maxima": {
                "A": 1,
                "B": 2,
                "AB_joint": 3,
                "M": 2,
            },
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
