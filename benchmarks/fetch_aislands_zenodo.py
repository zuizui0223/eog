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


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": "eog-aislands-freeze/0.1"})


def _download(url: str, path: Path) -> None:
    with urllib.request.urlopen(_request(url), timeout=120) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _load_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(_request(url), timeout=120) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object from {url}")
    return payload


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


def _normalise_version(value: object) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"^version\s*", "", text)
    text = re.sub(r"^v(?=\d)", "", text)
    return text.strip()


def _record_version(record: dict[str, object]) -> str:
    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        return ""
    return _normalise_version(metadata.get("version"))


def _version_records(payload: dict[str, object]) -> list[dict[str, object]]:
    hits = payload.get("hits")
    if isinstance(hits, dict):
        rows = hits.get("hits") or []
    elif isinstance(hits, list):
        rows = hits
    else:
        rows = payload.get("records") or []
    return [row for row in rows if isinstance(row, dict)]


def _resolve_record(requested_id: int, expected_version: str) -> tuple[dict[str, object], str, str]:
    """Resolve a concept/version reference to one exact Zenodo record."""
    requested_api = f"https://zenodo.org/api/records/{requested_id}"
    initial = _load_json(requested_api)
    initial_id = int(initial.get("id", -1))
    concept_id = str(initial.get("conceptrecid") or "").strip()
    requested_matches = initial_id == int(requested_id) or concept_id == str(requested_id)
    if not requested_matches:
        raise ValueError(
            f"Zenodo response is unrelated to requested record/concept {requested_id}: "
            f"record={initial_id}, concept={concept_id or 'missing'}"
        )

    wanted = _normalise_version(expected_version)
    if _record_version(initial) == wanted:
        resolved = initial
        mode = "direct_or_concept_redirect"
    else:
        links = initial.get("links") or {}
        versions_url = links.get("versions") if isinstance(links, dict) else None
        if not versions_url:
            raise ValueError(
                f"requested A-Islands version {expected_version!r} is not the resolved version "
                "and Zenodo supplied no versions link"
            )
        versions = _version_records(_load_json(str(versions_url)))
        matches = [record for record in versions if _record_version(record) == wanted]
        if len(matches) != 1:
            found = sorted({_record_version(record) for record in versions if _record_version(record)})
            raise ValueError(
                f"expected exactly one Zenodo version {expected_version!r}; "
                f"found {len(matches)} matches among versions {found}"
            )
        resolved = matches[0]
        mode = "resolved_via_versions"

    resolved_id = int(resolved.get("id", -1))
    if resolved_id < 1:
        raise ValueError("resolved Zenodo version has no valid numeric record ID")
    exact_api = f"https://zenodo.org/api/records/{resolved_id}"
    exact = _load_json(exact_api)
    if int(exact.get("id", -1)) != resolved_id:
        raise ValueError("exact Zenodo record endpoint did not preserve the resolved record ID")
    if _record_version(exact) != wanted:
        raise ValueError(
            f"exact Zenodo record version {_record_version(exact)!r} != expected {wanted!r}"
        )
    exact_concept = str(exact.get("conceptrecid") or "").strip()
    if concept_id and exact_concept and exact_concept != concept_id:
        raise ValueError("resolved Zenodo record belongs to a different concept")
    return exact, exact_api, mode


def fetch_record(
    requested_record_or_concept_id: int,
    output_dir: Path,
    *,
    expected_version: str = "1.0",
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    extracted_dir = output_dir / "extracted"
    raw_dir.mkdir(exist_ok=True)
    extracted_dir.mkdir(exist_ok=True)

    metadata, exact_api, resolution_mode = _resolve_record(
        requested_record_or_concept_id,
        expected_version,
    )
    metadata_path = output_dir / "zenodo_record.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    files = metadata.get("files") or []
    if not isinstance(files, list) or not files:
        raise ValueError("Zenodo record has no downloadable files")

    inventory: list[dict[str, object]] = []
    for entry in sorted(files, key=lambda item: str(item.get("key", ""))):
        if not isinstance(entry, dict):
            raise ValueError("malformed Zenodo file entry")
        key = str(entry.get("key") or "").strip()
        links = entry.get("links") or {}
        url = links.get("content") or links.get("self") if isinstance(links, dict) else None
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

    metadata_block = metadata.get("metadata") or {}
    if not isinstance(metadata_block, dict):
        metadata_block = {}
    manifest = {
        "requested_record_or_concept_id": int(requested_record_or_concept_id),
        "resolved_record_id": int(metadata["id"]),
        "conceptrecid": metadata.get("conceptrecid"),
        "expected_version": _normalise_version(expected_version),
        "version": _record_version(metadata),
        "version_resolution": resolution_mode,
        "doi": metadata.get("doi"),
        "title": metadata_block.get("title"),
        "publication_date": metadata_block.get("publication_date"),
        "source_api": exact_api,
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
    parser.add_argument("--expected-version", default="1.0")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(
        fetch_record(
            args.record_id,
            args.output_dir,
            expected_version=args.expected_version,
        ),
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
