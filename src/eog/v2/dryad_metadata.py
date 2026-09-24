"""Dryad public version/file metadata for response-unopened EOG-WF source freezing.

This module is network-free. It validates Dryad REST API JSON that has already been
retrieved under a metadata-only authorization. File payloads are never opened here.

Older Dryad versions may expose MD5 while newer files may expose SHA-256. Repository
identity therefore records the declared digest algorithm and value exactly. If a file is
later authorized for payload access, verification uses the repository digest and also
derives a local SHA-256 from the exact downloaded bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping, Sequence


_SUPPORTED_DIGESTS = {
    "md5": "md5",
    "sha-1": "sha1",
    "sha1": "sha1",
    "sha-256": "sha256",
    "sha256": "sha256",
}


def _sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty str")
    return value.strip()


@dataclass(frozen=True)
class DryadVersionIdentity:
    version_id: int
    version_number: int
    version_status: str
    visibility: str
    files_href: str
    self_href: str
    last_modification_date: str | None
    fingerprint: str


@dataclass(frozen=True)
class DryadFileIdentity:
    file_id: int
    version_id: int
    path: str
    size: int
    mime_type: str | None
    status: str | None
    digest_type: str
    digest: str
    self_href: str
    download_href: str | None
    fingerprint: str


def _id_from_href(href: str, pattern: str, label: str) -> int:
    match = re.fullmatch(pattern, href)
    if match is None:
        raise ValueError(f"{label} is not canonical: {href!r}")
    return int(match.group(1))


def select_latest_public_submitted_version(
    versions_document: Mapping[str, object],
) -> DryadVersionIdentity:
    """Select the highest-numbered public submitted Dryad version."""

    embedded = _mapping(
        versions_document.get("_embedded"),
        "versions._embedded",
    )
    rows = embedded.get("stash:versions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise TypeError("versions._embedded.stash:versions must be an array")

    candidates = []
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"version {index}")
        status = str(row.get("versionStatus") or "").strip().casefold()
        visibility = str(row.get("visibility") or "").strip().casefold()
        if status != "submitted" or visibility not in {"", "public"}:
            continue

        number = row.get("versionNumber")
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ValueError(f"version {index} has invalid versionNumber")

        links = _mapping(row.get("_links"), f"version {index}._links")
        self_href = _text(
            _mapping(links.get("self"), "version self link").get("href"),
            "version self href",
        )
        files_href = _text(
            _mapping(links.get("stash:files"), "version files link").get("href"),
            "version files href",
        )
        version_id = _id_from_href(
            self_href,
            r"/api/v2/versions/([1-9][0-9]*)",
            "version self href",
        )
        if files_href != f"/api/v2/versions/{version_id}/files":
            raise ValueError("version files href is inconsistent with version ID")

        last_modification = row.get("lastModificationDate")
        if last_modification is not None:
            last_modification = str(last_modification)

        payload = {
            "version_id": version_id,
            "version_number": number,
            "version_status": status,
            "visibility": visibility,
            "files_href": files_href,
            "self_href": self_href,
            "last_modification_date": last_modification,
        }
        candidates.append(
            DryadVersionIdentity(
                version_id=version_id,
                version_number=number,
                version_status=status,
                visibility=visibility,
                files_href=files_href,
                self_href=self_href,
                last_modification_date=last_modification,
                fingerprint=_sha256(payload),
            )
        )

    if not candidates:
        raise ValueError("no public submitted Dryad version found")
    return max(candidates, key=lambda value: (value.version_number, value.version_id))


def resolve_dryad_file_identity(
    row: Mapping[str, object],
    *,
    expected_version_id: int,
) -> DryadFileIdentity:
    """Resolve one Dryad file metadata row without opening its payload."""

    path = _text(row.get("path"), "Dryad file path")
    size = row.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ValueError(f"Dryad file {path!r} has invalid size")

    digest_type_raw = _text(row.get("digestType"), f"{path} digestType").casefold()
    if digest_type_raw not in _SUPPORTED_DIGESTS:
        raise ValueError(
            f"Dryad file {path!r} has unsupported digestType {digest_type_raw!r}"
        )
    algorithm = _SUPPORTED_DIGESTS[digest_type_raw]
    digest = _text(row.get("digest"), f"{path} digest").lower()
    expected_length = hashlib.new(algorithm).digest_size * 2
    if len(digest) != expected_length or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(f"Dryad file {path!r} has invalid {algorithm} digest")

    links = _mapping(row.get("_links"), f"{path}._links")
    self_href = _text(
        _mapping(links.get("self"), f"{path} self link").get("href"),
        f"{path} self href",
    )
    file_id = _id_from_href(
        self_href,
        r"/api/v2/files/([1-9][0-9]*)",
        f"{path} self href",
    )

    version_link = links.get("stash:version")
    if version_link is not None:
        version_href = _text(
            _mapping(version_link, f"{path} version link").get("href"),
            f"{path} version href",
        )
        observed_version = _id_from_href(
            version_href,
            r"/api/v2/versions/([1-9][0-9]*)",
            f"{path} version href",
        )
        if observed_version != expected_version_id:
            raise ValueError(
                f"Dryad file {path!r} version mismatch: "
                f"{observed_version} != {expected_version_id}"
            )

    download_href = None
    for relation in ("stash:file-download", "stash:download"):
        link = links.get(relation)
        if isinstance(link, Mapping) and str(link.get("href") or "").strip():
            download_href = str(link["href"]).strip()
            break

    mime_type = row.get("mimeType")
    if mime_type is not None:
        mime_type = str(mime_type).strip() or None
    status = row.get("status")
    if status is not None:
        status = str(status).strip() or None

    payload = {
        "file_id": file_id,
        "version_id": expected_version_id,
        "path": path,
        "size": size,
        "mime_type": mime_type,
        "status": status,
        "digest_type": digest_type_raw,
        "digest": digest,
        "self_href": self_href,
        "download_href": download_href,
    }
    return DryadFileIdentity(
        file_id=file_id,
        version_id=expected_version_id,
        path=path,
        size=size,
        mime_type=mime_type,
        status=status,
        digest_type=digest_type_raw,
        digest=digest,
        self_href=self_href,
        download_href=download_href,
        fingerprint=_sha256(payload),
    )


def resolve_dryad_file_roster(
    file_rows: Sequence[Mapping[str, object]],
    *,
    expected_version_id: int,
) -> tuple[DryadFileIdentity, ...]:
    """Resolve and canonically sort one complete Dryad file roster."""

    identities = tuple(
        resolve_dryad_file_identity(
            row,
            expected_version_id=expected_version_id,
        )
        for row in file_rows
        if str(row.get("status") or "").strip().casefold() != "deleted"
    )
    if not identities:
        raise ValueError("Dryad file roster is empty")
    paths = [value.path for value in identities]
    ids = [value.file_id for value in identities]
    if len(paths) != len(set(paths)):
        raise ValueError("Dryad file paths must be unique")
    if len(ids) != len(set(ids)):
        raise ValueError("Dryad file IDs must be unique")
    return tuple(sorted(identities, key=lambda value: (value.path, value.file_id)))


def verify_dryad_file_bytes(
    identity: DryadFileIdentity,
    raw: bytes,
) -> str:
    """Verify a later authorized payload and return its independently derived SHA-256."""

    if not isinstance(identity, DryadFileIdentity):
        raise TypeError("identity must be DryadFileIdentity")
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    if len(raw) != identity.size:
        raise ValueError(
            f"Dryad file byte-size drift: {len(raw)} != {identity.size}"
        )
    algorithm = _SUPPORTED_DIGESTS[identity.digest_type]
    observed = hashlib.new(algorithm, raw).hexdigest()
    if observed != identity.digest:
        raise ValueError(
            f"Dryad repository digest drift: {observed} != {identity.digest}"
        )
    return hashlib.sha256(raw).hexdigest()
