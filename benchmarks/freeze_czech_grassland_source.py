"""Freeze public source metadata for the Czech dry-grassland plant benchmark.

No workbook bytes, species eligibility, graph geometry, or EOG outcome are
inspected here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.parse
import urllib.request

DOI = "10.5061/dryad.jh9w0vt8f"
EXPECTED_FILE = "Belinchón.et.al.Oikos2020.data.xlsx"
DRYAD_ROOT = "https://datadryad.org"
API_ROOT = f"{DRYAD_ROOT}/api/v2"


def _absolute(url: str) -> str:
    return urllib.parse.urljoin(DRYAD_ROOT + "/", url)


def _json(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        _absolute(url),
        headers={"User-Agent": "eog-nonisland-freeze/0.1", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("Dryad endpoint did not return a JSON object")
    return value


def _link(obj: dict[str, object], *names: str) -> str | None:
    links = obj.get("_links")
    if not isinstance(links, dict):
        return None
    for name in names:
        row = links.get(name)
        if isinstance(row, dict) and row.get("href"):
            return _absolute(str(row["href"]))
    return None


def _files(payload: dict[str, object]) -> list[dict[str, object]]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        return []
    for key in ("stash:files", "files"):
        rows = embedded.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def freeze(output: Path) -> dict[str, object]:
    encoded = urllib.parse.quote(f"doi:{DOI}", safe="")
    dataset_url = f"{API_ROOT}/datasets/{encoded}"
    dataset = _json(dataset_url)
    version_url = _link(dataset, "stash:version", "version")
    version = _json(version_url) if version_url else dataset
    files_url = _link(version, "stash:files", "files") or _link(dataset, "stash:files", "files")
    if not files_url:
        raise ValueError("Dryad API did not expose files")
    payload = _json(files_url)
    rows = _files(payload)
    matches = [
        row for row in rows
        if str(row.get("path") or row.get("fileName") or row.get("name") or "").strip() == EXPECTED_FILE
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {EXPECTED_FILE!r}, got {len(matches)}")
    row = matches[0]
    size = int(row.get("size") or 0)
    digest = str(row.get("digest") or "")
    digest_type = str(row.get("digestType") or "")
    if size <= 0 or not digest or not digest_type:
        raise ValueError("Dryad file lacks required integrity metadata")

    manifest = {
        "status": "preoutcome_source_metadata_freeze",
        "doi": DOI,
        "dataset_api": dataset_url,
        "version_api": version_url,
        "title": dataset.get("title") or version.get("title"),
        "publication_date": dataset.get("publicationDate") or version.get("publicationDate"),
        "published_design_reference": {
            "n_patches": 272,
            "taxon_group": "vascular plants",
            "role": "external literature reference only; workbook schema not yet inspected",
        },
        "file": {
            "name": EXPECTED_FILE,
            "declared_size": size,
            "declared_digest": digest,
            "declared_digest_type": digest_type,
            "mime_type": row.get("mimeType"),
            "api_self": _link(row, "self"),
            "api_download": _link(row, "stash:download", "download"),
        },
        "binary_verification_requirement": "Workbook bytes must match Dryad-declared size and digest before schema inspection or EOG analysis.",
        "scientific_boundary": "source identity/integrity freeze only; no workbook schema, species filtering, local-support fit, graph construction, or EOG outcome inspected",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.output), indent=2))


if __name__ == "__main__":
    main()
