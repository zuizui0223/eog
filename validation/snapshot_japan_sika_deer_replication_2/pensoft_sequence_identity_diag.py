from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_japan_sika_deer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "pensoft_sequence_identity_diag.json"
RESP = CONTRACT["forbidden_response"]


def get_page(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 EOG-SnapshotJapan-metadata-diagnostic/1.0",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return raw, r.geturl(), r.headers.get("Content-Type"), r.headers.get("Content-Length")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main():
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.pensoft_sequence_identity_diag.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "landing": {},
        "candidate_links": [],
        "response_firewall": {
            "sequence_payload_requests": 0,
            "sequence_payload_bytes_opened": 0,
            "sequence_csv_header_bytes_opened": 0,
            "sequence_rows_opened": False,
            "sequence_values_opened": False,
            "model_fits": 0,
            "heldout_scores": 0,
        },
    }
    try:
        doi_url = "https://doi.org/" + RESP["supplement_doi"]
        raw, final_url, ctype, clen = get_page(doi_url)
        netloc = urllib.parse.urlparse(final_url).netloc.lower()
        if not netloc.endswith("pensoft.net"):
            raise RuntimeError(f"supplement DOI did not resolve to Pensoft: {final_url}")
        text = raw.decode("utf-8", errors="replace")
        hrefs = re.findall(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', text, flags=re.I)
        candidates = []
        for href in hrefs:
            u = urllib.parse.urljoin(final_url, html.unescape(href))
            low = u.lower()
            if RESP["filename"].lower() in low or any(tok in low for tok in ("supp", "download", ".csv")):
                candidates.append(u)
        candidates = sorted(set(candidates))
        filename_mentions = text.lower().count(RESP["filename"].lower())
        doi_mentions = text.lower().count(RESP["supplement_doi"].lower())
        result["landing"] = {
            "doi_url": doi_url,
            "final_url": final_url,
            "content_type": ctype,
            "reported_content_length": clen,
            "html_bytes": len(raw),
            "html_sha256": hashlib.sha256(raw).hexdigest(),
            "expected_filename_mentions": filename_mentions,
            "supplement_doi_mentions": doi_mentions,
        }
        result["candidate_links"] = candidates
        exact_filename_links = [u for u in candidates if RESP["filename"].lower() in u.lower()]
        if len(exact_filename_links) == 1:
            result["status"] = "pensoft_landing_resolves_unique_exact_sequence_file_link"
            result["reason"] = "supplement DOI landing metadata exposes exactly one link containing the frozen sequence filename; sequence file bytes remain unopened"
        elif filename_mentions > 0:
            result["status"] = "pensoft_landing_mentions_sequence_file_but_no_unique_direct_link"
            result["reason"] = "landing HTML names the frozen sequence file but does not expose one unique direct file link"
        else:
            result["status"] = "stop_pensoft_landing_does_not_resolve_frozen_sequence_identity"
            result["reason"] = "supplement DOI landing HTML does not expose the frozen sequence filename or one unambiguous direct link; no sequence payload was opened"
        result["fingerprint"] = hashlib.sha256(canonical({k: v for k, v in result.items() if k != "fingerprint"})).hexdigest()
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = hashlib.sha256(canonical({k: v for k, v in result.items() if k != "fingerprint"})).hexdigest()
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
