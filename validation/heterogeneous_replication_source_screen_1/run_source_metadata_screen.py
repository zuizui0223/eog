from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_screen_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/heterogeneous_replication_source_screen_1/source_metadata_screen.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "metadata_requests": 0,
    "metadata_bytes_opened": 0,
    "candidate_file_payload_requests": 0,
    "candidate_file_payload_bytes_opened": 0,
    "response_header_bytes_opened": 0,
    "response_rows_opened": False,
    "response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def get_json(url: str) -> tuple[dict, str]:
    AUDIT["metadata_requests"] += 1
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-heterogeneous-replication-metadata-screen/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"metadata request failed: status={status}, bytes={len(body)}, url={url}")
    return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()


def file_metadata(row: dict, item_id: str) -> dict:
    checksum = row.get("checksum")
    if isinstance(checksum, dict):
        checksum_value = checksum.get("value") or checksum.get("checksum")
        checksum_type = checksum.get("type") or checksum.get("algorithm")
    else:
        checksum_value = checksum
        checksum_type = None
    return {
        "item_id": item_id,
        "name": row.get("name") or row.get("title"),
        "size": row.get("size"),
        "content_type": row.get("contentType") or row.get("content_type"),
        "checksum": checksum_value,
        "checksum_type": checksum_type,
        "has_download_uri": bool(row.get("downloadUri") or row.get("url")),
        "original_metadata": bool(row.get("originalMetadata")),
    }


def item_summary(item: dict) -> dict:
    item_id = str(item.get("id") or "")
    return {
        "id": item_id,
        "title": item.get("title"),
        "body": item.get("body"),
        "files": [file_metadata(row, item_id) for row in (item.get("files") or [])],
    }


def main() -> None:
    results = []
    item_template = CONTRACT["metadata_access"]["allowed_item_url_template"]
    child_template = CONTRACT["metadata_access"]["allowed_children_url_template"]

    for candidate in CONTRACT["candidates"]:
        item_id = candidate["sciencebase_item_id"]
        item_url = item_template.format(item_id=item_id)
        children_url = child_template.format(item_id=item_id)
        item, item_sha = get_json(item_url)
        children_payload, children_sha = get_json(children_url)
        children = children_payload.get("items") or []
        summaries = [item_summary(item)] + [item_summary(child) for child in children]
        files = [file for summary in summaries for file in summary["files"]]
        names = [str(file.get("name") or "") for file in files]
        extensions = [name.rsplit(".", 1)[-1].lower() if "." in name else "" for name in names]
        mixed_archive_only = bool(files) and all(ext in {"zip", "tar", "gz", "tgz", "7z"} for ext in extensions)
        results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "official_doi": candidate["official_doi"],
                "sciencebase_item_id": item_id,
                "top_item_metadata_sha256": item_sha,
                "children_metadata_sha256": children_sha,
                "top_item_title": item.get("title"),
                "direct_child_count": len(children),
                "file_object_count": len(files),
                "file_names": names,
                "mixed_archive_only": mixed_archive_only,
                "items": summaries,
            }
        )

    payload = {
        "schema": "eog.heterogeneous_replication_source_metadata_screen.v1",
        "screen_id": CONTRACT["screen_id"],
        "status": "metadata_inventory_complete",
        "candidates": results,
        "audit": dict(AUDIT),
        "selection_not_yet_scored": True,
    }
    if AUDIT["candidate_file_payload_requests"] != 0 or AUDIT["candidate_file_payload_bytes_opened"] != 0:
        raise RuntimeError("candidate file payload firewall violated")
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
