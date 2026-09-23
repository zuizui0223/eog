import pytest

from eog.v2.git_blob_identity import (
    GitBlobIdentity,
    git_blob_sha1,
    verify_expected_git_blob,
)


def test_git_blob_sha1_matches_known_git_object_rule():
    payload = b"hello\n"
    # git hash-object for b"hello\\n"
    assert git_blob_sha1(payload) == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_identity_derives_byte_count_and_sha256_from_same_raw_bytes():
    payload = b"a,b\r\n1,2\r\n"
    identity = GitBlobIdentity.from_bytes(payload)
    assert identity.raw_byte_count == len(payload)
    assert len(identity.raw_sha256) == 64
    assert len(identity.git_blob_sha1) == 40
    identity.verify(payload)


def test_newline_representation_changes_blob_identity_and_byte_count():
    lf = GitBlobIdentity.from_bytes(b"a,b\n1,2\n")
    crlf = GitBlobIdentity.from_bytes(b"a,b\r\n1,2\r\n")
    assert lf.git_blob_sha1 != crlf.git_blob_sha1
    assert lf.raw_byte_count != crlf.raw_byte_count
    assert lf.raw_sha256 != crlf.raw_sha256


def test_verify_expected_blob_uses_blob_sha_as_primary_contract():
    payload = b"projects.csv\n"
    expected = git_blob_sha1(payload)
    identity = verify_expected_git_blob(
        payload,
        expected_git_blob_sha1=expected,
    )
    assert identity.git_blob_sha1 == expected
    assert identity.raw_byte_count == len(payload)


def test_verify_expected_blob_rejects_different_raw_representation():
    payload = b"x\n"
    expected = git_blob_sha1(payload)
    with pytest.raises(ValueError, match="Git blob mismatch"):
        verify_expected_git_blob(
            b"x\r\n",
            expected_git_blob_sha1=expected,
        )


def test_invalid_expected_blob_sha_fails_closed():
    with pytest.raises(ValueError, match="40 lowercase hex"):
        verify_expected_git_blob(b"x", expected_git_blob_sha1="not-a-sha")
