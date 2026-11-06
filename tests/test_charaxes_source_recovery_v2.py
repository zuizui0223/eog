import hashlib
import io
import pytest
from benchmarks.charaxes_source_recovery_v2 import fetch_verified

PAYLOAD = b'header,value\nexample,1\n'
ENTRY = {'name':'fixture.csv', 'url':'https://zenodo.org/api/records/20525795/files/fixture.csv/content', 'size':len(PAYLOAD), 'md5':hashlib.md5(PAYLOAD).hexdigest()}
class Response(io.BytesIO):
    status = 200
    headers = {'Content-Encoding':'identity','Content-Type':'text/plain'}
    def geturl(self): return ENTRY['url']
def test_wildcard_accept_and_exact_source():
    seen=[]
    def open_(request, timeout):
        seen.append(request)
        return Response(PAYLOAD)
    raw, info = fetch_verified(ENTRY, opener=open_)
    assert raw == PAYLOAD
    assert seen[0].get_header('Accept') == '*/*'
    assert seen[0].full_url == ENTRY['url']
    assert info['md5'] == ENTRY['md5']
    assert info['size'] == len(PAYLOAD)
@pytest.mark.parametrize('payload',[PAYLOAD+b'X',PAYLOAD.replace(b'1',b'2')])
def test_changed_bytes_are_rejected(payload):
    with pytest.raises(ValueError):
        fetch_verified(ENTRY, opener=lambda request,timeout:Response(payload))
def test_no_retry_on_http_error():
    from urllib.error import HTTPError
    calls=[]
    def fail(request,timeout):
        calls.append(request)
        raise HTTPError(request.full_url,429,'rate limit',{},None)
    with pytest.raises(HTTPError): fetch_verified(ENTRY,opener=fail)
    assert len(calls)==1
def test_foreign_redirect_is_rejected_before_following():
    from benchmarks.charaxes_source_recovery_v2 import SameHostRedirect
    from urllib.request import Request
    with pytest.raises(ValueError,match='unapproved'):
        SameHostRedirect().redirect_request(Request(ENTRY['url']),None,302,'Found',{},'https://example.org/file')
