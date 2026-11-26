"""Retrieve only the official harvested FGDC XML; never open fish files."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
URL = "https://data.usgs.gov/datacatalog/metadata/USGS.615c9c83d34e7b019242b88f.xml"
DOI = "10.5066/P9MFJXK1"
LIMIT = 2097152


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def extract(raw):
    if len(raw) > LIMIT or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("unsupported XML or byte limit")
    root = ET.fromstring(raw)
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    if root.tag != "metadata":
        raise ValueError("not FGDC metadata")
    title = root.findtext("./idinfo/citation/citeinfo/title", default="")
    identity = "riverscape snorkeling" in title.lower() and "elwha" in title.lower()
    doi_ok = any(DOI.lower() in (node.text or "").lower()
                 for node in root.iter("onlink"))
    entities = []
    for node in root.findall("./eainfo/detailed"):
        entities.append({"entity_label": node.findtext("enttyp/enttypl"),
                         "attribute_labels": [a.findtext("attrlabl")
                                              for a in node.findall("attr")]})
    # Entity labels are not necessarily archive filenames or file manifests.
    return {"title": title, "identity_title_matches": identity,
            "doi_in_citation_links": doi_ok, "entity_schema_labels": entities,
            "xml_bytes": len(raw), "xml_sha256": hashlib.sha256(raw).hexdigest(),
            "status": ("ORIGINAL_XML_SCHEMA_READ_RESPONSE_STILL_SEALED"
                       if identity and doi_ok else "HOLD_XML_IDENTITY_UNCONFIRMED")}


def self_test():
    raw = b"""<metadata><idinfo><citation><citeinfo>
    <title>Riverscape snorkeling surveys, Elwha River</title>
    <onlink>https://doi.org/10.5066/P9MFJXK1</onlink>
    </citeinfo></citation></idinfo><eainfo><detailed><enttyp>
    <enttypl>fixture</enttypl></enttyp><attr><attrlabl>reach_id</attrlabl>
    </attr></detailed></eainfo></metadata>"""
    good = extract(raw)
    assert good["status"] == "ORIGINAL_XML_SCHEMA_READ_RESPONSE_STILL_SEALED"
    assert good["entity_schema_labels"] == [{"entity_label": "fixture", "attribute_labels": ["reach_id"]}]
    assert extract(raw.replace(DOI.encode(), b"other"))["status"] == "HOLD_XML_IDENTITY_UNCONFIRMED"
    try:
        extract(b"<!DOCTYPE metadata><metadata/>")
    except ValueError:
        pass
    else:
        raise AssertionError("DTD accepted")
    print("Offline XML metadata fixtures passed.")


def run():
    p = json.loads((HERE / "sdc_xml_protocol.json").read_text(encoding="utf-8"))
    if (p["status"] != "FROZEN_BEFORE_ORIGINAL_XML_REQUEST" or p["url"] != URL
            or p["dataset_doi"] != DOI or p["max_requests_per_execution"] != 1
            or p["redirects"] is not False or p["byte_limit"] != LIMIT
            or p["timeout_seconds"] != 20):
        raise ValueError("frozen request contract changed")
    receipt = {"metadata_url": URL, "request_attempts": 1,
               "response_payloads_opened": 0, "response_rows_parsed": 0, "scores": 0,
               "file_manifest_verified": False, "response_access_authorized": False}
    try:
        request = Request(URL, headers={"Accept": "application/xml,text/xml",
                                       "User-Agent": "EOG-public-metadata-audit/1.0"})
        with build_opener(NoRedirect()).open(request, timeout=20) as resp:
            receipt["http_status"] = resp.status
            if resp.geturl() != URL or resp.headers.get_content_type() not in (
                    "application/xml", "text/xml", "application/octet-stream"):
                raise ValueError("unexpected endpoint or content type")
            raw = resp.read(LIMIT + 1)
        receipt.update(extract(raw))
    except Exception as exc:
        receipt.update({"status": "HOLD_XML_REQUEST_OR_SCHEMA_FAILED",
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
            parser.error("--output required")
        result = run()
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(result["status"])
