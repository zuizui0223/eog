"""Response-blind Figshare metadata inventory for the fresh RMAP attempt.

This stage may read one bounded, versioned article-metadata JSON document.  It
deliberately does not dereference any file ``download_url`` returned by Figshare.
The output is identity evidence for deciding whether later file roles can be
frozen without opening a mixed response archive.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path("build/rmap_paired_complementarity/metadata")
API_ROOT = "https://api.figshare.com/v2"
USER_AGENT = "EOG-RMAP-response-blind-metadata-preflight/1.0"
MAX_METADATA_BYTES = 2_000_000


def _bounded_json_get(url: str, audit: dict) -> dict:
    audit["metadata_request_urls"].append(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read(MAX_METADATA_BYTES + 1)
        status = getattr(response, "status", None) or response.getcode()
        content_type = response.headers.get("Content-Type", "")
    if status != 200:
        raise RuntimeError(f"Figshare metadata returned HTTP {status}: {url}")
    if len(payload) > MAX_METADATA_BYTES:
        raise RuntimeError(
            f"Figshare metadata exceeded bounded cap of {MAX_METADATA_BYTES} bytes"
        )
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Figshare metadata was not valid UTF-8 JSON ({content_type!r})"
        ) from exc
    if not isinstance(value, dict):
        raise RuntimeError("Figshare article metadata root must be an object")
    audit["metadata_response_bytes"] = len(payload)
    audit["metadata_content_type"] = content_type
    return value


def _normalise_doi(value: object) -> str:
    text = str(value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.casefold().startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.casefold()


def _file_identity(row: object) -> dict:
    if not isinstance(row, dict):
        raise RuntimeError("Figshare files inventory contains a non-object row")
    file_id = row.get("id")
    name = row.get("name")
    size = row.get("size")
    if isinstance(file_id, bool) or not isinstance(file_id, int) or file_id <= 0:
        raise RuntimeError(f"Figshare file has invalid ID: {file_id!r}")
    if not isinstance(name, str) or not name.strip():
        raise RuntimeError(f"Figshare file {file_id} has no non-empty name")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise RuntimeError(f"Figshare file {file_id} has invalid size: {size!r}")
    download_url = row.get("download_url")
    if not isinstance(download_url, str) or not download_url.startswith("https://"):
        raise RuntimeError(f"Figshare file {file_id} has no HTTPS download URL identity")
    return {
        "id": file_id,
        "name": name.strip(),
        "size": size,
        "is_link_only": row.get("is_link_only"),
        "supplied_md5": row.get("supplied_md5"),
        "computed_md5": row.get("computed_md5"),
        "download_url": download_url,
    }


def run(output: Path) -> dict:
    contract = json.loads((ROOT / "source_contract.json").read_text(encoding="utf-8"))
    source = contract["source"]
    article_id = int(source["article_id"])
    version = int(source["article_version"])
    url = f"{API_ROOT}/articles/{article_id}/versions/{version}"
    output.mkdir(parents=True, exist_ok=True)

    audit = {
        "attempt_id": contract["attempt_id"],
        "stage": "response_blind_figshare_metadata_inventory",
        "metadata_request_urls": [],
        "metadata_response_bytes": 0,
        "file_download_requests": [],
        "file_payload_bytes_opened": 0,
        "archive_member_bytes_opened": 0,
        "response_rows_opened": False,
        "response_file_ids": [],
        "response_file_ids_status": "unresolved_all_file_payload_access_forbidden",
    }
    try:
        article = _bounded_json_get(url, audit)
        observed = {
            "id": article.get("id"),
            "title": article.get("title"),
            "doi": article.get("doi"),
            "version": article.get("version"),
            "published_date": article.get("published_date"),
            "modified_date": article.get("modified_date"),
        }
        identity_checks = {
            "article_id_matches": observed["id"] == article_id,
            "version_matches": observed["version"] == version,
            "doi_matches": _normalise_doi(observed["doi"])
            == _normalise_doi(source["versioned_doi"]),
            "title_matches": observed["title"] == source["expected_title"],
        }
        if not all(identity_checks.values()):
            raise RuntimeError(
                "Figshare article identity drift: "
                + json.dumps(identity_checks, sort_keys=True)
            )

        raw_files = article.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise RuntimeError("exact Figshare article version exposes no top-level files")
        files = sorted((_file_identity(row) for row in raw_files), key=lambda row: row["id"])
        if len({row["id"] for row in files}) != len(files):
            raise RuntimeError("Figshare file IDs are not unique")
        if len({row["name"] for row in files}) != len(files):
            raise RuntimeError("Figshare top-level file names are not unique")

        audit.update(
            {
                "status": "metadata_inventory_pass",
                "article": observed,
                "identity_checks": identity_checks,
                "files": files,
                "file_count": len(files),
                "declared_file_bytes": sum(row["size"] for row in files),
                "next": contract["next_gate_if_metadata_inventory_passes"],
            }
        )
    except Exception as exc:
        audit.update(
            {
                "status": "metadata_inventory_stop",
                "stop_reason": repr(exc),
            }
        )
        (output / "metadata_inventory.json").write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    if audit["file_download_requests"]:
        raise AssertionError("metadata stage attempted a file download")
    if audit["file_payload_bytes_opened"] != 0:
        raise AssertionError("metadata stage opened file payload bytes")
    if audit["response_rows_opened"] is not False:
        raise AssertionError("metadata stage opened response rows")

    (output / "metadata_inventory.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return audit


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    try:
        result = run(output)
    except (OSError, RuntimeError, ValueError, KeyError, urllib.error.URLError) as exc:
        print(f"RMAP metadata inventory stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "article": result["article"],
                "files": [
                    {"id": row["id"], "name": row["name"], "size": row["size"]}
                    for row in result["files"]
                ],
                "file_download_requests": [],
                "file_payload_bytes_opened": 0,
                "response_rows_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
