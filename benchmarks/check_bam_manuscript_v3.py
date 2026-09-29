#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "manuscript/bam_identifiability/MANUSCRIPT_AUDIT_V3.json"
        ),
    )
    args = parser.parse_args()

    manuscript_path = (
        ROOT / "manuscript" / "bam_identifiability" / "MANUSCRIPT_DRAFT_V3.md"
    )
    text = manuscript_path.read_text(encoding="utf-8")

    deterministic = load_json(
        "validation/known_truth_bam_v3/result_summary_v3.json"
    )
    restrict = load_json(
        "validation/restrictiveness_ambiguity_v3_1/audit_summary_v3_1.json"
    )
    temporal = load_json(
        "validation/independent_stochastic_temporal_v3_2/result_summary_v3_2.json"
    )
    multi = load_json(
        "validation/multilandscape_stochastic_bam_v4/result_summary_v4.json"
    )
    measure = load_json(
        "validation/bam_identifiability_theory_v1/"
        "targeted_measurement_exact_audit_summary_v1.json"
    )

    checks = {
        "deterministic_evidence_ladder": (
            deterministic["pooled_unique_counts"]
            == {
                "E0": 0,
                "E1": 25,
                "E2": 159,
                "E3": 275,
                "E4": 565,
                "E5": 768,
                "E6": 768,
            }
            and deterministic["eligible_truth_count"] == 768
        ),
        "restrictiveness_audit": (
            restrict["strict_support_inclusion_pair_count"] == 304
            and restrict["nesting_monotonicity_violations"] == 0
            and "304/304" in text
        ),
        "temporal_audit": (
            temporal["static_support_classes"]["count"] == 8
            and temporal["temporal_signature_classes"]["count"] == 20
            and temporal["temporal_strict_gain_runs"] == 256
            and "256/384" in text
        ),
        "multilandscape_denominator": (
            multi["planned_landscape_count"] == 8
            and multi["eligible_landscape_count"] == 6
            and multi["design_stop_count"] == 2
            and multi["eligible_stochastic_runs"] == 1152
        ),
        "exact_measurement_bounds": (
            measure["exact_maximum_measurements"]
            == {
                "A": 1,
                "B": 2,
                "AB_joint": 3,
                "M": 2,
                "tau": 0,
                "M_tau_joint": 2,
            }
            and measure["failures"] == 0
        ),
        "eog_wf_separation": all(
            token not in text
            for token in (
                "Azores yellow eel",
                "King Rail",
                "Tampa Bay",
                "Layer B",
                "macro log loss",
                "3/31/3",
            )
        ),
        "prior_art_boundary": all(
            token in text
            for token in (
                "Our contribution is not to rediscover that general fact.",
                "Hitting-set optimization itself is not novel",
                "Soberón & Peterson, 2005",
                "Saupe et al., 2012",
                "Yanco et al., 2020",
                "Atkinson & Cox, 1974",
            )
        ),
        "math_surface": all(
            token not in text
            for token in (
                "A cap B",
                "R_1subset",
                "C(R_1)supseteq",
                "S_6subseteq",
                "D_msubseteq",
                "bigcup_{min Q}",
            )
        ),
    }

    payload = {
        "schema": "eog.bam_inverse_identifiability.manuscript_audit.v3",
        "manuscript": str(manuscript_path.relative_to(ROOT)),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "source_fingerprints": {
            "deterministic_v3": deterministic["result_fingerprint"],
            "restrictiveness_v3_1": restrict["result_fingerprint"],
            "temporal_v3_2": temporal["result_fingerprint"],
            "multilandscape_v4": multi["result_fingerprint"],
            "targeted_measurement_exact": measure["result_fingerprint"],
        },
    }
    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["fingerprint"] = hashlib.sha256(payload_bytes).hexdigest()

    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
