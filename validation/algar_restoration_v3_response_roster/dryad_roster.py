from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urljoin
import urllib.error
import urllib.request

from eog.v2.dryad_metadata import (
    resolve_dryad_file_roster,
    select_latest_public_submitted_version,
)
from eog.v2.source_discovery_firewall import (
    SourceDescriptor,
    classify_source_descriptor,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "roster_contract.json"
DEFAULT_OUTPUT = HERE / "dryad_roster_result.json"

JsonFetcher = Callable[[str, int, str], tuple[dict[str, object], dict[str, object]]]


class RosterStop(RuntimeError):
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


def fetch_json(
    url: str,
    maximum_bytes: int,
    role: str,
) -> tuple[dict[str, object], dict[str, object]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "EOG-WF-Algar-Dryad-Roster/1.0",
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise RosterStop(f"{role} returned HTTP {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise RosterStop(f"{role} transport unavailable: {exc}") from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise RosterStop(f"{role} returned HTTP {status}")
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise RosterStop(f"{role} unexpectedly used content encoding")
        body = response.read(int(maximum_bytes) + 1)
        final_url = response.geturl()

    if not body:
        raise RosterStop(f"{role} returned an empty body")
    if len(body) > int(maximum_bytes):
        raise RosterStop(f"{role} exceeded frozen JSON byte bound")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RosterStop(f"{role} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RosterStop(f"{role} JSON root is not an object")

    return payload, {
        "role": role,
        "url": url,
        "final_url": final_url,
        "status": status,
        "bytes_opened": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _href(document: Mapping[str, object], relation: str, label: str) -> str:
    links = document.get("_links")
    if not isinstance(links, Mapping):
        raise RosterStop(f"{label} lacks _links")
    link = links.get(relation)
    if not isinstance(link, Mapping):
        raise RosterStop(f"{label} lacks {relation}")
    href = str(link.get("href") or "").strip()
    if not href:
        raise RosterStop(f"{label} {relation} href is empty")
    return href


def _absolute(base: str, href: str) -> str:
    if href.startswith("https://"):
        return href
    if href.startswith("http://"):
        raise RosterStop("Dryad metadata link unexpectedly uses HTTP")
    return urljoin(base.rstrip("/") + "/", href.lstrip("/"))


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher: JsonFetcher = fetch_json,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    dryad = contract["dryad"]
    bounds = contract["metadata_only_authorization"]

    base = {
        "schema": "eog.algar_restoration_v3_dryad_response_roster.result.v1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "focal_species_selected": False,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }
    ledger: list[dict[str, object]] = []

    try:
        dataset, item = fetcher(
            str(dryad["api_dataset_url"]),
            int(dryad["maximum_json_bytes_per_request"]),
            "dryad_dataset_metadata",
        )
        ledger.append(item)

        identifier = str(dataset.get("identifier") or "").strip().casefold()
        expected_identifiers = {
            str(dryad["doi"]).casefold(),
            f"doi:{dryad['doi']}".casefold(),
        }
        if identifier not in expected_identifiers:
            raise RosterStop(f"Dryad DOI identity drift: {identifier!r}")

        title = str(dataset.get("title") or "").strip()
        expected_substring = str(
            dryad["expected_publication_title_substring"]
        ).casefold()
        if expected_substring not in title.casefold():
            raise RosterStop("Dryad title does not match the frozen publication identity")

        version_href = _href(dataset, "stash:version", "Dryad dataset")
        version_url = _absolute(str(dryad["api_base_url"]), version_href)
        version_row, item = fetcher(
            version_url,
            int(dryad["maximum_json_bytes_per_request"]),
            "dryad_latest_version_metadata",
        )
        ledger.append(item)

        version_doc = {
            "_embedded": {
                "stash:versions": [version_row],
            }
        }
        version = select_latest_public_submitted_version(version_doc)

        files_url = _absolute(
            str(dryad["api_base_url"]),
            version.files_href,
        )
        separator = "&" if "?" in files_url else "?"
        page_url = (
            files_url
            + separator
            + f"per_page={min(int(dryad['maximum_files']), 1000)}"
        )

        rows: list[Mapping[str, object]] = []
        page_count = 0
        while page_url:
            page_count += 1
            if page_count > int(dryad["maximum_file_pages"]):
                raise RosterStop("Dryad file roster exceeded frozen page bound")

            page, item = fetcher(
                page_url,
                int(dryad["maximum_json_bytes_per_request"]),
                f"dryad_file_roster_page_{page_count}",
            )
            ledger.append(item)
            embedded = page.get("_embedded")
            if not isinstance(embedded, Mapping):
                raise RosterStop("Dryad file page lacks _embedded")
            values = embedded.get("stash:files")
            if not isinstance(values, list):
                raise RosterStop("Dryad file page stash:files is not an array")
            rows.extend(
                value for value in values if isinstance(value, Mapping)
            )
            if len(rows) > int(dryad["maximum_files"]):
                raise RosterStop("Dryad file roster exceeded frozen file-count bound")

            links = page.get("_links")
            next_href = None
            if isinstance(links, Mapping):
                next_link = links.get("next")
                if isinstance(next_link, Mapping):
                    next_href = str(next_link.get("href") or "").strip() or None
            page_url = (
                None
                if next_href is None
                else _absolute(str(dryad["api_base_url"]), next_href)
            )

        roster = resolve_dryad_file_roster(
            rows,
            expected_version_id=version.version_id,
        )

        classifications = []
        response_candidates = []
        ambiguous = []
        safe_candidates = []
        row_by_path = {
            str(row.get("path") or "").strip(): row for row in rows
        }
        for identity in roster:
            row = row_by_path.get(identity.path, {})
            description = str(row.get("description") or "")
            classified = classify_source_descriptor(
                SourceDescriptor(
                    source_id=f"dryad-file-{identity.file_id}",
                    path_or_name=identity.path,
                    metadata_note=description,
                )
            )
            item = {
                "file": asdict(identity),
                "classification": classified.classification,
                "content_open_allowed": classified.content_open_allowed,
                "response_indicators": list(classified.response_indicators),
                "safe_indicators": list(classified.safe_indicators),
                "classification_fingerprint": classified.fingerprint,
            }
            classifications.append(item)
            if classified.classification == "response_bearing":
                response_candidates.append(identity.path)
            elif classified.classification == "safe_candidate":
                safe_candidates.append(identity.path)
            else:
                ambiguous.append(identity.path)

        result = {
            **base,
            "status": "dryad_response_roster_resolved_metadata_only",
            "dataset": {
                "identifier": dataset.get("identifier"),
                "title": title,
                "publication_date": dataset.get("publicationDate"),
                "version_number": dataset.get("versionNumber"),
                "related_works": dataset.get("relatedWorks"),
            },
            "version": asdict(version),
            "file_count": len(roster),
            "files": classifications,
            "response_bearing_paths": sorted(response_candidates),
            "safe_candidate_paths": sorted(safe_candidates),
            "ambiguous_do_not_open_paths": sorted(ambiguous),
            "next_gate": contract["next_if_roster_resolved"],
        }
    except (RosterStop, ValueError, TypeError, KeyError) as exc:
        result = {
            **base,
            "status": "stop_dryad_metadata_roster",
            "reason": str(exc),
            "next_gate": "none; do not open any Dryad file payload",
        }

    result["request_ledger"] = ledger
    result["metadata_requests"] = len(ledger)
    result["metadata_bytes_opened"] = sum(
        int(item["bytes_opened"]) for item in ledger
    )
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
                "file_count": result.get("file_count"),
                "response_bearing_paths": result.get("response_bearing_paths"),
                "ambiguous_do_not_open_paths": result.get(
                    "ambiguous_do_not_open_paths"
                ),
                "file_payload_bytes_opened": result["file_payload_bytes_opened"],
                "fingerprint": result["fingerprint"],
            },
            sort_keys=True,
        )
    )
