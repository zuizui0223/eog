"""Canonical Git blob identity for response-independent EOG-WF source artifacts.

Git object identity is defined over exact bytes as:

    sha1(b"blob " + ascii(len(payload)) + b"\\0" + payload)

For repository-backed prospective sources, this lets the scientific contract bind the
actual raw bytes without mixing API-decoded text length, newline normalization, or
transport representation with source identity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


def git_blob_sha1(payload: bytes) -> str:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class GitBlobIdentity:
    git_blob_sha1: str
    raw_byte_count: int
    raw_sha256: str
    fingerprint: str

    @classmethod
    def from_bytes(cls, payload: bytes) -> "GitBlobIdentity":
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        values = {
            "git_blob_sha1": git_blob_sha1(payload),
            "raw_byte_count": len(payload),
            "raw_sha256": hashlib.sha256(payload).hexdigest(),
        }
        return cls(
            git_blob_sha1=values["git_blob_sha1"],
            raw_byte_count=values["raw_byte_count"],
            raw_sha256=values["raw_sha256"],
            fingerprint=_sha256(values),
        )

    def verify(self, payload: bytes) -> None:
        observed = type(self).from_bytes(payload)
        if observed.git_blob_sha1 != self.git_blob_sha1:
            raise ValueError(
                "raw source Git blob SHA-1 differs from frozen identity"
            )
        if observed.raw_byte_count != self.raw_byte_count:
            raise ValueError(
                "raw source byte count differs from frozen identity"
            )
        if observed.raw_sha256 != self.raw_sha256:
            raise ValueError(
                "raw source SHA-256 differs from frozen identity"
            )


def verify_expected_git_blob(
    payload: bytes,
    *,
    expected_git_blob_sha1: str,
) -> GitBlobIdentity:
    """Verify exact raw bytes against a prospectively frozen Git blob object ID.

    Byte count and SHA-256 are derived from the verified raw bytes. They are outputs,
    not independently hand-copied source declarations.
    """

    expected = str(expected_git_blob_sha1).strip().lower()
    if len(expected) != 40 or any(ch not in "0123456789abcdef" for ch in expected):
        raise ValueError("expected_git_blob_sha1 must be 40 lowercase hex characters")
    observed = GitBlobIdentity.from_bytes(payload)
    if observed.git_blob_sha1 != expected:
        raise ValueError(
            f"raw source Git blob mismatch: {observed.git_blob_sha1} != {expected}"
        )
    return observed
