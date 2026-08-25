from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_japan_sika_deer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
RESP = CONTRACT["forbidden_response"]
OUT = BUILD / "pensoft_xml_sequence_identity.json"
XML_URL = "https://bdj.pensoft.net/article/141168/download/xml/"
XLINK = "{http://www.w3.org/1999/xlink}href"


def get_xml():
    req = urllib.request.Request(
        XML_URL,
        headers={
            "User-Agent": "Mozilla/5.0 EOG-SnapshotJapan-article-metadata/1.0",
            "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return raw, r.geturl(), r.headers.get("Content-Type")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def text_of(el):
    return " ".join("".join(el.itertext()).split())


def main():
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.pensoft_xml_sequence_identity.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "article_xml": {},
        "matching_supplements": [],
        "response_firewall": {
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
        raw, final_url, ctype = get_xml()
        root = ET.fromstring(raw)
        matches = []
        all_supp_count = 0
        for el in root.iter():
            tag = el.tag.rsplit("}", 1)[-1]
            if tag != "supplementary-material":
                continue
            all_supp_count += 1
            blob = text_of(el)
            attrs = dict(el.attrib)
            hrefs = []
            for sub in el.iter():
                for k, v in sub.attrib.items():
                    if k == XLINK or k.rsplit("}", 1)[-1] == "href":
                        hrefs.append(v)
            xml_fragment = ET.tostring(el, encoding="unicode")
            filename_hit = RESP["filename"].lower() in xml_fragment.lower() or RESP["filename"].lower() in blob.lower()
            doi_hit = RESP["supplement_doi"].lower() in xml_fragment.lower() or RESP["supplement_doi"].lower() in blob.lower()
            if filename_hit or doi_hit:
                matches.append({
                    "id": attrs.get("id"),
                    "mime_type": attrs.get("mimetype") or attrs.get("mime-type"),
                    "mime_subtype": attrs.get("mime-subtype"),
                    "filename_hit": filename_hit,
                    "doi_hit": doi_hit,
                    "hrefs": sorted(set(hrefs)),
                    "text": blob[:1000],
                    "fragment_sha256": hashlib.sha256(xml_fragment.encode("utf-8")).hexdigest(),
                })
        result["article_xml"] = {
            "url": XML_URL,
            "final_url": final_url,
            "content_type": ctype,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "supplementary_material_count": all_supp_count,
        }
        result["matching_supplements"] = matches
        exact = [x for x in matches if x["filename_hit"] and x["doi_hit"]]
        if len(exact) == 1:
            result["status"] = "pensoft_xml_resolves_exact_sequence_supplement_identity"
            result["reason"] = "official article XML binds the frozen supplement DOI and frozen sequence filename to one supplementary-material element; sequence CSV bytes remain unopened"
        else:
            result["status"] = "stop_pensoft_xml_does_not_resolve_unique_sequence_identity"
            result["reason"] = f"official article XML yielded {len(exact)} elements jointly matching the frozen DOI and filename; sequence CSV bytes remain unopened"
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
