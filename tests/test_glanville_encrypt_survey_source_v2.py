import json
import runpy
import hashlib
import pytest


def _m():
    return runpy.run_path("scripts/glanville_encrypt_survey_source_v2.py")


def _p():
    return json.load(open("validation/glanville_genetic_host_world_v2/protocol_v2.json"))


def test_original_archive_and_new_key_frozen():
    p=_p();x=_m()["map_protocol"](p)
    assert p["source_identifiers"]["uploaded_original_DiLeo2022_CSV_SHA256"]=="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
    assert x["prior_source_repository"]["archive_sha256"]=="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"
    assert x["status"]=="frozen_after_user_file_inspection_before_crosswalk"
    assert x["max_public_years"]==[2007,2008,2009,2010,2011,2012]
    assert "PRIVATE KEY" not in json.dumps(p)
    assert hashlib.sha256(x["ephemeral_encryption_public_key_pem"].encode()).hexdigest()==x["public_key_sha256"]


def test_mismatched_source_or_year_is_an_immediate_stop():
    m=_m();p=_p()
    p["source_provider_contract"]["max_public_years"]=[2007]
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_IDENTITY"):
        m["map_protocol"](p)
    p=_p();p["source_identifiers"]["publisher_zip_Schulz2019_Zenodo_4987060_SHA256"]="0"*64
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_IDENTITY"):
        m["map_protocol"](p)


def test_no_key_substitution_or_wrong_protocol():
    m=_m();p=_p()
    p["encrypted_bridge"]["public_key_sha256"]="0"*64
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_IDENTITY"):
        m["map_protocol"](p)
    p=_p();p["status"]="post_result"
    with pytest.raises(ValueError,match="STOP_V2_PROTOCOL_STATUS"):
        m["map_protocol"](p)
