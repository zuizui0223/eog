import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "world_survival_regime_v1"
PROTOCOL = BASE / "neon_small_mammal_protocol_v1.json"
LOCK = BASE / "neon_small_mammal_protocol_lock_v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha1(path):
    raw = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def test_neon_regime_protocol_locked_before_metadata_or_response_access():
    protocol = _load(PROTOCOL)
    lock = _load(LOCK)

    assert lock["protocol_git_blob_sha1"] == _git_blob_sha1(PROTOCOL)
    assert lock["lock_state"] == "frozen_before_metadata_capture"
    assert lock["candidate_roster_captured"] is False
    assert lock["biological_response_endpoint_requests"] == 0
    assert lock["biological_response_bytes_opened"] == 0
    assert lock["model_fits"] == 0
    assert lock["scored_systems"] == 0

    assert protocol["current_stage"] == "metadata_capture_not_started"


def test_neon_metadata_capture_contract_forbids_response_endpoints():
    protocol = _load(PROTOCOL)
    source = protocol["source"]

    assert source["product_code"] == "DP1.10072.001"
    assert source["release"] == "RELEASE-2026"
    forbidden = source["forbidden_before_forecast_lock"]
    assert "/api/v0/data/*" in forbidden
    assert "/api/v0/data/query*" in forbidden
    assert "mam_pertrapnight payload or header" in forbidden
    assert "mam_perplotnight payload or header" in forbidden


def test_neon_site_and_node_selection_is_deterministic_before_response():
    protocol = _load(PROTOCOL)
    sites = protocol["candidate_sites"]
    nodes = protocol["node_registry"]

    assert sites["sort"] == "siteCode ascending"
    assert sites["maximum_sites"] == 16
    assert "first 16" in sites["selection"]
    assert sites["no_replacement_after_response_open"] is True

    assert nodes["unit"] == "individual mammal trap named location"
    assert nodes["minimum_nodes"] == 20
    assert nodes["geometry_metric"] == "haversine_km"


def test_neon_target_guild_and_design_contamination_exclusions_are_frozen():
    protocol = _load(PROTOCOL)
    target = protocol["response_target"]

    assert target["include_if"] == {
        "dwc:taxonRank": "species",
        "taxonProtocolCategory": "target",
    }
    excluded = {
        row["scientific_name"]
        for row in target["design_contamination_exclusions"]
    }
    assert excluded == {"Peromyscus leucopus", "Peromyscus maniculatus"}
    assert target["minimum_positive_nodes"] == 2
    assert target["negative_records_used_for_world_elimination"] is False


def test_neon_regime_forecast_stays_layer_a_only():
    protocol = _load(PROTOCOL)
    worlds = protocol["worlds"]
    forecast = protocol["forecast"]
    integrity = protocol["integrity"]

    assert worlds["external_open"] is False
    assert worlds["all_worlds_falsifiable"] is True
    assert worlds["horizon"] == "node_count_minus_1"

    assert forecast["score"] == (
        "median_horizon_reachable_fraction / largest_weak_component_fraction"
    )
    assert forecast["cutoff"] == 0.5
    assert forecast["freeze_before_data_endpoint_access"] is True

    assert integrity["model_fits"] == 0
    assert integrity["log_loss_used"] is False
    assert integrity["prior_eogwf_stopped_systems_reused"] is False
    assert integrity["prior_consumed_systems_reused"] is False
