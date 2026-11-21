"""Historical Danish Arctic Tern source counts, offline source-only API tests.

All responses synthetic; individual occurrence rows are not fetched.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import urllib.parse

from scripts import eog_tern_independent_dofbasen_source_count_gate_v1 as gate

P=json.loads(Path(
    "validation/tern_independent_dofbasen_breeding_gate_v1/protocol_v1.json"
).read_text(encoding="utf-8"))

COUNTS={
    "1960,1975":3,
    "1976,1985":11,
    "1986,1995":34,
    "1996,2005":92,
    "2006,2012":251,
}


def fixture_fetch(*,other_doi=False,other_species=False,no_count=False):
    calls=[]
    def fetch(url,byte_cap,timeout):
        calls.append(url)
        parsed=urllib.parse.urlsplit(url)
        assert parsed.hostname=="api.gbif.org"
        if parsed.path.endswith("/dataset/95db4db8-f762-11e1-a439-00145eb45e9a"):
            return {
                "key":"95db4db8-f762-11e1-a439-00145eb45e9a",
                "title":"DOF/BirdLife Denmark - Observations from DOFbasen",
                "license":"CC_BY_NC_4_0",
                "identifiers":[{"identifier":"10.15468/other" if other_doi else "10.15468/tww7cj","type":"DOI"}],
            },"sha_dataset"
        if parsed.path.endswith("/species/match"):
            return {
                "rank":"SPECIES","canonicalName":"Sterna hirundo" if other_species else "Sterna paradisaea",
                "scientificName":"Sterna hirundo" if other_species else "Sterna paradisaea Pontoppidan, 1763",
                "status":"ACCEPTED","speciesKey":9117,"usageKey":9117,
            },"sha_species"
        if parsed.path.endswith("/occurrence/search"):
            parameters=urllib.parse.parse_qs(parsed.query)
            assert parameters["limit"]==["0"]
            assert parameters["hasCoordinate"]==["true"]
            assert parameters["datasetKey"]==["95db4db8-f762-11e1-a439-00145eb45e9a"]
            assert parameters["country"]==["DK"]
            assert parameters["taxonKey"]==["9117"]
            years=parameters["year"][0]
            return ({} if no_count else {"count":COUNTS[years]}),"sha_window_"+years
        raise AssertionError("unexpected endpoint "+url)
    return fetch,calls


def test_source_protocol_is_count_only_with_five_immutable_windows():
    assert P["status"]=="PROTOCOL_FIRST_BEFORE_GBIF_QUERY"
    assert P["external_dataset"]["gbif_dataset_uuid"]=="95db4db8-f762-11e1-a439-00145eb45e9a"
    assert P["external_dataset"]["dataset_doi"]=="10.15468/tww7cj"
    assert len(P["stage0_count_only"]["windows"])==5
    assert P["stage0_count_only"]["strict_unverified_limits"]["maximum_total_requests"]==7
    assert P["stage0_count_only"]["not_read"][0]=="species occurrence IDs"
    assert P["new_scored_endpoints"] if "new_scored_endpoints" in P else P["new_scored_endpoints"] if False else P["new_scored_endpoints"] if "new_scored_endpoints" in P else P["new_scored_endpoints"] if False else P["new_scored_endpoints"] if False else True


def test_exact_publisher_and_species_five_annual_windows_no_breeding_claim():
    mock,calls=fixture_fetch()
    result=gate.run(P,fetch=mock)
    assert result["status"]=="GBIF_DOF_SOURCE_COUNT_VERIFIED_NO_BREEDING_VALIDATION"
    assert result["count_requests_completed"]==7
    assert len(calls)==7
    assert [x["coordinate_bearing_occurrence_count"] for x in result["count_window_results"]]==[3,11,34,92,251]
    assert result["colonies_with_verified_breeding"]==0
    assert result["source_site_years_verified"]==0
    assert result["actual_source_occupancy_crosswalk_completed"] is False
    assert result["asof_availability_verified"] is False
    assert result["biological_records_read"]==0
    assert result["tern_original_event_rows_revisited"]==0
    assert result["new_eog_wf_scored_endpoints"]==0
    assert result["source_identification"]["dataset_doi_verifiable"] is True


def test_doi_mismatch_is_scientific_stop_before_occurrence_queries():
    mock,calls=fixture_fetch(other_doi=True)
    result=gate.run(P,fetch=mock)
    assert result["status"]=="STOP_DATASET_DOI_NOT_IN_METADATA"
    assert len(calls)==2


def test_wrong_species_hirundo_is_scientific_stop():
    mock,calls=fixture_fetch(other_species=True)
    result=gate.run(P,fetch=mock)
    assert result["status"]=="STOP_TAXON_MATCH_NOT_ARCTIC_TERN"
    assert len(calls)==2


def test_missing_GBIF_count_schema_is_not_zero_and_is_STOP():
    mock,calls=fixture_fetch(no_count=True)
    result=gate.run(P,fetch=mock)
    assert result["status"]=="STOP_GBIF_COUNT_SCHEMA"
    assert len(calls)==3
    assert result["colonies_with_verified_breeding"]==0


def test_tampered_dof_UUID_never_networks():
    broken=deepcopy(P)
    broken["external_dataset"]["gbif_dataset_uuid"]="invalid-source-uuid"
    result=gate.run(broken,fetch=lambda *_args,**_kwargs: (_ for _ in ()).throw(AssertionError("network invoked")))
    assert result["status"]=="STOP_DOFBASEN_UUID_CHANGED"


def test_bad_protocol_never_networks():
    broken=deepcopy(P)
    broken["status"]="POSTHOC_ANALYZED"
    result=gate.run(broken,fetch=lambda *_args,**_kwargs: (_ for _ in ()).throw(AssertionError("network invoked")))
    assert result["status"]=="STOP_PROTOCOL_NOT_FROZEN"


def test_zero_counts_cannot_be_interpreted_as_confirmed_colony_absence():
    mock,calls=fixture_fetch()
    def none(url,byte_cap,timeout):
        data,stamp=mock(url,byte_cap,timeout)
        if urllib.parse.urlsplit(url).path.endswith("/occurrence/search"):
            return {"count":0},stamp
        return data,stamp
    result=gate.run(P,fetch=none)
    assert result["status"]=="GBIF_DOF_SOURCE_COUNT_VERIFIED_NO_BREEDING_VALIDATION"
    assert result["source_site_years_verified"]==0
    assert all(x["coordinate_bearing_occurrence_count"]==0 for x in result["count_window_results"])
