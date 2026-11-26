"""One exact public catalog metadata request; never retrieve response files."""
import argparse
import json
import re
from pathlib import Path
from urllib.request import build_opener, HTTPRedirectHandler, Request

ROOT = Path(__file__).resolve().parent
ITEM = "615c9c83d34e7b019242b88f"
DOI = "10.5066/P9MFJXK1"
URL = f"https://www.sciencebase.gov/catalog/item/{ITEM}?format=json"
LIMIT = 2097152


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def manifest(obj):
    title = obj.get("title", "")
    identity = (obj.get("id") == ITEM and isinstance(title, str)
                and "riverscape snorkeling" in title.lower()
                and "elwha" in title.lower())
    # Check only metadata identifier/link fields, not descriptive outcome text.
    identifiers = json.dumps([obj.get("identifiers", []), obj.get("webLinks", [])])
    doi_ok = bool(re.search(re.escape(DOI) + r"(?![A-Za-z0-9])", identifiers, re.I))
    files = obj.get("files", [])
    result = []
    if not isinstance(files, list):
        files = []
    for f in files:
        if not isinstance(f, dict):
            continue
        name, size = f.get("name"), f.get("size")
        ck = f.get("checksum")
        kind, val = (ck.get("type"), ck.get("value")) if isinstance(ck, dict) else (None, None)
        algorithm = str(kind).upper().replace("-", "")
        lengths = {"MD5": 32, "SHA1": 40, "SHA256": 64, "SHA512": 128}
        digest_ok = (algorithm in lengths and isinstance(val, str)
                     and len(val) == lengths[algorithm]
                     and bool(re.fullmatch("[0-9a-fA-F]+", val)))
        # Only export catalog name, size and validated digest. Never export links.
        result.append({"name": name if isinstance(name, str) else None,
                       "size": size if type(size) is int and size >= 0 else None,
                       "checksum_type": algorithm if digest_ok else None,
                       "checksum": val.lower() if digest_ok else None})
    complete = bool(result) and len(result) == len(files) and all(
        f["name"] and f["size"] is not None and f["checksum"] for f in result
    ) and len({f["name"] for f in result}) == len(result)
    return {"id": obj.get("id"), "title": title,
            "identity_confirmed": identity, "doi_confirmed": doi_ok,
            "files": result,
            "status": ("MANIFEST_METADATA_COMPLETE_RESPONSE_STILL_SEALED"
                       if identity and doi_ok and complete else "HOLD_INCOMPLETE_MANIFEST"),
            "response_payloads_opened": 0, "response_rows_parsed": 0,
            "scores": 0}


def self_test():
    fake = {"id": ITEM, "title": "Riverscape snorkeling surveys, Elwha River",
            "identifiers": [{"type": "DOI", "key": DOI}],
            "files": [{"name": "fixture.csv", "size": 100,
                       "checksum": {"type": "MD5", "value": "a"*32},
                       "url": "https://example.invalid/forbidden"}]}
    good = manifest(fake)
    assert good["status"].startswith("MANIFEST_METADATA_COMPLETE")
    assert "example.invalid" not in json.dumps(good)
    fake["files"][0]["checksum"]["value"] = "invalid"
    assert manifest(fake)["status"] == "HOLD_INCOMPLETE_MANIFEST"
    fake["id"] = "wrong"
    assert not manifest(fake)["identity_confirmed"]
    print("Offline metadata-only fixtures passed.")


def run():
    p = json.loads((ROOT / "manifest_protocol.json").read_text(encoding="utf-8"))
    if (p["status"] != "FROZEN_BEFORE_CI_METADATA_REQUEST" or
        p["url"] != URL or p["dataset_doi"] != DOI or p["item_id"] != ITEM or
        p["max_requests_per_run"] != 1 or p["redirects"] is not False or
        p["byte_limit"] != LIMIT or p["timeout_seconds"] != 20):
        raise ValueError("frozen metadata request contract changed")
    receipt = {"dataset_doi": DOI, "item_id": ITEM, "request_attempts": 1,
               "response_payloads_opened": 0, "response_rows_parsed": 0, "scores": 0}
    try:
        request = Request(URL, headers={"Accept": "application/json",
                                       "User-Agent": "EOG-public-metadata-audit/1.0"})
        with build_opener(NoRedirect()).open(request, timeout=20) as resp:
            receipt["http_status"] = resp.status
            if resp.geturl() != URL or resp.headers.get_content_type() != "application/json":
                raise ValueError("unexpected endpoint or content type")
            raw = resp.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise ValueError("metadata byte limit exceeded")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("unexpected catalog schema")
        receipt.update(manifest(data))
    except Exception as exc:
        receipt.update({"status": "HOLD_METADATA_REQUEST_OR_SCHEMA_FAILED",
                        "error_type": type(exc).__name__,
                        "http_error_code": getattr(exc, "code", None)})
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if args.output is None:
            parser.error("--output required for catalog request")
        result = run()
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(result["status"])
