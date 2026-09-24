from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
from io import StringIO
import json
from pathlib import Path
from typing import Callable
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_screen_contract.json"
DEFAULT_OUTPUT = HERE / "prelock_screen_result.json"
USER_AGENT = "EOG-Snapshot-USA-2024-Prelock/1.0"


class PrelockScreenStop(RuntimeError):
    """Fail-closed source/metadata/safe-file qualification stop."""


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _https_url(base: str, href: str) -> str:
    url = urljoin(base, href)
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise PrelockScreenStop(f"non-HTTPS Dryad link is forbidden: {url!r}")
    return url


def _fetch(
    url: str,
    *,
    maximum_bytes: int,
    accept: str,
    opener,
    role: str,
) -> tuple[bytes, dict[str, object]]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "Accept-Encoding": "identity",
        },
    )
    try:
        response = opener.open(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise PrelockScreenStop(f"{role} returned HTTP {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise PrelockScreenStop(f"{role} transport unavailable: {exc}") from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise PrelockScreenStop(f"{role} returned HTTP {status}")
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise PrelockScreenStop(f"{role} unexpectedly applied content encoding")
        final_url = response.geturl()
        if urlparse(final_url).scheme != "https":
            raise PrelockScreenStop(f"{role} redirected outside HTTPS")
        body = response.read(maximum_bytes + 1)

    if len(body) > maximum_bytes:
        raise PrelockScreenStop(f"{role} exceeded frozen byte bound")
    return body, {
        "role": role,
        "requested_url": url,
        "final_url": final_url,
        "status": status,
        "bytes_opened": len(body),
    }


def _fetch_json(
    url: str,
    *,
    maximum_bytes: int,
    opener,
    role: str,
) -> tuple[dict[str, object], dict[str, object]]:
    body, ledger = _fetch(
        url,
        maximum_bytes=maximum_bytes,
        accept="application/json",
        opener=opener,
        role=role,
    )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrelockScreenStop(f"{role} is not UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise PrelockScreenStop(f"{role} JSON root is not an object")
    ledger["sha256"] = hashlib.sha256(body).hexdigest()
    return payload, ledger


def _one_file(files_doc: dict[str, object], path: str) -> dict[str, object]:
    embedded = files_doc.get("_embedded")
    if not isinstance(embedded, dict):
        raise PrelockScreenStop("Dryad files response lacks _embedded")
    files = embedded.get("stash:files")
    if not isinstance(files, list):
        raise PrelockScreenStop("Dryad files response lacks stash:files")
    matches = [
        row for row in files if isinstance(row, dict) and row.get("path") == path
    ]
    if len(matches) != 1:
        raise PrelockScreenStop(
            f"Dryad file {path!r} expected exactly once, observed {len(matches)}"
        )
    return dict(matches[0])


def _file_identity(row: dict[str, object]) -> dict[str, object]:
    path = str(row.get("path") or "").strip()
    digest = str(row.get("digest") or "").strip().lower()
    digest_type = str(row.get("digestType") or "").strip().lower()
    size = row.get("size")
    links = row.get("_links")
    if not path:
        raise PrelockScreenStop("Dryad file metadata has empty path")
    if digest_type not in {"sha-256", "sha256"}:
        raise PrelockScreenStop(
            f"Dryad file {path!r} lacks SHA-256 identity: {digest_type!r}"
        )
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise PrelockScreenStop(f"Dryad file {path!r} has invalid SHA-256 digest")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise PrelockScreenStop(f"Dryad file {path!r} has invalid byte size")
    if not isinstance(links, dict):
        raise PrelockScreenStop(f"Dryad file {path!r} has no links")
    download = links.get("stash:download")
    if not isinstance(download, dict) or not str(download.get("href") or "").strip():
        raise PrelockScreenStop(f"Dryad file {path!r} has no download link")
    return {
        "path": path,
        "size": size,
        "sha256": digest,
        "download_href": str(download["href"]),
        "metadata_fingerprint": canonical_sha256(
            {
                "path": path,
                "size": size,
                "sha256": digest,
                "download_href": str(download["href"]),
            }
        ),
    }


def _clean(row: dict[str, str], field: str, row_number: int) -> str:
    value = str(row.get(field) or "").strip()
    if not value:
        raise PrelockScreenStop(
            f"deployments field {field!r} is empty at row {row_number}"
        )
    return value


def _audit_deployments(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PrelockScreenStop("deployments file is not UTF-8") from exc
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise PrelockScreenStop("deployments file has no header")

    required = {
        "Project",
        "State",
        "Camera_Trap_Array",
        "Site_Name",
        "Deployment_ID",
        "Start_Date",
        "End_Date",
        "Survey_Nights",
        "Latitude",
        "Longitude",
    }
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise PrelockScreenStop(
            f"deployments file is missing required fields: {missing!r}"
        )

    rows = list(reader)
    if not rows:
        raise PrelockScreenStop("deployments file has no rows")

    deployments: list[str] = []
    nodes: list[tuple[str, str, str]] = []
    states: list[str] = []
    arrays: list[tuple[str, str]] = []
    coordinates_by_node: dict[tuple[str, str, str], set[tuple[float, float]]] = (
        defaultdict(set)
    )
    survey_nights: list[float] = []
    starts: list[str] = []
    ends: list[str] = []

    for row_number, row in enumerate(rows, start=2):
        project = _clean(row, "Project", row_number)
        state = _clean(row, "State", row_number)
        array = _clean(row, "Camera_Trap_Array", row_number)
        site = _clean(row, "Site_Name", row_number)
        deployment = _clean(row, "Deployment_ID", row_number)
        start = _clean(row, "Start_Date", row_number)
        end = _clean(row, "End_Date", row_number)
        nights_text = _clean(row, "Survey_Nights", row_number)
        lat_text = _clean(row, "Latitude", row_number)
        lon_text = _clean(row, "Longitude", row_number)

        try:
            lat = float(lat_text)
            lon = float(lon_text)
            nights = float(nights_text)
        except ValueError as exc:
            raise PrelockScreenStop(
                f"numeric deployment field failed at row {row_number}"
            ) from exc
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise PrelockScreenStop(
                f"coordinate outside geographic bounds at row {row_number}"
            )
        if nights <= 0:
            raise PrelockScreenStop(
                f"Survey_Nights must be positive at row {row_number}"
            )

        node = (project, array, site)
        deployments.append(deployment)
        nodes.append(node)
        states.append(state)
        arrays.append((project, array))
        coordinates_by_node[node].add((lat, lon))
        survey_nights.append(nights)
        starts.append(start)
        ends.append(end)

    node_counts = Counter(nodes)
    inconsistent_nodes = sorted(
        "|".join(node)
        for node, coords in coordinates_by_node.items()
        if len(coords) != 1
    )
    deployment_counts = Counter(deployments)

    return {
        "header": list(reader.fieldnames),
        "deployment_row_count": len(rows),
        "unique_deployment_id_count": len(deployment_counts),
        "duplicate_deployment_id_value_count": sum(
            count > 1 for count in deployment_counts.values()
        ),
        "unique_stable_node_count": len(node_counts),
        "repeated_stable_node_count": sum(
            count > 1 for count in node_counts.values()
        ),
        "unique_outer_state_count": len(set(states)),
        "unique_array_count": len(set(arrays)),
        "nodes_with_multiple_exact_coordinates_count": len(inconsistent_nodes),
        "nodes_with_multiple_exact_coordinates": inconsistent_nodes[:20],
        "survey_nights_min": min(survey_nights),
        "survey_nights_max": max(survey_nights),
        "deployment_start_min": min(starts),
        "deployment_start_max": max(starts),
        "deployment_end_min": min(ends),
        "deployment_end_max": max(ends),
    }


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    opener=None,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = contract["source_identity"]
    bounds = contract["metadata_bounds"]
    safe_cfg = contract["safe_file"]
    response_cfg = contract["response_file"]
    minima = contract["response_independent_architecture_minima"]

    opener = opener or urllib.request.build_opener()
    ledger: list[dict[str, object]] = []
    base = {
        "schema": "eog.snapshot_usa_2024_prelock_screen_result.v1",
        "screen_id": contract["screen_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "candidate_locked": False,
        "focal_species_selected": False,
        "response_file_requests": 0,
        "response_file_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    try:
        dataset, item = _fetch_json(
            source["api_dataset_url"],
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_dataset_metadata",
        )
        ledger.append(item)
        identifier = str(dataset.get("identifier") or "").strip().casefold()
        if identifier not in {
            f"doi:{source['doi']}".casefold(),
            str(source["doi"]).casefold(),
        }:
            raise PrelockScreenStop(
                f"Dryad dataset identifier drift: {identifier!r}"
            )
        if str(dataset.get("title") or "").strip() != source["title"]:
            raise PrelockScreenStop("Dryad dataset title drift")
        links = dataset.get("_links")
        if not isinstance(links, dict):
            raise PrelockScreenStop("Dryad dataset metadata lacks links")
        version_link = links.get("stash:version")
        if not isinstance(version_link, dict):
            raise PrelockScreenStop("Dryad dataset metadata lacks latest version link")
        version_href = str(version_link.get("href") or "").strip()
        if not version_href:
            raise PrelockScreenStop("Dryad latest version href is empty")

        version_url = _https_url("https://datadryad.org", version_href)
        version, item = _fetch_json(
            version_url,
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_latest_version_metadata",
        )
        ledger.append(item)
        version_links = version.get("_links")
        if not isinstance(version_links, dict):
            raise PrelockScreenStop("Dryad version metadata lacks links")
        files_link = version_links.get("stash:files")
        if isinstance(files_link, dict) and str(files_link.get("href") or "").strip():
            files_href = str(files_link["href"])
        else:
            files_href = version_href.rstrip("/") + "/files"
        files_url = _https_url("https://datadryad.org", files_href)
        separator = "&" if "?" in files_url else "?"
        files_url = (
            f"{files_url}{separator}per_page="
            f"{int(bounds['maximum_files_per_version'])}"
        )
        files_doc, item = _fetch_json(
            files_url,
            maximum_bytes=int(bounds["maximum_json_bytes"]),
            opener=opener,
            role="dryad_latest_version_files",
        )
        ledger.append(item)

        safe_file = _file_identity(
            _one_file(files_doc, str(safe_cfg["path"]))
        )
        response_file = _file_identity(
            _one_file(files_doc, str(response_cfg["path"]))
        )
        if safe_file["size"] > int(safe_cfg["maximum_bytes"]):
            raise PrelockScreenStop("safe deployments file exceeds frozen byte bound")

        safe_url = _https_url(
            "https://datadryad.org",
            str(safe_file["download_href"]),
        )
        safe_bytes, item = _fetch(
            safe_url,
            maximum_bytes=int(safe_cfg["maximum_bytes"]),
            accept="text/csv,*/*",
            opener=opener,
            role="dryad_safe_deployments_file",
        )
        ledger.append(item)
        if len(safe_bytes) != safe_file["size"]:
            raise PrelockScreenStop(
                "safe deployments file byte size differs from Dryad metadata"
            )
        safe_sha = hashlib.sha256(safe_bytes).hexdigest()
        if safe_sha != safe_file["sha256"]:
            raise PrelockScreenStop(
                "safe deployments file SHA-256 differs from Dryad metadata"
            )

        audit = _audit_deployments(safe_bytes)
        transport = evaluate_source_transport_qualification(
            (
                TransportRouteEvidence(
                    route_id="dryad_separate_deployments_file",
                    route_type="separate_safe_assets",
                    qualified=True,
                    safe_payload_bytes_opened=len(safe_bytes),
                    response_payload_bytes_opened=0,
                    reason=(
                        "Dryad file metadata identified separate deployment and "
                        "sequence assets; only deployments was downloaded and "
                        "verified against Dryad SHA-256"
                    ),
                    transport_detail=f"version={version_href}",
                ),
            )
        )

        closed_registry = (
            audit["nodes_with_multiple_exact_coordinates_count"] == 0
        )
        declaration = CandidatePreflightDeclaration(
            attempt_id="snapshot_usa_2024_source_architecture_prelock_v1",
            minimum_nodes=int(minima["minimum_unique_nodes"]),
            minimum_outer_units=int(minima["minimum_outer_units"]),
            minimum_repeated_nodes=int(minima["minimum_repeated_nodes"]),
            require_separate_geometry_and_response=True,
            require_coordinate_geometry=True,
            require_closed_analysis_registry=True,
            require_response_blind_transport_qualification=True,
        )
        evidence = CandidatePreflightEvidence(
            source_identity=f"Dryad:{source['doi']}",
            geometry_source_identity=(
                f"{safe_file['path']}@sha256:{safe_file['sha256']}"
            ),
            response_source_identity=(
                f"{response_file['path']}@sha256:{response_file['sha256']}"
            ),
            geometry_response_separable=True,
            coordinate_geometry_present=True,
            node_count=int(audit["unique_stable_node_count"]),
            outer_unit_count=int(audit["unique_outer_state_count"]),
            repeated_node_count=int(audit["repeated_stable_node_count"]),
            layout_design="natural_irregular",
            analysis_registry_closed=closed_registry,
            response_blind_transport_qualified=transport.ready,
            transport_qualification_fingerprint=transport.fingerprint,
            response_rows_opened=False,
            response_bytes_opened=False,
            note=(
                "source architecture only; no focal taxon selected and "
                "sequences.csv payload unopened"
            ),
        )
        preflight = evaluate_candidate_preflight(declaration, evidence)

        arrays_pass = audit["unique_array_count"] >= int(
            minima["minimum_arrays"]
        )
        survey_pass = audit["survey_nights_min"] > 0
        registry_pass = (
            closed_registry
            if bool(minima["require_all_nodes_single_coordinate_pair"])
            else True
        )
        architecture_ready = (
            preflight.ready
            and arrays_pass
            and survey_pass
            and registry_pass
        )

        result = {
            **base,
            "status": (
                "source_ready_for_focal_selection_prelock"
                if architecture_ready
                else "source_architecture_unqualified_prelock"
            ),
            "dataset_identity": {
                "identifier": dataset.get("identifier"),
                "title": dataset.get("title"),
                "version_number": dataset.get("versionNumber"),
                "version_href": version_href,
            },
            "safe_file": {
                **safe_file,
                "actual_sha256": safe_sha,
                "payload_bytes_opened": len(safe_bytes),
            },
            "response_file": {
                **response_file,
                "payload_requests": 0,
                "payload_bytes_opened": 0,
            },
            "deployment_audit": audit,
            "transport_qualification": asdict(transport),
            "candidate_preflight": asdict(preflight),
            "additional_architecture_checks": {
                "minimum_arrays": int(minima["minimum_arrays"]),
                "arrays_pass": arrays_pass,
                "require_positive_survey_nights": bool(
                    minima["require_positive_survey_nights"]
                ),
                "survey_nights_pass": survey_pass,
                "require_all_nodes_single_coordinate_pair": bool(
                    minima["require_all_nodes_single_coordinate_pair"]
                ),
                "single_coordinate_per_node_pass": registry_pass,
            },
        }
    except (
        PrelockScreenStop,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        result = {
            **base,
            "status": "source_screen_stop_prelock",
            "reason": str(exc),
        }

    result["request_ledger"] = ledger
    result["metadata_and_safe_bytes_opened"] = sum(
        int(item["bytes_opened"]) for item in ledger
    )
    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "fingerprint": result["fingerprint"],
                "response_file_payload_bytes_opened": (
                    result["response_file_payload_bytes_opened"]
                ),
            },
            sort_keys=True,
        )
    )
