"""Synthetic source bytes + actual already frozen published aggregate receipts only.

This never downloads or parses bird observation records or genuine Dryad files.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))

from audit_helgeland_ranke2021_published_comparator_v1 import (
    CAT, FILE_IDS, FROZEN, SOURCE,
    compare, hash_locally_authorized_files, validate_manifest,
)


def docs():
    return (
        json.loads(SOURCE.read_text(encoding="utf-8")),
        json.loads(FROZEN.read_text(encoding="utf-8")),
    )


def test_exact_official_2021_inventory_declared_hashes_not_unseen_raw_bytes():
    m, _ = docs()
    validate_manifest(m)
    assert m["source"]["dataset_id"] == 74465
    assert m["source"]["version_id"] == 136299
    assert m["source"]["first_published"] == "2021-08-24"
    assert m["source"]["dataset_doi"] == "10.5061/dryad.v41ns1rx1"
    assert sum(f["size_bytes"] for f in m["files"]) == 618221
    assert set(f["name"] for f in m["files"]) == set(FILE_IDS)
    for f in m["files"]:
        assert len(f["declared_sha256"]) == 64
    assert m["access_gate"]["2021_raw_file_bodies_sha256_verified"] is False
    assert m["access_gate"]["2021_year_island_recruit_values_read"] is False
    assert m["access_gate"]["no_auth_bypass_permitted"] is True


def test_published_2021_recruit_and_2026_raw_positive_marginals_are_distinct():
    m, frozen = docs()
    x = compare(m, frozen)
    p = x["EOG_next_year_direct_positive"]
    a = x["published_confirmed_recruit"]
    assert p["numerator"] == 219 and p["denominator"] == 1272
    assert a["numerator"] == 376 and a["denominator"] == 2192
    assert p["first_followup_vs_next_year_discordant_count"] == 118
    assert a["recruits_recorded_after_recruitment_year"] == 19
    assert p["within_habitat_positive_count"] == 191
    assert a["within_habitat_positive_count"] == 326
    assert x["published_category_counts"] == {
        "farm_to_farm": 99, "farm_to_nonfarm": 19,
        "nonfarm_to_farm": 31, "nonfarm_to_nonfarm": 227,
    }
    assert x["proxy_category_counts"] == {
        "farm_to_farm": 62, "farm_to_nonfarm": 7,
        "nonfarm_to_farm": 21, "nonfarm_to_nonfarm": 129,
    }
    xtra = x["descriptive_aggregate_only"]
    assert abs(xtra["difference_in_proportion_percentage_points"] - 0.06369646054262) < 1e-10
    assert abs(xtra["difference_in_within_habitat_percentage_points"] - 0.51248421257165) < 1e-10
    assert abs(xtra["habitat_transition_distribution_total_variation"] - 0.03325075293889) < 1e-10
    assert x["independent_recruitment_or_movement_validation"] is False
    assert x["individual_level_concordance_evaluable"] is False
    assert x["claim_of_new_biological_effect"] is False
    assert x["EOG_WF_denominator_modified"] is False
    assert "2021_raw_file_bodies_sha256_verified" not in x.get("sources", {})
    assert x["sources"]["2021_source_raw_bodies_verified"] is False


@pytest.mark.parametrize("mutator", [
    lambda x: x["published_recruit_results"].update(confirmed_interisland_dispersers=377),
    lambda x: x["EOG_frozen_proxy"].update(different_island_code_positive_ids=220),
    lambda x: x["scientific_bounds"].update(no_extra_EOG_WF_scored_endpoint=False),
    lambda x: x["access_gate"].update(no_auth_bypass_permitted=False),
    lambda x: x["files"][0].update(declared_sha256="a" * 64),
    lambda x: x["files"][0].update(file_id=9),
])
def test_official_source_claims_and_published_counts_fail_closed(mutator):
    m, f = docs()
    bad = copy.deepcopy(m)
    mutator(bad)
    with pytest.raises(ValueError):
        compare(bad, f)


def test_corrupted_original_frozen_11_island_EOG_proxy_fails():
    m, f = docs()
    bad = copy.deepcopy(f)
    bad["receipt"]["counts"]["named_11_primary_next_different_codes"] += 1
    with pytest.raises(ValueError, match="reconciliation"):
        compare(m, bad)
    bad = copy.deepcopy(f)
    bad["receipt"]["scientific_boundaries"]["no_dispersal_rate_or_true_recruitment"] = False
    with pytest.raises(ValueError, match="Original EOG"):
        compare(m, bad)


def test_offline_sha256_attests_only_exact_user_legitimately_supplied_synthetic_bytes(tmp_path):
    one, two = b"fake synthetic text only", b"another invented original"
    invented = [("a.txt", one), ("b.txt", two),
                ("c.txt", b"third invented"), ("d.txt", b"fourth invented")]
    for name, content in invented:
        (tmp_path / name).write_bytes(content)
    records = [
        {"name": name, "file_id": 111 + index, "size_bytes": len(content),
         "declared_sha256": hashlib.sha256(content).hexdigest()}
        for index, (name, content) in enumerate(invented)
    ]
    x = hash_locally_authorized_files(tmp_path, {"files": records})
    assert len(x["files"]) == 4
    assert x["all_four_authorized_source_bytes_sha256_verified"] is True
    assert x["file_rows_or_columns_read"] is False
    assert x["surveyed_zero_or_2021_2014_forecast_authorized"] is False
    assert "fake synthetic text" not in json.dumps(x)
    assert "another invented" not in json.dumps(x)

    (tmp_path / "b.txt").write_bytes(b"same length, new data....")
    with pytest.raises(ValueError, match="byte-size mismatch|SHA256 mismatch"):
        hash_locally_authorized_files(tmp_path, {"files": records})
    (tmp_path / "b.txt").unlink()
    with pytest.raises(FileNotFoundError, match="missing"):
        hash_locally_authorized_files(tmp_path, {"files": records})


def test_offline_file_parser_refuses_traversal_and_symlink(tmp_path):
    parent = tmp_path / "dir"
    parent.mkdir()
    (parent / "good.txt").write_bytes(b"x")
    r = {"files":[{"name": n, "file_id": idx,
                   "size_bytes": 1, "declared_sha256": hashlib.sha256(b"x").hexdigest()}
                  for idx, n in enumerate(("../good.txt", "good.txt", "good.txt", "good.txt"))]}
    with pytest.raises(ValueError, match="source path"):
        hash_locally_authorized_files(parent, r)
    symlink = parent / "ref.txt"
    symlink.symlink_to(parent / "good.txt")
    r["files"][0]["name"] = "ref.txt"
    with pytest.raises(FileNotFoundError, match="missing"):
        hash_locally_authorized_files(parent, r)


def test_recruit_status_does_not_pretend_to_measure_surveyed_negative():
    m, f = docs()
    x = compare(m, f)
    assert all(x["scientific_bounds"][k] for k in (
        "no_surveyed_zero_or_detection_effort_claim",
        "2021_reference_is_published_overlap_not_independent_heldout_confirmation",
        "aggregate_prevalence_or_habitat_share_agreement_is_NOT_validated_measurement_equivalence",
        "no_extra_EOG_WF_scored_endpoint",
    ))
    assert x["sources"]["individual_or_year_row_join_performed"] is False


def test_actual_comparator_is_offline_only_and_no_file_bodies_claimed():
    code = (ROOT / "scripts/audit_helgeland_ranke2021_published_comparator_v1.py").read_text()
    for forbidden in ("urllib", "requests", "httpx", "boto3", "subprocess", "eval("):
        assert forbidden not in code
    assert code.index("validate_manifest(m)") < code.index("proxy_n =")
