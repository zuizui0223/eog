"""Physical-header gate has no biological response parser or scored outcomes."""
from pathlib import Path
import json

import pytest

from benchmarks.run_pyrgus_bam_header_gate_v1 import (
    parse_first_header, classify_headers, run_gate,
)
from eog.v2.http_range_transport import HttpRangeTransportError


def test_first_header_ignores_all_following_bytes():
    prefix=(b"\xef\xbb\xbfSite,Host_density,solar_irradiance,Longitude,Latitude\n"
            b"PRIVATE_RESPONSE_DO_NOT_INTERPRET\n")
    assert parse_first_header(prefix)==[
        "Site","Host_density","solar_irradiance","Longitude","Latitude"
    ]


def test_invalid_header_fails_closed():
    with pytest.raises(ValueError,match="NOT_COMPLETE"):
        parse_first_header(b"Site,Host_density")
    with pytest.raises(ValueError,match="DUPLICATE"):
        parse_first_header(b"Site,site\nPRIVATE\n")


def _factory(source_headers, *, fail=None):
    class FakeTransport:
        def __init__(self,url,*,allowed_hosts,maximum_archive_size):
            self.url=url
            assert "datadryad.org" in allowed_hosts
        def bind_frozen_size(self,n):
            assert n in (8380,2763)
        def read_range(self,start,end,role):
            assert (start,end,role)==(0,511,"frozen_csv_header")
            if fail and "59822" in self.url:
                raise HttpRangeTransportError(fail)
            line=source_headers[0 if "59822" in self.url else 1]
            return line+b"\n"+b"R"*(511-len(line))
    return FakeTransport


def test_fixed_two_headers_and_no_patch_join_promotion():
    source=(
        b"Site,Year,Abundance",
        b"Site,Host_density,Solar_irradiance,Longitude,Latitude",
    )
    r=run_gate(transport_factory=_factory(source))
    assert r["status"]=="HEADERS_PARSED_NO_BIOLOGY__PATCH_JOIN_NOT_VERIFIED"
    assert r["biological_data_rows_parsed"]==0
    assert r["biology_models_fitted"]==0
    assert r["header_only_bytes_transferred"]==1024
    assert r["column_join_verified"] is False
    assert r["header_assessment"]["candidate_join_header_names"]==["site"]
    assert r["header_assessment"]["site_host_header_candidates"]==["hostdensity"]
    assert r["header_assessment"]["site_abiotic_header_candidates"]==["solarirradiance"]
    assert "longitude" in r["header_assessment"]["site_location_header_candidates"]


def test_transport_failure_never_attempts_second_source():
    requested=[]
    fake=_factory((b"Site,Year",b"Site,Host_density"),
                  fail="bounded Range returned HTTP 403; body was not opened")
    def factory(*args,**kwargs):
        requested.append(args[0])
        return fake(*args,**kwargs)
    r=run_gate(transport_factory=factory)
    assert r["status"]=="SOURCE_STOP_HTTP_403"
    assert requested==[
        "https://datadryad.org/stash/downloads/file_stream/59822"
    ]
    assert r["biological_data_rows_parsed"]==0
    assert r["header_assessment"] is None
