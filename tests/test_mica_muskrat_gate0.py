from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "validation" / "mica_muskrat_endpoint3" / "gate0_archive_transport.py"


def _load():
    spec = importlib.util.spec_from_file_location("mica_gate0", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _archive() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mica/deployments.csv", "deploymentID,locationID\nd1,l1\n")
        zf.writestr("mica/observations.csv", "observationID\no1\n")
        zf.writestr("mica/media.csv", "mediaID\nm1\n")
        zf.writestr("mica/datapackage.json", "{}")
    return buf.getvalue()


def test_zip_metadata_never_reads_member_payload_and_selects_frozen_members():
    m = _load()
    data = _archive()
    requests = []

    def read_range(start, end, role):
        requests.append((start, end, role))
        return data[start : end + 1]

    inventory = m.inspect_zip_metadata(len(data), read_range)
    payloads = [
        (int(x["payload_start"]), int(x["payload_end"]))
        for x in inventory["members"]
        if x["payload_end"] is not None
    ]
    for start, end, _ in requests:
        assert not any(m._overlaps((start, end), payload) for payload in payloads)

    rules = {
        "deployment_member": {"exact_unique_basename": "deployments.csv", "required_count": 1},
        "observation_member": {"exact_unique_basename": "observations.csv", "required_count": 1},
        "media_member": {"exact_unique_basename": "media.csv", "required_count": 1},
        "datapackage_member": {"exact_unique_basename": "datapackage.json", "required_count": 1},
    }
    selected = m.select_frozen_members(inventory, rules)
    assert selected["deployment_member"]["name"] == "mica/deployments.csv"
    assert selected["observation_member"]["name"] == "mica/observations.csv"
    assert selected["media_member"]["name"] == "mica/media.csv"
    assert selected["datapackage_member"]["name"] == "mica/datapackage.json"


def test_duplicate_frozen_basename_fails_closed():
    m = _load()
    inventory = {
        "members": [
            {"name": "a/deployments.csv", "basename": "deployments.csv"},
            {"name": "b/deployments.csv", "basename": "deployments.csv"},
        ]
    }
    with pytest.raises(m.Gate0Stop, match="expected exactly one"):
        m.select_frozen_members(
            inventory,
            {"deployment_member": {"exact_unique_basename": "deployments.csv", "required_count": 1}},
        )


def test_head_opens_zero_body_bytes(monkeypatch):
    m = _load()

    class Headers(dict):
        def items(self):
            return super().items()

    class Response:
        status = 200
        headers = Headers({"Content-Length": "12345", "Content-Type": "application/zip"})
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def getcode(self): return 200
        def geturl(self): return "https://ipt.inbo.be/archive.do?r=mica-agouti"
        def read(self, *args, **kwargs):
            raise AssertionError("HEAD body must never be read")

    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    transport = m.StrictIptTransport(
        "https://ipt.inbo.be/archive.do?r=mica-agouti",
        ("ipt.inbo.be",),
        ("application/zip",),
    )
    meta = transport.head()
    assert meta["content_length"] == 12345
    assert meta["body_bytes_opened"] == 0


def test_http_200_range_stops_before_body_read(monkeypatch):
    m = _load()

    class Headers(dict):
        def items(self):
            return super().items()

    class Response:
        status = 200
        headers = Headers({"Content-Length": "12345", "Content-Type": "application/zip"})
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def getcode(self): return 200
        def geturl(self): return "https://ipt.inbo.be/archive.do?r=mica-agouti"
        def read(self, *args, **kwargs):
            raise AssertionError("HTTP 200 range fallback body must not be read")

    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    transport = m.StrictIptTransport(
        "https://ipt.inbo.be/archive.do?r=mica-agouti",
        ("ipt.inbo.be",),
        ("application/zip",),
    )
    transport.archive_size = 12345
    with pytest.raises(m.Gate0Stop, match="HTTP 200"):
        transport.read_range(12323, 12344, "zip_eocd_zero_comment")
    assert transport.range_ledger[-1]["bytes_opened"] == 0


def test_contract_freezes_deployment_semantics_before_deployment_bytes():
    import json
    contract = json.loads(
        (ROOT / "validation" / "mica_muskrat_endpoint3" / "source_contract.json").read_text()
    )
    gate = contract["deployment_gate_frozen_before_deployment_bytes"]
    assert gate["analysis_node"] == "locationID"
    assert gate["minimum_active_nodes_per_heldout_week"] == 15
    assert gate["minimum_heldout_outer_weeks"] == 8
    assert gate["minimum_repeated_nodes_spanning_calibration_and_heldout"] == 15
    assert gate["minimum_total_analysis_nodes"] == 20
    assert gate["minimum_distinct_response_blind_structural_scales"] == 3
    assert gate["response_derived_node_filtering"] is False
    assert contract["transport_firewall"]["full_archive_download_forbidden"] is True
    assert contract["post_stop_retuning"] is False
