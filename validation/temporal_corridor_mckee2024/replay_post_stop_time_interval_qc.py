#!/usr/bin/env python3
"""Replay McKee 2024 original 12h date-only temporal interval diagnostics.

Pair and triplet stages were independently precommitted before the respective
new computations. Read only five sparse 12h DBF fields; never read SHP
geometries or open the dense 2h holdout. Nothing identifying an individual,
an exact GPS fix/time, or any ecological route is exported. Local naive
clock arithmetic is not a certified physical elapsed time across DST.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import stat
import struct
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED


HERE = Path(__file__).resolve().parent
SHA256 = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"
SOURCE_BYTES = 1539661
RECORDS = 28953
EXPECTED_NAMES = {"GPS12hrs_Locs.shp", "GPS12hrs_Locs.shx",
                  "GPS12hrs_Locs.dbf", "GPS12hrs_Locs.prj"}
FIELDS = ("Herd", "AID", "SeasnYr", "Season", "Timstmp")
H = 45000
EPOCH = datetime(1970, 1, 1)
PAIR_PROTO = HERE / "post_stop_time_interval_identifiability_protocol_v1.json"
TRIPLE_PROTO = HERE / "post_stop_triplet_time_coherence_protocol_v1.json"
T0 = "T0_FULL_DAY_UNCERTAINTY"
T1 = "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"


def _seconds(value: datetime) -> int:
    """Naive civil-clock seconds (NOT UTC epoch or DST-corrected time)."""
    return int((value - EPOCH).total_seconds())


def _source_rows(archive: Path):
    if archive.name != "GPS12hrs_Locs.zip" or archive.stat().st_size != SOURCE_BYTES:
        raise ValueError("12h source filename or byte size differs from frozen Dryad")
    h = hashlib.sha256()
    with archive.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != SHA256:
        raise ValueError("12h source SHA256 differs from frozen Dryad identity")

    groups: dict[tuple[str, ...], list[tuple[int, int, int, str, int]]] = defaultdict(list)
    precision = Counter()
    with ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) != 4 or {i.filename for i in entries} != EXPECTED_NAMES:
            raise ValueError("Unexpected source ZIP member layout")
        for item in entries:
            if (item.is_dir() or item.flag_bits & 1
                or stat.S_IFMT((item.external_attr >> 16) & 0xFFFF) == stat.S_IFLNK
                or item.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                or item.file_size > 120_000_000
                or item.file_size / max(1, item.compress_size) >= 200):
                raise ValueError("Unsafe ZIP member")
        with z.open("GPS12hrs_Locs.dbf") as f:
            h = f.read(32)
            if len(h) != 32:
                raise ValueError("DBF header truncated")
            n = struct.unpack("<I", h[4:8])[0]
            hlen = struct.unpack("<H", h[8:10])[0]
            rlen = struct.unpack("<H", h[10:12])[0]
            if n != RECORDS or not 33 <= hlen <= 16384:
                raise ValueError("Unfrozen DBF record count/header")
            desc = f.read(hlen - 32)
            if len(desc) != hlen - 32 or desc[-1] != 13:
                raise ValueError("DBF field header malformed")
            fields = {}
            cursor = 1
            for idx in range(0, len(desc) - 1, 32):
                d = desc[idx:idx + 32]
                key = d[:11].split(b"\x00")[0].decode("ascii")
                size = int(d[16])
                fields[key] = (cursor, cursor + size)
                cursor += size
            if cursor != rlen or not set(FIELDS).issubset(fields):
                raise ValueError("Physical DBF fields differ from frozen schema")
            for ordinal in range(n):
                raw = f.read(rlen)
                if len(raw) != rlen or raw[0] != 32:
                    raise ValueError("DBF row missing, deleted or truncated")
                values = {
                    name: raw[fields[name][0]:fields[name][1]]
                        .decode("latin1").strip(" \x00\t")
                    for name in FIELDS
                }
                key = tuple(values[name] for name in FIELDS[:4])
                if not all(key):
                    raise ValueError("Missing declared animal/season grouping key")
                time_text = values["Timstmp"]
                if len(time_text) == 10:
                    try:
                        dt = datetime.strptime(time_text, "%Y-%m-%d")
                    except ValueError as exc:
                        raise ValueError("Unknown date-only timestamp") from exc
                    lower = _seconds(dt)
                    t0_upper_exclusive = lower + 86400
                    t1_upper_inclusive = lower + 3600
                    kind = "date"
                elif len(time_text) == 19:
                    try:
                        dt = datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S")
                    except ValueError as exc:
                        raise ValueError("Unknown full timestamp") from exc
                    lower = _seconds(dt)
                    t0_upper_exclusive = lower
                    t1_upper_inclusive = lower
                    kind = "full"
                else:
                    raise ValueError("Unexpected GPS timestamp syntax; source STOP")
                precision[kind] += 1
                groups[key].append((
                    lower, t0_upper_exclusive, t1_upper_inclusive,
                    kind, ordinal,
                ))
    if precision != Counter({"date": 10835, "full": 18118}):
        raise ValueError("Source time-precision counts drifted")
    if len(groups) != 421:
        raise ValueError("Frozen animal/season grouping count drifted")
    for records in groups.values():
        # The same frozen T0-derived ordering is used in both scenarios.
        records.sort(key=lambda item: (item[0], item[1], item[4]))
    if sum(len(v) for v in groups.values()) != RECORDS:
        raise ValueError("Not all DBF records assigned to groups")
    return groups, precision


def pair_status(a, b, index: int, *, integer_closed: bool = False):
    """Pairwise gap-only classification; no biological dispersal inference.

    The historical v1 comparison used T0 next-midnight upper-exclusive
    endpoints as mathematical infima. The separately frozen v2 uses exact
    whole-second clock precision and closes that date-only upper bound
    at 23:59:59, retaining the historical v1 behavior when requested.
    """
    al, au = a[0], a[index]
    bl, bu = b[0], b[index]
    if integer_closed and index == 1:
        if a[3] == "date":
            au -= 1
        if b[3] == "date":
            bu -= 1
    min_gap = bl - au
    max_gap = bu - al
    possible = max_gap >= 1 and min_gap <= H
    robust = min_gap >= 1 and max_gap <= H
    return (
        "robust" if robust else
        "contingent" if possible else "excluded",
        min_gap <= 0,
    )


def time_triplet_possible(windows, max_gap=H):
    """Exact integer-second witness existence for three time windows.

    Windows are closed (inclusive) [lower, upper] intervals. All
    positive forward step lengths are integers between 1 and max_gap.
    """
    if len(windows) != 3:
        raise ValueError("Exactly three closed time windows are required")
    (l0, u0), (l1, u1), (l2, u2) = windows
    if any(lo > hi for lo, hi in windows):
        raise ValueError("Nonexistent closed timestamp window")
    a1 = max(l1, l0 + 1)
    b1 = min(u1, u0 + max_gap)
    a2 = max(l2, a1 + 1)
    b2 = min(u2, b1 + max_gap)
    return a1 <= b1 and a2 <= b2


def _triple_pair_possible(windows, max_gap=H):
    def possible(a, b):
        return b[1] >= a[0] + 1 and b[0] <= a[1] + max_gap
    return possible(windows[0], windows[1]) and possible(windows[1], windows[2])


PAIR_V2_PROTO = HERE / "post_stop_time_endpoint_seconds_protocol_v2.json"


def pair_audit(groups, *, integer_closed: bool = False) -> dict:
    stage = json.loads(PAIR_PROTO.read_text(encoding="utf-8"))
    if integer_closed:
        v2 = json.loads(PAIR_V2_PROTO.read_text(encoding="utf-8"))
        if (
            v2.get("schema") != "eog.mckee2024.post_stop_time_endpoint_seconds_correction.v2"
            or v2.get("status") != "FROZEN_AFTER_V1_ENDPOINT_AUDIT_BEFORE_CORRECTED_RECOMPUTATION"
            or v2.get("source_sha256") != SHA256
            or v2["pair_criterion"]["possible"] != "max_gap >= 1 AND min_gap <= 45000"
        ):
            raise ValueError("Exact-second correction contract must be precommitted")
    if (
        stage.get("schema") != "eog.mckee2024.post_stop_12h_time_interval_identifiability.v1"
        or stage.get("status") != "FROZEN_BEFORE_NEW_INTERVAL_GAP_COMPUTATION"
        or stage.get("max_bridge_gap_hours") != 12.5
        or stage["source"]["sha256"] != SHA256
    ):
        raise ValueError("Pair audit requires precommitted source/clock rules")
    out = {}
    crosses = Counter()
    types = Counter()
    for index, label in ((1, T0), (2, T1)):
        c = Counter()
        for group in groups.values():
            g = Counter()
            for left, right in zip(group, group[1:]):
                status, ambiguous = pair_status(
                    left, right, index, integer_closed=integer_closed
                )
                c[status] += 1
                c["total_pairs"] += 1
                g[status] += 1
                if ambiguous:
                    c["ambiguous_order"] += 1
                    g["ambiguous_order"] += 1
                if index == 1:
                    types["-".join(sorted((left[3], right[3]))) ] += 1
                else:
                    crosses[
                        pair_status(left, right, 1, integer_closed=integer_closed)[0] + "=>" + status
                    ] += 1
            if len(group) > 1:
                c["groups_all_robust"] += int(g["robust"] == len(group) - 1)
                c["groups_any_contingent"] += int(g["contingent"] > 0)
                c["groups_any_excluded"] += int(g["excluded"] > 0)
                c["groups_any_ambiguous"] += int(g["ambiguous_order"] > 0)
        if c["total_pairs"] != 28532:
            raise ValueError("Frozen adjacent pair denominator drifted")
        out[label] = dict(c)
    return {
        "schema": (
            "eog.mckee2024.post_stop_time_pair_replay.v2"
            if integer_closed else "eog.mckee2024.post_stop_time_pair_replay.v1"
        ),
        "status": (
            "EXACT_INTEGER_SECONDS_LOCAL_TIME_ONLY__STOP_PRESERVED"
            if integer_closed else "LOCAL_TIME_PAIR_INTERPRETATIONS_ONLY__STOP_PRESERVED"
        ),
        "source_sha256_verified": True,
        "records": RECORDS,
        "groups": len(groups),
        "pair_timestamp_types": dict(sorted(types.items())),
        "pair_status_by_scenario": out,
        "status_transitions": dict(sorted(crosses.items())),
        "dense_2h_holdout_opened": False,
        "coordinates_read_or_exported": False,
        "ecological_score_computed": False,
    }


def triple_audit(groups) -> dict:
    stage = json.loads(TRIPLE_PROTO.read_text(encoding="utf-8"))
    if (
        stage.get("schema") != "eog.mckee2024.post_stop_triplet_time_coherence.v1"
        or stage.get("status") != "FROZEN_BEFORE_NEW_3_RECORD_TIME_FEASIBILITY_COMPUTATION"
        or stage.get("source_sha256") != SHA256
        or stage.get("maximum_allowed_gap_seconds") != H
        or stage.get("minimum_allowed_forward_gap_seconds") != 1
    ):
        raise ValueError("Triple audit requires precommitted temporal composition rules")
    out = {}
    total = sum(max(0, len(g) - 2) for g in groups.values())
    if total != 28111:
        raise ValueError("Frozen source triplet denominator drifted")
    for label, index in ((T0, 1), (T1, 2)):
        counts = Counter()
        patterns = Counter()
        impacted_groups = 0
        for group in groups.values():
            impacted = False
            for j in range(len(group) - 2):
                triplet = group[j:j + 3]
                windows = [
                    (
                        item[0],
                        item[1] - 1 if index == 1 and item[3] == "date"
                        else item[index],
                    )
                    for item in triplet
                ]
                each_possible = _triple_pair_possible(windows)
                whole_possible = time_triplet_possible(windows)
                counts["total_triplets"] += 1
                if each_possible:
                    counts["both_edges_pairwise_possible"] += 1
                    if whole_possible:
                        counts["globally_feasible_among_two_possible"] += 1
                    else:
                        counts["pairwise_possible_but_globally_infeasible"] += 1
                        patterns[
                            "".join("D" if item[3] == "date" else "F" for item in triplet)
                        ] += 1
                        impacted = True
                else:
                    counts["at_least_one_pairwise_impossible"] += 1
                if whole_possible:
                    counts["globally_feasible_all_triplets"] += 1
            impacted_groups += int(impacted)
        counts["groups_with_any_false_chain"] = impacted_groups
        out[label] = {
            **dict(counts),
            "false_chain_timestamp_precision_signatures": dict(sorted(patterns.items())),
        }
    return {
        "schema": "eog.mckee2024.post_stop_triplet_time_coherence_replay.v1",
        "status": "PAIRWISE_TIME_PATH_SPLICING_DIAGNOSIS_ONLY__STOP_PRESERVED",
        "source_sha256_verified": True,
        "records": RECORDS, "groups": len(groups),
        "within_group_triplets": total,
        "results": out,
        "dense_2h_holdout_opened": False,
        "coordinates_read_or_exported": False,
        "ecological_score_computed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--stage", choices=("pair", "pair_v2", "triplet"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    protocol = (
        TRIPLE_PROTO if args.stage == "triplet"
        else PAIR_V2_PROTO if args.stage == "pair_v2"
        else PAIR_PROTO
    )
    if not protocol.exists():
        raise SystemExit("Frozen stage contract missing; refusing source data")
    groups, _ = _source_rows(args.source_zip)
    result = (
        triple_audit(groups) if args.stage == "triplet"
        else pair_audit(groups, integer_closed=args.stage == "pair_v2")
    )
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content)


if __name__ == "__main__":
    main()
