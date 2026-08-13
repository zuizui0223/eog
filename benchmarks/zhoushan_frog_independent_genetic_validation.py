"""One-time Zhoushan pond-frog independent exact-genetic validation.

All graph, coordinate, predictor, estimator and inference choices are frozen upstream.
This is the first program that computes empirical pairwise FST from the released raw
microsatellite workbook and immediately evaluates the frozen EOG predictor ladder.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
import xlrd

from benchmarks.zhoushan_weir_cockerham import all_pairwise_theta
from eog.genetic_validation import GeneticValidationConfig, evaluate_genetic_validation_ladder
from eog.genetic_validation_io import load_population_csv, load_predictor_pair_csv

FROZEN_DIR = Path("benchmarks/frozen/zhoushan_frog_response_free")
POPULATIONS_CSV = FROZEN_DIR / "populations.csv"
PREDICTORS_CSV = FROZEN_DIR / "predictors.csv"
PREDICTOR_MANIFEST = FROZEN_DIR / "predictor_manifest.json"
RAW_MAPPING_CSV = FROZEN_DIR / "raw_population_mapping.csv"

EXPECTED_RAW_MD5 = "0f9d9b36bb0c481f41170ad2d6cc6344"
EXPECTED_RAW_SHA256 = "52ee37e431aff3303d58685cfef064a7ee34cf0117f52eaca3889e21eacebb17"
EXPECTED_POPULATIONS_SHA256 = "a540a3d2ec6dd9b74a2ed80bc040d649cb179ec89e0e60ad87f3e529e96cf6f5"
EXPECTED_PREDICTORS_SHA256 = "dd14cacf10ce39442977b6b68ae7fc45ced7ae78e458e4feb8338fadd138d7d9"
EXPECTED_MANIFEST_FINGERPRINT = "e0a18112d9adfd197958b3e0e1cd1043485055425371b073f2cb74ad917ead70"
EXPECTED_COORDINATE_FINGERPRINT = "decfa791f879c38dd6168240684383b01e2f2ab730de8c36575291c622a4e794"
EXPECTED_OPERATOR_FINGERPRINT = "242d251353d1180d9a39a8698969246264e65a3ba9b6ad3c0a5a3fc3259369df"
EXPECTED_CONNECTIVITY_FINGERPRINT = "2822fbd07b22d4a6f77123077f49f660e99a9641da6cecbf44203b45b5ffefb9"

EXPECTED_IDS = (
    "Guoju", "Xiepu", "Yuanhua", "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi",
    "Mayi", "Taohua", "Dengbu", "Zhujiajian", "Putuoshan", "Zhoushan", "Damao",
    "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Dayushan", "Daishan",
    "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
)
RAW_BLOCK_ORDER = (
    "Haining", "Zhenhai", "Beilun", "Meishan", "Fodu", "Liuheng", "Xiashi", "Huni",
    "Taohua", "Dengbu", "Mayi", "Damao", "Zhujiajian", "Putuoshan", "Zhoushan",
    "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Daishan", "Dayushan",
    "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
)
LOCUS_ORDER = ("Rnh-1", "Rnh-2", "Rnh-3", "Rnh-4", "Rnh-6", "Rnh-9", "Rnh-10", "Rnh-12", "Rnh-13")
EXPECTED_INDIVIDUALS_PER_POPULATION = 30
BOOTSTRAP_SEED = 20260813
BOOTSTRAP_REPLICATES = 10_000
RIDGE_PENALTY = 1.0


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _verify_frozen_predictors() -> dict[str, object]:
    if _digest(POPULATIONS_CSV, "sha256") != EXPECTED_POPULATIONS_SHA256:
        raise ValueError("Zhoushan frozen populations CSV drifted")
    if _digest(PREDICTORS_CSV, "sha256") != EXPECTED_PREDICTORS_SHA256:
        raise ValueError("Zhoushan frozen predictors CSV drifted")
    manifest = json.loads(PREDICTOR_MANIFEST.read_text(encoding="utf-8"))
    checks = {
        "predictor_manifest_fingerprint": EXPECTED_MANIFEST_FINGERPRINT,
        "coordinate_fingerprint": EXPECTED_COORDINATE_FINGERPRINT,
        "operator_fingerprint": EXPECTED_OPERATOR_FINGERPRINT,
        "connectivity_fingerprint": EXPECTED_CONNECTIVITY_FINGERPRINT,
    }
    for key, expected in checks.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Zhoushan frozen predictor manifest drifted: {key}")
    if manifest.get("population_ids") != list(EXPECTED_IDS):
        raise ValueError("Zhoushan frozen population identity/order drifted")
    if manifest.get("n_pairs") != 351 or manifest.get("n_populations") != 27:
        raise ValueError("Zhoushan frozen predictor dimensions drifted")
    if manifest.get("genetic_response_attached") is not False:
        raise ValueError("Zhoushan predictor artifact is no longer response-free")
    return manifest


def _load_raw_mapping() -> dict[str, str]:
    with RAW_MAPPING_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["raw_prefix", "frozen_population_id", "mapping_basis"]:
            raise ValueError("Zhoushan raw population mapping schema drifted")
        rows = list(reader)
    if len(rows) != 27:
        raise ValueError("Zhoushan raw population mapping must contain exactly 27 rows")
    mapping = {row["raw_prefix"].strip(): row["frozen_population_id"].strip() for row in rows}
    if tuple(mapping) != (
        "Haining", "Zhenhai", "Beilun", "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi",
        "Mayi", "Taohua", "Dengbu", "Zhujiajian", "Putuoshan", "Zhoushan", "Damao",
        "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Dayushan", "Daishan",
        "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
    ):
        raise ValueError("Zhoushan raw population mapping order/identity drifted")
    if set(mapping.values()) != set(EXPECTED_IDS):
        raise ValueError("Zhoushan raw population mapping must be one-to-one onto frozen nodes")
    if mapping["Haining"] != "Yuanhua" or mapping["Zhenhai"] != "Xiepu" or mapping["Beilun"] != "Guoju":
        raise ValueError("Zhoushan mainland administrative identity adapter drifted")
    return mapping


def _as_allele(value: object) -> int | None:
    if value in ("", None):
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"unexpected nonnumeric microsatellite allele value: {value!r}")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"microsatellite allele code must be finite and positive: {value!r}")
    rounded = int(round(numeric))
    if abs(numeric - rounded) > 1e-9:
        raise ValueError(f"microsatellite allele code must be integer-valued: {value!r}")
    return rounded


def _individual_prefix(identifier: str) -> str:
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", identifier.strip())
    if not match:
        raise ValueError(f"unexpected Zhoushan individual identifier: {identifier!r}")
    if not (1 <= int(match.group(2)) <= 30):
        raise ValueError(f"Zhoushan individual suffix outside 1..30: {identifier!r}")
    return match.group(1)


def parse_raw_genotypes(path: Path) -> tuple[dict[str, dict[str, list[tuple[int, int] | None]]], dict[str, object]]:
    if _digest(path, "md5") != EXPECTED_RAW_MD5 or _digest(path, "sha256") != EXPECTED_RAW_SHA256:
        raise ValueError("Zhoushan raw microsatellite workbook identity mismatch")
    mapping = _load_raw_mapping()
    book = xlrd.open_workbook(str(path), on_demand=True)
    if book.sheet_names() != ["Microsatellite data"]:
        raise ValueError("Zhoushan raw workbook sheet set drifted")
    sheet = book.sheet_by_index(0)
    if sheet.nrows != 813 or sheet.ncols != 19:
        raise ValueError("Zhoushan raw workbook dimensions drifted")

    observed_loci = tuple(str(sheet.cell_value(0, 1 + 2 * index)).strip() for index in range(9))
    if observed_loci != LOCUS_ORDER:
        raise ValueError(f"Zhoushan raw locus identity/order drifted: {observed_loci}")
    for index in range(9):
        second_header = str(sheet.cell_value(0, 2 + 2 * index)).strip()
        if second_header:
            raise ValueError("Zhoushan second allele columns must have empty header cells")
    if str(sheet.cell_value(1, 0)).strip() != "Mainland populations":
        raise ValueError("Zhoushan mainland category row drifted")
    if str(sheet.cell_value(92, 0)).strip() != "Island populations":
        raise ValueError("Zhoushan island category row drifted")

    populations: dict[str, dict[str, list[tuple[int, int] | None]]] = {
        population: {locus: [] for locus in LOCUS_ORDER} for population in EXPECTED_IDS
    }
    raw_counts = {prefix: 0 for prefix in RAW_BLOCK_ORDER}
    partial_missing = 0
    complete_genotypes = 0
    missing_genotypes = 0
    raw_prefix_sequence = []

    for row_index in list(range(2, 92)) + list(range(93, 813)):
        identifier = str(sheet.cell_value(row_index, 0)).strip()
        prefix = _individual_prefix(identifier)
        if prefix not in mapping:
            raise ValueError(f"unknown Zhoushan raw population prefix: {prefix}")
        raw_counts[prefix] += 1
        if raw_counts[prefix] == 1:
            raw_prefix_sequence.append(prefix)
        population = mapping[prefix]
        for locus_index, locus in enumerate(LOCUS_ORDER):
            left = _as_allele(sheet.cell_value(row_index, 1 + 2 * locus_index))
            right = _as_allele(sheet.cell_value(row_index, 2 + 2 * locus_index))
            if (left is None) != (right is None):
                partial_missing += 1
                genotype = None
                missing_genotypes += 1
            elif left is None:
                genotype = None
                missing_genotypes += 1
            else:
                genotype = (left, right)
                complete_genotypes += 1
            populations[population][locus].append(genotype)

    if tuple(raw_prefix_sequence) != RAW_BLOCK_ORDER:
        raise ValueError(f"Zhoushan raw population block order drifted: {tuple(raw_prefix_sequence)}")
    if any(raw_counts[prefix] != EXPECTED_INDIVIDUALS_PER_POPULATION for prefix in RAW_BLOCK_ORDER):
        raise ValueError(f"Zhoushan raw population counts drifted: {raw_counts}")
    for population in EXPECTED_IDS:
        for locus in LOCUS_ORDER:
            if len(populations[population][locus]) != EXPECTED_INDIVIDUALS_PER_POPULATION:
                raise ValueError(f"Zhoushan population/locus genotype count drifted: {population} {locus}")

    audit = {
        "raw_md5": EXPECTED_RAW_MD5,
        "raw_sha256": EXPECTED_RAW_SHA256,
        "n_populations": 27,
        "n_individuals": sum(raw_counts.values()),
        "individuals_per_population": raw_counts,
        "loci": list(LOCUS_ORDER),
        "n_loci": len(LOCUS_ORDER),
        "complete_diploid_genotypes": complete_genotypes,
        "missing_diploid_genotypes": missing_genotypes,
        "partial_missing_diploid_rows": partial_missing,
        "raw_prefix_sequence": raw_prefix_sequence,
        "raw_to_frozen_population": mapping,
    }
    return populations, audit


def _response_matrix(pair_results) -> tuple[np.ndarray, list[dict[str, object]], dict[str, object]]:
    lookup = {population: index for index, population in enumerate(EXPECTED_IDS)}
    matrix = np.zeros((27, 27), dtype=float)
    rows = []
    invalid = []
    for result in pair_results:
        i = lookup[result.population_a]
        j = lookup[result.population_b]
        theta = float(result.theta)
        if not math.isfinite(theta) or theta < 0.0 or theta >= 1.0:
            invalid.append({"population_a": result.population_a, "population_b": result.population_b, "fst": theta})
        matrix[i, j] = matrix[j, i] = theta
        rows.append(asdict(result))
    if len(rows) != 351:
        raise ValueError("Zhoushan response computation must produce exactly 351 pairs")
    summary = {
        "n_pairs": len(rows),
        "n_nonfinite_or_outside_linearized_domain": len(invalid),
        "invalid_pairs": invalid,
        "min_fst": float(np.nanmin([row["theta"] for row in rows])),
        "max_fst": float(np.nanmax([row["theta"] for row in rows])),
    }
    return matrix, rows, summary


def _predictor_bundle_matrices():
    populations = load_population_csv(POPULATIONS_CSV)
    if tuple(record.population_id for record in populations) != EXPECTED_IDS:
        raise ValueError("Zhoushan archived predictor population order drifted")
    predictors = load_predictor_pair_csv(PREDICTORS_CSV, populations)
    return populations, predictors


def _model_payload(validation) -> list[dict[str, object]]:
    return [
        {
            "model_id": model.model_id,
            "predictor_names": list(model.predictor_names),
            "n_estimable_folds": model.n_estimable_folds,
            "n_total_folds": model.n_total_folds,
            "n_predictions": model.n_predictions,
            "mse": model.mse,
            "mae": model.mae,
            "folds": [asdict(fold) for fold in model.folds],
        }
        for model in validation.models
    ]


def _bootstrap_primary(validation) -> dict[str, object]:
    by_model = {model.model_id: model for model in validation.models}
    reference = by_model["strong_reference"]
    augmented = by_model["strong_reference_eog"]
    ref_folds = {fold.held_out_population: fold for fold in reference.folds}
    aug_folds = {fold.held_out_population: fold for fold in augmented.folds}
    if tuple(ref_folds) != EXPECTED_IDS or tuple(aug_folds) != EXPECTED_IDS:
        raise ValueError("Zhoushan strong-reference LOPO folds do not cover all frozen populations")
    differences = np.asarray(
        [aug_folds[population].mse - ref_folds[population].mse for population in EXPECTED_IDS],
        dtype=float,
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = rng.integers(0, len(differences), size=(BOOTSTRAP_REPLICATES, len(differences)))
    bootstrap_means = np.mean(differences[samples], axis=1)
    lower, upper = np.percentile(bootstrap_means, [2.5, 97.5])
    return {
        "population_order": list(EXPECTED_IDS),
        "per_population_mse_difference": differences.tolist(),
        "mean_difference": float(np.mean(differences)),
        "median_difference": float(np.median(differences)),
        "fraction_negative": float(np.mean(differences < 0.0)),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_95_percentile": [float(lower), float(upper)],
    }


def evaluate(raw_path: Path) -> dict[str, object]:
    manifest = _verify_frozen_predictors()
    populations, genotype_audit = parse_raw_genotypes(raw_path)
    pair_results = all_pairwise_theta(
        populations,
        population_order=EXPECTED_IDS,
        locus_order=LOCUS_ORDER,
    )
    genetic_matrix, response_rows, response_summary = _response_matrix(pair_results)

    base = {
        "status": "pending",
        "study_doi": "10.1111/mec.12634",
        "raw_genotype_provenance": genotype_audit,
        "response_estimator": "Weir-Cockerham-1984-theta-all-nine-loci",
        "response_summary": response_summary,
        "frozen_predictor_manifest_fingerprint": manifest["predictor_manifest_fingerprint"],
        "frozen_operator_fingerprint": manifest["operator_fingerprint"],
        "frozen_connectivity_fingerprint": manifest["connectivity_fingerprint"],
        "response_transform": "FST/(1-FST)",
        "ridge_penalty": RIDGE_PENALTY,
        "validation_scheme": "leave-one-population-out",
        "raw_pairwise_fst": response_rows,
        "claim_boundary": "symmetric neutral microsatellite FST cannot validate migration direction",
    }

    if response_summary["n_nonfinite_or_outside_linearized_domain"]:
        base.update(
            {
                "status": "response_transform_nonadmissible",
                "promotion_go": False,
                "validation_executed": False,
                "reason": "at least one predeclared raw pairwise FST is outside [0,1); values are retained and not clipped",
            }
        )
        base["fingerprint"] = _canonical_sha256(base)
        return base

    _, predictors = _predictor_bundle_matrices()
    validation = evaluate_genetic_validation_ladder(
        EXPECTED_IDS,
        genetic_matrix,
        predictors.geographic_distance,
        predictors.environmental_distance,
        predictors.eog_continuous_distance,
        predictors.eog_disconnected,
        strong_reference_distance=predictors.strong_reference_distance,
        config=GeneticValidationConfig(response_transform="linearized_fst", ridge_penalty=RIDGE_PENALTY),
    )
    by_model = {model.model_id: model for model in validation.models}
    bootstrap = _bootstrap_primary(validation)
    strong_operational = bool(by_model["strong_reference"].mse <= by_model["ibd"].mse)
    mean_negative = bool(bootstrap["mean_difference"] < 0.0)
    bootstrap_excludes_zero = bool(bootstrap["bootstrap_95_percentile"][1] < 0.0)
    go = bool(strong_operational and mean_negative and bootstrap_excludes_zero)
    if not strong_operational:
        status = "indeterminate_strong_reference_failure"
    elif go:
        status = "independent_empirical_genetic_added_information"
    else:
        status = "independent_empirical_genetic_no_added_information"

    base.update(
        {
            "status": status,
            "promotion_go": go,
            "validation_executed": True,
            "models": _model_payload(validation),
            "contrasts": [asdict(contrast) for contrast in validation.contrasts],
            "validation_fingerprint": validation.fingerprint,
            "primary_population_inference": bootstrap,
            "decision_checks": {
                "all_27_populations_and_351_pairs": True,
                "strong_reference_mse_le_ibd": strong_operational,
                "mean_population_delta_mse_lt_zero": mean_negative,
                "bootstrap_upper_95_lt_zero": bootstrap_excludes_zero,
            },
        }
    )
    base["fingerprint"] = _canonical_sha256(base)
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--genotypes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--response-csv", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.genotypes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    rows = result["raw_pairwise_fst"]
    args.response_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.response_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["population_a", "population_b", "fst", "linearized_fst", "n_usable_loci"],
        )
        writer.writeheader()
        for row in rows:
            theta = float(row["theta"])
            linearized = theta / (1.0 - theta) if math.isfinite(theta) and 0.0 <= theta < 1.0 else ""
            writer.writerow(
                {
                    "population_a": row["population_a"],
                    "population_b": row["population_b"],
                    "fst": f"{theta:.12g}",
                    "linearized_fst": "" if linearized == "" else f"{linearized:.12g}",
                    "n_usable_loci": row["n_usable_loci"],
                }
            )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
