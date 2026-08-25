from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/big_thicket_replication_1/gate0_site_and_headers.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "sciencebase_metadata_requests": 0,
    "sciencebase_metadata_bytes_opened": 0,
    "site_location_payload_requests": 0,
    "site_location_payload_bytes_opened": 0,
    "sample_matrix_header_requests": 0,
    "sample_matrix_header_bytes_opened": 0,
    "sample_data_header_requests": 0,
    "sample_data_header_bytes_opened": 0,
    "biological_response_payload_requests": 0,
    "biological_response_payload_bytes_opened": 0,
    "biological_response_header_bytes_opened": 0,
    "biological_response_rows_opened": False,
    "biological_response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def item_metadata() -> dict:
    item_id = CONTRACT["official_source"]["sciencebase_item_id"]
    url = f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Big-Thicket-Gate0/1.0", "Accept": "application/json"})
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"ScienceBase metadata failed: status={status}, bytes={len(body)}")
    observed_sha = hashlib.sha256(body).hexdigest()
    expected_sha = CONTRACT["official_source"]["sciencebase_item_metadata_sha256"]
    if observed_sha != expected_sha:
        raise RuntimeError(f"ScienceBase item metadata drift: {observed_sha} != {expected_sha}")
    return json.loads(body.decode("utf-8"))


def download_url(file_row: dict) -> str:
    value = file_row.get("downloadUri") or file_row.get("url")
    if not value:
        raise RuntimeError(f"no download URI for {file_row.get('name')}")
    return str(value)


def file_map(metadata: dict) -> dict[str, dict]:
    result = {str(row.get("name") or ""): row for row in (metadata.get("files") or [])}
    for required in CONTRACT["pre_response_asset_identities"]:
        if required not in result:
            raise RuntimeError(f"frozen ScienceBase asset missing: {required}")
        frozen = CONTRACT["pre_response_asset_identities"][required]
        row = result[required]
        checksum = row.get("checksum") or {}
        if isinstance(checksum, dict):
            observed_md5 = str(checksum.get("value") or checksum.get("checksum") or "")
        else:
            observed_md5 = str(checksum)
        if observed_md5 != frozen["md5"] or int(row.get("size") or 0) != int(frozen["bytes"]):
            raise RuntimeError(f"asset identity drift for {required}")
    return result


def get_full_geometry(file_row: dict, name: str) -> tuple[list[str], list[list[str]], str]:
    frozen = CONTRACT["pre_response_asset_identities"][name]
    req = urllib.request.Request(download_url(file_row), headers={"User-Agent": "EOG-Big-Thicket-Gate0/1.0", "Accept-Encoding": "identity"})
    AUDIT["site_location_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(int(frozen["bytes"]) + 1)
        status = int(getattr(response, "status", 200))
    AUDIT["site_location_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != int(frozen["bytes"]):
        raise RuntimeError(f"{name} transport/size mismatch: status={status}, bytes={len(body)}")
    observed_md5 = hashlib.md5(body).hexdigest()
    if observed_md5 != frozen["md5"]:
        raise RuntimeError(f"{name} MD5 mismatch: {observed_md5}")
    text = body.decode("utf-8-sig")
    parsed = list(csv.reader(io.StringIO(text)))
    if not parsed or len(parsed) < 2:
        raise RuntimeError("Site Locations.csv has no data rows")
    header = parsed[0]
    rows = parsed[1:]
    if any(len(row) != len(header) for row in rows):
        raise RuntimeError("Site Locations.csv row width mismatch")
    return header, rows, observed_md5


def get_physical_header(file_row: dict, audit_prefix: str) -> dict:
    req = urllib.request.Request(download_url(file_row), headers={"User-Agent": "EOG-Big-Thicket-Gate0/1.0", "Accept-Encoding": "identity"})
    AUDIT[f"{audit_prefix}_header_requests"] += 1
    opened = bytearray()
    terminator = None
    with urllib.request.urlopen(req, timeout=60) as response:
        status = int(getattr(response, "status", 200))
        if status != 200:
            raise RuntimeError(f"{audit_prefix} header HTTP status {status}")
        while len(opened) < 4096:
            chunk = response.read(1)
            if not chunk:
                break
            opened.extend(chunk)
            if chunk == b"\r":
                terminator = "CR"
                break
            if chunk == b"\n":
                terminator = "LF"
                break
    AUDIT[f"{audit_prefix}_header_bytes_opened"] += len(opened)
    if terminator is None:
        raise RuntimeError(f"{audit_prefix} header did not terminate within 4096 bytes")
    header_bytes = bytes(opened[:-1])
    text = header_bytes.decode("utf-8-sig")
    rows = list(csv.reader([text]))
    if len(rows) != 1:
        raise RuntimeError(f"{audit_prefix} physical header parse failure")
    return {"physical_header": rows[0], "terminator": terminator, "bytes_opened": len(opened)}


def main() -> None:
    metadata = item_metadata()
    files = file_map(metadata)
    site_header, site_rows, site_md5 = get_full_geometry(files["Site Locations.csv"], "Site Locations.csv")
    matrix_header = get_physical_header(files["Sample Matrix.csv"], "sample_matrix")
    sample_data_header = get_physical_header(files["Sample Data.csv"], "sample_data")

    site_payload = {
        "header": site_header,
        "row_count": len(site_rows),
        "rows": site_rows,
        "md5": site_md5,
        "registry_row_fingerprint": canonical_sha256({"header": site_header, "rows": site_rows}),
    }
    payload = {
        "schema": "eog.big_thicket_gate0_site_and_headers.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": "site_payload_and_sampling_headers_opened_response_blind",
        "site_locations": site_payload,
        "sample_matrix": matrix_header,
        "sample_data": sample_data_header,
        "audit": dict(AUDIT),
        "biological_response_assets_still_forbidden": ["Observations.csv", "Vocalizations.csv", "BITH01.csv", "BITH07.csv", "BITH12.csv", "BITH17.csv", "BITH22.csv", "BITH27.csv", "BITH31.csv", "BITH37.csv", "BITH41.csv"],
    }
    if AUDIT["biological_response_payload_requests"] != 0 or AUDIT["biological_response_payload_bytes_opened"] != 0:
        raise RuntimeError("biological-response firewall violated")
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
