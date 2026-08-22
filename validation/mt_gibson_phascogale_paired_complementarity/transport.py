"""Dryad transport boundary for the Mt Gibson phascogale attempt.

The public Dryad version-download redirect contains a short-lived, signed archive
assembler URL.  That assembler in turn references an official tokenized endpoint
which returns independent S3 URLs for the six files in the fixed version.  This
module uses that manifest to keep the response object physically separate:

* preflight may download only the three declared camera nonresponse objects;
* the response header is acquired one byte at a time and stops at the first CR/LF;
* outcome mode may download the response object once, after authorization.

Short-lived URLs and tokens are intentionally never returned in audit records or
included in exception messages.
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


USER_AGENT = "EOG-mt-gibson-phascogale-frozen-transport/1.0"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _bounded_json_get(url: str, maximum_bytes: int, *, role: str) -> Any:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        },
    )
    try:
        with urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            payload = response.read(maximum_bytes + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"{role} request failed") from exc
    if status != 200:
        raise RuntimeError(f"{role} returned HTTP {status}")
    if len(payload) > maximum_bytes:
        raise RuntimeError(f"{role} exceeded its bounded response size")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{role} did not return bounded UTF-8 JSON") from exc


def _version_redirect(version_download_url: str) -> str:
    request = Request(
        version_download_url,
        method="HEAD",
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        build_opener(_NoRedirect).open(request, timeout=90)
    except HTTPError as exc:
        if exc.code != 302:
            raise RuntimeError(
                f"Dryad version identity returned HTTP {exc.code}, expected 302"
            ) from exc
        location = exc.headers.get("Location")
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("Dryad version identity request failed") from exc
    else:
        raise RuntimeError("Dryad version identity did not return the frozen redirect")
    if not location:
        raise RuntimeError("Dryad version redirect omitted Location")
    parsed = urlparse(location)
    if parsed.scheme != "https" or not parsed.netloc.endswith(
        ".lambda-url.us-west-2.on.aws"
    ):
        raise RuntimeError("Dryad version redirect used an undeclared assembly host")
    return location


def _assembly_manifest_url(version_redirect: str, version_id: int) -> str:
    query = parse_qs(urlparse(version_redirect).query)
    values = query.get("download_url", [])
    if len(values) != 1:
        raise RuntimeError("Dryad assembly redirect omitted one download_url")
    value = unquote(values[0])
    parsed = urlparse(value)
    prefix = f"/api/v2/versions/{version_id}/zip_assembly/"
    if (
        parsed.scheme != "https"
        or parsed.netloc != "datadryad.org"
        or not parsed.path.startswith(prefix)
        or len(parsed.path) <= len(prefix)
    ):
        raise RuntimeError("Dryad assembly manifest route differs from the frozen version")
    return value


def fetch_file_manifest(contract: dict, audit: dict) -> dict[str, str]:
    """Return ephemeral file URLs in memory and record only sanitized identities."""

    source = contract["dryad_source"]
    redirect = _version_redirect(source["version_download_url"])
    assembly_url = _assembly_manifest_url(redirect, int(source["version_id"]))
    value = _bounded_json_get(
        assembly_url,
        int(source["manifest_maximum_bytes"]),
        role="Dryad tokenized file manifest",
    )
    if not isinstance(value, list):
        raise RuntimeError("Dryad tokenized file manifest is not a list")

    declared = contract["files"]
    observed: dict[str, dict[str, object]] = {}
    ephemeral: dict[str, str] = {}
    for row in value:
        if not isinstance(row, dict):
            raise RuntimeError("Dryad tokenized file manifest contains a non-object row")
        name = row.get("filename")
        size = row.get("size")
        url = row.get("url")
        if not isinstance(name, str) or name in observed:
            raise RuntimeError("Dryad tokenized file manifest has invalid file names")
        if name not in declared:
            raise RuntimeError("Dryad tokenized file manifest contains an undeclared file")
        if isinstance(size, bool) or not isinstance(size, int):
            raise RuntimeError("Dryad tokenized file manifest has an invalid file size")
        if size != int(declared[name]["size"]):
            raise RuntimeError(f"Dryad manifest size drift for {name}")
        if not isinstance(url, str):
            raise RuntimeError("Dryad tokenized file manifest omitted an object URL")
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc
            != "dryad-assetstore-merritt-west.s3.us-west-2.amazonaws.com"
        ):
            raise RuntimeError(f"Dryad object host drift for {name}")
        observed[name] = {
            "filename": name,
            "size": size,
            "object_host": parsed.netloc,
            "declared_sha256": declared[name]["sha256"],
            "role": declared[name]["role"],
        }
        ephemeral[name] = url

    if set(observed) != set(declared):
        raise RuntimeError(
            "Dryad tokenized file manifest did not exactly match the closed six-file version"
        )
    audit["manifest_requests"] = 1
    audit["manifest_file_identities"] = [observed[name] for name in sorted(observed)]
    audit["ephemeral_urls_persisted"] = False
    return ephemeral


def _bounded_object_get(url: str, expected_size: int, *, role: str) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        with urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            payload = response.read(expected_size + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"{role} object request failed") from exc
    if status != 200:
        raise RuntimeError(f"{role} object returned HTTP {status}")
    if len(payload) != expected_size:
        raise RuntimeError(
            f"{role} object size mismatch: {len(payload)} != {expected_size}"
        )
    return payload


def download_nonresponse_member(
    name: str,
    contract: dict,
    manifest: dict[str, str],
    audit: dict,
) -> bytes:
    spec = contract["files"][name]
    if spec["role"] not in {"nonresponse_readme", "nonresponse_effort", "nonresponse_geometry"}:
        raise RuntimeError("non-admitted object cannot be opened through the nonresponse path")
    payload = _bounded_object_get(manifest[name], int(spec["size"]), role=name)
    observed = hashlib.sha256(payload).hexdigest()
    if observed != spec["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for nonresponse object {name}")
    audit["nonresponse_download_requests"].append(name)
    audit["opened_nonresponse_files"].append(
        {"filename": name, "bytes": len(payload), "sha256": observed}
    )
    return payload


def download_response_once(
    contract: dict,
    manifest: dict[str, str],
    audit: dict,
) -> bytes:
    name = contract["response_file"]
    spec = contract["files"][name]
    if audit["response_download_requests"]:
        raise RuntimeError("once-only response download budget is already exhausted")
    audit["response_download_requests"].append(name)
    payload = _bounded_object_get(manifest[name], int(spec["size"]), role="response")
    audit["response_payload_bytes_opened"] = len(payload)
    audit["response_rows_opened"] = True
    audit["response_values_opened"] = True
    observed = hashlib.sha256(payload).hexdigest()
    if observed != spec["sha256"]:
        raise RuntimeError("once-opened response object SHA-256 mismatch")
    return payload


def _proxy_tunnel_headers(proxy) -> dict[str, str]:  # noqa: ANN001
    if proxy is None or proxy.username is None:
        return {}
    username = unquote(proxy.username)
    password = unquote(proxy.password or "")
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Proxy-Authorization": f"Basic {token}"}


def _range_connection(parsed):  # noqa: ANN001
    proxy_value = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy_value:
        proxy = urlparse(proxy_value)
        connection = http.client.HTTPSConnection(
            proxy.hostname,
            proxy.port or 80,
            timeout=30,
        )
        connection.set_tunnel(
            parsed.hostname,
            443,
            headers=_proxy_tunnel_headers(proxy),
        )
        return connection
    return http.client.HTTPSConnection(parsed.hostname, 443, timeout=30)


def read_bounded_response_header(
    contract: dict,
    manifest: dict[str, str],
    audit: dict,
) -> tuple[str, str, int, dict[str, object]]:
    """Read exactly one physical response header record, never a data-row byte."""

    name = contract["response_file"]
    spec = contract["files"][name]
    maximum = int(contract["response_header_firewall"]["maximum_header_bytes"])
    parsed = urlparse(manifest[name])
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    opened = bytearray()
    offsets: list[int] = []
    reconnects = 0
    connection = _range_connection(parsed)
    try:
        for offset in range(maximum):
            for attempt in range(2):
                try:
                    connection.request(
                        "GET",
                        path,
                        headers={
                            "Host": parsed.hostname,
                            "User-Agent": USER_AGENT,
                            "Accept-Encoding": "identity",
                            "Range": f"bytes={offset}-{offset}",
                        },
                    )
                    response = connection.getresponse()
                    payload = response.read()
                    expected_range = f"bytes {offset}-{offset}/{int(spec['size'])}"
                    if (
                        response.status != 206
                        or len(payload) != 1
                        or response.getheader("Content-Range") != expected_range
                    ):
                        raise RuntimeError(
                            f"bounded response-header Range verification failed at {offset}"
                        )
                    break
                except (OSError, http.client.HTTPException) as exc:
                    connection.close()
                    if attempt == 1:
                        raise RuntimeError(
                            f"bounded response-header transport failed at byte {offset}"
                        ) from exc
                    reconnects += 1
                    connection = _range_connection(parsed)
            offsets.append(offset)
            if payload in {b"\r", b"\n"}:
                terminator = "CR" if payload == b"\r" else "LF"
                break
            opened.extend(payload)
        else:
            raise RuntimeError("response header terminator was not found inside frozen bound")
    finally:
        connection.close()

    try:
        header_text = opened.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError("bounded response header is not UTF-8") from exc
    evidence = {
        "filename": name,
        "range_request_count": len(offsets),
        "contiguous_byte_interval": [0, offsets[-1]],
        "header_content_bytes": len(opened),
        "terminator": terminator,
        "bytes_consumed_including_terminator": len(offsets),
        "header_sha256": hashlib.sha256(opened).hexdigest(),
        "range_offsets_fingerprint": _canonical_sha256(offsets),
        "transport_reconnects": reconnects,
        "response_rows_opened": False,
        "response_values_opened": False,
        "ephemeral_url_persisted": False,
    }
    audit["response_header_range_requests"] = len(offsets)
    audit["response_header_bytes_opened"] = len(offsets)
    audit["response_payload_bytes_opened"] = 0
    audit["response_rows_opened"] = False
    audit["response_values_opened"] = False
    return header_text, terminator, len(offsets), evidence
