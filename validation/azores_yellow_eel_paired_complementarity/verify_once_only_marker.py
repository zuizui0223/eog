from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[1]
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

    bindings = marker.get("git_blob_bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise SystemExit("marker must contain non-empty git_blob_bindings")
    for relative, expected in sorted(bindings.items()):
        path = REPOSITORY_ROOT / relative
        if not path.is_file():
            raise SystemExit(f"marker-bound file missing: {relative}")
        observed = git_blob_sha(path)
        if observed != expected:
            raise SystemExit(f"marker-bound Git blob mismatch for {relative}: {observed} != {expected}")

    auth = json.loads((HERE / "outcome_access_authorization.json").read_text(encoding="utf-8"))
    smoke = json.loads((HERE / "synthetic_smoke_certificate.json").read_text(encoding="utf-8"))
    stage1 = json.loads((HERE / "stage1_certificate.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))

    if auth["status"] != "authorized_once_only_exact_count_gate_required":
        raise SystemExit("outcome authorization is not green")
    if smoke["status"] != "synthetic_pre_response_runner_pass":
        raise SystemExit("synthetic smoke certificate is not green")

    prior_failures = marker.get("prior_pre_response_failure_certificates")
    if not isinstance(prior_failures, list) or not prior_failures:
        raise SystemExit("marker must declare prior pre-response failure certificates")
    for relative in prior_failures:
        certificate = json.loads((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
        status = str(certificate.get("status") or "")
        if not status.startswith("terminal_pre_response_"):
            raise SystemExit(f"prior failure is not certified pre-response: {relative}")
        firewall = certificate.get("response_firewall_at_terminal") or {}
        if firewall.get("response_payload_requests") != 0 or firewall.get("response_payload_bytes_opened") != 0:
            raise SystemExit(f"prior failure certificate does not prove zero response payload access: {relative}")
        if firewall.get("response_rows_opened") is not False or firewall.get("response_values_opened") is not False:
            raise SystemExit(f"prior failure certificate reports response row/value access: {relative}")

    availability = stage1["temporal_availability"]["availability_fingerprint"]
    if len(availability) != 64:
        raise SystemExit("Stage1 availability fingerprint is not a complete SHA-256")
    if availability != freeze["node_geometry"]["availability_fingerprint"]:
        raise SystemExit("Stage1/full-freeze availability mismatch")

    if marker["authorization_fingerprint"] != auth["fingerprint"]:
        raise SystemExit("marker authorization fingerprint mismatch")
    canonical_freeze = canonical_sha256(freeze)
    if marker["full_freeze_spec_canonical_sha256"] != auth["full_freeze_spec_sha256"]:
        raise SystemExit("marker/auth canonical full-freeze fingerprint mismatch")
    if marker["full_freeze_spec_canonical_sha256"] != canonical_freeze:
        raise SystemExit("canonical full-freeze SHA-256 mismatch")
    if marker.get("full_freeze_spec_sha256") != canonical_freeze:
        raise SystemExit("legacy-compatible full_freeze_spec_sha256 is not the canonical freeze hash")

    expected_sections = marker["scientific_section_fingerprints"]
    if auth["section_fingerprints"] != expected_sections:
        raise SystemExit("scientific section fingerprints differ from marker")

    print("once-only marker verification PASS")


if __name__ == "__main__":
    main()
