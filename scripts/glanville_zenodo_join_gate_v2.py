#!/usr/bin/env python3
"""Pinned Glanville archive key-grain audit, strictly without biological scoring.

Second-stage structured join qualification (not a source retry or EOG-WF result).
Only aggregate row counts, column identities and cross-archive key overlap are
exported. Unverified source/patch identifiers are never silently reconciled.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile


class SourceStop(Exception):
    pass


def _norm(x: object) -> str:
    return "".join(c.lower() for c in str(x).strip().lstrip("\ufeff") if c.isalnum())


def _download(src: dict, directory: Path, seconds: int) -> Path:
    archive = directory / src["filename"]
    request = urllib.request.Request(src["archive_url"], headers={
        "User-Agent": "EOG-exploratory-source-join-audit/1.0",
        "Accept": "*/*",
    })
    sha = hashlib.sha256()
    size = 0
    try:
        with urllib.request.urlopen(request, timeout=seconds) as response:
            with archive.open("wb") as out:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(block)
                    if size > src["max_bytes"]:
                        raise SourceStop("STOP_SOURCE_COMPRESSED_BYTE_BUDGET")
                    sha.update(block)
                    out.write(block)
    except urllib.error.HTTPError as exc:
        raise SourceStop(f"STOP_TRANSPORT_HTTP_{exc.code}_{src['tag']}") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise SourceStop("STOP_TRANSPORT_" + type(exc).__name__ + "_" + src["tag"]) from exc
    if sha.hexdigest() != src["sha256"]:
        raise SourceStop("STOP_SOURCE_SHA_MISMATCH_" + src["tag"])
    return archive


def _table(archive: Path, mode: str, path: str, sep: str,
           required: tuple[str, ...], max_rows: int, max_fields: int,
           key_names: tuple[str, ...] = ()) -> dict:
    if mode == "zip":
        z = zipfile.ZipFile(archive)
        if path not in z.namelist():
            z.close()
            raise SourceStop("STOP_SOURCE_SCHEMA_MISSING_" + path)
        source = z.open(path)
    elif mode == "tar.gz":
        z = tarfile.open(archive, "r:gz")
        try:
            member = z.getmember(path)
        except KeyError as exc:
            z.close()
            raise SourceStop("STOP_SOURCE_SCHEMA_MISSING_" + path) from exc
        source = z.extractfile(member)
        if source is None:
            z.close()
            raise SourceStop("STOP_SOURCE_SCHEMA_NOT_A_FILE_" + path)
    else:
        raise SourceStop("STOP_SOURCE_SCHEMA_UNKNOWN_ARCHIVE_TYPE")
    rows = 0
    missing = 0
    duplicates = 0
    keyset = set()
    years = set()
    good_xy = 0
    bad_xy = 0
    try:
        with z:
            with source:
                with io.TextIOWrapper(source, encoding="utf-8-sig", errors="replace", newline="") as textstream:
                    first = textstream.readline()
                    if first.lower().strip().startswith("sep="):
                        lines = iter(textstream)
                        csv_sep = first.strip()[4:] or sep
                    else:
                        lines = itertools.chain((first,), textstream)
                        csv_sep = sep
                    reader = csv.DictReader(lines, delimiter=csv_sep)
                    if not reader.fieldnames:
                        raise SourceStop("STOP_SOURCE_SCHEMA_NO_HEADER_" + path)
                    fields = reader.fieldnames
                    if len(fields) > max_fields:
                        raise SourceStop("STOP_SOURCE_SCHEMA_TOO_MANY_FIELDS_" + path)
                    cmap = {_norm(k): k for k in fields if k is not None}
                    miss = [k for k in required if _norm(k) not in cmap]
                    if miss:
                        raise SourceStop("STOP_SOURCE_SCHEMA_HEADERS_" + path + ":" + ",".join(miss))
                    actual_keys = [cmap[_norm(k)] for k in key_names if _norm(k) in cmap]
                    if key_names and len(actual_keys) != len(key_names):
                        actual_keys = []
                    xcol, ycol = cmap.get("x"), cmap.get("y")
                    for row in reader:
                        rows += 1
                        if rows > max_rows:
                            raise SourceStop("STOP_SOURCE_ROWS_BUDGET_" + path)
                        if actual_keys:
                            vals = tuple(str(row.get(key, "") or "").strip() for key in actual_keys)
                            if any(not v or v.lower() in ("na", "n/a", "nan", "none") for v in vals):
                                missing += 1
                            elif vals in keyset:
                                duplicates += 1
                            else:
                                keyset.add(vals)
                        yearcol = cmap.get("year")
                        if yearcol:
                            y = str(row.get(yearcol, "") or "").strip()
                            try:
                                if y:
                                    years.add(int(float(y)))
                            except (ValueError, OverflowError):
                                pass
                        if xcol and ycol:
                            try:
                                x = float(row.get(xcol, ""))
                                y = float(row.get(ycol, ""))
                                if math.isfinite(x) and math.isfinite(y):
                                    good_xy += 1
                                else:
                                    bad_xy += 1
                            except (TypeError, ValueError):
                                bad_xy += 1
                    return {
                        "path": path, "rows": rows, "header": fields,
                        "candidate_keys": list(key_names),
                        "keys_exist": bool(actual_keys),
                        "unique_keys": len(keyset),
                        "duplicate_key_rows": duplicates,
                        "missing_key_rows": missing,
                        "year_range": [min(years), max(years)] if years else None,
                        "coordinates_finite_rows": good_xy,
                        "coordinates_invalid_rows": bad_xy,
                        "_keys": keyset,
                    }
    except (csv.Error, UnicodeError) as exc:
        raise SourceStop("STOP_SOURCE_CSV_PARSE_" + path + ":" + type(exc).__name__) from exc


def _family(path: Path, max_rows: int, max_fields: int):
    tables = []
    for name in ("master-input.csv", "master-output.csv"):
        # Header is exported even if Patch and Year are absent.
        result = _table(path, "tar.gz", name, ",", (), max_rows, max_fields, ())
        fields = {_norm(n) for n in result["header"]}
        if "patch" in fields and "year" in fields:
            result = _table(path, "tar.gz", name, ",", (), max_rows, max_fields, ("patch", "year"))
        result["individual_level_patches_present"] = "patch" in fields
        result["year_present"] = "year" in fields
        tables.append(result)
    return tables


def run_gate(proto: dict, output: Path) -> dict:
    result = {
        "schema_version": 1,
        "status": "STOP_UNSTARTED",
        "parent_gate": proto["parent_gate"],
        "source_sha_verification": {},
        "table_summaries": [],
        "models_fit": 0,
        "ecological_responses_scored": 0,
        "EOG_WF_new_endpoints": 0,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="eog_glanville_join_") as dirname:
            folder = Path(dirname)
            paths = {}
            for src in proto["sources"]:
                path = _download(src, folder, proto["limits"]["timeout_seconds"])
                paths[src["tag"]] = path
                result["source_sha_verification"][src["tag"]] = src["sha256"]
            max_rows = proto["limits"]["max_csv_rows_each"]
            max_fields = proto["limits"]["max_csv_fields"]
            a = paths["schulz2019_occupancy"]
            b = paths["fountain2017_families"]
            survey = _table(a, "zip", proto["source_2019_tables"]["survey"], "\t",
                            tuple(proto["source_2019_required_survey_columns"]),
                            max_rows, max_fields, ("patch", "year"))
            network = _table(a, "zip", proto["source_2019_tables"]["patch_network"], "\t",
                             tuple(proto["source_2019_required_network_columns"]),
                             max_rows, max_fields, ("patch",))
            areas = _table(a, "zip", proto["source_2019_tables"]["patch_area"], "\t",
                           ("patch", "year", "area"), max_rows, max_fields, ("patch", "year"))
            family = _family(b, max_rows, max_fields)
            network_patch = {v[0] for v in network["_keys"]}
            survey_patch = {v[0] for v in survey["_keys"]}
            result["survey_spatial_join"] = {
                "survey_distinct_patches": len(survey_patch),
                "network_distinct_patches": len(network_patch),
                "survey_patches_matched": len(survey_patch & network_patch),
                "survey_patches_unmatched": len(survey_patch - network_patch),
                "survey_patch_years": len(survey["_keys"]),
                "patch_area_join_patch_years": len(survey["_keys"] & areas["_keys"]),
            }
            linked = []
            for fam in family:
                if fam["keys_exist"]:
                    linked.append({
                        "file_path": fam["path"],
                        "candidate_patch_years": len(fam["_keys"]),
                        "same_literal_patch_year_overlap": len(survey["_keys"] & fam["_keys"]),
                    })
            result["family_join_candidates"] = linked
            for table in [survey, network, areas, *family]:
                table.pop("_keys", None)
                result["table_summaries"].append(table)
            if not survey_patch or not network_patch or not (survey_patch & network_patch):
                raise SourceStop("STOP_SPATIAL_JOIN_NO_SHARED_PATCH_IDS")
            result["status"] = (
                "SOURCE_SPATIAL_AND_FAMILY_KEYS_JOINABLE_UNVERIFIED_PROVENANCE"
                if any(row["same_literal_patch_year_overlap"] > 0 for row in linked)
                else "SOURCE_SPATIAL_KEYS_VERIFIED_FAMILY_LINK_UNRESOLVED"
            )
            result["coordinate_crs"] = "UNVERIFIED_FROM_ORIGINAL_ARCHIVE_SCHEMA"
            result["biological_interpretation"] = (
                "None. Patch/time joins and full-sib labels cannot certify mother, "
                "founder, chronological colonisation or independent dispersal bounds."
            )
    except (SourceStop, zipfile.BadZipFile, tarfile.TarError) as exc:
        result["status"] = str(exc) if isinstance(exc, SourceStop) else "STOP_SOURCE_SCHEMA_ARCHIVE_ERROR"
        result["error_type"] = type(exc).__name__
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    result["receipt_sha256_without_self_hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    output.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "receipt_path": str(output)}, sort_keys=True))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", type=Path, default=Path("validation/glanville_zenodo_join_gate_v2/protocol_v2.json"))
    ap.add_argument("--output", type=Path, default=Path("results/glanville_zenodo_join_gate_v2/receipt.json"))
    args = ap.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    run_gate(protocol, args.output)


if __name__ == "__main__":
    main()
