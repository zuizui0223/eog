import hashlib
import json
import runpy
import pytest


def _m():
    return runpy.run_path("scripts/glanville_conditional_pairing_ciphertext_v3.py")


def _p():
    return json.load(open("validation/glanville_conditional_pairing_null_v3/protocol_v3.json"))


def test_frozen_sha_and_public_only_ephemeral_key():
    p=_p()
    v=_m()["translate"](p)
    assert v["prior_source_repository"]["archive_sha256"]=="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"
    assert v["max_public_years"]==[2007,2008,2009,2010,2011,2012]
    assert hashlib.sha256(v["ephemeral_encryption_public_key_pem"].encode()).hexdigest()==v["public_key_sha256"]
    assert "PRIVATE KEY" not in json.dumps(p)
    assert p["predeclared_primary_conditional_recombination_null"]["monte_carlo_replicates"]==1999
    assert p["predeclared_primary_conditional_recombination_null"]["seed"]==20261120


def test_fail_closed_on_modified_source_or_new_key():
    m=_m();p=_p()
    p["source_transport"]["new_local_ephemeral_rsa_public_key_sha256"]="0"*64
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_SIGNATURE"):
        m["translate"](p)
    p=_p();p["sources"]["survey"]["sha256"]="0"*64
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_SIGNATURE"):
        m["translate"](p)


def test_regional_source_and_period_cannot_be_extended():
    m=_m();p=_p()
    p["status"]="post-outcome"
    with pytest.raises(ValueError,match="STOP_FROZEN_SOURCE_CONTRACT"):
        m["translate"](p)
    p=_p();p["source_transport"]["single_download_no_retry"]=False
    with pytest.raises(ValueError,match="STOP_SOURCE_REACQUISITION_SIGNATURE"):
        m["translate"](p)
