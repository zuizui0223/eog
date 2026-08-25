from __future__ import annotations

import gate0_response_free as gate

ORIGINAL_DISCOVERY = gate.discover_response_metadata_only


def discover_with_frozen_metadata_candidates():
    response = gate.CONTRACT["forbidden_response"]
    try:
        return ORIGINAL_DISCOVERY()
    except RuntimeError as exc:
        if "found 0 candidate Zenodo records" not in str(exc):
            raise

    accepted = []
    inspected = []
    for rid in response.get("metadata_only_candidate_record_ids_if_search_unindexed", []):
        rec, nbytes, _ = gate.get_json(f"https://zenodo.org/api/records/{int(rid)}")
        inspected.append({"record_id": int(rid), "metadata_bytes": nbytes})
        observed_doi = str(rec.get("doi") or rec.get("metadata", {}).get("doi") or "")
        title = str(rec.get("metadata", {}).get("title") or "")
        files = [f.get("key") for f in rec.get("files", [])]
        if (
            observed_doi == response["supplement_doi"]
            and "Supplementary material 2" in title
            and response["filename"] in files
        ):
            accepted.append(rec)

    if len(accepted) != 1:
        raise RuntimeError(
            "frozen metadata-only candidate check did not resolve exactly one sequence record; "
            f"accepted={[int(x['id']) for x in accepted]}, inspected={inspected}"
        )

    rec = accepted[0]
    fm = gate.record_file_meta(rec, response["filename"])
    return {
        "record_id": fm["record_id"],
        "supplement_doi": response["supplement_doi"],
        "title": str(rec.get("metadata", {}).get("title") or ""),
        "filename": fm["filename"],
        "size": fm["size"],
        "checksum_algorithm": fm["checksum_algorithm"],
        "checksum": fm["checksum"],
        "discovery_mode": "frozen_adjacent_record_metadata_only_fallback_after_unindexed_search",
        "candidate_metadata_checks": inspected,
        "payload_requests": 0,
        "payload_bytes_opened": 0,
        "header_bytes_opened": 0,
        "rows_opened": False,
        "values_opened": False,
    }


gate.discover_response_metadata_only = discover_with_frozen_metadata_candidates

if __name__ == "__main__":
    raise SystemExit(gate.main())
