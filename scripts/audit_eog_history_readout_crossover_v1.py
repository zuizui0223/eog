#!/usr/bin/env python3
"""Post-hoc v18–v23 READOUT crossover audit of prior frozen simulation artifacts.

No generator calls, no biological data, no added measurement menu. The frozen v23
idealized occupancy/provenance/combined libraries are compared within the SAME
three-source landscape configurations used by the existing v18-v22 matched audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

from audit_matched_eog_source_history_v1 import (
    ARCHIVES, load_artifact, row_key, verify_matched_record, EPS
)

V23 = {
    "id": 11324893031,
    "sha256": "a859e7b6ec5e8af47b56a67a10b89ae7ab65ca3e1a70aed9317f663f863eaae9",
    "fingerprint": "ab37b83de94fce5e6d35918b9f5730a63364cebf0bb00ec662eececc5ae85244",
}
READOUTS = ("occupancy_only", "provenance_only", "combined")


def load_v23(path: Path) -> dict:
    if hashlib.sha256(path.read_bytes()).hexdigest() != V23["sha256"]:
        raise ValueError("v23 original artifact SHA-256 does not match frozen source")
    with zipfile.ZipFile(path) as z:
        if z.namelist() != ["result_v23.json"]:
            raise ValueError("v23 unexpected archive members")
        payload = json.loads(z.read("result_v23.json"))
    if payload["fingerprint"] != V23["fingerprint"]:
        raise ValueError("v23 result fingerprint mismatch")
    if (payload["row_count"], payload["eligible_row_count"], payload["design_row_count"]) != (384, 384, 768):
        raise ValueError("v23 original universe changed")
    rows = {row_key(v): v for v in payload["rows"]}
    if len(rows) != 384 or not all(v["eligible"] for v in rows.values()):
        raise ValueError("v23 duplicate or ineligible landscape")
    return rows


def paired_readout_outcomes(key, phases):
    v18, v21, v22, v23 = (phases[x] for x in ("v18", "v21", "v22", "v23"))
    layouts = {}
    for place in ("clustered", "dispersed"):
        p18 = v18["designs"][place]["3"]
        p21 = v21["designs"][place]
        p22 = v22["designs"][place]
        p23 = v23["designs"][place]
        if not (
            p18["source_ids"] == p21["source_ids"]
            == p22["source_ids"] == p23["source_ids"]
        ):
            raise ValueError(f"{key}: v23 source list doesn't match frozen three-source design")
        if p23["history_count"] != 3:
            raise ValueError(f"{key}: v23 historical alternatives changed")
        if p23["plans"]["occupancy_only"]["full_history"]["identified"] != p22["full_history"]["identified"]:
            raise ValueError(f"{key}: v23 occupancy arm not equal to exact frozen v22 arm")

        ids = {}
        for readout in READOUTS:
            record = p23["plans"][readout]["full_history"]
            value = bool(record["identified"])
            if (record["minimum_size"] is None) == value:
                raise ValueError(f"{key}: v23 readout estimability inconsistent")
            ids[readout] = value
        if (ids["occupancy_only"] or ids["provenance_only"]) and not ids["combined"]:
            raise ValueError(f"{key}: combined observation cannot lose identifiability")
        layouts[place] = {
            "ids": ids,
            "coverage": p18["union_reachable_fraction"],
            "insurance": p18["worst_source_loss_retention"],
            "provenance_memory": p21["provenance_disagreement_fraction"],
        }
    return layouts


def summarize(outcomes):
    if len(outcomes) != 384:
        raise ValueError("not all 384 landscapes matched")
    contingency = {}
    for t in READOUTS:
        counts = Counter((
            row["clustered"]["ids"][t],
            row["dispersed"]["ids"][t]
        ) for row in outcomes.values())
        contingency[t] = {
            "neither": counts[False, False],
            "dispersed_only": counts[False, True],
            "clustered_only": counts[True, False],
            "both": counts[True, True],
        }
    coverage_tradeoff = 0
    crossovers = 0
    inverse_crossovers = 0
    crossovers_tradeoff = 0
    crossovers_clustered_more_provenance = 0
    crossovers_both_combined_identifiable = 0
    strata = {s: {} for s in ("barrier", "autocorrelation", "neighbourhood")}
    for key, row in outcomes.items():
        c,d = row["clustered"],row["dispersed"]
        tradeoff = (d["coverage"] > c["coverage"] + EPS and
                    c["insurance"] > d["insurance"] + EPS)
        occ=(c["ids"]["occupancy_only"],d["ids"]["occupancy_only"])
        prov=(c["ids"]["provenance_only"],d["ids"]["provenance_only"])
        flip=occ==(False,True) and prov==(True,False)
        inverse=occ==(True,False) and prov==(False,True)
        stronger=c["provenance_memory"] > d["provenance_memory"] + EPS
        if tradeoff: coverage_tradeoff+=1
        if flip: crossovers+=1
        if inverse: inverse_crossovers+=1
        if flip and tradeoff: crossovers_tradeoff+=1
        if flip and stronger: crossovers_clustered_more_provenance+=1
        if flip and all(c0["ids"]["combined"] for c0 in (c,d)):
            crossovers_both_combined_identifiable+=1
        for factor, value in (
            ("barrier",key[2]),("autocorrelation",key[0]),("neighbourhood",key[1])
        ):
            name=str(value)
            entry=strata[factor].setdefault(name,{"n":0,"crossovers":0,"tradeoff":0})
            entry["n"]+=1
            entry["crossovers"]+=int(flip)
            entry["tradeoff"]+=int(tradeoff)
    return {
        "schema": "eog.virtual_worlds.history_readout_crossover.v1",
        "status": "POST_RESULT_EXPLORATORY_NOT_PREREGISTERED",
        "matched_landscapes": 384,
        "three_sources_per_design": True,
        "readout_levels": {
            "occupancy_only": "ideal full binary snapshots at t4,t5,t6,t8 after activation, source nodes excluded",
            "provenance_only": "ideal nodewise equilibrium earliest-source labels from existing v23 provenance assays",
            "combined": "both v23 evidence libraries; observation count not comparable to field sampling cost",
        },
        "original_artifact_zip_sha256": {
            **{k: v["sha256"] for k,v in ARCHIVES.items()},
            "v23": V23["sha256"],
        },
        "original_result_fingerprints": {
            **{k: v["fingerprint"] for k,v in ARCHIVES.items()},
            "v23": V23["fingerprint"],
        },
        "identification_by_readout": {
            t: {
                "clustered": contingency[t]["clustered_only"]+contingency[t]["both"],
                "dispersed": contingency[t]["dispersed_only"]+contingency[t]["both"],
            }
            for t in READOUTS
        },
        "paired_identifiability": contingency,
        "readout_crossover": {
            "occupancy_d_only__provenance_c_only": crossovers,
            "occupancy_c_only__provenance_d_only": inverse_crossovers,
            "crossover_with_coverage_insurance_tradeoff": crossovers_tradeoff,
            "crossover_with_more_clustered_provenance_memory": crossovers_clustered_more_provenance,
            "combined_resolves_both_crossover_designs": crossovers_both_combined_identifiable,
            "coverage_insurance_tradeoff_all_landscapes": coverage_tradeoff,
        },
        "strata": strata,
        "interpretation": (
            "In the same matched synthetic source network, the source layout ranking of "
            "exact activation-history identifiability can reverse when the declared "
            "observation library changes from transient occupancy to earliest-source "
            "provenance. This is an observation-dependent readout effect, not a change "
            "in the latent ecological landscape or a demographic persistence result."
        ),
        "boundaries": [
            "The observation libraries and three activation histories were fixed in v23; the cross-phase layout comparison is post hoc.",
            "A provenance assay returns ideal earliest-source identity rather than a realistic genetic ancestry, migration or demographic estimate.",
            "Occupancy and provenance libraries have different information content and cost; rates are not equal-effort field recommendations.",
            "No new simulation, mechanism, external ecological endpoint or causal mediation is inferred.",
            "Original v18-v23 preregistered results, refutations, and EOG-WF empirical programme remain unchanged.",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for phase in ("v18","v19","v21","v22","v23"):
        parser.add_argument(f"--{phase}",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--assert-frozen",type=Path)
    opts=parser.parse_args()
    phases={k:load_artifact(getattr(opts,k),k) for k in ARCHIVES}
    phases["v23"]=load_v23(opts.v23)
    universe=set(phases["v18"])
    if any(set(p)!=universe for p in phases.values()):
        raise ValueError("The v23 universe is not the same latent 384-landscape panel")
    rows={}
    for key in sorted(universe):
        # Recheck all v18-v22 spatial/support/historical alignment before v23.
        verify_matched_record(key,{k:phases[k][key] for k in ARCHIVES})
        rows[key]=paired_readout_outcomes(key,{k:phases[k][key] for k in phases})
    report=summarize(rows)
    if opts.assert_frozen:
        if report!=json.loads(opts.assert_frozen.read_text(encoding="utf-8")):
            raise ValueError("Crossover report does not equal frozen exploratory evidence")
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"matched":384,
                      "crossover":report["readout_crossover"]},sort_keys=True))


if __name__=="__main__":
    main()
