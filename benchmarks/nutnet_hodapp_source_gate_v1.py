"""Metadata-only candidate gate for Hodapp et al. grassland factorial experiment.

Do not download/parse outcome CSV contents. This gate does not score any response.
Run with: python benchmarks/nutnet_hodapp_source_gate_v1.py --output report.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

DOI = "10.5061/dryad.8vs569h"
DRYAD = "https://datadryad.org"
ZENODO = "https://zenodo.org"
DATASET_API = DRYAD + "/api/v2/datasets/doi%3A10.5061%2Fdryad.8vs569h"
MIRROR_API = ZENODO + "/api/records/5023851"
EXPECTED = ("composition-data.csv", "env-param-Y0.csv")
MAX_METADATA_BYTES = 2_000_000

def get_json(url: str) -> tuple[dict | None, str]:
    """Fetch ONLY a bounded JSON manifest from an allowed metadata endpoint."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("datadryad.org", "zenodo.org"):
        return None, "STOP_UNAPPROVED_HOST"
    request = Request(url, headers={
        "User-Agent": "EOG-source-only-qualification/1.0 (research provenance)",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=15) as response:
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                return None, "STOP_NOT_JSON:" + content_type[:80]
            content = response.read(MAX_METADATA_BYTES + 1)
            if len(content) > MAX_METADATA_BYTES:
                return None, "STOP_OVERSIZE_METADATA"
            result = json.loads(content.decode("utf-8"))
            return (result, "HTTP_200_JSON") if isinstance(result, dict) else (None, "STOP_NOT_OBJECT")
    except HTTPError as e:
        return None, f"HTTP_{e.code}"
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError) as e:
        return None, "SOURCE_ACCESS_STOP:" + type(e).__name__ + ":" + str(e)[:120]

def find_files(payload: object) -> dict[str, dict]:
    """Walk metadata-only JSON; never read biological response content."""
    found: dict[str, dict] = {}
    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            name = node.get("filename", node.get("name", node.get("key", node.get("path", ""))))
            if isinstance(name, str):
                leaf = name.rsplit("/", 1)[-1]
                if leaf in EXPECTED:
                    checksum = node.get("checksum", node.get("digest", node.get("sha256", node.get("md5", ""))))
                    size = node.get("size", node.get("size_bytes", node.get("bytes", None)))
                    found[leaf] = {"name": leaf, "size": size, "checksum": checksum}
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
    walk(payload)
    return found

def dryad_version_href(dataset: dict) -> str | None:
    links = dataset.get("_links", {})
    for label in ("stash:version", "latest-version", "version"):
        node = links.get(label, {})
        if isinstance(node, dict) and isinstance(node.get("href"), str):
            return urljoin(DRYAD, node["href"])
    return None

def candidate_state(files: dict[str, dict], authoritative: bool) -> str:
    if set(files) != set(EXPECTED):
        return "SOURCE_STOP_EXPECTED_FILES_MISSING"
    if not authoritative:
        return "MIRROR_PROVENANCE_UNVERIFIED"
    for entry in files.values():
        size = entry.get("size")
        check = entry.get("checksum")
        if not (isinstance(size, int) and size > 0 and isinstance(check, str) and len(check) >= 32):
            return "SOURCE_STOP_INCOMPLETE_FILE_INTEGRITY_METADATA"
    return "SOURCE_METADATA_COMPLETE_BYTES_NOT_VERIFIED"

def run(metadata_get=get_json) -> dict:
    observations = []
    dataset, status = metadata_get(DATASET_API)
    observations.append({"endpoint": "dryad_dataset", "access_status": status})
    selected_files: dict[str, dict] = {}
    source = None
    if dataset is not None:
        direct_files = find_files(dataset)
        selected_files.update(direct_files)
        href = dryad_version_href(dataset)
        if href:
            # Dryad version listing is manifest JSON, not the raw CSV.
            if href.startswith(DRYAD + "/api/v2/"):
                payload, stat = metadata_get(href + "/files")
                observations.append({"endpoint": "dryad_version_files", "access_status": stat})
                if payload is not None:
                    selected_files.update(find_files(payload))
        source = "Dryad"
    if set(selected_files) != set(EXPECTED):
        mirror, stat = metadata_get(MIRROR_API)
        observations.append({"endpoint": "zenodo_mirror_metadata", "access_status": stat})
        if mirror is not None:
            mirror_files = find_files(mirror)
            if len(mirror_files) > len(selected_files):
                selected_files = mirror_files
                source = "Zenodo candidate; source-byte equivalence not established"
    result = {
        "schema": "eog.nutnet_hodapp_source_only_gate.result.v1",
        "source_doi": DOI,
        "phase": "SOURCE_METADATA_ONLY",
        "status": candidate_state(selected_files, source == "Dryad"),
        "catalogue": source,
        "expected_files": list(EXPECTED),
        "identified_file_metadata": selected_files,
        "source_requests": observations,
        "post_treatment_cover_rows_opened": 0,
        "actual_intervention_signs_scored": 0,
        "scientific_claim": "No BAM inference, no causal treatment direction, and no EOG-WF endpoint was evaluated.",
    }
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source_requests": result["source_requests"]}, indent=2))

if __name__ == "__main__":
    main()
