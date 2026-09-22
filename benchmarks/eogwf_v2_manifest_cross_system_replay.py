"""Cross-system response-free validation of the EOG-WF v2 manifest surface.

This benchmark combines the two real safe-source portability replays:

- Southwest Louisiana passive acoustics: prediction-facing Layer B remains eligible.
- Tampa Bay seagrass repeated transects: structural use remains available but the
  historical static/generation-shift Layer-B design is withheld from prediction.

Neither replay opens biological outcomes. The contrast tests the decision boundary of
one generic pre-response interface rather than asking for universally favorable
prediction.
"""

from __future__ import annotations

import json

from benchmarks.louisiana_manifest_v2_portability_replay import (
    run_replay as run_louisiana,
)
from benchmarks.tampa_manifest_v2_portability_replay import run_replay as run_tampa


def run_replay() -> dict[str, object]:
    louisiana = run_louisiana()
    tampa = run_tampa()

    if louisiana["uses_biological_response"] is not False:
        raise AssertionError("Louisiana replay unexpectedly uses biological response")
    if tampa["uses_biological_response"] is not False:
        raise AssertionError("Tampa replay unexpectedly uses biological response")

    louisiana_status = louisiana["statuses"]
    tampa_status = tampa["statuses"]

    if louisiana_status["structural"] != "structural_ready":
        raise AssertionError(louisiana_status)
    if tampa_status["structural"] != "structural_ready":
        raise AssertionError(tampa_status)
    if louisiana_status["predictive"] != "predictive_complement_candidate":
        raise AssertionError(louisiana_status)
    if tampa_status["predictive"] != "ineligible_generation_shift":
        raise AssertionError(tampa_status)
    if louisiana_status["predictive_use_allowed"] is not True:
        raise AssertionError(louisiana_status)
    if tampa_status["predictive_use_allowed"] is not False:
        raise AssertionError(tampa_status)

    return {
        "schema": "eog.manifest_cross_system_portability_replay.v1",
        "uses_biological_response": False,
        "counts_as_predictive_evidence": False,
        "systems": {
            "southwest_louisiana_passive_acoustics": {
                "node_count": louisiana["counts"]["node_count"],
                "context_count": louisiana["counts"]["context_count"],
                "candidate_count": louisiana["counts"]["scored_candidate_count"],
                "observation_mode": louisiana_status["observation"],
                "structural_status": louisiana_status["structural"],
                "predictive_status": louisiana_status["predictive"],
                "predictive_use_allowed": louisiana_status[
                    "predictive_use_allowed"
                ],
            },
            "tampa_bay_seagrass_transects": {
                "node_count": tampa["counts"]["node_count"],
                "context_count": tampa["counts"]["context_count"],
                "candidate_count": tampa["counts"]["scored_candidate_count"],
                "observation_mode": tampa_status["observation"],
                "structural_status": tampa_status["structural"],
                "predictive_status": tampa_status["predictive"],
                "predictive_use_allowed": tampa_status["predictive_use_allowed"],
            },
        },
        "genericity_result": (
            "same_pre_response_contract_supports_system_specific_prediction_decisions"
        ),
        "interpretation": (
            "The manifest layer is portable across distinct monitoring designs without "
            "forcing one prediction decision: Louisiana reaches predictive-complement "
            "eligibility, whereas Tampa remains structurally admissible but is stopped "
            "from default Layer-B prediction because its frozen train/serve generation "
            "and source semantics violate the same response-independent gate."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
