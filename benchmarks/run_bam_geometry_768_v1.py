#!/usr/bin/env python3
"""Exploratory 12-system × 64-world BAM geometry readout.

All worlds were generated and exposed in earlier work. This is a *new descriptive
readout of known truths*, not an independent simulation or confirmatory endpoint.
The protocol was committed before this geometry readout was scored.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eog.comparative import fit_robust_reference, infer_comparative_geometry, transform_with_reference  # noqa: E402
from eog.reference_policy import ReferenceDeclaration, validate_reference_declaration  # noqa: E402
from eog.bam_support_topology import profile_bam_support_topology  # noqa: E402
from eog.support_topology import SupportGridMetadata, SupportTopologyConfig  # noqa: E402
from eog.v2.known_truth_bam_generality import (  # noqa: E402
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)

PROTOCOL = ROOT / "validation/bam_geometry_768_v1/protocol_v1.json"
PROTOCOL_COMMIT = "cd7a9222bb8512713a47e26f96d4411229736329"
GROUPS = ("U", "A", "B", "M", "AB", "AM", "BM", "ABM")
BASELINES = ("U", "A", "B", "M", "AB", "AM", "BM")
DRAW_SEED = 20261029
N_DRAWS = 16


def _sha(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        .encode("utf-8")
    ).hexdigest()


def _boolmask(bits: int, n: int) -> np.ndarray:
    return np.array([bool(bits & (1 << i)) for i in range(n)], dtype=bool)


def _assert_grid(system) -> None:
    landscape = system.landscape
    expected = tuple(
        f"r{r}c{c}"
        for r in range(system.spec.height)
        for c in range(system.spec.width)
    )
    coords = tuple(
        (float(c), float(r))
        for r in range(system.spec.height)
        for c in range(system.spec.width)
    )
    if (
        landscape.node_ids != expected
        or landscape.coordinates != coords
        or len(landscape.environment) != len(expected)
    ):
        raise ValueError("BAMWorld node ID and coordinate order are not exact grid row-major")


def _masks(world, n):
    full = (1 << n) - 1
    a, b, m = world.abiotic_mask, world.biotic_mask, world.movement_mask
    if world.occupied_mask != (a & b & m):
        raise ValueError("original BAM G intersection failed")
    if any(bits < 0 or bits >> n for bits in (a, b, m, world.occupied_mask)):
        raise ValueError("original BAM mask exceeds declared node universe")
    return {
        "U": full, "A": a, "B": b, "M": m,
        "AB": a & b, "AM": a & m, "BM": b & m, "ABM": a & b & m,
    }


def _positive_span(z):
    if len(z) < 2:
        return None
    delta = z[:, None, :] - z[None, :, :]
    dist = np.sqrt(np.sum(delta * delta, axis=2))
    upper = dist[np.triu_indices(len(z), k=1)]
    pos = upper[upper > 0]
    return float(np.quantile(pos, 0.90)) if len(pos) else 0.0


def _centroid_mean(z):
    if len(z) < 2:
        return None
    return float(np.mean(np.linalg.norm(z - np.mean(z, axis=0), axis=1)))


def _summary(values):
    if not values:
        return {"n": 0, "median": None}
    a = np.asarray(values, dtype=float)
    return {"n": len(a), "median": float(np.median(a)),
            "min": float(np.min(a)), "max": float(np.max(a))}


def _direction(values):
    positive = sum(x > 1e-12 for x in values)
    negative = sum(x < -1e-12 for x in values)
    return {"positive": positive, "negative": negative,
            "zero": len(values) - positive - negative}


def _compute_system(spec, *, limit_worlds=None):
    system = build_generality_system(spec)
    gate = audit_system_activation(system)
    if gate.status != "PASS":
        raise ValueError(f"parent system failed frozen activation gate: {spec.system_id}")
    _assert_grid(system)
    n = len(system.landscape.node_ids)
    features = np.asarray(system.landscape.environment, dtype=float)
    reference = fit_robust_reference(
        features,
        provenance=f"retrospective complete frozen BAM environment: {spec.system_id}",
    )
    policy = ReferenceDeclaration(
        mode="pooled-descriptive", intent="retrospective",
        source_description="original fixed candidate node feature space, including all groups",
        fitted_before_evaluation=False, includes_evaluation_groups=True,
        outcome_informed=False,
    )
    validate_reference_declaration(policy)
    z = transform_with_reference(features, reference)
    world_list = system.worlds if limit_worlds is None else system.worlds[:limit_worlds]

    full_cache = {}
    match_cache = {}
    g_groups = defaultdict(list)
    all_rows = []
    config = SupportTopologyConfig(
        thresholds=(0.5,), neighbourhood=4, minimum_persistence_steps=1,
    )
    grid = SupportGridMetadata(
        x_origin=0.0, y_origin=0.0, x_resolution=1.0, y_resolution=1.0,
        crs="synthetic-cartesian-grid",
    )

    def full_geometry(bits):
        if bits not in full_cache:
            indices = np.flatnonzero(_boolmask(bits, n))
            if len(indices) < 2:
                full_cache[bits] = None
            else:
                g = infer_comparative_geometry(features[indices], reference)
                full_cache[bits] = {
                    "n": len(indices),
                    "span": float(g.span),
                    "mst_compactness": float(g.continuity),
                    "gap_strength": float(g.gap_strength),
                    "mst_cut_components": int(g.component_count),
                    "centroid_mean": _centroid_mean(z[indices]),
                }
        return full_cache[bits]

    def matched(bits, size):
        key = (bits, size)
        if key in match_cache:
            return match_cache[key]
        indices = np.flatnonzero(_boolmask(bits, n))
        if size < 2 or len(indices) < size:
            return None
        if len(indices) == size:
            spans = [full_geometry(bits)["span"]]
            centroids = [full_geometry(bits)["centroid_mean"]]
        else:
            seed = int.from_bytes(
                hashlib.sha256(
                    f"{DRAW_SEED}|{spec.system_id}|{bits}|{size}".encode()
                ).digest()[:8], "big"
            )
            rng = np.random.default_rng(seed)
            spans = []
            centroids = []
            for _ in range(N_DRAWS):
                selection = np.sort(rng.choice(indices, size=size, replace=False))
                spans.append(_positive_span(z[selection]))
                centroids.append(_centroid_mean(z[selection]))
        result = {
            "span_median": float(np.median(spans)),
            "span_q05": float(np.quantile(spans, 0.05)),
            "span_q95": float(np.quantile(spans, 0.95)),
            "centroid_median": float(np.median(centroids)),
        }
        match_cache[key] = result
        return result

    for world in world_list:
        masks = _masks(world, n)
        g_bits = masks["ABM"]
        g_n = g_bits.bit_count()
        groups = {}
        for name in GROUPS:
            groups[name] = {
                "node_count": masks[name].bit_count(),
                "environmental_geometry": full_geometry(masks[name]),
            }

        coords = {
            system.landscape.node_ids[i]: divmod(i, spec.width)
            for i in range(n) if g_bits & (1 << i)
        }
        geo = profile_bam_support_topology(
            np.ones((spec.height, spec.width), dtype=float),
            A=_boolmask(masks["A"], n).reshape(spec.height, spec.width),
            B=_boolmask(masks["B"], n).reshape(spec.height, spec.width),
            M=_boolmask(masks["M"], n).reshape(spec.height, spec.width),
            occurrence_cells=coords, config=config, grid=grid,
        )
        ratios = {}
        ctr_ratios = {}
        if g_n >= 2:
            primary = matched(g_bits, g_n)
            if primary and primary["span_median"] > 0:
                for baseline in BASELINES:
                    control = matched(masks[baseline], g_n)
                    if control and control["span_median"] > 0:
                        ratios[baseline] = float(
                            np.log(primary["span_median"] / control["span_median"])
                        )
                    else:
                        ratios[baseline] = None
                    if control and control["centroid_median"] > 0:
                        ctr_ratios[baseline] = float(
                            np.log(primary["centroid_median"] / control["centroid_median"])
                        )
                    else:
                        ctr_ratios[baseline] = None

        g_geom = full_geometry(g_bits)
        spatial_count = geo["groups"]["ABM"]["tracked_component_lineages"]
        row = {
            "system_id": spec.system_id,
            "world_id": world.world_id,
            "world_fingerprint": world.fingerprint,
            "A_bits": masks["A"], "B_bits": masks["B"],
            "M_bits": masks["M"], "G_bits": g_bits,
            "node_count": n, "G_nodes": g_n,
            "group_node_counts": {
                name: groups[name]["node_count"] for name in GROUPS
            },
            "G_environmental_geometry": g_geom,
            "G_geographic_component_count": spatial_count,
            "G_spatial_vs_environmental_component_disagree": (
                None if g_geom is None
                else (spatial_count != g_geom["mst_cut_components"])
            ),
            "A_detached_component_count": geo["groups"]["A"][
                "lineage_class_counts"]["persistent_detached_component"],
            "B_detached_component_count": geo["groups"]["B"][
                "lineage_class_counts"]["persistent_detached_component"],
            "M_detached_component_count": geo["groups"]["M"][
                "lineage_class_counts"]["persistent_detached_component"],
            "ratios_G_to_baselines": ratios,
            "centroid_ratios_G_to_baselines": ctr_ratios,
        }
        all_rows.append(row)
        g_groups[g_bits].append(row)

    alias_families = [
        group for group in g_groups.values()
        if len(set((r["A_bits"], r["B_bits"], r["M_bits"]) for r in group)) > 1
    ]
    # Identical G must have identical environmental geometry and spatial components.
    for group in g_groups.values():
        first = group[0]
        for other in group[1:]:
            if (other["G_environmental_geometry"] != first["G_environmental_geometry"]
                or other["G_geographic_component_count"]
                != first["G_geographic_component_count"]):
                raise AssertionError("same G has different G-derived geometry")

    valid = [r for r in all_rows if r["G_environmental_geometry"] is not None]
    differences = [
        r["G_spatial_vs_environmental_component_disagree"] for r in valid
    ]
    per_baseline = {}
    for baseline in BASELINES:
        values = [
            r["ratios_G_to_baselines"].get(baseline)
            for r in all_rows
        ]
        valid_ratios = [x for x in values if x is not None]
        ctr_values = [
            r["centroid_ratios_G_to_baselines"].get(baseline)
            for r in all_rows
        ]
        ctr_valid = [x for x in ctr_values if x is not None]
        per_baseline[baseline] = {
            "span_log_ratio": _summary(valid_ratios),
            "span_direction": _direction(valid_ratios),
            "centroid_log_ratio": _summary(ctr_valid),
            "opposed_direction_n": sum(
                (a > 1e-12 and b < -1e-12)
                or (a < -1e-12 and b > 1e-12)
                for a, b in zip(values, ctr_values)
                if a is not None and b is not None
            ),
        }

    report = {
        "system_id": spec.system_id,
        "source_fingerprint": system.fingerprint,
        "activation_status": gate.status,
        "n_worlds": len(all_rows),
        "G_estimable_n": len(valid),
        "G_unestimable_n": len(all_rows) - len(valid),
        "distinct_G": len(g_groups),
        "same_G_alias_family_count": len(alias_families),
        "worlds_in_alias_families": sum(len(g) for g in alias_families),
        "same_G_nonidentification_checks": sum(
            len(group) - 1 for group in g_groups.values()
        ),
        "G_spatial_vs_environmental_component_disagreement": sum(differences),
        "G_component_comparison_n": len(differences),
        "detached_geographic_components": {
            name: _summary([
                row[f"{name}_detached_component_count"] for row in all_rows
            ])
            for name in ("A", "B", "M")
        },
        "G_geographic_components_frequency": dict(
            sorted(Counter(r["G_geographic_component_count"] for r in all_rows).items())
        ),
        "comparisons": per_baseline,
    }
    return report, all_rows


def run(*, smoke=False):
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["schema"] != "eog.bam_geometry_768.protocol.v1":
        raise ValueError("protocol schema mismatch")
    systems = SYSTEM_SPECS[:1] if smoke else SYSTEM_SPECS
    report_rows = []
    worlds = []
    for spec in systems:
        info, rows = _compute_system(spec, limit_worlds=4 if smoke else None)
        report_rows.append(info)
        worlds.extend(rows)
    if not smoke and (
        len(report_rows) != protocol["source_roster"]["systems"]
        or len(worlds) != protocol["source_roster"]["expected_worlds"]
        or any(s["n_worlds"] != protocol["source_roster"]["worlds_per_system"]
               for s in report_rows)
    ):
        raise ValueError("fixed 12x64 roster failed")
    result = {
        "schema": "eog.bam_geometry_768.result.v1",
        "status": "POST_EXPOSURE_EXPLORATORY_KNOWN_TRUTH",
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "parent_worlds": "12 heterogeneous deterministic known-truth BAM systems",
        "n_systems": len(report_rows),
        "n_worlds": len(worlds),
        "n_draws": N_DRAWS,
        "seed": DRAW_SEED,
        "n_G_estimable": sum(s["G_estimable_n"] for s in report_rows),
        "n_G_unestimable": sum(s["G_unestimable_n"] for s in report_rows),
        "n_same_G_alias_families": sum(s["same_G_alias_family_count"] for s in report_rows),
        "n_worlds_in_same_G_alias_families": sum(s["worlds_in_alias_families"] for s in report_rows),
        "n_same_G_invariance_checks": sum(s["same_G_nonidentification_checks"] for s in report_rows),
        "n_spatial_MST_disagreements": sum(
            s["G_spatial_vs_environmental_component_disagreement"]
            for s in report_rows
        ),
        "n_spatial_MST_comparable": sum(
            s["G_component_comparison_n"] for s in report_rows
        ),
        "systems": report_rows,
        "limits": [
            "Retrospective geometry readout of previously exposed finite worlds; "
            "not independent ecological replication or preregistered field evidence.",
            "A/B/M masks are known by construction, not inferred from environmental geometry.",
            "Shared-reference matched span/centroid differences are descriptive and noncausal.",
            "Geographic connectivity is binary grid adjacency, not realized movement.",
            "64 models within a system reuse the same landscape and are not independent replicates.",
        ],
    }
    result["fingerprint"] = _sha(result)
    return result, worlds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    result, rows = run(smoke=args.smoke)
    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, payload in (
            ("result_summary_v1.json", result), ("world_rows_v1.json", rows)
        ):
            (args.output_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
                encoding="utf-8",
            )
    brief = {
        "status": result["status"],
        "n_systems": result["n_systems"],
        "n_worlds": result["n_worlds"],
        "n_G_estimable": result["n_G_estimable"],
        "n_G_unestimable": result["n_G_unestimable"],
        "n_same_G_alias_families": result["n_same_G_alias_families"],
        "n_worlds_in_same_G_alias_families":
            result["n_worlds_in_same_G_alias_families"],
        "n_same_G_invariance_checks": result["n_same_G_invariance_checks"],
        "n_spatial_MST_disagreements": result["n_spatial_MST_disagreements"],
        "n_spatial_MST_comparable": result["n_spatial_MST_comparable"],
        "systems": [
            {
                "id": s["system_id"],
                "n_G_estimable": s["G_estimable_n"],
                "distinct_G": s["distinct_G"],
                "alias_family_n": s["same_G_alias_family_count"],
                "G_vs_U": s["comparisons"]["U"]["span_log_ratio"]["median"],
                "G_vs_A": s["comparisons"]["A"]["span_log_ratio"]["median"],
                "spatial_vs_MST_disagree":
                    s["G_spatial_vs_environmental_component_disagreement"],
            }
            for s in result["systems"]
        ],
        "fingerprint": result["fingerprint"],
    }
    print("BAM_GEOMETRY_SUMMARY="+json.dumps(brief, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
