import hashlib
import json
from pathlib import Path


RESULT = Path("benchmarks/frozen/finland_strict_source_cohort/empirical_result_summary.json")


def _canonical_sha256(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()


def test_finland_strict_source_result_is_frozen_no_go():
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    observed = result.pop("fingerprint")
    assert _canonical_sha256(result) == observed == "209eb703be5e0574bec9ebc8b129d0760fdb8c6db807c5fe7ccbb2d519e2afe0"
    assert result["workflow_run"] == 31690500533
    assert result["artifact_id"] == 9177201442
    assert result["result_fingerprint"] == "97de0a30c197e8352589fd98f0da976c69d4761229d2ec70106975292182068e"
    assert result["n_species"] == 180
    assert result["n_rows"] == 74700
    assert result["pooled_R2_minus_R0_log_loss"] == -0.021035162498828225
    assert result["mean_species_C_minus_R2_log_loss"] == -0.00013800642598677228
    assert result["species_bootstrap_95_interval"] == [-0.00028370978779246455, 1.4795433136458638e-08]
    assert result["checks"] == {
        "minimum_species": True,
        "strong_reference_operational": True,
        "mean_species_candidate_increment": True,
        "bootstrap_upper_bound": False,
    }
    assert result["decision"] == "no_empirical_added_information"
    assert result["promotion_go"] is False
    assert result["post_response_retuning_allowed"] is False
