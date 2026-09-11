#!/usr/bin/env python3
"""Response-blind Stage0 for the single active Illinois coyote candidate.

Permitted: public Dryad metadata plus README/deployment/effort/site-covariate bytes.
Forbidden: any byte of Coyote_Detection_History.csv, including its header.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "build" / "layer_b_mechanism_v2" / "illinois_coyote_stage0"
OUTPUT = OUTDIR / "stage0_nonresponse.json"
BASE = "https://datadryad.org"
DOI = "doi:10.5061/dryad.p8cz8wb5w"
EXPECTED_TITLE = (
    "Camera trap detections and environmental covariates for modeling scale-dependent "
    "coyote (Canis latrans) site-use intensity across Illinois, USA (2021–2024)"
)
RESPONSE = "Coyote_Detection_History.csv"
ALLOWED = {
    "README.md",
    "Camera_Deployment_Data.csv",
    "Effort_DetVariable.csv",
    "Camera_Site_Data.csv",
}
EXPECTED_YEARS = {"2021/22", "2022/23", "2023/24"}


def _request(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "eog-qualification-v2-response-blind/1",
            "Accept": "application/json, text/plain, text/csv, */*",
            "X-API-Version": "2.1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def _json(url: str) -> dict:
    return json.loads(_request(url).decode("utf-8"))


def _absolute(href: str) -> str:
    return urllib.parse.urljoin(BASE, href)


def _sha(data: bytes, digest_type: str) -> str:
    name = digest_type.lower().replace("-", "")
    if name == "sha256":
        return hashlib.sha256(data).hexdigest()
    if name == "md5":
        return hashlib.md5(data).hexdigest()
    raise RuntimeError(f"unsupported published digest type: {digest_type!r}")


def _file_id(meta: dict) -> str:
    href = meta.get("_links", {}).get("self", {}).get("href", "")
    return href.rstrip("/").rsplit("/", 1)[-1]


def _download_allowed(meta: dict) -> tuple[bytes, str]:
    fid = _file_id(meta)
    candidates = []
    href = meta.get("_links", {}).get("stash:download", {}).get("href")
    if href:
        candidates.append(_absolute(href))
    if fid:
        candidates.extend(
            [
                f"{BASE}/api/v2/files/{fid}/download",
                f"{BASE}/downloads/file_stream/{fid}",
                f"{BASE}/stash/downloads/file_stream/{fid}",
            ]
        )
    errors = []
    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        try:
            return _request(url), url
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(f"no individual-file transport succeeded: {errors}")


def _files_for_latest_version(dataset: dict) -> tuple[str, list[dict]]:
    href = dataset.get("_links", {}).get("stash:version", {}).get("href")
    if not href:
        encoded = urllib.parse.quote(DOI, safe="")
        versions = _json(f"{BASE}/api/v2/datasets/{encoded}/versions?per_page=100")
        entries = versions.get("_embedded", {}).get("stash:versions", [])
        if not entries:
            raise RuntimeError("Dryad exposed no public dataset version")
        entries = sorted(entries, key=lambda x: int(x.get("versionNumber", 0)))
        href = entries[-1].get("_links", {}).get("self", {}).get("href")
    if not href:
        raise RuntimeError("could not resolve latest public Dryad version href")
    files = _json(f"{_absolute(href)}/files?per_page=100")
    entries = files.get("_embedded", {}).get("stash:files", [])
    if files.get("total") is not None and int(files["total"]) != len(entries):
        raise RuntimeError("Dryad file listing was paginated/truncated unexpectedly")
    return href, entries


def _decode(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8 text") from exc


def _rows(data: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    text = _decode(data, label)
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise RuntimeError(f"{label} has no CSV header")
    rows = list(reader)
    return list(reader.fieldnames), rows


def _site_key(header: list[str]) -> str:
    documented = [x for x in ("Site_ID", "Site.ID") if x in header]
    if len(documented) != 1:
        raise RuntimeError(f"expected one documented site identifier, found {documented}")
    return documented[0]


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "eog.layer_b_mechanism_v2.illinois_coyote_stage0_nonresponse.v1",
        "candidate": "illinois_coyote_2021_2024",
        "response_file": RESPONSE,
        "response_metadata_read": False,
        "response_payload_requests": 0,
        "response_header_bytes_opened": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "inner_selection_decisions": 0,
        "heldout_scores": 0,
        "response_open_authorized": False,
        "allowed_files": {},
    }
    try:
        encoded = urllib.parse.quote(DOI, safe="")
        dataset = _json(f"{BASE}/api/v2/datasets/{encoded}")
        if dataset.get("title") != EXPECTED_TITLE:
            raise RuntimeError(f"unexpected Dryad dataset title: {dataset.get('title')!r}")
        result["dataset_identity"] = {
            "doi": DOI,
            "title": dataset.get("title"),
            "publicationDate": dataset.get("publicationDate"),
            "versionNumber": dataset.get("versionNumber"),
            "storageSize": dataset.get("storageSize"),
        }
        version_href, file_entries = _files_for_latest_version(dataset)
        result["dryad_version_href"] = version_href
        by_path = {str(entry.get("path")): entry for entry in file_entries}
        missing = sorted((ALLOWED | {RESPONSE}) - set(by_path))
        if missing:
            raise RuntimeError(f"required Dryad filenames missing: {missing}")

        response_meta = by_path[RESPONSE]
        if not response_meta.get("digest") or not response_meta.get("digestType"):
            raise RuntimeError("response file lacks immutable Dryad digest metadata")
        result["response_metadata_read"] = True
        result["response_identity"] = {
            "path": RESPONSE,
            "file_id": _file_id(response_meta),
            "size": response_meta.get("size"),
            "mimeType": response_meta.get("mimeType"),
            "digest": response_meta.get("digest"),
            "digestType": response_meta.get("digestType"),
        }

        payloads: dict[str, bytes] = {}
        for filename in sorted(ALLOWED):
            meta = by_path[filename]
            published_digest = str(meta.get("digest") or "")
            digest_type = str(meta.get("digestType") or "")
            if not published_digest or not digest_type:
                raise RuntimeError(f"{filename} lacks published digest metadata")
            data, source_url = _download_allowed(meta)
            observed = _sha(data, digest_type)
            if observed.lower() != published_digest.lower():
                raise RuntimeError(
                    f"digest mismatch for {filename}: expected {published_digest}, got {observed}"
                )
            payloads[filename] = data
            result["allowed_files"][filename] = {
                "file_id": _file_id(meta),
                "size": len(data),
                "published_digest": published_digest,
                "digestType": digest_type,
                "observed_digest": observed,
                "checksum_match": True,
                "source_url": source_url,
            }

        readme = _decode(payloads["README.md"], "README.md")
        required_readme_facts = {
            "response_filename": RESPONSE,
            "weekly_response_columns": "o1-o28",
            "inactive_semantics": "N/A",
            "common_site_identifier": "Site_ID",
            "weekly_effort_columns": "week.1-week.28",
        }
        readme_checks = {
            "response_filename": RESPONSE in readme,
            "weekly_response_columns": "o1-o28" in readme,
            "inactive_semantics": "N/A" in readme and "not active" in readme,
            "common_site_identifier": "Site_ID" in readme,
            "weekly_effort_columns": "week.1-week.28" in readme,
        }
        if not all(readme_checks.values()):
            raise RuntimeError(f"README response semantics incomplete: {readme_checks}")
        result["readme_semantics"] = {
            "required_facts": required_readme_facts,
            "checks": readme_checks,
        }

        dep_header, dep_rows = _rows(payloads["Camera_Deployment_Data.csv"], "Camera_Deployment_Data.csv")
        dep_site = _site_key(dep_header)
        required_dep = {dep_site, "Study.Year", "Latitude", "Longitude"}
        if not required_dep.issubset(dep_header):
            raise RuntimeError(f"deployment header missing required fields: {sorted(required_dep - set(dep_header))}")
        site_year: dict[str, str] = {}
        coordinates: dict[str, tuple[float, float]] = {}
        year_counts = Counter()
        for row in dep_rows:
            sid = row[dep_site].strip()
            year = row["Study.Year"].strip()
            if not sid or not year:
                raise RuntimeError("blank site/year in deployment table")
            try:
                lat, lon = float(row["Latitude"]), float(row["Longitude"])
            except Exception as exc:
                raise RuntimeError(f"invalid coordinates for {sid}") from exc
            if not math.isfinite(lat) or not math.isfinite(lon):
                raise RuntimeError(f"non-finite coordinates for {sid}")
            if sid in site_year and site_year[sid] != year:
                raise RuntimeError(f"site {sid} maps to multiple study years")
            if sid in coordinates and coordinates[sid] != (lat, lon):
                raise RuntimeError(f"site {sid} maps to multiple coordinate pairs")
            site_year[sid] = year
            coordinates[sid] = (lat, lon)
            year_counts[year] += 1
        if len(coordinates) < 50:
            raise RuntimeError(f"only {len(coordinates)} unique deployment sites")
        if set(year_counts) != EXPECTED_YEARS:
            raise RuntimeError(f"unexpected Study.Year values: {dict(year_counts)}")

        effort_header, effort_rows = _rows(payloads["Effort_DetVariable.csv"], "Effort_DetVariable.csv")
        effort_site = _site_key(effort_header)
        weeks = [f"week.{i}" for i in range(1, 29)]
        if any(w not in effort_header for w in weeks):
            raise RuntimeError("effort table does not expose exact week.1-week.28 columns")
        effort_by_year = {year: {"active_site_weeks": 0, "active_camera_days": 0.0, "sites": set()} for year in EXPECTED_YEARS}
        for row in effort_rows:
            sid = row[effort_site].strip()
            if sid not in site_year:
                raise RuntimeError(f"effort site {sid!r} absent from deployment registry")
            year = site_year[sid]
            for week in weeks:
                raw = row.get(week, "").strip()
                if raw == "" or raw.upper() in {"NA", "N/A", "NAN"}:
                    continue
                value = float(raw)
                if value > 0:
                    effort_by_year[year]["active_site_weeks"] += 1
                    effort_by_year[year]["active_camera_days"] += value
                    effort_by_year[year]["sites"].add(sid)
        effort_summary = {}
        for year, d in sorted(effort_by_year.items()):
            effort_summary[year] = {
                "active_site_weeks": d["active_site_weeks"],
                "active_camera_days": d["active_camera_days"],
                "sites_with_positive_effort": len(d["sites"]),
            }
            if d["active_site_weeks"] < 60 or len(d["sites"]) < 20:
                raise RuntimeError(f"insufficient response-independent effort support in {year}: {effort_summary[year]}")

        result["deployment"] = {
            "exact_header": dep_header,
            "site_identifier": dep_site,
            "row_count": len(dep_rows),
            "unique_sites": len(coordinates),
            "unique_coordinate_pairs": len(set(coordinates.values())),
            "study_year_counts": dict(sorted(year_counts.items())),
        }
        result["effort"] = {
            "exact_header": effort_header,
            "site_identifier": effort_site,
            "row_count": len(effort_rows),
            "by_study_year": effort_summary,
        }
        if len(set(coordinates.values())) < 50:
            raise RuntimeError("fewer than 50 unique coordinate pairs after deployment parsing")

        result["status"] = "stage0_nonresponse_qualified_pending_independent_both_class_gate"
        result["source_identity_gate"] = "pass"
        result["geometry_and_effort_gate"] = "pass"
        result["response_semantics_gate"] = "partial_pass_README_semantics_frozen_response_payload_unopened"
        result["target_estimability_gate"] = "not_yet_passed_partition_level_both_class_evidence_required"
        result["response_open_authorized"] = False
        result["next_gate"] = "independent_partition_level_both_class_estimability_certificate"
        rc = 0
    except Exception as exc:
        result["status"] = "terminal_pre_response_stage0_nonresponse_stop"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["response_open_authorized"] = False
        rc = 2

    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
