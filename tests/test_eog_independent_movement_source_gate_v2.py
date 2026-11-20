"""Offline security, original publisher pin and scientific STOP checks."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import urllib.request

import pytest

from scripts import eog_independent_movement_source_gate_v2 as m

P = json.loads(Path("validation/independent_movement_source_gate_v2/protocol_v2.json").read_text(encoding="utf-8"))


def _req(host: str) -> urllib.request.Request:
    return urllib.request.Request(f"https://{host}/version/download")


def test_exact_provider_observed_aws_lambda_is_mandatory():
    contract=P["exact_trusted_redirect_contract"]
    assert contract["first_redirect_exact_no_wildcard"] is True
    h=m.ValidatedRedirect(contract)
    correct=contract["first_redirect_must_be_exact_host"]
    new=h.redirect_request(_req("datadryad.org"),None,302,"redirect",{},
                           f"https://{correct}/zip?t=fake")
    assert new is not None
    assert h.mandatory_first_seen
    assert h.hosts == [correct]
    assert "?t=fake" not in str(h.hosts)


def test_first_redirect_rejects_every_unpinned_host():
    h=m.ValidatedRedirect(P["exact_trusted_redirect_contract"])
    for destination in ("unexpected.lambda-url.us-west-2.on.aws","s3.amazonaws.com",
                        "evil.example.org"):
        with pytest.raises(ValueError,match="STOP_FIRST_REDIRECT_HOST_NOT_PINNED"):
            h.redirect_request(_req("datadryad.org"),None,302,"redirect",{},
                               f"https://{destination}/file")


def test_exact_lambda_may_redirect_only_to_restricted_s3_or_cloudfront():
    trusted=P["exact_trusted_redirect_contract"]["first_redirect_must_be_exact_host"]
    h=m.ValidatedRedirect(P["exact_trusted_redirect_contract"])
    h.redirect_request(_req("datadryad.org"),None,302,"a",{},f"https://{trusted}/zip")
    h.redirect_request(_req(trusted),None,302,"b",{},
                       "https://s3.us-west-2.amazonaws.com/dryad/f?Signature=private")
    assert h.hosts == [trusted,"s3.us-west-2.amazonaws.com"]
    assert "private" not in str(h.hosts)
    with pytest.raises(ValueError,match="STOP_UNVERIFIED_LATER_REDIRECT_HOST"):
        h.redirect_request(_req("s3.us-west-2.amazonaws.com"),None,302,"c",{},
                           "https://unrelated.example.org/evil")


def test_invalid_original_url_and_credentials_fail_closed():
    contract=P["exact_trusted_redirect_contract"]
    h=m.ValidatedRedirect(contract)
    with pytest.raises(ValueError,match="STOP_REDIRECT_FROM_NON_PUBLISHER_HOST"):
        h.redirect_request(_req("other.org"),None,302,"x",{},
                           "https://"+contract["first_redirect_must_be_exact_host"]+"/zip")
    with pytest.raises(ValueError,match="STOP_REDIRECT_NON_HTTPS_OR_CREDENTIALS"):
        h.redirect_request(_req("datadryad.org"),None,302,"x",{},
                           "http://"+contract["first_redirect_must_be_exact_host"]+"/zip")


def test_pin_identity_and_sha_gate_can_pass_without_modeling(monkeypatch):
    # Fake only the already-authenticated parser's returned source receipt.
    def fake_qualify(source,base):
        item=next(row for row in P["sources"] if row["id"]==source["id"])
        return {
            "source_id":source["id"],
            "status":"SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED",
            "publisher_version_id":str(item["version_id"]),
            "publisher_publication_date":item["expected_date"],
            "file_checks":[{
                "name":x["name"],"sha256":x["sha256"],"size_bytes":x["size"],
                "csv_header":["id","source","target"] if x["name"].endswith(".csv") else None,
                "data_row_count":0 if x["name"].endswith(".csv") else None,
            }for x in item["expected"]],
        }
    monkeypatch.setattr(m.v1,"_qualify_one",fake_qualify)
    result=m.run(P)
    assert result["status"]=="SOURCE_SCHEMA_QUALIFIED_BUT_MOVEMENT_VALIDATION_NOT_AUTHORIZED"
    assert result["origin_to_destination_inference_authorized"] is False
    assert result["full_three_axis_MRR_authorized"] is False
    assert all(row["publisher_sha256_all_files_independently_matched"]
               for row in result["source_results"])
    assert result["individual_records_exported"]==0
    assert result["new_eog_wf_endpoints"]==0


def test_sha_or_version_divergence_produces_explicit_source_stop(monkeypatch):
    def false_qualify(source,base):
        item=next(row for row in P["sources"] if row["id"]==source["id"])
        return {
            "source_id":source["id"],
            "status":"SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED",
            "publisher_version_id":item["version_id"],
            "publisher_publication_date":item["expected_date"],
            "file_checks":[{
                "name":x["name"],"sha256":"0"*64,"size_bytes":x["size"]
            }for x in item["expected"]],
        }
    monkeypatch.setattr(m.v1,"_qualify_one",false_qualify)
    z=m.run(P)
    assert z["status"]=="SOURCE_TRANSPORT_OR_SCHEMA_HAS_SCIENTIFIC_STOP"
    assert all(s["status"]=="STOP_PINNED_PUBLISHER_SHA256_OR_SIZE_MISMATCH"
               for s in z["source_results"])


def test_two_source_versions_and_filename_sha_roster_stay_frozen():
    assert len(P["sources"])==2
    assert [x["version_id"] for x in P["sources"]]==[148124,198534]
    assert P["ancestor_metadata_gate"]["original_reason"].startswith("STOP_UNEXPECTED")
    assert P["output"]["raw_individual_rows_exported"]==0
    assert P["output"]["ecological_models_fit"]==0
    assert P["output"]["new_eogwf_endpoints"]==0
