from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "aland_glanville_fritillary_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
UUID = CONTRACT["source"]["dataset_uuid"]
BASE = "https://metax.fairdata.fi"
DATASET_URL = f"{BASE}/v3/datasets/{UUID}"
FILES_URL = f"{BASE}/v3/datasets/{UUID}/files"
OUT = BUILD / "gate0_metadata.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def response_firewall():
    return {
        "dataset_file_payload_requests": 0,
        "dataset_file_payload_bytes_opened": 0,
        "dataset_file_headers_opened": False,
        "dataset_file_rows_opened": False,
        "dataset_file_values_opened": False,
        "locality_visit_payload_requests": 0,
        "nest_payload_requests": 0,
        "scientific_model_fits": 0,
        "heldout_scores": 0,
    }


def base_result():
    return {
        "schema": "eog.aland_glanville_fritillary_replication_2.gate0_metadata.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "metax": {},
        "files": [],
        "roles": {},
        "response_firewall": response_firewall(),
    }


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "EOG-fresh-validation-metadata-only/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def title_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("en", "und", "fi", "sv"):
            if value.get(k):
                return str(value[k])
        return " | ".join(str(v) for v in value.values() if v)
    return ""


def extract_results(obj):
    if isinstance(obj, list):
        return obj, None
    if not isinstance(obj, dict):
        raise RuntimeError("unexpected files response type")
    for key in ("results", "files", "data"):
        if isinstance(obj.get(key), list):
            nxt = obj.get("next")
            if not nxt and isinstance(obj.get("pagination"), dict):
                nxt = obj["pagination"].get("next")
            return obj[key], nxt
    raise RuntimeError(f"files response lacks a recognized result list; keys={sorted(obj.keys())}")


def scalar_checksum(f):
    for key in ("checksum", "checksum_value", "sha256", "md5"):
        value = f.get(key)
        if isinstance(value, str) and value:
            return {"type": key, "value": value}
        if isinstance(value, dict):
            val = value.get("value") or value.get("checksum_value")
            typ = value.get("algorithm") or value.get("type") or key
            if val:
                return {"type": str(typ), "value": str(val)}
    return None


def safe_file_meta(f):
    if not isinstance(f, dict):
        raise RuntimeError("file metadata item is not an object")
    name = f.get("filename") or f.get("file_name") or f.get("name")
    path = f.get("pathname") or f.get("path") or f.get("file_path") or name
    identifier = f.get("id") or f.get("identifier") or f.get("storage_identifier")
    size = f.get("byte_size")
    if size is None:
        size = f.get("size")
    return {
        "id": None if identifier is None else str(identifier),
        "name": None if name is None else str(name),
        "path": None if path is None else str(path),
        "size": size,
        "checksum": scalar_checksum(f),
        "storage_service": f.get("storage_service"),
        "frozen": f.get("frozen"),
        "pas_compatible_file": f.get("pas_compatible_file"),
    }


def role_for(meta):
    text = " ".join(str(meta.get(k) or "") for k in ("name", "path")).lower()
    # The role is assigned only from names/paths; no file bytes are opened.
    if "patch" in text and "visit" not in text and "locality" not in text and "nest" not in text:
        return "patch"
    if ("locality" in text and "visit" in text) or "locality_visit" in text or "locality-visit" in text:
        return "locality_visit"
    if "nest" in text:
        return "nest"
    return None


def normalize_next(next_value):
    if not next_value:
        return None
    if not isinstance(next_value, str):
        raise RuntimeError("non-string pagination next link")
    parsed = urllib.parse.urlparse(next_value)
    if parsed.scheme and parsed.netloc:
        if parsed.scheme != "https" or parsed.netloc != "metax.fairdata.fi":
            raise RuntimeError("pagination escaped metax.fairdata.fi")
        url = next_value
    else:
        url = urllib.parse.urljoin(BASE, next_value)
    p = urllib.parse.urlparse(url)
    if p.path != f"/v3/datasets/{UUID}/files":
        raise RuntimeError(f"pagination escaped frozen dataset files endpoint: {p.path}")
    return url


def write_result(result):
    result["fingerprint"] = fingerprint({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = base_result()
    try:
        dataset, n_dataset, final_dataset_url = get_json(DATASET_URL)
        if urllib.parse.urlparse(final_dataset_url).path != f"/v3/datasets/{UUID}":
            raise RuntimeError("dataset metadata request redirected outside frozen endpoint")
        if not isinstance(dataset, dict):
            raise RuntimeError("dataset metadata is not an object")

        observed_id = dataset.get("id") or dataset.get("identifier")
        title = title_text(dataset.get("title"))
        fileset = dataset.get("fileset") if isinstance(dataset.get("fileset"), dict) else {}
        result["metax"] = {
            "dataset_metadata_requests": 1,
            "dataset_metadata_bytes": n_dataset,
            "observed_dataset_id": None if observed_id is None else str(observed_id),
            "observed_title": title,
            "fileset_summary": {
                "storage_service": fileset.get("storage_service"),
                "total_files_count": fileset.get("total_files_count"),
                "total_files_size": fileset.get("total_files_size"),
            },
            "file_manifest_requests": 0,
            "file_manifest_bytes": 0,
        }
        if observed_id is not None and str(observed_id) != UUID:
            raise RuntimeError(f"Metax dataset id mismatch: {observed_id} != {UUID}")
        expected_title = CONTRACT["source"]["expected_public_title"]
        if title and title.strip() != expected_title:
            raise RuntimeError(f"Metax title mismatch: {title!r} != {expected_title!r}")

        all_files = []
        url = FILES_URL
        seen_pages = set()
        while url:
            if url in seen_pages:
                raise RuntimeError("pagination loop in Metax file manifest")
            seen_pages.add(url)
            obj, n_bytes, final_url = get_json(url)
            p = urllib.parse.urlparse(final_url)
            if p.path != f"/v3/datasets/{UUID}/files":
                raise RuntimeError("file manifest request redirected outside frozen endpoint")
            result["metax"]["file_manifest_requests"] += 1
            result["metax"]["file_manifest_bytes"] += n_bytes
            items, nxt = extract_results(obj)
            all_files.extend(items)
            url = normalize_next(nxt)
            if len(seen_pages) > 1000:
                raise RuntimeError("unreasonable file-manifest pagination depth")

        safe = [safe_file_meta(f) for f in all_files]
        # We intentionally retain no download/access URL fields.
        result["files"] = safe
        result["metax"]["manifest_file_count"] = len(safe)
        result["metax"]["manifest_fingerprint"] = fingerprint(safe)

        role_map = {"patch": [], "locality_visit": [], "nest": []}
        for meta in safe:
            role = role_for(meta)
            if role:
                role_map[role].append(meta)
        result["roles"] = role_map

        missing = [r for r in ("patch", "locality_visit", "nest") if not role_map[r]]
        if missing:
            result["status"] = "stop_required_physical_roles_not_identifiable_from_metadata"
            result["reason"] = "required roles missing or not name-identifiable from metadata only: " + ", ".join(missing)
            write_result(result)
            return 0

        ids_or_paths = []
        for role in ("patch", "locality_visit", "nest"):
            if len(role_map[role]) != 1:
                result["status"] = "stop_required_role_not_unique_in_metadata"
                result["reason"] = f"role {role} has {len(role_map[role])} candidate files; no payload inspection is allowed to resolve ambiguity"
                write_result(result)
                return 0
            m = role_map[role][0]
            ids_or_paths.append((m.get("id"), m.get("path")))

        normalized = [x[0] or x[1] for x in ids_or_paths]
        if len(set(normalized)) != 3:
            result["status"] = "stop_source_not_physically_separated"
            result["reason"] = "Patch, Locality visit and Nest do not resolve to three distinct physical file identifiers/paths"
            write_result(result)
            return 0

        result["status"] = "gate0_pass_physical_roles_separated_metadata_only"
        result["reason"] = "Metax metadata alone identifies one physically distinct Patch, Locality visit and Nest file; no dataset file payload/header/row/value was opened"
        write_result(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write_result(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
