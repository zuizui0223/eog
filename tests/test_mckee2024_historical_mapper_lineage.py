"""Offline regression for dated Migration Mapper pre/post-Dryad exporter provenance.

No external network, original animal identifiers, raw GPS or withheld 2h data
needed in GitHub CI. This locks the chronology and negative attribution
boundary, not the actual source-data export software identity.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
LEDGER = ROOT / "post_stop_historical_mapper_lineage_receipt_v1.json"
PRIOR = ROOT / "post_stop_midnight_serialization_receipt_v1.json"
QA = ROOT / "gate0_publisher_metadata_frozen_v1.json"
SHA = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_dryad_identity_exact_sha_and_status_without_heldout_data():
    r = _read(LEDGER)
    old = _read(PRIOR)
    source = r["primary_source"]
    assert source["dryad_doi"] == "10.5061/dryad.15dv41p51"
    assert source["published_date"] == "2024-07-18"
    assert source["file_id"] == 3334125
    assert source["bytes"] == 1539661
    assert source["sha256"] == old["source_sha256"] == SHA
    assert source["source_timestamp_shapes"] == {
        "date_only": 10835,
        "full_datetime": 18118,
        "fully_specified_exact_midnight": 0,
        "fully_specified_00hour_nonmidnight": 379,
    }
    assert len(source["physical_dbf_fields"]) == 11
    assert "Timstmp" in source["physical_dbf_fields"]
    assert r["access_limits"]["dense_2h_GPS_unopened"] is True
    assert r["access_limits"]["source_GPS_original_file_committed"] is False
    assert r["access_limits"]["predictive_EOG_or_BBMM_score_computed"] is False
    assert r["access_limits"]["EOG_WF_frozen_scored"] == 3


def test_immutable_git_commit_timeline_brackets_dryad_publication():
    r = _read(LEDGER)
    commits = r["historical_commits"]
    release = datetime.fromisoformat(r["primary_source"]["published_date"]).replace(tzinfo=timezone.utc)
    pre = [datetime.fromisoformat(c["date_utc"].replace("Z", "+00:00"))
           for c in commits[:3]]
    post = [datetime.fromisoformat(c["date_utc"].replace("Z", "+00:00"))
            for c in commits[3:]]
    assert all(t < release for t in pre)
    assert all(t > release for t in post)
    assert [c["commit"][:8] for c in commits] == [
        "affaea1e", "87b00491", "6d45fb51", "dc32cf36", "4786f018"
    ]
    assert commits[0]["immutable_blob_sha"] == "ba94cfa2888571fdf91d43f112ae0b613f4fc281"
    assert commits[0]["source_url"].startswith(
        "https://github.com/jmerkle1/Migration-Mapper/blob/affaea1ee55830638e20fe712908de188214e2ac/"
    )


def test_source_export_path_claims_bound_to_exact_commit_versions():
    r = _read(LEDGER)
    pre = r["historical_commits"][0]
    assert "as.character" in " ".join(pre["direct_line_evidence"])
    assert "masterCrs4326" in " ".join(pre["direct_line_evidence"])
    assert "lon/lat" in pre["supported"]
    after = r["historical_commits"][3:]
    assert after[0]["relative_to_dryad_publication"] == "AFTER_2024_07_18"
    assert after[1]["relative_to_dryad_publication"] == "AFTER_2024_07_18"
    assert "ADDED" in after[0]["direct_change"]
    assert "lon/lat" in after[1]["direct_change"]
    assert "x/y" in after[1]["direct_change"]
    assert "masterCrs4326" in r["historical_commits"][2]["direct_change"]
    assert "masterCrs" in r["historical_commits"][2]["direct_change"]
    assert len(r["independent_negative_evidence"]) >= 4


def test_source_provenance_limit_not_silently_lifted():
    r = _read(LEDGER)
    claims = r["inference"]
    assert claims["published_as_character_path_pre_dryad"] is True
    assert claims["R43_mechanism_consistent_with_source_pattern"] is True
    assert claims["publisher_source_exact_export_path_identified"] is False
    assert claims["original_R_version_identified"] is False
    assert claims["source_date_only_definitely_midnight"] is False
    assert claims["declared_EPSG3742_vs_Albers_discrepancy_resolved"] is False
    assert r["R_behavior"]["R_runtime_reexecuted_in_this_environment"] is False
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Historical prepublication Migration Mapper code audit" in readme
    report = (ROOT / "POST_STOP_MIDNIGHT_SERIALIZATION_PROVENANCE_20261124.md").read_text(encoding="utf-8")
    assert "## Historical code-dating correction" in report
    author_draft = (ROOT / "SOURCE_AUTHOR_QUERY_DRAFT_20261124.md").read_text(encoding="utf-8")
    assert "## Historical-lineage follow-up for sender review" in author_draft
    assert "UNSENT" in author_draft
