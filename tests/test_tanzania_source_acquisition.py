import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from eog.tanzania_source_acquisition import (
    SourceContractError,
    SourceIntegrityError,
    _oauth_token,
    compare_live_manifest,
    load_source_contract,
    verify_archive,
    verify_file,
)


def _contract(tmp_path: Path):
    payloads = {
        "a.csv": b"a,b\n1,2\n",
        "b.R": b"x <- 1\n",
    }
    files = []
    for file_id, (name, payload) in enumerate(payloads.items(), start=1):
        files.append(
            {
                "id": file_id,
                "name": name,
                "size": len(payload),
                "digest_type": "md5",
                "digest": hashlib.md5(payload).hexdigest(),
                "mime_type": "text/plain",
                "api_download": f"https://datadryad.org/api/v2/files/{file_id}/download",
                "public_stream": f"https://datadryad.org/downloads/file_stream/{file_id}",
            }
        )
    contract = {
        "doi": "10.5061/dryad.test",
        "dataset_api": "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.test",
        "version_id": 1,
        "version_api": "https://datadryad.org/api/v2/versions/1",
        "files": files,
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path, contract, payloads


def _live_manifest(contract):
    return {
        "doi": contract["doi"],
        "version_api": contract["version_api"],
        "files": [
            {
                "name": row["name"],
                "declared_size": row["size"],
                "declared_digest_type": row["digest_type"],
                "declared_digest": row["digest"],
                "api_download": row["api_download"],
            }
            for row in contract["files"]
        ],
    }


def test_contract_and_live_manifest_match(tmp_path):
    path, contract, _ = _contract(tmp_path)
    loaded = load_source_contract(path)
    compare_live_manifest(loaded, _live_manifest(contract))


def test_live_manifest_digest_drift_is_rejected(tmp_path):
    path, contract, _ = _contract(tmp_path)
    live = _live_manifest(contract)
    live["files"][0]["declared_digest"] = "0" * 32
    with pytest.raises(SourceContractError, match="digest drift"):
        compare_live_manifest(load_source_contract(path), live)


def test_nested_archive_is_verified_and_flattened(tmp_path):
    _, contract, payloads = _contract(tmp_path)
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, payload in payloads.items():
            archive.writestr(f"dryad-package/{name}", payload)
    verified_dir = tmp_path / "verified"
    verified = verify_archive(archive_path, contract, verified_dir)
    assert set(verified) == set(payloads)
    assert (verified_dir / "a.csv").read_bytes() == payloads["a.csv"]


def test_archive_with_missing_expected_file_is_not_accepted(tmp_path):
    _, contract, payloads = _contract(tmp_path)
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("a.csv", payloads["a.csv"])
    assert verify_archive(archive_path, contract, tmp_path / "verified") is None


def test_archive_digest_mismatch_is_hard_failure(tmp_path):
    _, contract, payloads = _contract(tmp_path)
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("a.csv", b"modified")
        archive.writestr("b.R", payloads["b.R"])
    with pytest.raises(SourceIntegrityError, match="mismatch"):
        verify_archive(archive_path, contract, tmp_path / "verified")


def test_archive_path_traversal_is_hard_failure(tmp_path):
    _, contract, payloads = _contract(tmp_path)
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../a.csv", payloads["a.csv"])
        archive.writestr("b.R", payloads["b.R"])
    with pytest.raises(SourceIntegrityError, match="unsafe path"):
        verify_archive(archive_path, contract, tmp_path / "verified")


def test_file_size_mismatch_is_hard_failure(tmp_path):
    _, contract, _ = _contract(tmp_path)
    path = tmp_path / "a.csv"
    path.write_bytes(b"x")
    assert path.stat().st_size != contract["files"][0]["size"]
    with pytest.raises(SourceIntegrityError, match="byte-size mismatch"):
        verify_file(path, contract["files"][0])


def test_direct_bearer_token_is_supported_without_network():
    token, mode = _oauth_token({"DRYAD_API_TOKEN": "abc"}, timeout=1)
    assert token == "abc"
    assert mode == "direct_bearer_token"


def test_partial_client_credentials_are_rejected():
    with pytest.raises(SourceContractError, match="supplied together"):
        _oauth_token({"DRYAD_CLIENT_ID": "only-one-half"}, timeout=1)
