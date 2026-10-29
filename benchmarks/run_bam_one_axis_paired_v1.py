#!/usr/bin/env python3
"""Reproduce previously exposed 1,344 nested BAM-world comparisons.

This is post-result exploratory analysis of the SAME 768 deterministic worlds,
not an independent experiment, a causal contrast, or ecological prevalence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from benchmarks.run_bam_geometry_768_v1 import run as run_parent  # noqa: E402
from eog.comparative import fit_robust_reference, transform_with_reference  # noqa: E402
from eog.v2.known_truth_bam_generality import (  # noqa: E402
    SYSTEM_SPECS, build_generality_system,
)

PARENT_RECEIPT = ROOT / "validation/bam_geometry_768_v1/result_receipt_v1.json"
N_DRAWS = 64
SEED = 20261029
AXES = (
    "A_narrow_vs_broad",
    "B_obligate_partner_vs_none",
    "B_antagonist_exclusion_vs_none",
    "B_partner_and_antagonist_vs_none",
    "M_barrier_closed_vs_open",
)


def bit_indices(bits: int, n: int) -> np.ndarray:
    return np.asarray([i for i in range(n) if bits & (1 << i)], dtype=int)


def span(z: np.ndarray) -> float | None:
    if len(z) < 2:
        return None
    pairwise = np.linalg.norm(z[:, None, :] - z[None, :, :], axis=2)
    positive = pairwise[np.triu_indices(len(z), 1)]
    positive = positive[positive > 0]
    return float(np.quantile(positive, 0.90)) if len(positive) else 0.0


def centroid(z: np.ndarray) -> float | None:
    if len(z) < 2:
        return None
    return float(np.mean(np.linalg.norm(z - z.mean(axis=0), axis=1)))


def source_rows():
    parent_summary, rows = run_parent(smoke=False)
    receipt = json.loads(PARENT_RECEIPT.read_text(encoding="utf-8"))
    if (
        parent_summary["fingerprint"] != receipt["result_fingerprint"]
        or len(rows) != receipt["source_universe"]["parameter_worlds"]
    ):
        raise ValueError("parent frozen 768-world geometry fingerprint mismatch")
    raw = (json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    observed_byte_sha = hashlib.sha256(raw).hexdigest()
    # The historical byte digest binds the original artifact, but it can
    # differ after an independently replayed NumPy/Python environment. Check
    # the scientific row identity *separately*, never assume byte parity.
    keys = ("system_id", "world_id", "world_fingerprint", "A_bits",
            "B_bits", "M_bits", "G_bits", "G_geographic_component_count")
    projected = [
        {**{key: row[key] for key in keys},
         "G_span_8dp": round(row["G_environmental_geometry"]["span"], 8)}
        for row in rows
    ]
    scientific_digest = hashlib.sha256(json.dumps(
        projected, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()
    expected_scientific_digest = (
        "6cc2a8944fa627880ef8cdc5f54a49e12ae5abe3f91e909559a5283270f9b768"
    )
    if scientific_digest != expected_scientific_digest:
        raise ValueError("reconstructed BAM world masks/IDs/G geometry digest mismatch")
    receipt["replayed_world_rows_sha256"] = observed_byte_sha
    receipt["replayed_scientific_projection_sha256"] = scientific_digest
    receipt["world_row_byte_parity"] = (
        observed_byte_sha == receipt["world_rows_json_sha256"]
    )
    if not receipt["world_row_byte_parity"]:
        print("SOURCE_BYTE_DIFFERENCE__SCIENTIFIC_ROWS_STABLE: "+
              observed_byte_sha, file=sys.stderr)
    return rows, receipt


def compute(rows, *, draws: int = N_DRAWS, seed: int = SEED):
    if not isinstance(draws, int) or draws < 1:
        raise ValueError("draws must be positive")
    if len(rows) != 768:
        raise ValueError("expected frozen 768-world roster")
    indices = {}
    for row in rows:
        labels = row["world_id"].split("|")
        if len(labels) != 3:
            raise ValueError("unexpected BAM world ID")
        key = (row["system_id"], *labels)
        if key in indices:
            raise ValueError("duplicated BAM world ID")
        indices[key] = row

    z_by_system = {}
    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        original = np.asarray(system.landscape.environment, dtype=float)
        ref = fit_robust_reference(
            original, provenance="frozen complete virtual BAM node environment"
        )
        z_by_system[spec.system_id] = transform_with_reference(original, ref)
    if len(z_by_system) != 12:
        raise ValueError("missing original BAM systems")

    # Prove generated feature scale and ordering reproduce the parent G spans.
    for row in rows:
        z = z_by_system[row["system_id"]]
        got = span(z[bit_indices(row["G_bits"], len(z))])
        expected = row["G_environmental_geometry"]["span"]
        if got is None or abs(got - expected) > 1e-10:
            raise ValueError("parent shared-reference span parity failed")

    records = []
    cache = {}

    def one(small, large, axis):
        if small["system_id"] != large["system_id"]:
            raise ValueError("pairs must share environmental landscape")
        if small["G_bits"] & ~large["G_bits"]:
            raise ValueError("restrictive G is not subset of permissive G")
        sid = small["system_id"]
        z = z_by_system[sid]
        small_index = bit_indices(small["G_bits"], len(z))
        large_index = bit_indices(large["G_bits"], len(z))
        ns, nl = len(small_index), len(large_index)
        current = span(z[small_index])
        current_centroid = centroid(z[small_index])
        if ns < 2:
            log_span = log_centroid = None
        elif ns == nl:
            log_span = log_centroid = 0.0
        else:
            key = (sid, small["G_bits"], large["G_bits"], ns)
            if key not in cache:
                token = f"{seed}|{sid}|{small['G_bits']}|{large['G_bits']}|{ns}"
                subseed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
                rng = np.random.default_rng(subseed)
                samples = [
                    np.sort(rng.choice(large_index, size=ns, replace=False))
                    for _ in range(draws)
                ]
                median_span = float(np.median([span(z[loc]) for loc in samples]))
                median_centroid = float(
                    np.median([centroid(z[loc]) for loc in samples])
                )
                cache[key] = (median_span, median_centroid)
            control_span, control_centroid = cache[key]
            log_span = (
                math.log(current / control_span)
                if current is not None and current > 0 and control_span > 0
                else None
            )
            log_centroid = (
                math.log(current_centroid / control_centroid)
                if current_centroid is not None and current_centroid > 0
                and control_centroid > 0 else None
            )
        records.append({
            "system_id": sid,
            "axis_contrast": axis,
            "restrictive_world": small["world_id"],
            "permissive_world": large["world_id"],
            "restrictive_G_n": ns,
            "permissive_G_n": nl,
            "loss_count": nl - ns,
            "same_G": small["G_bits"] == large["G_bits"],
            "matched_log_span_restrictive_over_permissive": log_span,
            "matched_log_centroid_restrictive_over_permissive": log_centroid,
            "delta_geographic_components": (
                small["G_geographic_component_count"] -
                large["G_geographic_component_count"]
            ),
            "delta_environmental_MST_components": (
                small["G_environmental_geometry"]["mst_cut_components"] -
                large["G_environmental_geometry"]["mst_cut_components"]
            ),
        })

    for spec in SYSTEM_SPECS:
        sid = spec.system_id
        movement = sorted({key[3] for key in indices if key[0] == sid})
        if len(movement) != 8:
            raise ValueError("expected exactly eight M variants")
        for m in movement:
            for b in ("B_none", "B_obligate_partner",
                      "B_antagonist_exclusion", "B_partner_and_antagonist"):
                one(indices[sid, "A_narrow", b, m],
                    indices[sid, "A_broad", b, m], "A_narrow_vs_broad")
        for a in ("A_narrow", "A_broad"):
            for m in movement:
                for b in ("B_obligate_partner", "B_antagonist_exclusion",
                          "B_partner_and_antagonist"):
                    one(indices[sid, a, b, m], indices[sid, a, "B_none", m],
                        f"{b}_vs_none")
        for a in ("A_narrow", "A_broad"):
            for b in ("B_none", "B_obligate_partner",
                      "B_antagonist_exclusion", "B_partner_and_antagonist"):
                for d in ("D1.01", "D2.01"):
                    for h in (("H3", "H10") if spec.width == 7 else ("H3", "H14")):
                        small_m = f"M_{d}_P0_{h}"
                        large_m = f"M_{d}_P1_{h}"
                        one(indices[sid, a, b, small_m], indices[sid, a, b, large_m],
                            "M_barrier_closed_vs_open")

    if len(records) != 1344:
        raise ValueError("fixed 1,344 paired contrasts missing")

    summary = []
    for axis in sorted(AXES):
        pairs = [r for r in records if r["axis_contrast"] == axis]
        altered = [r for r in pairs if r["loss_count"] > 0]
        valid = [r["matched_log_span_restrictive_over_permissive"] for r in altered
                 if r["matched_log_span_restrictive_over_permissive"] is not None]
        cvalid = [
            r["matched_log_centroid_restrictive_over_permissive"] for r in altered
            if r["matched_log_centroid_restrictive_over_permissive"] is not None
        ]
        sys_inc = sorted({
            r["system_id"] for r in altered
            if r["matched_log_span_restrictive_over_permissive"] is not None
            and r["matched_log_span_restrictive_over_permissive"] > 1e-12
        })
        summary.append({
            "axis_contrast": axis, "paired_worlds": len(pairs),
            "changed_G_pairs": len(altered),
            "same_G_pairs": len(pairs) - len(altered),
            "estimable_changed_G": len(valid),
            "median_matched_log_span": float(np.median(valid)) if valid else None,
            "span_smaller": sum(x < -1e-12 for x in valid),
            "span_larger": sum(x > 1e-12 for x in valid),
            "span_tie": sum(abs(x) <= 1e-12 for x in valid),
            "median_matched_log_centroid": (
                float(np.median(cvalid)) if cvalid else None
            ),
            "systems_with_span_increase": sys_inc,
            "geographic_component_count_increased": sum(
                r["delta_geographic_components"] > 0 for r in altered
            ),
            "geographic_component_count_decreased": sum(
                r["delta_geographic_components"] < 0 for r in altered
            ),
            "environmental_component_count_increased": sum(
                r["delta_environmental_MST_components"] > 0 for r in altered
            ),
            "environmental_component_count_decreased": sum(
                r["delta_environmental_MST_components"] < 0 for r in altered
            ),
            "systems": len({r["system_id"] for r in pairs}),
        })
    report = {
        "schema": "eog.bam_one_axis_paired_descriptive.v1",
        "status": "POST_EXPOSURE_EXPLORATORY",
        "n_systems": 12, "n_parent_worlds": len(rows),
        "pair_count": len(records),
        "changed_G_pair_count": sum(r["loss_count"] > 0 for r in records),
        "parent_fingerprint": "8c60d83820ae9693fa528791071d371748b032df65ca9cd62eb91d3103596d0c",
        "parent_world_rows_sha256": "89c7247315f4e545ac69cc6f9bb05fc875fde3c693ad1f368a80e972c072b90d",
        "reference": "original 12 per-system shared EOG median/MAD references",
        "draws": draws, "seed": seed, "summary": summary,
        "notes": [
            "1,344 contrasts are reused worlds across 12 landscapes, not independent ecology replicates.",
            "Nested BAM mask edits are known-truth structural contrasts, not empirical causal effects.",
            "Equal-size random thinning is a descriptive control, not population inference.",
            "Environmental MST cuts and geographic adjacency are different summaries.",
            "All contrasts and expected directional findings were viewed before this GitHub replay.",
        ],
    }
    report["fingerprint"] = hashlib.sha256(json.dumps(
        report, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()
    return report, records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows, provenance = source_rows()
    report, records = compute(rows)
    report["source_byte_parity"] = provenance["world_row_byte_parity"]
    report["replayed_world_rows_sha256"] = provenance["replayed_world_rows_sha256"]
    report["replayed_scientific_projection_sha256"] = provenance[
        "replayed_scientific_projection_sha256"
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+"\n",
        encoding="utf-8"
    )
    with (args.output_dir / "paired_worlds.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print("BAM_PAIRED_RESULT="+json.dumps({
        "n_worlds": report["n_parent_worlds"], "n_pairs": report["pair_count"],
        "changed_pairs": report["changed_G_pair_count"],
        "summary": report["summary"], "fingerprint": report["fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
