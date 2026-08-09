"""Freeze the published Dryad file inventory for the Tanzania benchmark.

Dryad currently blocks anonymous binary downloads from hosted CI runners. This
module therefore freezes public API metadata only. It does not claim to have
retrieved file bytes, inspect table schema, or compute any EOG outcome.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.parse
import urllib.request

DOI = "10.5061/dryad.p042h0c"
DRYAD_ROOT = "https://datadryad.org"
API_ROOT = f"{DRYAD_ROOT}/api/v2"
EXPECTED_FILES = {
    "0_usambara.R", "1_sites.R", "2_isolation_occurrence",
    "Nodes_E.csv", "Nodes_W.csv", "raster_east3.tif", "raster_west3.tif",
    "Sites.csv", "spp_occur.csv",
}


def _absolute(url: str) -> str:
    return urllib.parse.urljoin(DRYAD_ROOT + "/", url)


def _json(url: str) -> dict[str, object]:
    absolute = _absolute(url)
    request = urllib.request.Request(
        absolute,
        headers={"User-Agent": "eog-nonisland-freeze/0.1", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object from {absolute}")
    return value


def _link(obj: dict[str, object], *names: str) -> str | None:
    links = obj.get("_links")
    if not isinstance(links, dict):
        return None
    for name in names:
        value = links.get(name)
        if isinstance(value, dict) and value.get("href"):
            return _absolute(str(value["href"]))
    return None


def _embedded_files(payload: dict[str, object]) -> list[dict[str, object]]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        return []
    for key in ("stash:files", "files"):
        rows = embedded.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _file_pages(url: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    while url and url not in seen:
        url = _absolute(url)
        seen.add(url)
        payload = _json(url)
        rows.extend(_embedded_files(payload))
        url = _link(payload, "next") or ""
    return rows


def freeze(output_dir: Path, doi: str = DOI) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    encoded = urllib.parse.quote(f"doi:{doi}", safe="")
    dataset_url = f"{API_ROOT}/datasets/{encoded}"
    dataset = _json(dataset_url)
    version_url = _link(dataset, "stash:version", "version")
    version = _json(version_url) if version_url else dataset
    files_url = _link(version, "stash:files", "files") or _link(dataset, "stash:files", "files")
    if not files_url:
        raise ValueError("Dryad API response did not expose a files endpoint")
    rows = _file_pages(files_url)
    if not rows:
        raise ValueError("Dryad files endpoint returned no files")

    files: list[dict[str, object]] = []
    for row in rows:
        name = str(row.get("path") or row.get("fileName") or row.get("name") or "").strip()
        if not name:
            raise ValueError(f"malformed Dryad file record: {row}")
        files.append({
            "name": Path(name).name,
            "declared_size": int(row.get("size") or 0),
            "declared_digest": row.get("digest"),
            "declared_digest_type": row.get("digestType"),
            "mime_type": row.get("mimeType"),
            "api_self": _link(row, "self"),
            "api_download": _link(row, "stash:download", "download"),
        })

    names = {str(row["name"]) for row in files}
    missing = sorted(EXPECTED_FILES - names)
    extras = sorted(names - EXPECTED_FILES)
    if missing:
        raise ValueError(f"Dryad API inventory is missing expected files: {missing}")
    if any(int(row["declared_size"]) <= 0 for row in files):
        raise ValueError("Dryad API inventory contains a non-positive declared file size")
    if any(not row["declared_digest"] for row in files):
        raise ValueError("Dryad API inventory contains a file without a declared digest")

    manifest = {
        "status": "public_metadata_frozen_binary_bytes_not_retrieved_in_hosted_ci",
        "doi": doi,
        "dataset_api": dataset_url,
        "version_api": version_url,
        "title": dataset.get("title") or version.get("title"),
        "publication_date": dataset.get("publicationDate") or version.get("publicationDate"),
        "expected_files": sorted(EXPECTED_FILES),
        "extra_files": extras,
        "files": sorted(files, key=lambda row: str(row["name"])),
        "binary_verification_requirement": "Before any EOG outcome, locally obtained bytes must match the API-declared size and digest for every analysis input file.",
        "hosted_ci_limitation": "At 2026-08-09, Dryad anonymous binary endpoints returned 401/403 or bot-challenge HTML to GitHub-hosted runners; these responses are not treated as data.",
        "scientific_boundary": "source identity/file-inventory freeze only; no table schema, species eligibility, support model, EOG graph, or EOG outcome inspected",
    }
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--doi", default=DOI)
    args = parser.parse_args()
    print(json.dumps(freeze(args.output_dir, args.doi), indent=2))


if __name__ == "__main__":
    main()
