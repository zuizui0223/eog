"""Do not follow redirects or fetch a single biological payload byte."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from scripts import eog_independent_movement_redirect_host_v1 as m

P = json.loads(Path("validation/independent_movement_redirect_host_v1/protocol_v1.json").read_text(encoding="utf-8"))


def test_external_cdn_host_never_followed(monkeypatch):
    urls=[]
    def fake(url,method,timeout):
        urls.append((url,method))
        assert method=="HEAD"
        return 302,"https://storage.googleapis.com/dryad-signed-download?sig=SUPER_SECRET"
    monkeypatch.setattr(m,"_one_nofollow_request",fake)
    r=m.run(P)
    assert r["status"]=="HOST_DIAGNOSTIC_COMPLETED__SOURCE_SCHEMA_STILL_STOP"
    assert r["source_qualified"] is False
    assert len(urls)==2
    assert all(x[1]=="HEAD" for x in urls)
    for result in r["source_results"]:
        assert result["status"]=="STOP_UNVERIFIED_REDIRECT_HOST"
        assert result["last_redirect_hostname"]=="storage.googleapis.com"
        assert result["body_bytes_read"]==0
        assert "SUPER_SECRET" not in json.dumps(result)


def test_same_host_hop_chain_limited_and_external_not_followed(monkeypatch):
    calls=[]
    def fake(url,method,timeout):
        calls.append(url)
        if url.endswith("/download"):
            return 301,"https://datadryad.org/downloads/next"
        return 302,"https://cdn.other-provider.example/download?q=sensitive"
    monkeypatch.setattr(m,"_one_nofollow_request",fake)
    result=m.probe_one(P["frozen_endpoint_roster"][0],P)
    assert result["hop_status_codes"]==[301,302]
    assert result["last_redirect_hostname"]=="cdn.other-provider.example"
    assert len(calls)==2
    assert "sensitive" not in json.dumps(result)


def test_same_host_hop_limit_prevents_unbounded_network(monkeypatch):
    calls=[]
    def fake(url,method,timeout):
        calls.append(url)
        return 302,"https://datadryad.org/next"+str(len(calls))
    monkeypatch.setattr(m,"_one_nofollow_request",fake)
    r=m.probe_one(P["frozen_endpoint_roster"][0],P)
    assert len(calls)==3
    assert r["status"]=="STOP_SAME_HOST_HOP_BUDGET"


def test_head_not_allowed_falls_back_once_but_no_body_reads(monkeypatch):
    methods=[]
    def fake(url,method,timeout):
        methods.append(method)
        if method=="HEAD":return 405,None
        return 302,"https://s3.us-west-2.amazonaws.com/bucket?secret=hush"
    monkeypatch.setattr(m,"_one_nofollow_request",fake)
    r=m.probe_one(P["frozen_endpoint_roster"][0],P)
    assert methods==["HEAD","GET"]
    assert r["status"]=="STOP_UNVERIFIED_REDIRECT_HOST"
    assert r["last_redirect_hostname"]=="s3.us-west-2.amazonaws.com"
    assert r["used_body_unread_get_fallback"]
    assert "hush" not in json.dumps(r)


def test_direct_content_200_is_not_read_or_scored(monkeypatch):
    monkeypatch.setattr(m,"_one_nofollow_request",lambda url,method,timeout:(200,None))
    r=m.probe_one(P["frozen_endpoint_roster"][0],P)
    assert r["status"]=="STOP_DIRECT_ZIP_RESPONSE_200_UNREAD"
    assert r["bytes_from_file_body_read"]==0


def test_scheme_and_user_credentials_are_rejected():
    assert m._safe_host("https://s3.amazonaws.com/bucket?q=secret")=="s3.amazonaws.com"
    assert m._safe_host("http://s3.amazonaws.com/foo") is None
    assert m._safe_host("https://username:password@datadryad.org/d") is None
    assert m._safe_host("javascript:alert(1)") is None


def test_invalid_initial_endpoint_cannot_be_probed(monkeypatch):
    one=deepcopy(P["frozen_endpoint_roster"][0])
    one["official_zip_endpoint"]="https://example.com/source"
    monkeypatch.setattr(m,"_one_nofollow_request",lambda *args:(_ for _ in ()).throw(AssertionError("SHOULD NOT CALL")))
    with pytest.raises(ValueError,match="STOP_START_HOST_NOT_FROZEN"):
        m.probe_one(one,P)


def test_source_status_hard_gate_and_no_wf_endpoint():
    assert P["frozen_endpoint_roster"][0]["version_id"]==148124
    assert P["frozen_endpoint_roster"][1]["version_id"]==198534
    assert P["methods"]["max_same_host_head_hops"]==3
    assert P["output"]["biological_rows_read"]==0
    assert P["output"]["new_eogwf_endpoints"]==0
