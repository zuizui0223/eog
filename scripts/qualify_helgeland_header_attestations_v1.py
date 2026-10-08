#!/usr/bin/env python3
"""Offline Helgeland HEADER-ATTESTATION gate (not a source-data file reader).

Only accepts a small JSON manifest whose inputs were prepared externally
from FIRST HEADER LINES; never requests or opens a biological file or URL.
Names passing this test do not prove cross-file ID values join or indicate
independent byte verification, provenance truth, detection, or ecology.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT=BASE/"helgeland_header_schema_contract_v1.json"
FROZEN=BASE/"helgeland_source_metadata_frozen_v1.json"
SAFE_NAME=re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,127}$")
ALLOWED_DELIMITERS={"TAB","COMMA","SEMICOLON","WHITESPACE"}
MANIFEST_SCHEMA="eog.helgeland.header_only_attestation.v1"


def qualification(contract:dict,inventory:dict,attestation:dict|None)->dict:
    if contract["schema"]!="eog.helgeland.response_blind_header_contract.v1":
        raise ValueError("Wrong frozen contract schema")
    if inventory["schema"]!="eog.helgeland.public_dryad_api_inventory.frozen_observed_v1":
        raise ValueError("Wrong frozen metadata inventory schema")
    if contract["response_blind_gate_policy"]["biological_scoring_authorized"] is not False:
        raise ValueError("Biological outcome scoring must remain unauthorized")
    if contract["present_evidence"]["first_header_line_independently_extracted"] is not False:
        raise ValueError("Frozen original evidence stage changed; require new protocol")

    allowed={}
    for source, data in inventory["inventories"].items():
        if data["dryad_version_id"]!=contract["expected_source_version_ids"][source]:
            raise ValueError("Frozen source version does not match frozen header contract")
        if data["doi"]!=contract["source_doi_pins"][source]:
            raise ValueError("Frozen DOI changed")
        for f in data["files"]:
            allowed[f"{source}/{f['name']}"]={
                "doi":data["doi"],
                "dryad_version_id":data["dryad_version_id"],
                "dryad_file_id":f["file_metadata_id"],
            }

    required=contract["expected_header_roles"]
    if not all(key in allowed for key in required):
        raise ValueError("Required file absent from source inventory")

    counts={"expected_physical_headers":len(required),
            "attested_header_files":0,
            "unresolved_header_files":sorted(required)}
    base={
        "schema":"eog.helgeland.response_blind_header_qualification_receipt.v1",
        "scope":"UNTRUSTED_EXTERNAL_FIRST_LINE_ATTESTATION_ONLY",
        "source_versions":{"fitness_2025":354268,"pedigree_2024":278334},
        "individual_values_or_genotypes_opened_by_this_script":False,
        "dryad_file_bytes_opened_by_this_script":False,
        "id_and_island_value_join_verified":False,
        "header_matches_not_physical_byte_checksums":True,
        "ecological_endpoint_authorized":False,
        "first_island_founder_identified":False,
        "source_loss_or_recolonization_identified":False,
        "counts":counts,
    }
    if attestation is None:
        return {**base,"status":"HOLD_PHYSICAL_HEADERS_NOT_ATTESTED"}
    if attestation.get("schema")!=MANIFEST_SCHEMA:
        raise ValueError("Header attestation has unsupported schema")
    if set(attestation)!={"schema","records"}:
        raise ValueError("Header attestation contains unexpected keys; reject any row-level payload")
    records=attestation["records"]
    if not isinstance(records,list) or len(records)>len(required):
        raise ValueError("Unexpected header-only record count")
    observed={}
    for f in records:
        permitted={"file_key","doi","dryad_version_id","dryad_file_id",
                   "header_tokens","delimiter","first_line_only",
                   "contains_response_values","independent_extraction_reference"}
        if not isinstance(f,dict) or set(f)!=permitted:
            raise ValueError("Unexpected header record fields; no biological values allowed")
        key=f["file_key"]
        if not isinstance(key,str) or key not in required or key in observed:
            raise ValueError("Invalid, duplicate or nonrequired source header")
        expected=allowed[key]
        for field in ("doi","dryad_version_id","dryad_file_id"):
            if f[field]!=expected[field]:
                raise ValueError(f"{key}: mismatched source file identity {field}")
        if f["first_line_only"] is not True or f["contains_response_values"] is not False:
            raise ValueError("Not a header-only evidence record")
        if f["delimiter"] not in ALLOWED_DELIMITERS:
            raise ValueError("Undeclared or unknown physical delimiter")
        marker=f["independent_extraction_reference"]
        if not isinstance(marker,str) or not (8<=len(marker)<=256) or "\n" in marker:
            raise ValueError("Header has no bounded extraction provenance reference")
        tokens=f["header_tokens"]
        if not isinstance(tokens,list) or not 1<=len(tokens)<=200:
            raise ValueError("Invalid number of header fields")
        if not all(isinstance(t,str) and SAFE_NAME.fullmatch(t) for t in tokens):
            raise ValueError("Header contains nonschema tokens or unsafe characters")
        if len(set(tokens))!=len(tokens):
            raise ValueError("Duplicate physical column headers")
        if sum(len(t.encode("utf-8")) for t in tokens)>4096:
            raise ValueError("Header exceeds first-line-only budget")
        required_names=required[key]["required_exact"]
        if not all(x in tokens for x in required_names):
            raise ValueError(f"{key}: physical headers do not match published dictionary roles")
        observed[key]={"columns":len(tokens),"declared_delimiter":f["delimiter"]}
    counts["attested_header_files"]=len(observed)
    counts["unresolved_header_files"]=sorted(set(required)-set(observed))
    if counts["unresolved_header_files"]:
        return {**base,"status":"HOLD_INCOMPLETE_PHYSICAL_HEADER_SET",
                "attested_header_counts":observed}

    return {**base,
            "status":"HEADER_NAMES_ATTESTED_KEYS_STILL_UNJOINED",
            "attested_header_counts":observed,
            "interpretation":(
                "Only external header tokens align with the published dictionary. "
                "No source-file bytes were independently verified; individual ID "
                "and island keys were NOT joined, and no biological inference is licensed."
            )}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header-attestation-json",type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory=json.loads(FROZEN.read_text(encoding="utf-8"))
    attest=json.loads(args.header_attestation_json.read_text(encoding="utf-8")) if args.header_attestation_json else None
    report=qualification(contract,inventory,attest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",
                          encoding="utf-8")
    print(json.dumps({"status":report["status"],"counts":report["counts"]},sort_keys=True))


if __name__=="__main__":
    main()
