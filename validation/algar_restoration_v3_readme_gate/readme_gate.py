from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "readme_contract.json"
DEFAULT_OUTPUT = HERE / "readme_gate_result.json"


class ReadmeGateStop(RuntimeError):
    pass


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _fetch_exact(url: str, expected_size: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-README-Gate/1.0",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise ReadmeGateStop(f"README GET returned HTTP {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise ReadmeGateStop(f"README transport unavailable: {exc}") from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise ReadmeGateStop(f"README GET returned HTTP {status}")
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise ReadmeGateStop("README unexpectedly used content encoding")
        body = response.read(expected_size + 1)
    if len(body) != expected_size:
        raise ReadmeGateStop(
            f"README byte-size drift: {len(body)} != {expected_size}"
        )
    return body


def _normalise_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _extract_target_section(
    lines: list[str],
    *,
    target_file: str,
    known_file_paths: list[str],
) -> dict[str, object]:
    target_indices = [
        index
        for index, line in enumerate(lines)
        if target_file.casefold() in line.casefold()
    ]
    if not target_indices:
        raise ReadmeGateStop(
            "README does not mention the frozen target response filename"
        )

    start = target_indices[0]
    known_other = [
        path for path in known_file_paths if path != target_file
    ]

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line_fold = lines[index].casefold()
        if any(path.casefold() in line_fold for path in known_other):
            end = index
            break

    # Keep a small amount of preceding context because README headings frequently sit
    # directly above a filename line.
    context_start = max(0, start - 2)
    section = lines[context_start:end]
    while section and not section[-1].strip():
        section.pop()

    compact = [line for line in section if line.strip()]
    joined = "\n".join(compact)
    return {
        "start_line_1based": context_start + 1,
        "end_line_1based": context_start + len(section),
        "lines": compact,
        "sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
    }


def _question_support(section_lines: list[str]) -> dict[str, object]:
    text = "\n".join(section_lines).casefold()

    groups = {
        "event_or_detection_role": (
            "detection",
            "observation",
            "independent",
            "30min",
            "30 min",
        ),
        "station_or_node_field": (
            "station",
            "site",
            "camera",
            "location",
            "placename",
        ),
        "date_or_time_field": (
            "date",
            "time",
            "year",
            "month",
            "day",
            "timestamp",
        ),
        "species_or_taxon_field": (
            "species",
            "taxon",
            "common name",
            "scientific name",
        ),
    }

    evidence: dict[str, object] = {}
    for key, tokens in groups.items():
        matched = tuple(token for token in tokens if token in text)
        evidence[key] = {
            "supported": bool(matched),
            "matched_terms": list(matched),
        }
    return evidence


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    doc = contract["authorized_documentation_file"]
    target = contract["documentation_extraction"]["target_response_file"]
    known_files = list(contract["forbidden_payloads"]["response_csv_files"]) + [
        doc["path"]
    ]

    base = {
        "schema": "eog.algar_restoration_v3_readme_documentation_gate.result.v1",
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
        raw = _fetch_exact(str(doc["public_url"]), int(doc["size"]))
        observed_sha = hashlib.sha256(raw).hexdigest()
        if observed_sha != str(doc["sha256"]):
            raise ReadmeGateStop(
                f"README SHA-256 drift: {observed_sha} != {doc['sha256']}"
            )
        base["documentation_payload_requests"] = 1
        base["documentation_payload_bytes_opened"] = len(raw)

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReadmeGateStop("README is not valid UTF-8 text") from exc

        lines = _normalise_lines(text)
        section = _extract_target_section(
            lines,
            target_file=str(target),
            known_file_paths=known_files,
        )
        support = _question_support(list(section["lines"]))
        all_supported = all(
            bool(value["supported"]) for value in support.values()
        )

        file_mentions = sorted(
            {
                path
                for path in known_files
                if any(path.casefold() in line.casefold() for line in lines)
            }
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
            "mentioned_frozen_files": file_mentions,
            "target_section": section,
            "question_support": support,
            "all_four_questions_supported": all_supported,
            "next_gate": (
                contract["next_if_pass"]
                if all_supported
                else "none; do not open any response CSV payload"
            ),
        }
    except (ReadmeGateStop, ValueError, TypeError, KeyError) as exc:
        result = {
            **base,
            "status": "stop_readme_documentation_gate",
            "reason": str(exc),
            "next_gate": "none; do not open any response CSV payload",
        }

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
                "documentation_payload_bytes_opened": result[
                    "documentation_payload_bytes_opened"
                ],
                "response_csv_payload_bytes_opened": result[
                    "response_csv_payload_bytes_opened"
                ],
                "question_support": result.get("question_support"),
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
