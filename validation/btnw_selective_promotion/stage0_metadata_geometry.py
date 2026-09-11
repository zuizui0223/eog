#!/usr/bin/env python3
"""Response-blind Stage0 for the BTNW fresh selective-promotion candidate.

Authorized live access:
- one Dryad dataset metadata GET;
- one Dryad current-version file-manifest metadata GET;
- one immutable author GitHub README blob GET;
- one immutable author GitHub geometry blob GET.

The Dryad response file payload (model_data.rds) is never requested, previewed,
range-read, or HEADed. This stage cannot fit models, select an arm, or score
heldout outcomes.
"""
from __future__ import annotations

import base64
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "validation/btnw_selective_promotion/source_contract_v1.json"
OUTPUT = ROOT / "build/btnw_selective_promotion/stage0_metadata_geometry.json"
DRYAD_BASE = "https://datadryad.org"
DRYAD_API_VERSION = "2.1.0"
UA = "eog-btnw-response-blind-stage0/1.0"


class Stage0Stop(RuntimeError):
    pass


def _json_get(url: str) -> dict:
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json", "X-API-Version": DRYAD_API_VERSION})
    with urlopen(req, timeout=60) as r:  # noqa: S310 - frozen public metadata URL
        status = int(getattr(r, "status", 200))
        raw = r.read()
    if status != 200:
        raise Stage0Stop(f"HTTP status {status} for metadata GET")
    try:
        obj = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise Stage0Stop(f"metadata JSON decode failed: {type(exc).__name__}") from exc
    if not isinstance(obj, dict):
        raise Stage0Stop("metadata response is not a JSON object")
    return obj


def _github_blob(repo: str, blob_sha: str) -> bytes:
    url = f"https://api.github.com/repos/{repo}/git/blobs/{blob_sha}"
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=60) as r:  # noqa: S310 - frozen public git blob
        status = int(getattr(r, "status", 200))
        raw = r.read()
    if status != 200:
        raise Stage0Stop(f"GitHub blob HTTP status {status}")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise Stage0Stop(f"GitHub blob JSON decode failed: {type(exc).__name__}") from exc
    if obj.get("sha") != blob_sha:
        raise Stage0Stop("GitHub blob identity mismatch")
    if obj.get("encoding") != "base64":
        raise Stage0Stop("GitHub blob encoding is not base64")
    try:
        return base64.b64decode(obj["content"], validate=False)
    except Exception as exc:
        raise Stage0Stop(f"GitHub blob base64 decode failed: {type(exc).__name__}") from exc


def _version_href(dataset: dict) -> str:
    links = dataset.get("_links")
    if not isinstance(links, dict):
        raise Stage0Stop("Dryad dataset metadata lacks _links")
    v = links.get("stash:version")
    if not isinstance(v, dict) or not isinstance(v.get("href"), str) or not v["href"]:
        raise Stage0Stop("Dryad dataset metadata lacks stash:version href")
    href = v["href"]
    if not href.startswith("/api/v2/versions/"):
        raise Stage0Stop("Dryad current-version href has unexpected form")
    return href


def _iter_dicts(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _iter_dicts(v)
    elif isinstance(x, list):
        for v in x:
            yield from _iter_dicts(v)


def _find_response_file(manifest: dict, expected_name: str) -> dict:
    matches = []
    seen = set()
    for d in _iter_dicts(manifest):
        path = d.get("path")
        if not isinstance(path, str) or Path(path).name != expected_name:
            continue
        if not any(k in d for k in ("id", "size", "digest", "digestType", "mimeType")):
            continue
        canonical = json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)
        if canonical in seen:
            continue
        seen.add(canonical)
        matches.append(d)
    if len(matches) != 1:
        raise Stage0Stop(f"expected exactly one {expected_name} metadata object, found {len(matches)}")
    f = matches[0]
    file_id = f.get("id")
    if file_id in (None, ""):
        raise Stage0Stop("response file metadata lacks id")
    digest = f.get("digest")
    digest_type = f.get("digestType")
    if not isinstance(digest, str) or not digest.strip():
        raise Stage0Stop("published response file metadata lacks digest")
    if not isinstance(digest_type, str) or not digest_type.strip():
        raise Stage0Stop("published response file metadata lacks digestType")
    try:
        size_int = int(f.get("size"))
    except Exception as exc:
        raise Stage0Stop("response file metadata size is not integer-like") from exc
    if size_int <= 0:
        raise Stage0Stop("response file metadata size is nonpositive")
    return {"id": file_id, "path": path, "size": size_int, "digest": digest.strip(), "digestType": digest_type.strip(), "mimeType": f.get("mimeType")}


def _linear_quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise Stage0Stop("empty distance pool")
    if not (0.0 <= q <= 1.0):
        raise Stage0Stop("invalid quantile")
    h = (len(sorted_values) - 1) * q
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return float(sorted_values[lo])
    frac = h - lo
    return float(sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo]))


def _haversine(lat1, lon1, lat2, lon2, radius):
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    return 2.0 * radius * math.asin(math.sqrt(a))


def _parse_geometry(raw: bytes, c: dict) -> tuple[list[dict], list[float]]:
    try:
        text = raw.decode("utf-8-sig")
    except Exception as exc:
        raise Stage0Stop(f"geometry UTF-8 decode failed: {type(exc).__name__}") from exc
    rdr = csv.DictReader(io.StringIO(text))
    exact = c["independent_documentation"]["geometry_columns_exact"]
    required = [exact["site_id"], exact["longitude"], exact["latitude"]]
    if rdr.fieldnames is None or any(x not in rdr.fieldnames for x in required):
        raise Stage0Stop(f"geometry exact columns missing; required={required}, found={rdr.fieldnames}")
    rows = []
    seen = set()
    for row in rdr:
        site = str(row[exact["site_id"]]).strip()
        if not site or site in seen:
            raise Stage0Stop("geometry site IDs are missing or duplicated")
        try:
            lon = float(row[exact["longitude"]])
            lat = float(row[exact["latitude"]])
        except Exception as exc:
            raise Stage0Stop("geometry coordinate parse failed") from exc
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise Stage0Stop("geometry contains nonfinite coordinates")
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise Stage0Stop("geometry coordinate out of range")
        seen.add(site)
        rows.append({"site_id": site, "longitude": lon, "latitude": lat})
    expected_n = int(c["response_semantics_frozen_from_independent_documentation"]["survey_sites"])
    if len(rows) != expected_n:
        raise Stage0Stop(f"geometry row/site denominator drift: {len(rows)} != {expected_n}")
    radius = float(c["geometry_world_rule"]["earth_radius_km"])
    distances = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            d = _haversine(rows[i]["latitude"], rows[i]["longitude"], rows[j]["latitude"], rows[j]["longitude"], radius)
            if math.isfinite(d) and d > 0.0:
                distances.append(d)
    distances.sort()
    qs = [float(x) for x in c["geometry_world_rule"]["local_quantiles"]]
    thresholds = [_linear_quantile(distances, q) for q in qs]
    if any((not math.isfinite(x) or x <= 0) for x in thresholds):
        raise Stage0Stop("distance thresholds are not positive finite")
    if any(not (a < b) for a, b in zip(thresholds, thresholds[1:])):
        raise Stage0Stop("distance thresholds are not strictly increasing")
    return rows, thresholds


def _verify_readme(raw: bytes) -> dict:
    try:
        text = raw.decode("utf-8-sig")
    except Exception as exc:
        raise Stage0Stop(f"README UTF-8 decode failed: {type(exc).__name__}") from exc
    needles = ("114", "25", "4", "model_data.rds", "thinnedpoints.csv")
    missing = [x for x in needles if x not in text]
    if missing:
        raise Stage0Stop(f"pinned README lacks frozen documentation tokens: {missing}")
    return {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "tokens_verified": list(needles)}


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.btnw_selective_promotion.stage0_metadata_geometry.v1",
        "attempt_id": c["attempt_id"],
        "source_contract_blob_sha256": sha256(CONTRACT.read_bytes()).hexdigest(),
        "status": "stop_pre_response_metadata_identity_transport_or_geometry",
        "response_payload_requests": 0,
        "response_payload_bytes": 0,
        "response_header_bytes": 0,
        "response_rows": 0,
        "response_values_opened": false,
        "model_fits": 0,
        "selector_decisions": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": false,
        "counts_as_empirical_conclusion": false,
        "changes_closed_eog_wf": false
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        if c.get("response_opening_authorized_by_this_contract") is not False:
            raise Stage0Stop("source contract unexpectedly authorizes response opening")
        access = c["stage0_authorized_access_only"]
        for key in ("dryad_response_file_payload_gets", "dryad_response_file_payload_bytes", "response_headers_rows_values", "model_fits", "selector_decisions", "heldout_scores"):
            if int(access[key]) != 0:
                raise Stage0Stop("source contract response firewall drifted")
        doi = c["published_dataset"]["dryad_doi"]
        encoded = quote("doi:" + doi, safe="")
        dataset = _json_get(f"{DRYAD_BASE}/api/v2/datasets/{encoded}")
        if str(dataset.get("identifier", "")).lower() != ("doi:" + doi).lower():
            raise Stage0Stop("Dryad dataset identifier mismatch")
        href = _version_href(dataset)
        version_id = href.rstrip("/").split("/")[-1]
        if not version_id.isdigit():
            raise Stage0Stop("Dryad version id is not numeric")
        manifest = _json_get(f"{DRYAD_BASE}{href}/files?per_page=100")
        response_meta = _find_response_file(manifest, c["published_dataset"]["response_file_name"])
        doc = c["independent_documentation"]
        repo = doc["author_repository"]
        readme_raw = _github_blob(repo, doc["author_readme_blob_sha"])
        readme_audit = _verify_readme(readme_raw)
        geom_raw = _github_blob(repo, doc["geometry_blob_sha"])
        if len(geom_raw) != int(doc["geometry_file_size_bytes"]):
            raise Stage0Stop("geometry blob size differs from frozen source contract")
        rows, thresholds = _parse_geometry(geom_raw, c)
        base.update({
            "status": "stage0_source_geometry_qualified_class_support_pending",
            "dryad": {
                "dataset_identifier": dataset.get("identifier"),
                "dataset_id": dataset.get("id"),
                "version_href": href,
                "version_id": int(version_id),
                "version_number": dataset.get("versionNumber"),
                "version_status": dataset.get("versionStatus"),
                "response_file_metadata": response_meta,
                "dataset_metadata_gets": 1,
                "version_metadata_gets": 0,
                "file_manifest_metadata_gets": 1
            },
            "author_repository": {
                "repository": repo,
                "commit": doc["author_repository_commit"],
                "readme_blob_sha": doc["author_readme_blob_sha"],
                "readme_audit": readme_audit,
                "geometry_blob_sha": doc["geometry_blob_sha"],
                "geometry_sha256": sha256(geom_raw).hexdigest(),
                "geometry_bytes": len(geom_raw),
                "unique_valid_sites": len(rows),
                "github_blob_gets": 2
            },
            "geometry": {
                "distance": c["geometry_world_rule"]["distance"],
                "pairwise_nonzero_distance_count": len(rows) * (len(rows) - 1) // 2,
                "quantiles": c["geometry_world_rule"]["local_quantiles"],
                "quantile_method": c["geometry_world_rule"]["quantile_method"],
                "local_thresholds_km": thresholds,
                "world_ids": c["geometry_world_rule"]["world_ids"]
            },
            "next_gate": "separate_pre_response_class_support_audit",
            "final_response_opening_authorized": false
        })
    except Exception as exc:
        base["stop_reason"] = f"{type(exc).__name__}:{exc}"
    OUTPUT.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(base, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
