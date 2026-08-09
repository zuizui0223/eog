"""Fetch and fingerprint the Brodie-Newmark Tanzania fragmentation dataset.

Acquisition only: this module does not fit a support model, build an EOG graph,
or inspect any EOG performance statistic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
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


def _request(url: str):
    return urllib.request.Request(_absolute(url), headers={"User-Agent": "eog-nonisland-freeze/0.1", "Accept": "application/json"})


def _json(url: str) -> dict[str, object]:
    absolute = _absolute(url)
    with urllib.request.urlopen(_request(absolute), timeout=120) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object from {absolute}")
    return value


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
            return [r for r in rows if isinstance(r, dict)]
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


def fetch(output_dir: Path, doi: str = DOI) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = output_dir / "raw"
    raw.mkdir(exist_ok=True)
    encoded = urllib.parse.quote(f"doi:{doi}", safe="")
    dataset_url = f"{API_ROOT}/datasets/{encoded}"
    dataset = _json(dataset_url)

    version_url = _link(dataset, "stash:version", "version")
    version = _json(version_url) if version_url else dataset
    files_url = _link(version, "stash:files", "files") or _link(dataset, "stash:files", "files")
    if not files_url:
        raise ValueError("Dryad API response did not expose a files endpoint")
    file_rows = _file_pages(files_url)
    if not file_rows:
        raise ValueError("Dryad files endpoint returned no files")

    inventory: list[dict[str, object]] = []
    for row in file_rows:
        name = str(row.get("path") or row.get("fileName") or row.get("name") or "").strip()
        file_id = row.get("id")
        if not name or file_id in (None, ""):
            raise ValueError(f"malformed Dryad file record: {row}")
        download = f"{DRYAD_ROOT}/downloads/file_stream/{int(file_id)}"
        target = raw / Path(name).name
        with urllib.request.urlopen(urllib.request.Request(download, headers={"User-Agent": "eog-nonisland-freeze/0.1"}), timeout=180) as response, target.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        inventory.append({
            "id": int(file_id),
            "name": target.name,
            "size": target.stat().st_size,
            "sha256": _sha256(target),
            "declared_digest": row.get("digest"),
            "declared_digest_type": row.get("digestType"),
            "public_download": download,
        })

    names = {row["name"] for row in inventory}
    missing = sorted(EXPECTED_FILES - names)
    extras = sorted(names - EXPECTED_FILES)
    if missing:
        raise ValueError(f"Dryad source is missing expected files: {missing}")

    manifest = {
        "doi": doi,
        "dataset_api": dataset_url,
        "version_api": version_url,
        "title": dataset.get("title") or version.get("title"),
        "publication_date": dataset.get("publicationDate") or version.get("publicationDate"),
        "expected_files": sorted(EXPECTED_FILES),
        "extra_files": extras,
        "files": sorted(inventory, key=lambda r: str(r["name"])),
        "scientific_boundary": "source acquisition/fingerprint only; no EOG outcome inspected",
    }
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--doi", default=DOI)
    args = p.parse_args()
    print(json.dumps(fetch(args.output_dir, args.doi), indent=2))


if __name__ == "__main__":
    main()
