"""Post-exposure, source-pinned stratification of EOG x BAM span directions.

Only reads PR #677 canonical result.json and fibre_envelopes.csv.
No new worlds, responses, field validation, or independent experiments.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

SOURCE_SHA256 = {
    "fibre_envelopes.csv": "2bc644dd3f76750bdfef320c47662c64a47e00fa3e175f3864e296d0cb1dc803",
    "result.json": "584ad345ef2fbc6370b258e2e3d9c25a8fff98ab19dae19a55c7abdfb1bfa196",
}
AXES = ("A", "B", "M")
VALID = {"-1", "0", "1", "-1|0", "-1|1", "0|1", "-1|0|1"}


def signs(value: str) -> tuple[int, ...]:
    if value not in VALID:
        raise ValueError(f"invalid direction set: {value!r}")
    parts = tuple(map(int, value.split("|")))
    if tuple(sorted(set(parts))) != parts:
        raise ValueError(f"unsorted or duplicate direction: {value!r}")
    return parts


def audit(source: Path) -> dict:
    for filename, expected in SOURCE_SHA256.items():
        actual = sha256((source / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"original source hash mismatch: {filename} {actual}")
    parent = json.loads((source / "result.json").read_text())
    a = parent["audit"]
    if (a["worlds"], a["current_G_fibres"], a["mask_ambiguous_fibres"]) != (768, 129, 69):
        raise ValueError("parent denominator mismatch")
    with (source / "fibre_envelopes.csv").open(newline="") as fp:
        span = [r for r in csv.DictReader(fp) if r["metric"] == "span"]
    if len(span) != 387:
        raise ValueError("expected 129 x 3 span rows")

    grouped = {axis: [] for axis in AXES}
    fibres = {}
    for r in span:
        axis = r["release_axis"]
        if axis not in AXES:
            raise ValueError(f"invalid axis {axis}")
        ident = r["direction_identified"]
        map_ident = r["map_identified"]
        if ident not in ("True", "False") or map_ident not in ("True", "False"):
            raise ValueError("invalid Boolean field")
        r["sign_set"] = signs(r["directions"])
        if (ident == "True") != (len(r["sign_set"]) == 1):
            raise ValueError("direction identification mismatch")
        if (map_ident == "True") != (int(r["n_release_maps"]) == 1):
            raise ValueError("map identification mismatch")
        r["mechanism_alias"] = int(r["n_mask_triples"]) > 1
        r["map_alias"] = int(r["n_release_maps"]) > 1
        key = (r["system_id"], r["G_bits"])
        if axis in fibres.setdefault(key, {}):
            raise ValueError("duplicate current-G-axis")
        fibres[key][axis] = r
        grouped[axis].append(r)

    if len(fibres) != 129 or len({k[0] for k in fibres}) != 12:
        raise ValueError("incorrect current G or landscape denominator")
    if any(set(f) != set(AXES) for f in fibres.values()):
        raise ValueError("incomplete three-axis fibre")
    if any(len({r["n_mask_triples"] for r in f.values()}) != 1 for f in fibres.values()):
        raise ValueError("A/B/M aliases differ for same current G")

    parent_axis = {(x["release_axis"], x["metric"]): x for x in parent["axis_targets"]}
    results = {}
    for axis, rows in grouped.items():
        count = lambda check: sum(bool(check(r)) for r in rows)
        up = count(lambda r: r["sign_set"] == (1,))
        down = count(lambda r: r["sign_set"] == (-1,))
        zero = count(lambda r: r["sign_set"] == (0,))
        zero_ambig = count(lambda r: len(r["sign_set"]) > 1 and 0 in r["sign_set"])
        opposite = count(lambda r: -1 in r["sign_set"] and 1 in r["sign_set"])
        prior = parent_axis[(axis, "span")]
        if (up, down, zero, opposite, up+down+zero) != (
            prior["identified_increase"], prior["identified_decrease"],
            prior["identified_no_change"], prior["opposite_sign_fibres"],
            prior["direction_identified_fibres"],
        ):
            raise ValueError("parent positive/negative/zero parity failure")
        if up + down + zero + zero_ambig + opposite != 129:
            raise ValueError("direction classes do not partition 129 fibres")
        results[axis] = {
            "identified_positive": up,
            "identified_negative": down,
            "identified_zero": zero,
            "ambiguous_zero_vs_nonzero": zero_ambig,
            "ambiguous_opposite_sign": opposite,
            "possible_nonzero": 129 - zero,
            "identified_nonzero": up + down,
            "identified_nonzero_among_possible_nonzero": (up + down) / (129 - zero),
            "identified_nonzero_with_mechanism_alias": count(
                lambda r: len(r["sign_set"]) == 1 and r["sign_set"] != (0,) and r["mechanism_alias"]
            ),
            "identified_nonzero_with_released_map_alias": count(
                lambda r: len(r["sign_set"]) == 1 and r["sign_set"] != (0,) and r["map_alias"]
            ),
            "landscapes_with_identified_nonzero": len({
                r["system_id"] for r in rows
                if len(r["sign_set"]) == 1 and r["sign_set"] != (0,)
            }),
        }

    all_known = [f for f in fibres.values() if all(len(f[a]["sign_set"]) == 1 for a in AXES)]
    joint = {
        "all_three_identified": len(all_known),
        "all_three_identified_mechanism_alias": sum(f["A"]["mechanism_alias"] for f in all_known),
        "all_three_identified_any_nonzero": sum(
            any(f[a]["sign_set"] != (0,) for a in AXES) for f in all_known
        ),
        "all_three_identified_all_nonzero": sum(
            all(f[a]["sign_set"] != (0,) for a in AXES) for f in all_known
        ),
    }
    if (joint["all_three_identified"], joint["all_three_identified_mechanism_alias"]) != (115, 55):
        raise ValueError("joint-parent parity mismatch")
    return {
        "schema": "eog.bam_nonzero_span_direction.posthoc.v1",
        "status": "POST_EXPOSURE_DESCRIPTIVE_NO_NEW_ENDPOINT",
        "source_run": 42224332364,
        "source_artifact": 13504738461,
        "source_member_sha256": SOURCE_SHA256,
        "denominators": {
            "landscapes": 12, "candidate_worlds": 768,
            "current_G_fibres": 129, "mechanism_ambiguous_fibres": 69,
        },
        "axis": results,
        "joint": joint,
        "claim_limit": "Ideal finite BAM mask-deletion and full-census span, not causal field response or ecological prediction accuracy.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    result = audit(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"axis": result["axis"], "joint": result["joint"]}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
