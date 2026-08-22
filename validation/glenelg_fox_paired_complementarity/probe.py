#!/usr/bin/env python3
"""Response-blind transport, registry, and geometry probe for Glenelg Ark.

Only ZIP metadata and the two declared non-response members are read from
``data.clean.zip``.  The fox detection member is located from the central
directory so byte non-overlap can be audited, but its local header and payload
are never requested by this program.
"""
from __future__ import annotations

import argparse
import binascii
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
from urllib.parse import urlparse
import urllib.request
import zlib


ARCHIVE_URL = "https://datadryad.org/downloads/file_stream/4657362"
DATASET_DOI = "10.5061/dryad.80gb5mm4h"
USER_AGENT = "eog-glenelg-response-blind-probe/1.0"
SAFE_BASENAMES = (
    "sites_monitoring_glenelg.csv",
    "env_cov_allsites_glenelg_scaled_updated.csv",
)
RESPONSE_BASENAME = "stacked_weekly_PA_glenelg_combined_fox.csv"
LCC_TARGETS = (0.25, 0.50, 0.75, 0.90)
PUBLISHED_RADII_KM = (1.15, 2.30, 4.60, 6.90)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def range_get(
    start: int,
    end: int,
    ledger: list[dict[str, object]],
    role: str,
) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        status = getattr(response, "status", None) or response.getcode()
        body = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        final_url = response.geturl()
    expected = end - start + 1
    if status != 206:
        raise RuntimeError(f"range request returned HTTP {status}, expected 206")
    if len(body) != expected:
        raise RuntimeError(f"range response length {len(body)} != {expected}")
    content_range = headers.get("content-range", "")
    if not content_range.startswith(f"bytes {start}-{end}/"):
        raise RuntimeError(f"unexpected Content-Range: {content_range!r}")
    ledger.append(
        {
            "role": role,
            "start": start,
            "end": end,
            "bytes": len(body),
            "status": status,
            "content_range": content_range,
            "final_host": urlparse(final_url).netloc,
        }
    )
    return body, headers


def archive_size(ledger: list[dict[str, object]]) -> tuple[int, dict[str, str]]:
    body, headers = range_get(0, 0, ledger, "archive_size_probe")
    if len(body) != 1:
        raise RuntimeError("one-byte size probe returned the wrong length")
    match = re.fullmatch(r"bytes 0-0/(\d+)", headers.get("content-range", ""))
    if match is None:
        raise RuntimeError("archive size is absent from Content-Range")
    return int(match.group(1)), headers


def central_directory(
    size: int,
    ledger: list[dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    tail_size = min(size, 65_557)
    tail_start = size - tail_size
    tail, _ = range_get(tail_start, size - 1, ledger, "zip_eocd_tail")
    marker = b"PK\x05\x06"
    relative = tail.rfind(marker)
    if relative < 0:
        raise RuntimeError("ZIP end-of-central-directory record was not found")
    if relative + 22 > len(tail):
        raise RuntimeError("truncated ZIP end-of-central-directory record")
    fields = struct.unpack_from("<4s4H2IH", tail, relative)
    disk_number, cd_disk, disk_records, total_records = fields[1:5]
    cd_size, cd_offset, comment_len = fields[5:8]
    if disk_number != 0 or cd_disk != 0 or disk_records != total_records:
        raise RuntimeError("multi-disk ZIP archives are not supported")
    if relative + 22 + comment_len != len(tail):
        raise RuntimeError("ZIP EOCD/comment does not terminate at archive end")
    if cd_offset + cd_size > tail_start:
        begin = cd_offset - tail_start
        if begin < 0:
            raise RuntimeError("central-directory partial overlap is unsupported")
        raw = tail[begin : begin + cd_size]
        ledger.append(
            {
                "role": "zip_central_directory_reused_from_tail",
                "start": cd_offset,
                "end": cd_offset + cd_size - 1,
                "bytes": cd_size,
                "status": 206,
            }
        )
    else:
        raw, _ = range_get(
            cd_offset,
            cd_offset + cd_size - 1,
            ledger,
            "zip_central_directory",
        )
    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(raw):
        if cursor + 46 > len(raw):
            raise RuntimeError("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", raw, cursor)
        if values[0] != b"PK\x01\x02":
            raise RuntimeError(f"invalid central-directory signature at {cursor}")
        flags = values[3]
        method = values[4]
        crc32 = values[7]
        compressed_size = values[8]
        uncompressed_size = values[9]
        name_len, extra_len, member_comment_len = values[10:13]
        local_offset = values[16]
        end = cursor + 46 + name_len + extra_len + member_comment_len
        if end > len(raw):
            raise RuntimeError("central-directory variable fields are truncated")
        name_bytes = raw[cursor + 46 : cursor + 46 + name_len]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = name_bytes.decode(encoding)
        members.append(
            {
                "name": name,
                "basename": name.rsplit("/", 1)[-1],
                "flags": flags,
                "method": method,
                "crc32": f"{crc32:08x}",
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "local_header_offset": local_offset,
            }
        )
        cursor = end
    if cursor != len(raw) or len(members) != total_records:
        raise RuntimeError(
            f"central-directory count mismatch: {len(members)} != {total_records}"
        )
    identity = {
        "archive_bytes": size,
        "central_directory_offset": cd_offset,
        "central_directory_bytes": cd_size,
        "central_directory_sha256": hashlib.sha256(raw).hexdigest(),
        "member_count": len(members),
        "eocd_comment_bytes": comment_len,
    }
    return members, identity


def unique_member(members: list[dict[str, object]], basename: str) -> dict[str, object]:
    found = [member for member in members if member["basename"] == basename]
    if len(found) != 1:
        raise RuntimeError(f"expected one ZIP member named {basename!r}, found {len(found)}")
    return found[0]


def local_layout(
    member: dict[str, object],
    ledger: list[dict[str, object]],
    *,
    read_payload: bool,
) -> tuple[dict[str, object], bytes | None]:
    offset = int(member["local_header_offset"])
    fixed, _ = range_get(offset, offset + 29, ledger, f"local_header:{member['basename']}")
    values = struct.unpack("<4s5H3I2H", fixed)
    if values[0] != b"PK\x03\x04":
        raise RuntimeError(f"invalid local ZIP header for {member['name']}")
    method = values[3]
    name_len, extra_len = values[9], values[10]
    name_bytes, _ = range_get(
        offset + 30,
        offset + 30 + name_len - 1,
        ledger,
        f"local_name:{member['basename']}",
    )
    encoding = "utf-8" if int(member["flags"]) & 0x800 else "cp437"
    local_name = name_bytes.decode(encoding)
    if local_name != member["name"]:
        raise RuntimeError(f"local/central member name mismatch for {member['name']}")
    if method != int(member["method"]):
        raise RuntimeError(f"local/central compression mismatch for {member['name']}")
    data_start = offset + 30 + name_len + extra_len
    data_end = data_start + int(member["compressed_size"]) - 1
    layout = {
        **member,
        "data_start": data_start,
        "data_end": data_end,
        "member_interval_start": offset,
        "member_interval_end": data_end,
    }
    if not read_payload:
        return layout, None
    compressed, _ = range_get(
        data_start,
        data_end,
        ledger,
        f"safe_payload:{member['basename']}",
    )
    if method == 8:
        payload = zlib.decompress(compressed, -15)
    elif method == 0:
        payload = compressed
    else:
        raise RuntimeError(f"unsupported ZIP compression method {method}")
    if len(payload) != int(member["uncompressed_size"]):
        raise RuntimeError(f"uncompressed size mismatch for {member['name']}")
    observed_crc = f"{binascii.crc32(payload) & 0xffffffff:08x}"
    if observed_crc != member["crc32"]:
        raise RuntimeError(f"CRC mismatch for {member['name']}")
    layout["sha256"] = hashlib.sha256(payload).hexdigest()
    return layout, payload


def csv_rows(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise RuntimeError("CSV has no header")
    header = [str(value) for value in reader.fieldnames]
    if any(not value for value in header) or len(set(header)) != len(header):
        raise RuntimeError("CSV header contains empty or duplicate names")
    rows = [dict(row) for row in reader]
    if not rows:
        raise RuntimeError("CSV has no data rows")
    return header, rows


def normalized(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def choose_column(header: list[str], aliases: tuple[str, ...], label: str) -> str:
    alias_set = {normalized(value) for value in aliases}
    found = [name for name in header if normalized(name) in alias_set]
    if len(found) != 1:
        raise RuntimeError(f"could not uniquely identify {label} column: {found}")
    return found[0]


def finite_float(value: str, label: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise RuntimeError(f"{label} is not finite")
    return result


def registry_audit(payload: bytes) -> tuple[list[tuple[str, float, float]], dict[str, object]]:
    header, rows = csv_rows(payload)
    latitude = choose_column(header, ("latitude", "lat", "y"), "latitude")
    longitude = choose_column(header, ("longitude", "lon", "long", "x"), "longitude")
    non_coordinate = [name for name in header if name not in (latitude, longitude)]
    uniqueness = {
        name: len({(row.get(name) or "").strip() for row in rows})
        for name in non_coordinate
    }
    id_candidates = [name for name in non_coordinate if uniqueness[name] == len(rows)]
    if not id_candidates:
        raise RuntimeError("site registry has no unique non-coordinate identifier")
    preferred = [
        name
        for name in id_candidates
        if normalized(name) in {"site", "siteid", "station", "stationid", "pointid"}
    ]
    site_id = preferred[0] if len(preferred) == 1 else id_candidates[0]
    records: list[tuple[str, float, float]] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, start=2):
        identifier = (row.get(site_id) or "").strip()
        if not identifier or identifier in seen:
            raise RuntimeError(f"empty/duplicate site identifier at row {number}")
        seen.add(identifier)
        lat = finite_float(row.get(latitude) or "", f"latitude row {number}")
        lon = finite_float(row.get(longitude) or "", f"longitude row {number}")
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise RuntimeError(f"coordinate out of range at row {number}")
        records.append((identifier, lat, lon))
    if len(records) != 240:
        raise RuntimeError(f"fixed monitoring registry row count {len(records)} != 240")
    return records, {
        "header": header,
        "rows": len(rows),
        "site_id_column": site_id,
        "latitude_column": latitude,
        "longitude_column": longitude,
        "unique_counts": uniqueness,
        "site_ids_sha256": canonical_sha256(sorted(seen)),
        "ordered_registry_sha256": canonical_sha256(records),
    }


def availability_audit(payload: bytes, registry_ids: set[str]) -> dict[str, object]:
    header, rows = csv_rows(payload)
    station_year = choose_column(header, ("station_year", "stationyear"), "station-year")
    data_source = choose_column(header, ("data_source", "datasource"), "data source")
    latitude = choose_column(header, ("latitude", "lat"), "latitude")
    longitude = choose_column(header, ("longitude", "lon", "long"), "longitude")
    source_counts: dict[str, int] = {}
    for row in rows:
        value = (row.get(data_source) or "").strip()
        source_counts[value] = source_counts.get(value, 0) + 1
    matching_sources = [
        value for value in source_counts if normalized(value) == "glenelgark"
    ]
    if len(matching_sources) != 1:
        raise RuntimeError(f"could not uniquely identify Glenelg Ark rows: {matching_sources}")
    source_value = matching_sources[0]
    selected = [row for row in rows if (row.get(data_source) or "").strip() == source_value]
    station_year_values = [(row.get(station_year) or "").strip() for row in selected]
    if any(not value for value in station_year_values):
        raise RuntimeError("Glenelg Ark availability has an empty station-year")
    if len(set(station_year_values)) != len(station_year_values):
        raise RuntimeError("Glenelg Ark availability has duplicate station-years")
    parsed: list[tuple[str, int]] = []
    unparsed: list[str] = []
    for value in station_year_values:
        match = re.search(r"(?:^|[_ .-])((?:19|20)\d{2})$", value)
        if match is None:
            unparsed.append(value)
            continue
        year = int(match.group(1))
        station = value[: match.start(1)].rstrip("_ .-")
        parsed.append((station, year))
    if unparsed:
        raise RuntimeError(f"station-year suffix parsing failed for {unparsed[:5]}")
    years = sorted({year for _, year in parsed})
    stations = {station for station, _ in parsed}
    if years != list(range(2013, 2020)):
        raise RuntimeError(f"Glenelg Ark years {years} != 2013..2019")
    # Registry aliases are audited exactly but are not repaired in this probe.  The
    # final contract may proceed only if one published identifier transform is
    # frozen and proves a complete one-to-one join.
    exact_join = stations == registry_ids
    by_year = {year: sum(observed_year == year for _, observed_year in parsed) for year in years}
    coordinates = [
        (
            finite_float(row.get(latitude) or "", "availability latitude"),
            finite_float(row.get(longitude) or "", "availability longitude"),
        )
        for row in selected
    ]
    return {
        "header": header,
        "rows_all_sources": len(rows),
        "data_source_counts": source_counts,
        "glenelg_ark_source_token": source_value,
        "glenelg_ark_site_year_rows": len(selected),
        "years": years,
        "site_years_by_year": by_year,
        "station_count": len(stations),
        "station_ids_sha256": canonical_sha256(sorted(stations)),
        "registry_exact_identifier_join": exact_join,
        "registry_only_identifiers": sorted(registry_ids - stations)[:20],
        "availability_only_identifiers": sorted(stations - registry_ids)[:20],
        "station_year_column": station_year,
        "data_source_column": data_source,
        "latitude_column": latitude,
        "longitude_column": longitude,
        "coordinates_sha256": canonical_sha256(coordinates),
    }


def haversine_km(first: tuple[float, float], second: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, first)
    lat2, lon2 = map(math.radians, second)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * 6371.0088 * math.asin(min(1.0, math.sqrt(value)))


def graph_stats(n: int, edges: list[tuple[float, int, int]], threshold: float) -> dict[str, object]:
    parent = list(range(n))
    size = [1] * n
    degree = [0] * n

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            return
        if size[root_left] < size[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        size[root_left] += size[root_right]

    edge_count = 0
    for distance, left, right in edges:
        if distance > threshold + 1e-12:
            break
        union(left, right)
        degree[left] += 1
        degree[right] += 1
        edge_count += 1
    components: dict[int, int] = {}
    for node in range(n):
        root = find(node)
        components[root] = components.get(root, 0) + 1
    largest = max(components.values())
    return {
        "threshold_km": threshold,
        "edge_count": edge_count,
        "component_count": len(components),
        "largest_component_nodes": largest,
        "largest_component_fraction": largest / n,
        "isolated_nodes": sum(value == 0 for value in degree),
        "isolated_fraction": sum(value == 0 for value in degree) / n,
    }


def geometry_audit(registry: list[tuple[str, float, float]]) -> dict[str, object]:
    edges: list[tuple[float, int, int]] = []
    for left in range(len(registry)):
        for right in range(left + 1, len(registry)):
            distance = haversine_km(registry[left][1:], registry[right][1:])
            if distance <= 0:
                raise RuntimeError("registry contains co-located distinct site identifiers")
            edges.append((distance, left, right))
    edges.sort()
    candidate_distances = sorted({distance for distance, _, _ in edges})
    lcc_rows: list[dict[str, object]] = []
    for target in LCC_TARGETS:
        chosen: dict[str, object] | None = None
        for distance in candidate_distances:
            stats = graph_stats(len(registry), edges, distance)
            if float(stats["largest_component_fraction"]) + 1e-12 >= target:
                chosen = stats
                break
        if chosen is None:
            raise RuntimeError(f"could not attain LCC target {target}")
        chosen = {"target_fraction": target, **chosen}
        lcc_rows.append(chosen)
    thresholds = [round(float(row["threshold_km"]), 12) for row in lcc_rows]
    published_rows = [graph_stats(len(registry), edges, radius) for radius in PUBLISHED_RADII_KM]
    return {
        "distance_metric": "haversine_km_earth_radius_6371.0088",
        "pair_count": len(edges),
        "minimum_distance_km": edges[0][0],
        "maximum_distance_km": edges[-1][0],
        "lcc_target_rows": lcc_rows,
        "distinct_lcc_threshold_count": len(set(thresholds)),
        "lcc_thresholds_nested_nondecreasing": thresholds == sorted(thresholds),
        "published_fox_radius_rows": published_rows,
        "distance_edges_sha256": canonical_sha256(
            [(round(distance, 12), left, right) for distance, left, right in edges]
        ),
    }


def intervals_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return max(left[0], right[0]) <= min(left[1], right[1])


def run(output: Path) -> dict[str, object]:
    ledger: list[dict[str, object]] = []
    archive_bytes, first_headers = archive_size(ledger)
    members, archive_identity = central_directory(archive_bytes, ledger)
    safe_members = {name: unique_member(members, name) for name in SAFE_BASENAMES}
    response_member = unique_member(members, RESPONSE_BASENAME)

    # The response interval is computed exclusively from central-directory metadata.
    # Its local header is deliberately not requested.
    response_start = int(response_member["local_header_offset"])
    later_offsets = sorted(
        int(member["local_header_offset"])
        for member in members
        if int(member["local_header_offset"]) > response_start
    )
    response_interval_end = (later_offsets[0] - 1) if later_offsets else int(
        archive_identity["central_directory_offset"]
    ) - 1
    response_interval = (response_start, response_interval_end)

    payloads: dict[str, bytes] = {}
    safe_layouts: dict[str, dict[str, object]] = {}
    for basename, member in safe_members.items():
        layout, payload = local_layout(member, ledger, read_payload=True)
        if payload is None:
            raise AssertionError("safe member payload was not returned")
        safe_layouts[basename] = layout
        payloads[basename] = payload

    forbidden_roles = [entry for entry in ledger if str(entry["role"]).startswith("response")]
    overlapping_requests = [
        entry
        for entry in ledger
        if intervals_overlap(
            (int(entry["start"]), int(entry["end"])), response_interval
        )
    ]
    if forbidden_roles or overlapping_requests:
        raise RuntimeError("a response-member byte range was requested during the probe")

    registry, registry_result = registry_audit(payloads[SAFE_BASENAMES[0]])
    availability = availability_audit(payloads[SAFE_BASENAMES[1]], {row[0] for row in registry})
    geometry = geometry_audit(registry)

    result: dict[str, object] = {
        "attempt_id": "glenelg_fox_paired_complementarity_v1",
        "stage": "response_blind_transport_registry_geometry_probe",
        "status": "probe_pass",
        "dataset_doi": DATASET_DOI,
        "archive_url": ARCHIVE_URL,
        "archive_identity": {
            **archive_identity,
            "etag": first_headers.get("etag"),
            "last_modified": first_headers.get("last-modified"),
        },
        "central_directory_member_names": [member["name"] for member in members],
        "safe_member_layouts": safe_layouts,
        "response_member_central_directory_only": {
            **response_member,
            "conservative_interval_start": response_interval[0],
            "conservative_interval_end": response_interval[1],
            "local_header_opened": False,
            "payload_opened": False,
        },
        "range_ledger": ledger,
        "response_interval_overlap_count": len(overlapping_requests),
        "response_rows_opened": False,
        "response_values_opened": False,
        "registry": registry_result,
        "availability": availability,
        "geometry": geometry,
        "published_count_status": "uncertain_pre_response",
        "model_fits": 0,
        "heldout_scores": 0,
    }
    result["result_fingerprint"] = canonical_sha256(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
