"""Zenodo metadata-only source gate: no biological file access."""
import json
from pathlib import Path
from urllib.error import HTTPError

from benchmarks.run_charaxes_zenodo_metadata_gate_v1 import evaluate, parse_metadata

P=json.loads(Path("validation/charaxes_zenodo_metadata_v1/protocol_v1.json").read_text())


def fixture():
    return {
        "id":20525795,"doi":"10.5281/zenodo.20525795",
        "metadata":{"publication_date":"2026-06-03"},
        "files":{"entries":{
            "C_jasius_readme.csv":{
                "key":"C_jasius_readme.csv","size":1150,
                "checksum":"md5:296db7fac71b138ec6d84f99391388e0",
                "links":{"content":"https://zenodo.org/api/records/20525795/files/C_jasius_readme.csv/content"}
            },
            "C_jasius_reduced_dataset.csv":{
                "key":"C_jasius_reduced_dataset.csv","size":152900,
                "checksum":"md5:6f9f638a1c6966f567c4b7b783a5a47d",
                "links":{"content":"https://zenodo.org/api/records/20525795/files/C_jasius_reduced_dataset.csv/content"}
            }
        }}
    }


def test_exact_two_file_roster_validates_no_rows():
    requests=[]
    def fetch(url):
        requests.append(url)
        return fixture()
    x=evaluate(P,fetch)
    assert x["status"]=="SOURCE_METADATA_QUALIFIED_NO_RESPONSE_ROWS"
    assert requests==["https://zenodo.org/api/records/20525795"]
    assert x["file_metadata"]["file_count"]==2
    assert x["biological_response_rows_opened"]==0
    assert x["data_files_opened"]==0
    assert x["ecological_scores"]==0


def test_checksum_mismatch_fails_closed():
    f=fixture()
    f["files"]["entries"]["C_jasius_reduced_dataset.csv"]["checksum"]="md5:"+"0"*32
    r=evaluate(P,lambda url:f)
    assert r["status"]=="SOURCE_STOP_CHECKSUM_MISMATCH"
    assert r["file_metadata"] is None


def test_extra_file_fails_closed():
    f=fixture()
    f["files"]["entries"]["other.csv"]={"key":"other.csv","size":120,"checksum":"md5:"+"a"*32}
    r=evaluate(P,lambda url:f)
    assert r["status"]=="SOURCE_STOP_UNEXPECTED_FILE_ROSTER"


def test_wrong_record_id_fails_closed():
    f=fixture()
    f["id"]=20525796
    r=evaluate(P,lambda url:f)
    assert r["status"]=="SOURCE_STOP_RECORD_ID_MISMATCH"


def test_rate_limit_is_terminal_and_no_retry():
    calls=[]
    def fail(url):
        calls.append(url)
        raise HTTPError(url,429,"rate limit",{},None)
    r=evaluate(P,fail)
    assert r["status"]=="SOURCE_STOP_HTTP_429"
    assert r["request_count"]==1
    assert len(calls)==1
    assert r["biological_response_rows_opened"]==0
