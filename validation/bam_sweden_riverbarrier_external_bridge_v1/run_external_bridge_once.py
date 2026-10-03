"""Once-only execution for the Sweden river-barrier M-only bridge.

The runner is inert until:
1. Gate0 Dryad metadata PASS is committed;
2. README schema certificate is authorized and fingerprint-bound;
3. execution contract is authorized.

Only rawdf.csv is parsed. Other Dryad files may be checksum-verified inside a version
archive fallback but are never interpreted.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
import zipfile

import pandas as pd

from eog.v2.bam_sweden_riverbarrier_external_bridge import execute_bridge


HERE = Path(__file__).resolve().parent
GATE0 = HERE / "gate0_dryad_identity_certificate.json"
README_CERT = HERE / "readme_schema_certificate.json"
CONTRACT = HERE / "execution_contract_draft.json"
OUTPUT = HERE / "external_bridge_result_v1.json"

BASE = "https://datadryad.org"
USER_AGENT = "EOG-Sweden-RiverBarrier-OnceOnly/1.0"


class ExecutionStop(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        payload_requests: int = 0,
        payload_bytes_opened: int = 0,
    ) -> None:
        super().__init__(message)
        self.payload_requests = int(payload_requests)
        self.payload_bytes_opened = int(payload_bytes_opened)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def load_authorized_contract():
    if not GATE0.exists():
        raise ExecutionStop("Gate0 certificate is not committed")
    if not README_CERT.exists():
        raise ExecutionStop("README schema certificate is not committed")
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    readme = json.loads(README_CERT.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    if gate0.get("status") != "dryad_source_identity_ready":
        raise ExecutionStop("Gate0 is not PASS")
    if readme.get("status") != "readme_schema_ready":
        raise ExecutionStop("README schema certificate is not PASS")
    if readme.get("gate0_fingerprint") != gate0.get("fingerprint"):
        raise ExecutionStop("README certificate Gate0 fingerprint mismatch")
    if contract.get("status") != "authorized_for_once_only_rawdf_execution":
        raise ExecutionStop("execution contract is not authorized")
    if (
        contract["gate0_certificate"]["fingerprint"]
        != gate0.get("fingerprint")
    ):
        raise ExecutionStop("execution contract Gate0 fingerprint mismatch")
    if (
        contract["documentation_schema_certificate"]["fingerprint"]
        != readme.get("fingerprint")
    ):
        raise ExecutionStop("execution contract README fingerprint mismatch")
    return gate0, readme, contract


def _rawdf_spec(gate0: dict):
    rows = [row for row in gate0["files"] if row["path"] == "rawdf.csv"]
    if len(rows) != 1:
        raise ExecutionStop(f"expected one rawdf metadata row, got {len(rows)}")
    return rows[0]


def _verified_member(
    archive: zipfile.ZipFile,
    member: str,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    body = archive.read(member)
    if len(body) != int(expected_size):
        raise ExecutionStop(
            f"archive member size drift for {member}",
            payload_bytes_opened=len(body),
        )
    sha = hashlib.sha256(body).hexdigest()
    if sha != expected_sha256:
        raise ExecutionStop(
            f"archive member sha256 drift for {member}",
            payload_bytes_opened=len(body),
        )
    return body


def try_version_archive(gate0: dict) -> tuple[bytes, int] | None:
    version_id = int(gate0["version_id"])
    url = f"{BASE}/api/v2/versions/{version_id}/download"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/zip",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            if int(response.status) != 200:
                return None
            ceiling = sum(int(row["size_bytes"]) for row in gate0["files"]) + 5_000_000
            archive_bytes = response.read(ceiling + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return None

    if len(archive_bytes) > ceiling:
        raise ExecutionStop(
            "version archive exceeded frozen safety ceiling",
            payload_requests=1,
            payload_bytes_opened=len(archive_bytes),
        )

    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
        by_basename: dict[str, str] = {}
        for info in archive.infolist():
            if info.is_dir():
                continue
            base = Path(info.filename).name
            if base in by_basename:
                raise ExecutionStop(f"duplicate archive basename: {base}")
            by_basename[base] = info.filename

        expected_names = {str(row["path"]) for row in gate0["files"]}
        if set(by_basename) != expected_names:
            raise ExecutionStop(
                "version archive roster drift: "
                f"missing={sorted(expected_names-set(by_basename))}; "
                f"unexpected={sorted(set(by_basename)-expected_names)}"
            )

        rawdf_meta = _rawdf_spec(gate0)
        rawdf = _verified_member(
            archive,
            by_basename["rawdf.csv"],
            int(rawdf_meta["size_bytes"]),
            str(rawdf_meta["sha256"]),
        )
    except Exception as exc:
        if isinstance(exc, ExecutionStop):
            message = str(exc)
        elif isinstance(exc, zipfile.BadZipFile):
            message = "version archive is not a ZIP"
        else:
            message = f"version archive verification failed: {exc}"
        raise ExecutionStop(
            message,
            payload_requests=1,
            payload_bytes_opened=len(archive_bytes),
        ) from exc

    return rawdf, len(archive_bytes)


def configured_token() -> str | None:
    for key in ("DRYAD_TOKEN", "DRYAD_API_TOKEN", "DRYAD_ACCESS_TOKEN"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return None


def download_rawdf_exact(gate0: dict, token: str) -> bytes:
    meta = _rawdf_spec(gate0)
    req = urllib.request.Request(
        BASE + str(meta["download_api_path"]),
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            if int(response.status) != 200:
                raise ExecutionStop(
                    f"rawdf download returned HTTP {response.status}"
                )
            body = response.read(int(meta["size_bytes"]) + 1)
    except ExecutionStop:
        raise
    except Exception as exc:
        raise ExecutionStop(f"rawdf download failed: {exc}") from exc

    if len(body) != int(meta["size_bytes"]):
        raise ExecutionStop(
            "rawdf size drift",
            payload_requests=1,
            payload_bytes_opened=len(body),
        )
    sha = hashlib.sha256(body).hexdigest()
    if sha != str(meta["sha256"]):
        raise ExecutionStop(
            "rawdf sha256 drift",
            payload_requests=1,
            payload_bytes_opened=len(body),
        )
    return body


def parse_rawdf(body: bytes, expected_columns: list[str]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(
            io.BytesIO(body),
            encoding="utf-8",
            keep_default_na=True,
        )
    except Exception as exc:
        raise ExecutionStop(f"CSV parse failed: {exc}") from exc
    if list(frame.columns) != list(expected_columns):
        raise ExecutionStop(
            "CSV schema mismatch: "
            f"expected={expected_columns}, observed={list(frame.columns)}"
        )
    return frame


def main() -> int:
    payload_requests = 0
    payload_bytes_opened = 0
    values_parsed = False
    try:
        gate0, readme, contract = load_authorized_contract()
        archive = try_version_archive(gate0)
        if archive is not None:
            rawdf_body, opened = archive
            payload_requests = 1
            payload_bytes_opened = opened
            transport = "anonymous_verified_version_archive"
        else:
            token = configured_token()
            if token is None:
                raise ExecutionStop(
                    "anonymous version archive unavailable and Dryad credential absent"
                )
            rawdf_body = download_rawdf_exact(gate0, token)
            payload_requests = 1
            payload_bytes_opened = len(rawdf_body)
            transport = "credential_bound_exact_file"

        frame = parse_rawdf(
            rawdf_body,
            contract["frozen_parser"]["exact_columns"],
        )
        values_parsed = True
        result = execute_bridge(frame)
        result["transport"] = transport
        result["gate0_fingerprint"] = gate0["fingerprint"]
        result["readme_fingerprint"] = readme["fingerprint"]
        result["rawdf_sha256"] = _rawdf_spec(gate0)["sha256"]
        result["rawdf_payload_requests"] = payload_requests
        result["rawdf_or_archive_bytes_opened"] = payload_bytes_opened
        result["rawdf_values_parsed"] = True
    except Exception as exc:
        if isinstance(exc, ExecutionStop):
            payload_requests += exc.payload_requests
            payload_bytes_opened += exc.payload_bytes_opened
        result = {
            "schema": "eog.bam_sweden_riverbarrier_external_bridge.result.v1",
            "status": "stop_before_or_during_once_only_execution",
            "reason": str(exc),
            "rawdf_payload_requests": payload_requests,
            "rawdf_or_archive_bytes_opened": payload_bytes_opened,
            "rawdf_values_parsed": values_parsed,
            "model_fits": 0,
            "retry_allowed": payload_bytes_opened == 0,
            "scientific_effect": (
                "none_pre_response_transport_stop"
                if payload_bytes_opened == 0
                else "terminal_payload_stop_no_rerun"
            ),
        }

    result["fingerprint"] = canonical_sha256(
        {k: v for k, v in result.items() if k != "fingerprint"}
    )
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
