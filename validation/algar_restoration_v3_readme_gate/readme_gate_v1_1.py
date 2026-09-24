from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

from validation.algar_restoration_v3_readme_gate.readme_gate import (
    ReadmeGateStop,
    _canonical_sha256,
    _extract_target_section,
    _normalise_lines,
    _question_support,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "readme_contract_v1_1.json"
DEFAULT_OUTPUT = HERE / "readme_gate_result_v1_1.json"


class ReadmeTransportStop(ReadmeGateStop):
    def __init__(self, message: str, ledger: list[dict[str, object]]):
        super().__init__(message)
        self.ledger = list(ledger)


def _head(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "Accept": "text/plain,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-README-Gate/1.1",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        return {
            "role": "readme_head",
            "method": "HEAD",
            "status": int(exc.code),
            "final_url": url,
            "content_length": None,
            "bytes_opened": 0,
            "error": f"HTTP {exc.code}",
        }
    except (OSError, urllib.error.URLError) as exc:
        return {
            "role": "readme_head",
            "method": "HEAD",
            "status": None,
            "final_url": url,
            "content_length": None,
            "bytes_opened": 0,
            "error": str(exc),
        }

    with response:
        status = int(getattr(response, "status", response.getcode()))
        final_url = response.geturl()
        content_length = response.headers.get("Content-Length")
        content_encoding = response.headers.get("Content-Encoding", "identity")
    return {
        "role": "readme_head",
        "method": "HEAD",
        "status": status,
        "final_url": final_url,
        "content_length": content_length,
        "content_encoding": content_encoding,
        "bytes_opened": 0,
        "error": None,
    }


def _get_exact(
    url: str,
    *,
    expected_size: int,
    maximum_bytes: int,
) -> tuple[bytes, dict[str, object]]:
    if maximum_bytes < expected_size:
        raise ValueError("maximum_bytes must be >= expected_size")

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-README-Gate/1.1",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        ledger = [{
            "role": "readme_get",
            "method": "GET",
            "status": int(exc.code),
            "final_url": url,
            "content_length": None,
            "content_encoding": None,
            "bytes_opened": 0,
            "sha256": None,
            "error": f"HTTP {exc.code}",
        }]
        raise ReadmeTransportStop(
            f"README GET returned HTTP {exc.code}",
            ledger,
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        ledger = [{
            "role": "readme_get",
            "method": "GET",
            "status": None,
            "final_url": url,
            "content_length": None,
            "content_encoding": None,
            "bytes_opened": 0,
            "sha256": None,
            "error": str(exc),
        }]
        raise ReadmeTransportStop(
            f"README GET transport unavailable: {exc}",
            ledger,
        ) from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        final_url = response.geturl()
        content_length = response.headers.get("Content-Length")
        content_encoding = response.headers.get("Content-Encoding", "identity")
        if status != 200:
            item = {
                "role": "readme_get",
                "method": "GET",
                "status": status,
                "final_url": final_url,
                "content_length": content_length,
                "content_encoding": content_encoding,
                "bytes_opened": 0,
                "sha256": None,
                "error": f"HTTP {status}",
            }
            raise ReadmeTransportStop(
                f"README GET returned HTTP {status}",
                [item],
            )
        if str(content_encoding).casefold() != "identity":
            item = {
                "role": "readme_get",
                "method": "GET",
                "status": status,
                "final_url": final_url,
                "content_length": content_length,
                "content_encoding": content_encoding,
                "bytes_opened": 0,
                "sha256": None,
                "error": "unexpected content encoding",
            }
            raise ReadmeTransportStop(
                "README unexpectedly used content encoding",
                [item],
            )
        body = response.read(maximum_bytes)

    item = {
        "role": "readme_get",
        "method": "GET",
        "status": status,
        "final_url": final_url,
        "content_length": content_length,
        "content_encoding": content_encoding,
        "bytes_opened": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "error": None,
    }
    if len(body) != expected_size:
        raise ReadmeTransportStop(
            f"README byte-size drift: {len(body)} != {expected_size}",
            [item],
        )
    return body, item


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    doc = contract["authorized_documentation_file"]
    target = contract["documentation_extraction"]["target_response_file"]
    response_paths = [
        "Algar_2015_2019_30min_Independent_JPE_Beirne_et_al_2021.csv",
        "YData_JPE_Beirne_et_al_2021.csv",
        "YData_dataframe_format_JPE_Beirne_et_al_2021.csv",
        "monthly_counts_JPE_Beirne_et_al_2021.csv",
        "total_observations_JPE_Beirne_et_al_2021.csv",
        "Species_comon_names_JPE_Beirne_et_al_2021.csv",
    ]
    ledger: list[dict[str, object]] = []

    base = {
        "schema": "eog.algar_restoration_v3_readme_documentation_gate.result.v1_1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "documentation_payload_requests": 0,
        "documentation_payload_bytes_opened": 0,
        "response_csv_payload_requests": 0,
        "response_csv_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "focal_taxon_changed": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    try:
        head_item = _head(str(doc["public_url"]))
        ledger.append(head_item)

        raw, get_item = _get_exact(
            str(doc["public_url"]),
            expected_size=int(doc["size"]),
            maximum_bytes=int(contract["transport_accounting"]["get_maximum_bytes"]),
        )
        ledger.append(get_item)
        base["documentation_payload_requests"] = 1
        base["documentation_payload_bytes_opened"] = len(raw)

        observed_sha = hashlib.sha256(raw).hexdigest()
        if observed_sha != str(doc["sha256"]):
            raise ReadmeGateStop(
                f"README SHA-256 drift: {observed_sha} != {doc['sha256']}"
            )

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReadmeGateStop("README is not valid UTF-8 text") from exc

        lines = _normalise_lines(text)
        section = _extract_target_section(
            lines,
            target_file=str(target),
            known_file_paths=response_paths + [doc["path"]],
        )
        support = _question_support(list(section["lines"]))
        all_supported = all(
            bool(value["supported"]) for value in support.values()
        )
        result = {
            **base,
            "status": (
                "readme_documentation_sufficient_for_schema_freeze"
                if all_supported
                else "stop_readme_documentation_insufficient"
            ),
            "documentation_file": {
                "path": doc["path"],
                "file_id": doc["file_id"],
                "bytes": len(raw),
                "sha256": observed_sha,
            },
            "target_response_file": target,
            "target_section": section,
            "question_support": support,
            "all_four_questions_supported": all_supported,
            "next_gate": (
                contract["next_if_pass"]
                if all_supported
                else "none; do not open any response CSV payload"
            ),
        }
    except ReadmeTransportStop as exc:
        ledger.extend(exc.ledger)
        result = {
            **base,
            "status": "stop_readme_transport_v1_1",
            "reason": str(exc),
            "next_gate": "none; do not open any response CSV payload",
        }
    except (ReadmeGateStop, ValueError, TypeError, KeyError) as exc:
        result = {
            **base,
            "status": "stop_readme_documentation_gate_v1_1",
            "reason": str(exc),
            "next_gate": "none; do not open any response CSV payload",
        }

    result["request_ledger"] = ledger
    result["documentation_payload_bytes_opened"] = sum(
        int(item.get("bytes_opened", 0))
        for item in ledger
        if item.get("method") == "GET"
    )
    result["fingerprint"] = _canonical_sha256(
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
                "reason": result.get("reason"),
                "documentation_payload_bytes_opened": result[
                    "documentation_payload_bytes_opened"
                ],
                "response_csv_payload_bytes_opened": result[
                    "response_csv_payload_bytes_opened"
                ],
                "question_support": result.get("question_support"),
                "request_ledger": result.get("request_ledger"),
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
