#!/usr/bin/env python3
"""Read-only public Dryad historic versions inventory for honest time-sliced baselines.

NO public-data file bytes are downloaded or decoded. The dataset's *latest*
version is deliberately never treated as a historical input. Public API JSON
metadata alone cannot certify observed absence, row timestamps or predictions.
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import date
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://datadryad.org"
SOURCES = {
    "baalsrud_2014": {
        "doi": "10.5061/dryad.nb260",
        "cutoff": "2014-12-31",
        "expected_files": frozenset({
            "DemographicNe-Datafile.csv",
            "README_for_DemographicNe-Datafile.txt",
        }),
    },
    "niskanen_2020": {
        "doi": "10.5061/dryad.m0cfxpp10",
        "cutoff": "2020-12-31",
        "expected_files": frozenset({
            "Pop_size_1997_2012.csv",
            "Pop_size_1998_2013.csv",
            "Dryad_readme.txt",
        }),
    },
}
API_DOI = re.compile(
    r"^/api/v2/datasets/doi%3A10\.5061%2Fdryad\.(?:nb260|m0cfxpp10)/versions$",
    re.IGNORECASE,
)
API_VERSION_FILES = re.compile(r"^/api/v2/versions/[0-9]+/files$")
API_VERSION = re.compile(r"^/api/v2/versions/([0-9]+)$")
API_FILE = re.compile(r"^/api/v2/files/([0-9]+)$")


def api_json(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    # Versions with >10 files need an explicit bounded per_page=100 request.
    # Any other query argument remains forbidden (including user-controlled pages).
    allow_page_size = bool(API_VERSION_FILES.fullmatch(parsed.path) and
                           parsed.query == "per_page=100")
    if (parsed.scheme != "https" or parsed.netloc != "datadryad.org"
            or parsed.fragment or
            (parsed.query and not allow_page_size) or
            not (API_DOI.fullmatch(parsed.path) or
                 API_VERSION_FILES.fullmatch(parsed.path))):
        raise ValueError("Refusing endpoint other than two public JSON namespaces")
    request = urllib.request.Request(
        url, headers={"Accept": "application/json",
                      "User-Agent": "EOG-historical-source-vintage-readonly/1.0"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Non-JSON response from Dryad")
        raw = response.read(3_000_001)
    if len(raw) > 3_000_000:
        raise ValueError("Public version metadata too large")
    out = json.loads(raw)
    if not isinstance(out, dict):
        raise ValueError("Expected metadata dictionary")
    return out


def choose_asof_version(spec: dict, version_listing: dict) -> tuple[dict, list[dict]]:
    published = version_listing.get("_embedded", {}).get("stash:versions")
    if not isinstance(published, list) or not published:
        raise ValueError("No unambiguous version list from official Dryad API")
    if version_listing.get("total") != len(published):
        raise ValueError("Historical version inventory incomplete or paginated")
    candidates: list[dict] = []
    public_versions: list[dict] = []
    cutoff = date.fromisoformat(spec["cutoff"])
    for item in published:
        stamp = item.get("publicationDate")
        version_number = item.get("versionNumber")
        link = item.get("_links", {}).get("self", {}).get("href")
        if not (isinstance(stamp, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", stamp)
                and isinstance(version_number, int)
                and isinstance(link, str) and API_VERSION.fullmatch(link)):
            raise ValueError("Incomplete version timestamp, revision number or canonical link")
        record = {
            "published_date": stamp,
            "version_number": version_number,
            "version_id": int(API_VERSION.fullmatch(link).group(1)),
        }
        public_versions.append(record)
        if date.fromisoformat(stamp) <= cutoff:
            candidates.append(record)
    if not candidates:
        raise ValueError("No version demonstrably published by historical cutoff")
    picked = sorted(candidates, key=lambda x: (x["published_date"], x["version_number"],
                                               x["version_id"]))[-1]
    return picked, public_versions


def qualify_file_inventory(spec: dict, chosen: dict, files: dict) -> dict:
    vid = chosen["version_id"]
    # Dryad includes the validated per_page parameter in the self link.
    # Never accept links to a different version or arbitrary pages.
    self_href = files.get("_links", {}).get("self", {}).get("href")
    if self_href not in (f"/api/v2/versions/{vid}/files",
                         f"/api/v2/versions/{vid}/files?per_page=100"):
        raise ValueError("File inventory is not version-scoped to historical selection")
    entries = files.get("_embedded", {}).get("stash:files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("No public file records")
    if files.get("total") != len(entries) or files.get("count") != len(entries):
        raise ValueError("Historical version file list incomplete")
    recorded = []
    for item in entries:
        name = item.get("path")
        size = item.get("size")
        meta_link = item.get("_links", {}).get("self", {}).get("href")
        if (not isinstance(name, str) or not name or "/" in name or
            "\\" in name or name.startswith(".")):
            raise ValueError("Unsafe file name in historical version")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ValueError("Missing public source file size")
        if not isinstance(meta_link, str) or not API_FILE.fullmatch(meta_link):
            raise ValueError("Missing public source file metadata ID")
        recorded.append({
            "name": name,
            "file_id": int(API_FILE.fullmatch(meta_link).group(1)),
            "source_reported_bytes": size,
            "source_reported_digest_type": item.get("digestType"),
            "source_reported_digest": item.get("digest"),
            "independently_hashed_bytes": False,
            "biological_rows_read": False,
        })
    if (len({r["name"] for r in recorded}) != len(recorded) or
        len({r["file_id"] for r in recorded}) != len(recorded)):
        raise ValueError("Duplicate historical names or file IDs")
    names = {r["name"] for r in recorded}
    if not spec["expected_files"].issubset(names):
        raise ValueError("Historical cutoff files do not include preregistered baseline filenames")
    return {
        "status": "HISTORICAL_PUBLIC_VERSION_METADATA_ELIGIBLE__BYTES_UNVERIFIED",
        "selected": chosen,
        "historical_cutoff": spec["cutoff"],
        "file_count": len(recorded),
        "files": sorted(recorded, key=lambda x: x["name"]),
        "required_file_names": sorted(spec["expected_files"]),
        "actual_source_file_bytes_read": False,
        "biological_rows_read": False,
        "published_version_available_by_cutoff": True,
        "source_files_at_cutoff_qualified_as_model_features": False,
        "island_code_and_calendar_crosswalk_verified": False,
        "surveyed_zero_observation_verified": False,
        "ecological_endpoint_authorized": False,
    }


def audit(fetch=api_json) -> dict:
    results = {}
    for key, spec in SOURCES.items():
        version_url = (API + "/api/v2/datasets/" +
                       urllib.parse.quote("doi:" + spec["doi"], safe="") + "/versions")
        try:
            picked, history = choose_asof_version(spec, fetch(version_url))
            files = fetch(API + f"/api/v2/versions/{picked['version_id']}/files?per_page=100")
            details = qualify_file_inventory(spec, picked, files)
            details["doi"] = spec["doi"]
            details["published_version_history"] = history
            details["versions_after_cutoff_not_eligible"] = [
                item for item in history if date.fromisoformat(item["published_date"]) >
                date.fromisoformat(spec["cutoff"])
            ]
            results[key] = details
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError,
                json.JSONDecodeError) as exc:
            results[key] = {
                "status": "HOLD_HISTORICAL_SOURCE_VERSION_UNVERIFIED",
                "doi": spec["doi"],
                "historical_cutoff": spec["cutoff"],
                "error_type": type(exc).__name__,
                "error_summary": str(exc)[:180],
                "actual_source_file_bytes_read": False,
                "biological_rows_read": False,
                "ecological_endpoint_authorized": False,
            }
    return {
        "schema": "eog.helgeland.historical_dryad_version_metadata.v1",
        "status": (
            "BOTH_HISTORICAL_PUBLIC_METADATA_VINTAGES_IDENTIFIED"
            if all(v["status"] == "HISTORICAL_PUBLIC_VERSION_METADATA_ELIGIBLE__BYTES_UNVERIFIED"
                   for v in results.values())
            else "HOLD_INCOMPLETE_HISTORICAL_PUBLIC_VINTAGES"
        ),
        "datasets": results,
        "latest_Dryad_version_never_assumed_to_exist_at_past_cutoff": True,
        "actual_biological_file_bytes_read": False,
        "individual_bird_rows_read": False,
        "old_8_islands_match_2026_11_islands": False,
        "actual_2021_2022_outcomes_read": False,
        "historically_frozen_model_or_forecast_qualified": False,
        "ecological_scoring_authorized": False,
    }



FROZEN_FILE = (Path(__file__).resolve().parents[1] /
               "validation/eog_virtual_world_ecology_synthesis_v1/"
               "helgeland_historical_public_vintages_frozen_v1.json")


def canonical_files_sha256(records: list[dict]) -> str:
    """Hash the complete *metadata catalog*, not any underlying bird data bytes."""
    relevant = sorted(
        ({k: r[k] for k in ("name", "file_id", "source_reported_bytes",
                           "source_reported_digest_type", "source_reported_digest")}
         for r in records),
        key=lambda x: x["name"]
    )
    canonical = json.dumps(relevant, ensure_ascii=False,
                           sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_against_frozen(result: dict, frozen: dict) -> dict:
    if result.get("status") != "BOTH_HISTORICAL_PUBLIC_METADATA_VINTAGES_IDENTIFIED":
        raise ValueError("Cannot verify historical source drift without both public inventories")
    if (frozen.get("schema") !=
        "eog.helgeland.historical_public_dryad_versions.frozen_observed_v1" or
        frozen.get("status") !=
        "HISTORICAL_2014_2020_SOURCE_METADATA_FROZEN__NO_BIRD_BYTES_READ"):
        raise ValueError("Historical frozen version contract missing")
    if set(result["datasets"]) != set(frozen["archives"]) != set(SOURCES):
        raise ValueError("Historical dataset set was altered")
    for name in SOURCES:
        source = result["datasets"][name]
        baseline = frozen["archives"][name]
        for key, source_key in (
            ("doi", "doi"), ("cutoff", "historical_cutoff"),
            ("version_id", "version_id"), ("version_number", "version_number"),
            ("published_date", "published_date"),
        ):
            value = (source.get(source_key) if source_key in ("doi", "historical_cutoff")
                     else source["selected"].get(source_key))
            if value != baseline[key]:
                raise ValueError(f"{name}: historical version changed at {key}")
        if source["file_count"] != baseline["file_count"]:
            raise ValueError(f"{name}: historical file count differs")
        if canonical_files_sha256(source["files"]) != baseline["canonical_full_file_metadata_sha256"]:
            raise ValueError(f"{name}: complete historical file catalog changed")
        for critical in baseline["critical_files"]:
            matches = [f for f in source["files"] if f["name"] == critical["name"]]
            if len(matches) != 1:
                raise ValueError(f"{name}: key historic file missing")
            file = matches[0]
            for ref, src in (
                ("file_id", "file_id"), ("size_bytes", "source_reported_bytes"),
                ("source_digest_type", "source_reported_digest_type"),
                ("source_digest", "source_reported_digest")
            ):
                if critical[ref] != file[src]:
                    raise ValueError(f"{name}: source file identity changed")
        if source["published_version_history"] != baseline["version_history"]:
            raise ValueError(f"{name}: historic release lineage changed")
        if (source["actual_source_file_bytes_read"] is not False or
            source["ecological_endpoint_authorized"] is not False or
            source["source_files_at_cutoff_qualified_as_model_features"] is not False):
            raise ValueError(f"{name}: biological/feature eligibility boundary violated")
    for key in ("public_2014_2020_file_rows_read", "source_reported_digest_independently_verified",
                "island_crosswalk_verified", "future_2021_2022_outcomes_read",
                "prospective_EOG_model_or_heldout_score_authorized"):
        if frozen.get(key) is not False:
            raise ValueError(f"Frozen historical evidence boundary changed: {key}")
    return {
        "status": "MATCHES_FROZEN_2014_V1_AND_2020_V8_PUBLIC_VERSION_METADATA",
        "historic_file_metadata_catalogs_matched": 2,
        "bird_data_bytes_read": False,
        "historical_biological_prediction_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-frozen", type=Path, default=None)
    args = parser.parse_args()
    report = audit()
    if args.verify_frozen is not None:
        frozen = json.loads(args.verify_frozen.read_text(encoding="utf-8"))
        report["frozen_identity_check"] = verify_against_frozen(report, frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({
        "status": report["status"],
        "source_status": {key: value["status"] for key, value in report["datasets"].items()}
    }, sort_keys=True))


if __name__ == "__main__":
    main()
