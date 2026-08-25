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
        return raw, r.geturl(), dict(r.headers.items())


def head_only(url: str):
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={
            "User-Agent": "Mozilla/5.0 EOG-SnapshotJapan-metadata-diagnostic/1.0",
            "Accept": "text/csv,application/octet-stream,*/*;q=0.1",
            "Referer": "https://bdj.pensoft.net/",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.geturl(), dict(r.headers.items())


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main():
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.pensoft_sequence_identity_diag.v2",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "landing": {},
        "candidate_links": [],
        "direct_supplement_head": {},
        "response_firewall": {
            "sequence_http_head_requests": 0,
            "sequence_payload_get_requests": 0,
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
        raw, final_url, headers = get_page(doi_url)
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
            "content_type": headers.get("Content-Type"),
            "html_bytes": len(raw),
            "html_sha256": hashlib.sha256(raw).hexdigest(),
            "expected_filename_mentions": filename_mentions,
            "supplement_doi_mentions": doi_mentions,
        }
        result["candidate_links"] = candidates

        direct = [u for u in candidates if "/article/download/suppl/" in u.lower()]
        if filename_mentions <= 0 or doi_mentions <= 0 or len(direct) != 1:
            result["status"] = "stop_pensoft_landing_does_not_resolve_unique_direct_sequence_endpoint"
            result["reason"] = (
                "supplement DOI landing did not jointly provide the frozen filename, DOI and exactly one direct supplement endpoint; "
                "sequence payload remained unopened"
            )
        else:
            head_url, head_headers = head_only(direct[0])
            result["response_firewall"]["sequence_http_head_requests"] = 1
            disp = head_headers.get("Content-Disposition") or head_headers.get("content-disposition")
            ctype = head_headers.get("Content-Type") or head_headers.get("content-type")
            clen = head_headers.get("Content-Length") or head_headers.get("content-length")
            etag = head_headers.get("ETag") or head_headers.get("etag")
            result["direct_supplement_head"] = {
                "landing_direct_url": direct[0],
                "head_final_url": head_url,
                "content_disposition": disp,
                "content_type": ctype,
                "content_length": clen,
                "etag": etag,
            }
            final_host = urllib.parse.urlparse(head_url).netloc.lower()
            if not (final_host.endswith("pensoft.net") or final_host.endswith("zenodo.org")):
                result["status"] = "stop_pensoft_direct_sequence_endpoint_redirects_to_unfrozen_host"
                result["reason"] = f"HEAD redirected to unexpected host {final_host}; payload remained unopened"
            else:
                result["status"] = "pensoft_sequence_identity_resolved_without_payload"
                result["reason"] = (
                    "the frozen supplement DOI landing names the exact sequence file and exposes one direct supplement endpoint; "
                    "HEAD metadata were recorded without GET/body access"
                )

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
