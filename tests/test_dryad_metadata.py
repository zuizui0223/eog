import hashlib

import pytest

from eog.v2.dryad_metadata import (
    resolve_dryad_file_identity,
    resolve_dryad_file_roster,
    select_latest_public_submitted_version,
    verify_dryad_file_bytes,
)


def versions_doc():
    return {
        "_embedded": {
            "stash:versions": [
                {
                    "versionNumber": 1,
                    "versionStatus": "submitted",
                    "visibility": "public",
                    "lastModificationDate": "2021-01-01",
                    "_links": {
                        "self": {"href": "/api/v2/versions/10"},
                        "stash:files": {"href": "/api/v2/versions/10/files"},
                    },
                },
                {
                    "versionNumber": 2,
                    "versionStatus": "submitted",
                    "visibility": "public",
                    "lastModificationDate": "2022-01-01",
                    "_links": {
                        "self": {"href": "/api/v2/versions/20"},
                        "stash:files": {"href": "/api/v2/versions/20/files"},
                    },
                },
                {
                    "versionNumber": 3,
                    "versionStatus": "error",
                    "visibility": "public",
                    "_links": {
                        "self": {"href": "/api/v2/versions/30"},
                        "stash:files": {"href": "/api/v2/versions/30/files"},
                    },
                },
            ]
        }
    }


def file_row(raw=b"abc", *, digest_type="md5", file_id=7, path="data.csv", version_id=20):
    algorithm = "md5" if digest_type == "md5" else "sha256"
    return {
        "path": path,
        "size": len(raw),
        "mimeType": "text/csv",
        "status": "copied",
        "digestType": digest_type,
        "digest": hashlib.new(algorithm, raw).hexdigest(),
        "_links": {
            "self": {"href": f"/api/v2/files/{file_id}"},
            "stash:version": {"href": f"/api/v2/versions/{version_id}"},
            "stash:download": {"href": f"/api/v2/downloads/{file_id}"},
        },
    }


def test_selects_highest_public_submitted_version():
    value = select_latest_public_submitted_version(versions_doc())
    assert value.version_id == 20
    assert value.version_number == 2
    assert value.files_href == "/api/v2/versions/20/files"


def test_resolves_md5_file_identity_without_opening_payload():
    row = file_row()
    identity = resolve_dryad_file_identity(row, expected_version_id=20)
    assert identity.file_id == 7
    assert identity.digest_type == "md5"
    assert identity.path == "data.csv"
    assert len(identity.fingerprint) == 64


def test_resolves_sha256_file_identity():
    row = file_row(digest_type="sha-256")
    identity = resolve_dryad_file_identity(row, expected_version_id=20)
    assert identity.digest_type == "sha-256"
    assert len(identity.digest) == 64


def test_file_version_mismatch_fails_closed():
    row = file_row(version_id=99)
    with pytest.raises(ValueError, match="version mismatch"):
        resolve_dryad_file_identity(row, expected_version_id=20)


def test_complete_roster_is_sorted_and_unique():
    rows = [
        file_row(file_id=2, path="z.csv"),
        file_row(file_id=1, path="a.csv"),
    ]
    roster = resolve_dryad_file_roster(rows, expected_version_id=20)
    assert [value.path for value in roster] == ["a.csv", "z.csv"]


def test_duplicate_paths_fail_closed():
    rows = [
        file_row(file_id=1, path="a.csv"),
        file_row(file_id=2, path="a.csv"),
    ]
    with pytest.raises(ValueError, match="paths must be unique"):
        resolve_dryad_file_roster(rows, expected_version_id=20)


def test_later_payload_verification_checks_repository_digest_and_derives_sha256():
    raw = b"abc"
    identity = resolve_dryad_file_identity(
        file_row(raw, digest_type="md5"),
        expected_version_id=20,
    )
    assert verify_dryad_file_bytes(identity, raw) == hashlib.sha256(raw).hexdigest()


def test_later_payload_digest_drift_fails_closed():
    identity = resolve_dryad_file_identity(
        file_row(b"abc", digest_type="md5"),
        expected_version_id=20,
    )
    with pytest.raises(ValueError, match="byte-size drift|repository digest drift"):
        verify_dryad_file_bytes(identity, b"abd")
