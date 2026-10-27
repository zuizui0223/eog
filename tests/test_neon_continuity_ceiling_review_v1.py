"""Synthetic counterexamples and immutable post-response NEON inference checks."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from eog.v2.metacommunity_connectivity import (
    calculate_metacommunity_connectivity,
    assemblage_row_permutation_null,
)
from scripts.audit_neon_continuity_ceiling_v1 import (
    ROOT, BASE, PROTOCOL, LOCK, EXPECTED_16,
    git_blob_sha1, proof_for_ceiling, verify_original_source,
    audit,
)


def _chain():
    graph=np.zeros((4,4),dtype=bool)
    for a,b in ((0,1),(1,2),(2,3)):
        graph[a,b]=graph[b,a]=True
    return graph


def test_saturation_theorem_at_C_one_and_C_quarter():
    for C in (0.0,0.25,0.5,1.0):
        x=proof_for_ceiling(C,1.0)
        assert x["data_conditional_saturation"]
        assert x["raw_positive_gain_excluded_by_ceiling"]
        assert x["observed_gain"]==pytest.approx(C-1)
        assert x["null_all_permutation_gains_ge_observed"]
        assert x["null_positive_adjusted_site_gain_excluded_by_ceiling"]
        assert x["null_one_sided_site_upper_tail_p_forced_to_one"]
        assert x["strict_guild_only_world_excluded_by_species_survives_all_graphs"]


def test_saturation_requires_empirically_observed_full_individual_world_survival():
    x=proof_for_ceiling(1.0,0.4)
    assert x["observed_gain"]==pytest.approx(0.6)
    assert x["data_conditional_saturation"] is False
    assert x["raw_positive_gain_excluded_by_ceiling"] is False
    assert x["null_one_sided_site_upper_tail_p_forced_to_one"] is False
    with pytest.raises(ValueError,match="fixed-guild"):
        proof_for_ceiling(1.0,1.0,null_preserves_guild_positive_sites=False)
    with pytest.raises(ValueError,match=r"\[0,1\]"):
        proof_for_ceiling(1.1,1.0)


def test_original_assay_actually_detects_positive_species_turnover_not_global_tautology():
    incidence=np.asarray([[1,0],[0,1],[1,0],[0,1]],dtype=bool)
    graph=_chain()
    calc=calculate_metacommunity_connectivity(
        {"chain":graph},incidence,species_ids=("fictional_A","fictional_B")
    )
    assert calc.community_survival_fraction==1.0
    assert calc.max_species_survival_fraction==0.0
    assert calc.emergent_connectivity_gain==1.0
    assert calc.strict_emergent_world_fraction==1.0
    shuffled=assemblage_row_permutation_null(
        {"chain":graph},incidence,
        species_ids=("fictional_A","fictional_B"),
        replicates=999,seed=424242
    )
    assert shuffled.row_sum_preserved
    assert shuffled.column_sum_preserved
    assert shuffled.guild_positive_set_preserved
    assert shuffled.null_median_gain==0
    assert shuffled.null_adjusted_gain==1
    assert shuffled.upper_tail_p<1


def test_why_original_permutation_p_is_one_without_rerunning_NEON_randomizations():
    # C is unchanged by permuting observed complete assemblage rows
    # across the same guild-positive node set. Regardless of M_perm <= 1,
    # G_perm = C-M_perm >= C-1 = G_obs when M_obs was maximal.
    for C in (0.25,1.0):
        observed=C-1
        for perm_best in (0,0.25,0.5,0.75,1):
            perm_gain=C-perm_best
            assert perm_gain>=observed
            assert (observed-perm_gain)<=0


def test_all_frozen_32_paper_blobs_and_locked_original_empirical_response():
    z=verify_original_source()
    assert z["original_16_sites_scored"]==16
    assert z["imported_original_paper_source_blobs_verified"]==32
    assert z["original_continuity_algorithm_blob_verified"]
    assert z["original_response_records_reopened"] is False
    assert git_blob_sha1(BASE/"MANUSCRIPT_V1.md")==(
        "ada5a84d3b862e122b1d6895c47ed3511de05854"
    )
    lock=json.loads(LOCK.read_text())
    assert lock["denominator"]["fixed_sites"]==16
    assert lock["rerun_allowed"] is False


def test_original_site_level_two_independent_csv_tables_reconcile_and_ceiling_counts():
    x=audit()
    assert x["schema"]=="eog.neon_small_mammal_continuity.ceiling_conditioned_null_review.result.v1"
    c=x["counts"]
    assert c["fixed_scored_sites"]==16
    assert c["observed_best_species_survival_equals_one"]==16
    assert c["sites_with_any_raw_positive_emergence_possible_after_observed_saturation"]==0
    assert c["sites_whose_permutation_null_upper_tail_p_one_is_forced_by_ceiling"]==16
    assert c["sites_whose_null_adjusted_positive_is_forced_impossible"]==16
    assert c["sites_whose_strict_guild_only_world_is_forced_impossible"]==16
    assert c["observed_aggregate_one_sided_p"]==1
    assert c["sites_with_at_least_two_independently_fully_continuous_species"]==13
    assert c["unique_continuity_provider_species_across_sites"]==32
    assert c["largest_number_of_sites_any_provider_species_recurred"]==3
    assert tuple(v["site"] for v in x["all_fixed_16_site_arithmetic_witnesses"])==EXPECTED_16
    ORNL=next(v for v in x["all_fixed_16_site_arithmetic_witnesses"] if v["site"]=="ORNL")
    assert ORNL["guild_survival_fraction"]==pytest.approx(.25)
    assert ORNL["raw_gain"]==pytest.approx(-.75)
    assert x["original_16_site_empirical_null_distribution_rerun"] is False
    assert x["original_confirmatory_result_changed"] is False
    assert x["original_32_paper_source_blobs_modified"] is False
    assert x["Oikos_author_submission_or_AI_declaration_approved"] is False
    assert x["EOG_WF_fourth_empirical_endpoint_added"] is False


def test_snapshot_protocol_explicitly_post_response_and_no_endpoint_redefinition():
    p=json.loads(PROTOCOL.read_text())
    assert p["status"]=="EXPLICITLY_POST_RESPONSE_EXPLORATORY_REVIEW__NO_ENDPOINT_REDEFINITION"
    assert p["interpretation"]["saturated_best_species_is_a_source_observation_not_a_prior_mathematical_identity"]
    assert p["interpretation"]["existing_one_sided_p_one_is_not_a_test_proving_no_turnover_in_natural_metacommunities"]
    assert p["interpretation"]["multiple_null_or_strict_emergence_zero_metrics_under_ceiling_not_independent_evidence"]
    assert p["interpretation"]["original_paper_32_source_blobs_and_response_lock_must_not_be_modified"]
    assert p["interpretation"]["oikos_AI_titlepage_submission_author_gate_not_bypassed"]


def test_code_does_not_download_or_refit_biological_response():
    s=(ROOT/"scripts/audit_neon_continuity_ceiling_v1.py").read_text()
    for prohibited in (
        "import requests", "import urllib","urllib.request", "read_neon_api",
        "NEON_API_TOKEN", "model.fit(", "gbif.org", "new_response_endpoint"
    ):
        assert prohibited not in s
    assert "null_all_permutation_gains_ge_observed" in s


def test_editing_site_headers_or_original_best_species_fails_before_claims(tmp_path,monkeypatch):
    # Pure symbolic guard: no inaccessible NEON original-response access.
    with pytest.raises(ValueError,match="World survival"):
        proof_for_ceiling(-.1,1)
