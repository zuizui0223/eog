"""Source-locked Arctic tern banding event geography: offline synthetic controls only.

No real movement files accessed in regression tests; the one source archive
is read exactly once in dedicated CI after a protocol-first SHA freeze.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import zipfile

import pytest

from benchmarks import tern_known_origin_geographic_minrelax_v1 as m

PROTO=json.loads(Path("validation/tern_known_origin_geographic_minrelax_v1/protocol_v1.json").read_text(encoding="utf-8"))


def _synthetic_rows():
    R=PROTO["frozen_estimands"]["earth_radius_km"]
    def event(uid,year,depart,arrive):
        return {
            "UID":uid,"year":year,"origin":depart,"arrival":arrive,
            "publisher_distance_km":m._greatcircle_km(depart,arrive,R),
        }
    return {
        "breeding_adult":[
            event("adult_train",1970,(55.0,10.0),(55.0,10.2)),
            event("adult_test",1976,(55.0,12.0),(55.0,10.0)),
        ],
        "natal_chick":[
            event("natal_train1",1970,(55.0,9.0),(55.0,10.0)),
            event("natal_train2",1971,(55.0,9.1),(55.0,9.2)),
            event("natal_train3",1972,(55.0,11.0),(55.0,11.2)),
            event("natal_test",1977,(55.0,12.0),(55.0,10.0)),
        ],
    }


def _test_protocol():
    p=deepcopy(PROTO)
    p["source_frozen"]["expected_csvs"][0]["rows"]=2
    p["source_frozen"]["expected_csvs"][1]["rows"]=4
    p["no_leakage_and_QA"]["min_retrospective_reference_source_sites"]=1
    p["no_leakage_and_QA"]["min_holdout_events_per_group"]=1
    return p


def test_original_source_sha_metadata_locked_before_real_events():
    assert PROTO["status"]=="FROZEN_PRE_RAW_EVENT_OPEN_AFTER_PUBLISHER_SHA_MANIFEST"
    assert PROTO["source_frozen"]["published_version_id"]==466530
    assert [x["rows"] for x in PROTO["source_frozen"]["expected_csvs"]]==[200,890]
    assert PROTO["frozen_estimands"]["prespecified_thresholds_km"]==[5,20,50,100]
    assert PROTO["frozen_estimands"]["primary_threshold_km"]==20
    assert PROTO["source_inference"]["time_information_boundary"].startswith("The historical year")
    assert PROTO["claim_boundary"]["no_eog_wf_new_endpoint"]==0


def test_correct_haversine_source_and_endpoint_units():
    R=PROTO["frozen_estimands"]["earth_radius_km"]
    assert m._greatcircle_km((55.0,10.0),(55.0,10.0),R)==0.0
    assert 63.0 < m._greatcircle_km((55.0,10.0),(55.0,11.0),R) < 65.0
    assert 110 < m._greatcircle_km((55.0,10.0),(56.0,10.0),R) < 112


def test_same_colony_event_index_and_real_source_unavailable_overestimation():
    result=m.analyze_events(_synthetic_rows(),_test_protocol())
    assert result["status"]=="EXTERNAL_POST_PUBLICATION_SOURCE_GEOGRAPHY_DESCRIPTIVE_ONLY"
    assert result["retrospectively_indexed_distinct_earlier_departure_locations"]==4
    assert result["published_distance_match_within_2km_rows"]==6
    assert result["publisher_distance_total_rows"]==6
    assert result["outcomes"]["breeding_adult"]["event_rows"]==1
    assert result["outcomes"]["natal_chick"]["event_rows"]==1
    assert result["outcomes"]["breeding_adult"]["source_optimism_gap_gt_2km_events"]==1
    adult_r20=next(x for x in result["outcomes"]["breeding_adult"]["radii"] if x["radius_km"]==20)
    assert adult_r20["actual_marked_source_feasible"]==0
    assert adult_r20["some_retrospective_source_feasible"]==1
    assert adult_r20["source_agnostic_false_assurance_events"]==1
    assert adult_r20["conservative_rounding_margin_false_assurance_events"]==1
    assert result["new_EOG_WF_endpoints"]==0
    assert "adult_test" not in json.dumps(result)
    assert "natal_test" not in json.dumps(result)


def test_future_recorded_origins_are_not_added_to_historic_catalogue():
    data=_synthetic_rows()
    first=m.analyze_events(data,_test_protocol())
    data["breeding_adult"][1]["origin"]=(55.0,9.5)
    data["breeding_adult"][1]["publisher_distance_km"]=m._greatcircle_km(
        data["breeding_adult"][1]["origin"],
        data["breeding_adult"][1]["arrival"],
        PROTO["frozen_estimands"]["earth_radius_km"])
    next_result=m.analyze_events(data,_test_protocol())
    assert first["retrospectively_indexed_distinct_earlier_departure_locations"]==4
    assert next_result["retrospectively_indexed_distinct_earlier_departure_locations"]==4


def test_original_archive_sha_of_all_five_members_not_only_selected_CSVs():
    p=deepcopy(PROTO)
    contents={}
    for i,row in enumerate(p["source_frozen"]["exact_files"]):
        data=f"public file {i}: purely synthetic, not a real bird event".encode()
        contents[row["name"]]=data
        row["size_bytes"]=len(data)
        row["sha256"]=sha256(data).hexdigest()
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name,data in contents.items():
            z.writestr(f"public/{name}",data)
    archive=out.getvalue()
    selected=m._read_source_zip(archive,p)
    assert set(selected)=={"Ad_DaD.csv","U_DaD.csv"}
    assert selected["U_DaD.csv"]==contents["U_DaD.csv"]
    p["source_frozen"]["exact_files"][-1]["sha256"]="0"*64
    with pytest.raises(m.ScientificStop,match="STOP_PUBLISHER_SHA256_OR_BYTE_IDENTITY"):
        m._read_source_zip(archive,p)


def test_event_csv_header_and_year_frozen():
    base="UID,depart_lat,depart_lon,arrive_lat,arrive_lon,year,distance_km,direction_deg\n"
    row="1,55.00,10.00,55.00,11.00,1970,63.78,90\n"
    expected={"rows":1,"expected_year_min":1946,"expected_year_max":2005}
    rows=m._parse_event_table((base+row).encode(),expected)
    assert len(rows)==1
    assert rows[0]["origin"]==(55.0,10.0)
    with pytest.raises(m.ScientificStop,match="STOP_COORDINATE_PRECISION"):
        m._parse_event_table((base+row.replace("55.00,10.00","55.001,10.00")).encode(),expected)
    with pytest.raises(m.ScientificStop,match="STOP_EVENT_YEAR"):
        m._parse_event_table((base+row.replace(",1970,",",2021,")).encode(),expected)
    with pytest.raises(m.ScientificStop,match="STOP_PUBLISHER_EVENT_COUNT"):
        m._parse_event_table((base+row).encode(),{"rows":2,"expected_year_min":1946,"expected_year_max":2005})
    with pytest.raises(m.ScientificStop,match="STOP_PUBLISHER_EVENT_HEADER"):
        m._parse_event_table(("A,depart_lat,depart_lon\n"+row).encode(),expected)


def test_published_distance_disagreement_blocks_field_scoring():
    data=_synthetic_rows()
    data["breeding_adult"][1]["publisher_distance_km"]=0.0
    data["natal_chick"][3]["publisher_distance_km"]=0.0
    with pytest.raises(m.ScientificStop,match="STOP_PUBLISHED_DISTANCE_GEO_CONCORDANCE"):
        m.analyze_events(data,_test_protocol())


def test_outcome_holds_event_level_not_independent_individual_inference():
    z=m.analyze_events(_synthetic_rows(),_test_protocol())
    assert z["individual_ring_ids_present"] is False
    assert z["prior_year_catalogue_is_verified_available_at_time"] is False
    assert z["is_asof_prospective"] is False
    assert z["environment_or_barrier_MRR_evaluated"] is False
    assert z["event_records_exported"]==0
    assert z["new_EOG_WF_endpoints"]==0
