import json
from pathlib import Path


def _data():
    return json.loads(Path("validation/glanville_uploaded_origin_crosswalk_v1/frozen_aggregate_summary_v1.json").read_text())


def _prior():
    return json.loads(Path("validation/glanville_minrelax_empirical_unitfix_v2/frozen_aggregate_summary_v2.json").read_text())


def _contract():
    return json.loads(Path("validation/glanville_uploaded_origin_crosswalk_v1/protocol_v1.json").read_text())


def test_sha_locked_dataset_and_public_encryption_only():
    d=_data();p=_contract()
    assert d["status"]=="CROSSWALK_PASSED_AGGREGATE_ONLY_POST_UPLOAD_EXPLORATORY"
    assert d["upload"]["sha256"]==p["source_published_dataset"]["source_sha256"]
    assert d["reference_2019"]["archive_sha256"]==p["prior_source_repository"]["archive_sha256"]
    assert d["upload"]["bytes"]==137353
    assert d["reference_2019"]["survey_patch_year_rows"]==22406
    assert d["reference_2019"]["network_patches"]==4656
    assert p["raw_user_uploaded_file_in_repo"] is False
    assert p["raw_source_bytes_in_artifact"] is False


def test_family_patch_grain_and_counts_do_not_relabel_true_migration():
    d=_data()
    x=d["input_grain"]
    assert x["assignment_rows"]==799
    assert x["moved_assignment_rows"]==498
    assert x["same_patch_rows"]==301
    assert x["split_families_2_destination_rows"]==39
    assert x["unique_families"]==760
    assert x["moved_assignment_rows"]+x["same_patch_rows"]==x["assignment_rows"]
    assert len(d["per_arrival_year"])==5
    assert sum(y["assigned_rows"] for y in d["per_arrival_year"])==799
    assert sum(y["moved_rows"] for y in d["per_arrival_year"])==498
    assert sum(y["same_patch_rows"] for y in d["per_arrival_year"])==301
    assert sum(y["all_three_survey_rows_matched"] for y in d["per_arrival_year"])==783


def test_original_eog_annual_rosters_replayed_not_redefined():
    d=_data();parent=_prior()
    expected={(p["year"],p["source_lookback_years"]):p for p in parent["annual"]}
    total=0
    for y,stored in d["yearly_EOG_frozen_parent_source_target_roster_replayed"].items():
        old=expected[(int(y),1)]
        assert stored["targets"]==old["n_targets"]
        assert stored["sources"]==old["n_sources"]
        total+=stored["targets"]
    assert total==1465
    assert d["mover_overlap_EOG_recorded_zero_to_positive"]["full_EOG_target_patch_year_denominator_2008_2012"]==total


def test_genetic_source_and_target_overlap_and_multiple_assignments_are_kept_separate():
    d=_data()
    src=d["mover_source_prior_status"]
    assert src["recorded_positive"]+src["recorded_zero"]+src["no_survey_row"]==498
    assert src["recorded_positive"]==475
    assert src["recorded_zero"]==17
    assert src["no_survey_row"]==6
    x=d["mover_overlap_EOG_recorded_zero_to_positive"]
    assert x["assignment_rows"]==172
    assert x["distinct_target_patch_years"]==103
    assert x["joint_source_candidate_and_target_assignment_rows"]==163
    assert x["joint_distinct_target_patch_years"]==100
    assert x["distinct_target_patch_years"]<=x["assignment_rows"]
    assert x["joint_distinct_target_patch_years"]<=x["joint_source_candidate_and_target_assignment_rows"]
    assert sum(y["movers_target_EOG_eligible_rows"] for y in d["per_arrival_year"])==172
    assert sum(y["movers_target_distinct_EOG_patch_years"] for y in d["per_arrival_year"])==103
    assert sum(y["movers_both_source_and_target_eligible_rows"] for y in d["per_arrival_year"])==163


def test_geometric_matching_and_estimand_difference_not_overinterpreted():
    d=_data()
    a=d["geometry_498_moved_assignments"]
    assert a["checkable"]==498
    assert a["absolute_residual_km_median"] < a["q95"] < a["max"]
    selected=d["jointly_eligible_163_movement_rows"]
    assert selected["assigned_exceeds_nearest_by_gt_1km"]<=163
    assert selected["assigned_distance_km_median"] > selected["nearest_previous_year_EOG_recorded_positive_source_km_median"]
    assert any("not" in x.lower() for x in d["scientific_boundary"])


def test_target_year_equal_weighting_does_not_count_repeated_families_as_independent_sites():
    d=_data()
    g=d["distinct_EOG_target_equal_weighting"]
    overlap=d["mover_overlap_EOG_recorded_zero_to_positive"]
    assert g["distinct_patches_by_arrival_year"]==overlap["joint_distinct_target_patch_years"]==100
    assert g["assigned_genetic_family_patch_rows"]==overlap["joint_source_candidate_and_target_assignment_rows"]==163
    assert g["distinct_targets_with_median_assigned_distance_exceeding_nearest_by_gt_1km"]==42
    assert g["median_of_targetwise_assigned_minus_nearest_distance_km"]>0
    assert g["share_of_full_2008_2012_EOG_target_patch_years"]==100/1465
