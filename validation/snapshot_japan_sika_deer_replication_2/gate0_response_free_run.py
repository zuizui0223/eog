from __future__ import annotations

import json
from pathlib import Path

import gate0_response_free as gate

CERT_PATH = Path(__file__).resolve().parent / "pensoft_xml_sequence_identity_certificate.json"
ORIGINAL_RECORD_FILE_META = gate.record_file_meta

# Response-independent schema decision: Snapshot arrays are represented by the
# published Camtrap DP subproject_name field. project_id may coexist in the same
# deployment table but is not an alias for array identity in this replication.
gate.DEP_ALIASES["subproject_name"] = ["subproject_name", "subprojectName"]
gate.HAB_ALIASES["subproject_name"] = ["subproject_name", "subprojectName"]


def record_file_meta_current_zenodo(record: dict, filename: str):
    meta = ORIGINAL_RECORD_FILE_META(record, filename)
    if meta.get("content_url"):
        return meta
    matches = [f for f in record.get("files", []) if f.get("key") == filename]
    if len(matches) != 1:
        raise RuntimeError(f"record {record.get('id')} has {len(matches)} files named {filename}")
    self_url = matches[0].get("links", {}).get("self")
    if not self_url:
        raise RuntimeError(f"current Zenodo file object has neither links.content nor links.self for {filename}")
    meta["content_url"] = self_url
    meta["content_url_source"] = "links.self_current_zenodo_records_api"
    return meta


def discover_from_frozen_pensoft_certificate():
    response = gate.CONTRACT["forbidden_response"]
    cert = json.loads(CERT_PATH.read_text())
    if cert.get("status") != "pensoft_xml_resolves_exact_sequence_supplement_identity":
        raise RuntimeError("Pensoft sequence identity certificate is not passing")
    s = cert["supplement"]
    if s["doi"] != response["supplement_doi"]:
        raise RuntimeError("sequence DOI mismatch between contract and identity certificate")
    if s["published_file_name"] != response["filename"]:
        raise RuntimeError("sequence filename mismatch between contract and identity certificate")
    if s["binary_object_url"] != response["binary_object_url"]:
        raise RuntimeError("sequence binary object mismatch between contract and identity certificate")
    if cert["article_xml"]["sha256"] != response["article_xml_sha256"]:
        raise RuntimeError("article XML identity mismatch between contract and certificate")
    a = cert["response_firewall"]
    if any([
        a["sequence_payload_get_requests"] != 0,
        a["sequence_payload_bytes_opened"] != 0,
        a["sequence_csv_header_bytes_opened"] != 0,
        a["sequence_rows_opened"] is not False,
        a["sequence_values_opened"] is not False,
    ]):
        raise RuntimeError("identity certificate does not preserve zero-response firewall")
    return {
        "identity_source": "official_pensoft_article_xml_certificate",
        "supplement_doi": s["doi"],
        "filename": s["published_file_name"],
        "pensoft_element_id": s["pensoft_element_id"],
        "binary_object_url": s["binary_object_url"],
        "jats_xlink_href": s["jats_xlink_href"],
        "published_sequence_count": s["published_sequence_count"],
        "article_xml_sha256": cert["article_xml"]["sha256"],
        "matching_fragment_sha256": cert["article_xml"]["matching_fragment_sha256"],
        "payload_requests": 0,
        "payload_bytes_opened": 0,
        "header_bytes_opened": 0,
        "rows_opened": False,
        "values_opened": False,
    }


gate.record_file_meta = record_file_meta_current_zenodo
gate.discover_response_metadata_only = discover_from_frozen_pensoft_certificate

if __name__ == "__main__":
    raise SystemExit(gate.main())
