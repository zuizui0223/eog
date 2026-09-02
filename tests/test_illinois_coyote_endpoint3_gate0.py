import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "validation" / "illinois_coyote_endpoint3" / "gate0_metadata.py"
CONTRACT_PATH = ROOT / "validation" / "illinois_coyote_endpoint3" / "source_contract.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("illinois_coyote_gate0", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _files_payload(names):
    return {
        "_embedded": {
            "stash:files": [
                {
                    "path": name,
                    "size": 100 + i,
                    "digest": f"md5-{i}",
                    "digestType": "md5",
                    "mimeType": "text/csv" if name.endswith(".csv") else "text/markdown",
                    "status": "copied",
                    "_links": {
                        "self": {"href": f"/api/v2/files/{1000+i}"},
                        "stash:download": {"href": f"/api/v2/files/{1000+i}/download"},
                    },
                }
                for i, name in enumerate(names)
            ]
        }
    }


def test_metadata_gate_accepts_exact_frozen_file_universe_without_payload_access():
    m = _load_module()
    contract = _contract()
    expected = contract["dryad"]["expected_exact_file_names"]
    result = m.evaluate_metadata(
        contract,
        {"identifier": "doi:10.5061/dryad.p8cz8wb5w"},
        {"id": 12345},
        _files_payload(expected),
    )
    assert result["status"] == "gate0_metadata_ready"
    assert result["file_count"] == 8
    assert result["metadata_only"] is True
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_metadata_gate_fails_closed_on_file_identity_drift():
    m = _load_module()
    contract = _contract()
    names = list(contract["dryad"]["expected_exact_file_names"])
    names[-1] = "unexpected.csv"
    try:
        m.evaluate_metadata(
            contract,
            {"identifier": "doi:10.5061/dryad.p8cz8wb5w"},
            {"id": 12345},
            _files_payload(names),
        )
    except m.MetadataGateStop as exc:
        assert "file identity drift" in str(exc)
    else:
        raise AssertionError("file identity drift must stop")


def test_contract_keeps_detection_history_forbidden_and_paper_bindings_fixed():
    contract = _contract()
    assert contract["roles"]["forbidden_response_until_full_freeze"] == "Coyote_Detection_History.csv"
    assert "any CSV header" in contract["stage0_forbidden"]
    assert contract["selection_boundary"]["response_count_used_for_selection"] is False
    assert contract["selection_boundary"]["source_paper_blindness_claimed"] is False
    assert contract["paper_ready_bindings"] == {
        "cross_ecosystem_synthesis_canonical_sha256": "1617b18b6b0c3e2797945c3d30111a4e3e6941a560a6b8a39b8d117e84c82b02",
        "feature_count_placebo_canonical_sha256": "72129df202a4d8c0203b507f82c3cbc6c612feb028d12b6386dc39abde4de8cd",
        "excluded_world_information_canonical_sha256": "7f76113602346347829378c1daaf8a3f057d1ee6fe72f0141dc998b69966a53a",
    }
