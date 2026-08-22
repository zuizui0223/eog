"""Strict GitHub transport boundary for the response-blind Portal preflight."""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "EOG-portal-DM-response-blind-preflight/1.0"
RAW_HOST = "raw.githubusercontent.com"


def git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _raw_url(contract: dict, path: str) -> str:
    commit = contract["publication"]["repository_commit"]
    return f"https://{RAW_HOST}/weecology/PortalData/{commit}/{path}"


def _bounded_get(url: str, maximum: int, *, role: str) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        with urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            payload = response.read(maximum + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"{role} request failed") from exc
    if status != 200:
        raise RuntimeError(f"{role} returned HTTP {status}")
    if len(payload) > maximum:
        raise RuntimeError(f"{role} exceeded its bounded size")
    return payload


def audit_fixed_tree(contract: dict, audit: dict) -> list[dict[str, object]]:
    tree = contract["github_tree"]
    payload = _bounded_get(tree["url"], int(tree["maximum_bytes"]), role="fixed Git tree")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("fixed Git tree was not UTF-8 JSON") from exc
    if value.get("truncated") is True or not isinstance(value.get("tree"), list):
        raise RuntimeError("fixed Git tree is missing a complete tree list")

    declared = contract["files"]
    observed: dict[str, dict[str, object]] = {}
    for row in value["tree"]:
        path = row.get("path")
        if path not in declared:
            continue
        spec = declared[path]
        compact = {
            "path": path,
            "type": row.get("type"),
            "sha": row.get("sha"),
            "size": row.get("size"),
            "role": spec["role"],
        }
        if compact["type"] != "blob":
            raise RuntimeError(f"declared source path is not a blob: {path}")
        if compact["sha"] != spec["git_blob_sha1"]:
            raise RuntimeError(f"fixed source blob drift: {path}")
        if compact["size"] != spec["size"]:
            raise RuntimeError(f"fixed source size drift: {path}")
        observed[path] = compact
    if set(observed) != set(declared):
        raise RuntimeError(
            f"fixed Git tree is missing declared paths: {sorted(set(declared)-set(observed))}"
        )
    audit["tree_metadata_requests"] = 1
    audit["tree_metadata_bytes"] = len(payload)
    return [observed[path] for path in sorted(observed)]


def download_nonresponse(path: str, contract: dict, audit: dict) -> bytes:
    spec = contract["files"][path]
    if spec["role"] not in set(contract["response_firewall"]["pre_response_allowed_roles"]):
        raise RuntimeError("non-admitted object cannot cross the nonresponse firewall")
    payload = _bounded_get(_raw_url(contract, path), int(spec["size"]), role=path)
    if len(payload) != int(spec["size"]):
        raise RuntimeError(f"nonresponse size mismatch: {path}")
    observed = git_blob_sha1(payload)
    if observed != spec["git_blob_sha1"]:
        raise RuntimeError(f"nonresponse Git blob mismatch: {path}")
    audit["nonresponse_download_requests"].append(path)
    audit["opened_nonresponse_files"].append(
        {"path": path, "bytes": len(payload), "git_blob_sha1": observed}
    )
    return payload


def _proxy_headers(proxy) -> dict[str, str]:  # noqa: ANN001
    if proxy is None or proxy.username is None:
        return {}
    username = unquote(proxy.username)
    password = unquote(proxy.password or "")
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return {"Proxy-Authorization": f"Basic {token}"}


def _connection():
    proxy_value = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy_value:
        proxy = urlparse(proxy_value)
        connection = http.client.HTTPSConnection(proxy.hostname, proxy.port or 80, timeout=30)
        connection.set_tunnel(RAW_HOST, 443, headers=_proxy_headers(proxy))
        return connection
    return http.client.HTTPSConnection(RAW_HOST, 443, timeout=30)


def read_bounded_response_header(
    contract: dict,
    audit: dict,
) -> tuple[str, str, int, dict[str, object]]:
    """Read one response header byte per verified HTTP range and no data-row byte."""

    path = contract["response_file"]
    spec = contract["files"][path]
    maximum = int(contract["response_header_firewall"]["maximum_header_bytes"])
    commit = contract["publication"]["repository_commit"]
    request_path = f"/weecology/PortalData/{commit}/{path}"
    opened = bytearray()
    offsets: list[int] = []
    reconnects = 0
    connection = _connection()
    try:
        for offset in range(maximum):
            for attempt in range(2):
                try:
                    connection.request(
                        "GET",
                        request_path,
                        headers={
                            "Host": RAW_HOST,
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
                    connection = _connection()
            offsets.append(offset)
            if payload in {b"\r", b"\n"}:
                terminator = "CR" if payload == b"\r" else "LF"
                break
            opened.extend(payload)
        else:
            raise RuntimeError("response header terminator not found inside frozen bound")
    finally:
        connection.close()

    try:
        header_text = opened.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError("bounded response header is not UTF-8") from exc
    evidence = {
        "path": path,
        "range_request_count": len(offsets),
        "contiguous_byte_interval": [0, offsets[-1]],
        "header_content_bytes": len(opened),
        "terminator": terminator,
        "bytes_consumed_including_terminator": len(offsets),
        "header_sha256": hashlib.sha256(opened).hexdigest(),
        "transport_reconnects": reconnects,
        "response_rows_opened": False,
        "response_values_opened": False,
    }
    audit["response_header_range_requests"] = len(offsets)
    audit["response_header_bytes_opened"] = len(offsets)
    return header_text, terminator, len(offsets), evidence
