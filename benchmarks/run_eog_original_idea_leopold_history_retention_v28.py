#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import numpy as np

from eog.history_retention import (
    partial_r2_factorial_distance,
    partial_r2_factorial_scalar,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_leopold_history_retention_v28/protocol_v28.json"
MANIFEST = ROOT / "validation/eog_original_idea_leopold_history_retention_v28/common_panel_manifest_v28.json"

SOURCE_REPOSITORY = "dleopold/Populus_priorityEffects"
SOURCE_COMMIT = "d8082daabfccccf3bcbdd631b4438f44c04014c1"
SOURCE = {
    "sample_metadata": (
        "data/Sample_data.csv",
        "dcdc54ff26013714ab29ddce77211ac3b0043938",
    ),
    "otu_table": (
        "output/compiled/OTU.table.csv",
        "8784a02f7617a7cc207e3da8c7798753d082a4b6",
    ),
    "bias": (
        "output/tabs/bias.csv",
        "45167a953653e7706e8a515516309bc6afec4cf5",
    ),
    "rust_measurements": (
        "data/rust_measurements.csv",
        "a98138a2355f72b6946ba34138696d971c2cab37",
    ),
}
FOCAL_TAXA = (
    "Alternaria",
    "Aureobasidium",
    "Cladosporium",
    "Dioszegia",
    "Fusarium",
)
PERMUTATIONS = 9999
SEED = 20261005
PUBLISHED_OUTLIER = "G4.T2.R5.TP1"


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("utf-8")
    return hashlib.sha1(header + payload).hexdigest()


def download_source(path: str, expected_blob: str) -> bytes:
    url = (
        "https://raw.githubusercontent.com/"
        f"{SOURCE_REPOSITORY}/{SOURCE_COMMIT}/{path}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-v28-reproducible-benchmark"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    actual = git_blob_sha(payload)
    if actual != expected_blob:
        raise RuntimeError(
            f"source blob mismatch for {path}: expected {expected_blob}, got {actual}"
        )
    return payload


def read_csv(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    rows = []
    for row in reader:
        rows.append(
            {
                (key or "").strip(): (value or "").strip()
                for key, value in row.items()
            }
        )
    return rows


def read_otu(payload: bytes) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    reader = csv.reader(io.StringIO(payload.decode("utf-8-sig")))
    header = next(reader)
    taxa = tuple(header[1:])
    table: dict[str, dict[str, float]] = {}
    for row in reader:
        if not row:
            continue
        sample_id = row[0]
        values = {
            taxon: float(value)
            for taxon, value in zip(taxa, row[1:], strict=True)
        }
        if sample_id in table:
            raise RuntimeError(f"duplicate OTU sample ID {sample_id}")
        table[sample_id] = values
    return taxa, table


def bray_curtis(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2 or matrix.shape[0] < 2:
        raise ValueError("composition matrix must contain at least two rows")
    n = matrix.shape[0]
    distance = np.zeros((n, n), dtype=float)
    for i in range(n):
        numerator = np.abs(matrix[i + 1 :] - matrix[i]).sum(axis=1)
        denominator = (matrix[i + 1 :] + matrix[i]).sum(axis=1)
        values = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator),
            where=denominator > 0,
        )
        distance[i, i + 1 :] = values
        distance[i + 1 :, i] = values
    return distance


def scalar_residual_ss(values: np.ndarray, labels: np.ndarray) -> float:
    total = 0.0
    for label in np.unique(labels):
        group = values[labels == label]
        total += float(np.sum((group - np.mean(group)) ** 2))
    return total


def distance_residual_ss(distance: np.ndarray, labels: np.ndarray) -> float:
    total = 0.0
    for label in np.unique(labels):
        index = np.flatnonzero(labels == label)
        if index.size <= 1:
            continue
        sub = distance[np.ix_(index, index)]
        total += float(np.sum(np.triu(sub * sub, 1)) / index.size)
    return total


def fast_partial(reduced_ss: float, full_ss: float) -> float:
    if reduced_ss <= 0:
        return 0.0
    value = (reduced_ss - full_ss) / reduced_ss
    if value < -1e-9 or value > 1 + 1e-9:
        raise RuntimeError(f"invalid nested partial R2 {value}")
    return float(np.clip(value, 0.0, 1.0))


def group_labels(genotype: np.ndarray, treatment: np.ndarray) -> np.ndarray:
    return np.asarray(
        [f"{g}\x1f{t}" for g, t in zip(genotype, treatment, strict=True)],
        dtype=object,
    )


def partial_scalar_fast(
    values: np.ndarray,
    genotype: np.ndarray,
    treatment: np.ndarray,
) -> float:
    reduced = scalar_residual_ss(values, genotype)
    full = scalar_residual_ss(values, group_labels(genotype, treatment))
    return fast_partial(reduced, full)


def partial_distance_fast(
    distance: np.ndarray,
    genotype: np.ndarray,
    treatment: np.ndarray,
) -> float:
    reduced = distance_residual_ss(distance, genotype)
    full = distance_residual_ss(distance, group_labels(genotype, treatment))
    return fast_partial(reduced, full)


def permute_within_genotype(
    treatment: np.ndarray,
    genotype: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    result = treatment.copy()
    for level in np.unique(genotype):
        index = np.flatnonzero(genotype == level)
        result[index] = rng.permutation(treatment[index])
    return result


def permutation_profile(
    corrected_distance: np.ndarray,
    raw_distance: np.ndarray,
    rust: np.ndarray,
    genotype: np.ndarray,
    treatment: np.ndarray,
) -> dict:
    observed = {
        "community_corrected": partial_distance_fast(
            corrected_distance, genotype, treatment
        ),
        "community_raw": partial_distance_fast(raw_distance, genotype, treatment),
        "rust_lesion": partial_scalar_fast(rust, genotype, treatment),
    }
    exceed = {key: 0 for key in observed}
    null_values = {key: np.empty(PERMUTATIONS, dtype=float) for key in observed}
    rng = np.random.default_rng(SEED)
    for permutation_index in range(PERMUTATIONS):
        permuted = permute_within_genotype(treatment, genotype, rng)
        stats = {
            "community_corrected": partial_distance_fast(
                corrected_distance, genotype, permuted
            ),
            "community_raw": partial_distance_fast(raw_distance, genotype, permuted),
            "rust_lesion": partial_scalar_fast(rust, genotype, permuted),
        }
        for key, value in stats.items():
            null_values[key][permutation_index] = value
            if value >= observed[key] - 1e-12:
                exceed[key] += 1

    result = {}
    for key in observed:
        values = null_values[key]
        median = float(np.median(values))
        result[key] = {
            "partial_r2": observed[key],
            "permutation_p": (exceed[key] + 1) / (PERMUTATIONS + 1),
            "permutations": PERMUTATIONS,
            "seed": SEED,
            "null_mean": float(np.mean(values)),
            "null_median": median,
            "null_sd": float(np.std(values, ddof=1)),
            "null_q025": float(np.quantile(values, 0.025)),
            "null_q975": float(np.quantile(values, 0.975)),
            "excess_over_null_median": float(observed[key] - median),
            "calibration_role": (
                "summary_of_predeclared_permutation_diagnostic_not_new_primary_estimand"
            ),
        }
    return result


def build_inputs(source: dict[str, bytes], manifest: dict) -> dict:
    metadata = read_csv(source["sample_metadata"])
    bias_rows = read_csv(source["bias"])
    rust_rows = read_csv(source["rust_measurements"])
    otu_taxa, otu = read_otu(source["otu_table"])

    missing_taxa = [taxon for taxon in FOCAL_TAXA if taxon not in otu_taxa]
    if missing_taxa:
        raise RuntimeError(f"missing focal taxa: {missing_taxa}")

    bias = {row["Taxon"]: float(row["Bhat"]) for row in bias_rows}
    missing_bias = [taxon for taxon in FOCAL_TAXA if taxon not in bias]
    if missing_bias:
        raise RuntimeError(f"missing focal bias factors: {missing_bias}")

    metadata_by_id = {}
    for row in metadata:
        sample_id = row["SampID"]
        if sample_id in metadata_by_id:
            raise RuntimeError(f"duplicate metadata sample ID {sample_id}")
        metadata_by_id[sample_id] = row

    rust_by_plant: dict[str, list[dict[str, str]]] = {}
    for row in rust_rows:
        rust_by_plant.setdefault(row["SampID"], []).append(row)

    samples = []
    corrected = []
    raw = []
    rust = []
    first_colonist = []
    genotype = []
    treatment = []
    region = []

    for item in manifest["plants"]:
        sample_id = item["sample_id"]
        plant_id = item["plant_id"]
        if sample_id not in metadata_by_id:
            raise RuntimeError(f"manifest sample absent from metadata: {sample_id}")
        if sample_id not in otu:
            raise RuntimeError(f"manifest sample absent from OTU table: {sample_id}")
        if plant_id not in rust_by_plant:
            raise RuntimeError(f"manifest plant absent from rust table: {plant_id}")

        meta = metadata_by_id[sample_id]
        for key, expected in (
            ("Genotype", item["genotype"]),
            ("Region", item["region"]),
            ("Treatment", item["treatment"]),
        ):
            if meta[key] != expected:
                raise RuntimeError(
                    f"manifest/source mismatch for {sample_id} {key}: "
                    f"{expected!r} vs {meta[key]!r}"
                )

        raw_vector = np.asarray(
            [otu[sample_id][taxon] for taxon in FOCAL_TAXA],
            dtype=float,
        )
        corrected_vector = np.asarray(
            [
                otu[sample_id][taxon] / bias[taxon]
                for taxon in FOCAL_TAXA
            ],
            dtype=float,
        )
        if raw_vector.sum() <= 0 or corrected_vector.sum() <= 0:
            raise RuntimeError(f"zero focal-taxon abundance for {sample_id}")
        raw_vector /= raw_vector.sum()
        corrected_vector /= corrected_vector.sum()

        leaf_area = sum(float(row["Leaf_cm2"]) for row in rust_by_plant[plant_id])
        lesion_area = sum(
            float(row["Lesion_cm2"]) for row in rust_by_plant[plant_id]
        )
        if leaf_area <= 0:
            raise RuntimeError(f"nonpositive leaf area for {plant_id}")

        trt = item["treatment"]
        focal_index = FOCAL_TAXA.index(trt)
        samples.append(sample_id)
        raw.append(raw_vector)
        corrected.append(corrected_vector)
        rust.append(lesion_area / leaf_area)
        first_colonist.append(corrected_vector[focal_index])
        genotype.append(item["genotype"])
        treatment.append(trt)
        region.append(item["region"])

    return {
        "sample_id": np.asarray(samples, dtype=object),
        "corrected": np.vstack(corrected),
        "raw": np.vstack(raw),
        "rust": np.asarray(rust, dtype=float),
        "first_colonist": np.asarray(first_colonist, dtype=float),
        "genotype": np.asarray(genotype, dtype=object),
        "treatment": np.asarray(treatment, dtype=object),
        "region": np.asarray(region, dtype=object),
    }


def score_subset(inputs: dict, mask: np.ndarray) -> dict:
    corrected_distance = bray_curtis(inputs["corrected"][mask])
    raw_distance = bray_curtis(inputs["raw"][mask])
    rust = inputs["rust"][mask]
    genotype = inputs["genotype"][mask]
    treatment = inputs["treatment"][mask]

    generic_corrected = partial_r2_factorial_distance(
        corrected_distance, treatment, genotype
    ).partial_r2
    generic_rust = partial_r2_factorial_scalar(
        rust, treatment, genotype
    ).partial_r2
    fast_corrected = partial_distance_fast(
        corrected_distance, genotype, treatment
    )
    fast_rust = partial_scalar_fast(rust, genotype, treatment)
    if not np.isclose(generic_corrected, fast_corrected, atol=1e-9, rtol=0):
        raise RuntimeError(
            f"generic/fast composition mismatch {generic_corrected} vs {fast_corrected}"
        )
    if not np.isclose(generic_rust, fast_rust, atol=1e-9, rtol=0):
        raise RuntimeError(
            f"generic/fast rust mismatch {generic_rust} vs {fast_rust}"
        )

    return {
        "n": int(mask.sum()),
        "community_corrected_partial_r2": fast_corrected,
        "community_raw_partial_r2": partial_distance_fast(
            raw_distance, genotype, treatment
        ),
        "rust_lesion_partial_r2": fast_rust,
        "first_colonist_partial_r2": partial_scalar_fast(
            inputs["first_colonist"][mask],
            genotype,
            treatment,
        ),
    }


def run() -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v28_target_scoring":
        raise RuntimeError("v28 protocol is not frozen")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["status"] != "frozen_before_target_scoring":
        raise RuntimeError("v28 common panel is not frozen")

    source = {}
    verified = {}
    for key, (path, blob) in SOURCE.items():
        payload = download_source(path, blob)
        source[key] = payload
        verified[key] = {
            "path": path,
            "expected_git_blob_sha": blob,
            "verified_git_blob_sha": git_blob_sha(payload),
            "bytes": len(payload),
        }

    inputs = build_inputs(source, manifest)
    if inputs["sample_id"].size != manifest["counts"]["common_panel"]:
        raise RuntimeError("common-panel row count changed")

    all_mask = np.ones(inputs["sample_id"].size, dtype=bool)
    corrected_distance = bray_curtis(inputs["corrected"])
    raw_distance = bray_curtis(inputs["raw"])

    # Gate: fast permutation statistic must equal the generic frozen engine at the
    # observed labelling before any permutation distribution is scored.
    generic_corrected = partial_r2_factorial_distance(
        corrected_distance, inputs["treatment"], inputs["genotype"]
    ).partial_r2
    generic_rust = partial_r2_factorial_scalar(
        inputs["rust"], inputs["treatment"], inputs["genotype"]
    ).partial_r2
    if not np.isclose(
        generic_corrected,
        partial_distance_fast(
            corrected_distance, inputs["genotype"], inputs["treatment"]
        ),
        atol=1e-9,
        rtol=0,
    ):
        raise RuntimeError("fast distance statistic does not match generic engine")
    if not np.isclose(
        generic_rust,
        partial_scalar_fast(
            inputs["rust"], inputs["genotype"], inputs["treatment"]
        ),
        atol=1e-9,
        rtol=0,
    ):
        raise RuntimeError("fast scalar statistic does not match generic engine")

    primary_perm = permutation_profile(
        corrected_distance,
        raw_distance,
        inputs["rust"],
        inputs["genotype"],
        inputs["treatment"],
    )

    first_colonist_result = partial_r2_factorial_scalar(
        inputs["first_colonist"],
        inputs["treatment"],
        inputs["genotype"],
    )

    outlier_mask = inputs["sample_id"] != PUBLISHED_OUTLIER

    # Composition-only sensitivity: all structurally eligible TP1 plants with OTU data.
    # This is assembled independently from the common panel and never used for rust.
    metadata = read_csv(source["sample_metadata"])
    otu_taxa, otu = read_otu(source["otu_table"])
    bias_rows = read_csv(source["bias"])
    bias = {row["Taxon"]: float(row["Bhat"]) for row in bias_rows}
    comp_all_rows = [
        row
        for row in metadata
        if row["Samp_type"] == "Experiment"
        and row["Timepoint"] == "1"
        and row["Treatment"] in FOCAL_TAXA
        and row["Genotype"] not in {"", "NA"}
        and row["SampID"] in otu
    ]
    comp_all_matrix = []
    comp_all_genotype = []
    comp_all_treatment = []
    for row in comp_all_rows:
        vector = np.asarray(
            [otu[row["SampID"]][taxon] / bias[taxon] for taxon in FOCAL_TAXA],
            dtype=float,
        )
        if vector.sum() <= 0:
            continue
        comp_all_matrix.append(vector / vector.sum())
        comp_all_genotype.append(row["Genotype"])
        comp_all_treatment.append(row["Treatment"])
    comp_all_matrix = np.vstack(comp_all_matrix)
    comp_all_distance = bray_curtis(comp_all_matrix)
    comp_all_r2 = partial_r2_factorial_distance(
        comp_all_distance,
        np.asarray(comp_all_treatment, dtype=object),
        np.asarray(comp_all_genotype, dtype=object),
    ).partial_r2

    by_region = {}
    for reg in ("East", "West"):
        mask = inputs["region"] == reg
        by_region[reg] = score_subset(inputs, mask)

    result = {
        "schema": "eog.original_idea_leopold_history_retention.result.v28",
        "status": "completed_external_target_specific_history_retention",
        "source_commit": SOURCE_COMMIT,
        "source_verification": verified,
        "common_panel": {
            "n": int(inputs["sample_id"].size),
            "genotypes": int(np.unique(inputs["genotype"]).size),
            "treatments": int(np.unique(inputs["treatment"]).size),
        },
        "primary": {
            "fungal_community_composition": primary_perm["community_corrected"],
            "rust_lesion_fraction": primary_perm["rust_lesion"],
        },
        "secondary": {
            "first_colonist_proportional_abundance": {
                "partial_r2": first_colonist_result.partial_r2,
                "permutation_p": None,
                "role": "positive_control_target_definition_depends_on_treatment",
            }
        },
        "sensitivities": {
            "raw_count_composition": primary_perm["community_raw"],
            "published_outlier_exclusion": score_subset(inputs, outlier_mask),
            "composition_all_structurally_eligible_tp1": {
                "n": int(comp_all_matrix.shape[0]),
                "partial_r2": comp_all_r2,
            },
            "by_region_descriptive": by_region,
        },
        "gates": {
            "generic_fast_composition_match": True,
            "generic_fast_rust_match": True,
            "target_score_added_after_protocol_freeze": False,
        },
    }
    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
