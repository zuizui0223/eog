import hashlib
import json
from pathlib import Path

from benchmarks import traversability_confirmation as benchmark


CONTRACT = Path("benchmarks/traversability_confirmation_contract.json")


def _fingerprint(payload):
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_traversability_confirmation_contract_matches_executable_constants():
    contract = json.loads(CONTRACT.read_text())
    fingerprint = contract.pop("fingerprint")
    assert _fingerprint(contract) == fingerprint == "e40dd8807a3ca51b3d228cf29ef6d8c9ee66caf4837dd29ec2e85479b34fb034"

    assert tuple(contract["confirmation_seeds"]) == benchmark.CONFIRMATION_SEEDS
    assert tuple(contract["regimes"]) == benchmark.REGIMES
    assert contract["n_motifs"] == benchmark.N_MOTIFS
    assert contract["n_folds"] == benchmark.N_FOLDS
    assert contract["l2_penalty"] == benchmark.L2_PENALTY
    assert contract["minimum_favourable_seeds"] == benchmark.MIN_FAVOURABLE_SEEDS
    assert contract["gates"]["endpoint_retreat"]["R3_minus_R0_mean_min"] == -benchmark.MAX_ENDPOINT_EXTRA_GAIN
    assert contract["gates"]["path_added_information"]["R1_minus_R0_mean_max"] == -benchmark.MIN_PATH_GAIN
    assert contract["gates"]["niche_added_information"]["R2_minus_R1_mean_max"] == -benchmark.MIN_NICHE_GAIN
    assert contract["gates"]["long_jump_added_information"]["R3_minus_R2_mean_max"] == -benchmark.MIN_LONG_JUMP_GAIN


def test_confirmation_contract_forbids_post_outcome_gate_tuning():
    contract = json.loads(CONTRACT.read_text())
    assert "retain fail" in contract["failure_policy"]
    assert "no empirical outcome" in contract["response_firewall"]
