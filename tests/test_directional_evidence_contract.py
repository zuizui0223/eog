import hashlib
import json
from pathlib import Path

from benchmarks import directional_evidence_confirmation as benchmark


CONTRACT = Path("benchmarks/directional_evidence_confirmation_contract.json")


def _fingerprint(payload):
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_directional_evidence_contract_matches_executable_constants():
    contract = json.loads(CONTRACT.read_text())
    fingerprint = contract.pop("fingerprint")
    assert _fingerprint(contract) == fingerprint == "dc7e43c33fd724c813c09b8dbbc6228cb6d377271f40330323b0f8920d98db3c"
    assert tuple(contract["confirmation_seeds"]) == benchmark.CONFIRMATION_SEEDS
    assert tuple(contract["node_ids"]) == benchmark.NODE_IDS
    assert tuple(contract["occurrence_ids"]) == benchmark.OCCURRENCE_IDS
    assert tuple(contract["fixed_source_ids"]) == benchmark.FIXED_SOURCE_IDS
    assert contract["max_steps"] == benchmark.MAX_STEPS
    assert contract["loss_support"] == benchmark.LOSS_SUPPORT
    assert contract["minimum_support_ratio"] == benchmark.MINIMUM_SUPPORT_RATIO
    assert tuple(
        (row["earlier_id"], row["later_id"], row["evidence_id"])
        for row in contract["constraints"]
    ) == tuple(
        (item.earlier_id, item.later_id, item.evidence_id)
        for item in benchmark.CONSTRAINTS
    )


def test_directional_contract_forbids_post_outcome_tuning_and_winner_score():
    contract = json.loads(CONTRACT.read_text())
    assert "retain fail" in contract["failure_policy"]
    assert "no empirical" in contract["empirical_firewall"]
    assert contract["selection_policy"].startswith("no winner score")
