"""Execute the frozen A-Islands support/reachability benchmark.

This runner implements the already-frozen contracts from PRs #80-#83. It does not
choose taxa, folds, predictors, graph scenarios, bins, or aggregation rules from the
outcomes it computes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.conditional_reachability import conditional_reachability_concordance
from eog.island_reachability import evaluate_island_reachability
from eog.support_model import SupportModelError, fit_penalized_logistic_support

PREDICTORS = ("bio1", "bio5", "bio6", "bio12", "bio15")
FROZEN_CLIMATE_SHA256 = "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285"
FROZEN_COHORT_SHA256 = "cf645d55b8bcc46be8a8dc5399db736bbcc20bb7114a72c79a5dee61ec918e12"
FROZEN_FOLDS_SHA256 = "221a925e289347069c89354d26acfab83fa3d4bc130b56f0178b8db30ab427fa"
BOOTSTRAP_REPLICATES = 10_000
SIGN_FLIP_REPLICATES = 100_000
RANDOM_SEED = 20260808


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _col(rows: list[dict[str, str]], *names: str) -> str:
    if not rows:
        raise ValueError("input table is empty")
    wanted = {name.casefold() for name in names}
    matches = [key for key in rows[0] if key.casefold() in wanted]
    if len(matches) != 1:
        raise ValueError(f"missing or ambiguous column among {names}; available={list(rows[0])}")
    return matches[0]


def _canonical_id(value: str) -> str:
    text = str(value).strip()
    try:
        number = float(text)
    except ValueError:
        return text
    return str(int(number)) if np.isfinite(number) and number.is_integer() else text


def _auc(labels: np.ndarray, scores: np.ndarray) -> float | None:
    y = np.asarray(labels, dtype=int)
    s = np.asarray(scores, dtype=float)
    pos = s[y == 1]
    neg = s[y == 0]
    if pos.size == 0 or neg.size == 0:
        return None
    delta = pos[:, None] - neg[None, :]
    return float((np.sum(delta > 0) + 0.5 * np.sum(delta == 0)) / delta.size)


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(
    island_data: Path,
    species_data: Path,
    cohort: Path,
    folds: Path,
    climate: Path,
    fold_output: Path,
    species_output: Path,
    summary_output: Path,
) -> dict[str, object]:
    hashes = {
        "cohort": _sha256(cohort),
        "folds": _sha256(folds),
        "climate": _sha256(climate),
        "island_data": _sha256(island_data),
        "species_data": _sha256(species_data),
    }
    if hashes["cohort"] != FROZEN_COHORT_SHA256:
        raise ValueError("cohort does not match frozen pre-outcome SHA-256")
    if hashes["folds"] != FROZEN_FOLDS_SHA256:
        raise ValueError("spatial folds do not match frozen pre-outcome SHA-256")
    if hashes["climate"] != FROZEN_CLIMATE_SHA256:
        raise ValueError("climate table does not match frozen pre-outcome SHA-256")

    islands = _read(island_data)
    species_rows = _read(species_data)
    cohort_rows = _read(cohort)
    fold_rows = _read(folds)
    climate_rows = _read(climate)

    island_list = _col(islands, "List_ID", "list_ID")
    island_id = _col(islands, "Island_ID", "island_ID")
    species_list = _col(species_rows, "List_ID", "list_ID")
    species_name = _col(species_rows, "Species_update", "species_update")
    cohort_name = _col(cohort_rows, "species")
    fold_id_col = _col(fold_rows, "island_id")
    fold_col = _col(fold_rows, "fold")
    x_col = _col(fold_rows, "x")
    y_col = _col(fold_rows, "y")
    climate_id = _col(climate_rows, "island_id")
    climate_cols = [_col(climate_rows, predictor) for predictor in PREDICTORS]

    list_to_island = {_canonical_id(row[island_list]): _canonical_id(row[island_id]) for row in islands}
    surveyed = sorted(
        {_canonical_id(list_to_island[_canonical_id(row[species_list])]) for row in species_rows},
        key=int,
    )
    if len(surveyed) != 842:
        raise ValueError(f"expected 842 surveyed islands, got {len(surveyed)}")

    fold_by_island = {_canonical_id(row[fold_id_col]): int(row[fold_col]) for row in fold_rows}
    coords = {
        _canonical_id(row[fold_id_col]): (float(row[y_col]), float(row[x_col])) for row in fold_rows
    }
    climate_by_island = {
        _canonical_id(row[climate_id]): np.asarray([float(row[col]) for col in climate_cols], dtype=float)
        for row in climate_rows
    }
    if set(fold_by_island) != set(surveyed) or set(climate_by_island) != set(surveyed):
        raise ValueError("fold/climate island universe differs from frozen 842-island universe")
    if sorted(set(fold_by_island.values())) != [1, 2, 3, 4, 5]:
        raise ValueError("frozen evaluation must contain exactly folds 1..5")

    taxa = sorted({row[cohort_name].strip() for row in cohort_rows if row[cohort_name].strip()})
    if len(taxa) != 886:
        raise ValueError(f"expected 886 frozen taxa, got {len(taxa)}")
    taxon_set = set(taxa)
    presence = {taxon: set() for taxon in taxa}
    for row in species_rows:
        taxon = row[species_name].strip()
        if taxon not in taxon_set:
            continue
        list_id = _canonical_id(row[species_list])
        if list_id not in list_to_island:
            raise ValueError(f"species List_ID missing from island_data: {list_id}")
        presence[taxon].add(list_to_island[list_id])

    node_ids = tuple(surveyed)
    x = np.vstack([climate_by_island[node] for node in node_ids])
    lat = np.asarray([coords[node][0] for node in node_ids], dtype=float)
    lon = np.asarray([coords[node][1] for node in node_ids], dtype=float)
    fold_vector = np.asarray([fold_by_island[node] for node in node_ids], dtype=int)

    fold_results: list[dict[str, object]] = []
    species_results: list[dict[str, object]] = []

    for taxon in taxa:
        labels = np.asarray([int(node in presence[taxon]) for node in node_ids], dtype=int)
        taxon_fold_values: list[float] = []
        for fold in range(1, 6):
            heldout = fold_vector == fold
            training = ~heldout
            anchors = training & (labels == 1)
            record: dict[str, object] = {
                "species": taxon,
                "fold": fold,
                "training_presences": int(np.sum(anchors)),
                "training_absences": int(np.sum(training & (labels == 0))),
                "heldout_presences": int(np.sum(heldout & (labels == 1))),
                "heldout_absences": int(np.sum(heldout & (labels == 0))),
                "support_evaluable": 0,
                "reachability_evaluable": 0,
                "primary_evaluable": 0,
                "failure": "",
                "concordance": "",
                "comparable_pairs": 0,
                "informative_strata": 0,
                "support_auc": "",
                "reachability_auc": "",
            }
            try:
                model = fit_penalized_logistic_support(
                    x[training], labels[training], l2_penalty=1.0, min_class_count=5
                )
                support = model.predict_support(x)
                record["support_evaluable"] = 1
                if np.sum(anchors) < 5:
                    raise ValueError("fewer than five training-presence anchors")
                reach = evaluate_island_reachability(
                    node_ids, lat, lon, x, training, anchors
                )
                record["reachability_evaluable"] = 1
                held_labels = labels[heldout]
                held_support = support[heldout]
                held_distance = reach.nearest_anchor_distance_km[heldout]
                held_reach = reach.connected_frequency[heldout]
                concordance = conditional_reachability_concordance(
                    held_labels, held_support, held_distance, held_reach,
                    support_bins=5, distance_bins=5,
                )
                record["comparable_pairs"] = concordance.comparable_pairs
                record["informative_strata"] = concordance.informative_strata
                record["support_auc"] = "" if (value := _auc(held_labels, held_support)) is None else value
                record["reachability_auc"] = "" if (value := _auc(held_labels, held_reach)) is None else value
                if concordance.concordance is not None:
                    record["primary_evaluable"] = 1
                    record["concordance"] = concordance.concordance
                    taxon_fold_values.append(concordance.concordance)
                else:
                    record["failure"] = "no comparable presence-absence pairs within frozen 5x5 strata"
            except (SupportModelError, ValueError, np.linalg.LinAlgError) as exc:
                record["failure"] = str(exc)
            fold_results.append(record)

        species_value = None if not taxon_fold_values else float(np.mean(taxon_fold_values))
        species_results.append({
            "species": taxon,
            "estimable_folds": len(taxon_fold_values),
            "conditional_concordance": "" if species_value is None else species_value,
        })

    estimable = np.asarray(
        [float(row["conditional_concordance"]) for row in species_results if row["conditional_concordance"] != ""],
        dtype=float,
    )
    if estimable.size == 0:
        raise RuntimeError("no species has an estimable primary statistic")
    overall = float(np.mean(estimable))
    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap = np.mean(rng.choice(estimable, size=(BOOTSTRAP_REPLICATES, len(estimable)), replace=True), axis=1)
    bootstrap_ci = [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))]

    centered = estimable - 0.5
    observed_abs = abs(float(np.mean(centered)))
    exceed = 0
    chunk = 1000
    for start in range(0, SIGN_FLIP_REPLICATES, chunk):
        size = min(chunk, SIGN_FLIP_REPLICATES - start)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(size, len(centered)))
        simulated = np.abs(np.mean(signs * centered[None, :], axis=1))
        exceed += int(np.sum(simulated >= observed_abs))
    sign_flip_p = float((exceed + 1) / (SIGN_FLIP_REPLICATES + 1))

    fold_fields = [
        "species", "fold", "training_presences", "training_absences", "heldout_presences",
        "heldout_absences", "support_evaluable", "reachability_evaluable", "primary_evaluable",
        "failure", "concordance", "comparable_pairs", "informative_strata", "support_auc",
        "reachability_auc",
    ]
    _write_csv(fold_output, fold_results, fold_fields)
    _write_csv(species_output, species_results, ["species", "estimable_folds", "conditional_concordance"])

    summary = {
        "status": "first_authoritative_aislands_species_outcome_execution",
        "n_declared_taxa": 886,
        "n_islands": 842,
        "n_species_estimable": int(len(estimable)),
        "overall_conditional_concordance": overall,
        "null": 0.5,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": RANDOM_SEED,
        "bootstrap_95_ci": bootstrap_ci,
        "sign_flip_replicates": SIGN_FLIP_REPLICATES,
        "sign_flip_two_sided_p": sign_flip_p,
        "input_sha256": hashes,
        "fold_output_sha256": _sha256(fold_output),
        "species_output_sha256": _sha256(species_output),
        "authoritative_contracts": ["#80", "#81", "#82", "#83", "#87"],
        "claim_boundary": (
            "Tests added held-out structural information conditional on frozen pointwise support and nearest-training-presence distance; not SDM superiority or dispersal probability."
        ),
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--folds", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--fold-output", type=Path, required=True)
    parser.add_argument("--species-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
