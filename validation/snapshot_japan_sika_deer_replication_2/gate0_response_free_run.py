from __future__ import annotations

import urllib.error

import gate0_response_free as gate

ORIGINAL_DISCOVERY = gate.discover_response_metadata_only


def discover_with_frozen_metadata_candidates():
    response = gate.CONTRACT["forbidden_response"]
    try:
        return ORIGINAL_DISCOVERY()
    except RuntimeError as exc:
        if "found 0 candidate Zenodo records" not in str(exc):
            raise

    bounds = response.get("metadata_only_candidate_record_id_range_if_search_unindexed")
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise RuntimeError("missing frozen metadata-only record-id range")
    lo, hi = map(int, bounds)
    accepted = []
    inspected = []
    for rid in range(lo, hi + 1):
        try:
            rec, nbytes, _ = gate.get_json(f"https://zenodo.org/api/records/{rid}")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                inspected.append({"record_id": rid, "status": "404_not_found"})
                continue
            raise
        observed_doi = str(rec.get("doi") or rec.get("metadata", {}).get("doi") or "")
        title = str(rec.get("metadata", {}).get("title") or "")
        files = [f.get("key") for f in rec.get("files", [])]
        inspected.append({
            "record_id": rid,
            "status": "metadata_opened",
            "metadata_bytes": nbytes,
            "doi": observed_doi,
            "title": title,
            "file_keys": files,
        })
        if (
            observed_doi == response["supplement_doi"]
            and "Supplementary material 2" in title
            and response["filename"] in files
        ):
            accepted.append(rec)

    if len(accepted) != 1:
        raise RuntimeError(
            "bounded frozen metadata-only scan did not resolve exactly one sequence record; "
            f"accepted={[int(x['id']) for x in accepted]}"
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
        "discovery_mode": "bounded_frozen_record_metadata_scan_after_unindexed_search",
        "candidate_metadata_scan_range": [lo, hi],
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
