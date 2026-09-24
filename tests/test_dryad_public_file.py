import hashlib

import pytest

from eog.v2.dryad_public_file import (
    resolve_dryad_published_file,
    verify_dryad_file_bytes,
)


def record(raw=b"abc"):
    return {
        "path": "deployments.csv",
        "size": len(raw),
        "digest": hashlib.sha256(raw).hexdigest(),
        "digestType": "sha-256",
        "_links": {
            "self": {"href": "/api/v2/files/12345"},
            "stash:download": {"href": "/api/v2/files/12345/download"},
        },
    }


def test_resolves_anonymous_public_route_from_canonical_file_id():
    identity = resolve_dryad_published_file(record())
    assert identity.file_id == 12345
    assert identity.public_download_url == (
        "https://datadryad.org/stash/downloads/file_stream/12345"
    )
    assert identity.path == "deployments.csv"
    assert len(identity.fingerprint) == 64


def test_download_bytes_are_verified_against_repository_identity():
    raw = b"abc"
    identity = resolve_dryad_published_file(record(raw))
    assert verify_dryad_file_bytes(identity, raw) == hashlib.sha256(raw).hexdigest()


def test_byte_size_drift_fails_closed():
    identity = resolve_dryad_published_file(record(b"abc"))
    with pytest.raises(ValueError, match="byte-size drift"):
        verify_dryad_file_bytes(identity, b"abcd")


def test_sha_drift_fails_closed():
    row = record(b"abc")
    row["digest"] = "0" * 64
    identity = resolve_dryad_published_file(row)
    with pytest.raises(ValueError, match="SHA-256 drift"):
        verify_dryad_file_bytes(identity, b"abc")


def test_self_and_download_links_must_agree():
    row = record()
    row["_links"]["stash:download"]["href"] = "/api/v2/files/999/download"
    with pytest.raises(ValueError, match="inconsistent with file ID"):
        resolve_dryad_published_file(row)


def test_non_sha256_identity_is_rejected():
    row = record()
    row["digestType"] = "md5"
    with pytest.raises(ValueError, match="must declare SHA-256"):
        resolve_dryad_published_file(row)


def test_noncanonical_self_href_is_rejected():
    row = record()
    row["_links"]["self"]["href"] = "/api/v2/files/not-an-id"
    with pytest.raises(ValueError, match="canonical file ID"):
        resolve_dryad_published_file(row)
