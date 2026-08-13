import hashlib
import json
from pathlib import Path

from benchmarks import occurrence_rule_compatibility_confirmation as benchmark


CONTRACT = Path("benchmarks/occurrence_rule_compatibility_confirmation_contract.json")


def _fingerprint(payload):
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_occurrence_rule_confirmation_contract_matches_executable_constants():
    contract = json.loads(CONTRACT.read_text())
    fingerprint = contract.pop("fingerprint")
    assert _fingerprint(contract) == fingerprint == "cd792c4aa5f3e1e7cdd5b4d4b9e61be8d8f191d00733ff53eac5f0a16a7f29ba"
    assert tuple(contract["confirmation_seeds"]) == benchmark.CONFIRMATION_SEEDS
    assert tuple(contract["node_ids"]) == benchmark.NODE_IDS
    assert tuple(contract["occurrence_ids"]) == benchmark.OCCURRENCE_IDS
    assert tuple(contract["fixed_source_ids"]) == benchmark.FIXED_SOURCE_IDS
    assert contract["max_steps"] == benchmark.MAX_STEPS
    assert contract["loss_support"] == benchmark.LOSS_SUPPORT


def test_contract_forbids_winner_score_and_post_outcome_tuning():
    contract = json.loads(CONTRACT.read_text())
    assert contract["selection_policy"].startswith("no winner score")
    assert "retain fail" in contract["failure_policy"]
    assert "no empirical" in contract["empirical_firewall"]
