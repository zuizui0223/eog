from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "documentation_contract.json"
DEFAULT_OUTPUT = HERE / "documentation_result.json"


class DocumentationGateStop(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def fetch_documentation(url: str, maximum_bytes: int) -> tuple[bytes, dict[str, object]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-Documentation/1.1",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise DocumentationGateStop(
            f"documentation GET returned HTTP {exc.code}"
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise DocumentationGateStop(
            f"documentation transport unavailable: {exc}"
        ) from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise DocumentationGateStop(
                f"documentation GET returned HTTP {status}"
            )
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise DocumentationGateStop(
                "documentation unexpectedly used content encoding"
            )
        body = response.read(int(maximum_bytes) + 1)
        final_url = response.geturl()

    if len(body) > int(maximum_bytes):
        raise DocumentationGateStop(
            "documentation exceeded frozen byte bound"
        )
    return body, {
        "url": url,
        "final_url": final_url,
        "status": status,
        "bytes_opened": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _decode_utf8(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentationGateStop(
            "documentation is not valid UTF-8/UTF-8-BOM text"
        ) from exc


def _nonempty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def _sanitize_line(line: str, known_paths: tuple[str, ...]) -> str:
    """Preserve frozen filenames but redact all other numeric tokens."""

    protected = str(line)
    placeholders: dict[str, str] = {}
    for index, path in enumerate(sorted(known_paths, key=len, reverse=True)):
        placeholder = f"__EOGFILE_{chr(65 + index)}__"
        if path in protected:
            protected = protected.replace(path, placeholder)
            placeholders[placeholder] = path

    # Redact integers/decimals outside exact frozen filenames. This deliberately removes
    # any class-count or prevalence number from the persisted result.
    protected = re.sub(
        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![A-Za-z])",
        "<n>",
        protected,
    )
    for placeholder, path in placeholders.items():
        protected = protected.replace(placeholder, path)
    return protected


def _extract_sanitized_file_roles(
    lines: list[str],
    known_paths: tuple[str, ...],
    *,
    maximum_saved_lines_per_file: int,
) -> dict[str, list[str]]:
    if maximum_saved_lines_per_file < 1:
        raise ValueError("maximum_saved_lines_per_file must be positive")

    result: dict[str, list[str]] = {}
    for path in known_paths:
        indices = [index for index, line in enumerate(lines) if path in line]
        selected: list[str] = []
        for index in indices:
            selected.append(_sanitize_line(lines[index], known_paths))
            if index + 1 < len(lines):
                selected.append(_sanitize_line(lines[index + 1], known_paths))
            if len(selected) >= maximum_saved_lines_per_file:
                break
        if selected:
            # Stable deduplication while preserving documentation order.
            result[path] = list(dict.fromkeys(selected))[:maximum_saved_lines_per_file]
    return result


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher=fetch_documentation,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    doc = contract["authorized_documentation_file"]
    response = contract["candidate_response_file_from_metadata"]
    policy = contract["extraction_policy"]
    known_paths = tuple(str(value) for value in contract["known_roster_paths"])

    if bool(policy["save_full_documentation_text"]):
        raise ValueError("full README persistence is forbidden")
    if str(response["path"]) not in known_paths:
        raise ValueError("candidate response file is not in frozen Dryad roster")

    base = {
        "schema": "eog.algar_restoration_v3_response_documentation.result.v1_1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "focal_taxon": contract["focal_taxon"],
        "response_file_path": response["path"],
        "documentation_payload_requests": 0,
        "documentation_payload_bytes_opened": 0,
        "response_file_payload_requests": 0,
        "response_file_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    try:
        raw, request = fetcher(
            str(doc["public_download_url"]),
            int(doc["maximum_bytes"]),
        )
        if len(raw) != int(doc["size"]):
            raise DocumentationGateStop(
                f"documentation byte-size drift: {len(raw)} != {doc['size']}"
            )
        digest = hashlib.sha256(raw).hexdigest()
        if digest != str(doc["digest"]).lower():
            raise DocumentationGateStop(
                f"documentation SHA-256 drift: {digest} != {doc['digest']}"
            )

        text = _decode_utf8(raw)
        lines = _nonempty_lines(text)
        role_lines = _extract_sanitized_file_roles(
            lines,
            known_paths,
            maximum_saved_lines_per_file=int(
                policy["maximum_saved_lines_per_file"]
            ),
        )
        response_path = str(response["path"])
        response_mentions = role_lines.get(response_path, [])

        result = {
            **base,
            "status": "documentation_opened_sanitized_response_still_locked",
            "documentation_file": {
                "path": doc["path"],
                "file_id": doc["file_id"],
                "version_id": doc["version_id"],
                "size": doc["size"],
                "sha256": digest,
            },
            "documentation_request": request,
            "documentation_payload_requests": 1,
            "documentation_payload_bytes_opened": len(raw),
            "nonempty_line_count": len(lines),
            "documented_file_roles_sanitized": role_lines,
            "documented_roster_paths": sorted(role_lines),
            "response_filename_documented": bool(response_mentions),
            "response_role_lines_sanitized": response_mentions,
            "full_documentation_text_persisted": False,
            "numeric_biological_summaries_persisted": False,
            "next_gate_if_sufficient": contract["next_if_documentation_sufficient"],
            "next_gate_if_insufficient": contract["next_if_documentation_insufficient"],
        }
    except (DocumentationGateStop, KeyError, TypeError, ValueError) as exc:
        result = {
            **base,
            "status": "stop_documentation_gate",
            "reason": str(exc),
            "documentation_request": None,
            "full_documentation_text_persisted": False,
            "numeric_biological_summaries_persisted": False,
            "next_gate": "none; response CSV remains locked",
        }

    result["fingerprint"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "fingerprint"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "status": result["status"],
                "response_filename_documented": result.get(
                    "response_filename_documented"
                ),
                "documented_roster_paths": result.get("documented_roster_paths"),
                "response_file_payload_bytes_opened": (
                    result["response_file_payload_bytes_opened"]
                ),
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
