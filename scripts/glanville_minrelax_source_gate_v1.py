#!/usr/bin/env python3
"""One-shot, source-only Glanville archive qualification.

No ecological response scoring, inference, model fitting or archival of raw data.
All expected paths, row counts and request limits were frozen in the protocol
before the source download. A blocked transport is a scientific STOP, not success.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import urllib.error
import urllib.request
import zipfile


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _norm(name: object) -> str:
    return "".join(ch.lower() for ch in str(name).strip().lstrip("\ufeff") if ch.isalnum())


def _write_receipt(path: Path, result: dict) -> dict:
    content = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
    result["receipt_sha256_without_self_hash"] = _sha((content + "\n").encode("utf-8"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "receipt": str(path), "source_sha256": result.get("archive_sha256")}, sort_keys=True))
    return result


def _read_member(z: zipfile.ZipFile, member: zipfile.ZipInfo, expected: dict, max_rows: int) -> dict:
    sha = hashlib.sha256()
    with z.open(member) as source:
        for data in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(data)

    result: dict = {
        "member_path": member.filename,
        "member_sha256": sha.hexdigest(),
        "uncompressed_bytes": member.file_size,
        "rows": 0,
    }
    patch_year: set[tuple[str, str]] = set()
    ids_year: set[tuple[str, str]] = set()
    missing_patch_or_year = 0
    missing_id_or_year = 0
    years: set[int] = set()
    repeated_patch_year = 0
    repeated_dna_year = 0
    with z.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("STOP_SCHEMA_NO_CSV_HEADER: " + member.filename)
        fieldnames = reader.fieldnames
        norm_to_actual = {_norm(x): x for x in fieldnames if x is not None}
        required = expected["required_columns"]
        missing = [col for col in required if _norm(col) not in norm_to_actual]
        result["header"] = fieldnames
        result["missing_required_headers"] = missing
        if missing:
            raise ValueError("STOP_SCHEMA_MISSING_HEADERS: " + member.filename + ": " + ",".join(missing))
        patch_col = norm_to_actual.get("patch")
        year_col = norm_to_actual.get("year")
        dna_col = norm_to_actual.get("dna") or norm_to_actual.get("id")
        for row in reader:
            result["rows"] += 1
            if result["rows"] > max_rows:
                raise ValueError("STOP_RESOURCE_ROWS_OVER_LIMIT: " + member.filename)
            year = str(row.get(year_col, "") or "").strip() if year_col else ""
            patch = str(row.get(patch_col, "") or "").strip() if patch_col else ""
            dna = str(row.get(dna_col, "") or "").strip() if dna_col else ""
            if year:
                try:
                    years.add(int(float(year)))
                except (ValueError, OverflowError):
                    pass
            if patch_col and year_col:
                if patch and year:
                    pair = (patch, year)
                    if pair in patch_year:
                        repeated_patch_year += 1
                    patch_year.add(pair)
                else:
                    missing_patch_or_year += 1
            if dna_col and year_col:
                if dna and year:
                    pair = (dna, year)
                    if pair in ids_year:
                        repeated_dna_year += 1
                    ids_year.add(pair)
                else:
                    missing_id_or_year += 1
    result.update({
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "distinct_patch_year": len(patch_year),
        "duplicate_patch_year_rows": repeated_patch_year,
        "rows_missing_patch_or_year": missing_patch_or_year,
        "distinct_individual_id_year": len(ids_year),
        "duplicate_individual_id_year_rows": repeated_dna_year,
        "rows_missing_individual_id_or_year": missing_id_or_year,
        "readme_expected_rows": expected["expected_rows_publisher_readme"],
        "matches_readme_row_count": result["rows"] == expected["expected_rows_publisher_readme"],
    })
    result["_patch_year_keys"] = patch_year
    result["_individual_id_year_keys"] = ids_year
    return result


def qualify(protocol: dict, output: Path) -> dict:
    source = protocol["source"]
    limits = protocol["limits"]
    receipt: dict = {
        "schema_version": 1,
        "gate": "source_only_metadata_row_and_join_qualification",
        "source_doi": source["doi"],
        "pinned_file_id": source["file_stream_id"],
        "source_version_date": source["version_date"],
        "scored_ecological_outcomes": 0,
        "model_fits": 0,
        "new_eogwf_predictive_endpoints": 0,
        "status": "STOP_UNSTARTED",
    }
    try:
        request = urllib.request.Request(source["download_url"], headers={
            "User-Agent": "EOG-source-audit/1.0 (academic data qualification)",
            "Accept": "*/*",
        })
        with tempfile.TemporaryDirectory(prefix="eog_source_only_") as tmpdir:
            path = Path(tmpdir) / "source_archive.zip"
            sha = hashlib.sha256()
            total = 0
            try:
                with urllib.request.urlopen(request, timeout=limits["timeout_seconds"]) as response:
                    receipt["transport_http_status"] = getattr(response, "status", None)
                    receipt["transport_final_url"] = response.geturl()
                    with path.open("wb") as sink:
                        for chunk in iter(lambda: response.read(1024 * 1024), b""):
                            total += len(chunk)
                            if total > limits["archive_bytes_max"]:
                                raise ValueError("STOP_ARCHIVE_OVER_BYTE_LIMIT")
                            sha.update(chunk)
                            sink.write(chunk)
            except urllib.error.HTTPError as exc:
                receipt.update({"status": "STOP_TRANSPORT_HTTP_" + str(exc.code), "transport_http_status": exc.code})
                return _write_receipt(output, receipt)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                receipt.update({"status": "STOP_TRANSPORT_NETWORK", "transport_error_type": type(exc).__name__})
                return _write_receipt(output, receipt)
            receipt.update({"downloaded_bytes": total, "archive_sha256": sha.hexdigest()})
            if not zipfile.is_zipfile(path):
                raise ValueError("STOP_DOWNLOADED_CONTENT_NOT_ZIP")
            with zipfile.ZipFile(path) as z:
                files = tuple(info for info in z.infolist() if not info.is_dir())
                if len(files) > limits["archive_members_max"]:
                    raise ValueError("STOP_ARCHIVE_TOO_MANY_MEMBERS")
                if sum(info.file_size for info in files) > limits["uncompressed_bytes_max"]:
                    raise ValueError("STOP_ARCHIVE_UNCOMPRESSED_BUDGET")
                if any(info.filename.startswith("/") or
                       ".." in info.filename.replace("\\", "/").split("/")
                       for info in files):
                    raise ValueError("STOP_ARCHIVE_UNSAFE_MEMBER_PATH")
                selected = {}
                for basename, expected in protocol["expected_tables"].items():
                    matches = [info for info in files if info.filename.replace("\\", "/").endswith("/" + basename) or info.filename == basename]
                    if len(matches) != 1:
                        raise ValueError("STOP_ARCHIVE_MISSING_OR_DUPLICATE_TABLE:" + basename)
                    selected[basename] = _read_member(z, matches[0], expected, limits["table_rows_max"])
                # No response outcome or genetic values enter any join calculation.
                survey = selected["fall_survey_2004_2013.csv"]["_patch_year_keys"]
                snp = selected["raw.snps.csv"]["_patch_year_keys"]
                families = selected["colonyFamilies.csv"]["_individual_id_year_keys"]
                snpids = selected["raw.snps.csv"]["_individual_id_year_keys"]
                receipt["join_checks"] = {
                    "survey_distinct_patch_year": len(survey),
                    "genotypes_distinct_patch_year": len(snp),
                    "genotype_patch_year_overlap_with_survey": len(snp & survey),
                    "genotype_patch_year_unmatched": len(snp - survey),
                    "genotype_distinct_dna_year": len(snpids),
                    "family_distinct_dna_year": len(families),
                    "genotype_dna_year_overlap_with_family": len(snpids & families),
                    "genotype_dna_year_unmatched": len(snpids - families),
                }
                for row in selected.values():
                    row.pop("_patch_year_keys", None)
                    row.pop("_individual_id_year_keys", None)
                receipt["tables"] = selected
                counts_match = all(row["matches_readme_row_count"] for row in selected.values())
                headers_match = all(not row["missing_required_headers"] for row in selected.values())
                if not counts_match or not headers_match:
                    receipt["status"] = "STOP_README_SCHEMA_OR_COUNT_DISAGREEMENT"
                elif not (snp & survey) or not (snpids & families):
                    receipt["status"] = "STOP_NO_VALID_ID_JOIN"
                else:
                    receipt["status"] = "SOURCE_STRUCTURE_JOIN_POSSIBLE_NOT_ECOLOGICAL_READY"
                receipt["biological_inference"] = (
                    "NOT_EVALUATED: joining source table keys does not establish source identity, "
                    "movement origin, dispersal calibration or independent future response"
                )
                return _write_receipt(output, receipt)
    except (ValueError, zipfile.BadZipFile, UnicodeError, csv.Error) as exc:
        receipt["status"] = str(exc) if str(exc).startswith("STOP_") else "STOP_SOURCE_SCHEMA_ERROR"
        receipt["error_type"] = type(exc).__name__
        return _write_receipt(output, receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("validation/glanville_minrelax_source_gate_v1/protocol_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("results/glanville_minrelax_source_gate_v1/receipt.json"))
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    qualify(protocol, args.output)


if __name__ == "__main__":
    main()
