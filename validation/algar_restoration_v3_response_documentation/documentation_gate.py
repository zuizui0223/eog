from __future__ import annotations

import hashlib
import json
from pathlib import Path
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
            "User-Agent": "EOG-WF-Algar-Documentation/1.0",
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


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher=fetch_documentation,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    doc = contract["authorized_documentation_file"]
    response = contract["candidate_response_file_from_metadata"]

    base = {
        "schema": "eog.algar_restoration_v3_response_documentation.result.v1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "focal_taxon": contract["focal_taxon"],
        "response_file_path": response["path"],
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
        response_mentions = [
            line for line in lines
            if str(response["path"]) in line
        ]
        result = {
            **base,
            "status": "documentation_opened_verified_response_still_locked",
            "documentation_file": {
                "path": doc["path"],
                "file_id": doc["file_id"],
                "version_id": doc["version_id"],
                "size": doc["size"],
                "sha256": digest,
            },
            "documentation_request": request,
            "documentation_text": text,
            "nonempty_line_count": len(lines),
            "candidate_response_filename_mentions": response_mentions,
            "response_filename_documented": bool(response_mentions),
            "next_gate_if_sufficient": contract["next_if_documentation_sufficient"],
            "next_gate_if_insufficient": contract["next_if_documentation_insufficient"],
        }
    except (DocumentationGateStop, KeyError, TypeError, ValueError) as exc:
        result = {
            **base,
            "status": "stop_documentation_gate",
            "reason": str(exc),
            "documentation_request": None,
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
                "response_file_payload_bytes_opened": (
                    result["response_file_payload_bytes_opened"]
                ),
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
