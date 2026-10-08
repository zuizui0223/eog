#!/usr/bin/env python3
"""Match FOUR already-frozen virtual-world result artifacts; never rerun a generator.

This is a POST-RESULT descriptive analysis. The v18-v22 source geometries reuse
the same 384 latent landscapes. Rows and phase results are NOT independent
replications, and these contrasts are NOT preregistered joint hypotheses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

ARCHIVES = {
    "v18": {
        "id": 11321111760,
        "sha256": "82fa7504b46b94369f787888be5d6c1a5e8d3caff622a8e686b23dc57007f9d2",
        "fingerprint": "f039164f427f52f3d8b0ebd78705056c723689933a96cfd5740417f0f8f90089",
    },
    "v19": {
        "id": 11321161763,
        "sha256": "bc4910968de071bab204ee9793a25aa4df69ce591ea8787ef8c8e6c62c7c6686",
        "fingerprint": "a1a4bcf4a8e6f91888f41e9f14826c662da66b869348c14ed8592b411636fd2d",
    },
    "v21": {
        "id": 11322163376,
        "sha256": "666ae4757128e8d3455bd8caeffee31d15c38da381db55f08215861705a3ff38",
        "fingerprint": "40d349a8b134c72add0cd4aeb757b569654d45a519c2efcfe9114a1584dfdd25",
    },
    "v22": {
        "id": 11324282807,
        "sha256": "fe74470d84018941a9fe180218c281effa67cea1e0b577ccb8a86e874e776129",
        "fingerprint": "3436235e0cc96b14088c27377a79b057b1018c74e71edbd48bac0a83e8a9e9dd",
    },
}

EPS = 1e-12
PHASES = tuple(ARCHIVES)


def row_key(row):
    return (
        row["environmental_autocorrelation"],
        row["neighbourhood"],
        float(row["truth_barrier_density"]),
        int(row["replicate"]),
    )


def load_artifact(path: Path, phase: str):
    expected = ARCHIVES[phase]
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected["sha256"]:
        raise ValueError(f"{phase}: immutable result ZIP SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        if archive.namelist() != [f"result_{phase}.json"]:
            raise ValueError(f"{phase}: archive has unexpected members")
        result = json.loads(archive.read(f"result_{phase}.json"))
    if result["fingerprint"] != expected["fingerprint"]:
        raise ValueError(f"{phase}: result fingerprint mismatch")
    if result["row_count"] != 384 or result["eligible_row_count"] != 384:
        raise ValueError(f"{phase}: frozen row count changed")
    rows = {row_key(row): row for row in result["rows"]}
    if len(rows) != 384 or not all(row["eligible"] for row in rows.values()):
        raise ValueError(f"{phase}: row identity or eligibility violated")
    return rows


def verify_matched_record(key, records):
    a, b, c, d = (records[p] for p in PHASES)
    if a["anchor_source"] != b["anchor_source"] or a["anchor_source"] != c["anchor_source"]:
        raise ValueError(f"{key}: anchor identity changed")
    output = {"barrier": key[2], "autocorrelation": key[0], "neighbourhood": key[1]}
    for placement in ("clustered", "dispersed"):
        v18 = a["designs"][placement]["3"]
        v19 = b["designs"][placement]["3"]
        v21 = c["designs"][placement]
        v22 = d["designs"][placement]
        ids = [v18["source_ids"], v19["source_ids"],
               v21["source_ids"], v22["source_ids"]]
        if not all(x == ids[0] for x in ids) or len(ids[0]) != 3:
            raise ValueError(f"{key} / {placement}: source identities differ")
        n = v18["union_reachable_node_count"]
        if n != v19["union_reachable_node_count"] or n != v21["equilibrium_union_node_count"]:
            raise ValueError(f"{key} / {placement}: reachable node count changed")
        overlap = v18["multi_source_overlap_fraction"]
        if (not math.isclose(overlap, v19["static_ambiguous_fraction"], abs_tol=EPS)
            or not math.isclose(overlap, v21["static_origin_ambiguity_fraction"], abs_tol=EPS)):
            raise ValueError(f"{key} / {placement}: source-basin definitions disagree")
        if not v21["equilibrium_occupancy_equal_across_histories"] or not v22["equilibrium_snapshot_identical"]:
            raise ValueError(f"{key} / {placement}: no longer history-aliased at equilibrium")
        f = v22["full_history"]
        if bool(f["identified"]) != (f["minimum_size"] is not None):
            raise ValueError(f"{key} / {placement}: inconsistent observational identity")
        output[placement] = {
            "coverage": v18["union_reachable_fraction"],
            "insurance": v18["worst_source_loss_retention"],
            "overlap": overlap,
            "provenance": v21["provenance_disagreement_fraction"],
            "transient_jaccard": v21["mean_pairwise_transient_occupancy_jaccard_distance"],
            "identified_from_occupancy_snapshots": bool(f["identified"]),
            "minimal_snapshots": f["minimum_size"],
        }
    return output


def paired_differences(row):
    c, d = row["clustered"], row["dispersed"]
    return {
        "coverage_d_minus_c": d["coverage"] - c["coverage"],
        "insurance_c_minus_d": c["insurance"] - d["insurance"],
        "overlap_c_minus_d": c["overlap"] - d["overlap"],
        "provenance_c_minus_d": c["provenance"] - d["provenance"],
        "transient_d_minus_c": d["transient_jaccard"] - c["transient_jaccard"],
        "observability_d_minus_c": (
            int(d["identified_from_occupancy_snapshots"])
            - int(c["identified_from_occupancy_snapshots"])
        ),
    }


def summarize(matches):
    if len(matches) != 384:
        raise ValueError("matched panel must contain exactly 384 landscapes")
    pairs = [(row, paired_differences(row)) for row in matches]
    keys = tuple(pairs[0][1])
    conditions = {
        "three_source_coverage_insurance_tradeoff": (
            lambda row, d: d["coverage_d_minus_c"] > EPS
                           and d["insurance_c_minus_d"] > EPS
        ),
        "dispersed_only_history_identifiable": (
            lambda row, d: d["observability_d_minus_c"] == 1
        ),
        "clustered_only_history_identifiable": (
            lambda row, d: d["observability_d_minus_c"] == -1
        ),
        "joint_tradeoff_and_dispersed_only_identifiable": (
            lambda row, d: d["coverage_d_minus_c"] > EPS
                           and d["insurance_c_minus_d"] > EPS
                           and d["observability_d_minus_c"] == 1
        ),
        "clustered_more_provenance_but_dispersed_only_identifiable": (
            lambda row, d: d["provenance_c_minus_d"] > EPS
                           and d["observability_d_minus_c"] == 1
        ),
        "clustered_more_overlap_but_dispersed_only_identifiable": (
            lambda row, d: d["overlap_c_minus_d"] > EPS
                           and d["observability_d_minus_c"] == 1
        ),
    }
    counts = {name: sum(f(row, diff) for row, diff in pairs)
              for name, f in conditions.items()}
    hist = Counter((row["clustered"]["identified_from_occupancy_snapshots"],
                    row["dispersed"]["identified_from_occupancy_snapshots"])
                   for row, diff in pairs)
    contingency = {
        "neither": hist[False, False], "dispersed_only": hist[False, True],
        "clustered_only": hist[True, False], "both": hist[True, True]
    }
    strata = {}
    for factor in ("barrier", "autocorrelation", "neighbourhood"):
        strata[factor] = {}
        for val in sorted({row[factor] for row, diff in pairs}):
            subset = [(row, diff) for row, diff in pairs if row[factor] == val]
            strata[factor][str(val)] = {
                "n": len(subset),
                "joint": sum(conditions["joint_tradeoff_and_dispersed_only_identifiable"](r, v)
                             for r, v in subset),
                "tradeoff": sum(conditions["three_source_coverage_insurance_tradeoff"](r, v)
                                for r, v in subset),
                "dispersed_only": sum(v["observability_d_minus_c"] == 1
                                       for r, v in subset),
                "clustered_only": sum(v["observability_d_minus_c"] == -1
                                       for r, v in subset),
            }
    return {
        "schema": "eog.virtual_worlds.matched_source_geometry_history.v1",
        "status": "POST_RESULT_EXPLORATORY_NOT_PREREGISTERED",
        "matched_landscapes": len(matches),
        "source_identity_mismatches": 0,
        "three_sources_per_design": True,
        "readout": "v22 full-history identification from complete post-activation occupancy snapshots, not a direct provenance assay",
        "fingerprints": {k: ARCHIVES[k]["fingerprint"] for k in PHASES},
        "artifact_zip_sha256": {k: ARCHIVES[k]["sha256"] for k in PHASES},
        "counts": counts,
        "history_identifiability_contingency": contingency,
        "mean_paired_differences": {
            k: sum(v[k] for r, v in pairs) / len(pairs) for k in keys
        },
        "direction_counts": {
            k: {"positive": sum(v[k] > EPS for r, v in pairs),
                "tie": sum(abs(v[k]) <= EPS for r, v in pairs),
                "negative": sum(v[k] < -EPS for r, v in pairs)}
            for k in keys
        },
        "strata": strata,
        "interpretation": (
            "Source basin overlap can retain a stronger difference in equilibrium provenance "
            "while an occupancy-only transient observation library less often distinguishes "
            "activation history. History retention and historical observability are different "
            "properties of the declared state and readout."
        ),
        "boundaries": [
            "Exploratory cross-phase joining of related frozen synthetic panels, not a new randomized or preregistered joint experiment.",
            "No model, biological response, or real ecological process was reestimated.",
            "Worst-source-loss retention is structural reachable-set preservation, not metapopulation persistence or extinction risk.",
            "Observed identifiability concerns three synthetic activation schedules and complete structural occupancy snapshots.",
            "Differences in observable signal cannot be promoted to a causal mediation of source geometry through provenance.",
            "Existing EOG-WF empirical endpoints and the JBI BAM / Ecology Letters history-storage manuscripts are unchanged."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for phase in PHASES:
        parser.add_argument(f"--{phase}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assert-frozen", type=Path)
    a = parser.parse_args()
    panels = {phase: load_artifact(getattr(a, phase), phase) for phase in PHASES}
    common = set(panels["v18"])
    if any(set(panel) != common for panel in panels.values()):
        raise ValueError("Cannot join different truth-landscape panels")
    matched = [verify_matched_record(key, {p: panels[p][key] for p in PHASES})
               for key in sorted(common)]
    report = summarize(matched)
    if a.assert_frozen is not None:
        expected = json.loads(a.assert_frozen.read_text(encoding="utf-8"))
        if report != expected:
            raise ValueError("Frozen post-result aggregate differs from original audited receipt")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "matched_landscapes": report["matched_landscapes"],
                      "counts": report["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
