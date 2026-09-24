from __future__ import annotations

import json

from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_manifest_generator import generate_coordinate_world_family
from validation.algar_restoration_v2_source_qualification.evaluate import evaluate


def run_geometry(
    geometry_contract: dict[str, object],
    source_contract: dict[str, object],
    deployments_raw: bytes,
) -> dict[str, object]:
    source_result = evaluate(source_contract, {"deployments": deployments_raw})
    lock = geometry_contract["candidate_lock"]
    if not source_result["candidate_lock_allowed"]:
        raise ValueError("source qualification no longer allows candidate lock")
    if (
        source_result["certificate_fingerprint"]
        != lock["source_qualification_certificate_fingerprint"]
    ):
        raise ValueError("source qualification certificate fingerprint drift")
    if source_result["registry"]["canonical_node_count"] != lock["locked_node_universe_count"]:
        raise ValueError("locked node universe count drift")

    canonical = source_result["registry"]["canonical_nodes"]
    node_ids = tuple(sorted(canonical))
    coordinates = {
        node_id: (
            float(canonical[node_id]["longitude"]),
            float(canonical[node_id]["latitude"]),
        )
        for node_id in node_ids
    }
    geometry = geometry_contract["geometry"]
    family = generate_coordinate_world_family(
        node_ids,
        coordinates,
        metric=geometry["metric"],
        construction_mode=geometry["construction_mode"],
        axis_id=geometry["axis_id"],
        target_lcc_fractions=geometry["target_lcc_fractions"],
        world_id_prefix=geometry["world_id_prefix"],
        deduplicate_identical_thresholds=geometry["deduplicate_identical_thresholds"],
        local_semantics={
            "kind":"local",
            "source":"response_independent_locked_camera_coordinates",
        },
    )
    structural_worlds = {
        world_id: family.worlds[world_id]
        for world_id in family.structural_world_ids
    }
    audit = audit_world_universe_structure(
        node_ids,
        structural_worlds,
        horizon=int(geometry["horizon"]),
    )
    adequacy = geometry_contract["structural_adequacy"]
    gate = apply_structural_adequacy_gate(
        audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=float(
                adequacy["min_largest_weak_component_fraction"]
            ),
            max_isolated_node_fraction=float(
                adequacy["max_isolated_node_fraction"]
            ),
            require_at_least_one_world_pass=bool(
                adequacy["require_at_least_one_world_pass"]
            ),
        ),
    )
    audit_by_id={row.world_id:row for row in audit.world_audits}
    return {
        "schema":"eog.algar_restoration_v2_geometry.result.v1",
        "status":"structural_ready" if gate.passed else "stop_structural_adequacy",
        "candidate_locked":True,
        "focal_species_selected":False,
        "response_bytes_opened":0,
        "model_fits":0,
        "node_count":len(node_ids),
        "world_family":{
            "fingerprint":family.fingerprint,
            "generator_fingerprint":family.generator_fingerprint,
            "distance_matrix_fingerprint":family.distance_matrix_fingerprint,
            "structural_world_ids":list(family.structural_world_ids),
            "geometry_thresholds_km":list(family.geometry_thresholds),
        },
        "structural_gate":{
            "passed":gate.passed,
            "fingerprint":gate.fingerprint,
            "passing_world_ids":list(gate.passing_world_ids),
            "worlds":{
                world_id:{
                    "largest_weak_component_fraction":audit_by_id[world_id].largest_weak_component_fraction,
                    "isolated_node_fraction":audit_by_id[world_id].isolated_node_fraction,
                    "median_horizon_reachable_fraction":audit_by_id[world_id].median_horizon_reachable_fraction,
                    "directed_edge_count":audit_by_id[world_id].directed_edge_count,
                }
                for world_id in family.structural_world_ids
            },
        },
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }


if __name__=="__main__":
    raise SystemExit("workflow supplies exact safe source bytes")
