from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/louisiana_marsh_bird_replication_1/gate0_sites_samples.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "sciencebase_metadata_requests": 0,
    "sciencebase_metadata_bytes_opened": 0,
    "response_independent_payload_requests": 0,
    "response_independent_payload_bytes_opened": 0,
    "biological_response_payload_requests": 0,
    "biological_response_payload_bytes_opened": 0,
    "biological_response_header_bytes_opened": 0,
    "biological_response_rows_opened": False,
    "biological_response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def get_item() -> dict:
    item_id = CONTRACT["official_source"]["sciencebase_item_id"]
    req = urllib.request.Request(
        f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json",
        headers={"User-Agent": "EOG-Louisiana-Marsh-Bird-Gate0/1.0", "Accept": "application/json"},
    )
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"ScienceBase metadata failure: status={status}, bytes={len(body)}")
    observed = hashlib.sha256(body).hexdigest()
    expected = CONTRACT["official_source"]["sciencebase_item_metadata_sha256"]
    if observed != expected:
        raise RuntimeError(f"ScienceBase metadata changed: {observed} != {expected}")
    return json.loads(body.decode("utf-8"))


def file_map(item: dict) -> dict[str, dict]:
    files = {str(row.get("name") or ""): row for row in (item.get("files") or [])}
    frozen = {**CONTRACT["response_independent_assets"], **CONTRACT["biological_response_assets_forbidden"]}
    for name, identity in frozen.items():
        if name not in files:
            raise RuntimeError(f"frozen asset missing: {name}")
        row = files[name]
        checksum = row.get("checksum") or {}
        if isinstance(checksum, dict):
            md5 = str(checksum.get("value") or checksum.get("checksum") or "")
        else:
            md5 = str(checksum)
        if md5 != identity["md5"] or int(row.get("size") or 0) != int(identity["bytes"]):
            raise RuntimeError(f"asset identity drift: {name}")
    return files


def download_response_independent(files: dict[str, dict], name: str) -> bytes:
    frozen = CONTRACT["response_independent_assets"][name]
    url = files[name].get("downloadUri") or files[name].get("url")
    if not url:
        raise RuntimeError(f"no download URI for {name}")
    req = urllib.request.Request(str(url), headers={"User-Agent": "EOG-Louisiana-Marsh-Bird-Gate0/1.0", "Accept-Encoding": "identity"})
    AUDIT["response_independent_payload_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(int(frozen["bytes"]) + 1)
        status = int(getattr(response, "status", 200))
    AUDIT["response_independent_payload_bytes_opened"] += len(body)
    if status != 200 or len(body) != int(frozen["bytes"]):
        raise RuntimeError(f"{name} transport/size mismatch: status={status}, bytes={len(body)}")
    observed = hashlib.md5(body).hexdigest()
    if observed != frozen["md5"]:
        raise RuntimeError(f"{name} MD5 mismatch: {observed}")
    return body


def parse_table(payload: bytes, name: str) -> dict:
    text = payload.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise RuntimeError(f"{name} contains no data rows")
    header = rows[0]
    data = rows[1:]
    if not header or any(len(row) != len(header) for row in data):
        raise RuntimeError(f"{name} row-width/schema failure")
    return {
        "physical_header": header,
        "row_count": len(data),
        "rows": data,
        "table_fingerprint": canonical_sha256({"header": header, "rows": data}),
    }


def main() -> None:
    item = get_item()
    files = file_map(item)
    sites = parse_table(download_response_independent(files, "Sites.csv"), "Sites.csv")
    samples = parse_table(download_response_independent(files, "Samples.csv"), "Samples.csv")

    if sites["row_count"] != int(CONTRACT["gate0"]["required_site_row_count"]):
        raise RuntimeError(f"Sites.csv row count changed: {sites['row_count']}")
    if samples["row_count"] != int(CONTRACT["gate0"]["required_sampling_occasion_row_count"]):
        raise RuntimeError(f"Samples.csv row count changed: {samples['row_count']}")

    payload = {
        "schema": "eog.louisiana_marsh_bird_gate0_sites_samples.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": "response_blind_sites_and_sampling_payloads_pass",
        "sites": sites,
        "samples": samples,
        "audit": dict(AUDIT),
        "species_response_files_still_unopened": sorted(CONTRACT["biological_response_assets_forbidden"]),
    }
    if AUDIT["biological_response_payload_requests"] != 0 or AUDIT["biological_response_payload_bytes_opened"] != 0:
        raise RuntimeError("biological response firewall violated")
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
