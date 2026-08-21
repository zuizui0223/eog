from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("validation/giant_kelp_complementarity")
OUT = Path("build/giant_kelp_process_audit")
UA = "eog-giant-kelp-process-audit/1.1"


def resolve_location(pid: str, transport: list[dict]) -> str:
    encoded = urllib.parse.quote(pid, safe="")
    resolve_url = f"https://cn.dataone.org/cn/v2/resolve/{encoded}"

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(
        resolve_url,
        headers={"User-Agent": UA, "Accept": "application/xml,text/xml,*/*"},
    )
    try:
        with opener.open(req, timeout=60) as response:
            location = response.headers.get("Location")
            status = getattr(response, "status", None) or response.getcode()
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers.get("Location")
        status = exc.code
    transport.append(
        {
            "pid": pid,
            "resolve_url": resolve_url,
            "resolve_status": status,
            "location": location,
        }
    )
    if not location:
        raise RuntimeError(f"DataONE resolve exposed no location for {pid!r}")
    url = urllib.parse.urljoin(resolve_url, location)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or "/object/" not in parsed.path:
        raise RuntimeError(f"unsafe resolved DataONE object URL: {url!r}")
    return url


def download(
    pid: str,
    expected_size: int,
    expected_sha1: str,
    stem: str,
    transport: list[dict],
) -> Path:
    url = resolve_location(pid, transport)
    path = Path(tempfile.gettempdir()) / f"{stem}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    digest = hashlib.sha1()
    size = 0
    with urllib.request.urlopen(req, timeout=180) as response, path.open("wb") as handle:
        status = getattr(response, "status", None) or response.getcode()
        final = str(response.geturl())
        content_type = str(response.headers.get("Content-Type", ""))
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            handle.write(chunk)
    transport.append(
        {
            "pid": pid,
            "object_url": url,
            "final": final,
            "status": status,
            "content_type": content_type,
            "bytes": size,
            "sha1": digest.hexdigest(),
        }
    )
    if status != 200:
        raise RuntimeError(f"object status {status} for {pid}")
    if size != expected_size:
        raise RuntimeError(f"object size drift for {stem}: {size} != {expected_size}")
    if digest.hexdigest().casefold() != expected_sha1.casefold():
        raise RuntimeError(
            f"object checksum drift for {stem}: {digest.hexdigest()} != {expected_sha1}"
        )
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads((ROOT / "process_object_contract.json").read_text(encoding="utf-8"))
    process = contract["process_entity"]
    mapping = contract["patch_mapping_gate"]
    transport: list[dict] = []

    geometry_path = download(
        mapping["geometry_data_pid"],
        7_530_268,
        mapping["geometry_sha1"],
        "giant_kelp_geometry",
        transport,
    )
    geometry_patches: set[str] = set()
    with geometry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_geometry_fields = ("patch_number", "pixel_latitude", "pixel_longitude")
        if tuple(reader.fieldnames or ()) != expected_geometry_fields:
            raise RuntimeError(f"geometry schema drift: {reader.fieldnames!r}")
        for row_no, row in enumerate(reader, 2):
            patch = str(row["patch_number"]).strip()
            if not patch:
                raise RuntimeError(f"blank geometry patch at row {row_no}")
            geometry_patches.add(patch)
    if len(geometry_patches) != int(mapping["expected_geometry_patch_count"]):
        raise RuntimeError(f"geometry patch count drift: {len(geometry_patches)}")
    patch_index = {patch: idx for idx, patch in enumerate(sorted(geometry_patches))}

    process_path = download(
        process["data_pid"],
        int(process["size_bytes"]),
        process["checksum"],
        "giant_kelp_process",
        transport,
    )
    required = tuple(process["required_columns"])
    expected_periods = tuple(contract["period_order"])
    expected_period_set = set(expected_periods)
    period_index = {period: idx for idx, period in enumerate(expected_periods)}
    n = len(patch_index)

    source_ids: set[str] = set()
    destination_ids: set[str] = set()
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
            src = str(row["source_patch"]).strip()
            dst = str(row["destination_patch"]).strip()
            year_token = str(row["year"]).strip()
            semester_token = str(row["semester"]).strip()
            time_token = str(row["dispersal_time"]).strip()
            if not src or not dst:
                raise RuntimeError(f"blank process patch ID at row {row_no}")
            if not int_re.fullmatch(year_token):
                raise RuntimeError(f"non-strict year token at row {row_no}: {year_token!r}")
            if not int_re.fullmatch(semester_token):
                raise RuntimeError(
                    f"non-strict semester token at row {row_no}: {semester_token!r}"
                )
            year = int(year_token)
            semester = int(semester_token)
            if not 1996 <= year <= 2006 or semester not in (1, 2):
                raise RuntimeError(
                    f"out-of-contract period at row {row_no}: {year_token!r}/{semester_token!r}"
                )
            try:
                dispersal_time = float(time_token)
            except Exception as exc:
                raise RuntimeError(
                    f"invalid dispersal time at row {row_no}: {time_token!r}"
                ) from exc
            if not math.isfinite(dispersal_time) or dispersal_time < 0:
                raise RuntimeError(
                    f"nonfinite/negative dispersal time at row {row_no}: {time_token!r}"
                )
            if src not in patch_index:
                raise RuntimeError(f"unknown source patch at row {row_no}: {src!r}")
            if dst not in patch_index:
                raise RuntimeError(f"unknown destination patch at row {row_no}: {dst!r}")

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
                dispersal_time
                if stats["min_time"] is None
                else min(stats["min_time"], dispersal_time)
            )
            stats["max_time"] = (
                dispersal_time
                if stats["max_time"] is None
                else max(stats["max_time"], dispersal_time)
            )

    union_ids = source_ids | destination_ids
    period_pass = periods == expected_period_set
    source_subset = source_ids <= geometry_patches
    destination_subset = destination_ids <= geometry_patches
    union_equal = union_ids == geometry_patches
    mapping_pass = bool(period_pass and source_subset and destination_subset and union_equal)
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
        "candidate": contract["candidate"],
        "eml_to_physical_header_mapping": process["eml_to_physical_header_mapping"],
        "geometry_patch_count": len(geometry_patches),
        "process_row_count": row_count,
        "source_patch_count": len(source_ids),
        "destination_patch_count": len(destination_ids),
        "union_patch_count": len(union_ids),
        "source_subset_of_geometry": source_subset,
        "destination_subset_of_geometry": destination_subset,
        "union_equals_geometry": union_equal,
        "observed_period_count": len(periods),
        "observed_periods": sorted(periods, key=lambda value: period_index[value]),
        "expected_periods": list(expected_periods),
        "period_universe_pass": period_pass,
        "unique_source_destination_period_rows": True,
        "per_period": compact_period,
        "geometry_object_bytes_opened": True,
        "process_object_bytes_opened": True,
        "response_package_bytes_opened": False,
        "response_rows_opened": False,
        "transport": transport,
        "process_feature_boundary": contract["process_feature_boundary"],
        "next": (
            "freeze Layer A/B, shared conventional/process feature set, same learner, count gate and smoke before response access"
            if mapping_pass
            else "do not open response; stop or exclude process input only according to the prospectively frozen contract without retuning"
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
