from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from pre_response_finalize import canonical_sha256  # noqa: E402


def git_blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("marker")
    args = parser.parse_args()

    marker_path = HERE / args.marker
    marker = json.loads(marker_path.read_text(encoding="utf-8"))

    bindings = {
        "outcome_runner.py": marker["outcome_runner_git_blob_sha"],
        "runner_core.py": marker["runner_core_git_blob_sha"],
        "outcome_access_authorization.json": marker["authorization_git_blob_sha"],
        "synthetic_smoke_certificate.json": marker["synthetic_smoke_certificate_git_blob_sha"],
        "stage1_certificate.json": marker["stage1_certificate_git_blob_sha"],
        "full_freeze_spec.json": marker["full_freeze_spec_git_blob_sha"],
        "once_only_v1_pre_response_failure_certificate.json": marker["v1_failure_certificate_git_blob_sha"],
        "once_only_v2_pre_response_failure_certificate.json": marker["v2_failure_certificate_git_blob_sha"],
        "pre_response_finalize.py": marker["pre_response_finalize_git_blob_sha"],
        "verify_once_only_marker.py": marker["verifier_git_blob_sha"],
        ".github/workflows/azores_yellow_eel_once_only.yml": marker["workflow_git_blob_sha"],
    }
    repository_root = HERE.parents[1]
    for relative, expected in bindings.items():
        path = repository_root / relative if relative.startswith(".github/") else HERE / relative
        observed = git_blob_sha(path)
        if observed != expected:
            raise SystemExit(f"marker-bound Git blob mismatch for {relative}: {observed} != {expected}")

    auth = json.loads((HERE / "outcome_access_authorization.json").read_text(encoding="utf-8"))
    smoke = json.loads((HERE / "synthetic_smoke_certificate.json").read_text(encoding="utf-8"))
    stage1 = json.loads((HERE / "stage1_certificate.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
    v1 = json.loads((HERE / "once_only_v1_pre_response_failure_certificate.json").read_text(encoding="utf-8"))
    v2 = json.loads((HERE / "once_only_v2_pre_response_failure_certificate.json").read_text(encoding="utf-8"))

    if auth["status"] != "authorized_once_only_exact_count_gate_required":
        raise SystemExit("outcome authorization is not green")
    if smoke["status"] != "synthetic_pre_response_runner_pass":
        raise SystemExit("synthetic smoke certificate is not green")
    if v1["status"] != "terminal_pre_response_certificate_transcription_failure":
        raise SystemExit("v1 pre-response failure certificate status drift")
    if v2["status"] != "terminal_pre_response_hash_semantics_failure":
        raise SystemExit("v2 pre-response failure certificate status drift")
    for certificate, label in ((v1, "v1"), (v2, "v2")):
        firewall = certificate["response_firewall_at_terminal"]
        if firewall["response_payload_requests"] != 0 or firewall["response_payload_bytes_opened"] != 0:
            raise SystemExit(f"{label} failure certificate does not prove zero response access")
        if firewall["response_rows_opened"] is not False or firewall["response_values_opened"] is not False:
            raise SystemExit(f"{label} failure certificate reports row/value response access")

    availability = stage1["temporal_availability"]["availability_fingerprint"]
    if len(availability) != 64:
        raise SystemExit("Stage1 availability fingerprint is not a complete SHA-256")
    if availability != freeze["node_geometry"]["availability_fingerprint"]:
        raise SystemExit("Stage1/full-freeze availability mismatch")
    if marker["authorization_fingerprint"] != auth["fingerprint"]:
        raise SystemExit("marker authorization fingerprint mismatch")
    if marker["full_freeze_spec_canonical_sha256"] != auth["full_freeze_spec_sha256"]:
        raise SystemExit("marker/auth canonical full-freeze fingerprint mismatch")
    if canonical_sha256(freeze) != marker["full_freeze_spec_canonical_sha256"]:
        raise SystemExit("canonical full-freeze SHA-256 mismatch")

    expected_sections = marker["scientific_section_fingerprints"]
    if auth["section_fingerprints"] != expected_sections:
        raise SystemExit("scientific section fingerprints differ from marker")

    print("once-only marker verification PASS")


if __name__ == "__main__":
    main()
