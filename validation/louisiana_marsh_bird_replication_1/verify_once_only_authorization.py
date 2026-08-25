from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
AUTH = HERE / "outcome_access_authorization.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def git_blob_sha(path: Path) -> str:
    result = subprocess.run(
        ["git", "hash-object", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--marker", required=True)
    parser.add_argument("--mode", choices=("candidate", "actual"), required=True)
    args = parser.parse_args()

    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    core = auth["authorization_core"]
    observed_auth_fp = canonical_sha256(core)
    if observed_auth_fp != auth["authorization_fingerprint"]:
        raise SystemExit(
            f"authorization fingerprint mismatch: {observed_auth_fp} != {auth['authorization_fingerprint']}"
        )

    marker_path = Path(args.marker)
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    expected_name = (
        core["candidate_marker_path"] if args.mode == "candidate" else core["actual_marker_path"]
    )
    if marker_path.as_posix() != expected_name:
        raise SystemExit(f"marker path mismatch: {marker_path} != {expected_name}")
    if marker != core["marker_content"]:
        raise SystemExit("marker bytes/semantic content differs from frozen authorization marker content")
    if marker["authorization_fingerprint"] != auth["authorization_fingerprint"]:
        raise SystemExit("marker authorization fingerprint mismatch")
    if marker["attempt_id"] != core["attempt_id"]:
        raise SystemExit("marker attempt id mismatch")
    if marker["exact_count_gate_first"] is not True:
        raise SystemExit("marker does not require exact count gate first")
    if marker["response_rows_opened_before_marker"] is not False:
        raise SystemExit("marker claims response rows were already opened")
    if marker["rerun_permitted"] is not False:
        raise SystemExit("marker permits rerun")

    for relative_path, expected_sha in core["bound_git_blob_shas"].items():
        path = Path(relative_path)
        if not path.exists():
            raise SystemExit(f"bound path missing: {relative_path}")
        observed = git_blob_sha(path)
        if observed != expected_sha:
            raise SystemExit(
                f"Git blob mismatch for {relative_path}: {observed} != {expected_sha}"
            )

    freeze = json.loads(Path(core["full_freeze_path"]).read_text(encoding="utf-8"))
    observed_freeze = canonical_sha256(freeze)
    if observed_freeze != core["full_freeze_spec_sha256"]:
        raise SystemExit(
            f"canonical full-freeze mismatch: {observed_freeze} != {core['full_freeze_spec_sha256']}"
        )

    finalizer = json.loads(Path(core["pre_response_finalize_certificate_path"]).read_text(encoding="utf-8"))
    smoke = json.loads(Path(core["synthetic_smoke_certificate_path"]).read_text(encoding="utf-8"))
    preflight = json.loads(Path(core["production_preflight_certificate_path"]).read_text(encoding="utf-8"))
    header = json.loads(Path(core["header_certificate_path"]).read_text(encoding="utf-8"))
    if finalizer["finalizer_fingerprint"] != core["pre_response_finalize_fingerprint"]:
        raise SystemExit("pre-response finalizer certificate fingerprint mismatch")
    if smoke["smoke_fingerprint"] != core["synthetic_smoke_fingerprint"]:
        raise SystemExit("synthetic smoke certificate fingerprint mismatch")
    if preflight["production_boundary_fingerprint"] != core["production_preflight_fingerprint"]:
        raise SystemExit("production preflight certificate fingerprint mismatch")
    if header["result_fingerprint"] != core["header_certificate_fingerprint"]:
        raise SystemExit("header certificate fingerprint mismatch")

    for cert in (finalizer, smoke, preflight, header):
        text = json.dumps(cert, sort_keys=True)
        if '"KIRA_rows_opened": true' in text or '"selected_response_rows_opened": true' in text:
            raise SystemExit("certificate indicates row access before marker")

    print(json.dumps({
        "status": "once_only_authorization_verified",
        "mode": args.mode,
        "attempt_id": core["attempt_id"],
        "authorization_fingerprint": auth["authorization_fingerprint"],
        "full_freeze_spec_sha256": core["full_freeze_spec_sha256"],
        "bound_blob_count": len(core["bound_git_blob_shas"]),
        "response_rows_opened_before_marker": False,
        "rerun_permitted": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
