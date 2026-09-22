"""Cross-system response-free preflight synthesis for EOG-WF v2.

This benchmark does not pool predictive scores. It asks whether the v2 pre-response
contracts distinguish three different situations that were historically conflated as
"failure":

- STOC: the frozen spatial world scale was structurally incapable of spanning the
  intended forecast domain;
- Louisiana: the response-independent design translates through the full v2 contract
  and reaches predictive-outcome authorization;
- Tampa: the source/registry design was response-ready, but the frozen Layer-B feature
  generator is prediction-ineligible before consulting its observed predictive score.

The evidence type is preserved for each system; no historical endpoint is reopened.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmarks.louisiana_real_pre_response_v2_translation import (
    run_replay as run_louisiana,
)
from benchmarks.tampa_predictive_state_v2_translation import (
    run_replay as run_tampa,
)


ROOT = Path(__file__).resolve().parents[1]
STOC_SCALE = ROOT / "validation" / "stoc_eogwf" / "posthoc_scale_ladder_result.json"
TAMPA_GATE0 = (
    ROOT / "validation" / "tampa_seagrass_endpoint3" / "gate0_pass_certificate.json"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def run_benchmark() -> dict[str, object]:
    stoc = _load(STOC_SCALE)
    tampa_gate0 = _load(TAMPA_GATE0)
    louisiana = run_louisiana()
    tampa = run_tampa()

    # STOC evidence is deliberately response-blind and post-hoc method diagnosis.
    if stoc["species_response_columns_parsed"] is not False:
        raise AssertionError("STOC structural diagnostic must remain response blind")
    old_lcc = float(stoc["old_frozen_stoc_geo_q90_largest_component_fraction"])
    old_radius = float(stoc["old_frozen_stoc_geo_q90_threshold_km"])
    v2_domain_target = 0.90
    stoc_structural_pass = old_lcc >= v2_domain_target
    if stoc_structural_pass:
        raise AssertionError("historical STOC q90 world unexpectedly passes v2 domain bracket")
    q90_levels = [
        row
        for row in stoc["geography_ladder"]
        if float(row["target_largest_component_fraction"]) == v2_domain_target
    ]
    if len(q90_levels) != 1:
        raise AssertionError("STOC response-blind 0.90 structural target is not unique")
    bracket = q90_levels[0]

    # Louisiana is the strongest translation: all generic pre-response contracts exist.
    if louisiana["uses_biological_response"] is not False:
        raise AssertionError("Louisiana translation reopened biological response")
    if louisiana["certificate"]["predictive_outcome_access_allowed"] is not True:
        raise AssertionError("Louisiana full v2 preflight no longer authorizes outcome access")

    # Tampa Gate0 was prospectively response-ready, but v2 Layer-B use is independently blocked.
    if tampa_gate0["status"] != "gate0_pre_response_ready":
        raise AssertionError("Tampa historical Gate0 readiness drift")
    firewall = tampa_gate0["firewall"]
    if (
        int(firewall["occurrence_bytes_opened"]) != 0
        or int(firewall["model_fits"]) != 0
        or int(firewall["heldout_scores"]) != 0
    ):
        raise AssertionError("Tampa Gate0 is no longer response blind")
    if tampa["uses_observed_tampa_predictive_score"] is not False:
        raise AssertionError("Tampa v2 gate must not consult the historical score")
    if tampa["v2_predictive_state_gate"]["predictive_use_allowed"] is not False:
        raise AssertionError("Tampa historical Layer-B design must remain v2-ineligible")

    systems = {
        "stoc": {
            "disposition": "stop_before_response_structural_scale",
            "evidence_type": "posthoc_response_blind_method_diagnostic",
            "response_used": False,
            "trigger": "declared_world_universe_does_not_bracket_forecast_domain",
            "historical_q90_threshold_km": old_radius,
            "historical_q90_largest_component_fraction": old_lcc,
            "v2_domain_target_fraction": v2_domain_target,
            "response_blind_bracketing_threshold_km": float(
                bracket["distance_threshold"]
            ),
            "response_blind_bracketing_largest_component_fraction": float(
                bracket["achieved_largest_component_fraction"]
            ),
            "claim_ceiling": (
                "method-design diagnosis only; does not replace the frozen STOC test "
                "or count as independent confirmation"
            ),
        },
        "louisiana": {
            "disposition": "predictive_outcome_authorized",
            "evidence_type": "real_response_blind_full_v2_translation",
            "response_used": False,
            "trigger": "all_pre_response_contracts_satisfied",
            "node_count": int(louisiana["registry"]["node_count"]),
            "surveyed_unit_count": int(louisiana["effort"]["surveyed_count"]),
            "initialization_unit_count": int(
                louisiana["effort"]["initialization_count"]
            ),
            "scored_candidate_count": int(
                louisiana["effort"]["scored_candidate_count"]
            ),
            "predictive_state_status": str(
                louisiana["predictive_state"]["status"]
            ),
            "claim_ceiling": (
                "pre-response authorization only; does not establish predictive gain "
                "in a new endpoint"
            ),
        },
        "tampa": {
            "disposition": "response_ready_but_layer_b_prediction_blocked",
            "evidence_type": "frozen_pre_response_contract_plus_response_independent_geometry_audit",
            "response_used": False,
            "trigger": "prediction_facing_representation_contract_failure",
            "historical_gate0_ready": True,
            "node_count": int(tampa["frozen_candidate_universe"]["node_count"]),
            "candidate_unit_count": int(
                tampa["frozen_candidate_universe"]["candidate_unit_count"]
            ),
            "predictive_state_status": str(
                tampa["v2_predictive_state_gate"]["status"]
            ),
            "reasons": list(tampa["v2_predictive_state_gate"]["reasons"]),
            "claim_ceiling": (
                "would withhold default Layer-B supervised use; does not erase or "
                "reinterpret the historical Tampa endpoint"
            ),
        },
    }

    dispositions = {row["disposition"] for row in systems.values()}
    if len(dispositions) != 3:
        raise AssertionError("v2 preflight failed to separate the three system states")

    return {
        "schema": "eog.eogwf_v2_cross_system_preflight.v1",
        "uses_biological_response": False,
        "uses_historical_predictive_scores": False,
        "reruns_frozen_endpoints": False,
        "counts_as_predictive_evidence": False,
        "system_count": 3,
        "distinct_disposition_count": len(dispositions),
        "systems": systems,
        "interpretation": (
            "EOG-WF v2 does not treat every failed or adverse attempt as the same "
            "problem. It can stop a structurally under-scaled world universe before "
            "response access, authorize a fully declared sequential design, or retain "
            "structural use while blocking a prediction-facing representation whose "
            "generation semantics are unsafe. Generality is therefore expressed as a "
            "shared contract with system-specific dispositions, not as forcing one "
            "Layer-B feature block into every ecological dataset."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
