"""Integrity-gated acquisition of the Tanzania Dryad benchmark source.

The module is deliberately pre-outcome. It can authenticate to Dryad, fetch a
full dataset/version archive or individual files, and accepts bytes only when
every frozen size and digest matches the committed public source contract.
It never inspects species-level performance.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

DEFAULT_TOKEN_URL = "https://datadryad.org/oauth/token"
DEFAULT_TIMEOUT_SECONDS = 60
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_DIAGNOSTIC_BODY_BYTES = 4096
USER_AGENT = "eog-tanzania-source-acquisition/0.1"
_HEX_MD5 = re.compile(r"^[0-9a-f]{32}$")


class SourceContractError(ValueError):
    """Raised when the frozen or live source metadata is malformed/drifted."""


class SourceIntegrityError(RuntimeError):
    """Raised when downloaded bytes conflict with the frozen source contract."""


@dataclass(frozen=True)
class DownloadAttempt:
    route: str
    requested_url: str
    authenticated: bool
    status_code: int | None
    final_url: str | None
    content_type: str | None
    content_length: str | None
    bytes_written: int
    sha256: str | None
    classification: str
    detail: str | None = None


@dataclass(frozen=True)
class AcquisitionResult:
    status: str
    doi: str
    version_id: int
    auth_mode: str
    live_manifest_verified: bool
    attempts: list[dict[str, Any]]
    verified_files: dict[str, dict[str, Any]]
    verified_source_dir: str | None
    species_outcomes_inspected: bool
    next_gate: str


def load_source_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise SourceContractError("source contract must be a JSON object")
    for key in ("doi", "dataset_api", "version_id", "version_api", "files"):
        if key not in contract:
            raise SourceContractError(f"source contract missing {key}")
    if not isinstance(contract["files"], list) or not contract["files"]:
        raise SourceContractError("source contract files must be a non-empty list")

    names: set[str] = set()
    ids: set[int] = set()
    for raw in contract["files"]:
        if not isinstance(raw, dict):
            raise SourceContractError("every source file contract must be an object")
        for key in ("id", "name", "size", "digest_type", "digest", "api_download"):
            if key not in raw:
                raise SourceContractError(f"source file contract missing {key}")
        file_id = int(raw["id"])
        name = str(raw["name"])
        size = int(raw["size"])
        digest_type = str(raw["digest_type"]).lower()
        digest = str(raw["digest"]).lower()
        if file_id <= 0 or file_id in ids:
            raise SourceContractError(f"invalid or duplicate Dryad file id: {file_id}")
        if not name or PurePosixPath(name).name != name or name in names:
            raise SourceContractError(f"invalid or duplicate source filename: {name!r}")
        if size <= 0:
            raise SourceContractError(f"non-positive source size for {name}")
        if digest_type != "md5" or not _HEX_MD5.fullmatch(digest):
            raise SourceContractError(f"invalid frozen MD5 for {name}")
        if not str(raw["api_download"]).startswith("https://datadryad.org/"):
            raise SourceContractError(f"unexpected Dryad download URL for {name}")
        names.add(name)
        ids.add(file_id)
    return contract


def compare_live_manifest(contract: Mapping[str, Any], live_manifest: Mapping[str, Any]) -> None:
    """Hard-fail when current public Dryad metadata drifts from the freeze."""
    if str(live_manifest.get("doi")) != str(contract["doi"]):
        raise SourceContractError("live Dryad DOI does not match frozen source contract")
    if str(live_manifest.get("version_api")) != str(contract["version_api"]):
        raise SourceContractError("live Dryad version API does not match frozen version")
    rows = live_manifest.get("files")
    if not isinstance(rows, list):
        raise SourceContractError("live manifest has no files list")
    live = {str(row.get("name")): row for row in rows if isinstance(row, dict)}
    expected = {str(row["name"]): row for row in contract["files"]}
    if set(live) != set(expected):
        raise SourceContractError(
            f"live Dryad filenames drifted: missing={sorted(set(expected)-set(live))}, "
            f"extra={sorted(set(live)-set(expected))}"
        )
    for name, frozen in expected.items():
        row = live[name]
        if int(row.get("declared_size") or 0) != int(frozen["size"]):
            raise SourceContractError(f"live Dryad size drift for {name}")
        if str(row.get("declared_digest_type") or "").lower() != str(frozen["digest_type"]):
            raise SourceContractError(f"live Dryad digest type drift for {name}")
        if str(row.get("declared_digest") or "").lower() != str(frozen["digest"]):
            raise SourceContractError(f"live Dryad digest drift for {name}")
        if str(row.get("api_download") or "") != str(frozen["api_download"]):
            raise SourceContractError(f"live Dryad file download link drift for {name}")


def _oauth_token(
    environment: Mapping[str, str],
    *,
    timeout: int,
) -> tuple[str | None, str]:
    direct = environment.get("DRYAD_API_TOKEN") or environment.get("DRYAD_ACCESS_TOKEN")
    if direct:
        return direct.strip(), "direct_bearer_token"

    client_id = (environment.get("DRYAD_CLIENT_ID") or "").strip()
    client_secret = (environment.get("DRYAD_CLIENT_SECRET") or "").strip()
    if bool(client_id) != bool(client_secret):
        raise SourceContractError(
            "DRYAD_CLIENT_ID and DRYAD_CLIENT_SECRET must be supplied together"
        )
    if not client_id:
        return None, "none"

    token_url = (environment.get("DRYAD_TOKEN_URL") or DEFAULT_TOKEN_URL).strip()
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        token_url,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("ascii"),
        headers={
            "Authorization": f"Basic {basic}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(MAX_DIAGNOSTIC_BODY_BYTES).decode("utf-8", errors="replace")
        raise SourceContractError(
            f"Dryad OAuth token request failed with HTTP {exc.code}: {detail[:500]}"
        ) from exc
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise SourceContractError("Dryad OAuth response did not contain access_token")
    return str(payload["access_token"]), "client_credentials"


def _looks_like_html(prefix: bytes, content_type: str | None) -> bool:
    normalized = (content_type or "").lower()
    stripped = prefix.lstrip().lower()
    return (
        "text/html" in normalized
        or stripped.startswith(b"<!doctype html")
        or stripped.startswith(b"<html")
    )


def _safe_detail(payload: bytes) -> str:
    return payload[:MAX_DIAGNOSTIC_BODY_BYTES].decode("utf-8", errors="replace")


def _download_to_path(
    *,
    route: str,
    url: str,
    destination: Path,
    token: str | None,
    accept: str,
    timeout: int,
    max_bytes: int,
    referer: str | None = None,
) -> DownloadAttempt:
    headers = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }
    if referer:
        headers["Referer"] = referer
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.unlink(missing_ok=True)
    try:
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            body = exc.read(MAX_DIAGNOSTIC_BODY_BYTES)
            content_type = exc.headers.get("Content-Type") if exc.headers else None
            classification = f"http_{exc.code}"
            if _looks_like_html(body, content_type):
                classification = "html_or_bot_challenge"
            elif exc.code == 401:
                classification = "authentication_required"
            elif exc.code == 403:
                classification = "access_forbidden"
            elif exc.code == 405 and b"too large" in body.lower():
                classification = "archive_too_large"
            return DownloadAttempt(
                route=route,
                requested_url=url,
                authenticated=bool(token),
                status_code=int(exc.code),
                final_url=exc.geturl(),
                content_type=content_type,
                content_length=exc.headers.get("Content-Length") if exc.headers else None,
                bytes_written=0,
                sha256=None,
                classification=classification,
                detail=_safe_detail(body),
            )
        with response:
            status = int(getattr(response, "status", response.getcode()))
            content_type = response.headers.get("Content-Type")
            content_length = response.headers.get("Content-Length")
            if status != 200:
                body = response.read(MAX_DIAGNOSTIC_BODY_BYTES)
                return DownloadAttempt(
                    route=route,
                    requested_url=url,
                    authenticated=bool(token),
                    status_code=status,
                    final_url=response.geturl(),
                    content_type=content_type,
                    content_length=content_length,
                    bytes_written=0,
                    sha256=None,
                    classification="accepted_pending" if status == 202 else "non_200_response",
                    detail=_safe_detail(body),
                )

            sha = hashlib.sha256()
            total = 0
            prefix = b""
            with tmp.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    if len(prefix) < 512:
                        prefix += chunk[: 512 - len(prefix)]
                    total += len(chunk)
                    if total > max_bytes:
                        raise SourceContractError(
                            f"download exceeded safety limit of {max_bytes} bytes: {url}"
                        )
                    sha.update(chunk)
                    handle.write(chunk)
            if _looks_like_html(prefix, content_type):
                detail = _safe_detail(tmp.read_bytes())
                tmp.unlink(missing_ok=True)
                return DownloadAttempt(
                    route=route,
                    requested_url=url,
                    authenticated=bool(token),
                    status_code=status,
                    final_url=response.geturl(),
                    content_type=content_type,
                    content_length=content_length,
                    bytes_written=total,
                    sha256=sha.hexdigest(),
                    classification="html_or_bot_challenge",
                    detail=detail,
                )
            tmp.replace(destination)
            return DownloadAttempt(
                route=route,
                requested_url=url,
                authenticated=bool(token),
                status_code=status,
                final_url=response.geturl(),
                content_type=content_type,
                content_length=content_length,
                bytes_written=total,
                sha256=sha.hexdigest(),
                classification="downloaded",
            )
    except urllib.error.URLError as exc:
        tmp.unlink(missing_ok=True)
        return DownloadAttempt(
            route=route,
            requested_url=url,
            authenticated=bool(token),
            status_code=None,
            final_url=None,
            content_type=None,
            content_length=None,
            bytes_written=0,
            sha256=None,
            classification="network_error",
            detail=str(exc.reason),
        )
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _file_digest(path: Path, algorithm: str) -> str:
    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise SourceContractError(f"unsupported source digest algorithm: {algorithm}") from exc
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def verify_file(path: Path, expected: Mapping[str, Any]) -> dict[str, Any]:
    name = str(expected["name"])
    actual_size = path.stat().st_size
    expected_size = int(expected["size"])
    actual_digest = _file_digest(path, str(expected["digest_type"]))
    expected_digest = str(expected["digest"]).lower()
    if actual_size != expected_size:
        raise SourceIntegrityError(
            f"source byte-size mismatch for {name}: got {actual_size}, expected {expected_size}"
        )
    if actual_digest != expected_digest:
        raise SourceIntegrityError(
            f"source digest mismatch for {name}: got {actual_digest}, expected {expected_digest}"
        )
    return {
        "size": actual_size,
        "digest_type": str(expected["digest_type"]),
        "digest": actual_digest,
        "dryad_file_id": int(expected["id"]),
        "verified": True,
    }


def _archive_member_map(archive: zipfile.ZipFile, expected_names: set[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        member = PurePosixPath(info.filename)
        if member.is_absolute() or ".." in member.parts:
            raise SourceIntegrityError(f"unsafe path in Dryad archive: {info.filename!r}")
        basename = member.name
        if basename in expected_names:
            if basename in resolved:
                raise SourceIntegrityError(
                    f"duplicate expected basename in Dryad archive: {basename}"
                )
            resolved[basename] = info.filename
    return resolved


def verify_archive(
    archive_path: Path,
    contract: Mapping[str, Any],
    verified_dir: Path,
) -> dict[str, dict[str, Any]] | None:
    """Verify/extract a package; return None when it is a valid but incomplete zip."""
    if not zipfile.is_zipfile(archive_path):
        return None
    expected = {str(row["name"]): row for row in contract["files"]}
    staging = verified_dir.with_name(verified_dir.name + ".staging")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = _archive_member_map(archive, set(expected))
            if set(members) != set(expected):
                return None
            verified: dict[str, dict[str, Any]] = {}
            for name, row in expected.items():
                target = staging / name
                with archive.open(members[name]) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                verified[name] = verify_file(target, row)
        shutil.rmtree(verified_dir, ignore_errors=True)
        staging.replace(verified_dir)
        return verified
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _attempt_package_routes(
    contract: Mapping[str, Any],
    work_dir: Path,
    *,
    token: str | None,
    timeout: int,
    attempts: list[DownloadAttempt],
) -> tuple[dict[str, dict[str, Any]] | None, Path | None]:
    routes = [
        ("dataset_api_archive", str(contract["dataset_api"]).rstrip("/") + "/download"),
        ("version_api_archive", str(contract["version_api"]).rstrip("/") + "/download"),
    ]
    for route, url in routes:
        package = work_dir / f"{route}.zip"
        attempt = _download_to_path(
            route=route,
            url=url,
            destination=package,
            token=token,
            accept="application/zip",
            timeout=timeout,
            max_bytes=MAX_ARCHIVE_BYTES,
        )
        attempts.append(attempt)
        if attempt.classification != "downloaded":
            continue
        verified_dir = work_dir / "verified_source"
        verified = verify_archive(package, contract, verified_dir)
        if verified is not None:
            return verified, verified_dir
        attempts.append(
            DownloadAttempt(
                route=route + "_verification",
                requested_url=url,
                authenticated=bool(token),
                status_code=attempt.status_code,
                final_url=attempt.final_url,
                content_type=attempt.content_type,
                content_length=attempt.content_length,
                bytes_written=attempt.bytes_written,
                sha256=attempt.sha256,
                classification="downloaded_archive_missing_expected_files_or_not_zip",
            )
        )
    return None, None


def _attempt_individual_routes(
    contract: Mapping[str, Any],
    work_dir: Path,
    *,
    token: str | None,
    timeout: int,
    attempts: list[DownloadAttempt],
) -> tuple[dict[str, dict[str, Any]] | None, Path | None]:
    staging = work_dir / "verified_source.staging"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    verified: dict[str, dict[str, Any]] = {}
    landing = f"https://datadryad.org/dataset/doi%3A{urllib.parse.quote(str(contract['doi']), safe='')}"
    try:
        for row in contract["files"]:
            name = str(row["name"])
            candidates: list[tuple[str, str, str | None]] = []
            if token:
                candidates.append(("file_api_authenticated", str(row["api_download"]), token))
            public = row.get("public_stream")
            if public:
                candidates.append(("public_file_stream", str(public), None))
            if not candidates:
                candidates.append(("file_api_anonymous", str(row["api_download"]), None))

            acquired = False
            for route, url, route_token in candidates:
                target = staging / name
                attempt = _download_to_path(
                    route=f"{route}:{name}",
                    url=url,
                    destination=target,
                    token=route_token,
                    accept=str(row.get("mime_type") or "application/octet-stream"),
                    timeout=timeout,
                    max_bytes=max(int(row["size"]) * 2, int(row["size"]) + 1024 * 1024),
                    referer=landing if route == "public_file_stream" else None,
                )
                attempts.append(attempt)
                if attempt.classification != "downloaded":
                    continue
                verified[name] = verify_file(target, row)
                acquired = True
                break
            if not acquired:
                return None, None

        verified_dir = work_dir / "verified_source"
        shutil.rmtree(verified_dir, ignore_errors=True)
        staging.replace(verified_dir)
        return verified, verified_dir
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def acquire_tanzania_source(
    *,
    contract_path: Path,
    output_dir: Path,
    live_manifest_path: Path | None = None,
    environment: Mapping[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> AcquisitionResult:
    contract = load_source_contract(contract_path)
    live_verified = False
    if live_manifest_path is not None:
        live = json.loads(live_manifest_path.read_text(encoding="utf-8"))
        if not isinstance(live, dict):
            raise SourceContractError("live Dryad manifest must be a JSON object")
        compare_live_manifest(contract, live)
        live_verified = True

    env = dict(os.environ if environment is None else environment)
    token, auth_mode = _oauth_token(env, timeout=timeout)
    output_dir.mkdir(parents=True, exist_ok=True)
    attempts: list[DownloadAttempt] = []

    with tempfile.TemporaryDirectory(prefix="tanzania-source-", dir=output_dir) as tmp_name:
        work_dir = Path(tmp_name)
        verified, verified_dir = _attempt_package_routes(
            contract,
            work_dir,
            token=token,
            timeout=timeout,
            attempts=attempts,
        )
        if verified is None:
            verified, verified_dir = _attempt_individual_routes(
                contract,
                work_dir,
                token=token,
                timeout=timeout,
                attempts=attempts,
            )

        final_verified: Path | None = None
        if verified is not None and verified_dir is not None:
            final_verified = output_dir / "verified_source"
            shutil.rmtree(final_verified, ignore_errors=True)
            shutil.copytree(verified_dir, final_verified)
            status = "verified_official_dryad_bytes"
            next_gate = (
                "run audit_tanzania_verified_bytes.py, then recover explicit column/CRS "
                "semantics from the verified official scripts before any EOG outcome"
            )
        else:
            status = (
                "blocked_missing_dryad_credentials"
                if token is None
                else "blocked_download_unavailable_with_credentials"
            )
            next_gate = (
                "provide DRYAD_CLIENT_ID and DRYAD_CLIENT_SECRET (or DRYAD_API_TOKEN), "
                "rerun acquisition, and accept bytes only after exact frozen MD5/size verification"
            )

    result = AcquisitionResult(
        status=status,
        doi=str(contract["doi"]),
        version_id=int(contract["version_id"]),
        auth_mode=auth_mode,
        live_manifest_verified=live_verified,
        attempts=[asdict(item) for item in attempts],
        verified_files={} if verified is None else verified,
        verified_source_dir=None if final_verified is None else str(final_verified),
        species_outcomes_inspected=False,
        next_gate=next_gate,
    )
    (output_dir / "acquisition_report.json").write_text(
        json.dumps(asdict(result), indent=2) + "\n",
        encoding="utf-8",
    )
    if verified is not None:
        (output_dir / "verified_source_manifest.json").write_text(
            json.dumps(
                {
                    "status": status,
                    "doi": contract["doi"],
                    "version_id": contract["version_id"],
                    "files": verified,
                    "source_contract": str(contract_path),
                    "species_outcomes_inspected": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return result
