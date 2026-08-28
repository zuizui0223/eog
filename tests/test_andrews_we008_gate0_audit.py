from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "validation" / "andrews_we008_red_backed_vole_replication_2" / "gate0_metadata_only.py"
SPEC = importlib.util.spec_from_file_location("andrews_gate0_metadata_only", SCRIPT)
assert SPEC and SPEC.loader
GATE0 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE0)


def test_andrews_gate0_matches_frozen_role_against_eml_entity_description():
    xml = b"""<?xml version='1.0'?>
    <eml>
      <dataset>
        <dataTable>
          <entityName>WE00801</entityName>
          <entityDescription>Small vertebrate captures</entityDescription>
          <physical><objectName>WE00801.csv</objectName></physical>
        </dataTable>
      </dataset>
    </eml>
    """
    tables = GATE0.parse_tables(xml)

    selected = GATE0.select_entity(
        tables,
        {"ordinal": 1, "entity_name_contains": "Small vertebrate captures"},
    )

    assert selected["entity_name"] == "WE00801"
    assert selected["entity_descriptions"] == ["Small vertebrate captures"]


def test_andrews_gate0_uses_case_correct_catalog_landing_url():
    contract = json.loads(
        (ROOT / "validation" / "andrews_we008_red_backed_vole_replication_2" / "source_contract.json").read_text()
    )
    assert contract["source"]["landing_url"] == (
        "https://andlter.forestry.oregonstate.edu/data/abstract.aspx?dbcode=WE008"
    )


@pytest.mark.skipif(sys.version_info[:2] != (3, 12), reason="one audited external Gate0 run on Python 3.12 only")
def test_andrews_we008_metadata_only_gate0_preserves_response_firewall():
    """Audit-only PR gate: execute the frozen metadata-only Gate0 once in existing CI.

    This test is candidate-branch material and is not intended to merge to main.
    It may read WE008 landing/EML metadata and HEAD response-independent effort/
    geometry entities. It must never HEAD/GET the capture-response entity.
    """
    root = ROOT
    script = SCRIPT
    result_path = root / "build" / "andrews_we008_red_backed_vole_replication_2" / "gate0_metadata_only.json"

    proc = subprocess.run([sys.executable, str(script)], cwd=root, text=True, capture_output=True, timeout=180)
    assert result_path.exists(), proc.stdout + "\n" + proc.stderr
    result = json.loads(result_path.read_text())
    firewall = result["response_firewall"]

    assert firewall["capture_data_get_requests"] == 0
    assert firewall["capture_payload_bytes_opened"] == 0
    assert firewall["capture_header_bytes_opened"] == 0
    assert firewall["capture_rows_opened"] is False
    assert firewall["capture_values_opened"] is False
    assert firewall["model_fits"] == 0
    assert firewall["heldout_scores"] == 0
    assert result.get("head_checks", {}).get("forbidden_response_head_requests", 0) == 0

    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert result["status"] == "gate0_pass_metadata_only_physical_separation_and_transport", result
