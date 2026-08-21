from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

from audit_giant_kelp_process_mapping import download

ROOT = Path("validation/giant_kelp_complementarity")
OUT = Path("build/giant_kelp_process_audit")


def compile_pattern(text: str) -> re.Pattern[str]:
    pattern = re.compile(text)
    if pattern.groups != 1:
        raise ValueError(f"patch identity pattern must contain exactly one capture group: {text!r}")
    return pattern


def canonicalize(raw: object, pattern: re.Pattern[str], label: str) -> str:
    token = str(raw).strip()
    match = pattern.fullmatch(token)
    if match is None:
        raise RuntimeError(f"{label} token does not match frozen identity pattern: {token!r}")
    digits = match.group(1)
    if not re.fullmatch(r"[1-9][0-9]*", digits):
        raise RuntimeError(f"{label} capture is not a positive canonical integer token: {digits!r}")
    canonical = str(int(digits))
    if canonical != digits:
        raise RuntimeError(f"{label} uses a non-canonical integer representation: {digits!r}")
    return canonical


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    process_contract = json.loads((ROOT / "process_object_contract.json").read_text(encoding="utf-8"))
    geometry_contract = json.loads((ROOT / "southern_geometry_object_contract.json").read_text(encoding="utf-8"))
    identity_contract = json.loads((ROOT / "patch_identity_contract.json").read_text(encoding="utf-8"))
    process = process_contract["process_entity"]
    mapping = process_contract["patch_mapping_gate"]
    geometry = geometry_contract["southern_geometry_entity"]
    geometry_pattern = compile_pattern(identity_contract["geometry_raw_pattern"])
    process_pattern = compile_pattern(identity_contract["process_raw_pattern"])
    transport: list[dict] = []

    geometry_path = download(
        geometry["data_pid"],
        int(geometry["size_bytes"]),
        geometry["checksum"],
        "giant_kelp_geometry_mapping_v2",
        transport,
    )
    geometry_raw_to_canonical: dict[str, str] = {}
    geometry_canonical_to_raw: dict[str, str] = {}
    with geometry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != ("patch_number", "pixel_latitude", "pixel_longitude"):
            raise RuntimeError(f"geometry schema drift: {reader.fieldnames!r}")
        for row_no, row in enumerate(reader, 2):
            raw = str(row["patch_number"]).strip()
            canonical = canonicalize(raw, geometry_pattern, f"geometry row {row_no}")
            prior = geometry_raw_to_canonical.setdefault(raw, canonical)
            if prior != canonical:
                raise RuntimeError(f"geometry raw ID maps inconsistently: {raw!r}")
            other = geometry_canonical_to_raw.setdefault(canonical, raw)
            if other != raw:
                raise RuntimeError(
                    f"geometry canonical ID collision: {canonical!r} from {other!r} and {raw!r}"
                )

    expected_count = int(identity_contract["expected_patch_count"])
    geometry_ids = set(geometry_canonical_to_raw)
    if len(geometry_ids) != expected_count:
        raise RuntimeError(f"geometry canonical patch count drift: {len(geometry_ids)} != {expected_count}")
    patch_index = {patch: idx for idx, patch in enumerate(sorted(geometry_ids, key=int))}

    process_path = download(
        process["data_pid"],
        int(process["size_bytes"]),
        process["checksum"],
        "giant_kelp_process_mapping_v2",
        transport,
    )
    required = tuple(process["required_columns"])
    expected_periods = tuple(process_contract["period_order"])
    expected_period_set = set(expected_periods)
    period_index = {period: idx for idx, period in enumerate(expected_periods)}
    n = len(patch_index)
    source_ids: set[str] = set()
    destination_ids: set[str] = set()
    raw_source_ids: set[str] = set()
    raw_destination_ids: set[str] = set()
    periods: set[str] = set()
    seen: set[int] = set()
    per_period = {
        period: {
            "rows": 0,
            "min_time": None,
            "max_time": None,
            "source_ids": set(),
            "destination_ids": set(),
        }
        for period in expected_periods
    }
    row_count = 0
    int_re = re.compile(r"^[0-9]+$")

    with process_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        if fields != required:
            raise RuntimeError(f"process schema drift: {fields!r} != {required!r}")
        for row_no, row in enumerate(reader, 2):
            row_count += 1
            raw_src = str(row["source_patch"]).strip()
            raw_dst = str(row["destination_patch"]).strip()
            src = canonicalize(raw_src, process_pattern, f"process source row {row_no}")
            dst = canonicalize(raw_dst, process_pattern, f"process destination row {row_no}")
            raw_source_ids.add(raw_src)
            raw_destination_ids.add(raw_dst)
            year_token = str(row["year"]).strip()
            semester_token = str(row["semester"]).strip()
            time_token = str(row["dispersal_time"]).strip()
            if not int_re.fullmatch(year_token):
                raise RuntimeError(f"non-strict year token at row {row_no}: {year_token!r}")
            if not int_re.fullmatch(semester_token):
                raise RuntimeError(f"non-strict semester token at row {row_no}: {semester_token!r}")
            year = int(year_token)
            semester = int(semester_token)
            if not 1996 <= year <= 2006 or semester not in (1, 2):
                raise RuntimeError(f"out-of-contract period at row {row_no}: {year}/{semester}")
            try:
                dispersal_time = float(time_token)
            except Exception as exc:
                raise RuntimeError(f"invalid dispersal time at row {row_no}: {time_token!r}") from exc
            if not math.isfinite(dispersal_time) or dispersal_time < 0:
                raise RuntimeError(f"nonfinite/negative dispersal time at row {row_no}: {time_token!r}")
            if src not in patch_index:
                raise RuntimeError(f"canonical source patch not in geometry at row {row_no}: {src!r}")
            if dst not in patch_index:
                raise RuntimeError(f"canonical destination patch not in geometry at row {row_no}: {dst!r}")
            period = f"{year}-H{semester}"
            if period not in expected_period_set:
                raise RuntimeError(f"unexpected period at row {row_no}: {period}")
            key = period_index[period] * (n * n) + patch_index[src] * n + patch_index[dst]
            if key in seen:
                raise RuntimeError(
                    f"duplicate source-destination-period at row {row_no}: {(src, dst, period)!r}"
                )
            seen.add(key)
            source_ids.add(src)
            destination_ids.add(dst)
            periods.add(period)
            stats = per_period[period]
            stats["rows"] += 1
            stats["source_ids"].add(src)
            stats["destination_ids"].add(dst)
            stats["min_time"] = (
                dispersal_time if stats["min_time"] is None else min(stats["min_time"], dispersal_time)
            )
            stats["max_time"] = (
                dispersal_time if stats["max_time"] is None else max(stats["max_time"], dispersal_time)
            )

    process_union = source_ids | destination_ids
    source_subset = source_ids <= geometry_ids
    destination_subset = destination_ids <= geometry_ids
    union_equal = process_union == geometry_ids
    period_pass = periods == expected_period_set
    mapping_pass = bool(
        len(geometry_ids) == expected_count
        and len(process_union) == expected_count
        and source_subset
        and destination_subset
        and union_equal
        and period_pass
    )
    compact_period = {
        period: {
            "rows": stats["rows"],
            "source_patch_count": len(stats["source_ids"]),
            "destination_patch_count": len(stats["destination_ids"]),
            "min_time": stats["min_time"],
            "max_time": stats["max_time"],
        }
        for period, stats in per_period.items()
    }
    payload = {
        "status": "process_geometry_mapping_pass" if mapping_pass else "process_geometry_mapping_stop",
        "candidate": process_contract["candidate"],
        "patch_identity_contract_fingerprint": hashlib.sha256(
            (ROOT / "patch_identity_contract.json").read_bytes()
        ).hexdigest(),
        "geometry_raw_pattern": identity_contract["geometry_raw_pattern"],
        "process_raw_pattern": identity_contract["process_raw_pattern"],
        "canonical_node_id_rule": identity_contract["canonical_node_id"],
        "geometry_raw_patch_count": len(geometry_raw_to_canonical),
        "geometry_canonical_patch_count": len(geometry_ids),
        "process_raw_source_patch_count": len(raw_source_ids),
        "process_raw_destination_patch_count": len(raw_destination_ids),
        "process_canonical_source_patch_count": len(source_ids),
        "process_canonical_destination_patch_count": len(destination_ids),
        "process_canonical_union_patch_count": len(process_union),
        "source_subset_of_geometry": source_subset,
        "destination_subset_of_geometry": destination_subset,
        "union_equals_geometry": union_equal,
        "process_row_count": row_count,
        "observed_period_count": len(periods),
        "observed_periods": sorted(periods, key=lambda value: period_index[value]),
        "period_universe_pass": period_pass,
        "unique_source_destination_period_rows": True,
        "per_period": compact_period,
        "geometry_relabeling_is_bijective": len(geometry_raw_to_canonical) == len(geometry_ids),
        "geometry_object_bytes_opened": True,
        "process_object_bytes_opened": True,
        "response_package_bytes_opened": False,
        "response_rows_opened": False,
        "transport": transport,
        "next": (
            "freeze the paired-complementarity prediction contract and smoke before response access"
            if mapping_pass
            else "stop without opening response; do not add patch aliases or change the node universe"
        ),
    }
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    (OUT / "process_mapping_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not mapping_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
