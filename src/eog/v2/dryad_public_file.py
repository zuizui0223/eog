"""Published Dryad individual-file identities for response-blind source qualification.

Dryad's REST API exposes immutable file metadata (path, byte size, SHA-256 digest and
file ID) for public dataset versions. Public landing pages serve individual files through
an anonymous file_stream route. This module derives that route from the API file ID while
keeping scientific identity anchored to the repository-reported byte size and SHA-256.

It performs no network access itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping


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
class DryadPublishedFileIdentity:
    path: str
    size: int
    sha256: str
    file_id: int
    api_self_href: str
    api_download_href: str
    public_download_url: str
    fingerprint: str


def resolve_dryad_published_file(
    row: Mapping[str, object],
    *,
    public_base_url: str = "https://datadryad.org/stash/downloads/file_stream",
) -> DryadPublishedFileIdentity:
    """Resolve one public Dryad file record to a content-addressed anonymous route."""

    path = str(row.get("path") or "").strip()
    if not path:
        raise ValueError("Dryad file path must be non-empty")

    size = row.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ValueError(f"Dryad file {path!r} has invalid byte size")

    digest = str(row.get("digest") or "").strip().lower()
    digest_type = str(row.get("digestType") or "").strip().lower()
    if digest_type not in {"sha-256", "sha256"}:
        raise ValueError(
            f"Dryad file {path!r} must declare SHA-256, observed {digest_type!r}"
        )
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError(f"Dryad file {path!r} has invalid SHA-256 digest")

    links = row.get("_links")
    if not isinstance(links, Mapping):
        raise ValueError(f"Dryad file {path!r} has no _links")

    self_link = links.get("self")
    download_link = links.get("stash:download")
    if not isinstance(self_link, Mapping):
        raise ValueError(f"Dryad file {path!r} has no self link")
    if not isinstance(download_link, Mapping):
        raise ValueError(f"Dryad file {path!r} has no stash:download link")

    self_href = str(self_link.get("href") or "").strip()
    api_download_href = str(download_link.get("href") or "").strip()
    match = re.fullmatch(r"/api/v2/files/([1-9][0-9]*)", self_href)
    if match is None:
        raise ValueError(
            f"Dryad file {path!r} self href does not expose a canonical file ID"
        )
    file_id = int(match.group(1))

    expected_api_download = f"/api/v2/files/{file_id}/download"
    if api_download_href != expected_api_download:
        raise ValueError(
            f"Dryad file {path!r} download href is inconsistent with file ID"
        )

    base = str(public_base_url).rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("Dryad public_base_url must use HTTPS")
    public_url = f"{base}/{file_id}"

    payload = {
        "schema": "eog.dryad_published_file_identity.v1",
        "path": path,
        "size": size,
        "sha256": digest,
        "file_id": file_id,
        "api_self_href": self_href,
        "api_download_href": api_download_href,
        "public_download_url": public_url,
    }
    return DryadPublishedFileIdentity(
        path=path,
        size=size,
        sha256=digest,
        file_id=file_id,
        api_self_href=self_href,
        api_download_href=api_download_href,
        public_download_url=public_url,
        fingerprint=_sha256(payload),
    )


def verify_dryad_file_bytes(
    identity: DryadPublishedFileIdentity,
    raw: bytes,
) -> str:
    """Verify downloaded bytes against the Dryad repository identity."""

    if not isinstance(identity, DryadPublishedFileIdentity):
        raise TypeError("identity must be DryadPublishedFileIdentity")
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    if len(raw) != identity.size:
        raise ValueError(
            f"Dryad file byte-size drift: {len(raw)} != {identity.size}"
        )
    digest = hashlib.sha256(raw).hexdigest()
    if digest != identity.sha256:
        raise ValueError(
            f"Dryad file SHA-256 drift: {digest} != {identity.sha256}"
        )
    return digest
