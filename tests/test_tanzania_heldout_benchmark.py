from __future__ import annotations

import numpy as np

from eog.tanzania_current_flow_selection import (
    CurrentFlowSelection,
    PairedTierPrediction,
)
from eog.tanzania_heldout_benchmark import (
    SiteCandidateLibrary,
    TanzaniaSiteTable,
    build_site_candidate_library,
    normalize_site_table,
    run_species_fold,
    summarize_prediction_contrast,
)


def _full_sites_rows() -> list[dict[str, object]]:
    rows = []
    for index in range(14):
        region = "E" if index < 9 else "W"
        rows.append(
            {
                "name": f"site-{index:02d}",
                "region": region,
                "patch_number": index + 1,
                "area_ha": float(index + 1),
            }
        )
    return rows


def _payload(offset: float) -> dict[str, np.ndarray]:
    candidate_indices = np.arange(512, dtype=np.int64)
    combinations = np.column_stack(
        [candidate_indices + 1, candidate_indices + 2, candidate_indices + 3]
    )
    base = np.arange(42, dtype=float)[None, :] + 1.0 + offset
    primary = np.repeat(base, 512, axis=0) + candidate_indices[:, None] / 1000.0
    sensitivity = primary + 100.0
    return {
        "candidate_indices": candidate_indices,
        "combinations": combinations,
        "isolation_primary": primary,
        "isolation_sensitivity": sensitivity,
    }


def test_site_candidate_library_preserves_region_and_patch_identity() -> None:
    sites = normalize_site_table(_full_sites_rows())
    library = build_site_candidate_library(
        sites=sites,
        east_payload=_payload(0.0),
        west_payload=_payload(1000.0),
        isolation_mode="primary",
    )
    assert library.isolation_by_site.shape == (512, 14)
    assert library.isolation_by_site[0, 0] == 1.0
    assert library.isolation_by_site[0, 8] == 9.0
    assert library.isolation_by_site[0, 9] == 1010.0
    assert library.isolation_by_site[511, 13] == 1014.511


def _small_sites() -> TanzaniaSiteTable:
    areas = np.asarray([1.0, 2.0, 4.0, 8.0])
    return TanzaniaSiteTable(
        site_ids=("a", "b", "c", "d"),
        regions=("E", "E", "E", "E"),
        patch_numbers=np.asarray([1, 2, 3, 4], dtype=np.int64),
        areas_ha=areas,
        log10_areas_ha=np.log10(areas),
    )


def _small_library() -> SiteCandidateLibrary:
    indices = np.arange(512, dtype=np.int64)
    combinations = np.column_stack([indices + 1, indices + 2, indices + 3])
    isolation = np.repeat(
        np.asarray([[2.0, 3.0, 4.0, 5.0]]), 512, axis=0
    )
    return SiteCandidateLibrary(
        isolation_mode="primary",
        source_field="isolation_primary",
        site_ids=("a", "b", "c", "d"),
        candidate_indices=indices,
        combinations=combinations,
        isolation_by_site=isolation,
    )


def _features(*, invalidate_a: bool = False) -> list[dict[str, object]]:
    rows = []
    for site_id, role, distance, eog in (
        ("a", "training", 0.5, 1.0),
        ("b", "training", 0.7, 0.5),
        ("c", "training", 0.9, 0.25),
        ("d", "heldout", 1.1, 0.0),
    ):
        valid = not (invalidate_a and site_id == "a")
        rows.append(
            {
                "analysis_partition": "primary_loso",
                "fold_id": "fold-d",
                "species_id": "sp",
                "site_id": site_id,
                "region": "E",
                "role": role,
                "feature_valid": valid,
                "failure_reason": None if valid else "synthetic_invalid",
                "nearest_anchor_distance_km": distance if valid else None,
                "log10_1p_nearest_anchor_km": distance if valid else None,
                "eog_connected_frequency": eog if valid else None,
                "eog_median_normalized_bottleneck": 0.4 if valid else None,
            }
        )
    return rows


def _selection() -> CurrentFlowSelection:
    return CurrentFlowSelection(
        selected_candidate_index=2,
        selected_aic=10.0,
        selected_log_likelihood=-1.0,
        selected_pseudo_r2=0.2,
        selected_effective_parameter_count=4,
        n_candidates=512,
        n_valid_candidates=500,
        invalid_reason_counts=(("synthetic", 12),),
        aic_tie_decimals=10,
        heldout_labels_used=False,
    )


def test_species_fold_uses_training_labels_and_one_shared_selection() -> None:
    captured: dict[str, object] = {}

    def selector(**kwargs):
        captured["selection_response"] = np.asarray(kwargs["response_train"]).copy()
        captured["selection_shape"] = np.asarray(
            kwargs["candidate_isolation_train"]
        ).shape
        return _selection(), ()

    def tier_fitter(**kwargs):
        captured["model_response"] = np.asarray(kwargs["response_train"]).copy()
        captured["selected_candidate_index"] = kwargs[
            "selected_candidate_index"
        ]
        return PairedTierPrediction(
            reference_probability=np.asarray([0.4]),
            candidate_probability=np.asarray([0.2]),
            reference_active_predictors=("log10_area_ha",),
            candidate_active_predictors=(
                "log10_area_ha",
                "eog_connected_frequency",
            ),
            reference_dropped_constant_predictors=(),
            candidate_dropped_constant_predictors=(),
            shared_selected_candidate_index=2,
        )

    predictions, group = run_species_fold(
        partition="primary_loso",
        fold_id="fold-d",
        species_id="sp",
        sites=_small_sites(),
        response=np.asarray([1.0, 0.0, 1.0, 0.0]),
        feature_rows=_features(),
        library=_small_library(),
        selector=selector,
        tier_fitter=tier_fitter,
    )
    assert captured["selection_response"].tolist() == [1.0, 0.0, 1.0]
    assert captured["selection_shape"] == (512, 3)
    assert captured["model_response"].tolist() == [1.0, 0.0, 1.0]
    assert captured["selected_candidate_index"] == 2
    assert group["group_valid"] is True
    assert group["selected_candidate_index"] == 2
    assert len(predictions) == 1
    assert predictions[0]["prediction_valid"] is True
    assert predictions[0]["candidate_probability"] == 0.2
    assert predictions[0]["reference_probability"] == 0.4
    assert predictions[0]["log_loss_difference"] < 0.0


def test_single_class_after_structural_row_filter_is_explicit() -> None:
    def selector(**_kwargs):
        return _selection(), ()

    predictions, group = run_species_fold(
        partition="primary_loso",
        fold_id="fold-d",
        species_id="sp",
        sites=_small_sites(),
        response=np.asarray([1.0, 0.0, 0.0, 1.0]),
        feature_rows=_features(invalidate_a=True),
        library=_small_library(),
        selector=selector,
    )
    assert group["group_valid"] is False
    assert group["failure_reason"] == "valid_model_training_rows_single_class"
    assert predictions[0]["prediction_valid"] is False
    assert predictions[0]["reference_probability"] is None


def test_contrast_summary_uses_species_as_replication_unit() -> None:
    rows = []
    for species_id, probabilities in {
        "sp1": [(1, 0.55, 0.80), (0, 0.45, 0.20)],
        "sp2": [(1, 0.60, 0.75), (0, 0.40, 0.25)],
    }.items():
        for index, (observed, reference, candidate) in enumerate(probabilities):
            ref_loss = -np.log(reference if observed else 1.0 - reference)
            cand_loss = -np.log(candidate if observed else 1.0 - candidate)
            ref_brier = (reference - observed) ** 2
            cand_brier = (candidate - observed) ** 2
            rows.append(
                {
                    "species_id": species_id,
                    "site_id": f"{species_id}-{index}",
                    "prediction_valid": True,
                    "failure_reason": None,
                    "observed_presence": observed,
                    "reference_probability": reference,
                    "candidate_probability": candidate,
                    "log_loss_difference": cand_loss - ref_loss,
                    "brier_difference": cand_brier - ref_brier,
                }
            )
    summary = summarize_prediction_contrast(rows)
    assert summary["paired_score_summary"]["n_matched"] == 4
    assert (
        summary["log_loss_species_cluster_inference"][
            "macro_mean_species_difference"
        ]
        < 0.0
    )
    assert (
        summary["brier_species_cluster_inference"][
            "macro_mean_species_difference"
        ]
        < 0.0
    )
