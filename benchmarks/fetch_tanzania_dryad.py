"""Fetch and fingerprint the Brodie-Newmark Tanzania fragmentation dataset.

Acquisition only: this module does not fit a support model, build an EOG graph,
or inspect any EOG performance statistic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import zipfile

DOI = "10.5061/dryad.p042h0c"
DRYAD_ROOT = "https://datadryad.org"
API_ROOT = f"{DRYAD_ROOT}/api/v2"
USER_AGENT = "eog-nonisland-freeze/0.1"
EXPECTED_FILES = {
    "0_usambara.R", "1_sites.R", "2_isolation_occurrence",
    "Nodes_E.csv", "Nodes_W.csv", "raster_east3.tif", "raster_west3.tif",
    "Sites.csv", "spp_occur.csv",
}


def _absolute(url: str) -> str:
    return urllib.parse.urljoin(DRYAD_ROOT + "/", url)


def _json(url: str) -> dict[str, object]:
    absolute = _absolute(url)
    req = urllib.request.Request(absolute, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object from {absolute}")
    return value


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
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


def _download_bundle(dataset_url: str, target: Path) -> str:
    bundle_url = dataset_url.rstrip("/") + "/download"
    req = urllib.request.Request(bundle_url, headers={"User-Agent": USER_AGENT, "Accept": "application/zip"})
    with urllib.request.urlopen(req, timeout=300) as response, target.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    if not zipfile.is_zipfile(target):
        prefix = target.read_bytes()[:200]
        raise ValueError(f"Dryad dataset download was not a ZIP archive; prefix={prefix!r}")
    return bundle_url


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

    declared: dict[str, dict[str, object]] = {}
    for row in file_rows:
        name = str(row.get("path") or row.get("fileName") or row.get("name") or "").strip()
        if not name:
            raise ValueError(f"malformed Dryad file record: {row}")
        declared[Path(name).name] = row

    bundle = output_dir / "dryad_dataset.zip"
    bundle_url = _download_bundle(dataset_url, bundle)
    with zipfile.ZipFile(bundle) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        member_by_name = {Path(m.filename).name: m for m in members}
        missing = sorted(EXPECTED_FILES - set(member_by_name))
        if missing:
            raise ValueError(f"Dryad bundle is missing expected files: {missing}")
        for name in EXPECTED_FILES:
            member = member_by_name[name]
            target = raw / name
            with archive.open(member) as source, target.open("wb") as handle:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)

    inventory: list[dict[str, object]] = []
    for name in sorted(EXPECTED_FILES):
        target = raw / name
        row = declared.get(name)
        if row is None:
            raise ValueError(f"API file inventory did not contain {name}")
        actual_size = target.stat().st_size
        declared_size = int(row.get("size") or 0)
        if declared_size and actual_size != declared_size:
            raise ValueError(f"size mismatch for {name}: actual={actual_size}, declared={declared_size}")
        digest_type = str(row.get("digestType") or "").lower()
        declared_digest = str(row.get("digest") or "").lower()
        verified = None
        if digest_type and declared_digest:
            if digest_type not in hashlib.algorithms_available:
                raise ValueError(f"unsupported declared digest type {digest_type!r} for {name}")
            actual_declared_digest = _digest(target, digest_type)
            verified = actual_declared_digest == declared_digest
            if not verified:
                raise ValueError(
                    f"{digest_type} mismatch for {name}: actual={actual_declared_digest}, declared={declared_digest}"
                )
        inventory.append({
            "name": name,
            "size": actual_size,
            "sha256": _digest(target, "sha256"),
            "declared_size": declared_size,
            "declared_digest": row.get("digest"),
            "declared_digest_type": row.get("digestType"),
            "declared_digest_verified": verified,
        })

    extras = sorted(set(declared) - EXPECTED_FILES)
    manifest = {
        "doi": doi,
        "dataset_api": dataset_url,
        "version_api": version_url,
        "bundle_url": bundle_url,
        "bundle_sha256": _digest(bundle, "sha256"),
        "title": dataset.get("title") or version.get("title"),
        "publication_date": dataset.get("publicationDate") or version.get("publicationDate"),
        "expected_files": sorted(EXPECTED_FILES),
        "extra_files": extras,
        "files": inventory,
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
