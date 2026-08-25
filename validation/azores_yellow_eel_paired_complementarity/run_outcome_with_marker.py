from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def install_verified_marker_alias(marker_name: str) -> dict:
    marker_path = HERE / marker_name
    payload = marker_path.read_bytes()
    marker = json.loads(payload.decode("utf-8"))
    if marker.get("attempt_id") != "azores_yellow_eel_receiver_week_fresh_paired_v1":
        raise SystemExit("marker attempt mismatch")
    if marker.get("authorization_fingerprint") is None:
        raise SystemExit("marker authorization fingerprint missing")
    if marker.get("full_freeze_spec_sha256") is None:
        raise SystemExit("legacy-compatible canonical freeze fingerprint missing")
    # The frozen outcome runner predates versioned trigger markers and reads this exact
    # filename.  The workflow verifies marker_name before this wrapper runs.  We copy
    # the already-verified bytes only inside the ephemeral CI checkout; no repository
    # content or scientific freeze is changed.
    (HERE / "OUTCOME_AUTHORIZED_ONCE").write_bytes(payload)
    return marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("marker")
    parser.add_argument("--pre-response-only", action="store_true")
    args = parser.parse_args()

    marker = install_verified_marker_alias(args.marker)
    if not args.pre_response_only:
        os.execv(sys.executable, [sys.executable, str(HERE / "outcome_runner.py")])

    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import outcome_runner as runner

    runner.validate_authorization_and_runtime()
    metadata = runner.bounded_json(
        f"https://zenodo.org/api/records/{runner.SPEC['source_identity']['dataset_zenodo_record']}"
    )
    inputs = runner.reconstruct_response_independent_inputs(metadata)
    if runner.AUDIT["response_payload_requests"] != 0:
        raise SystemExit("pre-response-only smoke unexpectedly opened response payload")
    if runner.AUDIT["response_payload_bytes_opened"] != 0:
        raise SystemExit("pre-response-only smoke unexpectedly opened response bytes")
    if runner.AUDIT["response_rows_opened"] is not False:
        raise SystemExit("pre-response-only smoke unexpectedly opened response rows")

    result = {
        "status": "pre_response_execution_path_pass",
        "marker_version": marker.get("marker_version"),
        "authorization_fingerprint": marker["authorization_fingerprint"],
        "station_count": len(inputs["stations"]),
        "eligible_receiver_week_count": len(inputs["eligible_active_days"]),
        "response_payload_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "primary_outer_units_scored": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
