"""Acquire the SW Finland raw CSV through a byte-verified institutional mirror.

This is transport/provenance code only.  It downloads the exact Zenodo object linked from
Åbo Akademi and requires its bytes to match the cryptographic digest in Dryad's public API.
It does not parse CSV records or access the ``outcome`` column.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin

import requests


DRYAD_DOI = "10.5061/dryad.ffbg79cr6"
DRYAD_DATASET_URL = "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.ffbg79cr6"
INSTITUTIONAL_URL = "https://research.abo.fi/en/persons/mikael-von-numers/"
ZENODO_RECORD_ID = 4942881
ZENODO_API = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
EXPECTED_NAME = "colonization_select.csv"


def _filename_of(value: dict[str, object]) -> str:
    for key in ("path", "fileName", "filename", "name", "key"):
        raw = value.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip().split("/")[-1]
    return ""


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _normalise_algorithm(value: str) -> str:
    return value.lower().replace("_", "").replace("-", "").strip()


def _get_json(session: requests.Session, url: str) -> dict[str, object]:
    response = session.get(url, timeout=90)
    response.raise_for_status()
    value = response.json()
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object from {url}")
    return value


def acquire(output_file: str | Path) -> dict[str, object]:
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "EOG-v2-finland-response-free-provenance/1.0"})

    institutional = session.get(INSTITUTIONAL_URL, timeout=90)
    institutional.raise_for_status()
    if DRYAD_DOI not in institutional.text or str(ZENODO_RECORD_ID) not in institutional.text:
        raise RuntimeError("Åbo Akademi page no longer links the expected Dryad DOI and Zenodo record")

    dryad_dataset = _get_json(session, DRYAD_DATASET_URL)
    identifier = str(dryad_dataset.get("identifier") or dryad_dataset.get("id") or "")
    if "ffbg79cr6" not in identifier:
        raise RuntimeError(f"Dryad dataset identifier mismatch: {identifier!r}")
    version_link = ((dryad_dataset.get("_links") or {}).get("stash:version") or {}).get("href")
    if not version_link:
        raise RuntimeError("Dryad dataset API did not expose stash:version")
    dryad_version_url = urljoin("https://datadryad.org", str(version_link))
    dryad_version = _get_json(session, dryad_version_url)

    version_links = dryad_version.get("_links") or {}
    files_link = None
    if isinstance(version_links, dict):
        for key, value in version_links.items():
            if "file" not in str(key).lower():
                continue
            if isinstance(value, dict) and value.get("href"):
                files_link = value["href"]
                break
    dryad_files_url = (
        urljoin("https://datadryad.org", str(files_link))
        if files_link
        else dryad_version_url.rstrip("/") + "/files"
    )
    dryad_files = _get_json(session, dryad_files_url)

    candidates: dict[tuple[str, str, int], dict[str, object]] = {}
    for item in _walk(dryad_files):
        if not isinstance(item, dict) or _filename_of(item) != EXPECTED_NAME:
            continue
        digest = item.get("digest") or item.get("checksum")
        digest_type = item.get("digestType") or item.get("digest_type") or item.get("checksumType")
        size = item.get("size") or item.get("fileSize") or item.get("filesize")
        if digest is None or size is None:
            continue
        candidates[(str(digest), str(digest_type or ""), int(size))] = item
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected one cryptographically identified Dryad {EXPECTED_NAME}; found {len(candidates)}"
        )
    (dryad_digest, dryad_digest_type, dryad_size), _ = next(iter(candidates.items()))

    if ":" in dryad_digest:
        prefix, value = dryad_digest.split(":", 1)
        if not dryad_digest_type:
            dryad_digest_type = prefix
            dryad_digest = value
        elif _normalise_algorithm(prefix) in {"sha256", "md5"}:
            dryad_digest = value
    algorithm = _normalise_algorithm(dryad_digest_type)
    if not algorithm:
        algorithm = "sha256" if len(dryad_digest) == 64 else "md5" if len(dryad_digest) == 32 else ""
    if algorithm not in {"sha256", "md5"}:
        raise RuntimeError(f"unsupported/ambiguous Dryad digest algorithm: {dryad_digest_type!r}")
    dryad_digest = dryad_digest.lower()

    zenodo = _get_json(session, ZENODO_API)
    title = str((zenodo.get("metadata") or {}).get("title") or "")
    if "Island properties dominate species traits" not in title:
        raise RuntimeError(f"Zenodo mirror title mismatch: {title!r}")
    raw_files = zenodo.get("files")
    if isinstance(raw_files, list):
        entries = raw_files
    elif isinstance(raw_files, dict) and isinstance(raw_files.get("entries"), dict):
        entries = list(raw_files["entries"].values())
    else:
        raise RuntimeError(f"unexpected Zenodo files schema: {type(raw_files).__name__}")
    matches = [entry for entry in entries if isinstance(entry, dict) and _filename_of(entry) == EXPECTED_NAME]
    if len(matches) != 1:
        raise RuntimeError(f"Zenodo record does not contain exactly one {EXPECTED_NAME}")
    zenodo_file = matches[0]
    zenodo_size = int(zenodo_file.get("size"))
    if zenodo_size != dryad_size:
        raise RuntimeError(f"Dryad/Zenodo byte-size mismatch: {dryad_size} != {zenodo_size}")
    zenodo_checksum = str(zenodo_file.get("checksum") or "")
    links = zenodo_file.get("links") or {}
    content_url = links.get("content") or links.get("download") or links.get("self")
    if not content_url:
        raise RuntimeError("Zenodo file has no content URL")

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    computed_size = 0
    with session.get(str(content_url), stream=True, timeout=240) as response:
        response.raise_for_status()
        with output.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                md5.update(chunk)
                sha256.update(chunk)
                computed_size += len(chunk)
    if computed_size != dryad_size:
        raise RuntimeError(f"downloaded mirror size mismatch: {computed_size} != {dryad_size}")

    computed = {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}
    if computed[algorithm] != dryad_digest:
        raise RuntimeError(
            f"Dryad/{algorithm} byte identity FAILED: {computed[algorithm]} != {dryad_digest}"
        )
    if zenodo_checksum:
        if ":" not in zenodo_checksum:
            raise RuntimeError(f"ambiguous Zenodo checksum: {zenodo_checksum!r}")
        z_algorithm, z_digest = zenodo_checksum.split(":", 1)
        z_algorithm = _normalise_algorithm(z_algorithm)
        if z_algorithm not in computed or computed[z_algorithm] != z_digest.lower():
            raise RuntimeError("Zenodo declared checksum does not match downloaded bytes")

    return {
        "status": "finland-institutional-mirror-byte-identical-to-dryad",
        "institutional_url": INSTITUTIONAL_URL,
        "dryad_doi": DRYAD_DOI,
        "dryad_dataset_api": DRYAD_DATASET_URL,
        "dryad_version_api": dryad_version_url,
        "dryad_files_api": dryad_files_url,
        "dryad_file_name": EXPECTED_NAME,
        "dryad_file_size": dryad_size,
        "dryad_digest_type": algorithm,
        "dryad_digest": dryad_digest,
        "zenodo_record": ZENODO_RECORD_ID,
        "zenodo_api": ZENODO_API,
        "zenodo_title": title,
        "zenodo_file_name": EXPECTED_NAME,
        "zenodo_file_size": zenodo_size,
        "zenodo_checksum": zenodo_checksum,
        "downloaded_size": computed_size,
        "downloaded_md5": computed["md5"],
        "downloaded_sha256": computed["sha256"],
        "csv_contents_parsed": False,
        "outcome_values_accessed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()
    result = acquire(args.output)
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "downloaded_size": result["downloaded_size"],
                "downloaded_sha256": result["downloaded_sha256"],
                "outcome_values_accessed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
