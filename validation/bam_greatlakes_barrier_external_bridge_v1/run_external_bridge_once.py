"""Once-only Great Lakes A/M external-bridge execution.

This module is inert until a committed Gate1 PASS certificate and an authorized Gate2
contract are present.  It downloads exactly two checksum-bound RDS files, parses them
with base R readRDS, executes the frozen A/M bridge, and writes summary evidence only.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
import zipfile
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import numpy as np
import pandas as pd

from eog.tanzania_source_acquisition import (
    SourceContractError,
    _oauth_token,
)
from eog.v2.bam_greatlakes_barrier_external_bridge import (
    BridgeSchemaStop,
    calibration_species,
    evaluate_species,
    fit_habitat_scaling,
    join_catch_to_habitat,
    validate_catch_frame,
    validate_habitat_frame,
)


HERE = Path(__file__).resolve().parent
GATE0 = HERE / "gate0_dryad_identity_certificate.json"
GATE1 = HERE / "gate1_readme_certificate.json"
CONTRACT = HERE / "gate2_execution_contract_draft.json"
OUTPUT = HERE / "external_bridge_result_v1.json"
BASE = "https://datadryad.org"
USER_AGENT = "EOG-GreatLakes-AM-Bridge-OnceOnly/1.0"


class ExecutionStop(RuntimeError):
    pass


class _DropAuthOnCrossHostRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        if urlparse(req.full_url).netloc != urlparse(newurl).netloc:
            redirected.remove_header("Authorization")
        return redirected


_OPENER = build_opener(_DropAuthOnCrossHostRedirect())


def configured_dryad_token() -> tuple[str, str]:
    """Resolve credentials using the repository-wide Dryad conventions.

    Accepted sources, in order:
    1. legacy DRYAD_TOKEN used by the first bridge draft;
    2. DRYAD_API_TOKEN / DRYAD_ACCESS_TOKEN;
    3. DRYAD_CLIENT_ID + DRYAD_CLIENT_SECRET via the existing OAuth helper.

    No RDS request occurs here.
    """

    legacy = os.environ.get("DRYAD_TOKEN", "").strip()
    if legacy:
        return legacy, "legacy_dryad_token"

    try:
        token, mode = _oauth_token(os.environ, timeout=60)
    except SourceContractError as exc:
        raise ExecutionStop(
            f"Dryad credential resolution failed before RDS payload access: {exc}"
        ) from exc

    if not token:
        raise ExecutionStop(
            "Dryad credentials are absent; expected DRYAD_API_TOKEN, "
            "DRYAD_ACCESS_TOKEN, DRYAD_CLIENT_ID+DRYAD_CLIENT_SECRET, "
            "or legacy DRYAD_TOKEN; stop before any RDS payload request"
        )
    return token, mode


def verify_dryad_token() -> tuple[str, str]:
    token, auth_mode = configured_dryad_token()
    request = Request(
        BASE + "/api/v2/test",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with _OPENER.open(request, timeout=60) as response:
            if int(response.status) != 200:
                raise ExecutionStop(
                    f"Dryad token preflight returned HTTP {response.status}"
                )
            response.read(4096)
    except Exception as exc:
        raise ExecutionStop(
            f"Dryad token preflight failed before RDS payload access: {exc}"
        ) from exc
    return token, auth_mode


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


def load_authorized_contract() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not GATE0.exists():
        raise ExecutionStop("Gate0 PASS certificate is not committed")
    if not GATE1.exists():
        raise ExecutionStop("Gate1 PASS certificate is not committed")
    gate0 = json.loads(GATE0.read_text(encoding="utf-8"))
    gate1 = json.loads(GATE1.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if gate0.get("status") != "dryad_source_identity_ready":
        raise ExecutionStop("Gate0 is not PASS")
    if gate1.get("status") != "readme_schema_ready":
        raise ExecutionStop("Gate1 is not PASS")
    if gate1.get("gate0_fingerprint") != gate0.get("fingerprint"):
        raise ExecutionStop("Gate1 is not bound to the committed Gate0 certificate")
    if contract.get("status") != "authorized_for_once_only_rds_execution":
        raise ExecutionStop("Gate2 execution contract is not authorized")
    expected = contract["gate1_prerequisite"]["fingerprint"]
    if not expected or expected != gate1.get("fingerprint"):
        raise ExecutionStop("Gate1 fingerprint mismatch")
    return gate0, gate1, contract


def _verify_archive_member(
    archive: zipfile.ZipFile,
    member_name: str,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    body = archive.read(member_name)
    if len(body) != int(expected_size):
        raise ExecutionStop(
            f"version archive size drift for {member_name}: "
            f"expected {expected_size}, got {len(body)}"
        )
    sha = hashlib.sha256(body).hexdigest()
    if sha != str(expected_sha256):
        raise ExecutionStop(
            f"version archive sha256 drift for {member_name}: "
            f"expected {expected_sha256}, got {sha}"
        )
    return body


def try_anonymous_version_archive(
    gate0: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[bytes, bytes, int] | None:
    """Try the frozen Dryad version archive before requiring credentials.

    Any HTTP/auth failure before a 200 response returns None without opening RDS bytes.
    A successful archive response is accepted only after every Gate0 file matches the
    frozen size and SHA256; otherwise execution stops terminally after payload access.
    """

    version_id = int(gate0["version_id"])
    request = Request(
        BASE + f"/api/v2/versions/{version_id}/download",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/zip",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    try:
        with _OPENER.open(request, timeout=90) as response:
            if int(response.status) != 200:
                return None
            max_bytes = sum(int(row["size_bytes"]) for row in gate0["files"]) + 5_000_000
            archive_bytes = response.read(max_bytes + 1)
    except Exception:
        return None

    if len(archive_bytes) > max_bytes:
        raise ExecutionStop("Dryad version archive exceeded frozen safety ceiling")
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except zipfile.BadZipFile as exc:
        raise ExecutionStop(
            "Dryad version archive returned non-ZIP payload after HTTP 200"
        ) from exc

    by_basename: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        basename = Path(info.filename).name
        if basename in by_basename:
            raise ExecutionStop(
                f"duplicate basename in Dryad version archive: {basename}"
            )
        by_basename[basename] = info.filename

    expected_names = {str(row["path"]) for row in gate0["files"]}
    if set(by_basename) != expected_names:
        raise ExecutionStop(
            "Dryad version archive roster drift: "
            f"missing={sorted(expected_names-set(by_basename))}, "
            f"unexpected={sorted(set(by_basename)-expected_names)}"
        )

    verified: dict[str, bytes] = {}
    for row in gate0["files"]:
        name = str(row["path"])
        verified[name] = _verify_archive_member(
            archive,
            by_basename[name],
            int(row["size_bytes"]),
            str(row["sha256"]),
        )

    habitat_name = str(contract["frozen_files"]["habitat"]["path"])
    catch_name = str(contract["frozen_files"]["catch"]["path"])
    return verified[habitat_name], verified[catch_name], len(archive_bytes)


def download_bound_file(spec: dict[str, Any], token: str) -> bytes:
    request = Request(
        BASE + str(spec["download_api_path"]),
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    with _OPENER.open(request, timeout=90) as response:
        if int(response.status) != 200:
            raise ExecutionStop(
                f"{spec['path']} download returned HTTP {response.status}"
            )
        body = response.read(int(spec["size_bytes"]) + 1)
    if len(body) != int(spec["size_bytes"]):
        raise ExecutionStop(
            f"{spec['path']} size drift: expected {spec['size_bytes']}, got {len(body)}"
        )
    sha = hashlib.sha256(body).hexdigest()
    if sha != str(spec["sha256"]):
        raise ExecutionStop(
            f"{spec['path']} sha256 drift: expected {spec['sha256']}, got {sha}"
        )
    return body


_R_SCRIPT = r'''
args <- commandArgs(trailingOnly=TRUE)
obj <- readRDS(args[[1]])
if (!is.data.frame(obj)) {
  stop("RDS object is not a data.frame")
}
write.table(
  obj,
  file=args[[2]],
  sep="\t",
  row.names=FALSE,
  col.names=TRUE,
  quote=TRUE,
  na="NA",
  fileEncoding="UTF-8"
)
'''


def rds_bytes_to_frame(body: bytes, expected_columns: list[str]) -> pd.DataFrame:
    if shutil.which("Rscript") is None:
        raise ExecutionStop("Rscript is unavailable")
    with tempfile.TemporaryDirectory(prefix="eog_greatlakes_rds_") as tmp:
        tmpdir = Path(tmp)
        source = tmpdir / "input.rds"
        target = tmpdir / "output.tsv"
        script = tmpdir / "read.R"
        source.write_bytes(body)
        script.write_text(_R_SCRIPT, encoding="utf-8")
        proc = subprocess.run(
            ["Rscript", str(script), str(source), str(target)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise ExecutionStop(
                f"base-R readRDS parser failed: {proc.stderr.strip()[:1000]}"
            )
        frame = pd.read_csv(
            target,
            sep="\t",
            dtype=object,
            keep_default_na=True,
            na_values=["NA"],
        )
    if list(frame.columns) != list(expected_columns):
        raise ExecutionStop(
            "RDS schema mismatch: "
            f"expected={expected_columns}, observed={list(frame.columns)}"
        )
    return frame


def validate_year_period_consistency(catch: pd.DataFrame) -> None:
    rows = validate_catch_frame(catch)
    for period, expected_years in (
        ("90s", {1996, 1997}),
        ("2023", {2023}),
    ):
        years = set(
            int(value)
            for value in rows.loc[rows["period"] == period, "Year"]
        )
        if not years:
            raise ExecutionStop(f"catch frame has no rows for period {period}")
        if not years.issubset(expected_years):
            raise ExecutionStop(
                f"year-period inconsistency for {period}: {sorted(years)}"
            )


def _safe_fraction(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def execute_bridge(
    habitat_raw: pd.DataFrame,
    catch_raw: pd.DataFrame,
) -> dict[str, Any]:
    habitat = validate_habitat_frame(habitat_raw)
    catch = validate_catch_frame(catch_raw)
    validate_year_period_consistency(catch)
    joined = join_catch_to_habitat(catch, habitat)
    scaling = fit_habitat_scaling(habitat)

    species_names = calibration_species(joined)
    if not species_names:
        raise ExecutionStop("no species satisfy frozen calibration eligibility")

    species_rows = []
    contraction_fractions = []
    for species in species_names:
        result = evaluate_species(
            joined=joined,
            habitat=habitat,
            scaling=scaling,
            species=species,
        )
        calibration_count = len(result.calibration_world_ids)
        final_count = len(result.final_survivor_world_ids)
        eliminated = calibration_count - final_count
        contraction = _safe_fraction(eliminated, calibration_count)
        if contraction is not None:
            contraction_fractions.append(contraction)

        species_rows.append(
            {
                "species": result.species,
                "calibration_positive_node_count": len(
                    result.calibration_positive_nodes
                ),
                "heldout_positive_node_count": len(
                    result.heldout_positive_nodes
                ),
                "calibration_survivor_world_count": calibration_count,
                "final_survivor_world_count": final_count,
                "heldout_eliminated_world_count": eliminated,
                "heldout_contraction_fraction": contraction,
                "status": (
                    "no_heldout_positive_witness"
                    if not result.heldout_positive_nodes
                    else "heldout_falsified_all_calibration_worlds"
                    if calibration_count > 0 and final_count == 0
                    else "heldout_contracted_survivor_fiber"
                    if eliminated > 0
                    else "heldout_positive_no_contraction"
                ),
                "heldout_witness_rows": list(result.heldout_witness_rows),
            }
        )

    status_counts = dict(
        sorted(Counter(row["status"] for row in species_rows).items())
    )
    result_payload: dict[str, Any] = {
        "schema": "eog.bam_greatlakes_barrier_external_bridge.result.v1",
        "status": "completed_retrospective_external_AM_bridge",
        "scientific_role": (
            "retrospective_external_AM_subfamily_bridge_not_fresh_confirmatory_evidence"
        ),
        "eligible_species_count": len(species_rows),
        "status_counts": status_counts,
        "species_with_any_heldout_contraction": sum(
            (row["heldout_eliminated_world_count"] or 0) > 0
            for row in species_rows
        ),
        "species_with_complete_heldout_falsification": sum(
            row["status"] == "heldout_falsified_all_calibration_worlds"
            for row in species_rows
        ),
        "species_retaining_multiple_worlds_after_all_positive_evidence": sum(
            row["final_survivor_world_count"] > 1
            for row in species_rows
        ),
        "contraction_fraction_distribution": {
            "minimum": (
                None if not contraction_fractions else float(np.min(contraction_fractions))
            ),
            "median": (
                None if not contraction_fractions else float(np.median(contraction_fractions))
            ),
            "maximum": (
                None if not contraction_fractions else float(np.max(contraction_fractions))
            ),
        },
        "habitat_scaling": {
            "fields": [
                "width","max_depth","prop_clay","prop_silt","prop_sand",
                "prop_gravel","prop_boulder"
            ],
            "median": list(scaling.median),
            "iqr": list(scaling.iqr),
            "thresholds": [
                {"level": level, "distance": value}
                for level, value in scaling.thresholds
            ],
        },
        "species_results": species_rows,
        "claim_boundary": [
            "B is unrestricted; this is an empirical A/M subfamily bridge",
            "only positive records are hard ecological witnesses",
            "2023 nondetections are not interpreted as biological absence",
            "survivor contraction is not a causal barrier-effect estimate",
            "this retrospective bridge is not fresh confirmatory evidence",
        ],
    }
    result_payload["fingerprint"] = canonical_sha256(result_payload)
    return result_payload


def main() -> int:
    payload_requests = 0
    payload_bytes_opened = 0
    values_parsed = False
    try:
        gate0, gate1, contract = load_authorized_contract()
        habitat_spec = contract["frozen_files"]["habitat"]
        catch_spec = contract["frozen_files"]["catch"]

        anonymous_archive = try_anonymous_version_archive(gate0, contract)
        if anonymous_archive is not None:
            habitat_body, catch_body, archive_bytes_opened = anonymous_archive
            payload_requests += 1
            payload_bytes_opened += archive_bytes_opened
            auth_mode = "anonymous_verified_version_archive"
        else:
            token, auth_mode = verify_dryad_token()
            habitat_body = download_bound_file(habitat_spec, token)
            payload_requests += 1
            payload_bytes_opened += len(habitat_body)
            catch_body = download_bound_file(catch_spec, token)
            payload_requests += 1
            payload_bytes_opened += len(catch_body)

        habitat = rds_bytes_to_frame(
            habitat_body,
            contract["rds_parser"]["habitat_exact_columns"],
        )
        catch = rds_bytes_to_frame(
            catch_body,
            contract["rds_parser"]["catch_exact_columns"],
        )
        values_parsed = True
        result = execute_bridge(habitat, catch)
        result["gate1_fingerprint"] = gate1["fingerprint"]
        result["source_files"] = {
            "habitat_sha256": habitat_spec["sha256"],
            "catch_sha256": catch_spec["sha256"],
        }
        result["rds_payload_requests"] = payload_requests
        result["rds_payload_bytes_opened"] = payload_bytes_opened
        result["rds_values_parsed"] = values_parsed
        result["dryad_auth_mode"] = auth_mode
    except Exception as exc:
        result = {
            "schema": "eog.bam_greatlakes_barrier_external_bridge.result.v1",
            "status": "stop_before_or_during_once_only_execution",
            "reason": str(exc),
            "rds_payload_requests": payload_requests,
            "rds_payload_bytes_opened": payload_bytes_opened,
            "rds_values_parsed": values_parsed,
            "model_fits": 0,
            "retry_allowed": payload_bytes_opened == 0,
            "scientific_effect": (
                "none_pre_response_transport_stop"
                if payload_bytes_opened == 0
                else "terminal_partial_payload_stop_no_rerun"
            ),
        }

    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
