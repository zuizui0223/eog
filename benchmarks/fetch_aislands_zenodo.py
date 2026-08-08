"""Fetch and fingerprint the frozen A-Islands source record before EOG outcomes.

This utility intentionally performs data acquisition only. It does not fit an SDM,
run EOG, inspect held-out outcomes, or select taxa using EOG performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tarfile
import urllib.request
import zipfile


def _download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "eog-aislands-freeze/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_declared_checksum(path: Path, declared: str | None) -> dict[str, object]:
    if not declared:
        return {"declared_checksum": None, "checksum_verified": None}
    if ":" not in declared:
        return {"declared_checksum": declared, "checksum_verified": None}
    algorithm, expected = declared.split(":", 1)
    algorithm = algorithm.lower().strip()
    if algorithm not in hashlib.algorithms_available:
        return {"declared_checksum": declared, "checksum_verified": None}
    observed = _digest(path, algorithm)
    if observed.lower() != expected.lower():
        raise ValueError(f"checksum mismatch for {path.name}: {declared} != {algorithm}:{observed}")
    return {"declared_checksum": declared, "checksum_verified": True}


def _safe_extract_zip(path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"unsafe zip member: {member.filename}")
        archive.extractall(destination)


def _safe_extract_tar(path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"unsafe tar member: {member.name}")
        archive.extractall(destination)


def _normalise_name(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "", path.stem.casefold())


def _find_table(root: Path, token: str) -> Path:
    token = re.sub(r"[^a-z0-9]+", "", token.casefold())
    candidates = sorted(
        path for path in root.rglob("*.csv")
        if token in _normalise_name(path)
    )
    if len(candidates) != 1:
        names = [str(path.relative_to(root)) for path in candidates]
        raise ValueError(f"expected exactly one CSV matching {token!r}; found {names}")
    return candidates[0]


def fetch_record(record_id: int, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    extracted_dir = output_dir / "extracted"
    raw_dir.mkdir(exist_ok=True)
    extracted_dir.mkdir(exist_ok=True)

    api_url = f"https://zenodo.org/api/records/{record_id}"
    metadata_path = output_dir / "zenodo_record.json"
    _download(api_url, metadata_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    if int(metadata.get("id", -1)) != int(record_id):
        raise ValueError("Zenodo returned a different record ID")
    files = metadata.get("files") or []
    if not files:
        raise ValueError("Zenodo record has no downloadable files")

    inventory: list[dict[str, object]] = []
    for entry in sorted(files, key=lambda item: str(item.get("key", ""))):
        key = str(entry.get("key") or "").strip()
        links = entry.get("links") or {}
        url = links.get("content") or links.get("self")
        if not key or not url:
            raise ValueError(f"malformed Zenodo file entry: {entry}")
        destination = raw_dir / Path(key).name
        _download(str(url), destination)
        checksum_audit = _verify_declared_checksum(destination, entry.get("checksum"))
        row = {
            "key": key,
            "size": destination.stat().st_size,
            "sha256": _digest(destination, "sha256"),
            **checksum_audit,
        }
        inventory.append(row)

        lower = destination.name.casefold()
        if lower.endswith(".zip"):
            _safe_extract_zip(destination, extracted_dir)
        elif lower.endswith((".tar", ".tar.gz", ".tgz")):
            _safe_extract_tar(destination, extracted_dir)
        elif lower.endswith(".csv"):
            shutil.copy2(destination, extracted_dir / destination.name)

    island_source = _find_table(extracted_dir, "islanddata")
    species_source = _find_table(extracted_dir, "speciesdata")
    island_target = output_dir / "island_data.csv"
    species_target = output_dir / "species_data.csv"
    shutil.copy2(island_source, island_target)
    shutil.copy2(species_source, species_target)

    manifest = {
        "record_id": int(record_id),
        "conceptrecid": metadata.get("conceptrecid"),
        "doi": metadata.get("doi"),
        "title": (metadata.get("metadata") or {}).get("title"),
        "publication_date": (metadata.get("metadata") or {}).get("publication_date"),
        "source_api": api_url,
        "files": inventory,
        "resolved_island_data": str(island_source.relative_to(output_dir)),
        "resolved_species_data": str(species_source.relative_to(output_dir)),
        "island_data_sha256": _digest(island_target, "sha256"),
        "species_data_sha256": _digest(species_target, "sha256"),
        "scientific_boundary": (
            "pre-outcome source freeze only; no SDM, EOG, held-out outcome, or topology result inspected"
        ),
    }
    (output_dir / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-id", type=int, default=10775809)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fetch_record(args.record_id, args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
