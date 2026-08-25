from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.parse
from collections import Counter

import gate1_patch_profile as gate


def decode_frozen_patch(data: bytes):
    errors = []
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError("Patch CSV failed frozen decode order: " + " | ".join(errors))


def main():
    result = gate.base_result()
    a = result["response_firewall"]
    try:
        auth, auth_n, auth_final_url = gate.request_json(gate.AUTHORIZE_URL, gate.AUTH_BODY)
        a["patch_authorization_requests"] = 1
        if urllib.parse.urlparse(auth_final_url).netloc != "etsin.fairdata.fi":
            raise RuntimeError("Patch authorization redirected outside etsin.fairdata.fi")
        if not isinstance(auth, dict) or not isinstance(auth.get("url"), str):
            raise RuntimeError(f"Patch authorization response lacks url; keys={sorted(auth.keys()) if isinstance(auth, dict) else type(auth).__name__}")

        data, _final_download_url, content_type = gate.get_bytes_once(auth["url"])
        a["patch_payload_requests"] = 1
        a["patch_payload_bytes_opened"] = len(data)
        if len(data) != int(gate.SELECTED["size"]):
            raise RuntimeError(f"Patch byte-size mismatch: {len(data)} != {gate.SELECTED['size']}")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != gate.SELECTED["sha256"]:
            raise RuntimeError(f"Patch SHA-256 mismatch: {actual_sha} != {gate.SELECTED['sha256']}")

        text, encoding = decode_frozen_patch(data)
        sample = text[:65536]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        header = list(reader.fieldnames or [])
        if not header:
            raise RuntimeError("Patch CSV has no header")
        a["patch_header_opened"] = True
        rows = list(reader)
        a["patch_rows_opened"] = True
        a["patch_values_opened"] = True

        candidates = gate.candidate_groups(header)
        profiles = {
            group: {col: gate.profile_column(rows, col) for col in cols}
            for group, cols in candidates.items()
        }
        result["candidate_columns"] = profiles
        result["patch"] = {
            "authorization_response_bytes": auth_n,
            "payload_bytes": len(data),
            "verified_sha256": actual_sha,
            "content_type": content_type,
            "encoding": encoding,
            "encoding_rule": ["utf-8-sig", "cp1252"],
            "delimiter": delimiter,
            "header": header,
            "column_count": len(header),
            "row_count": len(rows),
            "blank_header_columns": [i for i, c in enumerate(header) if not str(c).strip()],
            "duplicate_header_names": sorted([k for k, v in Counter(header).items() if v > 1]),
            "identifier_candidate_names": candidates["identifier"],
            "geometry_candidate_names": candidates["geometry"],
            "temporal_eligibility_candidate_names": candidates["temporal_eligibility"],
        }
        result["status"] = "gate1_patch_profile_complete_response_still_closed"
        result["reason"] = "Exact frozen Patch payload was opened and profiled after size/SHA verification using the prospectively fixed UTF-8-SIG then CP1252 decode order; Locality Visit, Nest and all other dataset payloads remain unopened"
        gate.write_result(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response" if a["patch_payload_requests"] == 0 else "engineering_failure_after_response_independent_patch_only"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        gate.write_result(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
