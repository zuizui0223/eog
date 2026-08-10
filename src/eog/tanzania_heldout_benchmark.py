"""Execute the frozen Tanzania current-flow versus EOG held-out contrast.

This module joins four already-audited objects:

* the verified 14-fragment occurrence table and patch areas;
* the frozen 512-candidate current-flow libraries for East and West;
* leakage-safe nearest-anchor and EOG features generated from training labels only;
* the frozen training-only selector, common L2 probability tiers, and scoring rules.

The primary contrast is candidate minus reference, where the reference contains
patch area, the training-selected matrix-aware current-flow quantity, their
interaction, and nearest training-occurrence distance.  The candidate adds only
EOG connected frequency.  Negative held-out loss differences favour EOG.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .tanzania_current_flow_selection import (
    CurrentFlowSelection,
    CurrentFlowSelectionError,
    PairedTierPrediction,
    current_flow_eog_candidate_predictors,
    current_flow_reference_predictors,
    fit_shared_current_flow_reference_and_eog_tiers,
    select_training_current_flow_candidate,
)
from .tanzania_scoring import (
    bernoulli_log_loss,
    brier_score,
    paired_score_summary,
    paired_species_cluster_inference,
    species_cluster_inference,
    species_mean_differences,
)

BENCHMARK_SCHEMA_VERSION = "tanzania_heldout_current_flow_eog_v1"
EXPECTED_SITE_COUNT = 14
EXPECTED_CANDIDATE_COUNT = 512
EXPECTED_ELIGIBLE_SPECIES_COUNT = 60
EXPECTED_ELIGIBLE_SPECIES_SHA256 = (
    "4859178d155db2594a635896d794d1af4c4d655da924489d41ff64e8fc57f135"
)
EXPECTED_DESIGN_FINGERPRINT = (
    "f8b37bb30d230f92ad323870020d34e2225f898b85394124b965a2d0ecdeb324"
)
ISOLATION_FIELDS = {
    "primary": "isolation_primary",
    "inverse_area_sensitivity": "isolation_sensitivity",
}


class TanzaniaHeldoutBenchmarkError(ValueError):
    """Raised when a held-out benchmark input or execution contract is invalid."""


@dataclass(frozen=True)
class TanzaniaSiteTable:
    site_ids: tuple[str, ...]
    regions: tuple[str, ...]
    patch_numbers: np.ndarray
    areas_ha: np.ndarray
    log10_areas_ha: np.ndarray

    def index(self, site_id: str) -> int:
        try:
            return self.site_ids.index(str(site_id))
        except ValueError as exc:
            raise TanzaniaHeldoutBenchmarkError(f"unknown Tanzania site: {site_id}") from exc


@dataclass(frozen=True)
class SiteCandidateLibrary:
    isolation_mode: str
    source_field: str
    site_ids: tuple[str, ...]
    candidate_indices: np.ndarray
    combinations: np.ndarray
    isolation_by_site: np.ndarray


Selector = Callable[..., tuple[CurrentFlowSelection, tuple[Any, ...]]]
TierFitter = Callable[..., PairedTierPrediction]


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_jsonl_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(canonical_json(row).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _finite_float(value: object, label: str) -> float:
    try:
        result = float(value)
    except Exception as exc:
        raise TanzaniaHeldoutBenchmarkError(f"{label} must be numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise TanzaniaHeldoutBenchmarkError(f"{label} must be finite: {value!r}")
    return result


def _binary(value: object, label: str) -> int:
    text = str(value).strip()
    if text in {"0", "0.0"}:
        return 0
    if text in {"1", "1.0"}:
        return 1
    raise TanzaniaHeldoutBenchmarkError(f"{label} must be binary 0/1: {value!r}")


def eligible_species_sha256(species_ids: Sequence[str]) -> str:
    values = sorted(str(value).strip() for value in species_ids)
    if any(not value for value in values) or len(set(values)) != len(values):
        raise TanzaniaHeldoutBenchmarkError("eligible species IDs must be unique and nonblank")
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_site_table(
    sites_rows: Sequence[Mapping[str, object]],
    *,
    strict_source_shape: bool = True,
) -> TanzaniaSiteTable:
    rows: list[tuple[str, str, int, float]] = []
    seen: set[str] = set()
    for row in sites_rows:
        site_id = str(row["name"]).strip()
        region = str(row["region"]).strip()
        patch_number = int(row["patch_number"])
        area_ha = _finite_float(row["area_ha"], f"area for {site_id}")
        if not site_id or site_id in seen:
            raise TanzaniaHeldoutBenchmarkError("site names must be unique and nonblank")
        if region not in {"E", "W"}:
            raise TanzaniaHeldoutBenchmarkError(f"unexpected site region: {region!r}")
        if not 1 <= patch_number <= 42 or area_ha <= 0.0:
            raise TanzaniaHeldoutBenchmarkError(f"invalid site attributes for {site_id}")
        rows.append((site_id, region, patch_number, area_ha))
        seen.add(site_id)
    rows.sort(key=lambda item: item[0])
    if strict_source_shape:
        if len(rows) != EXPECTED_SITE_COUNT:
            raise TanzaniaHeldoutBenchmarkError(
                f"expected {EXPECTED_SITE_COUNT} sites, got {len(rows)}"
            )
        counts = Counter(item[1] for item in rows)
        if counts != Counter({"E": 9, "W": 5}):
            raise TanzaniaHeldoutBenchmarkError(
                f"unexpected East/West site counts: {dict(counts)}"
            )
    areas = np.asarray([item[3] for item in rows], dtype=float)
    return TanzaniaSiteTable(
        site_ids=tuple(item[0] for item in rows),
        regions=tuple(item[1] for item in rows),
        patch_numbers=np.asarray([item[2] for item in rows], dtype=np.int64),
        areas_ha=areas,
        log10_areas_ha=np.log10(areas),
    )


def normalize_occurrence_matrix(
    occurrence_rows: Sequence[Mapping[str, object]],
    *,
    site_ids: Sequence[str],
    species_ids: Sequence[str],
) -> dict[str, np.ndarray]:
    site_order = tuple(str(value) for value in site_ids)
    site_index = {value: index for index, value in enumerate(site_order)}
    species_order = tuple(str(value) for value in species_ids)
    species_set = set(species_order)
    output = {
        species_id: np.full(len(site_order), -1, dtype=np.int8)
        for species_id in species_order
    }
    for row in occurrence_rows:
        species_id = str(row["species"]).strip()
        if species_id not in species_set:
            continue
        site_id = str(row["name"]).strip()
        if site_id not in site_index:
            raise TanzaniaHeldoutBenchmarkError(f"unknown occurrence site: {site_id}")
        index = site_index[site_id]
        if output[species_id][index] != -1:
            raise TanzaniaHeldoutBenchmarkError(
                f"duplicate occurrence row: {species_id}@{site_id}"
            )
        output[species_id][index] = _binary(
            row["occur"], f"occurrence {species_id}@{site_id}"
        )
    for species_id, values in output.items():
        if np.any(values < 0):
            missing = [
                site_order[index] for index in np.flatnonzero(values < 0).tolist()
            ]
            raise TanzaniaHeldoutBenchmarkError(
                f"incomplete occurrence rows for {species_id}: {missing}"
            )
    return output


def validate_design_contract(design: Mapping[str, Any]) -> tuple[str, ...]:
    if design.get("status") != "tanzania_geometry_and_formula_contract_frozen_before_outcomes":
        raise TanzaniaHeldoutBenchmarkError("frozen Tanzania design contract is required")
    if design.get("design_fingerprint") != EXPECTED_DESIGN_FINGERPRINT:
        raise TanzaniaHeldoutBenchmarkError("Tanzania design fingerprint drifted")
    source = dict(design.get("source") or {})
    eligible = tuple(str(value) for value in source.get("eligible_species", []))
    if len(eligible) != EXPECTED_ELIGIBLE_SPECIES_COUNT:
        raise TanzaniaHeldoutBenchmarkError("Tanzania design must contain 60 eligible species")
    digest = eligible_species_sha256(eligible)
    if digest != EXPECTED_ELIGIBLE_SPECIES_SHA256:
        raise TanzaniaHeldoutBenchmarkError("eligible species fingerprint drifted")
    if source.get("eligible_species_sha256") != digest:
        raise TanzaniaHeldoutBenchmarkError("design eligible-species digest is inconsistent")
    return eligible


def _candidate_payload(payload: Mapping[str, np.ndarray], label: str) -> dict[str, np.ndarray]:
    required = {
        "candidate_indices",
        "combinations",
        "isolation_primary",
        "isolation_sensitivity",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise TanzaniaHeldoutBenchmarkError(f"{label} candidate payload missing {missing}")
    output = {key: np.asarray(payload[key]) for key in required}
    if not np.array_equal(
        output["candidate_indices"], np.arange(EXPECTED_CANDIDATE_COUNT, dtype=np.int64)
    ):
        raise TanzaniaHeldoutBenchmarkError(f"{label} candidate indices are not 0..511")
    if output["combinations"].shape != (EXPECTED_CANDIDATE_COUNT, 3):
        raise TanzaniaHeldoutBenchmarkError(f"{label} resistance combinations have wrong shape")
    for field in ("isolation_primary", "isolation_sensitivity"):
        values = np.asarray(output[field], dtype=float)
        if values.shape != (EXPECTED_CANDIDATE_COUNT, 42):
            raise TanzaniaHeldoutBenchmarkError(f"{label} {field} has wrong shape")
        if not np.isfinite(values).all() or np.any(values <= 0.0):
            raise TanzaniaHeldoutBenchmarkError(f"{label} {field} must be finite and positive")
        output[field] = values
    return output


def build_site_candidate_library(
    *,
    sites: TanzaniaSiteTable,
    east_payload: Mapping[str, np.ndarray],
    west_payload: Mapping[str, np.ndarray],
    isolation_mode: str,
) -> SiteCandidateLibrary:
    if isolation_mode not in ISOLATION_FIELDS:
        raise TanzaniaHeldoutBenchmarkError(
            f"unknown isolation mode {isolation_mode!r}; expected {sorted(ISOLATION_FIELDS)}"
        )
    east = _candidate_payload(east_payload, "East")
    west = _candidate_payload(west_payload, "West")
    if not np.array_equal(east["candidate_indices"], west["candidate_indices"]):
        raise TanzaniaHeldoutBenchmarkError("East/West candidate indices differ")
    if not np.array_equal(east["combinations"], west["combinations"]):
        raise TanzaniaHeldoutBenchmarkError("East/West resistance-grid ordering differs")
    field = ISOLATION_FIELDS[isolation_mode]
    isolation = np.empty(
        (EXPECTED_CANDIDATE_COUNT, len(sites.site_ids)), dtype=float
    )
    for site_index, (region, patch_number) in enumerate(
        zip(sites.regions, sites.patch_numbers.tolist(), strict=True)
    ):
        payload = east if region == "E" else west
        isolation[:, site_index] = payload[field][:, int(patch_number) - 1]
    if not np.isfinite(isolation).all() or np.any(isolation <= 0.0):
        raise TanzaniaHeldoutBenchmarkError("assembled site isolation library is invalid")
    return SiteCandidateLibrary(
        isolation_mode=isolation_mode,
        source_field=field,
        site_ids=sites.site_ids,
        candidate_indices=np.asarray(east["candidate_indices"], dtype=np.int64),
        combinations=np.asarray(east["combinations"], dtype=np.int64),
        isolation_by_site=isolation,
    )


def _feature_groups(
    feature_rows: Sequence[Mapping[str, Any]],
    *,
    selected_species: set[str],
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    seen: set[tuple[str, str, str, str]] = set()
    for raw in feature_rows:
        species_id = str(raw["species_id"])
        if species_id not in selected_species:
            continue
        partition = str(raw["analysis_partition"])
        fold_id = str(raw["fold_id"])
        site_id = str(raw["site_id"])
        identity = (partition, fold_id, species_id, site_id)
        if identity in seen:
            raise TanzaniaHeldoutBenchmarkError(f"duplicate feature row: {identity}")
        seen.add(identity)
        groups.setdefault((partition, fold_id, species_id), []).append(dict(raw))
    for rows in groups.values():
        rows.sort(key=lambda row: str(row["site_id"]))
    return dict(sorted(groups.items()))


def _selection_payload(
    selection: CurrentFlowSelection | None,
    library: SiteCandidateLibrary,
) -> dict[str, Any]:
    if selection is None:
        return {
            "selected_candidate_index": None,
            "selected_resistance_combination": None,
            "selected_aic": None,
            "selected_log_likelihood": None,
            "selected_pseudo_r2": None,
            "selected_effective_parameter_count": None,
            "n_valid_candidates": 0,
            "invalid_candidate_reason_counts": {},
        }
    matches = np.flatnonzero(
        library.candidate_indices == selection.selected_candidate_index
    )
    if matches.size != 1:
        raise TanzaniaHeldoutBenchmarkError("selected candidate is absent from library")
    combination = library.combinations[int(matches[0])]
    return {
        "selected_candidate_index": int(selection.selected_candidate_index),
        "selected_resistance_combination": {
            "eucalyptus": int(combination[0]),
            "tea": int(combination[1]),
            "other_agriculture": int(combination[2]),
        },
        "selected_aic": float(selection.selected_aic),
        "selected_log_likelihood": float(selection.selected_log_likelihood),
        "selected_pseudo_r2": float(selection.selected_pseudo_r2),
        "selected_effective_parameter_count": int(
            selection.selected_effective_parameter_count
        ),
        "n_valid_candidates": int(selection.n_valid_candidates),
        "invalid_candidate_reason_counts": dict(selection.invalid_reason_counts),
    }


def _base_prediction_row(
    *,
    partition: str,
    fold_id: str,
    species_id: str,
    site_id: str,
    isolation_mode: str,
    response: int,
    feature: Mapping[str, Any],
    selection_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "analysis_partition": partition,
        "fold_id": fold_id,
        "species_id": species_id,
        "site_id": site_id,
        "region": str(feature["region"]),
        "isolation_mode": isolation_mode,
        "observed_presence": int(response),
        "feature_valid": bool(feature["feature_valid"]),
        "nearest_anchor_distance_km": feature.get("nearest_anchor_distance_km"),
        "log10_1p_nearest_anchor_km": feature.get(
            "log10_1p_nearest_anchor_km"
        ),
        "eog_connected_frequency": feature.get("eog_connected_frequency"),
        "eog_median_normalized_bottleneck": feature.get(
            "eog_median_normalized_bottleneck"
        ),
        **dict(selection_payload),
    }


def _finish_prediction_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload["row_fingerprint_sha256"] = canonical_sha256(payload)
    return payload


def _failed_group_outputs(
    *,
    partition: str,
    fold_id: str,
    species_id: str,
    isolation_mode: str,
    heldout_features: Sequence[Mapping[str, Any]],
    response_by_site: Mapping[str, int],
    selection_payload: Mapping[str, Any],
    failure_reason: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for feature in heldout_features:
        site_id = str(feature["site_id"])
        row = _base_prediction_row(
            partition=partition,
            fold_id=fold_id,
            species_id=species_id,
            site_id=site_id,
            isolation_mode=isolation_mode,
            response=response_by_site[site_id],
            feature=feature,
            selection_payload=selection_payload,
        )
        row.update(
            {
                "prediction_valid": False,
                "failure_reason": failure_reason,
                "reference_probability": None,
                "candidate_probability": None,
                "reference_log_loss": None,
                "candidate_log_loss": None,
                "log_loss_difference": None,
                "reference_brier": None,
                "candidate_brier": None,
                "brier_difference": None,
            }
        )
        output.append(_finish_prediction_row(row))
    return output


def run_species_fold(
    *,
    partition: str,
    fold_id: str,
    species_id: str,
    sites: TanzaniaSiteTable,
    response: np.ndarray,
    feature_rows: Sequence[Mapping[str, Any]],
    library: SiteCandidateLibrary,
    selector: Selector = select_training_current_flow_candidate,
    tier_fitter: TierFitter = fit_shared_current_flow_reference_and_eog_tiers,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if response.shape != (len(sites.site_ids),):
        raise TanzaniaHeldoutBenchmarkError("species response does not align with sites")
    feature_by_site = {str(row["site_id"]): dict(row) for row in feature_rows}
    if set(feature_by_site) != set(sites.site_ids):
        raise TanzaniaHeldoutBenchmarkError(
            f"feature site coverage drift for {partition}/{fold_id}/{species_id}"
        )
    roles = np.asarray(
        [str(feature_by_site[site_id]["role"]) for site_id in sites.site_ids],
        dtype=object,
    )
    if np.any(~np.isin(roles, ("training", "heldout"))):
        raise TanzaniaHeldoutBenchmarkError("feature roles must be training/heldout")
    training_mask = roles == "training"
    heldout_mask = roles == "heldout"
    if not np.any(training_mask) or not np.any(heldout_mask):
        raise TanzaniaHeldoutBenchmarkError("fold must contain training and heldout sites")

    response_by_site = {
        site_id: int(response[index]) for index, site_id in enumerate(sites.site_ids)
    }
    heldout_features = [
        feature_by_site[site_id]
        for site_id in sites.site_ids
        if feature_by_site[site_id]["role"] == "heldout"
    ]
    selection: CurrentFlowSelection | None = None
    selection_failure: str | None = None
    try:
        selection, _fits = selector(
            log_area_train=sites.log10_areas_ha[training_mask],
            candidate_isolation_train=library.isolation_by_site[:, training_mask],
            response_train=response[training_mask],
            candidate_indices=library.candidate_indices,
        )
    except CurrentFlowSelectionError as exc:
        selection_failure = str(exc)
    selection_payload = _selection_payload(selection, library)

    valid_feature = np.asarray(
        [bool(feature_by_site[site_id]["feature_valid"]) for site_id in sites.site_ids],
        dtype=bool,
    )
    model_training_mask = training_mask & valid_feature
    model_heldout_mask = heldout_mask & valid_feature
    training_presence_count = int(np.sum(response[model_training_mask] == 1))
    training_absence_count = int(np.sum(response[model_training_mask] == 0))
    group_base: dict[str, Any] = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "analysis_partition": partition,
        "fold_id": fold_id,
        "species_id": species_id,
        "isolation_mode": library.isolation_mode,
        "selection_training_count": int(np.sum(training_mask)),
        "model_training_count": int(np.sum(model_training_mask)),
        "model_training_presence_count": training_presence_count,
        "model_training_absence_count": training_absence_count,
        "heldout_count": int(np.sum(heldout_mask)),
        "valid_heldout_feature_count": int(np.sum(model_heldout_mask)),
        "heldout_labels_used_in_selection": False,
        "heldout_labels_used_in_fitting": False,
        **selection_payload,
    }
    if selection_failure is not None:
        failure = "current_flow_selection_failed: " + selection_failure
        group = {
            **group_base,
            "group_valid": False,
            "failure_reason": failure,
            "reference_active_predictors": [],
            "candidate_active_predictors": [],
            "reference_dropped_constant_predictors": [],
            "candidate_dropped_constant_predictors": [],
        }
        group["group_fingerprint_sha256"] = canonical_sha256(group)
        return (
            _failed_group_outputs(
                partition=partition,
                fold_id=fold_id,
                species_id=species_id,
                isolation_mode=library.isolation_mode,
                heldout_features=heldout_features,
                response_by_site=response_by_site,
                selection_payload=selection_payload,
                failure_reason=failure,
            ),
            group,
        )
    if not np.any(model_heldout_mask):
        failure = "no_valid_heldout_structural_feature"
    elif training_presence_count < 1 or training_absence_count < 1:
        failure = "valid_model_training_rows_single_class"
    else:
        failure = None
    if failure is not None:
        group = {
            **group_base,
            "group_valid": False,
            "failure_reason": failure,
            "reference_active_predictors": [],
            "candidate_active_predictors": [],
            "reference_dropped_constant_predictors": [],
            "candidate_dropped_constant_predictors": [],
        }
        group["group_fingerprint_sha256"] = canonical_sha256(group)
        return (
            _failed_group_outputs(
                partition=partition,
                fold_id=fold_id,
                species_id=species_id,
                isolation_mode=library.isolation_mode,
                heldout_features=heldout_features,
                response_by_site=response_by_site,
                selection_payload=selection_payload,
                failure_reason=failure,
            ),
            group,
        )

    selected_rows = np.flatnonzero(
        library.candidate_indices == int(selection.selected_candidate_index)
    )
    if selected_rows.size != 1:
        raise TanzaniaHeldoutBenchmarkError("selected candidate index is not unique")
    selected_isolation = library.isolation_by_site[int(selected_rows[0])]
    distances = np.asarray(
        [
            np.nan
            if feature_by_site[site_id].get("log10_1p_nearest_anchor_km") is None
            else float(feature_by_site[site_id]["log10_1p_nearest_anchor_km"])
            for site_id in sites.site_ids
        ],
        dtype=float,
    )
    eog = np.asarray(
        [
            np.nan
            if feature_by_site[site_id].get("eog_connected_frequency") is None
            else float(feature_by_site[site_id]["eog_connected_frequency"])
            for site_id in sites.site_ids
        ],
        dtype=float,
    )
    if not np.isfinite(distances[model_training_mask | model_heldout_mask]).all():
        raise TanzaniaHeldoutBenchmarkError("valid structural distance contains non-finite values")
    if not np.isfinite(eog[model_training_mask | model_heldout_mask]).all():
        raise TanzaniaHeldoutBenchmarkError("valid EOG frequency contains non-finite values")

    reference_train, reference_names = current_flow_reference_predictors(
        log_area=sites.log10_areas_ha[model_training_mask],
        selected_isolation=selected_isolation[model_training_mask],
        log10_1p_anchor_distance_km=distances[model_training_mask],
    )
    candidate_train, candidate_names = current_flow_eog_candidate_predictors(
        log_area=sites.log10_areas_ha[model_training_mask],
        selected_isolation=selected_isolation[model_training_mask],
        log10_1p_anchor_distance_km=distances[model_training_mask],
        eog_connected_frequency=eog[model_training_mask],
    )
    reference_target, target_reference_names = current_flow_reference_predictors(
        log_area=sites.log10_areas_ha[model_heldout_mask],
        selected_isolation=selected_isolation[model_heldout_mask],
        log10_1p_anchor_distance_km=distances[model_heldout_mask],
    )
    candidate_target, target_candidate_names = current_flow_eog_candidate_predictors(
        log_area=sites.log10_areas_ha[model_heldout_mask],
        selected_isolation=selected_isolation[model_heldout_mask],
        log10_1p_anchor_distance_km=distances[model_heldout_mask],
        eog_connected_frequency=eog[model_heldout_mask],
    )
    if reference_names != target_reference_names or candidate_names != target_candidate_names:
        raise TanzaniaHeldoutBenchmarkError("training/target predictor schemas differ")
    try:
        prediction = tier_fitter(
            selected_candidate_index=int(selection.selected_candidate_index),
            response_train=response[model_training_mask],
            reference_predictors_train=reference_train,
            candidate_predictors_train=candidate_train,
            reference_predictors_target=reference_target,
            candidate_predictors_target=candidate_target,
            reference_predictor_names=reference_names,
            candidate_predictor_names=candidate_names,
        )
    except CurrentFlowSelectionError as exc:
        failure = "probability_tier_failed: " + str(exc)
        group = {
            **group_base,
            "group_valid": False,
            "failure_reason": failure,
            "reference_active_predictors": [],
            "candidate_active_predictors": [],
            "reference_dropped_constant_predictors": [],
            "candidate_dropped_constant_predictors": [],
        }
        group["group_fingerprint_sha256"] = canonical_sha256(group)
        return (
            _failed_group_outputs(
                partition=partition,
                fold_id=fold_id,
                species_id=species_id,
                isolation_mode=library.isolation_mode,
                heldout_features=heldout_features,
                response_by_site=response_by_site,
                selection_payload=selection_payload,
                failure_reason=failure,
            ),
            group,
        )

    valid_target_indices = np.flatnonzero(model_heldout_mask)
    probability_by_index = {
        int(site_index): (
            float(prediction.reference_probability[target_index]),
            float(prediction.candidate_probability[target_index]),
        )
        for target_index, site_index in enumerate(valid_target_indices.tolist())
    }
    output: list[dict[str, Any]] = []
    for site_index in np.flatnonzero(heldout_mask).tolist():
        site_id = sites.site_ids[site_index]
        feature = feature_by_site[site_id]
        row = _base_prediction_row(
            partition=partition,
            fold_id=fold_id,
            species_id=species_id,
            site_id=site_id,
            isolation_mode=library.isolation_mode,
            response=int(response[site_index]),
            feature=feature,
            selection_payload=selection_payload,
        )
        if site_index not in probability_by_index:
            row.update(
                {
                    "prediction_valid": False,
                    "failure_reason": str(feature.get("failure_reason") or "invalid_structural_feature"),
                    "reference_probability": None,
                    "candidate_probability": None,
                    "reference_log_loss": None,
                    "candidate_log_loss": None,
                    "log_loss_difference": None,
                    "reference_brier": None,
                    "candidate_brier": None,
                    "brier_difference": None,
                }
            )
        else:
            reference_probability, candidate_probability = probability_by_index[site_index]
            y = np.asarray([response[site_index]], dtype=float)
            reference_ll = float(
                bernoulli_log_loss(y, np.asarray([reference_probability]))[0]
            )
            candidate_ll = float(
                bernoulli_log_loss(y, np.asarray([candidate_probability]))[0]
            )
            reference_br = float(
                brier_score(y, np.asarray([reference_probability]))[0]
            )
            candidate_br = float(
                brier_score(y, np.asarray([candidate_probability]))[0]
            )
            row.update(
                {
                    "prediction_valid": True,
                    "failure_reason": None,
                    "reference_probability": reference_probability,
                    "candidate_probability": candidate_probability,
                    "reference_log_loss": reference_ll,
                    "candidate_log_loss": candidate_ll,
                    "log_loss_difference": candidate_ll - reference_ll,
                    "reference_brier": reference_br,
                    "candidate_brier": candidate_br,
                    "brier_difference": candidate_br - reference_br,
                }
            )
        output.append(_finish_prediction_row(row))

    group = {
        **group_base,
        "group_valid": True,
        "failure_reason": None,
        "reference_active_predictors": list(prediction.reference_active_predictors),
        "candidate_active_predictors": list(prediction.candidate_active_predictors),
        "reference_dropped_constant_predictors": list(
            prediction.reference_dropped_constant_predictors
        ),
        "candidate_dropped_constant_predictors": list(
            prediction.candidate_dropped_constant_predictors
        ),
    }
    group["group_fingerprint_sha256"] = canonical_sha256(group)
    return output, group


def run_benchmark_shard(
    *,
    sites_rows: Sequence[Mapping[str, object]],
    occurrence_rows: Sequence[Mapping[str, object]],
    design: Mapping[str, Any],
    feature_rows: Sequence[Mapping[str, Any]],
    east_payload: Mapping[str, np.ndarray],
    west_payload: Mapping[str, np.ndarray],
    selected_species: Sequence[str],
    isolation_modes: Sequence[str] = ("primary", "inverse_area_sensitivity"),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible = validate_design_contract(design)
    selected = tuple(str(value) for value in selected_species)
    if not selected or len(set(selected)) != len(selected):
        raise TanzaniaHeldoutBenchmarkError("selected species must be unique and nonempty")
    unknown = sorted(set(selected) - set(eligible))
    if unknown:
        raise TanzaniaHeldoutBenchmarkError(f"selected species outside frozen cohort: {unknown}")
    sites = normalize_site_table(sites_rows)
    occurrence = normalize_occurrence_matrix(
        occurrence_rows,
        site_ids=sites.site_ids,
        species_ids=eligible,
    )
    groups = _feature_groups(feature_rows, selected_species=set(selected))
    expected_group_count = len(selected) * 19
    if len(groups) != expected_group_count:
        raise TanzaniaHeldoutBenchmarkError(
            f"expected {expected_group_count} feature groups for selected species, got {len(groups)}"
        )

    predictions: list[dict[str, Any]] = []
    group_summaries: list[dict[str, Any]] = []
    for isolation_mode in isolation_modes:
        library = build_site_candidate_library(
            sites=sites,
            east_payload=east_payload,
            west_payload=west_payload,
            isolation_mode=str(isolation_mode),
        )
        for (partition, fold_id, species_id), rows in groups.items():
            group_predictions, group_summary = run_species_fold(
                partition=partition,
                fold_id=fold_id,
                species_id=species_id,
                sites=sites,
                response=occurrence[species_id].astype(float),
                feature_rows=rows,
                library=library,
            )
            predictions.extend(group_predictions)
            group_summaries.append(group_summary)
    predictions.sort(
        key=lambda row: (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
            str(row["site_id"]),
        )
    )
    group_summaries.sort(
        key=lambda row: (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
        )
    )
    return predictions, group_summaries


def summarize_prediction_contrast(
    prediction_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [dict(row) for row in prediction_rows]
    valid = np.asarray([bool(row["prediction_valid"]) for row in rows], dtype=bool)
    if not np.any(valid):
        raise TanzaniaHeldoutBenchmarkError("no valid matched held-out predictions")
    response = np.asarray([int(row["observed_presence"]) for row in rows], dtype=float)
    reference = np.asarray(
        [np.nan if row["reference_probability"] is None else float(row["reference_probability"]) for row in rows],
        dtype=float,
    )
    candidate = np.asarray(
        [np.nan if row["candidate_probability"] is None else float(row["candidate_probability"]) for row in rows],
        dtype=float,
    )
    species = [str(row["species_id"]) for row in rows]
    score = paired_score_summary(
        response,
        reference,
        candidate,
        reference_valid=valid,
        candidate_valid=valid,
    )
    log_inference = paired_species_cluster_inference(
        response,
        species,
        reference,
        candidate,
        reference_valid=valid,
        candidate_valid=valid,
    )
    brier_difference = np.asarray(
        [np.nan if row["brier_difference"] is None else float(row["brier_difference"]) for row in rows],
        dtype=float,
    )
    brier_inference = species_cluster_inference(
        species,
        brier_difference,
        valid=valid,
    )
    log_species = species_mean_differences(
        species,
        np.asarray(
            [np.nan if row["log_loss_difference"] is None else float(row["log_loss_difference"]) for row in rows],
            dtype=float,
        ),
        valid=valid,
    )
    brier_species = species_mean_differences(species, brier_difference, valid=valid)
    return {
        "paired_score_summary": asdict(score),
        "log_loss_species_cluster_inference": asdict(log_inference),
        "brier_species_cluster_inference": asdict(brier_inference),
        "species_mean_log_loss_differences": log_species,
        "species_mean_brier_differences": brier_species,
        "n_invalid_rows": int(np.sum(~valid)),
        "invalid_reason_counts": dict(
            sorted(
                Counter(
                    str(row["failure_reason"])
                    for row in rows
                    if not bool(row["prediction_valid"])
                ).items()
            )
        ),
    }
