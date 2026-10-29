#!/usr/bin/env python3
"""Deterministic descriptive demonstration of the experimental EOG × BAM bridge.

Reuses the existing 7×3 known-truth BAM generator. Not a new independent
ecological result, preregistered test or EOG-WF heldout predictive endpoint.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eog.bam_geometry import profile_known_truth_bam_world  # noqa: E402
from eog.comparative import fit_robust_reference  # noqa: E402
from eog.reference_policy import ReferenceDeclaration  # noqa: E402
from eog.v2.known_truth_bam import (  # noqa: E402
    build_bam_world,
    generate_biotic_state,
    make_bam_landscape,
)


def run() -> dict:
    landscape = make_bam_landscape()
    features = np.asarray(landscape.environment, dtype=float)
    partner_antagonist = generate_biotic_state(landscape)

    reference = fit_robust_reference(
        features, provenance="complete 7x3 known-truth node environment"
    )
    declaration = ReferenceDeclaration(
        mode="pooled-descriptive",
        intent="retrospective",
        source_description="complete synthetic candidate grid, not heldout",
        fitted_before_evaluation=False,
        includes_evaluation_groups=True,
        outcome_informed=False,
    )
    scenarios = (
        ("A_broad_B_none_M_open", "none", True),
        ("A_broad_B_partner_M_open", "obligate_partner", True),
        ("A_broad_B_none_M_closed", "none", False),
    )
    rows = []
    for world_id, b_mode, permeable in scenarios:
        world = build_bam_world(
            landscape,
            world_id=world_id,
            abiotic_label="A_broad",
            niche_center=(0.55, 0.55),
            niche_radius=(0.8, 0.8),
            biotic_state=partner_antagonist,
            biotic_mode=b_mode,
            movement_label="permeable" if permeable else "hard_barrier",
            source_id="r1c0",
            step_radius=1.01,
            barrier_permeable=permeable,
            horizon=10,
        )
        profile = profile_known_truth_bam_world(
            world,
            features,
            feature_node_ids=landscape.node_ids,
            reference=reference,
            declaration=declaration,
            n_draws=32,
            seed=20261029,
        )
        rows.append({
            "world_id": world.world_id,
            "source_world_fingerprint": world.fingerprint,
            "geometry_fingerprint": profile["fingerprint"],
            "node_counts": {
                key: profile["groups"][key]["n_nodes"]
                for key in ("U", "A", "B", "M", "AB", "AM", "BM", "ABM")
            },
            "matched_size": profile["parameters"]["matched_size"],
            "G_matched_span": (
                profile["groups"]["ABM"]["matched"]["median"]["span"]
                if profile["groups"]["ABM"]["matched"] is not None else None
            ),
            "G_vs_universe_matched_log_span_ratio": profile["contrasts"][
                "ABM_vs_U_matched_log_span_ratio"
            ],
        })
    return {
        "schema": "eog.bam_geometry_bridge_demo.v0",
        "validation_scope": "same-generator known-truth descriptive demonstration only",
        "n_synthetic_nodes": len(landscape.node_ids),
        "n_features": features.shape[1],
        "reference_policy": declaration.to_dict(),
        "worlds": rows,
        "interpretation_limit": "no causal attribution, unique BAM inversion, or field predictive claim",
    }


def main() -> None:
    print(json.dumps(run(), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
