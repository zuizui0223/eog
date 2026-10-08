#!/usr/bin/env python3
"""Distinguish standalone readout rescue from genuine mixed-library synergy in v23.

POST-RESULT DESCRIPTIVE ONLY. No landscape simulation or biological responses. 
The v23 original archive and committed v23 crossover receipt are immutable inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from audit_eog_history_readout_crossover_v1 import load_v23

LIBRARIES = ("occupancy_only", "provenance_only", "combined")


def classify_record(design: dict) -> tuple[str, bool]:
    plans = design["plans"]
    records = [plans[name]["full_history"] for name in LIBRARIES]
    flags = []
    for record in records:
        value = record["identified"]
        if not isinstance(value, bool):
            raise ValueError("History-identification status is not boolean")
        if value != (record["minimum_size"] is not None):
            raise ValueError("Identification and minimum action count disagree")
        if value and not record["minimum_action_ids"]:
            raise ValueError("Identified target without an action witness")
        flags.append(value)
    o, p, both = flags
    if (o or p) and not both:
        raise ValueError("Combining libraries must not lose identification")

    genuine_mixed = not o and not p and both
    if genuine_mixed:
        actions = plans["combined"]["full_history"]["minimum_action_ids"]
        families = [a.split("_", 1)[0] for a in actions]
        if sorted(families) != ["O", "P"] or len(actions) != 2:
            raise ValueError("Both-single-insufficient case lacks a two-family witness")
        if plans["combined"]["full_history"]["minimum_size"] != 2:
            raise ValueError("Mixed witness and reported exact burden disagree")
    return "".join("1" if v else "0" for v in flags), genuine_mixed


def analyze(v23_rows: dict, parent: dict) -> dict:
    if parent["status"] != "POST_RESULT_EXPLORATORY_NOT_PREREGISTERED":
        raise ValueError("Parent result cannot be promoted to confirmatory analysis")
    if set(v23_rows) == set() or len(v23_rows) != 384:
        raise ValueError("Original v23 landscape universe must contain 384 keys")
    if parent["matched_landscapes"] != len(v23_rows):
        raise ValueError("v23 matched parent denominator changed")
    panels = {}
    global_mixed = 0
    for place in ("clustered", "dispersed"):
        freq = Counter()
        for row in v23_rows.values():
            klass, mixed = classify_record(row["designs"][place])
            freq[klass] += 1
            global_mixed += int(mixed)
        if any(k not in {"000", "001", "011", "101", "111"} for k in freq):
            raise ValueError("Observed logically impossible identification triple")
        flags = {key: freq[key] for key in ("000", "001", "011", "101", "111")}
        if sum(flags.values()) != 384:
            raise ValueError("Readout classification did not cover all landscapes")
        o = flags["101"] + flags["111"]
        p = flags["011"] + flags["111"]
        combined = 384 - flags["000"]
        parent_counts = parent["identification_by_readout"]
        if (
            o != parent_counts["occupancy_only"][place]
            or p != parent_counts["provenance_only"][place]
            or combined != parent_counts["combined"][place]
        ):
            raise ValueError("Readout exclusive/synergy table disagrees with frozen crossover")
        occupancy_unresolved = 384-o
        provenance_unresolved = 384-p
        rescued_by_provenance_alone = flags["011"]
        synergistically_rescued = flags["001"]
        rescued_after_adding_provenance = rescued_by_provenance_alone+synergistically_rescued
        panels[place] = {
            "n": 384,
            "identifiability_triple_order": "occupancy_only,provenance_only,combined",
            "truth_table": flags,
            "occupancy_unresolved": occupancy_unresolved,
            "provenance_unresolved": provenance_unresolved,
            "provenance_alone_rescues_occupancy_unresolved": rescued_by_provenance_alone,
            "mixed_only_rescues_occupancy_unresolved": synergistically_rescued,
            "total_rescued_after_adding_provenance": rescued_after_adding_provenance,
            "fraction_unresolved_rescued_by_provenance_alone": (
                rescued_by_provenance_alone/occupancy_unresolved
            ),
            "fraction_unresolved_rescued_by_both_only": (
                synergistically_rescued/occupancy_unresolved
            ),
            "fraction_unresolved_rescued_in_total": (
                rescued_after_adding_provenance/occupancy_unresolved
            ),
            "newly_identified_by_occupancy_alone_after_provenance": flags["101"],
            "newly_identified_by_mixed_information_after_provenance": flags["001"],
        }
    if global_mixed != panels["clustered"]["truth_table"]["001"]+panels["dispersed"]["truth_table"]["001"]:
        raise ValueError("Mixed-only total failed internal accounting")
    return {
        "schema": "eog.virtual_worlds.v23_readout_synergy_decomposition.v1",
        "status": "POST_RESULT_DESCRIPTIVE_NOT_PREREGISTERED",
        "source": "original v23 complete 384-row synthetic action audit plus frozen matched-crossover receipt",
        "original_v23_artifact_id": 11324893031,
        "original_v23_sha256": parent["original_artifact_zip_sha256"]["v23"],
        "original_v23_fingerprint": parent["original_result_fingerprints"]["v23"],
        "parent_receipt": "validation/eog_virtual_world_ecology_synthesis_v1/matched_readout_crossover_v1.json",
        "panel_count": 384,
        "design_count": 768,
        "true_mixed_library_synergy_designs": global_mixed,
        "layouts": panels,
        "interpretation": (
            "The large raw gain from adding provenance under clustered geometry is mostly "
            "already distinguishable by provenance alone; the stricter mixed-library-only "
            "gain is smaller. Both geometries can have a rare history requiring two different "
            "observation families to distinguish all frozen activation alternatives."
        ),
        "boundaries": [
            "Two idealized action families have different information payload, dimensionality and field costs.",
            "The 768 layout cases share 384 landscapes, not 768 independent biological samples.",
            "This is an audit of existing simulated action minima, not a prospective ecological mechanism test.",
            "No causal history-memory pathway, optimal field budget, genetic origin inference or population persistence is established.",
            "Frozen known-truth programmes and empirical article denominators are not reopened.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v23", required=True, type=Path)
    ap.add_argument("--parent", required=True, type=Path)
    ap.add_argument("--assert-frozen", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    rows = load_v23(a.v23)
    parent = json.loads(a.parent.read_text(encoding="utf-8"))
    value = analyze(rows, parent)
    expected = json.loads(a.assert_frozen.read_text(encoding="utf-8"))
    if value != expected:
        raise ValueError("Audit differs from frozen descriptive readout-decomposition")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({"status": value["status"], "synergy": value["true_mixed_library_synergy_designs"],
                      "layouts": {k: v["truth_table"] for k, v in value["layouts"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
