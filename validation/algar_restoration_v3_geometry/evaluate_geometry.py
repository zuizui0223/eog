from __future__ import annotations

from eog.v2.adequacy_complete_ladder import plan_adequacy_complete_lcc_targets
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
    source_result=evaluate(source_contract,{"deployments":deployments_raw})
    source=geometry_contract["source_qualification"]
    if not source_result["candidate_lock_allowed"]:
        raise ValueError("source qualification no longer allows candidate lock")
    if source_result["certificate_fingerprint"]!=source["certificate_fingerprint"]:
        raise ValueError("source qualification certificate fingerprint drift")
    if source_result["registry"]["canonical_node_count"]!=source["node_count"]:
        raise ValueError("locked node universe count drift")

    canonical=source_result["registry"]["canonical_nodes"]
    node_ids=tuple(sorted(canonical))
    coordinates={
        node_id:(float(canonical[node_id]["longitude"]),float(canonical[node_id]["latitude"]))
        for node_id in node_ids
    }

    adequacy_raw=geometry_contract["structural_adequacy"]
    adequacy=StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(adequacy_raw["min_largest_weak_component_fraction"]),
        max_isolated_node_fraction=float(adequacy_raw["max_isolated_node_fraction"]),
        require_at_least_one_world_pass=bool(adequacy_raw["require_at_least_one_world_pass"]),
    )
    geometry=geometry_contract["geometry"]
    plan=plan_adequacy_complete_lcc_targets(
        len(node_ids),
        tuple(geometry["declared_lcc_targets"]),
        adequacy,
    )
    expected=geometry_contract["expected_finite_n_completion"]
    if plan.max_isolated_nodes!=expected["max_isolated_nodes"]:
        raise ValueError("finite-n isolated-node completion drift")
    if tuple(plan.completed_targets)!=tuple(expected["completed_lcc_targets"]):
        raise ValueError("adequacy-complete LCC target drift")

    family=generate_coordinate_world_family(
        node_ids,
        coordinates,
        metric=geometry["metric"],
        construction_mode="structural_lcc_ladder",
        axis_id="algar_v3_camera_location_haversine_km",
        target_lcc_fractions=plan.completed_targets,
        world_id_prefix=geometry["world_id_prefix"],
        deduplicate_identical_thresholds=geometry["deduplicate_identical_thresholds"],
        local_semantics={"kind":"local","source":"response_independent_locked_camera_coordinates"},
    )
    structural_worlds={world_id:family.worlds[world_id] for world_id in family.structural_world_ids}
    audit=audit_world_universe_structure(node_ids,structural_worlds,horizon=int(geometry["horizon"]))
    gate=apply_structural_adequacy_gate(audit,adequacy)
    by_id={row.world_id:row for row in audit.world_audits}

    return {
        "schema":"eog.algar_restoration_v3_geometry.result.v1",
        "status":"structural_ready" if gate.passed else "stop_structural_adequacy",
        "candidate_locked":True,
        "focal_species_selected":False,
        "response_bytes_opened":0,
        "model_fits":0,
        "heldout_scores":0,
        "node_count":len(node_ids),
        "adequacy_complete_plan":{
            "fingerprint":plan.fingerprint,
            "declared_targets":list(plan.declared_targets),
            "required_lcc_targets":list(plan.required_lcc_targets),
            "completed_targets":list(plan.completed_targets),
            "max_isolated_nodes":plan.max_isolated_nodes,
            "horizon_reachability_requires_independent_design":plan.horizon_reachability_requires_independent_design,
        },
        "world_family":{
            "fingerprint":family.fingerprint,
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
                    "largest_weak_component_fraction":by_id[world_id].largest_weak_component_fraction,
                    "isolated_node_fraction":by_id[world_id].isolated_node_fraction,
                    "median_horizon_reachable_fraction":by_id[world_id].median_horizon_reachable_fraction,
                    "directed_edge_count":by_id[world_id].directed_edge_count,
                } for world_id in family.structural_world_ids
            },
        },
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }
