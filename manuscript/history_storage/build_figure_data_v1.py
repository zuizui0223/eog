#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCES = {
    "v28": (
        ROOT / "validation/eog_original_idea_leopold_history_retention_v28/result_summary_v28.json",
        "60d32bf5daf49cb33f6c6989fd64ee7f0b74d544d0b3441e99d8605ba0b9b302",
    ),
    "v30": (
        ROOT / "validation/eog_grassland_above_below_history_retention_v30/result_summary_v30.json",
        "272dc58ef05977ce990811809b44c94889a0c68339b4a7ba93c615a239cd6a59",
    ),
    "v31": (
        ROOT / "validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json",
        "82a84ac84133f3a7eb45e29acb276ae64bc61f520ec5682fd56cf8c2a4a8f9ee",
    ),
    "v33": (
        ROOT / "validation/eog_role_mapping_specificity_v33/result_summary_v33.json",
        "e41b9fafdc7902a0fd6649c96d6f61b7aafa53de9abca6180179e3cb5fa335fb",
    ),
    "v34": (
        ROOT / "validation/eog_history_level_leverage_v34/result_summary_v34.json",
        "6ddf1d089dd3885c6d12a1809629ef1dd1486fcab7a03c81bfb9b7ce81ca0325",
    ),
    "v35": (
        ROOT / "validation/eog_dominance_tail_history_storage_v35/result_summary_v35.json",
        "185147dabd36f3890f8de9c86fb2cb46c8cb63a96c0e1fae102299bd3a9ac533",
    ),
    "v36": (
        ROOT / "validation/eog_alternaria_binary_components_v36/result_summary_v36.json",
        "dfbe027e089089096c4a8a571396081a5531b5d57e4d00ea8a8ccab64d3ac421",
    ),
    "v37": (
        ROOT / "validation/eog_alternaria_genotype_generality_v37/result_summary_v37.json",
        "bfc500301fbea9672d7e167f8f33e9c491220cc951a72678f1a8327d40fcbdf6",
    ),
}


def load() -> dict[str, dict]:
    out = {}
    for name, (path, expected) in SOURCES.items():
        obj = json.loads(path.read_text(encoding="utf-8"))
        observed = obj.get("result_fingerprint")
        if observed != expected:
            raise RuntimeError(
                f"{name} fingerprint changed: expected {expected}, observed {observed}"
            )
        out[name] = obj
    return out


def rows(data: dict[str, dict]) -> list[dict[str, object]]:
    v28, v30, v31, v33, v34, v35, v36, v37 = (
        data["v28"], data["v30"], data["v31"], data["v33"],
        data["v34"], data["v35"], data["v36"], data["v37"]
    )
    r: list[dict[str, object]] = []

    def add(fig, panel, system, target, metric, value, p=None, note=""):
        r.append({
            "figure": fig,
            "panel": panel,
            "system": system,
            "target": target,
            "metric": metric,
            "value": value,
            "permutation_p": p,
            "note": note,
        })

    # Figure 2
    for target, label in [
        ("fungal_community_composition", "Fungal composition"),
        ("rust_lesion_fraction", "Rust lesion state"),
    ]:
        x=v28["primary"][target]
        add("2","A","microbiome",label,"E",x["excess_over_null_median"],x["permutation_p"])
        add("2","A","microbiome",label,"observed_R2",x["partial_r2"],x["permutation_p"])
        add("2","A","microbiome",label,"null_median_R2",x["null_median"],x["permutation_p"])
    for target,label in [
        ("shoot_functional_group_composition","Shoot composition"),
        ("root_vertical_distribution","Root vertical distribution"),
    ]:
        x=v30["primary"][target]
        add("2","B","grassland",label,"E",x["excess_over_null_median"],x["permutation_p"])
        add("2","B","grassland",label,"observed_R2",x["partial_r2"],x["permutation_p"])
        add("2","B","grassland",label,"null_median_R2",x["null_median"],x["permutation_p"])
    x=v30["scalar_sensitivities"]["total_shoot_biomass"]
    add("2","B","grassland","Total shoot biomass","E",x["excess_over_null_median"],x["permutation_p"],"secondary")

    # Figure 3
    for system,label in [("v28_microbiome","microbiome"),("v30_grassland","grassland")]:
        x=v31["systems"][system]
        add("3",label,label,"Labeled composition","E",x["labeled_E"])
        add("3",label,label,"Rank abundance","E",x["rank_abundance_E"],x["rank_permutation_p"])
        add("3",label,label,"Shannon entropy","E",x["shannon_E"],x["shannon_permutation_p"],"secondary scalar")
        add("3",label,label,"Identity storage gap","gap",x["identity_storage_gap"])

    # Figure 4A
    add("4","A","microbiome","Correct role mapping","R2",v33["v28_microbiome"]["correct_partial_r2"],
        note=f"rank {v33['v28_microbiome']['correct_rank_descending']}/{v33['v28_microbiome']['mapping_count']}")
    add("4","A","microbiome","Incorrect mapping median","R2",v33["v28_microbiome"]["incorrect_mapping_median_r2"])
    add("4","A","grassland","Correct role mapping","R2",v33["v30_grassland"]["correct_partial_r2"],
        note=f"rank {v33['v30_grassland']['correct_rank_descending']}/{v33['v30_grassland']['mapping_count']}")
    add("4","A","grassland","Incorrect mapping median","R2",v33["v30_grassland"]["incorrect_mapping_median_r2"])

    # Figure 4B
    for history,x in v34["leave_one_history_out"].items():
        add("4","B","microbiome",history,"deletion_leverage_D",x["leverage_D"],x["permutation_p"])

    # Figure 4C
    add("4","C","microbiome","Alternaria vs Other — dominance","E",v36["dominance"]["E"],v36["dominance"]["permutation_p"])
    add("4","C","microbiome","Alternaria vs Other — lower-rank tail","E",v36["lower_rank_tail"]["E"],v36["lower_rank_tail"]["permutation_p"])
    for genotype,delta in v37["genotype_deltas"].items():
        add("4","C","microbiome",genotype,"genotype_dominance_delta",delta)

    # Supplementary component values
    add("S","dominance_tail","microbiome","Full dominance","E",v35["full_panel"]["dominance_rank1"]["E"],v35["full_panel"]["dominance_rank1"]["p"])
    add("S","dominance_tail","microbiome","Full lower-rank tail","E",v35["full_panel"]["lower_rank_tail"]["E"],v35["full_panel"]["lower_rank_tail"]["p"])
    add("S","dominance_tail","microbiome","Without Alternaria dominance","E",v35["without_Alternaria"]["dominance_rank1"]["E"],v35["without_Alternaria"]["dominance_rank1"]["p"])
    add("S","dominance_tail","microbiome","Without Alternaria lower-rank tail","E",v35["without_Alternaria"]["lower_rank_tail"]["E"],v35["without_Alternaria"]["lower_rank_tail"]["p"])

    return r


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args=parser.parse_args()

    data=load()
    output=rows(data)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.json.parent.mkdir(parents=True, exist_ok=True)

    fields=["figure","panel","system","target","metric","value","permutation_p","note"]
    with args.csv.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    args.json.write_text(
        json.dumps(
            {
                "schema":"eog.history_storage.figure_data.v1",
                "source_fingerprints":{k:v[1] for k,v in SOURCES.items()},
                "rows":output,
            },
            indent=2,
            allow_nan=False,
        )+"\n",
        encoding="utf-8",
    )
    print(f"wrote {len(output)} rows")


if __name__ == "__main__":
    main()
