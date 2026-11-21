"""Source-only GBIF/DOF breeding-field + coordinate uncertainty tests.

All external record values are synthetic fixtures. No actual breeding site-year
or marked Arctic tern movement is opened, reconstructed, or scored.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import urllib.parse

from scripts import eog_tern_independent_dofbasen_breeding_field_gate_v2 as gate

P=json.loads(Path(
 "validation/tern_independent_dofbasen_breeding_field_gate_v2/protocol_v2.json"
).read_text(encoding="utf-8"))
PREVIOUS=json.loads(Path(
 "validation/tern_independent_dofbasen_breeding_gate_v1/frozen_count_receipt_v1.json"
).read_text(encoding="utf-8"))


def fake_fetch(*,breeding_fields=True,wrong_count=False,wrong_taxon=False):
    calls=[]
    byyears={f'{w["from"]},{w["to"]}':w for w in P["source_sample_design"]["windows"]}
    def fetch(url,byte_cap,timeout):
        parsed=urllib.parse.urlsplit(url)
        assert parsed.scheme=="https" and parsed.hostname=="api.gbif.org"
        q=urllib.parse.parse_qs(parsed.query)
        assert q["datasetKey"]==["95db4db8-f762-11e1-a439-00145eb45e9a"]
        assert q["taxonKey"]==["5229230"]
        assert q["country"]==["DK"] and q["hasCoordinate"]==["true"]
        assert q["limit"]==["100"]
        window=byyears[q["year"][0]]
        assert int(q["offset"][0]) in window["offsets"]
        offset=int(q["offset"][0])
        entries=[]
        for i in range(100):
            row={
                "gbifID":f"SAFE_SYNTHETIC_{q['year'][0]}_{offset}_{i}",
                "datasetKey":"95db4db8-f762-11e1-a439-00145eb45e9a",
                "speciesKey":5229230 if not wrong_taxon else 2480000,
                "taxonKey":5229230,
                "scientificName":"Sterna paradisaea",
                "countryCode":"DK",
                "year":window["from"],"eventDate":f'{window["from"]}-07-01',
                "decimalLatitude":55.12813,"decimalLongitude":11.93725,
                "coordinateUncertaintyInMeters":(
                    25000 if i%3==0 else (1000 if i%3==1 else None)
                ),
                "hasGeospatialIssues":False,
                "behavior":"Ynglepar" if breeding_fields and i%5==0 else None,
                "reproductiveCondition":"Breeding" if breeding_fields and i%10==0 else None,
                "occurrenceRemarks":"private_observer_string_must_not_escape" if breeding_fields and i%7==0 else None,
                "basisOfRecord":"HUMAN_OBSERVATION",
                "occurrenceStatus":"PRESENT"
            }
            entries.append(row)
        calls.append(url)
        return {
            "count":window["count"]+(1 if wrong_count else 0),
            "results":entries,
        },"sha_synthetic_page"
    return fetch,calls


def test_stage1_pre_sample_freeze_and_no_matched_colonies():
    assert P["status"]=="FROZEN_BEFORE_ANY_GBIF_OCCURRENCE_RECORD_READ"
    assert P["parent_source_gate"]["species_key"]==5229230
    assert P["source_sample_design"]["expected_sample_records"]==1500
    assert P["source_sample_design"]["expected_requests"]==15
    assert all(x["limit"]==100 and len(x["offsets"])==3 for x in P["source_sample_design"]["windows"])
    assert P["frozen_baseline_results_unmodified"]=={
        "tern_known_20km_false_assurance":198,
        "tern_no_exact_candidate_20km_false_assurance":171
    }
    gate._validate_protocol(P,PREVIOUS)


def test_all_fifteen_pages_expose_only_schema_presence_and_uncertainty_counts():
    fetch,calls=fake_fetch()
    out=gate.inspect_frozen_record_pages(P,PREVIOUS,fetch=fetch)
    assert out["status"]=="GBIF_DOF_BREEDING_FIELD_SCHEMA_INSPECTED_NOT_SITE_YEAR_VALIDATED"
    assert len(calls)==15
    assert out["page_count"]==15
    assert out["actual_observed_records_read_ephemerally"]==1500
    assert len(out["window_field_summaries"])==5
    assert out["total_nonempty_field_counts"]["behavior"]==300
    assert out["total_nonempty_field_counts"]["reproductiveCondition"]==150
    assert out["total_nonempty_field_counts"]["occurrenceRemarks"]==225
    assert out["total_uncertainty_bins"]["GT_20000"]==510
    assert out["total_uncertainty_bins"]["MISSING"]==495
    assert out["total_uncertainty_bins"]["LE_1000"]==495
    assert out["sample_is_representative"] is False
    assert out["can_prove_source_colony_breeding_in_original_year"] is False
    assert out["historical_asof_source_data_verified"] is False
    assert out["independent_breeding_colonies_matched_to_original_tern"]==0
    assert out["original_tern_dispersal_event_rows_reopened"]==0
    assert out["new_EOG_WF_scored_endpoints"]==0
    raw=json.dumps(out)
    assert "SAFE_SYNTHETIC_" not in raw
    assert "private_observer_string_must_not_escape" not in raw
    assert "55.12813" not in raw
    assert "11.93725" not in raw


def test_empty_breeding_fields_are_a_scientific_source_stop():
    fetch,calls=fake_fetch(breeding_fields=False)
    out=gate.inspect_frozen_record_pages(P,PREVIOUS,fetch=fetch)
    assert out["status"]=="STOP_GBIF_SAMPLED_BREEDING_FIELDS_NOT_PRESENT"
    assert len(calls)==15
    assert out["source_site_years_verified"]==0


def test_source_counts_changed_since_stage0_cannot_be_slid_silently():
    fetch,calls=fake_fetch(wrong_count=True)
    out=gate.inspect_frozen_record_pages(P,PREVIOUS,fetch=fetch)
    assert out["status"]=="STOP_GBIF_DATASET_UPDATED_SINCE_COUNT_FREEZE"
    assert len(calls)==1
    assert out["individual_occurrence_records_exported"]==0


def test_taxon_mismatch_is_not_a_proven_colony_even_with_breeding_field():
    fetch,calls=fake_fetch(wrong_taxon=True)
    out=gate.inspect_frozen_record_pages(P,PREVIOUS,fetch=fetch)
    assert out["status"]=="STOP_GBIF_ORIGINAL_DATASET_OR_TAXON_CROSS_CONTAMINATION"
    assert out["speciesKey_mismatches_in_sample"]==1500
    assert out["independent_breeding_colonies_matched_to_original_tern"]==0


def test_publisher_protocol_drift_blocks_network():
    for edit in (
        lambda x:x.update(status="POSTHOC_SAMPLE"),
        lambda x:x["parent_source_gate"].update(species_key=1),
        lambda x:x["parent_source_gate"].update(source_receipt_sha256="0"*64),
        lambda x:x["source_sample_design"]["windows"][0].update(offsets=[0,1,2]),
        lambda x:x["source_sample_design"].update(expected_sample_records=5000),
        lambda x:x["field_quality_bins"].update(coordinate_uncertainty_meters=["UNKNOWN"]),
    ):
        faulty=deepcopy(P)
        edit(faulty)
        fetch,calls=fake_fetch()
        result=gate.inspect_frozen_record_pages(faulty,PREVIOUS,fetch=fetch)
        assert result["status"].startswith("STOP_")
        assert calls==[]


def test_coordinate_uncertainty_buckets_strictly_not_precise_if_missing():
    assert gate._uncertainty_bin(None)=="MISSING"
    assert gate._uncertainty_bin("")=="MISSING"
    assert gate._uncertainty_bin("nan")=="NONFINITE_OR_INVALID"
    assert gate._uncertainty_bin("-1")=="NONFINITE_OR_INVALID"
    assert gate._uncertainty_bin("1000")=="LE_1000"
    assert gate._uncertainty_bin("1500")=="GT_1000_LE_2000"
    assert gate._uncertainty_bin("25000")=="GT_20000"
