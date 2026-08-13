"""Response-free Stage-1 audit for the Fiji Pheidole candidate archive.

This script may inspect ZIP member names but may open only an explicit allowlist of
population/geography metadata CSV members.  It must never read VCF, genotype, FST/WC,
clustering or migration-result member contents before a later predictor freeze.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


EXPECTED_TITLE = "Genomic and phenomic analysis of island ant community assembly"
EXPECTED_DRYAD_DOI = "10.5061/dryad.xd2547dcp"
ALLOWLIST_BASENAMES = {
    "sequencemetadata.csv",
    "global_locality_full.csv",
    "pops.csv",
    "pop.csv",
}
GEO_ID_PATTERN = re.compile(
    r"(^|[^a-z])(lat|latitude|lon|long|longitude|gps|locality|location|population|pop|egpa|species|taxon)([^a-z]|$)",
    re.IGNORECASE,
)
PROHIBITED_NAME_PATTERN = re.compile(
    r"(\.vcf(?:\.gz)?$|snp|genotyp|\bfst\b|_wc(?:\.|_|$)|weir|cockerham|structure|migration)",
    re.IGNORECASE,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _record_contains_expected_identity(record: object) -> tuple[str, bool]:
    if not isinstance(record, dict):
        raise ValueError("Zenodo record metadata must be a JSON object")
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    title = str(metadata.get("title") or record.get("title") or "")
    serialized = json.dumps(record, sort_keys=True).lower()
    return title, EXPECTED_DRYAD_DOI.lower() in serialized


def _decode_csv(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("allowlisted metadata CSV has no supported text encoding")


def _audit_csv(member_name: str, data: bytes) -> dict[str, object]:
    text, encoding = _decode_csv(data)
    sample = text[: min(len(text), 32768)]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = tuple(reader.fieldnames or ())
    rows = list(reader)
    candidate_columns = [header for header in headers if GEO_ID_PATTERN.search(header or "")]
    distinct_counts: dict[str, int] = {}
    for header in candidate_columns:
        values = {
            str(row.get(header, "")).strip()
            for row in rows
            if str(row.get(header, "")).strip()
        }
        distinct_counts[header] = len(values)
    lower_headers = [header.lower() for header in headers]
    has_lat = any("lat" in header for header in lower_headers)
    has_lon = any(("lon" in header) or ("long" in header) for header in lower_headers)
    has_gps = any("gps" in header for header in lower_headers)
    has_population_identity = any(
        any(token in header for token in ("population", "pop", "egpa", "locality", "location"))
        for header in lower_headers
    )
    return {
        "member": member_name,
        "encoding": encoding,
        "delimiter": delimiter,
        "n_rows": len(rows),
        "headers": list(headers),
        "candidate_geography_identity_columns": candidate_columns,
        "candidate_distinct_counts": distinct_counts,
        "has_direct_lat_lon": bool(has_lat and has_lon),
        "has_gps_column": bool(has_gps),
        "has_population_or_locality_identity": bool(has_population_identity),
        "content_sha256": hashlib.sha256(data).hexdigest(),
    }


def audit_archive(record_json: Path, archive: Path) -> dict[str, object]:
    record = json.loads(record_json.read_text(encoding="utf-8"))
    title, has_expected_doi = _record_contains_expected_identity(record)

    member_inventory: list[dict[str, object]] = []
    allowlisted_audits: list[dict[str, object]] = []
    prohibited_members: list[str] = []
    sequence_metadata_present = False

    with zipfile.ZipFile(archive, "r") as handle:
        for info in handle.infolist():
            if info.is_dir():
                continue
            basename = PurePosixPath(info.filename).name.lower()
            member_inventory.append(
                {
                    "member": info.filename,
                    "basename": basename,
                    "uncompressed_size": int(info.file_size),
                    "compressed_size": int(info.compress_size),
                    "crc32": f"{info.CRC:08x}",
                    "allowlisted_metadata": basename in ALLOWLIST_BASENAMES,
                    "name_indicates_genetic_or_response_content": bool(
                        PROHIBITED_NAME_PATTERN.search(basename)
                    ),
                }
            )
            if PROHIBITED_NAME_PATTERN.search(basename):
                prohibited_members.append(info.filename)
            if basename == "sequencemetadata.csv":
                sequence_metadata_present = True
            if basename not in ALLOWLIST_BASENAMES:
                # Hard firewall: do not call read/open on any non-allowlisted member.
                continue
            data = handle.read(info)
            allowlisted_audits.append(_audit_csv(info.filename, data))

    population_identity_available = any(
        audit["has_population_or_locality_identity"] for audit in allowlisted_audits
    )
    direct_coordinates_available = any(
        audit["has_direct_lat_lon"] or audit["has_gps_column"]
        for audit in allowlisted_audits
    )
    locality_join_possible = (
        population_identity_available
        and any(
            PurePosixPath(str(audit["member"])).name.lower() == "global_locality_full.csv"
            for audit in allowlisted_audits
        )
    )

    checks = {
        "title_match": title.strip() == EXPECTED_TITLE,
        "dryad_doi_present_in_record_metadata": has_expected_doi,
        "archive_is_zip": zipfile.is_zipfile(archive),
        "sequence_metadata_present": sequence_metadata_present,
        "allowlisted_metadata_read": bool(allowlisted_audits),
        "population_or_locality_identity_available": population_identity_available,
        "geography_available_directly_or_via_locality_join": bool(
            direct_coordinates_available or locality_join_possible
        ),
        "genetic_member_contents_accessed": False,
    }
    admitted = all(
        value
        for key, value in checks.items()
        if key != "genetic_member_contents_accessed"
    ) and checks["genetic_member_contents_accessed"] is False

    result: dict[str, object] = {
        "status": "fiji-pheidole-pre-genetic-stage1-metadata-audit",
        "admitted": admitted,
        "zenodo_title": title,
        "expected_dryad_doi": EXPECTED_DRYAD_DOI,
        "record_json_sha256": _sha256(record_json),
        "archive_sha256": _sha256(archive),
        "archive_size_bytes": archive.stat().st_size,
        "n_archive_members": len(member_inventory),
        "n_allowlisted_metadata_members_read": len(allowlisted_audits),
        "n_genetic_or_response_named_members_inventory_only": len(prohibited_members),
        "genetic_or_response_named_members_inventory_only": sorted(prohibited_members),
        "genetic_member_contents_accessed": False,
        "checks": checks,
        "allowlisted_metadata_audits": allowlisted_audits,
        "member_inventory": member_inventory,
        "claim_boundary": (
            "Only exact-basename allowlisted geography/population metadata members were "
            "opened. Genetic/VCF/SNP/FST/WC/clustering/migration member contents were not read."
        ),
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-json", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_archive(args.record_json, args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
