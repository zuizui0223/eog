"""Audit the source-index mapping from pinned R seed-123 survreps stage.

Post-exposure source replay. No occupancy likelihood, data cleaning, new
independent field sampling, biological absence, or causal A/B/M inference.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA = "93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
META = {
    "doy", "surv", "site", "date", "method", "num", "0",
    "year", "month", "temp", "humid", "prec"
}
EXPECTED = {
    "published_q1": (27, 351, 144),
    "published_q2": (13, 188, 77),
}
UPSTREAM_COMMIT = "25d4c64da289ffcc14679619bb3b18bd494de872"


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return list(r), list(r.fieldnames)


def verify_source(surveys_path, sites_path):
    if hashlib.sha256(Path(surveys_path).read_bytes()).hexdigest() != SURVEY_SHA:
        raise ValueError("native survey source SHA mismatch")
    if hashlib.sha256(Path(sites_path).read_bytes()).hexdigest() != SITE_SHA:
        raise ValueError("native site source SHA mismatch")


def evaluate_one(original_rows, original_sites, species, mapping, cohort):
    if cohort not in EXPECTED:
        raise ValueError("unexpected cohort")
    nsite, native_n, positive_pairs = EXPECTED[cohort]
    if cohort == "published_q1":
        subset = [
            row for row in original_rows
            if row["site"] not in ("kis-banyato", "vadasz-turjan")
        ]
        roster = {
            row["site"] for row in original_sites
            if row["site"] not in ("kis-banyato", "vadasz-turjan")
        }
    else:
        roster = {
            row["site"] for row in original_sites if row["ci"] == "intervention"
        }
        subset = [row for row in original_rows if row["site"] in roster]
    if len(roster) != nsite or len(subset) != native_n:
        raise ValueError("published source cohort roster changed")
    if len(mapping) != nsite * 20:
        raise ValueError("wrong sample row count")
    orig_ids = {i + 1 for i, row in enumerate(original_rows) if row["site"] in roster}
    by_site_native = defaultdict(list)
    for idx, row in enumerate(original_rows, 1):
        if idx in orig_ids:
            by_site_native[row["site"]].append(row)
    by_site_sample = defaultdict(list)
    sample_ids_by_site = defaultdict(list)
    seen_positions = set()
    for item in mapping:
        site = item.get("site")
        try:
            src_id = int(item["eog_native_row_index"])
            pos = int(item["eog_replay_repeat_index"])
        except (TypeError, KeyError, ValueError) as e:
            raise ValueError("non-integer native source ID or repeat index") from e
        if src_id not in orig_ids or site not in roster or not 1 <= pos <= 20:
            raise ValueError("replay mapped to unexpected cohort or repeat position")
        source = original_rows[src_id - 1]
        if any(item.get(k) != source[k] for k in ("site", "surv", "date", "method")):
            raise ValueError("original source-row identity drift")
        if (site, pos) in seen_positions:
            raise ValueError("same site/repeat index reused")
        seen_positions.add((site, pos))
        sample_ids_by_site[site].append(src_id)
        by_site_sample[site].append(source)
    if set(by_site_sample) != roster:
        raise ValueError("not all declared sites have replayed mapping")
    if any(len(v) != 20 for v in sample_ids_by_site.values()):
        raise ValueError("not exactly 20 pseudo occasions per site")
    all_original_positive = set()
    all_selected_positive = set()
    by_species = {}
    for sp in species:
        sp_original = set()
        sp_sampled = set()
        for site in sorted(roster):
            native_pos = any(int(x[sp]) > 0 for x in by_site_native[site])
            sample_pos = any(int(x[sp]) > 0 for x in by_site_sample[site])
            if native_pos:
                sp_original.add(site)
                all_original_positive.add((site, sp))
            if sample_pos:
                sp_sampled.add(site)
                all_selected_positive.add((site, sp))
        by_species[sp] = {
            "native_positive_sites": len(sp_original),
            "seed123_positive_sites": len(sp_sampled),
            "lost_positive_sites": sorted(sp_original - sp_sampled)
        }
    if len(all_original_positive) != positive_pairs:
        raise ValueError("source-positive species-site count changed")
    if not all_selected_positive <= all_original_positive:
        raise ValueError("resampling cannot create new site-species detections")
    missing = sorted(all_original_positive - all_selected_positive)
    repeats = sum(20 - len(set(ids)) for ids in sample_ids_by_site.values())
    per_site = {
        site: {
            "native_row_count": len(by_site_native[site]),
            "sampled_positions": 20,
            "unique_native_rows_selected": len(set(sample_ids_by_site[site])),
            "duplicated_row_positions": 20 - len(set(sample_ids_by_site[site])),
            "raw_species_detected": sum(
                any(int(x[sp]) > 0 for x in by_site_native[site]) for sp in species
            ),
            "replay_species_detected": sum(
                any(int(x[sp]) > 0 for x in by_site_sample[site]) for sp in species
            ),
        }
        for site in sorted(roster)
    }
    return {
        "cohort": cohort,
        "native_rows": native_n,
        "sites": nsite,
        "sampled_positions": len(mapping),
        "distinct_native_source_rows_selected": sum(
            len(set(v)) for v in sample_ids_by_site.values()
        ),
        "repeated_source_row_positions": repeats,
        "sites_with_source_row_repeats": sum(
            len(set(v)) < 20 for v in sample_ids_by_site.values()
        ),
        "native_positive_species_site_pairs": positive_pairs,
        "seed123_positive_species_site_pairs": len(all_selected_positive),
        "seed123_lost_positive_species_site_pairs": len(missing),
        "lost_species_site_pairs": [
            {"site": site, "species": sp} for site, sp in missing
        ],
        "species": by_species,
        "sites_detail": per_site,
    }



def compare_overlapping_cohorts(q1, q2, map_q1, map_q2):
    """Post-result diagnostic of analyst-cohort-dependent R seed stream.

    The original source observations at common sites are identical, but
    R sampling order can differ when non-focal sites are filtered out.
    """
    common_sites = set(q2["sites_detail"])
    if not common_sites <= set(q1["sites_detail"]):
        raise ValueError("published Q2 site roster not nested in Q1")
    for site in common_sites:
        if q1["sites_detail"][site]["raw_species_detected"] != (
            q2["sites_detail"][site]["raw_species_detected"]
        ):
            raise ValueError("same-site original positive data differ across cohorts")
    map1 = defaultdict(list)
    map2 = defaultdict(list)
    for item in map_q1:
        if item["site"] in common_sites:
            map1[item["site"]].append(int(item["eog_native_row_index"]))
    for item in map_q2:
        map2[item["site"]].append(int(item["eog_native_row_index"]))
    same_sequence = sorted(
        site for site in common_sites if map1[site] == map2[site]
    )
    same_set = sorted(
        site for site in common_sites if set(map1[site]) == set(map2[site])
    )
    if any(len(map1[site]) != 20 or len(map2[site]) != 20 for site in common_sites):
        raise ValueError("shared site missing 20 generated positions")
    q1_lost = {
        (item["site"], item["species"]) for item in q1["lost_species_site_pairs"]
        if item["site"] in common_sites
    }
    q2_lost = {
        (item["site"], item["species"]) for item in q2["lost_species_site_pairs"]
    }
    switch = sorted(q1_lost ^ q2_lost)
    return {
        "status": "POST_EXPOSURE_COHORT_DEPENDENCE_NOT_BIOLOGICAL_CHANGE",
        "shared_native_source_sites": len(common_sites),
        "same_20_source_row_sequence_sites": len(same_sequence),
        "same_unique_source_row_set_sites": len(same_set),
        "q1_lost_native_positive_in_shared_sites": len(q1_lost),
        "q2_lost_native_positive_in_shared_sites": len(q2_lost),
        "disagreeing_pseudodetection_site_species_pairs": len(switch),
        "disagreeing_pairs": [
            {
                "site": site,
                "species": sp,
                "detected_after_Q1_replay": (site, sp) not in q1_lost,
                "detected_after_Q2_replay": (site, sp) not in q2_lost,
            }
            for site, sp in switch
        ],
        "interpretation": (
            "Same source-positive sites have a different seed-123 sampled "
            "row history because the cohort filter changes the order/number "
            "of RNG calls; this is analytical representation dependence, "
            "not natural temporal turnover or new field observations."
        ),
    }

def read_runtime(path):
    vals = {}
    for line in Path(path).read_text().splitlines():
        if "=" not in line:
            raise ValueError("unparseable R runtime line")
        k, v = line.split("=", 1)
        vals[k] = v
    if vals.get("seed") != "123" or vals.get("reps") != "20":
        raise ValueError("runtime not declared seed123/reps20")
    if not vals.get("R_version") or "Rejection" not in vals.get("RNGkind", ""):
        raise ValueError("missing pinned R RNG provenance")
    return vals


def run(survey_path, site_path, replay_dir):
    verify_source(survey_path, site_path)
    original, columns = rows(survey_path)
    site_rows, _ = rows(site_path)
    species = [x for x in columns if x not in META]
    if len(species) != 9:
        raise ValueError("unexpected species roster")
    result = {
        "schema": "eog.wetland_survreps_seed123_r_replay.v1",
        "status": "PINNED_PUBLIC_R_STAGE_REPLAY_NOT_HISTORICAL_PAPER_FIT",
        "analysis_type": "POST_EXPOSURE_SOURCE_METHOD_AUDIT",
        "native_sha256": {"survey": SURVEY_SHA, "site": SITE_SHA},
        "upstream_survreps_commit": UPSTREAM_COMMIT,
        "historical_publication_runtime_verified": False,
        "ecological_occupancy_fitting_permitted": False,
        "cohorts": {},
    }
    mappings = {}
    for cohort in ("published_q1", "published_q2"):
        mapping_path = Path(replay_dir) / f"{cohort}_source_row_mapping.csv"
        runtime_path = Path(replay_dir) / f"{cohort}_runtime.txt"
        mapping, _ = rows(mapping_path)
        mappings[cohort] = mapping
        result["cohorts"][cohort] = {
            "sampling": evaluate_one(
                original, site_rows, species, mapping, cohort
            ),
            "runtime": read_runtime(runtime_path),
            "mapping_sha256": hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
        }
    result["overlapping_cohort_diagnostic"] = compare_overlapping_cohorts(
        result["cohorts"]["published_q1"]["sampling"],
        result["cohorts"]["published_q2"]["sampling"],
        mappings["published_q1"],
        mappings["published_q2"],
    )
    result["interpretation_boundary"] = [
        "The script reproduces one conditional seed-123 sampling stage under a fixed R and public function version, not authors' exact historical fitted occupancy likelihood.",
        "Missing from a resampled table is not field absence; duplications are pseudo-replicates, not additional sampling effort.",
        "The two contradictory same-survey-ID source rows are preserved as in the unmodified published CSV; their physical identity remains unresolved.",
        "No independent A/B/M or movement data, no original treatment effects, and no fourth EOG-WF endpoint.",
    ]
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--surveys", type=Path, required=True)
    p.add_argument("--sites", type=Path, required=True)
    p.add_argument("--replay-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = run(args.surveys, args.sites, args.replay_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print("EOG_WETLAND_R_REPLAY=" + json.dumps({
        "fingerprint": out["fingerprint"],
        "overlap": out["overlapping_cohort_diagnostic"],
        "cohorts": {
            k: {
                "native_positive": v["sampling"]["native_positive_species_site_pairs"],
                "seed123_positive": v["sampling"]["seed123_positive_species_site_pairs"],
                "lost": v["sampling"]["seed123_lost_positive_species_site_pairs"],
                "repeated_positions": v["sampling"]["repeated_source_row_positions"],
                "unique_source_rows": v["sampling"]["distinct_native_source_rows_selected"],
                "runtime": v["runtime"]["R_version"],
                "RNGkind": v["runtime"]["RNGkind"],
            }
            for k, v in out["cohorts"].items()
        },
    }, sort_keys=True))
