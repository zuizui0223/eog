from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.version_info[:2] != (3, 12), reason="one audited external Gate0 run on Python 3.12 only")
def test_andrews_we008_metadata_only_gate0_preserves_response_firewall():
    """Audit-only PR gate: execute the frozen metadata-only Gate0 once in existing CI.

    This test is candidate-branch material and is not intended to merge to main.
    It may read WE008 landing/EML metadata and HEAD response-independent effort/
    geometry entities. It must never HEAD/GET the capture-response entity.
    """
    root = Path(__file__).resolve().parents[1]
    script = root / "validation" / "andrews_we008_red_backed_vole_replication_2" / "gate0_metadata_only.py"
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
