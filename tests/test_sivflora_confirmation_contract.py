import hashlib
import json
from pathlib import Path


CONTRACT = Path("benchmarks/sivflora_confirmation_contract.json")


def test_sivflora_confirmation_contract_is_preoutcome_and_fixed():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert payload["status"] == "pre_outcome"
    assert payload["source"]["zenodo_record_id"] == 14639076
    assert payload["source"]["file_name"] == "20250113_sivflora_v1.0.xlsx"
    assert payload["source"]["published_md5"] == "146d67f6b6628e9f570a2325880f76e8"
    assert payload["node_universe"]["expected_nodes"] == 22
    assert payload["node_universe"]["published_localities"] == 62
    assert payload["response"]["positive_statuses"] == ["native", "endemic"]
    assert payload["environment"]["variables"] == ["bio1", "bio5", "bio6", "bio12", "bio15"]
    assert payload["environment"]["products"] == ["CHELSA_v2.1", "WorldClim_v2.1"]
    assert payload["world_universe"]["world_count"] == 20
    assert payload["world_universe"]["geography_only_worlds"] == 4
    assert payload["world_universe"]["chelsa_worlds"] == 8
    assert payload["world_universe"]["worldclim_worlds"] == 8
    assert payload["validation"]["outer_split"] == "leave_one_island_out_22"
    assert payload["models"]["R2"].startswith("R1_plus_")
    assert payload["models"]["C_identity"] == "R2_plus_complete_20_bit_world_reachability_vector"
    assert payload["primary_metric"]["contrast"] == "C_identity_minus_R2"
    assert payload["primary_metric"]["bootstrap_seed"] == 20260816
    assert payload["favourable_gate"]["candidate_better_outer_islands_at_least"] == 12


def test_contract_has_stable_machine_hash_shape():
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert len(digest) == 64
    assert payload["no_added_value_rule"].startswith("If all favourable conditions are not satisfied")
