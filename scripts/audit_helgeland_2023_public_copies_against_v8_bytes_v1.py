#!/usr/bin/env python3
"""Strictly compare three official 2023 public copies to ORIGINAL 2020 v8 SHA256.

Never treat 2023-only data as 2020 input. Downloads only declared-identical
individual-file copies by fixed public web UI IDs, streams each anonymously
through SHA256, emits no original bytes, row values or first-line text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
HIST = BASE / "helgeland_historical_public_vintages_frozen_v1.json"
EQUIV = BASE / "helgeland_niskanen_v8_v10_registered_digest_match_frozen_v1.json"
IDS = {
    "Dryad_readme.txt": 1952534,
    "Pop_size_1997_2012.csv": 1952533,
    "Pop_size_1998_2013.csv": 1952529,
}
ROOT_URL = "https://datadryad.org/downloads/file_stream/"


def hash_official_public_copy(file_id: int, max_bytes: int) -> tuple[str, int]:
    if file_id not in IDS.values() or not 1 <= max_bytes <= 5000:
        raise ValueError("Refuse unpinned 2023 source file request")
    request = urllib.request.Request(
        ROOT_URL + str(file_id),
        headers={"User-Agent": "EOG-v8-identical-public-copy/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as stream:
            destination = urllib.parse.urlparse(stream.geturl())
            if (destination.scheme != "https" or not destination.hostname or
                destination.port not in (None, 443)):
                raise ValueError("Refusing unsafe public file-stream redirect")
            h = hashlib.sha256()
            count = 0
            for block in iter(lambda: stream.read(16384), b""):
                count += len(block)
                if count > max_bytes:
                    raise ValueError("Received more than original 2020-v8 registered bytes")
                h.update(block)
            return h.hexdigest(), count
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        # No signed object-storage URLs or data values in logs.
        code = exc.code if isinstance(exc, urllib.error.HTTPError) else "NETWORK"
        raise RuntimeError(f"PUBLIC_LATER_COPY_UNAVAILABLE_HTTP_{code}") from None


def verify(history: dict, equivalence: dict,
           fetch=hash_official_public_copy) -> dict:
    if (history.get("schema") !=
        "eog.helgeland.historical_public_dryad_versions.frozen_observed_v1"
        or equivalence.get("schema") !=
        "eog.helgeland.niskanen2020_v8_vs_2023_v10.registered_sha256.frozen_observed_v1"):
        raise ValueError("Original or later-copy frozen evidence absent")
    original = history["archives"]["niskanen_2020"]
    if (original["version_id"] != 78498 or original["published_date"] != "2020-08-19"
        or equivalence["source"]["later_v10_version_id"] != 208617
        or equivalence["source"]["historical_v8_version_id"] != 78498):
        raise ValueError("Not the original 2020 v8 vs 2023 v10 source pair")
    orig = {x["name"]:x for x in original["critical_files"]}
    newer = {x["name"]:x for x in equivalence["pairs"]}
    if not (set(orig)==set(newer)==set(IDS)):
        raise ValueError("Unfrozen source file set")
    items = []
    for name, later_id in IDS.items():
        v8 = orig[name]
        v10 = newer[name]
        if (v10["v8_file_id"]!=v8["file_id"] or
            v10["v10_file_id"]!=later_id or
            v10["source_reported_sizes_equal"] is not True or
            v10["source_reported_sha256_equal"] is not True):
            raise ValueError("Official registered later-copy equivalence unqualified")
        digest, count = fetch(later_id, v8["size_bytes"])
        if count != v8["size_bytes"] or digest.lower() != v8["source_digest"].lower():
            raise ValueError(f"{name}: actual later-copy bytes NOT identical to frozen 2020 v8")
        items.append({
            "file_name":name,"historical_v8_file_id":v8["file_id"],
            "public_later_copy_file_id":later_id,
            "independent_actual_byte_sha256_matches_historical_v8":True,
            "actual_size_matches_v8":True,
            "biological_content_parsed":False,
        })
    return {
        "schema":"eog.helgeland.niskanen2020_v8.later_public_copy_sha256.v1",
        "status":"THREE_PUBLIC_COPIES_INDEPENDENTLY_HASH_MATCH_ORIGINAL_2020_V8",
        "original_v8_version_id":78498,"later_v10_version_id":208617,
        "files":items,
        "only_three_file_ids_requested":True,
        "actual_bytes_decoded_as_biological_rows":False,
        "2023_only_files_authorized_as_2020_inputs":False,
        "2020_original_file_content_identified_from_2023_copy":True,
        "surveyed_zero_verified":False,"island_code_crosswalk_verified":False,
        "historical_model_fitted":False,"ecological_forecast_authorized":False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse overwrite")
    result = verify(json.loads(HIST.read_text(encoding="utf-8")),
                    json.loads(EQUIV.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status":result["status"],"file_count":len(result["files"])}))


if __name__=="__main__":
    main()
