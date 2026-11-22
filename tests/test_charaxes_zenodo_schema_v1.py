"""No Charaxes biological CSV rows may be parsed or written by schema preflight."""
import copy
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from benchmarks.run_charaxes_zenodo_schema_gate_v1 import (
    first_header, source_semantics, verified_payload, run_gate
)


def fixture(tmp_path):
    source=json.loads(Path("validation/charaxes_zenodo_schema_v1/protocol_v1.json").read_text())
    readme=b"column,definition\nHostCover,Host plant cover at multiple scales\n"
    response=(b"Year,TrapID,CharaxesCount,HostCover,ForestType,DistanceToHost\n"
              b"2023,SECRET_SITE_RESPONSE,SECRET_COUNT,SECRET_HOST,SECRET_FOREST,1000\n")
    data=[readme,response]
    for f,payload in zip(source["parent"]["files"],data):
        f["size"]=len(payload)
        f["md5"]=hashlib.md5(payload).hexdigest()
    p=tmp_path/"protocol.json"
    p.write_text(json.dumps(source))
    return p,data


def test_header_isolated_from_biological_rows():
    b=(b"Year,TrapID,CharaxesCount,HostCover,ForestType\n"
       b"SECRET_RESPONSE_MUST_NOT_BE_PARSED\n")
    assert first_header(b)==[
        "Year","TrapID","CharaxesCount","HostCover","ForestType"
    ]


def test_md5_mismatch_is_hard_stop():
    with pytest.raises(ValueError,match="MD5"):
        verified_payload(b"hello",{"size":5,"md5":"0"*32})


def test_mock_full_file_transfer_but_zero_row_parse(tmp_path):
    p,data=fixture(tmp_path)
    calls=[]
    def fetch(entry):
        calls.append(entry["name"])
        return data[len(calls)-1]
    r=run_gate(protocol_path=p,fetch=fetch)
    assert r["status"]=="FILES_MD5_VERIFIED_HEADERS_ONLY__ECOLOGICAL_AXES_UNQUALIFIED"
    assert len(calls)==2
    assert r["raw_bytes_transferred"]==sum(map(len,data))
    assert r["biological_data_bytes_transferred"]==len(data[1])
    assert r["biological_data_rows_parsed"]==0
    assert r["ecological_scores"]==0
    assert r["source_semantics"]["B_host_plant_proxy_qualified"] is False
    assert r["source_semantics"]["M_movement_only_proxy_qualified"] is False
    assert "SECRET_SITE_RESPONSE" not in json.dumps(r)
    assert r["source_semantics"]["column_token_flags"]["possible_host_cover"]


def test_single_source_failure_stops_and_does_not_fetch_other_file(tmp_path):
    p,data=fixture(tmp_path)
    calls=[]
    def fetch(entry):
        calls.append(entry["name"])
        raise HTTPError(entry["url"],429,"limit",{},None)
    r=run_gate(protocol_path=p,fetch=fetch)
    assert r["status"]=="SOURCE_STOP_HTTP_429"
    assert calls==["C_jasius_readme.csv"]
    assert r["raw_bytes_transferred"]==0
    assert r["biological_data_rows_parsed"]==0


def test_bad_csv_header_not_repaired_with_data_rows():
    with pytest.raises(ValueError,match="HEADER_PARSE"):
        first_header(b"OnlyOneColumn\n2018,SECRET\n")
