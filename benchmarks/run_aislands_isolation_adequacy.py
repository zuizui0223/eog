"""Execute the prospectively frozen A-Islands island-isolation adequacy test.

This runner is intentionally narrow.  The scientific design is frozen in
``validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json``.
It must not be used to tune the reference after observing the result.

Primary contrast
----------------
Candidate C minus reference R3 matched held-out log loss, species-macro.
Negative values favour the species-conditioned EOG structural probe.

The runner writes every held-out probability, fold applicability state, species
summary, aggregate inference and a result fingerprint.  Original authoritative
A-Islands/Tanzania outputs are read only for identity checks and are never modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from eog.island_isolation_reference import (
    AISLANDS_ISOLATION_SCALES_KM,
    build_island_isolation_reference_features,
)
from eog.prepared_island_connectivity import PreparedIslandConnectivity
from eog.support_model import fit_penalized_logistic_support


EARTH_RADIUS_KM = 6371.0088
EXPECTED = {
    "folds": "221a925e289347069c89354d26acfab83fa3d4bc130b56f0178b8db30ab427fa",
    "climate": "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285",
    "cohort": "cf645d55b8bcc46be8a8dc5399db736bbcc20bb7114a72c79a5dee61ec918e12",
    "area": "496789783a98e55e1b9552f6f6d28e7b4567ef0f52c795657c7e2fea9c60aae2",
    "mainland": "7d6f52f03702dd0cfae061023a1b2f405e39397de73eaad21b97d24176c4f869",
    "island_data": "d26ae154aeae1e6eab268f22268342077f7e8e7ef000d18a1f052f65866d5bde",
    "species_data": "43e7d2e8deb1d1d635c8db44a7fe68cfb79c2a059a2207914413a62431eb7b0c",
}
CLIMATE_NAMES = ("bio1", "bio5", "bio6", "bio12", "bio15")
TIER_NAMES = ("R0", "R1", "R2", "R3", "C")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def norm_id(value: object) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"[+-]?\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text


def norm_taxon(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def find_unique_sha(root: Path, expected_sha: str) -> Path:
    matches: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.stat().st_size > 50_000_000:
            continue
        try:
            if sha256_file(path) == expected_sha:
                matches.append(path)
        except OSError:
            continue
    if len(matches) != 1:
        raise RuntimeError(f"expected one repository file with SHA {expected_sha}, found {matches}")
    return matches[0]


def _candidate_key(keys: Iterable[str], preferred: Sequence[str]) -> str | None:
    lower = {key.casefold(): key for key in keys}
    for name in preferred:
        if name.casefold() in lower:
            return lower[name.casefold()]
    return None


def load_cohort(path: Path) -> list[str]:
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in ("taxa", "species", "cohort", "authoritative_taxa"):
            if isinstance(payload, dict) and isinstance(payload.get(key), list):
                values = payload[key]
                taxa = [norm_taxon(item.get("taxon") if isinstance(item, dict) else item) for item in values]
                taxa = [x for x in taxa if x]
                if len(taxa) == 886 and len(set(taxa)) == 886:
                    return taxa
        if isinstance(payload, list):
            taxa = [norm_taxon(item.get("taxon") if isinstance(item, dict) else item) for item in payload]
            taxa = [x for x in taxa if x]
            if len(taxa) == 886 and len(set(taxa)) == 886:
                return taxa
        raise ValueError("could not identify 886-taxon cohort in JSON")

    rows = read_csv(path)
    if not rows:
        raise ValueError("empty cohort table")
    keys = list(rows[0])
    primary_key = _candidate_key(keys, ("primary_cohort_included",))
    if primary_key is not None:
        rows = [row for row in rows if str(row.get(primary_key, "")).strip() == "1"]
        if len(rows) != 886:
            raise ValueError(
                "frozen cohort audit must contain exactly 886 rows with "
                f"primary_cohort_included=1, got {len(rows)}"
            )
        keys = list(rows[0])

    preferred = (
        "taxon",
        "taxon_name",
        "species",
        "species_name",
        "species_update",
        "scientific_name",
        "accepted_name",
    )
    ordered: list[str] = []
    preferred_key = _candidate_key(keys, preferred)
    if preferred_key:
        ordered.append(preferred_key)
    ordered.extend(key for key in keys if key not in ordered and key != primary_key)
    for key in ordered:
        taxa = [norm_taxon(row.get(key)) for row in rows]
        taxa = [x for x in taxa if x]
        if len(taxa) == 886 and len(set(taxa)) == 886:
            return taxa
    raise ValueError(f"could not identify 886 unique primary taxa in cohort columns {keys}")


def _load_json_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                return value
    raise ValueError(f"could not resolve row records in {path}")


def load_folds(path: Path) -> dict[str, str]:
    rows = _load_json_rows(path) if path.suffix.casefold() == ".json" else read_csv(path)
    if not rows:
        raise ValueError("empty folds table")
    keys = list(rows[0])
    id_key = _candidate_key(keys, ("island_id", "island_ID", "island", "node_id", "id"))
    fold_key = _candidate_key(keys, ("fold", "fold_id", "outer_fold", "spatial_fold", "block_fold"))
    if id_key is None:
        id_key = next((k for k in keys if "island" in k.casefold() and "id" in k.casefold()), None)
    if fold_key is None:
        fold_key = next((k for k in keys if "fold" in k.casefold()), None)
    if id_key is None or fold_key is None:
        raise ValueError(f"could not identify island/fold columns in {keys}")
    result = {norm_id(row[id_key]): str(row[fold_key]).strip() for row in rows}
    if len(result) != 842 or any(not value for value in result.values()):
        raise ValueError(f"fold mapping must contain 842 islands, got {len(result)}")
    return result


def load_climate(path: Path) -> dict[str, np.ndarray]:
    rows = _load_json_rows(path) if path.suffix.casefold() == ".json" else read_csv(path)
    if not rows:
        raise ValueError("empty climate table")
    keys = list(rows[0])
    id_key = _candidate_key(keys, ("island_id", "island_ID", "island", "node_id", "id"))
    if id_key is None:
        id_key = next((k for k in keys if "island" in k.casefold() and "id" in k.casefold()), None)
    lower = {key.casefold(): key for key in keys}
    climate_keys = []
    for name in CLIMATE_NAMES:
        if name in lower:
            climate_keys.append(lower[name])
        else:
            match = next((key for key in keys if key.casefold().replace("_", "") == name), None)
            if match is None:
                raise ValueError(f"missing {name} in climate columns {keys}")
            climate_keys.append(match)
    if id_key is None:
        raise ValueError("missing island id in climate table")
    result: dict[str, np.ndarray] = {}
    for row in rows:
        island_id = norm_id(row[id_key])
        values = np.asarray([float(row[key]) for key in climate_keys], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite climate values for island {island_id}")
        result[island_id] = values
    if len(result) != 842:
        raise ValueError(f"climate mapping must contain 842 islands, got {len(result)}")
    return result


def load_scalar_table(path: Path, value_name: str) -> dict[str, float]:
    rows = read_csv(path)
    if not rows:
        raise ValueError(f"empty table {path}")
    keys = list(rows[0])
    id_key = _candidate_key(keys, ("island_id", "island_ID"))
    value_key = _candidate_key(keys, (value_name,))
    if id_key is None or value_key is None:
        raise ValueError(f"missing island/value columns in {path}: {keys}")
    result = {norm_id(row[id_key]): float(row[value_key]) for row in rows}
    if len(result) != 842 or any(not math.isfinite(v) for v in result.values()):
        raise ValueError(f"{value_name} table must contain 842 finite values")
    return result


def load_model_audit(path: Path) -> tuple[list[str], np.ndarray]:
    rows = read_csv(path)
    if len(rows) != 842:
        raise ValueError(f"model audit must have 842 rows, got {len(rows)}")
    keys = list(rows[0])
    id_key = _candidate_key(keys, ("island_id", "island_ID"))
    x_key = _candidate_key(keys, ("x", "longitude", "lon", "x_centroid"))
    y_key = _candidate_key(keys, ("y", "latitude", "lat", "y_centroid"))
    if not all((id_key, x_key, y_key)):
        raise ValueError(f"could not identify audit id/x/y columns {keys}")
    ids = [norm_id(row[id_key]) for row in rows]
    coords = np.asarray([[float(row[x_key]), float(row[y_key])] for row in rows], dtype=float)
    if len(set(ids)) != 842 or not np.isfinite(coords).all():
        raise ValueError("audit island ids/coordinates are invalid")
    if np.any(np.abs(coords[:, 0]) > 180) or np.any(np.abs(coords[:, 1]) > 90):
        raise ValueError("A-Islands centroids are not longitude/latitude degrees")
    return ids, coords


def _required_column(rows: list[dict[str, str]], *names: str) -> str:
    if not rows:
        raise ValueError("source table is empty")
    key = _candidate_key(list(rows[0]), names)
    if key is None:
        raise ValueError(f"missing required column among {names}; available={list(rows[0])}")
    return key


def load_presence_sets(
    species_path: Path,
    island_path: Path,
    island_ids: set[str],
    cohort: Sequence[str],
) -> dict[str, set[str]]:
    """Map species List_ID rows to the authoritative surveyed Island_ID universe."""
    island_rows = read_csv(island_path)
    species_rows = read_csv(species_path)
    island_list_key = _required_column(island_rows, "List_ID", "list_ID")
    island_id_key = _required_column(island_rows, "Island_ID", "island_ID")
    species_list_key = _required_column(species_rows, "List_ID", "list_ID")

    list_to_island: dict[str, str] = {}
    for row in island_rows:
        list_id = str(row.get(island_list_key, "")).strip()
        island_id = norm_id(row.get(island_id_key))
        if not list_id or not island_id:
            raise ValueError("blank List_ID or Island_ID in island_data")
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"List_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id

    cohort_set = set(cohort)
    species_keys = list(species_rows[0]) if species_rows else []
    preferred_species_key = _candidate_key(
        species_keys,
        (
            "Species_update",
            "species_update",
            "taxon",
            "taxon_name",
            "species",
            "species_name",
            "scientific_name",
            "accepted_name",
        ),
    )
    candidate_order: list[str] = []
    if preferred_species_key:
        candidate_order.append(preferred_species_key)
    candidate_order.extend(
        key for key in species_keys if key not in candidate_order and key != species_list_key
    )
    species_key = None
    best_overlap = -1
    for key in candidate_order:
        overlap = sum(
            norm_taxon(row.get(key)) in cohort_set
            for row in species_rows[: min(len(species_rows), 50000)]
        )
        if overlap > best_overlap:
            best_overlap = overlap
            species_key = key
    if species_key is None or best_overlap <= 0:
        raise ValueError("could not identify species_data taxon column by frozen cohort overlap")

    result = {taxon: set() for taxon in cohort}
    for row in species_rows:
        list_id = str(row.get(species_list_key, "")).strip()
        if not list_id:
            raise ValueError("blank List_ID in species_data")
        if list_id not in list_to_island:
            raise ValueError(f"species_data List_ID missing from island_data: {list_id}")
        island_id = list_to_island[list_id]
        taxon = norm_taxon(row.get(species_key))
        if island_id in island_ids and taxon in cohort_set:
            result[taxon].add(island_id)

    missing = [taxon for taxon, islands in result.items() if not islands]
    if missing:
        raise ValueError(f"{len(missing)} frozen taxa have no presence rows; first={missing[:5]}")
    return result


def haversine_matrix(coords_lonlat: np.ndarray) -> np.ndarray:
    lon = np.radians(coords_lonlat[:, 0])
    lat = np.radians(coords_lonlat[:, 1])
    dlon = lon[:, None] - lon[None, :]
    dlat = lat[:, None] - lat[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def component_labels(distance_km: np.ndarray, radius_km: float) -> np.ndarray:
    n = distance_km.shape[0]
    parent = np.arange(n, dtype=int)
    rank = np.zeros(n, dtype=np.int8)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    rows, cols = np.where(np.triu(distance_km <= float(radius_km), k=1))
    for a, b in zip(rows.tolist(), cols.tolist()):
        union(int(a), int(b))
    roots = np.asarray([find(i) for i in range(n)], dtype=int)
    unique = {root: idx for idx, root in enumerate(sorted(set(roots.tolist())))}
    return np.asarray([unique[int(root)] for root in roots], dtype=int)


def build_prepared(ids: Sequence[str], coords_lonlat: np.ndarray) -> PreparedIslandConnectivity:
    distance = haversine_matrix(coords_lonlat)
    scenarios = tuple(f"g{int(scale)}_env_none" for scale in AISLANDS_ISOLATION_SCALES_KM)
    labels = tuple(component_labels(distance, scale) for scale in AISLANDS_ISOLATION_SCALES_KM)
    return PreparedIslandConnectivity(
        node_ids=tuple(ids),
        geographic_distance_km=distance,
        scenario_ids=scenarios,
        component_labels=labels,
    )


def fit_probabilities(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    """Fit the authoritative L2 support engine, then predict held-out rows."""
    model = fit_penalized_logistic_support(
        x_train,
        y_train,
        l2_penalty=1.0,
        min_class_count=5,
    )
    probabilities = np.asarray(model.predict_support(x_test), dtype=float)
    if probabilities.shape != (x_test.shape[0],) or not np.isfinite(probabilities).all():
        raise ValueError("support model returned invalid probabilities")
    return np.clip(probabilities, 1e-12, 1.0 - 1e-12)


def reduce_constant_columns(x_train: np.ndarray, x_test: np.ndarray, names: Sequence[str]) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    sd = np.std(x_train, axis=0, ddof=0)
    keep = np.isfinite(sd) & (sd > 1e-12)
    dropped = [name for name, flag in zip(names, keep.tolist()) if not flag]
    kept = [name for name, flag in zip(names, keep.tolist()) if flag]
    if not kept:
        raise ValueError("all predictors are constant/non-finite in outer training")
    return x_train[:, keep], x_test[:, keep], kept, dropped


def binary_log_loss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1.0 - 1e-12)
    y = np.asarray(y, dtype=float)
    return float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log1p(-p))))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def bootstrap_interval(values: np.ndarray, *, reps: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    out = np.empty(reps, dtype=float)
    n = len(values)
    for start in range(0, reps, 1000):
        end = min(reps, start + 1000)
        draws = rng.integers(0, n, size=(end - start, n))
        out[start:end] = np.mean(values[draws], axis=1)
    return float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975))


def sign_flip_p(values: np.ndarray, *, reps: int, seed: int) -> float:
    values = np.asarray(values, dtype=float)
    observed = abs(float(np.mean(values)))
    rng = np.random.default_rng(seed)
    extreme = 0
    n = len(values)
    for start in range(0, reps, 1000):
        m = min(1000, reps - start)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(m, n))
        means = np.mean(signs * values[None, :], axis=1)
        extreme += int(np.sum(np.abs(means) >= observed - 1e-15))
    return float((extreme + 1) / (reps + 1))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if not rows:
            raise ValueError(f"cannot infer CSV columns for empty output {path}")
        fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def tier_matrices(climate: np.ndarray, log_area: np.ndarray, mainland: np.ndarray, feature) -> tuple[dict[str, np.ndarray], dict[str, list[str]]]:
    base_names = list(CLIMATE_NAMES)
    matrices: dict[str, np.ndarray] = {"R0": climate}
    names: dict[str, list[str]] = {"R0": base_names}

    r1_extra = [log_area, mainland, feature.nearest_training_presence_km]
    r1_names = ["log_area_km2", "distance_to_australia_mainland_km", "nearest_training_presence_km"]
    matrices["R1"] = np.column_stack([climate, *r1_extra])
    names["R1"] = base_names + r1_names

    r2_extra = [feature.multi_source_pressure, feature.area_weighted_source_pressure]
    r2_names = ["multi_source_pressure", "area_weighted_source_pressure"]
    matrices["R2"] = np.column_stack([matrices["R1"], *r2_extra])
    names["R2"] = names["R1"] + r2_names

    r3_extra = [
        feature.nearest_other_island_km,
        feature.surrounding_island_pressure,
        feature.surrounding_landmass_pressure,
        feature.unanchored_component_exposure,
        feature.mainland_stepping_stone_frequency,
    ]
    r3_names = [
        "nearest_other_island_km",
        "surrounding_island_pressure",
        "surrounding_landmass_pressure",
        "unanchored_component_exposure",
        "mainland_stepping_stone_frequency",
    ]
    matrices["R3"] = np.column_stack([matrices["R2"], *r3_extra])
    names["R3"] = names["R2"] + r3_names

    matrices["C"] = np.column_stack([matrices["R3"], feature.geography_only_eog_connected_frequency])
    names["C"] = names["R3"] + ["geography_only_eog_connected_frequency"]
    return matrices, names


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = args.repo_root.resolve()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["schema_version"] != "eog_aislands_isolation_adequacy_v1_3":
        raise RuntimeError("wrong island-isolation contract schema")
    if contract["reference_design_status"] != "final_before_extension_species_outcomes":
        raise RuntimeError("reference design is not frozen")
    if contract["outcomes_inspected_for_this_extension"] is not False:
        raise RuntimeError("pre-outcome contract no longer records an uninspected extension")
    if tuple(float(v) for v in contract["scales_km"]) != tuple(AISLANDS_ISOLATION_SCALES_KM):
        raise RuntimeError("contract graph scales drifted")
    if contract["primary_contrast"] != "candidate C minus reference R3 matched held-out log loss":
        raise RuntimeError("primary contrast drifted")

    fold_path = find_unique_sha(repo_root, EXPECTED["folds"])
    climate_path = find_unique_sha(repo_root, EXPECTED["climate"])
    cohort_path = find_unique_sha(repo_root, EXPECTED["cohort"])
    for path, expected in (
        (args.area_csv, EXPECTED["area"]),
        (args.mainland_csv, EXPECTED["mainland"]),
        (args.island_data, EXPECTED["island_data"]),
        (args.species_data, EXPECTED["species_data"]),
    ):
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"input SHA mismatch for {path}: {actual} != {expected}")

    cohort = load_cohort(cohort_path)
    folds = load_folds(fold_path)
    climate_map = load_climate(climate_path)
    island_ids, coords = load_model_audit(args.island_audit_csv)
    if set(island_ids) != set(folds) or set(island_ids) != set(climate_map):
        raise RuntimeError("842-island identities differ across audit/folds/climate")
    area_map = load_scalar_table(args.area_csv, "area_km2")
    mainland_map = load_scalar_table(args.mainland_csv, "distance_to_australia_mainland_km")
    if set(island_ids) != set(area_map) or set(island_ids) != set(mainland_map):
        raise RuntimeError("842-island identities differ across area/mainland inputs")

    id_to_index = {island_id: index for index, island_id in enumerate(island_ids)}
    fold_values = np.asarray([folds[island_id] for island_id in island_ids], dtype=object)
    climate = np.vstack([climate_map[island_id] for island_id in island_ids])
    area = np.asarray([area_map[island_id] for island_id in island_ids], dtype=float)
    mainland = np.asarray([mainland_map[island_id] for island_id in island_ids], dtype=float)
    log_area = np.log(area)
    prepared = build_prepared(island_ids, coords)

    presence_sets = load_presence_sets(args.species_data, args.island_data, set(island_ids), cohort)
    fold_levels = sorted(set(fold_values.tolist()), key=lambda value: (len(str(value)), str(value)))
    if len(fold_levels) != 5:
        raise RuntimeError(f"expected five frozen outer folds, got {fold_levels}")

    prediction_rows: list[dict[str, object]] = []
    fold_rows: list[dict[str, object]] = []
    species_rows: list[dict[str, object]] = []

    for species_index, taxon in enumerate(cohort):
        y = np.zeros(len(island_ids), dtype=int)
        for island_id in presence_sets[taxon]:
            y[id_to_index[island_id]] = 1
        valid_fold_diffs_log: list[float] = []
        valid_fold_diffs_brier: list[float] = []
        valid_fold_count = 0

        for fold in fold_levels:
            test_mask = fold_values == fold
            train_mask = ~test_mask
            n_presence = int(np.sum(y[train_mask] == 1))
            n_absence = int(np.sum(y[train_mask] == 0))
            fold_record: dict[str, object] = {
                "taxon": taxon,
                "fold": fold,
                "training_presences": n_presence,
                "training_absences": n_absence,
                "heldout_rows": int(np.sum(test_mask)),
                "status": "pending",
                "failure_reason": "",
            }
            if n_presence < 5 or n_absence < 5:
                fold_record["status"] = "non_estimable"
                fold_record["failure_reason"] = "insufficient_training_class_count_5_5"
                fold_rows.append(fold_record)
                continue

            anchors = train_mask & (y == 1)
            try:
                feature = build_island_isolation_reference_features(
                    prepared,
                    anchors,
                    train_mask,
                    area,
                    mainland,
                )
                matrices, names = tier_matrices(climate, log_area, mainland, feature)
                probabilities: dict[str, np.ndarray] = {}
                dropped: dict[str, list[str]] = {}
                kept: dict[str, list[str]] = {}
                for tier in TIER_NAMES:
                    x_all = np.asarray(matrices[tier], dtype=float)
                    if not np.isfinite(x_all).all():
                        raise ValueError(f"non-finite predictors in {tier}")
                    x_train, x_test, kept_names, dropped_names = reduce_constant_columns(
                        x_all[train_mask], x_all[test_mask], names[tier]
                    )
                    probabilities[tier] = fit_probabilities(x_train, y[train_mask], x_test)
                    kept[tier] = kept_names
                    dropped[tier] = dropped_names
            except Exception as exc:
                fold_record["status"] = "non_estimable"
                fold_record["failure_reason"] = f"fit_or_feature_failure:{type(exc).__name__}:{exc}"
                fold_rows.append(fold_record)
                continue

            y_test = y[test_mask]
            loss = {tier: binary_log_loss(y_test, probabilities[tier]) for tier in TIER_NAMES}
            brier_score = {tier: brier(y_test, probabilities[tier]) for tier in TIER_NAMES}
            primary_log = loss["C"] - loss["R3"]
            primary_brier = brier_score["C"] - brier_score["R3"]
            valid_fold_diffs_log.append(primary_log)
            valid_fold_diffs_brier.append(primary_brier)
            valid_fold_count += 1
            fold_record.update({
                "status": "evaluable",
                "failure_reason": "",
                "c_minus_r3_log_loss": primary_log,
                "c_minus_r3_brier": primary_brier,
                "kept_predictors_json": json.dumps(kept, sort_keys=True, separators=(",", ":")),
                "dropped_predictors_json": json.dumps(dropped, sort_keys=True, separators=(",", ":")),
            })
            for tier in TIER_NAMES:
                fold_record[f"log_loss_{tier}"] = loss[tier]
                fold_record[f"brier_{tier}"] = brier_score[tier]
            fold_rows.append(fold_record)

            test_indices = np.flatnonzero(test_mask)
            for local_index, node_index in enumerate(test_indices.tolist()):
                row: dict[str, object] = {
                    "taxon": taxon,
                    "fold": fold,
                    "island_id": island_ids[node_index],
                    "observed": int(y[node_index]),
                }
                for tier in TIER_NAMES:
                    row[f"p_{tier}"] = float(probabilities[tier][local_index])
                prediction_rows.append(row)

        if valid_fold_count:
            species_rows.append({
                "taxon": taxon,
                "status": "estimable",
                "evaluable_folds": valid_fold_count,
                "declared_folds": len(fold_levels),
                "c_minus_r3_log_loss": float(np.mean(valid_fold_diffs_log)),
                "c_minus_r3_brier": float(np.mean(valid_fold_diffs_brier)),
            })
        else:
            species_rows.append({
                "taxon": taxon,
                "status": "non_estimable",
                "evaluable_folds": 0,
                "declared_folds": len(fold_levels),
                "c_minus_r3_log_loss": "",
                "c_minus_r3_brier": "",
            })

        if args.progress_every and (species_index + 1) % args.progress_every == 0:
            print(f"completed {species_index + 1}/{len(cohort)} taxa", flush=True)

    estimable = [row for row in species_rows if row["status"] == "estimable"]
    if not estimable:
        raise RuntimeError("no estimable species in island-isolation extension")
    log_values = np.asarray([float(row["c_minus_r3_log_loss"]) for row in estimable], dtype=float)
    brier_values = np.asarray([float(row["c_minus_r3_brier"]) for row in estimable], dtype=float)
    log_ci = bootstrap_interval(log_values, reps=10000, seed=20260812)
    brier_ci = bootstrap_interval(brier_values, reps=10000, seed=20260812)
    log_p = sign_flip_p(log_values, reps=100000, seed=20260812)
    brier_p = sign_flip_p(brier_values, reps=100000, seed=20260812)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "heldout_predictions.csv"
    folds_path = args.output_dir / "fold_applicability_and_scores.csv"
    species_path = args.output_dir / "species_summary.csv"
    write_csv(predictions_path, prediction_rows)
    write_csv(folds_path, fold_rows)
    write_csv(species_path, species_rows)

    failure_counts: dict[str, int] = {}
    for row in fold_rows:
        if row["status"] != "evaluable":
            key = str(row["failure_reason"])
            failure_counts[key] = failure_counts.get(key, 0) + 1

    aggregate = {
        "schema_version": "eog_aislands_isolation_adequacy_outcome_v1",
        "status": "first_and_only_authoritative_island_isolation_adequacy_execution",
        "contract_schema": contract["schema_version"],
        "taxa_declared": len(cohort),
        "taxa_estimable": len(estimable),
        "taxa_non_estimable": len(cohort) - len(estimable),
        "folds_declared": len(fold_rows),
        "folds_evaluable": sum(row["status"] == "evaluable" for row in fold_rows),
        "heldout_predictions": len(prediction_rows),
        "primary": {
            "contrast": "C_minus_R3_matched_heldout_log_loss",
            "favourable_direction": "negative",
            "species_macro_mean": float(np.mean(log_values)),
            "bootstrap_95_ci": list(log_ci),
            "bootstrap_replicates": 10000,
            "sign_flip_two_sided_p": log_p,
            "sign_flip_replicates": 100000,
            "species_favourable_negative": int(np.sum(log_values < 0)),
            "species_zero": int(np.sum(log_values == 0)),
            "species_adverse_positive": int(np.sum(log_values > 0)),
        },
        "secondary": {
            "contrast": "C_minus_R3_matched_heldout_brier",
            "favourable_direction": "negative",
            "species_macro_mean": float(np.mean(brier_values)),
            "bootstrap_95_ci": list(brier_ci),
            "sign_flip_two_sided_p": brier_p,
        },
        "failure_counts": failure_counts,
        "input_sha256": {
            "folds": EXPECTED["folds"],
            "climate": EXPECTED["climate"],
            "cohort": EXPECTED["cohort"],
            "island_data": EXPECTED["island_data"],
            "species_data": EXPECTED["species_data"],
            "area": EXPECTED["area"],
            "mainland": EXPECTED["mainland"],
            "contract": sha256_file(args.contract),
        },
        "output_sha256": {
            "heldout_predictions": sha256_file(predictions_path),
            "fold_applicability_and_scores": sha256_file(folds_path),
            "species_summary": sha256_file(species_path),
        },
        "scientific_boundary": "species-conditioned archipelago increment beyond frozen R3; not dispersal, colonisation, migration, historical-route, or causal-mechanism evidence",
    }
    aggregate["result_fingerprint"] = canonical_json_sha256(aggregate)
    aggregate_path = args.output_dir / "aggregate_result.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    return aggregate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--contract", type=Path, default=Path("validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json"))
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--island-audit-csv", type=Path, required=True)
    parser.add_argument("--area-csv", type=Path, required=True)
    parser.add_argument("--mainland-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--progress-every", type=int, default=50)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
