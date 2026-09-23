from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_selection_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_metadata_certificate.json"
USER_AGENT = "EOG-Endure-Dune-Aphid-Gate0/1.0"

ByteFetcher = Callable[[str, int], bytes]


class Gate0Stop(RuntimeError):
    """Terminal metadata identity/transport STOP before any archive access."""


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


def fetch_metadata(url: str, maximum_bytes: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise Gate0Stop(f"GBIF metadata GET returned HTTP {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise Gate0Stop(f"GBIF metadata transport unavailable: {exc}") from exc

    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise Gate0Stop(f"GBIF metadata GET returned HTTP {status}")
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise Gate0Stop("GBIF metadata unexpectedly used content encoding")
        body = response.read(int(maximum_bytes) + 1)

    if not body:
        raise Gate0Stop("GBIF metadata response was empty")
    if len(body) > int(maximum_bytes):
        raise Gate0Stop("GBIF metadata exceeded frozen byte bound")
    return body


def _normalized_doi(value: object) -> str:
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, dict):
        text = str(value.get("doi") or value.get("value") or "").strip()
    else:
        text = ""
    text = text.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    return text.casefold()


def evaluate_metadata(raw: bytes, contract: dict[str, object]) -> dict[str, object]:
    try:
        metadata = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Gate0Stop("GBIF metadata is not valid UTF-8 JSON") from exc
    if not isinstance(metadata, dict):
        raise Gate0Stop("GBIF metadata root is not an object")

    source = contract["source_identity"]
    observed_key = str(metadata.get("key") or "").strip()
    observed_title = str(metadata.get("title") or "").strip()
    observed_type = str(metadata.get("type") or "").strip().upper()
    observed_doi = _normalized_doi(metadata.get("doi"))

    if observed_key != source["gbif_dataset_key"]:
        raise Gate0Stop(
            f"GBIF dataset key drift: {observed_key!r} != {source['gbif_dataset_key']!r}"
        )
    if observed_title != source["title"]:
        raise Gate0Stop("GBIF dataset title drift")
    if observed_type not in {"SAMPLING_EVENT", "SAMPLINGEVENT"}:
        raise Gate0Stop(f"GBIF dataset type is not sampling event: {observed_type!r}")
    if observed_doi != str(source["doi"]).casefold():
        raise Gate0Stop(f"GBIF dataset DOI drift: {observed_doi!r}")

    endpoints = metadata.get("endpoints")
    if not isinstance(endpoints, list):
        raise Gate0Stop("GBIF metadata endpoints is not an array")
    archive_url = str(source["archive_url"])
    endpoint_urls = tuple(
        str(row.get("url") or "").strip()
        for row in endpoints
        if isinstance(row, dict)
    )
    if archive_url not in endpoint_urls:
        raise Gate0Stop("frozen IPT archive endpoint is absent from GBIF metadata")

    return {
        "gbif_dataset_key": observed_key,
        "title": observed_title,
        "dataset_type": observed_type,
        "doi": observed_doi,
        "archive_url": archive_url,
        "endpoint_urls": list(endpoint_urls),
        "metadata_modified": metadata.get("modified"),
        "metadata_pub_date": metadata.get("pubDate"),
        "metadata_license": metadata.get("license"),
        "metadata_publishing_organization_key": metadata.get(
            "publishingOrganizationKey"
        ),
    }


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher: ByteFetcher = fetch_metadata,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    gate = contract["gate0_metadata_only"]
    source = contract["source_identity"]

    base: dict[str, object] = {
        "schema": "eog.endure_dune_aphid_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "status": None,
        "metadata_request_count": 0,
        "metadata_bytes_opened": 0,
        "archive_requests": 0,
        "archive_bytes_opened": 0,
        "event_member_bytes_opened": 0,
        "occurrence_member_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }

    try:
        raw = fetcher(
            str(gate["authorized_url"]),
            int(gate["maximum_metadata_bytes"]),
        )
        base["metadata_request_count"] = 1
        base["metadata_bytes_opened"] = len(raw)
        identity = evaluate_metadata(raw, contract)
        result = {
            **base,
            "status": "gate0_metadata_ready_for_zip_inventory",
            "metadata_sha256": hashlib.sha256(raw).hexdigest(),
            "source_identity": identity,
            "next_gate": (
                "bounded ZIP EOCD and central-directory inventory only; "
                "do not open local headers or member payloads"
            ),
        }
    except (Gate0Stop, ValueError, TypeError) as exc:
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; terminal for this attempt and no repair/rerun",
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
                "fingerprint": result["fingerprint"],
                "metadata_bytes_opened": result["metadata_bytes_opened"],
            },
            sort_keys=True,
        )
    )
