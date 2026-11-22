#!/usr/bin/env python3
"""Reproduce frozen sparse 12h aggregate source-QC and post-STOP time diagnostics.

Never opens withheld 2h GPS, SHP geometry records, or exports individual AID,
precise time strings or coordinates. Stage protocols were committed before reads.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

from replay_sparse_schema_and_geometry import verify_source, dbf_schema

HERE = Path(__file__).resolve().parent
STAGES = {
    "initial": "gate2_sparse_only_aggregate_qc_protocol_v1.json",
    "patterns": "post_stop_field_diagnostic_protocol_v1.json",
    "hypotheses": "post_stop_semantics_hypotheses_v1.json",
}
FIELDS = ("State", "Herd", "SpcsCmm", "SpcsScn", "AID",
          "SeasnYr", "Season", "Year", "Timstmp", "UTM_E", "UTM_N")
FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
    "%m/%d/%Y %I:%M:%S %p", "%Y-%m-%dT%H:%M:%S",
)


def _parse_timestamp(value):
    for fmt in FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    if ":" in value and (" " in value or "T" in value):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return None


def _gap_counts(groups):
    counts = Counter()
    for times in groups.values():
        times.sort()
        for t0, t1 in zip(times, times[1:]):
            gap = (t1 - t0).total_seconds() / 3600
            if gap == 0:
                counts["duplicate"] += 1
            elif gap < 10:
                counts["under_10_hours"] += 1
            elif gap <= 14:
                counts["10_to_14_hours"] += 1
            elif gap <= 24:
                counts["over_14_to_24_hours"] += 1
            else:
                counts["over_24_hours"] += 1
    return {
        "groups": len(groups),
        "groups_at_least_3": sum(len(values) >= 3 for values in groups.values()),
        "gaps_total": sum(counts.values()),
        "gaps": dict(sorted(counts.items())),
    }


def run(archive, stage):
    n, header_len, row_len, fields = dbf_schema(archive)
    member_name = "GPS12hrs_Locs.dbf"
    out = {
        "schema": "eog.mckee2024.sparse12h.timestamp_source_qc_replay.v1",
        "stage": stage, "source_sha256_verified": True,
        "dbf_declared_rows": n,
        "dense_2h_holdout_opened": False,
        "raw_timestamps_or_identifiers_exported": False,
        "ecological_score_computed": False,
    }
    herd, season, species, missing = Counter(), Counter(), Counter(), Counter()
    parse, syntax, unparsed_syntax, hours = Counter(), Counter(), Counter(), Counter()
    animals = set()
    xvals, yvals = [], []
    groups_original, groups_midnight, groups_noon = defaultdict(list), defaultdict(list), defaultdict(list)
    with archive.open(member_name) as fp:
        fp.read(header_len)
        for i in range(n):
            raw = fp.read(row_len)
            if len(raw) != row_len or raw[0] != 0x20:
                raise ValueError("Invalid/truncated or deleted DBF row")
            values = {
                name: raw[fields[name][0]:fields[name][1]].decode("latin-1").strip(" \x00\t")
                for name in FIELDS
            }
            if stage == "initial":
                for name, value in values.items():
                    if not value:
                        missing[name] += 1
                herd[values["Herd"]] += 1
                season[values["Season"]] += 1
                species[values["SpcsCmm"]] += 1
                animals.add((values["Herd"], values["AID"]))
            if stage == "patterns":
                xvals.append(float(values["UTM_E"]))
                yvals.append(float(values["UTM_N"]))
            timestamp = values["Timstmp"]
            when = _parse_timestamp(timestamp)
            label = "parseable" if when is not None else "unparseable_or_missing"
            parse[label] += 1
            key = tuple(values[x] for x in ("Herd", "AID", "SeasnYr", "Season"))
            if not all(key):
                raise ValueError("Missing group identity prevents sparse-only QC")
            if when is not None:
                groups_original[key].append(when)
            if stage in ("patterns", "hypotheses"):
                signature = "".join(
                    "D" if char.isdigit() else "L" if char.isalpha() else char
                    for char in timestamp
                )
                syntax[signature] += 1
                if when is None:
                    unparsed_syntax[signature] += 1
            if stage == "hypotheses":
                if when is not None:
                    hours[f"{when.hour:02d}"] += 1
                    groups_midnight[key].append(when)
                    groups_noon[key].append(when)
                elif signature == "DDDD-DD-DD":
                    start = datetime.strptime(timestamp, "%Y-%m-%d")
                    groups_midnight[key].append(start)
                    groups_noon[key].append(start + timedelta(hours=12))
                else:
                    raise ValueError("Unrecognized timestamp shape; cannot impute silently")
    if stage == "initial":
        out.update({
            "herd_record_counts": dict(sorted(herd.items())),
            "season_record_counts": dict(sorted(season.items())),
            "species_record_counts": dict(sorted(species.items())),
            "missing_field_counts": dict(sorted(missing.items())),
            "unique_herd_animal_pairs": len(animals),
            "time_parse_counts": dict(sorted(parse.items())),
            "parsed_only_gaps": _gap_counts(groups_original),
            "status": "ORIGINAL_QC_STOP_NOT_RESCUED",
        })
    elif stage == "patterns":
        def rnd(x):
            if not math.isfinite(x):
                raise ValueError("Non-finite coordinate")
            return round(x / 10000) * 10000
        out.update({
            "timestamp_shape_counts": dict(sorted(syntax.items())),
            "unparsed_timestamp_shape_counts": dict(sorted(unparsed_syntax.items())),
            "negative_easting_count": sum(x < 0 for x in xvals),
            "rounded_xy_minmax": [rnd(min(xvals)), rnd(min(yvals)),
                                  rnd(max(xvals)), rnd(max(yvals))],
            "status": "POST_STOP_FORMAT_AND_BOUNDS_DIAGNOSTIC",
        })
    elif stage == "hypotheses":
        out.update({
            "hour_histogram_precise_time_records": dict(sorted(hours.items())),
            "date_only_midnight_hypothetical": _gap_counts(groups_midnight),
            "date_only_noon_negative_control": _gap_counts(groups_noon),
            "time_reinterpretation_accepted_as_truth": False,
            "status": "POST_STOP_HYPOTHESIS_COMPARISON_NO_PROMOTION",
        })
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--stage", choices=tuple(STAGES), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not (HERE / STAGES[args.stage]).exists():
        raise SystemExit("Frozen stage protocol missing")
    with verify_source(args.zip) as archive:
        summary = run(archive, args.stage)
    data = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data)


if __name__ == "__main__":
    main()
