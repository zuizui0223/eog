"""Extract pinned public FGDC metadata, never any response file."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
URL = "https://data.usgs.gov/datacatalog/metadata/USGS.615c9c83d34e7b019242b88f.xml"
SHA = "a51668a4fca0a0a13e082ad3b057a50c206ff3dbfb92d2abc1b8bfb9831a99ee"
SIZE = 34734
LIMIT = 2097152
EXPECTED = {
    "Elwha_Riverscape_reach_data.csv": ["Reach_ID", "Reach_Code", "Reach_Name", "Year",
        "Reach_Length_km", "Upstream_Reach_Boundary_rkm", "Downstream_Reach_Boundary_rkm",
        "Section", "Count_Saco", "Count_Onxx", "Count_Onts", "Count_Onmy",
        "Fish_km_Saco", "Fish_km_Onxx", "Fish_km_Onts", "Fish_km_Onmy", "JONTS", "JONKI", "JONXX"],
    "Elwha_Riverscape_reach_breaks.csv": ["reach_break", "UTM_easting", "UTM_northing"],
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def extract(raw, expected_sha=SHA, expected_size=SIZE):
    if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("metadata content identity changed")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("unsupported XML")
    root = ET.fromstring(raw)
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    if root.tag != "metadata":
        raise ValueError("not FGDC metadata")
    fields = {}
    for node in root.findall("./eainfo/detailed"):
        name = node.findtext("enttyp/enttypl")
        if name not in EXPECTED or name in fields:
            raise ValueError("unexpected or duplicate entity")
        attrs = [{"label": a.findtext("attrlabl"), "definition": a.findtext("attrdef"),
                  "definition_source": a.findtext("attrdefs")} for a in node.findall("attr")]
        if [a["label"] for a in attrs] != EXPECTED[name]:
            raise ValueError("pinned schema mismatch")
        fields[name] = {"entity_definition": node.findtext("enttyp/enttypd"), "fields": attrs}
    if set(fields) != set(EXPECTED):
        raise ValueError("missing entity")
    # Extract CRS and bounding fields only; no enumerated response domains.
    tags = ("utmzone", "horizdn", "ellips", "plandu", "geogunit", "mapprojn",
            "sfctrmer", "longcm", "latprjo", "feast", "fnorth", "absres", "ordres")
    crs = {tag: [n.text for n in root.findall(".//spref//" + tag) if n.text] for tag in tags}
    bounds = {tag: root.findtext("./idinfo/spdom/bounding/" + tag)
              for tag in ("westbc", "eastbc", "northbc", "southbc")}
    formats = [node.text for node in root.findall(".//distinfo//formname") if node.text]
    return {"status": "PINNED_METADATA_DETAILS_ONLY_RESPONSE_SEALED",
            "xml_sha256": expected_sha, "xml_bytes": len(raw), "crs": crs,
            "bounding_coordinates": bounds, "distribution_formats": formats,
            "entities": fields, "file_manifest_verified": False,
            "response_access_authorized": False, "physical_pre_post_split_verified": False}


def self_test():
    entities = "".join("<detailed><enttyp><enttypl>" + name +
                       "</enttypl></enttyp>" + "".join("<attr><attrlabl>" + label +
                       "</attrlabl><attrdef>fixture definition</attrdef><attrdomv><edom><edomv>DO_NOT_EXPORT</edomv></edom></attrdomv></attr>"
                       for label in labels) + "</detailed>" for name, labels in EXPECTED.items())
    raw = ("<metadata><spref><horizsys><planar><gridsys><utm><utmzone>10</utmzone></utm></gridsys></planar></horizsys></spref><eainfo>" +
           entities + "</eainfo></metadata>").encode()
    result = extract(raw, hashlib.sha256(raw).hexdigest(), len(raw))
    assert result["crs"]["utmzone"] == ["10"]
    assert len(result["entities"]) == 2 and not result["response_access_authorized"]
    assert "DO_NOT_EXPORT" not in json.dumps(result)
    try:
        extract(raw + b"x", hashlib.sha256(raw).hexdigest(), len(raw))
    except ValueError:
        pass
    else:
        raise AssertionError("changed metadata bytes accepted")
    print("Pinned metadata detail fixtures passed.")


def run():
    p = json.loads((HERE / "pinned_metadata_detail_protocol.json").read_text(encoding="utf-8"))
    if (p["status"] != "FROZEN_BEFORE_DETAIL_REQUEST" or p["url"] != URL or
            p["expected_bytes"] != SIZE or p["expected_sha256"] != SHA or
            p["max_requests"] != 1 or p["redirects"] is not False or
            p["timeout_seconds"] != 20 or p["byte_limit"] != LIMIT):
        raise ValueError("frozen detail protocol mismatch")
    r = {"metadata_url": URL, "request_attempts": 1, "response_payloads_opened": 0,
         "response_rows_parsed": 0, "scores": 0, "file_manifest_verified": False,
         "response_access_authorized": False}
    try:
        request = Request(URL, headers={"Accept": "application/xml,text/xml",
                                       "User-Agent": "EOG-public-metadata-audit/1.0"})
        with build_opener(NoRedirect()).open(request, timeout=20) as resp:
            r["http_status"] = resp.status
            if resp.geturl() != URL or resp.headers.get_content_type() not in (
                    "application/xml", "text/xml", "application/octet-stream"):
                raise ValueError("unexpected endpoint or content type")
            raw = resp.read(LIMIT + 1)
        r.update(extract(raw))
    except Exception as exc:
        r.update({"status": "HOLD_PINNED_DETAIL_REQUEST_OR_IDENTITY_FAILED",
                  "error_type": type(exc).__name__, "http_error_code": getattr(exc, "code", None)})
    return r


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.self_test:
        self_test()
    else:
        if a.output is None:
            p.error("--output required")
        r = run()
        a.output.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
        print(r["status"])
