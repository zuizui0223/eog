"""Offline checks of original McKee 12h ZIP/DBF header metadata provenance.

No original source ZIP, animal ID, GPS coordinates or dense 2h data in CI.
The local producer is SHA-locked and only reads file/member headers.
"""
from __future__ import annotations

import json
from pathlib import Path
import runpy

import pytest


ROOT=Path(__file__).resolve().parents[1]/"validation/temporal_corridor_mckee2024"
PROTOCOL=ROOT/"post_stop_archived_zip_dbf_header_protocol_v1.json"
RECEIPT=ROOT/"post_stop_archive_header_receipt_v1.json"
SCRIPT=ROOT/"replay_post_stop_archive_headers.py"
ns=runpy.run_path(str(SCRIPT))


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_precedes_header_inspection_and_source_hash_is_exact():
    p=read(PROTOCOL)
    r=read(RECEIPT)
    assert p["schema"]=="eog.mckee2024.prepublication_original_archive_header_provenance.v1"
    assert p["status"]=="FROZEN_BEFORE_NEW_DBF_HEADER_AND_LOCAL_ZIP_METADATA_INSPECTION"
    assert r["protocol_committed_before_local_header_inspection"]=="52c99bea76d55cf308551cb46fcf96b7f886408a"
    assert p["source"]["sha256"]==r["source_sha256"]==ns["ZIP_SHA256"]
    assert p["source"]["size_bytes"]==r["source_size_bytes"]==ns["ZIP_SIZE"]==1539661
    assert sorted(p["source"]["members"])==sorted(ns["MEMBERS"])
    assert ns["_guard"]()["status"]==p["status"]
    assert r["source_sha256_verified"] is True


def test_four_member_zip_dates_and_independent_dbf_header_date_agree():
    r=read(RECEIPT)
    z=r["members"]
    assert sorted(z)==sorted(ns["MEMBERS"])
    assert r["identical_member_DOS_timestamps"] is True
    assert r["common_DOS_timestamp"]=="2024-06-28T13:23:08"
    assert all(x["DOS_time_local_no_timezone"]=="2024-06-28T13:23:08" for x in z.values())
    assert all(x["zip_compression_method"]==8 for x in z.values())
    assert all(x["zip_creator_system_code"]==0 for x in z.values())
    assert r["dbf_header"]["last_updated_YY_MM_DD_raw"]==[124,6,28]
    assert r["dbf_header"]["last_updated_parsed_date"]=="2024-06-28"
    assert r["DBF_update_date_matches_ZIP_member_date"] is True
    assert r["July_18_2024_Dryad_release_source"].startswith("https://datadryad.org/dataset/")


def test_dbf_time_field_width_not_19_char_or_10_char_truncation():
    r=read(RECEIPT)
    d=r["dbf_header"]
    assert d["version_hex"]=="0x03"
    assert d["record_count"]==28953
    assert d["header_length_bytes"]==385
    assert d["record_length_bytes"]==769
    assert d["language_driver_id_hex"]=="0x57"
    assert len(d["field_descriptors"])==11
    assert [a["name"] for a in d["field_descriptors"]]==[
        "State","Herd","SpcsCmm","SpcsScn","AID",
        "SeasnYr","Season","Year","Timstmp","UTM_E","UTM_N"
    ]
    assert all((a["type"],a["width"],a["decimal_places"])==("C",80,0)
               for a in d["field_descriptors"][:9])
    assert all((a["type"],a["width"],a["decimal_places"])==("N",24,15)
               for a in d["field_descriptors"][9:])
    assert d["Timstmp_field_can_fit_full_19_character_string"] is True
    assert 1+sum(a["width"] for a in d["field_descriptors"])==769


def test_point_shapefile_counts_match_original_header_sizes_and_prj_conflict():
    r=read(RECEIPT)
    s=r["shape_headers"]
    assert r["source_prj_projected_wkt_name"]=="NAD_1983_HARN_UTM_Zone_12N"
    for ext,size in (("shp",810784),("shx",231724)):
        head=s["GPS12hrs_Locs."+ext]
        assert head["file_code"]==9994
        assert head["version"]==1000
        assert head["shape_type"]==1
        assert head["file_length_bytes"]==size
        assert r["members"]["GPS12hrs_Locs."+ext]["uncompressed_bytes"]==size
    assert s["GPS12hrs_Locs.shp"]["file_length_bytes"]==100+28*28953
    assert s["GPS12hrs_Locs.shx"]["file_length_bytes"]==100+8*28953


def test_header_times_do_not_upgrade_to_historical_source_truth():
    r=read(RECEIPT)
    assert r["DOS_time_author_creation_proof"] is False
    assert r["DBF_last_update_author_or_original_R_version_proof"] is False
    assert r["date_only_is_exact_midnight_proven"] is False
    assert r["CRS_author_intent_proven"] is False
    assert r["original_source_time_and_CRS_STOP_preserved"] is True
    assert r["dense_2h_GPS_opened"] is False
    assert r["DBF_record_rows_or_SHP_geometry_read"] is False
    assert r["raw_animal_IDs_dates_or_coordinates_exported"] is False
    assert r["ecological_or_EOG_prediction_scored"] is False
    assert r["original_EOG_WF_scored_endpoints"]==3


def test_only_exact_sha_locked_source_file_can_be_inspected(tmp_path):
    wrong=tmp_path/"GPS12hrs_Locs.zip"
    wrong.write_bytes(b"wrong original source content")
    with pytest.raises(ValueError,match="Wrong source archive"):
        ns["read_headers"](wrong)
    missing=tmp_path/"GPS2hrs_Locs.zip"
    missing.write_bytes(b"wrong original source content")
    with pytest.raises(ValueError,match="Wrong source archive"):
        ns["read_headers"](missing)
    assert ns["_guard"]()["source"]["no_dense_2h_access"] is True
